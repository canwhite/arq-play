# 2. 核心概念

## 学习目标
完成本节后，你能解释任务函数、Worker 配置、Redis 队列和幂等性如何配合。

## 心智模型

[Source-derived S5] 一条基本链路是：业务代码通过 Redis 连接池调用 `enqueue_job`，把函数名和参数放入队列；Worker 监听 Redis，找到已注册的函数并执行。见 [验证记录](07-verification-record.md#s5)。

```text
业务代码 -> Redis 队列 -> Worker -> 已注册的异步任务函数
```

[Illustrative] 可以把 Redis 想成“待办箱”，Worker 想成持续取件的工作人员；入队只表示工作已登记，不等于任务已经完成。

## 关键术语

- [Source-derived S6] **任务函数**：接收 `ctx` 上下文作为第一个参数的异步函数。见 [验证记录](07-verification-record.md#s6)。
- [Source-derived S7] **WorkerSettings**：Worker 配置类；源文示例通过 `functions` 注册任务，通过 `redis_settings` 指定 Redis。见 [验证记录](07-verification-record.md#s7)。
- [Source-derived S8] **幂等任务**：重复运行仍能安全得到可接受结果的任务。源文建议使用数据库事务或幂等键避免重复操作。见 [验证记录](07-verification-record.md#s8)。

## 依赖关系

[Source-derived S9] 示例需要 Python 包 `arq`、可访问的 Redis，以及 Worker 与业务代码能够引用相同的任务名称。源文明确给出 `pip install arq` 和本机 Redis 配置；更细的版本兼容性没有提供。见 [验证记录](07-verification-record.md#s9)。

## 具体例子

[Source-derived S10] 下面的任务打印问候并返回结果；`ctx` 是固定的第一个参数，`name` 是业务参数。

```python
async def say_hello(ctx, name: str) -> str:
    print(f"Hello {name}!")
    return f"Greeted {name}"
```
