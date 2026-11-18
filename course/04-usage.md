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

## 步骤二：集中维护任务

任务多了以后，生产者与 Worker 若各自写 `"say_hello"` 这种字符串，重命名或拼错时，只有任务执行才会失败。把函数、Worker 注册表、生产者使用的任务名放在同一个 `tasks.py`：

```python
# tasks.py
async def say_hello(ctx, name: str) -> str:
    print(f"Hello {name}!")
    return f"Greeted {name}"

async def add(ctx, a: int, b: int) -> int:
    return a + b

TASKS = [say_hello, add]

SAY_HELLO = say_hello.__name__
ADD = add.__name__
```

`TASKS` 是 Worker 的唯一注册表；`SAY_HELLO`、`ADD` 从函数对象生成，生产者无需重复手写字符串。任务函数一旦改名，Worker 注册和生产者入队名会一起更新。

再创建只负责 Worker 配置的 `worker.py`：

```python
# worker.py
from arq.connections import RedisSettings
from tasks import TASKS

class WorkerSettings:
    functions = TASKS
    redis_settings = RedisSettings(host="localhost", port=6379, database=0)
```

[Source-derived S17] 在 `worker.py` 中定义异步任务和 `WorkerSettings`，并把任务放进 `functions` 列表。这里将任务移至共享模块，但仍由 `WorkerSettings.functions` 注册。见 [验证记录](07-verification-record.md#s17)。

## 步骤三：启动 Worker

在**另一个终端**启动 Worker：

```bash
arq worker.WorkerSettings
```

`arq` 是安装 arq 后提供的 CLI。`worker` 是 `worker.py` 的模块名，`WorkerSettings` 是其中配置 Worker 的类名。CLI 会导入该类，创建并持续运行 Worker；`WorkerSettings` 本身不是一个需要在 Python 代码里手动实例化或 `await` 的对象。

开发时可让 Worker 处理完当前任务后退出：

```bash
arq worker.WorkerSettings --burst
```

[Source-derived S18] 命令格式是 `arq <模块名>.<WorkerSettings类名>`；启动后 Worker 监听 Redis 队列并执行任务。见 [验证记录](07-verification-record.md#s18)。

## 步骤四：从业务代码入队并获取返回值

在原终端运行以下 `main.py`。`enqueue_job()` 只返回 Job 句柄和 `job_id`；任务函数的 `return` 值要通过 `await job.result()` 获取。

```python
import asyncio
from arq import create_pool
from arq.connections import RedisSettings
from tasks import SAY_HELLO

async def main():
    redis = await create_pool(RedisSettings(host="localhost", port=6379))
    job = await redis.enqueue_job(SAY_HELLO, "Alice")
    print(f"Job enqueued: {job.job_id}")

    try:
        result = await job.result(timeout=10)
    except asyncio.TimeoutError:
        print("Job did not finish within 10 seconds")
    else:
        print(f"Job result: {result}")
    finally:
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(main())
```

Worker 正常执行后，两个终端分别看到：

```text
# Worker terminal
Hello Alice!

# main.py terminal
Job enqueued: <job-id>
Job result: Greeted Alice
```

`job.result(timeout=10)` 会轮询 Redis，最多等 10 秒；成功时返回 `say_hello()` 的 `return` 值。超时抛出 `asyncio.TimeoutError`；Worker 内任务抛出的异常会在这里再次抛出。因此 Web API 通常先返回 `job_id`，让客户端稍后查询结果，不应长时间占住请求等待任务完成。

[Source-derived S19] 入队端可打印 Job ID，Worker 执行任务时打印 `Hello Alice!`。本节补充的 `Job.result()` 调用以 arq 的 Job API 源码为准。见 [验证记录](07-verification-record.md#s19)。

## 小练习

[Illustrative] 把 `Alice` 换成另一个名字，并检查入队参数和任务函数参数是否一一对应。再思考：如果任务执行到一半 Worker 关闭，为什么任务必须允许重复运行？答案应联系幂等性，而不是假设“只执行一次”。
