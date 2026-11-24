# 幻觉与答案质量人工审计汇总（v1 评测集，E004 配置）

- 审计条目：**100**（A/B/C/D 各 25，缺文件：无）
- 判定分布：OK 71 / MISS 27 / HALLUC 2 / WRONG 0
- **幻觉率（strict）= 2.7%**（2/73，分母排除弃答）
- **幻觉率（guarded）= 2.0%**（2/100，分母含弃答）
- 弃答率 = 27.0%（27/100）
- 答案正确率（OK/全部，与 eval.py 的 judge 口径不同，勿混用）= 71.0%

## 分题型

| 题型 | OK | MISS | HALLUC | WRONG | 幻觉率(strict) |
|---|---|---|---|---|---|
| multi-hop | 13 | 11 | 0 | 0 | 0.0% |
| no-answer | 8 | 0 | 0 | 0 | 0.0% |
| paraphrase | 10 | 4 | 2 | 0 | 16.7% |
| single-hop | 40 | 12 | 0 | 0 | 0.0% |

## 分段

| 段 | OK | MISS | HALLUC | WRONG |
|---|---|---|---|---|
| A | 14 | 11 | 0 | 0 |
| B | 21 | 3 | 1 | 0 |
| C | 19 | 5 | 1 | 0 |
| D | 17 | 8 | 0 | 0 |

## 被判定为 HALLUC 的条目（逐条复核）

- `v1-B-020`（paraphrase｜B 段）：前半句（checkpointer 保存状态→可停止后恢复、甚至另一进程）有[1][2]支持，且回答自己承认「没有给出崩溃后自动从断点续跑的通用 API」；但随后给出的具体恢复手段 Command(resume) 在片段语境中仅对应 interrupt 决策，构成越界推断。gold 明确区分 invoke(None, config) 与 Command(resume=answer)，故判 HALLUC（API 语境误用型），不是纯措辞差异。
  - 断言：「恢复时用 Command(resume=...)（Python）或 new Command({ resume })（JavaScript）把决定交回给 middleware，agent 就会继续往下跑」——用户问的是进程崩溃后的断点续跑，但片段中 Command(resume) 只出现在 human-in-the-loop 流程里（"The middleware applies each decision"），没有任何片段支持它用于崩溃续跑；gold 的正确做法是 graph.invoke(None, config) 加载最新 checkpoint 重试未完成工作。回答把中断决策恢复路径套用为崩溃恢复路径，属片段不支持的断言。
- `v1-C-020`（paraphrase｜C 段）：两句「片段没有出现」是可被反证的具体断言：片段[3] 是 JS human-in-the-loop 的按 interrupt id 决策示例，代码里出现 `interrupt.value.name === "execute_sql"`，并对该工具返回 `{ type: "reject", message: "Archive the rows before deleting them." }`，即片段确实出现了数据库执行/删除相关的工具名与拒绝删除的说明。答案的其余机制性断言（checkpointer/thread_id、Command(resume)、FilesystemPermission）均有片段支持；主体仍是拒答，严格说兼具 MISS 特征，但含可反证的具体断言，判 HALLUC。
  - 断言：片段里**没有**出现「删库 / 数据库删除」相关的权限或工具配置
  - 断言：片段中没有出现「删库」或数据库删除工具的具体名称/参数

## 被判定为 MISS 的条目（召回缺失，不计幻觉）

- `v1-A-005`（single-hop）：未给出 gold 要求的 after_model 钩子，属召回失败而非幻觉：回答的替代说明（片段里只有 beforeModel/@before_model 属调用前；「调用之后删除」在片段中靠图节点连边 add_sequence/addEdge 实现；消息类型 RemoveMessage / REMOVE_ALL_ME
- `v1-A-006`（single-hop）：gold 的「默认 strategy 是 redact」「四种策略含 hash」未答。回答只声称「文档片段里出现的策略只有 redact/mask/block」，该限定与片段相符（片段确实没有默认值与 hash），并明确写「片段中没有说明不传 strategy 时的默认值」，属如实报缺口，无编造。
- `v1-A-007`（single-hop）：模型/工具/生命周期上下文的三分法及其瞬时/持久划分完全未答。回答的否定陈述有据：片段只有 Runtime/Framework/Harness 对照表、harness=prompt+tools+middleware、agent streaming 覆盖范围，确实没有该分类，也未编造该术语体系。
- `v1-A-008`（single-hop）：未答 chunk size/overlap 的调参方向。回答对片段的描述准确：5 个片段确为同一段 CHUNK_ANALYST_INSTRUCTIONS（逐字相同），只讲如何读 /retrieved/ 下文件并输出摘要，不含任何切分参数；回答据此列出缺失项，无编造。
- `v1-A-010`（single-hop）：只答了「写操作」一半且仅限 JS 版，gold 的「第一步必须先看有哪些表、再看最相关表结构」完全未答，故判 MISS。无幻觉：回答对 Python 片段[1] 的判断已核对全文（697 字符），其中确实没有 DML 禁令、也没有「先列表再结构」的步骤；JS 只读禁令、execute_sql、5 行限制、{top_k}
- `v1-A-012`（single-hop）：未答 stream.subgraphs（gold）。回答对片段的归纳准确：片段2/3 是 deepagents 的 streamMode:"updates" + subgraphs:true + namespace 区分主/子 agent，片段4/5 是 StreamChannel()/StreamChannel(na
- `v1-A-016`（multi-hop）：gold 的 state=短期记忆/单会话、store=长期记忆/跨会话、runtime context=会话级静态配置这组对比完全未答。回答列出的 runtime.context.user_id、namespace、runtime.store.asearch/aput/search 等均为片段原文，未编造记忆类型定义
- `v1-A-017`（multi-hop）：未答「所有路由是否都经主 agent」与「子 agent 未把结果写进最终消息的后果」。5 个片段确为同一段 stream 示例（逐字相同），只演示 namespace.length===0 区分主 agent、nodeName==="tools" 读子 agent 结果，不含路由拓扑或失败模式；回答的否定判断与片段一
- `v1-A-018`（multi-hop）：只给出第 2 步，gold 的第 1 步（自定义 auth handler 把请求解析为用户身份、每次运行从 runtime 读该身份）未答，故 MISS。回答的截断判断属实：片段2 正文即以「2. Mint or exchange a credential for that user.」开头；JS 示例与片段3 逐字
- `v1-A-020`（paraphrase）：未答「Model call limit 中间件」（gold），属召回失败。回答对片段1的描述准确：只见 @after_model 的 increment_counter 累加 model_call_count、以及 middleware=[check_call_limit, increment_counter] 的引用
- `v1-A-021`（paraphrase）：未答 Context editing 中间件（gold）。回答给出的两条线索均有出处且未越界：片段3 列举 before_model/after_model/wrap_tool_call（工具返回）可更新对话历史；片段4/5 的 85% 窗口截断旧工具调用、替换为磁盘文件指针。回答明确区分「自动行为」与「手动定向清理」
- `v1-B-002`（single-hop）：回答直接给出「没有找到」。gold 需要的 next 空元组=跑完、metadata.source=input/loop/update、writes、step，在 top5 中确实不存在：[1] 仅说 get_state 返回最新 checkpoint（含暂停节点与 interrupt），[3] 只用示例展示 next
- `v1-B-012`（single-hop）：回答给出「没有找到」。gold 的 read_file 行号/offset+limit/多模态、edit_file 精确替换+global replace、delete 递归删目录，在 top5 中确实没有；[1] 仅列工具名，[5] 仅演示 FilesystemMiddleware 工具白名单，[4] 是 inter
- `v1-B-019`（multi-hop）：回答「没有找到」，并逐片段说明只有 create_deep_agent 的 model/system_prompt/tools/memory/skills 示例，属实；gold 依赖的 interpreters 能力表（shell→sandbox backend）与文件工具表（execute 仅 sandbox）均未被
- `v1-C-013`（single-hop）：回答明确说没有找到普通函数 vs Task 的重跑/缓存对比；top5 确实只覆盖 [1][2] 的 @task/interrupt 顺序、[3][4] 的 pending writes、[5] 的节点改名，缺少 gold 所需内容。拒答本身无假断言，属检索失败，判 MISS。
- `v1-C-018`（multi-hop）：回答明确说没有找到子图与普通图节点的 checkpoint 对照；top5 只有 [1] 的子图三模式与 [3][5] 的 checkpoint 一般作用，缺少 gold 所需内容。拒答无假断言，属检索失败，判 MISS。
- `v1-C-019`（multi-hop）：回答明确说片段未涉及控制权/多 Agent 协作/嵌套；top5 只有 [1][2] 的 skill 描述重叠、[3][4] 的 SKILL.md 工具门控、[5] 的 skills 目录配置，缺少 gold 所需内容。拒答无假断言，判 MISS。
- `v1-C-021`（paraphrase）：回答说未找到完整 API，但 [1] 已展示 JS time travel 的 StateHistory、updateState、`graph.invoke(null, beforeAsk.config)` 与 Command resume；它仍称没有完整说明/没有 Python 版 API，且未给出 gold 的 g
- `v1-C-023`（paraphrase）：回答明确说没有找到语音链路；top5 只有 [1][2] 多 Agent 性能表、[3] Router turn 2 调用链、[4][5] 子图消息累积，缺少 gold 的 STT/agent/TTS 内容。拒答无假断言，属检索失败，判 MISS。
- `v1-D-003`（single-hop）：主干判断（分阶段加载、非一次性整份读入）正确，但只答出第 2 级 Read，未给出 gold 的三级拆分（frontmatter 的 name/description → SKILL.md 正文 → scripts/references/assets 支撑文件）。第 1 级片段本次未召回（top5 只有 skills#
- `v1-D-004`（single-hop）：明确拒答“为什么”，只复述 discovery 行为并指出片段未给设计动机，未编造上下文精简/on-demand 理由；gold 的解释不在本次 top5 内。score=0 但按幻觉口径应为 MISS 而非 HALLUC。
- `v1-D-013`（single-hop）：诚实拒答：只说明片段是 fault-tolerance 页面标题/简介与 ToolErrorMiddleware、ToolRetryMiddleware 的工具级重试，未编造 fallback 或调用上限中间件名。gold 的 modelFallbackMiddleware / ModelCallLimitMiddle
- `v1-D-014`（multi-hop）：第一问答对（同步不支持 mid-task 更新、异步可用 update_async_task）；第二问（启动时带哪些上下文）明确表示片段未覆盖。gold 的“server 上新 thread、isolated 只发任务描述、fork 带父对话历史、start_async_task 返回的 thread ID 即 tas
- `v1-D-015`（multi-hop）：第一问答对（自定义子 agent 显式传 skills、不继承、仅 general-purpose 继承、SkillsMiddleware 隔离）；第二问“文件存在哪由 backend 决定”未答，明确声明片段缺路径解析规则。gold 的 “procedural memory / 由 backend 决定”不在本次片段
- `v1-D-016`（multi-hop）：LocalShellBackend 侧准确（subprocess.run(shell=True)、无沙箱隔离），但 sandbox 侧的执行环境与生命周期（新会话=全新 sandbox、上一会话文件/包不保留）未答，声明片段缺 sandbox 细节。gold 的核心“生命周期”差异未覆盖。
- `v1-D-018`（multi-hop）：--init/--update 用途与不可组合、INSTRUCTIONS.md 读取与不重写均正确；对“是否有 update 专属选项”答“片段中未找到、无法确认存在”，未断言不存在，因此不是幻觉。gold 的 deferUnplannedClaimIssues（仅 update 有效、init 上 invalid_i
- `v1-D-019`（multi-hop）：如实说明片段只有 RAG 模式名（skills-guided retrieval、rubric grading）与通用 chunking 策略概述，未编造 splitter 参数或向量库配置；对片段[3]的内容概括准确。gold 的 chunkSize 1000/overlap 200、text-embedding-3

## 口径说明

- 本表只统计 **v1 评测集（100 题）+ E004 配置** 的一次运行。换配置/换评测集必须重跑并新起 RESULTS 行。
- MISS 与 HALLUC 严格区分：模型说「片段里没有」不算幻觉，但算「答不出」。
- 若某条被两个审计员判得不同，以本表为准；改动需在此注明。
