# 3. 核心功能

## 学习目标
完成本节后，你能识别 arq 示例中的输入、输出、配置能力和运行限制。

## 定义任务与注册 Worker

[Source-derived S11] Worker 配置类的 `functions` 列表注册任务函数，`redis_settings` 指定 Redis 主机、端口和数据库；`max_jobs` 可用于设置最大并发任务数。见 [验证记录](07-verification-record.md#s11)。

```python
from arq.connections import RedisSettings

async def say_hello(ctx, name: str) -> str:
    print(f"Hello {name}!")
    return f"Greeted {name}"

class WorkerSettings:
    functions = [say_hello]
    redis_settings = RedisSettings(host='localhost', port=6379, database=0)
    # max_jobs = 10
```

## 入队

[Source-derived S12] 业务代码使用 `create_pool` 连接 Redis，再以函数名字符串调用 `enqueue_job`；后续位置参数传给任务函数，返回的 Job 对象示例可提供 `job_id`。见 [验证记录](07-verification-record.md#s12)。

```python
redis = await create_pool(RedisSettings(host='localhost', port=6379))
job = await redis.enqueue_job('say_hello', 'Alice')
print(job.job_id)
```

## 启动模式

[Source-derived S13] `arq worker.WorkerSettings` 启动 Worker；`--burst` 处理当前队列后停止，适合脚本或 CI；`--watch <path>` 监控文件变化并自动重载，适合开发。见 [验证记录](07-verification-record.md#s13)。

## 限制与可观察结果

[Source-derived S14] 任务函数示例会打印 `Hello Alice!` 并返回 `Greeted Alice`；入队示例打印 Job ID。源文没有定义重试次数、结果持久化或错误处理 API，因此本课程不作这些承诺。见 [验证记录](07-verification-record.md#s14)。
