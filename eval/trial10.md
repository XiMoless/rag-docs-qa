# 第 0 周自检 · 手工 10 道试做题

> 清单要求：**手工做 10 道题，每题都能判断对错，并能在原文找到出处段落**。这是开工前第三条自检。
> 全部来自 `data/processed/chunks.jsonl` 的真实 chunk，`source` 列就是可点回的出处。

| # | 问题（模拟真实用户问法） | 标准答案要点 | 出处 chunk | 能判对错吗 | 能定位原文吗 |
|---|---|---|---|---|---|
| 1 | Deep Agents 的 `create_deep_agent` 里 `context_schema` 是干什么的？ | 定义「每次运行」的运行时上下文结构（用户 ID、API key、feature flag 这类 per-run 信息）；与 `state_schema`（图状态结构）是两件事 | `oss__python__deepagents__customization#009` | ✅ 能——答成「图状态」即错 | ✅ heading_path = ROOT（参数表页） |
| 2 | deepagents 里删文件用的 `delete` 工具对版本有什么要求？ | 需要 `deepagents>=0.7`；它可删单个文件，也可递归删除目录及其内容 | `oss__python__deepagents__tools#022` | ✅ 能——版本号是硬事实 | ✅ Built-in harness tools 表 |
| 3 | LangGraph、LangChain、Deep Agents 三者做 human-in-the-loop 的机制分别是什么？ | LangGraph 用 Interrupts；LangChain 用 human-in-the-loop middleware；Deep Agents 用 `interrupt_on` 参数 | `oss__python__concepts__products#010` | ✅ 能——三者错配即错 | ✅ Feature comparison 表 |
| 4 | 检索结果返回的片段太短、模型答不上来，该调什么？ | 增大 chunk size 或 overlap；另外「把相关思路切断」时也是增大 overlap 或按结构切分 | `oss__python__langchain__chunking#003` | ✅ 能——「片段缺上下文」对应「增大 size 或 overlap」 | ✅ Balance chunk size and overlap 表 |
| 5 | Markdown / HTML 文档推荐怎么切？ | 按文档结构切分，并把标题保留为 metadata | `oss__python__langchain__chunking#009` | ✅ 能——策略名是专有名词 | ✅ Choose a strategy 表 |
| 6 | Agent 的 state 里 `messages` 字段是怎么更新的？ | append-only：只追加新消息，不替换已有消息；类型 `list[BaseMessage]`，承载当前 thread 的完整对话历史 | `oss__python__langchain__agents#036` | ✅ 能——说成「覆盖/重写」即错 | ✅ Agent state 表 |
| 7 | Runtime Context、State、Store 三者的作用域有什么区别？ | Runtime Context=静态配置、对话级；State=短期记忆、对话级；Store=长期记忆、跨对话 | `oss__python__langchain__context-engineering#003` | ✅ 能——作用域答错即错 | ✅ Persistent context > Data sources 表 |
| 8 | 从零搭一个 deep agent，`TodoListMiddleware` 和 `SubAgentMiddleware` 各自加了什么能力？ | TodoListMiddleware 提供待办清单能力；SubAgentMiddleware 挂载可并行的可视化子代理（二者在同一份成品清单里并列出现） | `oss__python__langchain__deep-agent-from-scratch#051` | ⚠️ 部分——SubAgent 的作用需要同文档另一段才能说全 | ✅ What you built 表 |
| 9 | LangChain 组件里「Retrievers」这一类是干什么的？举两个实现 | 信息访问类组件，用于 RAG / 知识库检索；如 Vector retrievers、web retrievers | `oss__python__langchain__component-architecture#001` | ✅ 能 | ✅ Component categories 表 |
| 10 | 本语料里能查到 LlamaIndex 的 `VectorStoreIndex` 怎么配置 embedding 吗？ | **本题无答案**：语料只有 LangChain 官方文档，不含 LlamaIndex 内容，正确行为是明说找不到。 | 无。核实方式：全库检索 `llamaindex` 仅 2 处命中，均在 `oss__python__concepts__products#001` 与 JS 同名页的产品对比表里，只是把 LlamaIndex 列为「可选项」的一个名字，没有任何 API 文档 | ✅ 能——硬答即错 | ✅ 已实测：`llama_index` / `haystack` / `dspy` 全库 0 命中，`llamaindex` 仅表格提名 |

## 结论

- 10 道全部能判对错；第 8 题偏弱（需要跨段拼接才算完整），正式评测集里同类题要拆成 multi-hop 或换更独立的 chunk。
- 10 道全部能定位原文，`source` 列可直接在 `chunks.jsonl` 里按 `chunk_id` 找到。
- 发现一个真实约束：**表格型 chunk 是最可靠的事实来源**（题目 1/2/3/4/5/6/7/9 都来自表格），散文段落次之，纯代码块最差——这条已写进 `eval/AUTHORING.md` 的取材建议。
- 自检第 2 条：**通过**。
