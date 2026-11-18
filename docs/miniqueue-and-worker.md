# MiniQueue 与 Worker 的职责分工

`MiniQueue` 是生产者客户端，只负责“投递任务、取回结果”，不需要知道任务函数怎么实现。

`Worker` 是消费者，持有任务注册表：

```python
Worker({"add": add})
```

它收到 job 里的 `"function": "add"` 后，才把名字查成真实函数并执行：

```python
fn = self.functions[job["function"]]
```

| 对象 | 知道什么 | 做什么 |
|------|----------|--------|
| `MiniQueue` | 任务名、参数、job ID | `enqueue()` 写 Redis；`get_result()` 查 Redis |
| `Worker` | 任务名到 Python 函数的映射 | 从 Redis 取任务、执行函数、存执行结果 |

调用方可以这样使用，不必导入或接触 `add` 函数：

```python
queue = MiniQueue()
job_id = await queue.enqueue("add", 1, 2)
result = await queue.get_result(job_id)
```

可以把它理解成快递系统：

- `MiniQueue` 是寄件柜台：收件、给运单号、后续查物流。
- Redis 是中转仓库。
- `Worker` 是分拣和配送中心：知道 `add` 这类包裹要交给哪位处理员。

好处是 Web 服务等生产者只提交任务；Worker 可以独立部署、单独扩容。
