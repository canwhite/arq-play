# 4. 使用方法

## 学习目标
完成本节后，你能按顺序创建一个最小 Worker、提交任务并观察结果。

## 前置条件

[Source-derived S15] 源文给出的安装命令是 `pip install arq`；示例连接 `localhost:6379` 的 Redis。见 [验证记录](07-verification-record.md#s15)。

## 步骤一：安装

```bash
pip install arq
```

[Source-derived S16] 该命令安装 arq。见 [验证记录](07-verification-record.md#s16)。

## 步骤二：创建 Worker

[Source-derived S17] 在 `worker.py` 中定义异步任务和 `WorkerSettings`，并把任务放进 `functions` 列表。见 [验证记录](07-verification-record.md#s17)。

```python
from arq.connections import RedisSettings

async def say_hello(ctx, name: str) -> str:
    print(f"Hello {name}!")
    return f"Greeted {name}"

class WorkerSettings:
    functions = [say_hello]
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
```

## 步骤三：启动 Worker

```bash
arq worker.WorkerSettings
```

[Source-derived S18] 命令格式是 `arq <模块名>.<WorkerSettings类名>`；启动后 Worker 监听 Redis 队列并执行任务。见 [验证记录](07-verification-record.md#s18)。

## 步骤四：从业务代码入队

```python
import asyncio
from arq import create_pool
from arq.connections import RedisSettings

async def main():
    redis = await create_pool(RedisSettings(host='localhost', port=6379))
    job = await redis.enqueue_job('say_hello', 'Alice')
    print(f"Job enqueued: {job.job_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

[Source-derived S19] 预期观察包括入队端打印 Job ID，以及 Worker 执行任务时打印 `Hello Alice!`。见 [验证记录](07-verification-record.md#s19)。

## 小练习

[Illustrative] 把 `Alice` 换成另一个名字，并检查入队参数和任务函数参数是否一一对应。再思考：如果任务执行到一半 Worker 关闭，为什么任务必须允许重复运行？答案应联系幂等性，而不是假设“只执行一次”。
