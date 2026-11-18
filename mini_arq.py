import asyncio
import json
import os
import time
import uuid

import redis.asyncio as redis

PREFIX = "mini-arq"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

'''
将（List 主队列、BLPOP 阻塞拉取、处理中记录、显式确认、超时回收、asyncio.Semaphore 并发控制）串起来。
它不是 arq 的完整替代，而是把 arq 的核心骨架拆出来，方便对照理解。
'''
# ---------------------------------------------------------------
# 生产者侧：入队 + 查询结果
# ---------------------------------------------------------------
# 主线负责入队和拿结果
class MiniQueue:
    def __init__(self, redis_url=REDIS_URL, queue_name="default"):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.queue = f"{PREFIX}:queue:{queue_name}"
    
    # function  只存任务名。具体实现应在 Worker 消费队列时，通过任务注册表查到。
    async def enqueue(self, function: str, *args, **kwargs) -> str:
        job_id = uuid.uuid4().hex
        job = {
            "id": job_id,
            "function": function,
            "args": args,
            "kwargs": kwargs,
            "enqueued_at": time.time(),
        }
        # 主队列：LPUSH 入队，Worker 侧 BLPOP 从另一头取出
        """注意这里LIFO，这里的第一个L时last的意思，f是first的意思；后进先出，这是个栈
        与之相反的是FIFO，先进先出，是个队列，左进，右出，或者右进左出，排成一条线就ok
        """
        # 存取不用单独声明，直接使用redis就ok
        await self.r.lpush(self.queue, json.dumps(job))
        return job_id

    # 获取结果,就是到时间了redis去get
    async def get_result(self, job_id: str, timeout: float = 10) -> dict | None:
        key = f"{PREFIX}:result:{job_id}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = await self.r.get(key)
            if raw:
                return json.loads(raw)
            await asyncio.sleep(0.1)
        return None


# ---------------------------------------------------------------
# Worker 侧：拉取、执行、确认、回收
# ---------------------------------------------------------------
class Worker:
    def __init__(
        self,
        functions: dict,
        redis_url=REDIS_URL,
        queue_name="default",
        max_concurrent=10,
        job_timeout=30,
    ):
        self.r = redis.from_url(redis_url, decode_responses=True)
        self.queue = f"{PREFIX}:queue:{queue_name}"
        self.functions = functions
        self.sem = asyncio.Semaphore(max_concurrent)
        self.job_timeout = job_timeout
        self.in_progress_prefix = f"{PREFIX}:in-progress:"
        self.result_prefix = f"{PREFIX}:result:"
        self._stopping = False

    async def run(self):
        reaper = asyncio.create_task(self._reaper())
        try:
            while not self._stopping:
                # 先拿并发许可，再拉任务，避免从 Redis 拉出超过并发上限的任务
                await self.sem.acquire()
                # BLPOP 阻塞等待，timeout 让循环有机会响应停止信号
                item = await self.r.blpop(self.queue, timeout=1)
                if item is None:
                    self.sem.release()
                    continue
                job = json.loads(item[1])
                asyncio.create_task(self._execute(job))
        finally:
            reaper.cancel()

    async def _execute(self, job: dict):
        job_id = job["id"]
        in_progress_key = f"{self.in_progress_prefix}{job_id}"
        result_key = f"{self.result_prefix}{job_id}"
        payload = {"status": "failed", "error": "unknown"}
        try:
            # 1. 记录“处理中”：带开始时间和兜底 TTL
            await self.r.set(
                in_progress_key,
                json.dumps({"job": job, "started_at": time.time()}),
                ex=int(self.job_timeout) + 10,
            )
            # 2. 执行任务，硬超时防止任务无限挂起
            fn = self.functions[job["function"]]
            result = await asyncio.wait_for(
                fn(*job["args"], **job["kwargs"]), timeout=self.job_timeout
            )
            payload = {"status": "complete", "result": result}
        except asyncio.TimeoutError:
            payload = {"status": "failed", "error": "job timeout"}
        except Exception as exc:
            payload = {"status": "failed", "error": repr(exc)}
        finally:
            # 3. 确认：删除处理中记录，写结果
            try:
                await self.r.delete(in_progress_key)
                await self.r.set(result_key, json.dumps(payload), ex=3600)
            finally:
                self.sem.release()

    async def _reaper(self):
        """定期扫描处理中记录，把卡住/超时的任务重新入队。"""
        while True:
            await asyncio.sleep(5)
            async for key in self.r.scan_iter(f"{self.in_progress_prefix}*"):
                raw = await self.r.get(key)
                if raw is None:
                    continue
                data = json.loads(raw)
                # 留 5 秒缓冲，避免和 _execute 里的硬超时打架
                if time.time() - data["started_at"] <= self.job_timeout + 5:
                    continue
                # 用 SET NX 抢回收锁，防止多个 reaper 重复入队同一任务
                lock = f"{PREFIX}:reaper-lock:{data['job']['id']}"
                if await self.r.set(lock, "1", nx=True, ex=30):
                    await self.r.lpush(self.queue, json.dumps(data["job"]))
                    await self.r.delete(key)


# ---------------------------------------------------------------
# 示例：定义任务 + 跑起来
# ---------------------------------------------------------------
async def add(a, b):
    await asyncio.sleep(0.5)
    return a + b


async def main():
    # 先创建mini队列
    queue = MiniQueue()
    # worker实际上添加了真正的方法
    worker = Worker({"add": add}, max_concurrent=5, job_timeout=10)
    # worker执行了
    worker_task = asyncio.create_task(worker.run())

    # 拿到id
    job_id = await queue.enqueue("add", 1, 2)
    # 通过获取结果
    result = await queue.get_result(job_id)
    print(f"job {job_id} -> {result}")

    worker._stopping = True
    await worker_task


if __name__ == "__main__":
    asyncio.run(main())