# Redis List 如何形成任务队列

队列不是 Redis 自动凭空生成；它本质是 Redis 里一个名字固定的列表。生产者往列表放任务，worker 从列表取任务，于是形成先进先出队列。

## 先看最小过程

假设队列名叫 `jobs`，一开始不存在：

```text
Redis:
jobs 不存在
```

生产者提交两个任务：

```python
await redis.rpush("jobs", "发邮件给 A")
await redis.rpush("jobs", "生成日报")
```

`RPUSH` 意思：从列表右边放进去。Redis 自动创建名为 `jobs` 的列表：

```text
jobs:

左边                         右边
[发邮件给 A] [生成日报]
```

worker 取任务：

```python
_, job = await redis.blpop("jobs", timeout=30)
```

`BLPOP`：从左边拿走一个元素。因此先得到最早提交的“发邮件给 A”：

```text
jobs:

左边            右边
[生成日报]
```

再取一次，得到“生成日报”。这就是 FIFO（先进先出）：

```text
先放入 -> 先取出
```

## 为什么 `RPUSH` 配 `BLPOP`

两边操作方向相反：

```text
生产者：RPUSH -> 从右边入队
worker：BLPOP -> 从左边出队
```

所以新任务排在队尾，最老任务从队头离开。像排队买票：新人站队尾，窗口服务队头的人。

若改成下面这对，也同样 FIFO：

```text
LPUSH + BRPOP
```

关键不是左还是右，而是“放入一侧、从另一侧取出”。

## `BLPOP` 怎么和队列配合

若 `jobs` 为空：

```python
_, job = await redis.blpop("jobs", timeout=30)
```

worker 不会拿到空任务后不断重试；它的 Redis 连接会等在这里。

另一个程序执行：

```python
await redis.rpush("jobs", "处理订单 #42")
```

Redis 发现有人正在等 `jobs`：

```text
worker 等待 jobs
       ↓
生产者 RPUSH 一个新任务
       ↓
Redis 把任务交给等待中的 worker
       ↓
worker 开始处理任务
```

此时任务通常不会长期留在列表中：Redis 直接把它弹出并交给 worker。

## Redis 里的“队列”是什么

严格说，Redis 只提供 `List`（列表）这种数据结构；“队列”是我们根据操作方式赋予它的用途：

```text
Redis List + 固定 key（jobs）+ 入队规则 + 出队规则 = 任务队列
```

常见坑：`BLPOP` 一取到任务，任务便从 Redis 列表删除。worker 若随后崩溃，该任务可能丢失。生产环境常用“处理中队列”、重试机制，或 Redis Streams，保证任务能被找回。
