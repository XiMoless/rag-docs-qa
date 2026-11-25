# 幻觉与答案质量人工审计汇总（240 题 · E015 配置）

- 审计条目：**240 / 240**（8 份材料；缺 0 条，多 0 条）
- 判定分布：OK 213 / MISS 22 / HALLUC 5 / WRONG 0
- **幻觉率（strict）= 2.3%**（5/218，分母排除弃答）
- **幻觉率（guarded）= 2.1%**（5/240，分母含弃答）
- 弃答率 = 9.2%（22/240）
- 人工正确率 = 88.8%（OK/全部；**与 judge 的 0.761 不是同一口径**，judge 允许部分分）

## 分题集

| 题集 | n | OK | MISS | HALLUC | WRONG | 幻觉率(strict) | 弃答率 |
|---|---|---|---|---|---|---|---|
| v1 | 100 | 91 | 8 | 1 | 0 | 1.1% | 8.0% |
| v2 | 140 | 122 | 14 | 4 | 0 | 3.2% | 10.0% |

## 分题型

| 题型 | n | OK | MISS | HALLUC | WRONG | 幻觉率(strict) |
|---|---|---|---|---|---|---|
| multi-hop | 58 | 48 | 9 | 1 | 0 | 2.0% |
| no-answer | 20 | 20 | 0 | 0 | 0 | 0.0% |
| paraphrase | 38 | 32 | 5 | 1 | 0 | 3.0% |
| single-hop | 124 | 113 | 8 | 3 | 0 | 2.6% |

## 分段

| 材料 | OK | MISS | HALLUC | WRONG |
|---|---|---|---|---|
| 1 | 26 | 4 | 0 | 0 |
| 2 | 28 | 1 | 1 | 0 |
| 3 | 28 | 2 | 0 | 0 |
| 4 | 25 | 3 | 2 | 0 |
| 5 | 28 | 1 | 1 | 0 |
| 6 | 24 | 6 | 0 | 0 |
| 7 | 28 | 2 | 0 | 0 |
| 8 | 26 | 3 | 1 | 0 |

## HALLUC 逐条

- `v1-B-020`（paraphrase｜v1）：Command(resume=…) 在[3][4] 是 human-in-the-loop 审批流程里交回人工决定的 API，模型把它当成进程崩溃后续跑的通用恢复方式，属把 A 语境 API 当 B 语境解法；片段对应的正常续跑是 graph.invoke(None, config) 配 checkpointer。
  - 断言：恢复时用 Command(resume=...)（Python）或 new Command({ resume })（JavaScript）把决定交回给 middleware，agent 就会继续往下跑 [3][4]。
- `v2-E-004`（single-hop｜v2）：片段[5]用 class State(MessagesState)/@dataclass class Context 与 ToolRuntime[Context, State] 分别命名两类数据并演示 runtime.state 读图状态、runtime.context 读 per-run 值，故「没有任何片段命名/归类」与[5]冲突。
  - 断言：但没有任何片段把「这次调用传进来、运行期不该被改的 user id」和「当前会话里自己维护的计数器」这两类数据分别命名、归类
  - 断言：给出的文档里没有找到能回答这个问题的内容
- `v2-E-010`（single-hop｜v2）：片段[2]正是 safety_guardrail 的续页，含 bind_tools([ResponseSafety], tool_choice=...)、stream_writer(result) 与 tool_calls[0] 的 evaluation 判断，回答却称其为无关的 agent.stream 内容并据此弃答。
  - 断言：片段 [1] 在 `stream_writer = get_stream_writer()` 处就截断了，没有展示 `stream_writer(...)` 的调用方式
  - 断言：片段 [2]–[7] 内容完全相同，讲的是 `agent.stream(..., stream_mode="updates", subgraphs=True)` 下如何区分主 agent 与子 agent 的更新，与「中间件里用 writer 推送安全结论」无关
  - 断言：没有展示如何调用 `safety_model` 做判定、如何解析 `ResponseSafety`
- `v2-F-002`（single-hop｜v2）：把片段[1][2]（checkpoint_ns 与 thread_id 示例）的 RunnableConfig 当成片段[4][5]该小节『Add runtime configuration』的解法；该小节只写把配置加到函数签名，对应的是 context_schema/runtime.context，回答自己也承认[8]的 context= 才是运行时传参
  - 断言：在节点函数签名里加一个 `RunnableConfig` 类型的参数，即可拿到运行时配置
  - 断言：配置值从 `config` 的 `configurable` 字段读取
- `v2-I-018`（multi-hop｜v2）：问题问 Python langchain-mcp-adapters→langchain.mcp，却把片段[1]（JS @langchain/mcp-adapters 2.0 迁移页）的 prefixToolNameWithServerName 与单 server 也加前缀的结论搬来；Python 侧参数为 tool_name_prefix 且仅多 server 的 MCPConfig/ClientGroup 自动加前缀
  - 断言：默认会给工具名加上服务器名前缀，格式为 {server}_{tool}（例如 weather_get_forecast），即使只有一个服务器也是如此；除非设置 prefixToolNameWithServerName
  - 断言：1.x 中该选项默认是 false，2.0 改为默认开启。若要保留 1.x 的名字，需设置 prefixToolNameWithServerName: false

## WRONG 逐条

无。


## 口径说明

- 本表统计 **240 题 + E015 主配置**（k=8 / qe / rerank / expand±1）的一次运行。
- 与 `results/hallucination_summary.md`（v1 100 题 + E004 配置）不可混引：题集不同、配置不同。
- 「引用片段超出材料」的条目在 reason 里注明；只要没有与所给片段冲突就判 OK。
