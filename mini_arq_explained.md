# mini_arq.py：从入队到拿结果

`mini_arq.py` 是一个教学版异步任务队列：调用方把任务放入 Redis；Worker 后台取出并执行；调用方按任务 ID 查询结果。

它不是完整 `arq` 替代品。重点是理解任务在异常、超时、Worker 崩溃时如何不轻易丢失。

## 先看全局：一次 `add(1, 2)` 怎么走

```python
job_id = await queue.enqueue("add", 1, 2)
result = await queue.get_result(job_id)
```

```text
调用方
  |
  | enqueue("add", 1, 2)
  v
Redis 主队列
mini-arq:queue:default
  |
  | Worker.run() 用 BLPOP 取走任务
  v
Worker._execute()
  |-- 写入 in-progress：任务正在运行
  |-- 找到 add 函数，执行 add(1, 2)
  |-- 写入 result：成功或失败结果
  `-- 删除 in-progress，归还并发名额
  |
  v
调用方 get_result(job_id) 读取 result
```

餐厅类比：

- `MiniQueue`：点餐台，接单并发取餐号。
- Redis 主队列：订单栏。
- `Worker`：厨师，取单做菜。
- `in-progress`：正在制作的订单标记。
- `result`：出餐结果。
- `_reaper`：巡检员，发现厨师崩溃遗留的订单后重新挂回订单栏。

---

## 1. Redis 中有哪些数据

代码统一给 key 加前缀：

```python
PREFIX = "mini-arq"
```

因此 Redis 里主要有三类 key：

| 用途 | key 形式 | 内容 |
| --- | --- | --- |
| 等待执行 | `mini-arq:queue:default` | Redis List，存放排队任务 |
| 正在执行 | `mini-arq:in-progress:<job_id>` | 当前任务和开始时间 |
| 已有结果 | `mini-arq:result:<job_id>` | 成功结果或失败原因 |

Redis 地址来自环境变量：

```python
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
```

若没有设置 `REDIS_URL`，默认连接本机 Redis 的第 `0` 个数据库。

---

## 2. MiniQueue：负责“提交任务”和“查结果”

```python
queue = MiniQueue()
```

初始化时创建异步 Redis 客户端：

```python
self.r = redis.from_url(redis_url, decode_responses=True)
self.queue = f"{PREFIX}:queue:{queue_name}"
```

`decode_responses=True` 让 Redis 返回 Python 字符串，不返回 `bytes`。后面可直接用 `json.loads()` 解析 JSON。

### 2.1 `enqueue`：创建任务并放入主队列

调用：

```python
job_id = await queue.enqueue("add", 1, 2)
```

会生成一个唯一 ID：

```python
job_id = uuid.uuid4().hex
```

再组成任务数据：

```python
job = {
    "id": job_id,
    "function": "add",
    "args": (1, 2),
    "kwargs": {},
    "enqueued_at": time.time(),
}
```

转成 JSON 后放进 Redis List：

```python
await self.r.lpush(self.queue, json.dumps(job))
```

注意：这里是 `LPUSH`，Worker 使用 `BLPOP`，两者都操作 List 左侧。因此新任务会先被取走，实际顺序是 LIFO，后进先出：

```text
LPUSH A -> [A]
LPUSH B -> [B, A]
BLPOP    -> 取出 B
```

如果目标是常见的 FIFO，先进先出，应该使用：

```text
LPUSH 入队 + BRPOP 从右侧取出
```

### 2.2 `get_result`：等待结果

`enqueue` 只负责提交任务，不会等待任务完成。它立即返回 `job_id`。

```python
result = await queue.get_result(job_id)
```

`get_result` 每隔 0.1 秒读取一次结果 key：

```python
while time.time() < deadline:
    raw = await self.r.get(key)
    if raw:
        return json.loads(raw)
    await asyncio.sleep(0.1)
return None
```

流程：

```text
有 result key -> 返回 JSON 结果
没有 result key -> 等 0.1 秒 -> 再查
超过 timeout -> 返回 None
```

这叫轮询。代码好懂，但大量客户端频繁查询时会增加 Redis 请求量。

---

## 3. Worker：负责“取任务并执行”

Worker 创建时要传入允许执行的函数：

```python
worker = Worker({"add": add}, max_concurrent=5, job_timeout=10)
```

这三个参数最重要：

```python
self.functions = functions
self.sem = asyncio.Semaphore(max_concurrent)
self.job_timeout = job_timeout
```

### 3.1 `functions`：函数白名单

```python
{"add": add}
```

左边 `"add"` 是任务 JSON 里保存的名字；右边 `add` 是真正 Python 函数。

Worker 取到下面这个任务：

```json
{
  "function": "add",
  "args": [1, 2]
}
```

执行：

```python
fn = self.functions[job["function"]]
```

等价于：

```python
fn = self.functions["add"]  # 得到 add 函数
result = await fn(1, 2)      # 等价于 await add(1, 2)
```

白名单作用：Redis 中任务只能选择已注册函数。任务写入未知函数名时，Worker 会报错并记录失败，不会执行任意代码。

### 3.2 `Semaphore`：限制最多同时跑几个任务

```python
self.sem = asyncio.Semaphore(max_concurrent)
```

若 `max_concurrent=5`：

```text
前 5 个任务 -> 可立刻开始
第 6 个任务   -> 等其中一个任务结束
任务结束      -> release()，放行一个等待者
```

`Semaphore` 本质是“名额计数器”。`acquire()` 领取一个名额；`release()` 归还一个名额。

这里它还实现背压：Worker 先确认有执行能力，才从 Redis 取任务。未领取的任务继续留在 Redis 队列。

```python
await self.sem.acquire()                       # 先拿名额
item = await self.r.blpop(self.queue, timeout=1)  # 再取任务
```

这避免 Worker 把 100 个任务先取到本地、却只能同时执行 5 个。

`Semaphore(0)` 还能当作“等通知”的工具：`acquire()` 会一直等待，直到其他协程调用 `release()`。不过这里用它只做并发控制。

---

## 4. `run`：持续从 Redis 取任务

Worker 启动：

```python
worker_task = asyncio.create_task(worker.run())
```

`run()` 做两件事：启动回收器、循环取任务。

```python
reaper = asyncio.create_task(self._reaper())
while not self._stopping:
    await self.sem.acquire()
    item = await self.r.blpop(self.queue, timeout=1)
```

`BLPOP` 是“阻塞式左侧弹出”：

- 队列有任务：立即取出一个。
- 队列空：等待最多 1 秒。
- 1 秒仍为空：返回 `None`。

不能无限阻塞，因为 `while not self._stopping` 需要定期检查停止信号。

队列暂时为空时，已拿到的名额必须归还：

```python
if item is None:
    self.sem.release()
    continue
```

取到任务后：

```python
job = json.loads(item[1])
asyncio.create_task(self._execute(job))
```

`create_task` 让 `_execute(job)` 在后台执行；`run()` 可以继续领取下一个并发名额并拉取下一个任务。

---

## 5. `_execute`：单个任务的完整生命周期

一个任务从 Redis 被取出后，进入 `_execute(job)`。

```text
1. 写 in-progress 记录
2. 找到对应函数
3. 在超时限制内执行函数
4. 写 success / failed result
5. 删除 in-progress 记录
6. release() 归还并发名额
```

### 5.1 写入处理中记录

```python
await self.r.set(
    in_progress_key,
    json.dumps({"job": job, "started_at": time.time()}),
    ex=int(self.job_timeout) + 10,
)
```

记录两件事：任务原始数据、开始时间。

`ex` 是 Redis 的 TTL，过期自动删除。若任务超时是 30 秒，则该记录最多保留 40 秒。

这条记录用于 Worker 崩溃恢复：任务已被从主队列取走，但尚未完成时，仍能被 `_reaper` 找到。

### 5.2 找函数，限制执行时长

```python
fn = self.functions[job["function"]]
result = await asyncio.wait_for(
    fn(*job["args"], **job["kwargs"]),
    timeout=self.job_timeout,
)
```

- `fn`：从白名单取到的函数。
- `fn(*args, **kwargs)`：把任务参数传给函数。
- `asyncio.wait_for`：超过 `job_timeout` 就抛出 `asyncio.TimeoutError`。

成功时：

```python
payload = {"status": "complete", "result": result}
```

超时时：

```python
payload = {"status": "failed", "error": "job timeout"}
```

函数本身报错时：

```python
payload = {"status": "failed", "error": repr(exc)}
```

### 5.3 无论成功失败，都收尾

```python
finally:
    try:
        await self.r.delete(in_progress_key)
        await self.r.set(result_key, json.dumps(payload), ex=3600)
    finally:
        self.sem.release()
```

`finally` 表示不管任务成功、超时、函数报错，下面操作都要执行：

1. 删除处理中记录。
2. 结果写入 Redis，保留 1 小时。
3. 归还并发名额。

如果漏掉 `self.sem.release()`，名额会被耗尽，Worker 最后不再拉取新任务。

---

## 6. `_reaper`：Worker 崩溃后重新入队

正常超时由 `asyncio.wait_for` 处理。但若 Worker 进程直接崩溃，`finally` 根本没有机会运行：

```text
任务从主队列取出
    -> Worker 崩溃
    -> 没有 result
    -> in-progress 仍存在
```

`_reaper` 每 5 秒扫描 `in-progress` key：

```python
async for key in self.r.scan_iter(f"{self.in_progress_prefix}*"):
```

若运行时间超过“任务超时 + 5 秒缓冲”：

```python
if time.time() - data["started_at"] <= self.job_timeout + 5:
    continue
```

则尝试回收任务。

### 为什么要回收锁

多个 Worker 都可能运行 `_reaper`。没有锁时，两个 Worker 可能同时发现同一任务，都把它重新入队，导致重复执行。

```python
if await self.r.set(lock, "1", nx=True, ex=30):
```

- `nx=True`：只在 lock 不存在时创建成功。
- 成功的那个 reaper 才能回收。
- `ex=30`：锁 30 秒后自动失效，避免异常后永久锁住。

回收动作：

```python
await self.r.lpush(self.queue, json.dumps(data["job"]))
await self.r.delete(key)
```

任务重新进入主队列，之后可能被任何 Worker 再次执行。

## 7. 这个设计的可靠性边界

它提供“至少一次执行”，不是“恰好一次执行”。

```text
Worker 可能在任务已实际完成、但结果尚未写入 Redis 时崩溃
    -> reaper 会重试任务
    -> 同一任务可能执行两次
```

所以生产任务应尽可能幂等：重复执行后，最终业务结果仍正确。

例如：

```text
“将订单状态设为 paid”    -> 可设计为幂等
“每执行一次扣 100 元”     -> 需要额外防重
```

---

## 8. 示例运行顺序

```python
async def add(a, b):
    await asyncio.sleep(0.5)
    return a + b

async def main():
    queue = MiniQueue()
    worker = Worker({"add": add}, max_concurrent=5, job_timeout=10)
    worker_task = asyncio.create_task(worker.run())

    job_id = await queue.enqueue("add", 1, 2)
    result = await queue.get_result(job_id)
    print(f"job {job_id} -> {result}")

    worker._stopping = True
    await worker_task
```

执行顺序：

```text
1. 创建 queue 和 worker。
2. 后台启动 worker.run()。
3. 提交 add(1, 2) 任务。
4. Worker 取任务，执行约 0.5 秒。
5. Worker 写入 {'status': 'complete', 'result': 3}。
6. get_result() 读到结果。
7. 设置 _stopping，Worker 停止拉取新任务。
```

输出大致为：

```text
job <随机任务 ID> -> {'status': 'complete', 'result': 3}
```

## 9. 一句话记忆

```text
主队列负责“等执行”；in-progress 防止 Worker 崩溃丢任务；
result 给调用方查结果；Semaphore 限制并发；reaper 回收失联任务。
```
