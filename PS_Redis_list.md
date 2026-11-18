下面是一张统一的 CRUD 表，把 Redis List 最常用的命令按**增、删、改、查**归类。示例默认 `mylist = [a, b, c]`，可在 `redis-cli` 直接跑。

### Redis List 统一 CRUD 表

| 分类 | 命令 | 作用 | 解决什么问题 | 示例 |
| :--- | :--- | :--- | :--- | :--- |
| **增** | `LPUSH key v [v...]` | 从左端插入一个或多个元素 | 栈式入栈、头部优先入队 | `LPUSH mylist x` → `[x,a,b,c]` |
| **增** | `RPUSH key v [v...]` | 从右端插入一个或多个元素 | FIFO 队列标准入队 | `RPUSH mylist x` → `[a,b,c,x]` |
| **增** | `LPUSHX key v` | 仅 key 已存在时从左端插入 | 避免误创建空列表 | `LPUSHX nokey x` → `0`（不创建） |
| **增** | `RPUSHX key v` | 仅 key 已存在时从右端插入 | 尾部追加的幂等写入 | `RPUSHX mylist x` → `4` |
| **增** | `LINSERT key BEFORE\|AFTER pivot v` | 在指定元素前/后插入 | 在已知元素旁精准插入 | `LINSERT mylist BEFORE b x` → `[a,x,b,c]` |
| **删** | `LPOP key [count]` | 从左端移除并返回元素 | 栈出栈、头部消费 | `LPOP mylist` → `"a"`，变 `[b,c]` |
| **删** | `RPOP key [count]` | 从右端移除并返回元素 | FIFO 出队 | `RPOP mylist` → `"c"`，变 `[a,b]` |
| **删** | `LREM key count value` | 按值删除，`count>0` 从头、`<0` 从尾、`0` 全删 | 任务完成后从“处理中”列表移除、去重 | `LREM processing 1 task1` → 删 1 个匹配 |
| **删** | `LTRIM key start end` | 只保留区间内元素，其余丢弃 | 控制长度防无限增长、保留最近 N 条 | `LTRIM mylist 0 1` → `[a,b]` |
| **删** | `BLPOP key [key...] timeout` | 阻塞版 `LPOP`，可监听多个 key | 消除消费者轮询，队列空时挂起 | `BLPOP mylist 5` → 有则立即返回，空则等 5 秒 |
| **删** | `BRPOP key [key...] timeout` | 阻塞版 `RPOP` | 无轮询的 FIFO 消费 | `BRPOP queue 0` → 永久等待任务 |
| **删** | `LMOVE src dst LEFT\|RIGHT LEFT\|RIGHT` | 原子地从 src 弹出并推入 dst | 防丢任务：取出同时转移到“处理中”列表 | `LMOVE queue processing RIGHT LEFT` |
| **删** | `BLMOVE src dst ... timeout` | `LMOVE` 的阻塞版 | 原子转移 + 无轮询，可靠队列最优组合 | `BLMOVE queue processing RIGHT LEFT 0` |
| **删** | `RPOPLPUSH src dst` | 旧版特例：src 尾部弹出推入 dst 头部 | 兼容旧代码；6.2+ 建议用 `LMOVE` | `RPOPLPUSH queue processing` |
| **删** | `BRPOPLPUSH src dst timeout` | `RPOPLPUSH` 的阻塞版 | 旧版可靠队列阻塞消费 | `BRPOPLPUSH queue processing 5` |
| **删** | `LMPOP numkeys key... LEFT\|RIGHT [COUNT n]` | 从多个 key 中第一个非空列表弹出 | 多队列消费，返回值结构更简洁（7.0+） | `LMPOP 2 q1 q2 LEFT` |
| **删** | `BLMPOP timeout numkeys key... ...` | `LMPOP` 的阻塞版 | 多队列阻塞消费（7.0+） | `BLMPOP 5 2 q1 q2 LEFT` |
| **改** | `LSET key index value` | 按索引修改元素 | 更新已知位置的值 | `LSET mylist 0 A` → `[A,b,c]` |
| **改** | `LINSERT key BEFORE\|AFTER pivot v` | 在指定元素旁插入（也属“增”） | 精准插入而不打乱其余顺序 | `LINSERT mylist AFTER a x` → `[a,x,b,c]` |
| **改** | `LTRIM key start end` | 裁剪保留区间（也属“删”） | 修改 List 的“窗口” | `LTRIM mylist -2 -1` → `[b,c]` |
| **查** | `LLEN key` | 返回 List 长度 | 监控积压、判断空满 | `LLEN mylist` → `3` |
| **查** | `LINDEX key index` | 按索引取元素，`-1` 为最后 | 随机访问、查看队首/队尾而不弹出 | `LINDEX mylist -1` → `"c"` |
| **查** | `LRANGE key start end` | 取闭区间内所有元素 | 分页读取、查看内容、调试 | `LRANGE mylist 0 -1` → `[a,b,c]` |
| **查** | `LPOS key element [RANK n] [COUNT n]` | 查找元素位置索引（6.0.6+） | 判断任务是否已在队列、定位元素 | `LPOS mylist b` → `1` |
| **查** | `BLPOP` / `BRPOP` 的返回值 | 返回 `[key, value]` | 同时监听多队列时知道来源 | `BLPOP q1 q2 0` → `["q1","task"]` |

### 几个命令的归类说明

- **`LINSERT`** 既算“增”（插入新元素），也可视为“改”（改变列表结构），表中两处都列了，按你习惯归一类即可。
- **`LTRIM`** 既算“删”（丢弃区间外元素），也算“改”（修改列表窗口），同理。
- **`LMOVE`/`BLMOVE`/`RPOPLPUSH`** 归类为“删”，因为语义核心是“从源列表移除”；但它同时向目标列表“增”，是原子的一增一删。
- **`BLPOP`/`BRPOP`** 归类为“删”，因为它们是弹出操作，只是多了阻塞等待。

### 按场景速查

| 场景 | 命令组合 |
| :--- | :--- |
| 简单 FIFO 队列 | `RPUSH` 入队 + `LPOP` 出队 |
| 无轮询消费 | `BLPOP` / `BRPOP` |
| **可靠队列（不丢任务）** | `BLMOVE queue processing RIGHT LEFT 0` + `LREM` 确认 + 超时回收 |
| 栈 | `LPUSH` + `LPOP` |
| 控制长度 | `LTRIM key 0 N-1` |
| 查看内容 | `LRANGE key 0 -1` |
| 监控积压 | `LLEN key` |
| 多队列消费 | `BLPOP q1 q2 timeout` 或 `BLMPOP`（7.0+） |

**一句话记忆：增用 `L/RPUSH`，删用 `L/RPOP`，要无轮询加 `B`，要防丢任务用 `LMOVE`/`BLMOVE` 配 `LREM` 确认，改结构用 `LSET`/`LINSERT`/`LTRIM`，查状态用 `LLEN`/`LINDEX`/`LRANGE`/`LPOS`。**