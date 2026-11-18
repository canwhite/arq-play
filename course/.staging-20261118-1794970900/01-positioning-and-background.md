# 1. 定位与背景

## 学习目标
完成本节后，你能说明 arq 解决什么问题、适合谁，以及它与异步应用的关系。

[Source-derived S1] arq 是一个基于 Python `asyncio` 和 Redis 的异步作业队列；它由 Samuel Colvin 开发，定位为面向异步应用的轻量、现代 `rq` 继任者。见 [验证记录](07-verification-record.md#s1)。

## 它解决的问题

[Source-derived S2] 应用可以把耗时工作放入 Redis 队列，由独立 Worker 稍后执行，而业务代码只负责提交任务。源文将使用拆成两部分：定义并运行 Worker，以及在业务代码中入队任务。见 [验证记录](07-verification-record.md#s2)。

## 适用对象与前置知识

[Illustrative] 适合已经会基本 Python 异步编程、能运行 Redis，并希望把后台任务从请求处理流程中分离出来的开发者。本文不替你补充 Redis 安装或生产部署细节；这些内容不在源文件中。

## 重要背景

[Source-derived S3] 源文称，截至 2026 年 arq 进入“仅维护模式”：仍可稳定使用，但可能不会积极添加新功能。新项目选型时应把这一点作为评估因素。见 [验证记录](07-verification-record.md#s3)。

[Source-derived S4] arq 的任务可能重复执行：Worker 在任务成功或明确失败前不会把任务从队列移除；Worker 执行中关闭时，任务可能重新回到队列。见 [验证记录](07-verification-record.md#s4)。
