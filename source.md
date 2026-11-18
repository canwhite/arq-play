**arq** 通常被理解为 **Async Redis Queue** 的缩写，不过它的官方描述更直接：一个基于 Python `asyncio` 和 Redis 的异步作业队列（Job Queue）。它由 pydantic 的作者 Samuel Colvin 开发，定位是轻量、现代的 `rq`（Redis Queue）继任者，专门为异步应用设计。

### 🚀 如何快速使用 arq

使用 arq 主要涉及两部分：**定义并运行 Worker**，以及在**业务代码中入队任务**。

#### 1. 安装
```bash
pip install arq
```

#### 2. 定义任务与 Worker 配置
创建一个文件（例如 `worker.py`），在其中定义你的异步任务函数和 Worker 配置类。

```python
# worker.py
from arq.connections import RedisSettings

# 定义异步任务，第一个参数固定为 ctx (上下文)
async def say_hello(ctx, name: str) -> str:
    print(f"Hello {name}!")
    return f"Greeted {name}"

# 定义 Worker 配置类，类名可以自定义
class WorkerSettings:
    functions = [say_hello]  # 注册所有任务函数
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    # max_jobs = 10  # 可选：设置最大并发任务数
```

#### 3. 在业务代码中入队任务
在你的应用（如 FastAPI 接口）中，通过 `create_pool` 连接到 Redis，然后使用 `enqueue_job` 按**函数名**入队任务。

```python
# main.py
import asyncio
from arq import create_pool
from arq.connections import RedisSettings

async def main():
    redis = await create_pool(RedisSettings(host='localhost', port=6379))
    # 第一个参数是任务函数的名字（字符串），后续是传递给该函数的参数
    job = await redis.enqueue_job('say_hello', 'Alice')
    print(f"Job enqueued: {job.job_id}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 4. 启动 Worker
在终端中，使用 `arq` 命令行工具指向你的 `WorkerSettings` 类来启动 Worker。它会监听 Redis 队列并执行任务。

```bash
# 格式：arq <模块名>.<WorkerSettings类名>
arq worker.WorkerSettings
```

### 💡 几个关键点

**任务需要是幂等的**
这是使用 arq 时最重要的设计原则。arq 采用“**悲观执行**”策略：任务在成功或明确失败前不会从队列移除。如果 Worker 在任务执行过程中关闭，该任务会被重新放回队列，**可能会被再次执行**。因此，你的任务逻辑需要能安全地重复运行，例如通过数据库事务或幂等键来避免重复操作。

**注意项目状态**
根据 2026 年的信息，arq 项目已进入**仅维护模式**。这意味着它仍然稳定可用，但可能不会积极添加新功能。对于新项目，这是一个需要纳入考量的因素。

**常用的 Worker 启动模式**
- **`--burst`**：一次性模式，处理完当前队列中的所有任务后 Worker 会自动停止，适合脚本或 CI 场景。
- **`--watch <path>`**：开发模式，监控指定路径下的文件变化，自动重载 Worker。