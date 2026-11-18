# 6. 学习路径

## 学习目标
完成本节后，你能用可观察结果判断自己是否掌握了 arq 的最小使用闭环。

## 路径

1. [Source-derived S22] **准备**：会写基本 Python `async` 函数，并准备可访问的 Redis；安装 `arq`。见 [验证记录](07-verification-record.md#s22)。
2. [Source-derived S23] **理解**：掌握任务函数的 `ctx` 参数、Worker 的函数注册和 Redis 设置。见 [验证记录](07-verification-record.md#s23)。
3. [Source-derived S24] **实践**：启动 `arq worker.WorkerSettings`，再通过 `create_pool` 和 `enqueue_job` 提交任务。见 [验证记录](07-verification-record.md#s24)。
4. [Source-derived S25] **加固**：为任务设计幂等行为，因为 Worker 异常关闭时任务可能重复执行。见 [验证记录](07-verification-record.md#s25)。
5. [Illustrative] **延伸**：在确认基本闭环后，再研究项目当前版本、部署方式和错误处理；这些不在源文证据范围内。

## 完成检查

[Source-derived S26] 你可以认为最小学习目标达成，当你能：

- 写出一个带 `ctx` 的异步任务；
- 在 `functions` 中注册它；
- 用 `enqueue_job` 传入函数名和参数；
- 观察任务打印问候语，并记录返回 Job ID；
- 解释为什么不能假设任务只执行一次。

见 [验证记录](07-verification-record.md#s26)。
