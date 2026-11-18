# 5. 相关工具

## 学习目标
完成本节后，你能根据源文件提供的定位信息，做出谨慎的工具选择判断。

## 与 rq 的关系

[Source-derived S20] 源文把 arq 定位为轻量、现代的 `rq`（Redis Queue）继任者，并强调 arq 专门为异步应用设计。见 [验证记录](07-verification-record.md#s20)。

| 工具 | 源文支持的定位 | 选择提示 |
|---|---|---|
| arq | 基于 `asyncio` 和 Redis 的异步作业队列 | 已有异步 Python 应用且接受 Redis 队列模型时，可将其纳入评估 |
| rq | 被 arq 作为“继任者”对照提及 | 源文没有提供 rq 的 API、兼容性或版本对比，不能据此做迁移承诺 |

## 选择规则

[Source-derived S21] 新项目评估 arq 时，应同时考虑其异步定位和“仅维护模式”的项目状态。见 [验证记录](07-verification-record.md#s21)。

[Not applicable] 源文没有提供 Celery、Dramatiq 或其他队列工具的证据，因此本节不比较它们，也不虚构性能、功能或兼容性差异。
