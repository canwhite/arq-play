# 7. 验证记录

## 输入与完整性

- Root source: `/Users/doing/Desktop/arq-play/source.md`
- Read-only source checksum (SHA-256): `6770647df1e0bce2a7d63ac091f7a4cf183c364e43c1a8232493a5801e679433`
- Destination: `/Users/doing/Desktop/arq-play/course`
- Staging: `/Users/doing/Desktop/arq-play/course/.staging-20261118-1794970900`
- Source was not edited.

## Source evidence map

每条 `Source-derived` 标签都指向下列记录。行号按源文件从 0 开始计数。

| ID | Source locator | Affected sections |
|---|---|---|
| <a id="s1"></a>S1 | `source.md` lines 0-0: “基于 Python asyncio 和 Redis 的异步作业队列…轻量、现代的 rq（Redis Queue）继任者” | 01, 05 |
| <a id="s2"></a>S2 | lines 2-4: 使用涉及定义/运行 Worker 与业务代码入队 | 01 |
| <a id="s3"></a>S3 | lines 62-63: “仅维护模式”及其影响 | 01, 05 |
| <a id="s4"></a>S4 | lines 57-60: 悲观执行、Worker 关闭后可能再次执行 | 01, 02, 06 |
| <a id="s5"></a>S5 | lines 30-31, 49-50: 连接 Redis、入队、Worker 监听并执行 | 02 |
| <a id="s6"></a>S6 | lines 18-20: 任务函数第一个参数固定为 ctx | 02 |
| <a id="s7"></a>S7 | lines 23-27: functions、redis_settings、max_jobs | 02, 03 |
| <a id="s8"></a>S8 | lines 57-60: 幂等原则、事务或幂等键 | 02, 06 |
| <a id="s9"></a>S9 | lines 6-9, 14-27: 安装与 Redis 配置示例 | 02 |
| <a id="s10"></a>S10 | lines 18-21: say_hello 示例及返回值 | 02 |
| <a id="s11"></a>S11 | lines 23-27: Worker 配置字段 | 03 |
| <a id="s12"></a>S12 | lines 30-47: create_pool、enqueue_job、job_id | 03 |
| <a id="s13"></a>S13 | lines 49-55, 65-67: 启动、burst、watch | 03 |
| <a id="s14"></a>S14 | lines 18-21, 39-43: 可观察输出；源文未覆盖的能力保持未声明 | 03 |
| <a id="s15"></a>S15 | lines 6-9, 26: 安装与 localhost Redis | 04 |
| <a id="s16"></a>S16 | lines 6-9: pip install arq | 04 |
| <a id="s17"></a>S17 | lines 11-27: worker.py、任务与配置 | 04 |
| <a id="s18"></a>S18 | lines 49-55: CLI 格式和监听行为 | 04 |
| <a id="s19"></a>S19 | lines 19-21, 39-43: Hello 输出与 Job ID | 04 |
| <a id="s20"></a>S20 | lines 0-0: arq 与 rq 的定位关系 | 05 |
| <a id="s21"></a>S21 | lines 62-63: 维护模式对新项目的影响 | 05 |
| <a id="s22"></a>S22 | lines 6-9, 14-27: 安装与最小 Worker 前提 | 06 |
| <a id="s23"></a>S23 | lines 18-27: ctx、注册和 Redis 设置 | 06 |
| <a id="s24"></a>S24 | lines 30-55: 入队与启动顺序 | 06 |
| <a id="s25"></a>S25 | lines 57-60: 重复执行与幂等 | 06 |
| <a id="s26"></a>S26 | lines 18-21, 23-27, 30-47, 57-60: 综合完成检查依据 | 06 |

## Evidence gaps and research record

- Gap G1: 源文没有提供 Redis 安装、arq 版本兼容矩阵、生产部署、重试 API、结果存储或其他队列工具的可靠细节。它们不是完成源文课程所必需的，因此未做外部研究。
- Gap G2: “根据 2026 年的信息”是源文自身的时间性表述；本课程保留为 source-derived，不把它升级成独立外部确认。
- External research: none. Root content was treated as sufficient for the bounded course; no private content was sent externally.

## Audit inputs and findings

- Draft boundary: only the seven files in the staging directory; root source and files outside staging were excluded from edits.
- Section audit: completed by local structural checks below; no external post-mortem tool was available in this run.
- Cross-section consistency: terminology uses `WorkerSettings`, `functions`, `redis_settings`, `enqueue_job`, `ctx`, and “幂等” consistently.
- Findings resolved: all seven required filenames present; all source-derived paragraphs include an evidence ID; all examples are labeled; unsupported comparisons remain explicitly not applicable.
- Unresolved: no runtime execution was performed because the source does not establish that Redis or the arq package is installed in this workspace. Commands are source-derived examples, not execution claims.

## Promotion gate

Before promotion, verify the root checksum is unchanged, the staging files are regular files, the seven-file allowlist is exact, all local links resolve, and the destination is still empty. Then promote only these files:

1. `01-positioning-and-background.md`
2. `02-core-concepts.md`
3. `03-core-functionality.md`
4. `04-usage.md`
5. `05-related-tools.md`
6. `06-learning-path.md`
7. `07-verification-record.md`
