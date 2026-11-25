# 审计材料 4/8（30 条，明细文件第 91–120 行）

## v1-D-016（multi-hop）

**问题**：LocalShellBackend 和我在生产里用的 sandbox，在执行环境上最关键的区别是什么？

**gold**：LocalShellBackend 直接在宿主机上做文件系统操作和 shell 执行，没有任何隔离，只适合受控的开发环境。sandbox 是隔离环境，而且有生命周期：换一个新会话就是一个全新的 sandbox，文档示例里第二个会话里 pandas 都没装、上一个会话的文件也不在。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：最关键的区别是隔离性——LocalShellBackend 直接在宿主机上执行命令、没有沙箱隔离；而 sandbox backend 在隔离环境中执行。**

- LocalShellBackend 通过 `subprocess.run(shell=True)` 直接在你的机器上运行命令，**没有沙箱隔离** [5][6]。
- Sandbox backend 则在隔离环境中提供 execute 工具来运行 shell 命令 [1][2]。
- 文档明确建议：生产环境需要文件系统交互时，应使用 sandbox backend [3][4]。

另外补充两点差异（同样来自片段）：

- LocalShellBackend 是在 FilesystemBackend 基础上扩展出 execute 工具，用于在宿主机上跑 shell 命令 [18][20]；它支持 `timeout`（默认 120s）、`max_output_bytes`（默认 100,000）、`env`、`inherit_env` 等参数 [17][19]。
- 关于 execute 工具的可用范围，片段 [7] 的表述是「execute：在环境中运行 shell 命令（仅 sandbox backends 可用）」，这与 LocalShellBackend 也提供 execute 的说法存在表述差异；按片段原文，[7] 强调的是 sandbox backends 才提供 execute，而 [18][20] 说明 LocalShellBackend 也扩展了 execute。使用时请以具体 backend 文档为准。

**最小示例（Python，来自片段 [8] 的 sandbox 用法示意）：**

```python
return create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    backend=LangSmithSandbox(sandbox=ls_sandbox),
)
```

片段中没有给出 LocalShellBackend 的完整构造示例，因此这里不补充代码。

**top5 片段**：

片段[1] `oss__python__deepagents__overview#020` ｜ Deep Agents overview ｜ Execution environment > Code execution

```text
- Sandbox backends expose an execute tool for shell commands in an isolated environment.
```

片段[2] `oss__javascript__deepagents__overview#012` ｜ Deep Agents overview ｜ Execution environment > Code execution

```text
- Sandbox backends expose an execute tool for shell commands in an isolated environment.
```

片段[3] `oss__javascript__deepagents__backends#011` ｜ Backends ｜ Built-in backends > FilesystemBackend (local disk)

```text
3. Use a sandbox backend for production environments requiring filesystem interaction.
```

片段[4] `oss__python__deepagents__backends#017` ｜ Backends ｜ Built-in backends > FilesystemBackend (local disk)

```text
3. Use a sandbox backend for production environments requiring filesystem interaction.
```

片段[5] `oss__javascript__deepagents__backends#034` ｜ Backends ｜ Built-in backends > LocalShellBackend (local shell)

```text
- Commands run directly on your machine using subprocess.run(shell=True) with no sandboxing.
```

---

## v1-D-017（multi-hop）

**问题**：怎么让 agent 在调用某个工具之前停下来等我批准？我批准之后又该怎么让它继续跑？

**gold**：在配置里给对应工具打开 interruptOn，工具调用前就会暂停、等人工批准。中断后按顺序给每个 actionRequest 一个 decision（比如 approve），再用 Command 带上 resume 的 decisions 恢复执行。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

可以用 **Human-in-the-loop（人工介入）** 机制实现：agent 在调用敏感工具前会暂停并等待批准，批准后用 `Command(resume=...)` 恢复执行。关键前提是**必须配置持久化（checkpointer）并传入 `thread_id`**，否则无法暂停/恢复 [1][2][3]。

- **暂停**：调用 `agent.invoke(...)` 时传入带 `thread_id` 的 config，agent 会在执行敏感工具前暂停等待批准 [1][2]。
- **恢复**：再次调用 `agent.invoke`，传入 `Command(resume=...)`，并**使用同一个 `thread_id`** 来恢复被暂停的会话 [1][2]。
- 恢复时批准的动作写法为 `{"decisions": [{"type": "approve"}]}` [1][2]。

> 注意：片段中出现的 API 是 `Command(resume=...)`（Python）和 `new Command({ resume: ... })`（JavaScript），并没有出现名为 “approve_tool” 之类的专用 API；如果你记忆中的写法与此不同，请以片段为准。

## 最小可用示例

**JavaScript** [1]：

```javascript
// Human-in-the-loop requires a thread ID for persistence
const config = { configurable: { thread_id: "some_id" } };

// Agent will pause and wait for approval before executing sensitive tools
let result = await agent.invoke(
  { messages: [{ role: "user", content: "Send an email to the team" }] },
  config
);

result = await agent.invoke(
  new Command({ resume: { decisions: [{ type: "approve" }] } }),
  config  // Same thread ID to resume the paused conversation
);
```

**Python** [2]：

```python
# Human-in-the-loop requires a thread ID for persistence
config = {"configurable": {"thread_id": "some_id"}}

# Agent will pause and wait for approval before executing sensitive tools
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Send an email to the team"}]},
    config=config
)

result = agent.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config  # Same thread ID to resume the paused conversation
)
```

## 补充说明

- 暂停/恢复依赖持久化：例如 MCP 工具场景中，需要 `checkpointer=InMemorySaver()` 才能让被中断的运行有地方“等待” [3]。
- 在 deepagents 中，也可以用 `FilesystemPermission(..., mode="interrupt")` 配合 `checkpointer` 来在写入特定路径前暂停等待批准 [4]。
- 若使用 `interrupt()` 原语，暂停后可通过 `Command(resume=...)` 传回批准结果（如 `{"approved": True}`）继续执行 [5][7]。

> 说明：片段 [1][2] 只展示了“批准”的写法，未展示“拒绝”的具体取值；片段 [3] 提到 `decline` 或 `cancel` 可用于拒绝，但那是 MCP elicitation 场景的写法，不能直接等同于 [1][2] 中 `decisions` 的取值。

**top5 片段**：

片段[1] `oss__javascript__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
}); // Human-in-the-loop requires a thread ID for persistence const config = { configurable: { thread_id: "some_id" } }; // Agent will pause and wait for approval before executing sensitive tools let result = await agent.invoke( { messages: [{ role: "user", content: "Send an email to the team" }] }, config ); result = await agent.invoke( new Command({ resume: { decisions: [{ type: "approve" }] } }), config  // Same thread ID to resume the paused conversation ); ```
```

片段[2] `oss__python__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
ySaver(), ) # Human-in-the-loop requires a thread ID for persistence config = {"configurable": {"thread_id": "some_id"}} # Agent will pause and wait for approval before executing sensitive tools result = agent.invoke( {"messages": [{"role": "user", "content": "Send an email to the team"}]}, config=config ) result = agent.invoke( Command(resume={"decisions": [{"type": "approve"}]}), config=config  # Same thread ID to resume the paused conversation ) ```
```

片段[3] `oss__python__langchain__mcp__tools#015` ｜ Tools ｜ Server requests during tool execution > Elicitation

```text
= await adapter.list_tools() # Resuming a paused run needs persistence, so the interrupted run has # somewhere to wait. agent = create_agent("claude-sonnet-5", tools, checkpointer=InMemorySaver()) config: Any = {"configurable": {"thread_id": "booking-1"}} paused = await agent.ainvoke( {"messages": [{"role": "user", "content": "Book a table for 4."}]}, config ) [interrupt] = paused["__interrupt__"] [question] = interrupt.value["requests"] # Answers are keyed by the server's own request key, so nothing has to # be tracked across the pause. `decline` or `cancel` would refuse. answer = {"action": "accept", "content": {"date": "2026-09-14"}} return await agent.ainvoke(
```

片段[4] `oss__python__deepagents__permissions#003` ｜ Permissions ｜ Pause for human approval

```text
```

from deepagents import FilesystemPermission, create_deep_agent

from langgraph.checkpoint.memory import InMemorySaver



agent = create_deep_agent(

    model=model,

    permissions=[

        # Pause for approval before writing anything under /secrets.

        FilesystemPermission(

            operations=["write"],

            paths=["/secrets/**"],

            mode="interrupt",

        ),

    ],

    # Interrupt mode requires a checkpointer to pause and resume.

    checkpointer=InMemorySaver(),

)

```
```

片段[5] `oss__python__deepagents__human-in-the-loop#037` ｜ Human-in-the-loop ｜ Subagent interrupts > Interrupts within tool calls

```text
``` from langchain.agents import create_agent from langchain_anthropic import ChatAnthropic from langchain.messages import HumanMessage from langchain.tools import tool from langgraph.checkpoint.memory import InMemorySaver from langgraph.types import Command, interrupt from deepagents.graph import create_deep_agent from deepagents.middleware.subagents import CompiledSubAgent @tool(description="Request human approval before proceeding with an action.") def request_approval(action_description: str) -> str: """Request human approval using the interrupt() primitive.""" # interrupt() pauses execution and returns the value passed to Command(resume=...) approval = interrupt({ "type":
```

---

## v1-D-018（multi-hop）

**问题**：openwiki 的 --init 和 --update 到底该在什么时候用？是不是有些选项只能配在 update 上？

**gold**：--init 用于生成初始文档（默认 code mode），重跑会从零重建 wiki 但保留 openwiki/INSTRUCTIONS.md；--update 只更新已有文档，两者不能同时使用。确实有只在 update 上有效的选项：deferUnplannedClaimIssues 默认 false，开启后跳过给有 Claim 问题的未规划页面自动建任务，在 init run 上设置会返回 invalid_input 错误。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. `--init` 用于生成初始文档，默认是 code 模式；重复执行会从头重新生成仓库 wiki，但会保留 `openwiki/INSTRUCTIONS.md` [1]。
2. `--update` 用于更新已有文档，默认也是 code 模式 [1]。
3. `--init` 和 `--update` **不能同时使用** [1]。
4. 是的，确实有选项只能配在 update 上：`deferUnplannedClaimIssues` 仅在 update 运行中有效，在 init 运行中设置会返回 `invalid_input` 错误 [6]。

**最小可用示例**

```bash
# 初始化（默认 code 模式）
openwiki --init

# 更新（默认 code 模式）
openwiki --update

# 显式 code 模式
openwiki code --init
openwiki code --update
openwiki code --update --print

# 指定语言初始化
openwiki --init --language ko
```

**补充说明**

- `openwiki/INSTRUCTIONS.md` 是用户编写的范围与优先级说明，OpenWiki 在 init 和 update 时都会读取它；正常的 `--init` 和 `--update` 运行不会重写它 [2]。
- 在 TTY 中且不带 `--print` 时，`--init` / `--update` 会流式输出 agent 内容并在成功后自动退出 [1]。
- 片段中 `deferUnplannedClaimIssues` 的描述出现了重复表述（同一句说了两遍），但核心结论一致：仅 update 可用，init 上使用会报 `invalid_input` [6]。

**top5 片段**：

片段[1] `oss__openwiki__cli-reference#002` ｜ Command reference ｜ Core commands > Common flags

```text
| Flag | Description | | --- | --- | | --init | Generate initial documentation. Defaults to code mode. Re-running regenerates the repository wiki from scratch while preserving openwiki/INSTRUCTIONS.md . In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | --update | Update existing documentation. Defaults to code mode. In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | -l , --language <locale> | Generate wiki documentation in the given BCP-47 locale, for example ko , zh-CN , or pt-BR . Unrecognized values are rejected. |
```

片段[2] `oss__openwiki__code-mode#003` ｜ Code mode ｜ What code mode produces

```text
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
```

片段[3] `oss__openwiki__personal-mode#001` ｜ Personal mode ｜ ROOT

```text
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
```

片段[4] `oss__openwiki__code-mode#001` ｜ Code mode ｜ ROOT

```text
```

openwiki code --init

openwiki code --update

openwiki code --update --print

```
```

片段[5] `oss__openwiki__cli-reference#000` ｜ Command reference ｜ Core commands

```text
``` # Interactive chat in code mode (current repository) openwiki openwiki "Please generate documentation for this repository" # Personal mode openwiki personal openwiki personal --init openwiki personal --update # Explicit code mode openwiki code --init openwiki code --update openwiki code --update --print # Defaults to code mode and specify a language openwiki --init openwiki --update openwiki --init --language ko # One-shot print mode openwiki -p "Summarize what you can do" # Explore the wiki locally or export a static visualizer openwiki visualize openwiki visualize openwiki --port 4400 --no-open openwiki visualize openwiki --export docs/openwiki-visualizer
```

---

## v1-D-019（multi-hop）

**问题**：deep agents 做文档 RAG 时检索环节有哪几种做法？示例代码里的切分和向量库是怎么配的？

**gold**：一种做法是 skills-guided retrieval：agent 先加载一个描述该怎么搜这个语料的 skill（用哪个 index、query 怎么组织、引用格式），再按这份指引调用检索工具并综合作答。示例代码里用 RecursiveCharacterTextSplitter 按 chunkSize 1000、chunkOverlap 200 切分文档，用 text-embedding-3-small 做 embedding 存进 MemoryVectorStore，检索时 similaritySearch 取 4 条。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：给出的文档片段只能确认 Deep Agents 的 RAG 包含「skills-guided retrieval」这一种检索做法，以及一个把文档分块卸载到文件系统、交给子代理分析的教程模式；但**没有**给出示例代码里切分策略和向量库的具体配置。

**检索环节的做法**

- Skills-guided retrieval：用户提问后，代理加载一个相关 skill，该 skill 描述如何检索语料库（用哪个索引、如何构造查询、引用格式），代理按该指引调用检索工具，然后综合出答案 [9][10]。
- 片段 [1][2] 还提到 RAG 模式包括 skills-guided retrieval、rubric grading，以及一个教程：索引 LangChain 文档、把 chunks 卸载到文件系统、把分析委派给子代理 [1][2]。但 rubric grading 的具体检索做法在片段中没有展开。

**示例代码里的切分与向量库配置**

给出的文档里没有找到能回答这个问题的内容。缺的是：

- 示例代码中使用的切分器类型与参数（片段 [4][5] 只说明 chunking 页面涵盖 recursive、token-based、structure-aware、semantic chunking、small-to-big 等策略，但没有示例里的具体配置）[4][5]。
- 向量库/索引的具体选型与初始化参数。片段 [3][11] 只显示 `create_deep_agent` 的 `tools=[search_documentation]`、`backend=backend`、`subagents=[chunk_analyst_subagent]` 等，未出现向量库配置 [3][11]。

**片段中可见的相关代码（非切分/向量库部分）**

Python 侧 [3][11]：

```python
model = init_chat_model(model="anthropic:claude-sonnet-4-6")
agent = create_deep_agent(
    model=model,
    tools=[search_documentation],
    backend=backend,
    system_prompt=INSTRUCTIONS,
    subagents=[chunk_analyst_subagent],
)
```

JavaScript 侧 [6][7][8]：

```javascript
const maxConcurrentAnalysts = 3;
const instructions = RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=".repeat(80) + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.replace(
  "{max_concurrent_analysts}",
  String(maxConcurrentAnalysts),
);
const chunkAnalystSubagent = {
  name: "chunk-analyst",
  description: "Analyze one retrieved documentation chunk file. ...",
};
```

另外提示一处名称差异：你问的是「deep agents」，片段中的实际 API 名为 `create_deep_agent`，子代理名为 `chunk-analyst`，检索工具在示例中叫 `search_documentation` [3][6][11]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__rag#000` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ ROOT

```text
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
```

片段[2] `oss__python__deepagents__rag#000` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ ROOT

```text
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
```

片段[3] `oss__python__deepagents__rag#088` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Full code

```text
lapping facts and deduplicate source URLs. - Prefer concrete steps and code-oriented guidance from the documentation.""" max_concurrent_analysts = 3 INSTRUCTIONS = ( RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.format( max_concurrent_analysts=max_concurrent_analysts, ) ) chunk_analyst_subagent = { "name": "chunk-analyst", "description": ( "Analyze one retrieved documentation chunk file. " "Pass the user question and a single file path under /retrieved/." ), "system_prompt": CHUNK_ANALYST_INSTRUCTIONS, } model = init_chat_model(model="anthropic:claude-sonnet-4-6") agent = create_deep_agent( model=model, tools=[search_documentation],
```

片段[4] `oss__python__langchain__chunking#000` ｜ Chunk documents for retrieval ｜ ROOT

```text
Chunk documents for retrieval Choose a chunking strategy for RAG in LangChain, including recursive and token-based splitting, structure-aware and semantic chunking, small-to-big retrieval, and chunk metadata.
```

片段[5] `oss__javascript__langchain__chunking#000` ｜ Chunk documents for retrieval ｜ ROOT

```text
Chunk documents for retrieval Choose a chunking strategy for RAG in LangChain, including recursive and token-based splitting, structure-aware and semantic chunking, small-to-big retrieval, and chunk metadata.
```

---

## v1-D-020（paraphrase）

**问题**：我不想让派出去的子 agent 看到主对话里那一大段历史，最好它只看见我这次交给它的活，默认是这样吗？

**gold**：是的，默认就是。子 agent 的 mode 默认为 isolated，这种情况下它只能看到被委派的那项任务；如果想让它继承父 agent 的对话和 system prompt，才需要显式设成 fork。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：是的，默认就是这样。** 子 agent 默认使用 `"isolated"` 模式，只收到被委派的任务描述，不会看到父对话的历史，相当于全新开始 [1][2][4][5][6][7]。

补充要点：
- 默认模式名为 `"isolated"`（isolated 是默认值）[1][2][4][5][6][7]。
- 若想反过来让子 agent 继承父对话历史，需要显式设置 `mode: "fork"` [4][5][9][11]。
- 权衡：isolated 能保持上下文隔离，但子 agent 需要重新推导父 agent 已经做过的事情 [6][7]。

**最小可用示例（JavaScript，显式写出默认值）：**

```ts
const asyncSubagents: AsyncSubAgent[] = [
  {
    name: "drafter",
    description: "Drafts documents based on the conversation context",
    graphId: "drafter",
    mode: "isolated", // 默认值，只传任务描述，不带父对话历史
  },
];
```

（`mode: "fork"` 的写法见片段 [9]；Python 对应写法见片段 [11]。）

**top5 片段**：

片段[1] `oss__javascript__deepagents__async-subagents#030` ｜ Async subagents ｜ Choose a launch mode

```text
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
```

片段[2] `oss__python__deepagents__async-subagents#018` ｜ Async subagents ｜ Choose a launch mode

```text
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
```

片段[3] `oss__javascript__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[4] `oss__javascript__deepagents__overview#028` ｜ Deep Agents overview ｜ Delegation > Subagents

```text
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
```

片段[5] `oss__python__deepagents__overview#036` ｜ Deep Agents overview ｜ Delegation > Subagents

```text
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
```

---

## v1-D-021（paraphrase）

**问题**：我在 skill 里挂的自定义工具，模型要是不先读 SKILL.md、直接猜工具名硬调，会怎么样？

**gold**：会失败。skill 里的工具是 gated 的：在 agent 读到那个 skill 的 SKILL.md 之前，调用会被当成 unknown tool，即使模型猜对了名字和参数也一样。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：会失败，调用会被当作未知工具处理。** 即使模型猜对了工具名和参数，只要 agent 还没读过该 skill 的 `SKILL.md`，对 skill 工具的调用就会以「unknown tool」失败 [1][2]。

补充几点相关行为：

- skill 工具是「门控」的：只有 agent 读过 `SKILL.md` 之后，这些工具才会出现 [1][2][3][4]。
- 如果后续摘要（summarization）把这次「读取」从对话中丢弃，工具会再次变为不可用，直到 agent 重新读取该 skill [3][4][9][11]。
- 另一种让工具可用的方式是「pin」该 skill：效果等同于读取其 `SKILL.md`，工具会一直可用，直到摘要丢弃被 pin 的 skill 消息 [5][6]。

**最小示例（Python，来自片段）：**

```python
from deepagents import create_deep_agent
from deepagents.middleware import SkillsMiddleware

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    backend=backend,
    middleware=[
        SkillsMiddleware(
            backend=backend,
            sources=["/skills/"],
            tools=[list_issues, create_issue],
        ),
    ],
)
```

（片段 [12] 的代码块开头被截断，以上按可见部分整理；完整写法请以原文档为准。）

**排障提示**：如果发现 skill 工具不可用，先检查 agent 是否真的读过该 skill——工具只在读过 `SKILL.md` 后出现，并在摘要丢弃该读取后消失 [3][4]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[2] `oss__python__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[3] `oss__python__deepagents__skills#131` ｜ Skills ｜ Troubleshooting > Skill tool not available

```text
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
```

片段[4] `oss__javascript__deepagents__skills#131` ｜ Skills ｜ Troubleshooting > Skill tool not available

```text
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
```

片段[5] `oss__javascript__deepagents__skills#024` ｜ Skills ｜ Add tools to skills

```text
- Pinning a skill makes its tools available the same way reading its SKILL.md does. They stay available until summarization drops the pinned skill’s message.
```

---

## v1-D-022（paraphrase）

**问题**：整页网页原文丢给模型太烧 token 了，有没有现成的 loader 能顺手把网页压小一点？

**gold**：有，DomPruner 就是干这个的：它做 DOM AST 剪枝，把网页加载成紧凑的 Markdown，文档说能做到 97%+ 的 token reduction，而且不需要 API key。同一类需求里 Firecrawl 走另一条路，直接把网站变成 LLM-ready 的数据，支持 scrape、crawl、map、extract、search。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：有。文档里列出了一个专门做网页压缩的 loader：**DomPruner**，它通过 DOM AST 剪枝把网页加载为紧凑的 Markdown，号称 97%+ token 削减，且不需要 API key [3]。另外 DomPrunerLoader 也出现在 document loaders 总表里 [1][9]。

需要注意的差异/限制：
- 片段只给了名称和一句简介，**没有给出 DomPruner 的导入路径、类名用法或参数**，所以无法给出可运行的调用示例。
- 片段里同类网页 loader 还有 Firecrawl、Hyperbrowser、ProxyHatLoader 等，但它们的描述是抓取/爬取/代理，并未说明会压缩 token [3]。

最小可用示例：给出的文档里没有 DomPruner 的具体 API 用法，无法提供代码示例。若你只是想要“按 token 切块”来控制上下文，片段里有 TokenTextSplitter 的用法（注意这是切分器，不是 loader）：

```javascript
import { TokenTextSplitter } from "@langchain/textsplitters";

const splitter = new TokenTextSplitter({
  encodingName: "cl100k_base",
  chunkSize: 256, // target chunk size (tokens)
  chunkOverlap: 32, // overlap (tokens)
});

const chunks = await splitter.splitDocuments(docs);
```
[5]

缺失内容：DomPruner/DomPrunerLoader 的导入方式与参数说明。

**top5 片段**：

片段[1] `oss__python__integrations__document_loaders#013` ｜ Document loader integrations ｜ All document loaders

```text
ader |  | | DiffbotCrawlLoader |  | | DiffbotExtractLoader |  | | DomPrunerLoader |  | | PolarisAIDataInsightLoader |  | | ProxmintLoader |  | | Google memorystore for Redis |  | | PyMuPDFLayoutLoader |  | | OpeddFeedLoader |  | | langchain_box |  | | AnyToMarkdownLoader |  | | Web2MDLoader |  | | PaddleOCR-VL |  | | AlfrescoLoader |  | | OpenDMALoader |  | | CommentScraperLoader |  | | Google Classroom |  | | Google cloud SQL for mysql |  | | Kinetica document loader |  | | Google firestore in datastore mode |  | | AgentQLLoader |  | | CVFileLoader |  | | ProxyHatLoader |  | | AirbyteLoader |  | | CapslaneLoader |  | | PdfmuseLoader |  | | LyrenthLoader |  | | PlasmateSOMLLoader |  |
```

片段[2] `oss__javascript__integrations__splitters#009` ｜ Text splitter integrations ｜ Length-based

```text
```

import { TokenTextSplitter } from "@langchain/textsplitters";



const splitter = new TokenTextSplitter({ encodingName: "cl100k_base", chunkSize: 100, chunkOverlap: 0 })

const texts = splitter.splitText(document)

```
```

片段[3] `oss__python__integrations__document_loaders#012` ｜ Document loader integrations ｜ All document loaders

```text
DoclingLoader |  | | Azure blob storage loader |  | | FlatmarkLoader |  | | FirecrawlLoader |  | | OpenDocKitLoader |  | | OpenDataLoader PDF |  | | AnakinLoader |  | | Docugami |  | | HwpHwpxLoader |  | | PDFParser |  | | SingleStoreLoader |  | | YoutubeLoaderDL |  | | SuperPDFLoader |  | | MeshArcLoader |  | | HyperbrowserLoader |  | | FastOCRLoader |  | | ReplyLayerLoader |  | | HydrafetchLoader |  | | SecureLangChainLoader |  | | SpidraLoader |  | | PdfInspectorLoader |  | | WebCrawlerAPILoader |  | | CrwLoader |  | | Google bigtable |  | | Outline |  | | MinerULoader |  | | DiffbotCrawlLoader |  | | DiffbotExtractLoader |  | | DomPrunerLoader |  | | PolarisAIDataInsightLoader |  |
```

片段[4] `oss__python__integrations__document_loaders#004` ｜ Document loader integrations ｜ By category > Webpages

```text
fbot Extract API | API | | Docling | Uses Docling to load and parse web pages | Package | | DomPruner | DOM AST pruning: loads web pages as compact Markdown with 97%+ token reduction, no API key | Package | | Firecrawl | Turns websites into clean, LLM-ready data via scrape/crawl/map/extract/search | API | | Hyperbrowser | Platform for running and scaling headless browsers, can be used to scrape/crawl any site | API | | OpeddFeedLoader | Load a licensed Opedd content catalog as Documents with licensing provenance | API | | ProxyHatLoader | Load web pages through ProxyHat residential proxies as Documents | API |
```

片段[5] `oss__javascript__langchain__quickstart#037` ｜ Quickstart ｜ Build a real-world agent

```text
"fetch_text_from_url", description: "Fetch the document from a URL.", schema: z.object({ url: z.string().url() }), }, ); const model = await initChatModel("gemini-3.1-pro-preview", { modelProvider: "google", temperature: 0.5, timeout: 600_000, maxTokens: 25000, streaming: true, }); const checkpointer = new MemorySaver(); async function main() { const agent = createAgent({ model, tools: [fetchTextFromUrl], systemPrompt: SYSTEM_PROMPT, checkpointer, }); const deepAgent = createDeepAgent({ model, tools: [fetchTextFromUrl], systemPrompt: SYSTEM_PROMPT, checkpointer, }); const content = `Project Gutenberg hosts a full plain-text copy of F. Scott Fitzgerald's The Great Gatsby. URL:
```

---

## v1-D-023（paraphrase）

**问题**：openwiki 页面上的生成时间戳，如果我只改了 frontmatter、正文一个字没动，它会往前走吗？

**gold**：不会。更新时只要正文有变化（哪怕只是空白字符）时间戳就会前进；正文没变则保留之前那次事件，只改 front-matter 不推进它。新页面和刚初始化的页面会带上 generated: {by, at}，producer 记为 openwiki/<version>。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不会。** 只改 front-matter、正文完全没动时，生成时间戳不会前进；只有正文（body）发生变化——包括空白字符的变化——才会推进时间戳 [1]。

补充两点片段里的相关说明：
- 正文未变时，页面保留之前的事件（prior event）[1]。
- 生产者会被标记为 `openwiki/<version>`（或 coding-agent host）[1]。

**最小示例（示意，非片段原文代码）：**

```yaml
# 只改 front matter，例如：
type: concept        # 改动前
type: guide          # 改动后 —— 正文未变，generated.at 不前进
```

```markdown
正文内容保持不变
```

```yaml
# 正文哪怕只多一个空格，也会推进时间戳：
generated:
  by: openwiki/<version>
  at: <更新后的时间>
```

**差异提示：** 你问的是「生成时间戳」，片段 [1] 中的字段写作 `generated: {by, at}`，其中 `at` 即时间戳、`by` 为生产者；片段未使用「生成时间戳」这一中文命名，以片段字段名为准 [1]。

**top5 片段**：

片段[1] `oss__openwiki__code-mode#010` ｜ Code mode ｜ Open Knowledge Format

```text
- New and freshly initialized pages receive generated: {by, at} . During updates, any body change, including whitespace, advances the stamp; an unchanged body retains its prior event, and front-matter-only changes do not advance it. The producer is stamped as openwiki/<version> (or the coding-agent host)
```

片段[2] `oss__openwiki__code-mode#002` ｜ Code mode ｜ What code mode produces

```text
- openwiki/ : Generated Markdown wiki (quickstart, architecture, operations, and related topics)
```

片段[3] `oss__openwiki__code-mode#003` ｜ Code mode ｜ What code mode produces

```text
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
```

片段[4] `oss__openwiki__customize#002` ｜ Customize OpenWiki ｜ Agent instruction files

```text
- AGENTS.md : Created when missing. OpenWiki rewrites only the <!-- OPENWIKI:START --> … <!-- OPENWIKI:END --> block and leaves the rest of your content untouched
```

片段[5] `oss__openwiki__customize#003` ｜ Customize OpenWiki ｜ Agent instruction files

```text
- CLAUDE.md : Updated only when the file already exists. The managed block imports @AGENTS.md so Claude Code reads the same instructions. OpenWiki does not create CLAUDE.md when it is absent, and it leaves a file that is only @AGENTS.md unchanged
```

---

## v1-D-024（no-answer）

**问题**：Haystack 2.x 里 Pipeline.run 的 include_outputs_from 参数该怎么写？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段全部是 LangChain / LangGraph 的前端流式渲染（`useStream`、`injectStream`、`PipelineProgress` 组件、`SubgraphDiscoverySnapshot` 状态等）以及 LangChain 模型结构化输出的 `include_raw` 参数，没有任何关于 Haystack 2.x 或 `Pipeline.run` 的 `include_outputs_from` 参数的说明。

要回答这个问题，需要补充：Haystack 2.x `Pipeline.run` 的 API 文档片段，特别是 `include_outputs_from` 参数的类型、默认值和用法示例。

另外提醒一处名称差异：片段 [3] 中出现的是 LangChain 的 `include_raw=True`（用于同时获取解析结果和原始 AI 消息），与您问的 Haystack `include_outputs_from` 不是同一个 API，不能据此推断。

**top5 片段**：

片段[1] `oss__python__langgraph__frontend__graph-execution#008` ｜ Graph execution ｜ Building the pipeline progress bar

```text
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
```

片段[2] `oss__javascript__langgraph__frontend__graph-execution#008` ｜ Graph execution ｜ Building the pipeline progress bar

```text
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
```

片段[3] `oss__python__langchain__models#044` ｜ Models ｜ Structured output

```text
- Include raw : Set include_raw=True to get both the parsed output and the raw AI message.
```

片段[4] `oss__javascript__langgraph__frontend__graph-execution#005` ｜ Graph execution ｜ Setting up useStream

```text
``` import { Component, computed } from "@angular/core"; import { injectStream } from "@langchain/angular"; const AGENT_URL = "http://localhost:2024"; @Component({ selector: "app-pipeline-chat", template: ` <div> <app-pipeline-progress [nodes]="graphNodes()" [isLoading]="stream.isLoading()" /> <app-node-card-list [nodes]="graphNodes()" [stream]="stream" [isLoading]="stream.isLoading()" /> </div> `, }) export class PipelineChatComponent { stream = injectStream<typeof myAgent>({ apiUrl: AGENT_URL, assistantId: "graph_execution_cards", }); graphNodes = computed(() => [...this.stream.subgraphs().values()]); } ```
```

片段[5] `oss__python__langgraph__frontend__graph-execution#005` ｜ Graph execution ｜ Setting up useStream

```text
``` import { Component, computed } from "@angular/core"; import { injectStream } from "@langchain/angular"; const AGENT_URL = "http://localhost:2024"; @Component({ selector: "app-pipeline-chat", template: ` <div> <app-pipeline-progress [nodes]="graphNodes()" [isLoading]="stream.isLoading()" /> <app-node-card-list [nodes]="graphNodes()" [stream]="stream" [isLoading]="stream.isLoading()" /> </div> `, }) export class PipelineChatComponent { stream = injectStream<typeof myAgent>({ apiUrl: AGENT_URL, assistantId: "graph_execution_cards", }); graphNodes = computed(() => [...this.stream.subgraphs().values()]); } ```
```

---

## v1-D-025（no-answer）

**问题**：LangSmith 企业版的 SLA 承诺几个 9？超时赔付怎么算？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段只涉及 LangSmith 的用途与配置（如 tracing 可选/必选、设置 `LANGSMITH_TRACING=false` 关闭追踪、API Key 配置等）[2][3][4][5][8][11][15]，没有任何关于「企业版 SLA 承诺几个 9」或「超时赔付计算方式」的条款、指标或商务说明。缺少的是：LangSmith 企业版的 SLA 文档/服务条款，以及赔付（service credit）计算规则相关内容。

**top5 片段**：

片段[1] `oss__javascript__langchain__multi-agent__skills-sql-assistant#031` ｜ Build a SQL assistant with on-demand skills ｜ 5. Test progressive disclosure

```text
```

import { uuid7 } from "langsmith";

// Configuration for this conversation thread

const threadId = uuid7();

const config = { configurable: { thread_id: threadId } };



// Ask for a SQL query

const result = await agent.invoke(  

  {

    messages: [

      {

        role: "user",

        content:

          "Write a SQL query to find all customers " +

          "who made orders over $1000 in the last month",

      },

    ],

  },

  config

);



// Print the conversation

for (const message of result.messages) {

  console.log(`${message._getType()}: ${message.content}`);

}

```
```

片段[2] `oss__javascript__deepagents__deep-research#001` ｜ Build a deep research agent ｜ Prerequisites

```text
- LangSmith for tracing (optional if you are using the SDK; required for Managed Deep Agents)
```

片段[3] `oss__python__deepagents__deep-research#001` ｜ Build a deep research agent ｜ Prerequisites

```text
- LangSmith for tracing (optional if you are using the SDK; required for Managed Deep Agents)
```

片段[4] `oss__javascript__deepagents__content-builder#003` ｜ Build a content builder agent ｜ Prerequisites

```text
- LangSmith for tracing (optional on the SDK path; required for Managed Deep Agents)
```

片段[5] `oss__python__deepagents__content-builder#003` ｜ Build a content builder agent ｜ Prerequisites

```text
- LangSmith for tracing (optional on the SDK path; required for Managed Deep Agents)
```

---

## v2-E-001（single-hop）

**问题**：我们要在回复用户前把邮箱打码成只留后四位，另外在日志里换成不可逆的一串字符，PII 策略表里这两种分别叫什么、示例输出长什么样？

**gold**：只留后四位属于 mask，示例是 ****-****-****-1234；不可逆替换属于 hash，用确定性哈希，示例是 a8f5f167...。同一张表里还有 redact（替换为 [REDACTED_{PII_TYPE}]，例如 [REDACTED_EMAIL]）和 block（检测到就 Raise exception）。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- “只留后四位”对应策略 **`mask`**，示例输出形如 `****-****-****-1234` [1][2]。
- “换成不可逆的一串字符”对应策略 **`hash`**，示例输出形如 `a8f5f167...` [1][2]。

补充说明（以片段为准）：

- 片段里 `mask` 的描述是 “Partially obscure (e.g., last 4 digits)”，示例是 `****-****-****-1234` [1][2]。注意示例是卡号形态，片段没有单独给出邮箱 mask 后的具体样子。
- `hash` 的描述是 “Replace with deterministic hash”，示例是 `a8f5f167...` [1][2]。片段只说是确定性哈希，没有说明具体算法，也没有承诺“不可逆”这一措辞——你的说法与片段描述存在差异，片段仅写 deterministic hash。
- 另外 `redact` 是替换为 `[REDACTED_{PII_TYPE}]`（如 `[REDACTED_EMAIL]`），`block` 是检测到即抛异常 [1][2]，这两个不是你要的。

**最小可用示例（Python，来自片段 [6]）：**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="gpt-6.1-sol",
    tools=[customer_service_tool, email_tool],
    middleware=[
        # Redact emails in user input before sending to model
        PIIMiddleware(
            "email",
            strategy="redact",
            apply_to_input=True,
        ),
        # Mask credit cards in user input
        PIIMiddleware(
            "credit_card",
            strategy="mask",
            apply_to_input=True,
        ),
        # Block API keys - raise error if detected
        PIIMiddleware(
            "api_key",
            detector=r"sk-[a-zA-Z0-9]{32}",
            strategy="block",
            apply_to_input=True,
        ),
    ],
)
```

按你的需求，把 email 那条的 `strategy` 改成 `"mask"`（回复前打码）或 `"hash"`（日志里换哈希）即可；参数名以片段为准：Python 是 `strategy`、`apply_to_input` [8]，JS 是 `strategy`、`applyToInput` [9]。片段中 `apply_to_output` 默认 `False`，若要处理“回复用户前”的输出，需要显式开启 [8][9]。

**top5 片段**：

片段[1] `oss__python__langchain__guardrails#000` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
| Strategy | Description | Example |

| --- | --- | --- |

| redact | Replace with [REDACTED_{PII_TYPE}] | [REDACTED_EMAIL] |

| mask | Partially obscure (e.g., last 4 digits) | ****-****-****-1234 |

| hash | Replace with deterministic hash | a8f5f167... |

| block | Raise exception when detected | Error thrown |
```

片段[2] `oss__javascript__langchain__guardrails#000` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
| Strategy | Description | Example |

| --- | --- | --- |

| redact | Replace with [REDACTED_{PII_TYPE}] | [REDACTED_EMAIL] |

| mask | Partially obscure (e.g., last 4 digits) | ****-****-****-1234 |

| hash | Replace with deterministic hash | a8f5f167... |

| block | Raise exception when detected | Error thrown |
```

片段[3] `oss__python__langchain__guardrails#002` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
, ) # When user provides PII, it will be handled according to the strategy result = agent.invoke({ "messages": [{"role": "user", "content": "My email is john.doe@example.com and card is 5105-1051-0510-5100"}] }) ```
```

片段[4] `oss__python__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[customer_service_tool, email_tool], middleware=[ # Redact emails in user input before sending to model PIIMiddleware( "email", strategy="redact", apply_to_input=True, ), # Mask credit cards in user input PIIMiddleware( "credit_card", strategy="mask", apply_to_input=True, ), # Block API keys - raise error if detected PIIMiddleware( "api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block", apply_to_input=True, ), ], ) # When user provides PII, it will be handled according to the strategy result = agent.invoke({ "messages": [{"role":
```

片段[5] `oss__javascript__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` import { createAgent, piiMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [customerServiceTool, emailTool], middleware: [ // Redact emails in user input before sending to model piiMiddleware("email", { strategy: "redact", applyToInput: true, }), // Mask credit cards in user input piiMiddleware("credit_card", { strategy: "mask", applyToInput: true, }), // Block API keys - raise error if detected piiMiddleware("api_key", { detector: /sk-[a-zA-Z0-9]{32}/, strategy: "block", applyToInput: true, }), ], }); // When user provides PII, it will be handled according to the strategy const result = await agent.invoke({ messages: [{ role: "user", content:
```

---

## v2-E-002（single-hop）

**问题**：同一个 agent 上我要同时做关键词拦截、邮箱在输入和输出两侧都脱敏、敏感工具真人审批、事后模型安全审查，中间件该怎么叠？PII 那个默认管输出吗？

**gold**：叠法是 ContentFilterMiddleware(banned_keywords=["hack", "exploit"]) 做确定性输入过滤，然后两条 PIIMiddleware("email", strategy="redact", apply_to_input=True) 与 apply_to_output=True 分别管输入与输出，再用 HumanInTheLoopMiddleware(interrupt_on={"send_email": True}) 审敏感工具，最后 SafetyGuardrailMiddleware() 做模型侧审查。关键点是 PII 要注册两条并显式给 apply_to_input / apply_to_output 才覆盖两个方向。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. 可以按「输入过滤 → PII 输入/输出脱敏 → 敏感工具人工审批 → 事后模型安全审查」的顺序把多个 middleware 叠在同一个 `create_agent` 的 `middleware` 列表里 [1][2]。
2. **PII 中间件默认不管输出**：文档示例里输入侧和输出侧是分别用两个 `PIIMiddleware` 显式声明的（`apply_to_input=True` 一个、`apply_to_output=True` 一个），并没有“默认同时管两侧”的说法 [1][3]。所以你要输出侧脱敏，必须自己再加一个 `apply_to_output=True` 的实例 [1]。
3. 关键词拦截用的是 `ContentFilterMiddleware(banned_keywords=[...])`，人工审批用 `HumanInTheLoopMiddleware(interrupt_on={"send_email": True})`，事后模型审查用 `SafetyGuardrailMiddleware()` [1][8]。

**最小可用示例（Python）：**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ContentFilterMiddleware,
    PIIMiddleware,
    HumanInTheLoopMiddleware,
    SafetyGuardrailMiddleware,
)

agent = create_agent(
    model="gpt-6.1-sol",
    tools=[search_tool, send_email_tool],
    middleware=[
        # Layer 1: 关键词拦截（进 agent 前）
        ContentFilterMiddleware(banned_keywords=["hack", "exploit"]),
        # Layer 2: 邮箱脱敏——输入侧
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        # Layer 2: 邮箱脱敏——输出侧（默认不管输出，需显式声明）
        PIIMiddleware("email", strategy="redact", apply_to_output=True),
        # Layer 3: 敏感工具真人审批
        HumanInTheLoopMiddleware(interrupt_on={"send_email": True}),
        # Layer 4: 事后模型安全审查
        SafetyGuardrailMiddleware(),
    ],
)
```

**需要指出的差异/注意点：**

- 你问“PII 默认管输出吗”——按片段，**不默认**。片段 [3][7] 的示例都只写了 `apply_to_input=True`，输出侧脱敏在 [1] 里是单独一条 `apply_to_output=True` 的 middleware，说明两侧要分别配置 [1][3]。
- 片段 [1] 的 Layer 1 用的是 `ContentFilterMiddleware`，但该片段没有给出它的 import 路径；示例里我按同页命名补了 import，实际导入位置请以你所用版本为准（片段未明确）。
- JavaScript 版本对应写法是 `contentFilterMiddleware([...])`、`piiMiddleware("email", { strategy: "redact", applyToInput: true })`、`humanInTheLoopMiddleware({ interruptOn: {...} })`，参数名是驼峰式（`applyToInput` / `applyToOutput` / `interruptOn`），与 Python 的下划线风格不同 [2][4]。

**top5 片段**：

片段[1] `oss__python__langchain__guardrails#017` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, send_email_tool], middleware=[ # Layer 1: Deterministic input filter (before agent) ContentFilterMiddleware(banned_keywords=["hack", "exploit"]), # Layer 2: PII protection (before and after model) PIIMiddleware("email", strategy="redact", apply_to_input=True), PIIMiddleware("email", strategy="redact", apply_to_output=True), # Layer 3: Human approval for sensitive tools HumanInTheLoopMiddleware(interrupt_on={"send_email": True}), # Layer 4: Model-based safety check (after agent) SafetyGuardrailMiddleware(),
```

片段[2] `oss__javascript__langchain__guardrails#011` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` import { createAgent, piiMiddleware, humanInTheLoopMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, sendEmailTool], middleware: [ // Layer 1: Deterministic input filter (before agent) contentFilterMiddleware(["hack", "exploit"]), // Layer 2: PII protection (before and after model) piiMiddleware("email", { strategy: "redact", applyToInput: true, }), piiMiddleware("email", { strategy: "redact", applyToOutput: true, }), // Layer 3: Human approval for sensitive tools humanInTheLoopMiddleware({ interruptOn: { send_email: { allowAccept: true, allowEdit: true, allowRespond: true }, } }), // Layer 4: Model-based safety check (after agent)
```

片段[3] `oss__python__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[customer_service_tool, email_tool], middleware=[ # Redact emails in user input before sending to model PIIMiddleware( "email", strategy="redact", apply_to_input=True, ), # Mask credit cards in user input PIIMiddleware( "credit_card", strategy="mask", apply_to_input=True, ), # Block API keys - raise error if detected PIIMiddleware( "api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block", apply_to_input=True, ), ], ) # When user provides PII, it will be handled according to the strategy result = agent.invoke({ "messages": [{"role":
```

片段[4] `oss__javascript__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` import { createAgent, piiMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [customerServiceTool, emailTool], middleware: [ // Redact emails in user input before sending to model piiMiddleware("email", { strategy: "redact", applyToInput: true, }), // Mask credit cards in user input piiMiddleware("credit_card", { strategy: "mask", applyToInput: true, }), // Block API keys - raise error if detected piiMiddleware("api_key", { detector: /sk-[a-zA-Z0-9]{32}/, strategy: "block", applyToInput: true, }), ], }); // When user provides PII, it will be handled according to the strategy const result = await agent.invoke({ messages: [{ role: "user", content:
```

片段[5] `oss__python__langchain__guardrails#002` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
, ) # When user provides PII, it will be handled according to the strategy result = agent.invoke({ "messages": [{"role": "user", "content": "My email is john.doe@example.com and card is 5105-1051-0510-5100"}] }) ```
```

---

## v2-E-003（single-hop）

**问题**：我写了个工具想顺手把订单状态写进 state，同时让它直接结束对话；照文档用了 @tool(return_direct=True) 并返回 Command(update=...)，结果提示消息历史不合法，是漏了什么？

**gold**：漏了一条 ToolMessage。return_direct 的工具返回 Command(update={...}) 时，update 里除了自定义字段（如 last_order_status）还必须放一条 ToolMessage(content=status, tool_call_id=runtime.tool_call_id)，原文注释写的是 Must include a ToolMessage so the message history stays valid。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：漏了在 `Command(update=...)` 的 `messages` 里补一条 `ToolMessage`，并且 `tool_call_id` 要用 `runtime.tool_call_id`。文档示例里明确注释了「Must include a ToolMessage so the message history stays valid」[1]。另外注意：`return_direct=True` 是 `@tool` 装饰器的参数，而 `Command` 的 `update` 里要同时更新业务 state 和 `messages`[1]。

最小可用示例（照文档片段 [1]）：

```python
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

@tool(return_direct=True)
def fetch_and_store_order(order_id: str, runtime: ToolRuntime) -> Command:
    """Fetch order status and store it in state."""
    status = f"Order {order_id} is shipped and will arrive in 2 days."
    return Command(
        update={
            "last_order_status": status,
            # Must include a ToolMessage so the message history stays valid
            "messages": [
                ToolMessage(
                    content=status,
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

补充说明（同样来自片段）：

- 用 `Command` 更新 state 时，`messages` 里必须带 `ToolMessage`，且 `tool_call_id` 与触发本次工具调用的 id 对应，否则消息历史不合法 [1][7]。
- 如果工具签名里没有 `runtime`，就无法拿到 `runtime.tool_call_id`；片段 [2] 展示了另一种写法：用 `Annotated[str, InjectedToolCallId]` 注入 `tool_call_id`，再传给 `ToolMessage` [2]。你可以按自己工具的参数风格二选一。

如果你已经加了 `ToolMessage` 仍报错，请检查 `tool_call_id` 是否确实来自 `runtime.tool_call_id`（或注入的 `tool_call_id`），而不是自己随便填的字符串——片段里没有提供其他排查细节。

**top5 片段**：

片段[1] `oss__python__langchain__tools#034` ｜ Tools ｜ View example trace > Return a Command with return_direct

```text
``` from langchain.messages import ToolMessage from langchain.tools import ToolRuntime, tool from langgraph.types import Command @tool(return_direct=True) def fetch_and_store_order(order_id: str, runtime: ToolRuntime) -> Command: """Fetch order status and store it in state.""" status = f"Order {order_id} is shipped and will arrive in 2 days." return Command( update={ "last_order_status": status, # Must include a ToolMessage so the message history stays valid "messages": [ ToolMessage( content=status, tool_call_id=runtime.tool_call_id, ) ], } ) ```
```

片段[2] `oss__python__langchain__multi-agent__subagents#037` ｜ Subagents ｜ Context engineering > Subagent outputs

```text
``` from typing import Annotated from langchain.agents import AgentState from langchain.tools import InjectedToolCallId from langgraph.types import Command @tool( "subagent1_name", description="subagent1_description" ) def call_subagent1( query: str, tool_call_id: Annotated[str, InjectedToolCallId], ) -> Command: result = subagent1.invoke({ "messages": [{"role": "user", "content": query}] }) return Command(update={ # Pass back additional state from the subagent "example_state_key": result["example_state_key"], "messages": [ ToolMessage( content=result["messages"][-1].content, tool_call_id=tool_call_id ) ] }) ```
```

片段[3] `oss__python__langgraph__fault-tolerance#029` ｜ Fault tolerance ｜ Recovery strategies > LLM-recoverable errors

```text
``` from typing import Literal from langgraph.types import Command from typing_extensions import TypedDict class ToolError(Exception): """Raised when a tool call fails in a way the model can correct.""" class State(TypedDict): tool_call: str tool_result: str | None def run_tool(tool_call: str) -> str: if tool_call == "bad": raise ToolError("invalid args") return f"ok:{tool_call}" def execute_tool(state: State) -> Command[Literal["agent", "execute_tool"]]: try: result = run_tool(state["tool_call"]) return Command(update={"tool_result": result}, goto="agent") except ToolError as e: # Let the LLM see what went wrong and try again return Command( update={"tool_result": f"Tool error: {e}"},
```

片段[4] `oss__python__langchain__short-term-memory#032` ｜ Short-term memory ｜ Access memory > Tools > Write short-term memory from tools

```text
" else "Unknown user" return Command(update={ "user_name": name, # update the message history "messages": [ ToolMessage( "Successfully looked up user information", tool_call_id=runtime.tool_call_id ) ] }) @tool def greet( runtime: ToolRuntime[CustomContext, CustomState] ) -> str | Command: """Use this to greet the user once you found their info.""" user_name = runtime.state.get("user_name", None) if user_name is None: return Command(update={ "messages": [ ToolMessage( "Please call the 'update_user_info' tool it will get and update the user's name.", tool_call_id=runtime.tool_call_id ) ] }) return f"Hello {user_name}!" agent = create_agent( model="gpt-5-nano", tools=[update_user_info, greet],
```

片段[5] `oss__javascript__langchain__short-term-memory#031` ｜ Short-term memory ｜ Access memory > Tools > Write short-term memory from tools

```text
``` import { tool, createAgent, ToolMessage, type ToolRuntime } from "langchain"; import { Command, StateSchema } from "@langchain/langgraph"; import * as z from "zod"; const CustomState = new StateSchema({ userId: z.string().optional(), userName: z.string().optional(), }); const updateUserInfo = tool( async (_, config: ToolRuntime<typeof CustomState.State>) => { const userId = config.state.userId; const name = userId === "user_123" ? "John Smith" : "Unknown user"; return new Command({ update: { userName: name, // update the message history messages: [ new ToolMessage({ content: "Successfully looked up user information", tool_call_id: config.toolCall?.id ?? "", }), ], }, }); }, { name:
```

---

## v2-E-004（single-hop）

**问题**：工具里要读「这次调用传进来、运行期不该被改」的 user id，又要读当前会话里自己维护的计数器，运行时上下文里这两类分别叫什么？

**gold**：调用时传入、运行期不变的配置是 Context（immutable configuration passed at invocation time，常放 user IDs、session info）；当前会话内可变的是 State，即短期记忆，装 messages、counters 与自定义字段。要跨会话长期存活的数据则放 Store。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 片段里只说明了「per-run data」用 `context_schema` 定义、通过 `runtime.context` 读取 [1][2]，以及工具里可以同时读 `runtime.state`（图状态）和 `runtime.context`（运行期上下文）[5]。
- 但没有任何片段把「这次调用传进来、运行期不该被改的 user id」和「当前会话里自己维护的计数器」这两类数据分别命名、归类，也没有说明计数器应放在 state 还是 context 里。
- 片段 [10] 只提到 `thread_id` 用于持久化和恢复消息历史，并未涉及计数器存放位置。

另外指出一处与问题措辞相关的差异：片段中运行期上下文相关字段的写法是 `context_schema` / `contextSchema`（JS 侧为 `contextSchema`）[1][9]，读取方式是 `runtime.context` [1][2][5][6][7]；片段里没有出现「运行时上下文里两类分别叫什么」的命名说明。

**top5 片段**：

片段[1] `oss__javascript__deepagents__going-to-production#009` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- context : per-run data your tools and middleware read at invocation time, for example user_id , API keys, feature flags, or session metadata. Define the shape with context_schema and access it via runtime.context . See Runtime context .
```

片段[2] `oss__python__deepagents__going-to-production#009` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- context : per-run data your tools and middleware read at invocation time, for example user_id , API keys, feature flags, or session metadata. Define the shape with context_schema and access it via runtime.context . See Runtime context .
```

片段[3] `oss__javascript__langchain__human-in-the-loop#005` ｜ Human-in-the-loop ｜ Set the interrupt mode

```text
- "per_call" : Each tool call that needs review raises its own interrupt as it starts. Each interrupt carries a response_schema of the answers it accepts. You answer it with one decision, keyed by the interrupt ID.
```

片段[4] `oss__python__langchain__human-in-the-loop#005` ｜ Human-in-the-loop ｜ Set the interrupt mode

```text
- "per_call" : Each tool call that needs review raises its own interrupt as it starts. Each interrupt carries a response_schema of the answers it accepts. You answer it with one decision, keyed by the interrupt ID.
```

片段[5] `oss__python__langgraph__workflows-agents#037` ｜ Workflows and agents ｜ Agents > ToolNode > Access graph state and context from tools

```text
``` from dataclasses import dataclass from langchain.messages import AIMessage from langchain.tools import ToolRuntime, tool from langgraph.graph import MessagesState, START, StateGraph from langgraph.prebuilt import ToolNode class State(MessagesState): user_id: str @dataclass class Context: organization_id: str @tool def get_user_info(runtime: ToolRuntime[Context, State]) -> str: """Look up user information.""" # Read the current graph state passed to the ToolNode. user_id = runtime.state["user_id"] # Read explicit per-run values that are not part of graph state. organization_id = runtime.context.organization_id return f"User {user_id} in organization {organization_id}"
```

---

## v2-E-005（single-hop）

**问题**：工具日志里想把同一次调用和它后面触发的模型调用串起来，运行时上下文里该用哪个字段？想按第几次重试改变行为又该看哪个？

**gold**：串调用链用 Tool Call ID：唯一标识当前这次工具调用，用途写的是 correlate tool calls for logs and model invocations。想看重试就用 Execution Info，它给出当前执行的 thread ID、run ID 与 attempt number。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答这个问题的内容。

具体缺什么：

1. **“把同一次工具调用和它后面触发的模型调用串起来”该用哪个字段**：片段 [5] 只列出了运行时上下文可访问的几类信息（Stream Writer、Execution Info、Server Info、Config、Tool Call ID），其中提到 Tool Call ID 是“Unique identifier for the current tool invocation”，用途是“Correlate tool calls for logs and model invocations”[5]。但片段没有说明模型调用侧是否也暴露同一个 Tool Call ID、以及具体字段名是什么，因此无法确认“串起来”的准确字段。

2. **“按第几次重试改变行为”该看哪个**：片段 [5] 的 Execution Info 一行提到包含“Identity and retry information for the current execution (thread ID, run ID, attempt number)”，用途包括“adjust behavior based on retry state”[5]。这暗示应看 Execution Info 里的 attempt number，但片段没有给出该字段的准确名称和访问路径（例如 runtime 上的具体属性），所以不能给出确定答案。

另外提示一处可能的名称差异：片段 [5] 中该列标题写作 “edge base”（疑似截断/排版问题），并未出现 “runtime.context” 之类的完整访问方式；而 [3][4] 中的 `runtime.context` 是用于 per-run 数据（user_id、API keys 等），与“工具调用关联 ID / 重试次数”不是同一类内容，不能混用。

**top5 片段**：

片段[1] `oss__python__langchain__context-engineering#018` ｜ Context engineering in agents ｜ Response Format > Messages

```text
- Use life-cycle hooks like before_model , after_model , or wrap_tool_call (for tool returns) to update the conversation history. See the middleware documentation for more details.
```

片段[2] `oss__javascript__langchain__context-engineering#017` ｜ Context engineering in agents ｜ Response Format > Messages

```text
- Use life-cycle hooks like beforeModel , afterModel , or wrapToolCall (for tool returns) to update the conversation history. See the middleware documentation for more details.
```

片段[3] `oss__javascript__deepagents__going-to-production#009` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- context : per-run data your tools and middleware read at invocation time, for example user_id , API keys, feature flags, or session metadata. Define the shape with context_schema and access it via runtime.context . See Runtime context .
```

片段[4] `oss__python__deepagents__going-to-production#009` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- context : per-run data your tools and middleware read at invocation time, for example user_id , API keys, feature flags, or session metadata. Define the shape with context_schema and access it via runtime.context . See Runtime context .
```

片段[5] `oss__python__langchain__tools#009` ｜ Tools ｜ Access context

```text
edge base | | Stream Writer | Emit real-time updates during tool execution | Show progress for long-running operations | | Execution Info | Identity and retry information for the current execution (thread ID, run ID, attempt number) | Access thread/run IDs, adjust behavior based on retry state | | Server Info | Server-specific metadata when running on LangSmith Agent Server (assistant ID, graph ID, authenticated user) | Access assistant ID, graph ID, or authenticated user info | | Config | RunnableConfig for the execution | Access callbacks, tags, and metadata | | Tool Call ID | Unique identifier for the current tool invocation | Correlate tool calls for logs and model invocations |
```

---

## v2-E-006（single-hop）

**问题**：结构化输出解析失败时框架默认怎么处理？我想换成自己写的错误说明，还要能区分「格式不对」和「一次返回了多个结构」，参数怎么给？

**gold**：默认是 handle_errors=True，把错误交回模型重试。要自定义就给 handle_errors 传一个函数（签名形如 custom_error_handler(error: Exception) -> str），返回值会被当成工具消息回给模型；函数内部可用 isinstance 区分 StructuredOutputValidationError（格式问题）与 MultipleStructuredOutputsError（返回了多个结构），分别给不同提示。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. 在 Tool calling 策略下，`ToolStrategy` 的 `handle_errors` 默认是 `True`，即默认会处理错误（重试/回传错误信息给模型），而不是直接抛出 [1][7]。
2. 想换成自己写的错误说明，就把 `handle_errors` 传成一个自定义处理函数，函数接收 `Exception`、返回字符串作为错误说明 [1]。
3. 要区分「格式不对」和「一次返回了多个结构」，在函数里用 `isinstance` 判断 `StructuredOutputValidationError`（格式问题）和 `MultipleStructuredOutputsError`（多个结构化输出）[1]。
4. 注意：片段里 `handle_errors` 除了可传函数，也可传异常类型元组来指定对哪些异常重试，例如 `handle_errors=(ValueError, TypeError)` [8]；这与「传函数自定义说明」是两种用法，别混用。

**最小可用示例**（Python，来自 [1]）

```python
from langchain.agents.structured_output import StructuredOutputValidationError
from langchain.agents.structured_output import MultipleStructuredOutputsError

def custom_error_handler(error: Exception) -> str:
    if isinstance(error, StructuredOutputValidationError):
        return "There was an issue with the format. Try again."
    elif isinstance(error, MultipleStructuredOutputsError):
        return "Multiple structured outputs were returned. Pick the most relevant one."
    else:
        return f"Error: {str(error)}"

agent = create_agent(
    model="gpt-6.1-sol",
    tools=[],
    response_format=ToolStrategy(
        schema=Union[ContactInfo, EventDetails],
        handle_errors=custom_error_handler
    )  # Default: handle_errors=True
)
```

**补充说明（与你的说法可能不一致处）**

- 片段中参数名是 `response_format`（Python）[1]，不是 `responseFormat`；JS 侧示例用的是 `responseFormat` [12]，注意语言差异。
- 片段 [1] 的 `ToolStrategy(...)` 写法与片段 [7] 的 `Strategy(...)` 写法并存，二者出现在同一页相邻片段，片段本身未说明二者关系，建议以 [1] 的 `ToolStrategy` 为准。
- 另外，模型「拒绝」时结构化输出会抛 `ModelRefusalError`（Python [5]；JS 侧需 `includeRaw: true` 才不抛 [2]），这属于另一类错误，不在上述两个 `isinstance` 分支覆盖范围内，片段未给出在 `handle_errors` 中处理它的示例。

**top5 片段**：

片段[1] `oss__python__langchain__structured-output#046` ｜ Structured output ｜ Tool calling strategy > Error handling > Error handling strategies

```text
``` from langchain.agents.structured_output import StructuredOutputValidationError from langchain.agents.structured_output import MultipleStructuredOutputsError def custom_error_handler(error: Exception) -> str: if isinstance(error, StructuredOutputValidationError): return "There was an issue with the format. Try again." elif isinstance(error, MultipleStructuredOutputsError): return "Multiple structured outputs were returned. Pick the most relevant one." else: return f"Error: {str(error)}" agent = create_agent( model="gpt-6.1-sol", tools=[], response_format=ToolStrategy( schema=Union[ContactInfo, EventDetails], handle_errors=custom_error_handler )  # Default: handle_errors=True )
```

片段[2] `oss__javascript__langchain__models#048` ｜ Models ｜ Structured output

```text
- Refusals : If the model refuses, structured output throws ModelRefusalError , unless you set includeRaw: true . See Handle a model refusal and Structured output .
```

片段[3] `oss__javascript__langchain__structured-output#035` ｜ Structured output ｜ Handle parsing errors in chains

```text
- Model-level structured output : Bind the schema to the model with withStructuredOutput . When the provider supports native structured output, it enforces the schema and avoids most parsing failures. See Models - Structured output . Use this approach when the model supports it.
```

片段[4] `oss__python__langchain__structured-output#053` ｜ Structured output ｜ Handle parsing errors in chains

```text
- Model-level structured output : Bind the schema to the model with with_structured_output . When the provider supports native structured output, it enforces the schema and avoids most parsing failures. See Models - Structured output . Use this approach when the model supports it.
```

片段[5] `oss__python__langchain__models#046` ｜ Models ｜ Structured output

```text
- Refusals : If the model refuses, structured output raises ModelRefusalError . See Handle a model refusal and Structured output .
```

---

## v2-E-007（single-hop）

**问题**：轨迹评测的 mode 里，我想卡「只许调用参考里出现过的工具、多一个都不行」和「至少把参考里的工具都调用到、多调无妨」，这两个分别是什么？想要结构一致但顺序随便该用哪个？

**gold**：「不许多调」是 subset：只调用参考里出现过的工具（no extras），用来确保 agent 不越界；「至少覆盖」是 superset：允许额外调用，用来验证最低必需动作都做了。结构与工具调用一致但顺序任意用 unordered，严格同序用 strict。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

- 「只许调用参考里出现过的工具、多一个都不行」对应 **subset** 模式 [1][2]。
- 「至少把参考里的工具都调用到、多调无妨」对应 **superset** 模式 [1][2]。
- 「结构一致但顺序随便」对应 **unordered** 模式 [1][2]。

各模式说明（以片段为准）：

| 需求 | Mode | 片段描述 |
| --- | --- | --- |
| 只调用参考中的工具，不允许额外工具 | subset | "Agent calls only tools from reference (no extras)" [1][2] |
| 至少调用参考中的工具，允许额外工具 | superset | "Agent calls at least the reference tools (extras allowed)" [1][2] |
| 消息结构和工具调用与参考一致，但工具调用顺序任意 | unordered | "Same message structure and tool calls as reference, but tool calls can happen in any order" [1][2] |

补充说明：strict 模式要求消息结构和工具调用顺序完全一致（消息内容可以不同）[1][2]，所以如果你要「顺序随便」，不应选 strict，而应选 unordered。

最小可用示例（Python，来自片段 [3][4] 的写法）：

```python
from agentevals.trajectory.match import create_trajectory_match_evaluator

# 只允许参考中的工具，多一个都不行
subset_evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="subset",
)

# 至少调用参考中的工具，多调无妨
superset_evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="superset",
)

# 结构一致但顺序随便
unordered_evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="unordered",
)
```

片段 [3] 还给出了 strict 模式的调用形式 `create_trajectory_match_evaluator(trajectory_match_mode="strict")` [3]，[4] 给出了 superset 模式的调用形式 [4]，可作为同一 API 的参数写法参考。

**top5 片段**：

片段[1] `oss__javascript__langchain__test__evals#003` ｜ Agent Evals ｜ Trajectory match evaluator

```text
| Mode | Description | Use case |

| --- | --- | --- |

| strict | Exact match of message structure and tool calls in the same order (message content can differ) | Testing specific sequences (e.g., policy lookup before authorization) |

| unordered | Same message structure and tool calls as reference, but tool calls can happen in any order | Verifying information retrieval when order doesn’t matter |

| subset | Agent calls only tools from reference (no extras) | Ensuring agent doesn’t exceed expected scope |

| superset | Agent calls at least the reference tools (extras allowed) | Verifying minimum required actions are taken |
```

片段[2] `oss__python__langchain__test__evals#003` ｜ Agent Evals ｜ Trajectory match evaluator

```text
| Mode | Description | Use case |

| --- | --- | --- |

| strict | Exact match of message structure and tool calls in the same order (message content can differ) | Testing specific sequences (e.g., policy lookup before authorization) |

| unordered | Same message structure and tool calls as reference, but tool calls can happen in any order | Verifying information retrieval when order doesn’t matter |

| subset | Agent calls only tools from reference (no extras) | Ensuring agent doesn’t exceed expected scope |

| superset | Agent calls at least the reference tools (extras allowed) | Verifying minimum required actions are taken |
```

片段[3] `oss__python__langchain__test__evals#005` ｜ Agent Evals ｜ Trajectory match evaluator

```text
``` evaluator = create_trajectory_match_evaluator( trajectory_match_mode="strict", ) def test_weather_tool_called_strict(): result = agent.invoke({ "messages": [HumanMessage(content="What's the weather in San Francisco?")] }) reference_trajectory = [ HumanMessage(content="What's the weather in San Francisco?"), AIMessage(content="", tool_calls=[ {"id": "call_1", "name": "get_weather", "args": {"city": "San Francisco"}} ]), ToolMessage(content="It's 75 degrees and sunny in San Francisco.", tool_call_id="call_1"), AIMessage(content="The weather in San Francisco is 75 degrees and sunny."), ] evaluation = evaluator( outputs=result["messages"], reference_outputs=reference_trajectory ) # {
```

片段[4] `oss__python__langchain__test__evals#009` ｜ Agent Evals ｜ Trajectory match evaluator

```text
``` @tool def get_detailed_forecast(city: str): """Get detailed weather forecast for a city.""" return f"Detailed forecast for {city}: sunny all week." agent = create_agent("claude-sonnet-4-6", tools=[get_weather, get_detailed_forecast]) evaluator = create_trajectory_match_evaluator( trajectory_match_mode="superset", ) def test_agent_calls_required_tools_plus_extra(): result = agent.invoke({ "messages": [HumanMessage(content="What's the weather in Boston?")] }) # Reference only requires get_weather, but agent may call additional tools reference_trajectory = [ HumanMessage(content="What's the weather in Boston?"), AIMessage(content="", tool_calls=[ {"id": "call_1", "name":
```

片段[5] `oss__javascript__langchain__test__evals#010` ｜ Agent Evals ｜ Trajectory match evaluator

```text
t = await agent.invoke({ messages: [new HumanMessage("What's the weather in Boston?")] }); const referenceTrajectory = [ new HumanMessage("What's the weather in Boston?"), new AIMessage({ content: "", tool_calls: [ { id: "call_1", name: "get_weather", args: { city: "Boston" } }, ] }), new ToolMessage({ content: "It's 75 degrees and sunny in Boston.", tool_call_id: "call_1" }), new AIMessage("The weather in Boston is 75 degrees and sunny."), ]; const evaluation = await evaluator({ outputs: result.messages, referenceOutputs: referenceTrajectory, }); expect(evaluation.score).toBe(true); } ```
```

---

## v2-E-008（single-hop）

**问题**：跑真实模型的 agent 测试老是跟着回答措辞变红，怎么断言才稳？

**gold**：断言结构而不是内容：从 result["messages"] 里筛出所有带 tool_calls 的消息并摊平，assert any(tc["name"] == "get_weather" ...) 确认目标工具被调用过；再断言 isinstance(messages[-1], AIMessage) 且 len(messages[-1].content) > 0，不要拿具体文案做相等比较。

**judge 分**：0.0　**拒答标记**：None

**回答**：

**结论：** 给出的文档里没有找到能直接回答「如何让 agent 测试断言不受回答措辞影响」的完整方案。片段只提供了两类相关线索，但都不足以构成稳定断言的通用做法：

1. 片段提到「需要确定性、不被模型改写/总结/加工的输出」这一场景 [1][2]，以及「工具输出本身就是完整、可直接展示给用户的答案」这一场景 [10][12]——这暗示当断言依赖精确输出时，应让结果走确定性路径而非让模型自由措辞，但片段没有给出具体的断言写法。
2. 片段给出了 LLM-as-judge 的轨迹评估示例，用 `create_trajectory_llm_as_judge` / `createTrajectoryLLMAsJudge` 配合 `TRAJECTORY_ACCURACY_PROMPT`，断言的是 `evaluation["score"] is True` 而非文本相等 [3][5]。这是一种「用模型判分代替字符串比对」的思路，但片段只展示了轨迹质量评估，没有说明它是否/如何用于规避措辞波动。

**缺失的内容：** 片段没有说明如何对最终回答做语义等价断言、如何配置 judge 的评分维度、也没有任何关于「措辞无关断言」的专门章节。因此无法据此给出可靠的通用断言方案。

**最小可用示例（仅按片段原样，Python 轨迹评估）[3]：**

```python
from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

evaluator = create_trajectory_llm_as_judge(
    model="openai:gpt-5.4-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT,
)

def test_trajectory_quality():
    result = agent.invoke({
        "messages": [HumanMessage(content="What's the weather in Seattle?")]
    })
    evaluation = evaluator(outputs=result["messages"])
    assert evaluation["score"] is True
```

**名称差异提示：** 用户说的「断言」在片段中对应的是 `evaluation["score"] is True`（Python）[3] 与 `expect(evaluation.score).toBe(true)`（JavaScript）[5]；函数名在 Python 为 `create_trajectory_llm_as_judge` [3]，在 JavaScript 为 `createTrajectoryLLMAsJudge` [5]，注意不要混用。

**top5 片段**：

片段[1] `oss__javascript__langchain__tools#022` ｜ Tools ｜ View example trace

```text
- You need deterministic, unmodified output: the model cannot rephrase, summarize, or act on the tool result.
```

片段[2] `oss__python__langchain__tools#033` ｜ Tools ｜ View example trace

```text
- You need deterministic, unmodified output: the model cannot rephrase, summarize, or act on the tool result.
```

片段[3] `oss__python__langchain__test__evals#011` ｜ Agent Evals ｜ LLM-as-judge evaluator

```text
```

from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT



evaluator = create_trajectory_llm_as_judge(

    model="openai:gpt-5.4-mini",

    prompt=TRAJECTORY_ACCURACY_PROMPT,

)



def test_trajectory_quality():

    result = agent.invoke({

        "messages": [HumanMessage(content="What's the weather in Seattle?")]

    })



    evaluation = evaluator(

        outputs=result["messages"],

    )

    assert evaluation["score"] is True

```
```

片段[4] `oss__python__deepagents__streaming#049` ｜ Streaming ｜ Custom updates

```text
f'Analysis of "{topic}": Customer sentiment is 85% positive, ' "driven by product quality and support response times." ) agent = create_deep_agent( model="fireworks:accounts/fireworks/models/glm-5p2", system_prompt=( "You are a coordinator. For any analysis request, you MUST delegate " "to the analyst subagent using the task tool. Never try to answer directly. " "After receiving the result, summarize it in one sentence." ), subagents=[ { "name": "analyst", "description": "Performs data analysis with real-time progress tracking", "system_prompt": ( "You are a data analyst. You MUST call the analyze_data tool " "for every analysis request. Do not use any other tools. "
```

片段[5] `oss__javascript__langchain__test__evals#011` ｜ Agent Evals ｜ LLM-as-judge evaluator

```text
```

import { createTrajectoryLLMAsJudge, TRAJECTORY_ACCURACY_PROMPT } from "agentevals";



const evaluator = createTrajectoryLLMAsJudge({

  model: "openai:gpt-5.4-mini",

  prompt: TRAJECTORY_ACCURACY_PROMPT,

});



async function testTrajectoryQuality() {

  const result = await agent.invoke({

    messages: [new HumanMessage("What's the weather in Seattle?")]

  });



  const evaluation = await evaluator({

    outputs: result.messages,

  });

  expect(evaluation.score).toBe(true);

}

```
```

---

## v2-E-009（single-hop）

**问题**：集成测试要把真实 HTTP 调用录下来回放，但录像里会留明文 api key 和 authorization 头，vcr 那个 fixture 该怎么配？

**gold**：用 vcr_config 这个 pytest fixture（scope="session"）返回过滤配置：filter_headers 里加 ("authorization", "XXXX") 与 ("x-api-key", "XXXX")，filter_query_parameters 里加 ("api_key", "XXXX") 与 ("key", "XXXX")，值会被替换掉，录下来的请求就不带明文凭据。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：用 `vcr_config` fixture 返回一个字典，在 `filter_headers` 里把 `authorization` 和 `x-api-key` 替换成占位符，在 `filter_query_parameters` 里把 `api_key` 和 `key` 替换成占位符，这样录像里就不会留明文密钥 [1]。

最小可用示例（来自片段 [1]）：

```python
import pytest

@pytest.fixture(scope="session")
def vcr_config():
    return {
        "filter_headers": [
            ("authorization", "XXXX"),
            ("x-api-key", "XXXX"),
        ],
        "filter_query_parameters": [
            ("api_key", "XXXX"),
            ("key", "XXXX"),
        ],
    }
```

补充说明：
- 片段里用的是 `filter_headers` / `filter_query_parameters` 这两个键名，值都是 `(名称, 替换值)` 的元组列表，替换值统一写成 `"XXXX"` [1]。如果你记的键名或写法与此不同，以片段为准。
- 片段 [2] 还给出了 pytest 配置，启用 `vcr` marker 并设置 `addopts = "--record-mode=once"`，配合上面的 fixture 使用 [2]；片段 [8] 是同一配置的另一种写法（`[pytest]` 段）[8]。
- 片段 [10] 展示了用 `@pytest.mark.vcr()` 标记测试函数的用法 [10]。

注意：片段里没有说明 `filter_headers` 是否默认就会过滤 `authorization`，也没有给出除上述四个键之外的过滤项，这部分内容给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__python__langchain__test__integration-testing#011` ｜ Integration testing ｜ Record and replay HTTP calls

```text
```

import pytest



@pytest.fixture(scope="session")

def vcr_config():

    return {

        "filter_headers": [

            ("authorization", "XXXX"),

            ("x-api-key", "XXXX"),

        ],

        "filter_query_parameters": [

            ("api_key", "XXXX"),

            ("key", "XXXX"),

        ],

    }

```
```

片段[2] `oss__python__langchain__test__integration-testing#012` ｜ Integration testing ｜ Record and replay HTTP calls

```text
```

[pytest]

markers =

    vcr: record/replay HTTP via VCR

addopts = --record-mode=once

```
```

片段[3] `oss__python__langchain__test__integration-testing#013` ｜ Integration testing ｜ Record and replay HTTP calls

```text
```

[tool.pytest.ini_options]

markers = [

  "vcr: record/replay HTTP via VCR"

]

addopts = "--record-mode=once"

```
```

片段[4] `oss__python__langchain__test__integration-testing#004` ｜ Integration testing ｜ Manage API keys

```text
```

import os

import pytest



@pytest.fixture(autouse=True)

def check_api_keys():

    if not os.environ.get("OPENAI_API_KEY"):

        pytest.skip("OPENAI_API_KEY not set")

```
```

片段[5] `oss__python__deepagents__context-engineering#030` ｜ Context engineering in Deep Agents ｜ Runtime context

```text
``` from dataclasses import dataclass from deepagents import create_deep_agent from langchain.tools import ToolRuntime, tool @dataclass class Context: user_id: str api_key: str @tool def fetch_user_data(query: str, runtime: ToolRuntime[Context]) -> str: """Fetch data for the current user.""" user_id = runtime.context.user_id return f"Data for user {user_id}: {query}" agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", tools=[fetch_user_data], context_schema=Context, ) result = agent.invoke( {"messages": [{"role": "user", "content": "Get my recent activity"}]}, context=Context(user_id="user-123", api_key="sk-..."), ) ```
```

---

## v2-E-010（single-hop）

**问题**：agent 已经是流式返回，我另外想在中间件里把「另一个小模型判定的安全结论」实时推给前端：拿 writer 用哪个函数、发送怎么发？原文判完之后怎么用这个结果？

**gold**：用 get_stream_writer() 取到 writer，然后直接 stream_writer(result) 把结果推出去；这段里 result 来自 safety_model.bind_tools([ResponseSafety], tool_choice="any") 的 invoke。判完取 result.tool_calls[0]，若 args["evaluation"] == "unsafe" 就把 last_message 替换成拒绝语。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：

1. **拿 writer 用哪个函数**：片段 [1] 只出现了 `get_stream_writer()` 这一行调用（`stream_writer = get_stream_writer()`），但没有说明它的导入来源、返回值类型，也没有说明在中间件里应如何取得 writer 的完整用法。
2. **发送怎么发**：片段 [1] 在 `stream_writer = get_stream_writer()` 处就截断了，没有展示 `stream_writer(...)` 的调用方式、参数格式，也没有说明前端如何接收这类自定义流事件。
3. **判定结果怎么用**：片段 [1] 只定义了 `ResponseSafety` 模型和 `safety_guardrail` 函数的签名（`@after_agent(can_jump_to=["end"])`），没有展示如何调用 `safety_model` 做判定、如何解析 `ResponseSafety`、以及判定后如何返回或跳转（`can_jump_to=["end"]` 的具体语义也未说明）。

另外需要指出一处与片段不一致的地方：片段 [1] 中模型名写作 `init_chat_model("openai:gpt-6.1-sol")`，与常见模型命名不同，按规则以片段为准 [1]。

片段 [2]–[7] 内容完全相同，讲的是 `agent.stream(..., stream_mode="updates", subgraphs=True, version="v2")` 下如何区分主 agent 与子 agent 的更新（通过 `chunk["ns"]` 是否为空），与「中间件里用 writer 推送安全结论」无关，无法用于回答本问题。

建议补充以下文档内容后再问：`get_stream_writer` 的完整用法示例（含导入与调用）、`@after_agent` 中间件中向自定义流写入事件的官方示例、以及 `can_jump_to` 的说明。

**top5 片段**：

片段[1] `oss__python__langchain__streaming#040` ｜ Streaming ｜ View example trace > Streaming tool calls > Accessing completed messages

```text
``` from typing import Any, Literal from langchain.agents.middleware import after_agent, AgentState from langgraph.runtime import Runtime from langchain.messages import AIMessage from langchain.chat_models import init_chat_model from langgraph.config import get_stream_writer from pydantic import BaseModel class ResponseSafety(BaseModel): """Evaluate a response as safe or unsafe.""" evaluation: Literal["safe", "unsafe"] safety_model = init_chat_model("openai:gpt-6.1-sol") @after_agent(can_jump_to=["end"]) def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None: """Model-based guardrail: Use an LLM to evaluate response safety.""" stream_writer = get_stream_writer()
```

片段[2] `oss__python__langchain__streaming#041` ｜ Streaming ｜ View example trace > Streaming tool calls > Accessing completed messages

```text
r, Any] | None: """Model-based guardrail: Use an LLM to evaluate response safety.""" stream_writer = get_stream_writer() # Get the model response if not state["messages"]: return None last_message = state["messages"][-1] if not isinstance(last_message, AIMessage): return None # Use another model to evaluate safety model_with_tools = safety_model.bind_tools([ResponseSafety], tool_choice="any") result = model_with_tools.invoke( [ { "role": "system", "content": "Evaluate this AI response as generally safe or unsafe." }, { "role": "user", "content": f"AI response: {last_message.text}" } ] ) stream_writer(result) tool_call = result.tool_calls[0] if tool_call["args"]["evaluation"] == "unsafe":
```

片段[3] `oss__python__deepagents__streaming#011` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[4] `oss__python__deepagents__streaming#023` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[5] `oss__python__deepagents__streaming#026` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

---

## v2-E-011（single-hop）

**问题**：同一套 agent 部署在多环境，我想在调用记录上带环境名、用户 id、会话 id 和版本标签，方便按用户筛，代码里怎么传？

**gold**：在 agent.invoke 的 config 里传：tags 放用途/版本串（如 ["production", "email-assistant", "v1.0"]），metadata 放 {"user_id": "user_123", "session_id": "session_456", "environment": "production"}。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 Python 里，把环境名、用户 id、会话 id 放进 `config` 的 `metadata`，把版本标签放进 `config` 的 `tags`，然后传给 `agent.invoke(...)` 即可 [2][3]。注意：`metadata` 里的键名片段用的是 `user_id`、`session_id`、`environment`，`tags` 是字符串列表 [2][3]。

最小可用示例（Python）：

```python
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Send a welcome email"}]},
    config={
        "tags": ["production", "email-assistant", "v1.0"],
        "metadata": {
            "user_id": "user_123",
            "session_id": "session_456",
            "environment": "production"
        }
    }
)
```

补充说明：
- 如果不想在每次 `invoke` 里传，也可以用 `ls.tracing_context(...)` 包住调用，在其中传 `tags` 和 `metadata` [9][11]。
- 片段中另有一种「运行时上下文」的传法：用 `create_agent(..., context_schema=Context)` 并在 `invoke(..., context=Context(...))` 传静态上下文 [1]；这与上面用于追踪筛选的 `config.metadata` 是不同机制，片段 [8] 说明它用于「对话期间不变的静态上下文（如用户元数据）」。
- 若你用的是 JavaScript，片段 [4] 的写法是 `agent.invoke(input, { tags, metadata })`，且 metadata 键名为 `userId`、`sessionId` [4]；片段 [5] 则写成 `config: { tags, metadata }`，两处写法不一致，以你实际使用的版本为准。

**top5 片段**：

片段[1] `oss__python__migrate__langchain-v1#039` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Runtime context

```text
```

from dataclasses import dataclass



from langchain.agents import create_agent



@dataclass

class Context:

    user_id: str

    session_id: str



agent = create_agent(

    model=model,

    tools=tools,

    context_schema=Context  

)



result = agent.invoke(

    {"messages": [{"role": "user", "content": "Hello"}]},

    context=Context(user_id="123", session_id="abc")

)

```
```

片段[2] `oss__python__langchain__observability#003` ｜ LangSmith Observability ｜ Add metadata to traces

```text
```

response = agent.invoke(

    {"messages": [{"role": "user", "content": "Send a welcome email"}]},

    config={

        "tags": ["production", "email-assistant", "v1.0"],

        "metadata": {

            "user_id": "user_123",

            "session_id": "session_456",

            "environment": "production"

        }

    }

)

```
```

片段[3] `oss__python__langgraph__observability#002` ｜ LangSmith Observability ｜ Add metadata to traces

```text
```

response = agent.invoke(

    {"messages": [{"role": "user", "content": "Send a welcome email"}]},

    config={

        "tags": ["production", "email-assistant", "v1.0"],

        "metadata": {

            "user_id": "user_123",

            "session_id": "session_456",

            "environment": "production"

        }

    }

)

```
```

片段[4] `oss__python__langgraph__observability#003` ｜ LangSmith Observability ｜ Add metadata to traces

```text
```

with ls.tracing_context(

    enabled=True,

    tags=["production", "email-assistant", "v1.0"],

    metadata={"user_id": "user_123", "session_id": "session_456", "environment": "production"}):

    response = agent.invoke(

        {"messages": [{"role": "user", "content": "Send a welcome email"}]}

    )

```
```

片段[5] `oss__python__langchain__observability#004` ｜ LangSmith Observability ｜ Add metadata to traces

```text
```

with ls.tracing_context(

    enabled=True,

    tags=["production", "email-assistant", "v1.0"],

    metadata={"user_id": "user_123", "session_id": "session_456", "environment": "production"}):

    response = agent.invoke(

        {"messages": [{"role": "user", "content": "Send a welcome email"}]}

    )

```
```

---

## v2-E-012（single-hop）

**问题**：工具跑完要回模型一段人话，同时还要把结构化元数据（文档 id、页码）交给下游程序，ToolMessage 上这两样分别放哪？

**gold**：人话放 content（注释 Sent to model），结构化元数据放 artifact（注释 Artifact available downstream），例如 artifact={"document_id": "doc_123", "page": 0}；构造时还要带 tool_call_id 与 name，示例里分别是 "call_123" 与 "search_books"。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 给模型看的人话放 `content`，给下游程序用的结构化元数据放 `artifact`。`artifact` 的用途是「随工具执行结果传递、值得追踪但不发给模型」的任意数据 [2][3]。

**最小可用示例（Python）：**

```python
from langchain.messages import ToolMessage

message_content = "It was the best of times, it was the worst of times."  # 给模型
artifact = {"document_id": "doc_123", "page": 0}                          # 给下游

tool_message = ToolMessage(
    content=message_content,
    tool_call_id="call_123",
    name="search_books",
    artifact=artifact,
)
```

[1]

**补充说明：**

- `ToolMessage` 除 `role`、`content` 外，还有 `tool_call_id`（对应产生该结果的工具调用 id）和 `artifact`（不发给模型）两个字段 [2][3]。
- `tool_call_id` 必须与模型发起的工具调用 id 匹配 [4]。
- 若工具返回的是 MCP 结构化内容，适配器只在工具返回结构化内容时才设置 `artifact`，因此非 None 的 `artifact` 一定带有 `structured_content` [6]。
- JavaScript 版本写法相同，字段名一致（`content`、`tool_call_id`、`name`、`artifact`）[5]。

**与提问措辞的差异：** 你问的是「ToolMessage 上这两样分别放哪」，片段中字段名是 `content` 和 `artifact`，没有出现其他命名；请以片段为准。

**top5 片段**：

片段[1] `oss__python__langchain__messages#020` ｜ Messages ｜ Message types > Tool message

```text
```

from langchain.messages import ToolMessage



# Sent to model

message_content = "It was the best of times, it was the worst of times."



# Artifact available downstream

artifact = {"document_id": "doc_123", "page": 0}



tool_message = ToolMessage(

    content=message_content,

    tool_call_id="call_123",

    name="search_books",

    artifact=artifact,

)

```
```

片段[2] `oss__javascript__integrations__chat__anthropic#030` ｜ ChatAnthropic integration ｜ Prompt caching

```text
emMessage This represents a system message, which tells the model how to behave. Not every model provider supports this. #### ToolMessage This represents the result of a tool call. In addition to \`role\` and \`content\`, this message has: - a \`tool_call_id\` field which conveys the id of the call to the tool that was called to produce this result. - an \`artifact\` field which can be used to pass along arbitrary artifacts of the tool execution which are useful to track but which should not be sent to the model. #### (Legacy) FunctionMessage This is a legacy message type, corresponding to OpenAI's legacy function-calling API.
```

片段[3] `oss__javascript__integrations__chat__openai#045` ｜ ChatOpenAI integration ｜ Prompt caching

```text
emMessage This represents a system message, which tells the model how to behave. Not every model provider supports this. #### ToolMessage This represents the result of a tool call. In addition to \`role\` and \`content\`, this message has: - a \`tool_call_id\` field which conveys the id of the call to the tool that was called to produce this result. - an \`artifact\` field which can be used to pass along arbitrary artifacts of the tool execution which are useful to track but which should not be sent to the model. #### (Legacy) FunctionMessage This is a legacy message type, corresponding to OpenAI's legacy function-calling API.
```

片段[4] `oss__python__langchain__messages#018` ｜ Messages ｜ Message types > Tool message

```text
``` from langchain.messages import AIMessage from langchain.messages import ToolMessage # After a model makes a tool call # (Here, we demonstrate manually creating the messages for brevity) ai_message = AIMessage( content=[], tool_calls=[{ "name": "get_weather", "args": {"location": "San Francisco"}, "id": "call_123" }] ) # Execute tool and create result message weather_result = "Sunny, 72°F" tool_message = ToolMessage( content=weather_result, tool_call_id="call_123"  # Must match the call ID ) # Continue conversation messages = [ HumanMessage("What's the weather in San Francisco?"), ai_message,  # Model's tool call tool_message,  # Tool execution result ]
```

片段[5] `oss__javascript__langchain__messages#018` ｜ Messages ｜ Message types > Tool message

```text
```

import { ToolMessage } from "langchain";



// Artifact available downstream

const artifact = { document_id: "doc_123", page: 0 };



const toolMessage = new ToolMessage({

  content: "It was the best of times, it was the worst of times.",

  tool_call_id: "call_123",

  name: "search_books",

  artifact

});

```
```

---

## v2-E-013（single-hop）

**问题**：会话里那些自动插入的通知消息，source 有哪些取值？读文件时附带视频抽帧、评分器要求重写、异步子 agent 结束这三种分别对应什么 source、data 里带什么？

**gold**：分别对应 read_file_media（data 里有 path 与 tool_call_id）、rubric_grader（要求 agent 修订输出）、async_subagent（完成/失败/等输入，data 是 task event）。同一张表里还有 summarization（压缩对话历史）与 pinned_skill（把固定技能加进对话）。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：通知消息的 `source` 取值在片段中列出的有 `async_subagent`、`summarization`、`pinned_skill`、`rubric_grader`、`read_file_media`、`hitl_interrupt_decision` [1][3][10]。你问的三种情况对应如下：

- 读文件附带视频抽帧 → `read_file_media`，`data` 里有 `path` 和 `tool_call_id` [1]。
- 评分器要求重写 → `rubric_grader`，片段只说明「rubric grader 要求 agent 修改输出」，未说明 `data` 字段 [1]。
- 异步子 agent 结束 → `async_subagent`，`data` 是任务事件；示例中事件含 `agent_name` 和 `status`，`status` 可为 `success`、`error`、`timeout`、`cancelled` 或 `waiting` [1][6][7]。

最小可用示例（读取异步子 agent 通知，Python）：

```python
from langchain_core.messages import get_notification_metadata

for message in state["messages"]:
    metadata = get_notification_metadata(message)
    if metadata and metadata["source"] == "async_subagent":
        event = metadata["data"]
        print(event["agent_name"], event["status"])  # success, error, timeout, cancelled, or waiting
```

说明：片段 [1] 中 `read_file_media` 的描述是「read_file attaches frames sampled from a video file」，与「读文件时附带视频抽帧」一致；`rubric_grader` 的 `data` 内容片段未给出，无法补充。

**top5 片段**：

片段[1] `oss__python__langchain__messages#038` ｜ Messages ｜ Notifications

```text
| Source | Added when | Details |

| --- | --- | --- |

| async_subagent | An async subagent task finishes, fails, or waits for input. data is the task event. | Async subagents |

| summarization | The agent summarizes the conversation history. | Summarization |

| pinned_skill | The agent adds a pinned skill to the conversation. | Pin skills |

| rubric_grader | The rubric grader asks the agent to revise its output. | Grading rubrics |

| read_file_media | read_file attaches frames sampled from a video file. data has path and tool_call_id . | Built-in read_file tool |
```

片段[2] `oss__javascript__langchain__context-engineering#010` ｜ Context engineering in agents ｜ Response Format > Messages

```text
\n")} Reference these files when answering questions.`; // Inject file context before recent messages const messages = [ ...request.messages,  // Rest of conversation new HumanMessage(fileContext) ]; request = { ...request, messages }; } return handler(request); }, }); const agent = createAgent({ model: "gpt-6.1-sol", tools: [...], middleware: [injectFileContext], }); ```
```

片段[3] `oss__javascript__langchain__messages#036` ｜ Messages ｜ Notifications

```text
| Source | Added when | Details |

| --- | --- | --- |

| async_subagent | An async subagent task finishes, fails, or waits for input. data is the task event. | Async subagents |

| summarization | The agent summarizes the conversation history. | Summarization |

| pinned_skill | The agent adds a pinned skill to the conversation. | Pin skills |
```

片段[4] `oss__python__deepagents__streaming#058` ｜ Streaming ｜ Stream multiple modes

```text
``` # Skip internal middleware steps - only show meaningful node names INTERESTING_NODES = {"model", "tools"} last_source = "" mid_line = False  # True when we've written tokens without a trailing newline for chunk in agent.stream( {"messages": [{"role": "user", "content": "Analyze the impact of remote work on team productivity"}]}, stream_mode=["updates", "messages", "custom"], subgraphs=True, version="v2", ): is_subagent = any(s.startswith("tools:") for s in chunk["ns"]) source = "subagent" if is_subagent else "main" if chunk["type"] == "updates": for node_name in chunk["data"]: if node_name not in INTERESTING_NODES: continue if mid_line: print() mid_line = False print(f"[{source}] step:
```

片段[5] `oss__javascript__deepagents__streaming#073` ｜ Streaming ｜ Stream multiple modes

```text
; const source = isSubagent ? "subagent" : "main"; if (mode === "updates") { for (const nodeName of Object.keys(data)) { if (!INTERESTING_NODES.has(nodeName)) continue; if (midLine) { process.stdout.write("\n"); midLine = false; } console.log(`[${source}] step: ${nodeName}`); } } else if (mode === "messages") { const [message] = data; if (message.text) { // Print a header when the source changes if (source !== lastSource) { if (midLine) { process.stdout.write("\n"); midLine = false; } process.stdout.write(`\n[${source}] `); lastSource = source; } process.stdout.write(message.text); midLine = true; } } else if (mode === "custom") { if (midLine) { process.stdout.write("\n"); midLine = false; }
```

---

## v2-E-014（single-hop）

**问题**：好几个测试都要用同一个假聊天模型，每次重拼一堆预设消息太啰嗦，pytest 里怎么复用？

**gold**：用 @pytest.fixture 定义一个 weather_model，返回 FakeToolCallingModel(messages=iter([...]))；测试函数直接把它当参数（如 def test_tool_is_called(weather_model)），里面 create_agent(weather_model, tools=[get_weather]) 再 invoke。断言则筛出带 tool_calls 的 AIMessage，取第一个确认调的是目标工具。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：用 pytest fixture 把假模型封装起来复用即可。文档示例里定义了一个 `weather_model` fixture，返回 `FakeToolCallingModel`，预设消息用 `iter([...])` 传入，测试函数把 fixture 名当参数接收就能拿到同一个假模型 [1][7]。

最小可用示例（Python，来自文档）：

```python
import pytest
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolCall

@pytest.fixture
def weather_model():
    return FakeToolCallingModel(messages=iter([
        AIMessage(
            content="",
            tool_calls=[ToolCall(name="get_weather", args={"city": "Tokyo"}, id="call_1")],
        ),
        AIMessage(content="It is 72°F and sunny in Tokyo."),
    ]))

def test_tool_is_called(weather_model):
    agent = create_agent(weather_model, tools=[get_weather])
    result = agent.invoke({"messages": [HumanMessage(content="Weather in Tokyo?")]})
    tool_call_messages = [
        m for m in result["messages"]
        if isinstance(m, AIMessage) and m.tool_calls
    ]
    assert tool_call_messages[0].tool_calls[0]["name"] == "get_weather"
```

补充说明：
- 文档里 fixture 返回的是 `FakeToolCallingModel`，但片段中没有给出它的 import 来源，示例代码里也没有显式 import 它 [1][7]；如果你按此写代码，需要自行确认该类的导入路径，文档片段未覆盖。
- 注意 `messages=iter([...])` 用的是迭代器，意味着这个 fixture 的预设消息序列是一次性消耗的；若同一测试会话中多次调用，需留意文档未说明其重复使用行为 [1]。
- 若想模拟“每次调用都报错”，JS 侧文档提供 `fakeModel().alwaysThrow(...)` [5]；若想模拟“只响应一次、第二次调用抛错”，JS 侧用 `fakeModel().respond(...)` 排队响应 [3]。这些是 JavaScript 版 API，与 Python 的 `FakeToolCallingModel` 名称不同，不要混用 [1][3][5]。

**top5 片段**：

片段[1] `oss__python__langchain__test__unit-testing#005` ｜ Unit testing ｜ Share fake models with pytest fixtures

```text
``` import pytest from langchain.agents import create_agent from langchain.messages import AIMessage, HumanMessage, ToolCall @pytest.fixture def weather_model(): return FakeToolCallingModel(messages=iter([ AIMessage( content="", tool_calls=[ToolCall(name="get_weather", args={"city": "Tokyo"}, id="call_1")], ), AIMessage(content="It is 72°F and sunny in Tokyo."), ])) def test_tool_is_called(weather_model): agent = create_agent(weather_model, tools=[get_weather]) result = agent.invoke({"messages": [HumanMessage(content="Weather in Tokyo?")]}) tool_call_messages = [ m for m in result["messages"] if isinstance(m, AIMessage) and m.tool_calls ]
```

片段[2] `oss__python__langchain__test__integration-testing#001` ｜ Integration testing ｜ Separate unit and integration tests

```text
```

import pytest

from langchain.agents import create_agent

from langchain.messages import HumanMessage



@pytest.mark.integration

def test_agent_with_real_model():

    agent = create_agent("claude-sonnet-4-6", tools=[get_weather])

    result = agent.invoke({

        "messages": [HumanMessage(content="What's the weather in SF?")]

    })

    assert len(result["messages"]) > 1

```
```

片段[3] `oss__javascript__langchain__test__unit-testing#002` ｜ Unit testing ｜ Mock chat model with fakeModel > Quick start

```text
```

const model = fakeModel()

  .respond(new AIMessage("only one"));



await model.invoke([new HumanMessage("first")]);  // works

await model.invoke([new HumanMessage("second")]); // throws: "no response queued for invocation 1"

```
```

片段[4] `oss__python__contributing__code#037` ｜ Contributing to code ｜ Development workflow > Test writing guidelines

```text
```

@pytest.mark.requires("openai")

def test_openai_chat_integration():

    """Test OpenAI chat integration with real API."""



    chat = ChatOpenAI()

    response = chat.invoke("Hello")



    assert isinstance(response.content, str)

    assert len(response.content) > 0

```
```

片段[5] `oss__javascript__langchain__test__unit-testing#006` ｜ Unit testing ｜ Mock chat model with fakeModel > Simulate errors > Errors on every call

```text
```

import { fakeModel } from "langchain";

import { HumanMessage } from "@langchain/core/messages";



const model = fakeModel().alwaysThrow(new Error("service unavailable"));



await model.invoke([new HumanMessage("a")]); // throws "service unavailable"

await model.invoke([new HumanMessage("b")]); // throws "service unavailable"

```
```

---

## v2-E-015（single-hop）

**问题**：不调真模型怎么测「先调工具、再给答案」这个循环？FakeToolCallingModel 里为什么还要自己实现 bind_tools？

**gold**：FakeToolCallingModel 继承 GenericFakeChatModel，用 messages=iter([...]) 预置多轮：第一轮 AIMessage(content="", tool_calls=[ToolCall(name="get_weather", args={"city": "Tokyo"}, id="call_1")])，第二轮给最终回答，这样 agent 会真走一遍工具调用循环。bind_tools(self, tools, **kwargs) 直接 return self，因为这里要让同一个假模型继续吐预设消息而不是被换成新对象。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

**1. 怎么测「先调工具、再给答案」的循环**

用假模型按顺序预置两条消息：第一条是带 `tool_calls` 的 `AIMessage`（触发工具调用），第二条是普通 `AIMessage`（最终答案）。然后把假模型交给 `create_agent` 跑一遍，断言中间确实发生了一次工具调用、且最终回复里包含工具结果 [1][6]。

Python 侧用 `FakeToolCallingModel`（继承 `GenericFakeChatModel`），消息用 `iter([...])` 传入 [1][6]：

```python
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage, ToolCall
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

class FakeToolCallingModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self

@tool
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"72°F and sunny in {city}"

def test_agent_calls_tool_then_answers():
    model = FakeToolCallingModel(messages=iter([
        # Turn 1: the model calls the tool
        AIMessage(
            content="",
            tool_calls=[ToolCall(name="get_weather", args={"city": "Tokyo"}, id="call_1")],
        ),
        # Turn 2: the model answers using the tool result
        AIMessage(content="It is 72°F and sunny in Tokyo."),
    ]))
    agent = create_agent(model, tools=[get_weather])
    result = agent.invoke({"messages": [HumanMessage(content="Weather in Tokyo?")]})
    tool_call_messages = [
        m for m in result["messages"] if isinstance(m, AIMessage) and m.tool_calls
    ]
    assert len(tool_call_messages) == 1
    assert tool_call_messages[0].tool_calls[0]["name"] == "get_weather"
    assert "Tokyo" in result["messages"][-1].text
```

JS 侧用 `fakeModel()` 的链式写法：`.respondWithTools([...])` 预置工具调用，`.respond(new AIMessage(...))` 预置最终答案，再 `bindTools` 后手动跑循环或交给 agent [2][4][8]：

```javascript
const model = fakeModel()
  .respondWithTools([{ name: "get_weather", args: { city: "SF" }, id: "call_1" }])
  .respond(new AIMessage("It's 72°F and sunny in SF!"));
```

**2. 为什么 `FakeToolCallingModel` 里还要自己实现 `bind_tools`**

因为 agent 在构建时会先对模型调用 `bind_tools(tools)` 把工具绑定上去，而 `GenericFakeChatModel` 本身没有这个方法；不实现就会在这一步报错。这里直接 `return self`，即忽略绑定、原样返回自己，让预置的消息序列照常被消费 [1]。

## 需要指出的差异

- 你问的是 `FakeToolCallingModel`，但片段里它是**示例中自定义的类**（继承 `GenericFakeChatModel` 并覆写 `bind_tools`），不是 LangChain 内置的现成类 [1]。
- JS 侧对应的内置工具是 `fakeModel()`，提供 `.respondWithTools()` / `.respond()` 链式 API，与 Python 的 `iter([...])` 写法不同 [2][4][8]。
- 片段 [3] 展示的是真实模型下 `bind_tools` + 手动执行 `tool_calls` 的三步流程，属于生产用法，不是测试替身方案。

**top5 片段**：

片段[1] `oss__python__langchain__test__unit-testing#003` ｜ Unit testing ｜ Test a tool-calling loop

```text
``` from langchain.agents import create_agent from langchain.messages import AIMessage, HumanMessage, ToolCall from langchain.tools import tool from langchain_core.language_models.fake_chat_models import GenericFakeChatModel class FakeToolCallingModel(GenericFakeChatModel): def bind_tools(self, tools, **kwargs): return self @tool def get_weather(city: str) -> str: """Get the weather for a city.""" return f"72°F and sunny in {city}" def test_agent_calls_tool_then_answers(): model = FakeToolCallingModel(messages=iter([ # Turn 1: the model calls the tool AIMessage( content="", tool_calls=[ToolCall(name="get_weather", args={"city": "Tokyo"}, id="call_1")], ), # Turn 2:
```

片段[2] `oss__javascript__langchain__test__unit-testing#015` ｜ Unit testing ｜ Mock chat model with fakeModel > Use with bindTools

```text
= model.bindTools([getWeather]); while (true) { const response = await bound.invoke(messages); messages.push(response); if (!response.tool_calls?.length) { return { messages, finalResponse: response }; } for (const tc of response.tool_calls) { const result = await getWeather.invoke(tc.args); messages.push(new ToolMessage({ content: result as string, tool_call_id: tc.id!, })); } } } describe("weather agent", () => { test("calls get_weather and returns a final answer", async () => { const model = fakeModel() .respondWithTools([ { name: "get_weather", args: { city: "SF" }, id: "call_1" }, ]) .respond(new AIMessage("It's 72°F and sunny in SF!"));
```

片段[3] `oss__python__langchain__models#034` ｜ Models ｜ Tool calling

```text
``` # Bind (potentially multiple) tools to the model tools = [get_weather] tools_by_name = {tool.name: tool for tool in tools} model_with_tools = model.bind_tools(tools) # Step 1: Model generates tool calls messages = [{"role": "user", "content": "What's the weather in Boston?"}] ai_msg = model_with_tools.invoke(messages) messages.append(ai_msg) # Step 2: Execute tools and collect results for tool_call in ai_msg.tool_calls: # Execute the tool with the generated arguments tool = tools_by_name[tool_call["name"]] tool_result = tool.invoke(tool_call) messages.append(tool_result) # Step 3: Pass results back to model for final response final_response = model_with_tools.invoke(messages)
```

片段[4] `oss__javascript__langchain__test__unit-testing#014` ｜ Unit testing ｜ Mock chat model with fakeModel > Use with bindTools

```text
``` import { describe, test, expect } from "vitest"; import { fakeModel } from "langchain"; import { AIMessage, HumanMessage, ToolMessage } from "@langchain/core/messages"; import { tool } from "@langchain/core/tools"; import { z } from "zod"; const getWeather = tool( async ({ city }) => `72°F and sunny in ${city}`, { name: "get_weather", description: "Get weather for a city", schema: z.object({ city: z.string() }), } ); async function runAgent( model: ReturnType<typeof fakeModel>, input: string ) { const messages: any[] = [new HumanMessage(input)]; const bound = model.bindTools([getWeather]); while (true) { const response = await bound.invoke(messages); messages.push(response);
```

片段[5] `oss__javascript__langchain__test__unit-testing#012` ｜ Unit testing ｜ Mock chat model with fakeModel > Use with bindTools

```text
``` import { fakeModel } from "langchain"; import { AIMessage, HumanMessage } from "@langchain/core/messages"; import { tool } from "@langchain/core/tools"; import { z } from "zod"; const searchTool = tool(async ({ query }) => `Results for: ${query}`, { name: "search", description: "Search the web", schema: z.object({ query: z.string() }), }); const model = fakeModel() .respondWithTools([{ name: "search", args: { query: "weather" }, id: "1" }]) .respond(new AIMessage("The weather is sunny.")); const bound = model.bindTools([searchTool]); const r1 = await bound.invoke([new HumanMessage("weather?")]); console.log(r1.tool_calls[0].name); // "search"
```

---

## v2-E-016（multi-hop）

**问题**：真人审批把一个敏感工具调用拒了，会话历史里会多出什么记录？恢复执行要注意什么、我给的拒绝理由被带到哪？

**gold**：拒绝或 respond 决策会让 human-in-the-loop 中间件建一条 tool message，并在通知元数据里记一条 source 为 hitl_interrupt_decision 的记录、data 里带 decision。恢复必须用同一个 thread ID 再 invoke，决策塞进 Command(resume={"decisions": [{"type": "approve"}]})；文档强调 Human-in-the-loop requires a thread ID for persistence。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

**1. 会话历史里会多出什么记录**

当 human-in-the-loop 中间件对一次「拒绝（reject）」或「回复（respond）」决策生成工具消息时，会话历史中会新增一条来源为 `hitl_interrupt_decision` 的通知记录，其 `data` 中带有 `decision` 字段 [2][3]。

**2. 恢复执行要注意什么**

- 中断发生后，需要读取返回结果里的中断信息（Python 为 `result.interrupts`，JS 为 `result.__interrupt__`），其中包含待审批的动作请求和允许的决策类型（如 `allowed_decisions: ['approve', 'reject']`）[4][5]。
- 恢复执行时通过 `Command(...)` 传入决策来继续（片段在 `agent.invoke(Command(` 处截断，未展示完整参数）[4]。
- 在工具内部，`interrupt()` 会暂停执行，并返回传给 `Command(resume=...)` 的值；代码据此判断 `approval.get("approved")` 走批准或拒绝分支 [1][8]。

**3. 拒绝理由被带到哪**

拒绝理由会体现在工具调用的拒绝消息中，例如文档给出的响应 schema 形式为：`User rejected the tool call for \`write_file\` with reason: Write to the archive/ folder instead.` [6]。也就是说理由随该工具调用的拒绝结果一起返回/记录。

## 最小可用示例（Python，摘自片段）

```python
from langgraph.types import Command, interrupt

@tool(description="Request human approval before proceeding with an action.")
def request_approval(action_description: str) -> str:
    """Request human approval using the interrupt() primitive."""
    # interrupt() pauses execution and returns the value passed to Command(resume=...)
    approval = interrupt({
        "type": "approval_request",
        "action": action_description,
        "message": f"Please approve or reject: {action_description}",
    })
    if approval.get("approved"):
        return f"Action '{action_description}' was APPROVED. Proceeding..."
    else:
        return f"Action '{action_description}' was REJECTED. Reason: {approval.get('reason', 'No reason provided')}"
```

恢复时读取中断并传入决策（片段截断处）：

```python
print(result.interrupts)
# Interrupt(value={'action_requests': [...], 'review_configs': [...]})
agent.invoke(Command(...))
```

## 需要指出的差异 / 缺口

- 你问的「拒绝理由被带到哪」，片段只给出了拒绝消息的文本形式 [6] 和 `hitl_interrupt_decision` 通知含 `decision` 字段 [2][3]，**没有明确说明理由字段在通知 `data` 中的具体键名**，这部分给出的文档里没有找到。
- `Command(...)` 恢复时的完整参数（如何把 `approved`/`reason` 传回）在片段中被截断 [4]，无法从现有内容确认具体写法。
- Python 与 JS 的中断结构字段命名不同（Python 用 `action_requests`/`review_configs`/`allowed_decisions`，JS 用 `actionRequests`/`reviewConfigs`/`allowedDecisions`）[4][5]，使用时注意区分。

**top5 片段**：

片段[1] `oss__python__deepagents__human-in-the-loop#038` ｜ Human-in-the-loop ｜ Subagent interrupts > Interrupts within tool calls

```text
ve.""" # interrupt() pauses execution and returns the value passed to Command(resume=...) approval = interrupt({ "type": "approval_request", "action": action_description, "message": f"Please approve or reject: {action_description}", }) if approval.get("approved"): return f"Action '{action_description}' was APPROVED. Proceeding..." else: return f"Action '{action_description}' was REJECTED. Reason: {approval.get('reason', 'No reason provided')}" def main(): checkpointer = InMemorySaver() model = ChatAnthropic( model_name="claude-sonnet-4-6", max_tokens=4096, ) compiled_subagent = create_agent( model=model, tools=[request_approval], name="approval-agent", ) parent_agent = create_deep_agent(
```

片段[2] `oss__python__langchain__messages#037` ｜ Messages ｜ Notifications

```text
| Source | Added when | Details |

| --- | --- | --- |

| hitl_interrupt_decision | The human-in-the-loop middleware creates a tool message for a reject or respond decision. data has decision . | Interrupt decision types |

| summarization | The summarization middleware summarizes the conversation history. | Summarization |
```

片段[3] `oss__javascript__langchain__messages#035` ｜ Messages ｜ Notifications

```text
| Source | Added when | Details |

| --- | --- | --- |

| hitl_interrupt_decision | The human-in-the-loop middleware creates a tool message for a reject or respond decision. data has decision . | Interrupt decision types |

| summarization | The summarization middleware summarizes the conversation history. | Summarization |
```

片段[4] `oss__python__langchain__human-in-the-loop#039` ｜ Human-in-the-loop ｜ Responding to interrupts

```text
s print(result.interrupts) # > ( # >    Interrupt( # >       value={ # >          'action_requests': [ # >             { # >                'name': 'execute_sql', # >                'args': {'query': 'DELETE FROM records WHERE created_at < NOW() - INTERVAL \'30 days\';'}, # >                'description': 'Tool execution pending approval\n\nTool: execute_sql\nArgs: {...}' # >             } # >          ], # >          'review_configs': [ # >             { # >                'action_name': 'execute_sql', # >                'allowed_decisions': ['approve', 'reject'] # >             } # >          ] # >       } # >    ), # > ) # Resume with approval decision agent.invoke( Command(
```

片段[5] `oss__python__langchain__human-in-the-loop#040` ｜ Human-in-the-loop ｜ Responding to interrupts

```text
ct'] # >             } # >          ] # >       } # >    ), # > ) # Resume with approval decision agent.invoke( Command( resume={"decisions": [{"type": "approve"}]}  # or "reject" ), config=config, # Same thread ID to resume the paused conversation version="v2", ) ```
```

---

## v2-E-017（multi-hop）

**问题**：我想往对话里塞一条「后台任务跑完了」的通知，既要标出来源和附加数据、前端又要能读出来，框架给了什么读写函数？

**gold**：写用 add_notification_metadata(HumanMessage("Background task t_42 finished."), source="background_job", data={"task_id": "t_42", "status": "success"})，两者都在 langchain_core.messages 里；读用 get_notification_metadata(message)，返回 None 表示普通消息，否则可取 metadata["source"] 与 metadata.get("data")。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：框架提供了「写入通知元数据」和「读取通知元数据」两类函数，Python 与 JavaScript 各有一套，命名风格不同（snake_case vs camelCase），请按语言选用。

**写入（附加来源与数据）**
- JavaScript：`addNotificationMetadata(message, { source, data })` [1]
- Python：`add_notification_metadata(message, source=..., data=...)` [2]

**读取（前端/消费端解析）**
- JavaScript：`getNotificationMetadata(message)`，无元数据时返回 `undefined` [9]
- Python：`get_notification_metadata(message)`，无元数据时返回 `None` [11]

注意命名差异：你如果按 Python 的 `add_notification_metadata` 去 JS 里找会找不到，JS 侧是驼峰式 `addNotificationMetadata` [1][2]。

最小可用示例：

Python 写入 [2]：
```python
from langchain.messages import HumanMessage
from langchain_core.messages import add_notification_metadata

notification = add_notification_metadata(
    HumanMessage("Background task t_42 finished."),
    source="background_job",
    data={"task_id": "t_42", "status": "success"},
)
```

Python 读取 [11]：
```python
from langchain_core.messages import get_notification_metadata

for message in messages:
    metadata = get_notification_metadata(message)
    if metadata is None:
        print(message.text)  # A regular message
    else:
        print(f"[{metadata['source']}]", metadata.get("data"))
```

JavaScript 写入 [1]：
```javascript
import { HumanMessage, addNotificationMetadata } from "@langchain/core/messages";

const notification = addNotificationMetadata(
  new HumanMessage("Background task t_42 finished."),
  { source: "background_job", data: { task_id: "t_42", status: "success" } },
);
```

JavaScript 读取 [9]：
```javascript
import { getNotificationMetadata } from "@langchain/core/messages";

for (const message of messages) {
  const metadata = getNotificationMetadata(message);
  if (metadata === undefined) {
    console.log(message.text); // A regular message
  } else {
    console.log(`[${metadata.source}]`, metadata.data);
  }
}
```

补充说明：片段只覆盖了「消息上挂通知元数据 + 读取」这一层；关于前端如何把这些通知流式推送到界面，给出的文档里只有一句概述性描述（自定义 stream channel 可用 `useExtension` / `useChannel` 读取）[8]，没有具体 API 用法，无法据此给出前端读取的完整示例。

**top5 片段**：

片段[1] `oss__javascript__langchain__messages#033` ｜ Messages ｜ Notifications

```text
```

import { HumanMessage, addNotificationMetadata } from "@langchain/core/messages";



const notification = addNotificationMetadata(

  new HumanMessage("Background task t_42 finished."),

  { source: "background_job", data: { task_id: "t_42", status: "success" } },

);

```
```

片段[2] `oss__python__langchain__messages#035` ｜ Messages ｜ Notifications

```text
```

from langchain.messages import HumanMessage

from langchain_core.messages import add_notification_metadata



notification = add_notification_metadata(

    HumanMessage("Background task t_42 finished."),

    source="background_job",

    data={"task_id": "t_42", "status": "success"},

)

```
```

片段[3] `oss__javascript__integrations__chat__anthropic#031` ｜ ChatAnthropic integration ｜ Prompt caching

```text
del. #### (Legacy) FunctionMessage This is a legacy message type, corresponding to OpenAI's legacy function-calling API. \`ToolMessage\` should be used instead to correspond to the updated tool-calling API. This represents the result of a function call. In addition to \`role\` and \`content\`, this message has a \`name\` parameter which conveys the name of the function that was called to produce this result. ### Prompt templates <span data-heading-keywords="prompt,prompttemplate,chatprompttemplate"></span> Prompt templates help to translate user input and parameters into instructions for a language model.
```

片段[4] `oss__javascript__integrations__chat__openai#046` ｜ ChatOpenAI integration ｜ Prompt caching

```text
del. #### (Legacy) FunctionMessage This is a legacy message type, corresponding to OpenAI's legacy function-calling API. \`ToolMessage\` should be used instead to correspond to the updated tool-calling API. This represents the result of a function call. In addition to \`role\` and \`content\`, this message has a \`name\` parameter which conveys the name of the function that was called to produce this result. ### Prompt templates <span data-heading-keywords="prompt,prompttemplate,chatprompttemplate"></span> Prompt templates help to translate user input and parameters into instructions for a language model.
```

片段[5] `oss__python__langgraph__add-memory#016` ｜ Memory ｜ Add short-term memory > Use in production

```text
TART, "call_model") graph = builder.compile(checkpointer=checkpointer) config = { "configurable": { "thread_id": "1" } } stream = await graph.astream_events( {"messages": [{"role": "user", "content": "hi! I'm bob"}]}, config, version="v3", ) async for message in stream.messages: async for token in message.text: print(token, end="", flush=True) stream = await graph.astream_events( {"messages": [{"role": "user", "content": "what's my name?"}]}, config, version="v3", ) async for message in stream.messages: async for token in message.text: print(token, end="", flush=True) ```
```

---

## v2-E-018（multi-hop）

**问题**：我给 agent 的 state 加了自定义字段，工具里既要能读出它、又要能改掉它并让模型看到改了什么，分别怎么写？

**gold**：读：工具参数声明 runtime: ToolRuntime，用 runtime.state["user_id"] 取值，该字段声明在 class CustomState(AgentState) 里。写：让工具返回 Command(update={...})，update 里既写自定义字段（如 user_name）又放一条 ToolMessage("Successfully looked up user information", tool_call_id=runtime.tool_call_id) 更新消息历史，模型下一轮才看得到这次变动的说明。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 片段里只展示了**如何定义自定义 state**（通过 `state_schema` 或 middleware 的 `state_schema`）[3][4][8]，以及**在 middleware 的 `before_model`/`after_model` 里读写 state 字段**（如 `model_call_count`）[1][2][9][10]。
- 但没有任何片段展示**在工具（tool）函数内部读取自定义 state 字段并修改它、且让模型看到修改结果**的写法。片段 [8] 只展示了工具通过 `Annotated[CustomState, InjectedState]` **读取** `user_name`，没有展示工具**修改** state 并回传给模型的机制。
- 也没有片段说明工具修改 state 后如何让模型感知（例如通过返回值、`Command`/`update` 之类），因此无法给出可靠示例。

如果你能提供涉及「工具内更新 state」的文档片段，我可以据此补全。

**top5 片段**：

片段[1] `oss__python__migrate__langchain-v1#022` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Custom state > Defining state via middleware

```text
``` from langchain.agents.middleware import AgentState, AgentMiddleware from typing_extensions import NotRequired from typing import Any class CustomState(AgentState): model_call_count: NotRequired[int] class CallCounterMiddleware(AgentMiddleware[CustomState]): state_schema = CustomState def before_model(self, state: CustomState, runtime) -> dict[str, Any] | None: count = state.get("model_call_count", 0) if count > 10: return {"jump_to": "end"} return None def after_model(self, state: CustomState, runtime) -> dict[str, Any] | None: return {"model_call_count": state.get("model_call_count", 0) + 1} agent = create_agent( model="claude-sonnet-4-6", tools=[...],
```

片段[2] `oss__python__langchain__middleware__custom#029` ｜ Custom middleware ｜ Custom state schema

```text
{"jump_to": "end"} return None @after_model(state_schema=CustomState) def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None: return {"model_call_count": state.get("model_call_count", 0) + 1} agent = create_agent( model="gpt-6.1-sol", middleware=[check_call_limit, increment_counter], tools=[], ) # Invoke with custom state result = agent.invoke({ "messages": [HumanMessage("Hello")], "model_call_count": 0, "user_id": "user-123", }) ```
```

片段[3] `oss__python__migrate__langchain-v1#021` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Custom state > Defining state via state_schema

```text
```

from typing import Annotated

from langgraph.prebuilt import InjectedState, create_react_agent

from langgraph.prebuilt.chat_agent_executor import AgentState



class CustomState(AgentState):

    user_name: str



def greet(

    state: Annotated[CustomState, InjectedState]

) -> str:

    """Use this to greet the user by name."""

    user_name = state["user_name"]

    return f"Hello {user_name}!"



agent = create_react_agent(

    model="claude-sonnet-4-6",

    tools=[greet],

    state_schema=CustomState

)

```
```

片段[4] `oss__python__langchain__middleware__custom#028` ｜ Custom middleware ｜ Custom state schema

```text
``` from langchain.agents import create_agent from langchain.messages import HumanMessage from langchain.agents.middleware import AgentState, before_model, after_model from typing_extensions import NotRequired from typing import Any from langgraph.runtime import Runtime class CustomState(AgentState): model_call_count: NotRequired[int] user_id: NotRequired[str] @before_model(state_schema=CustomState, can_jump_to=["end"]) def check_call_limit(state: CustomState, runtime: Runtime) -> dict[str, Any] | None: count = state.get("model_call_count", 0) if count > 10: return {"jump_to": "end"} return None @after_model(state_schema=CustomState) def increment_counter(state: CustomState, runtime:
```

片段[5] `oss__python__langchain__middleware__custom#019` ｜ Custom middleware ｜ Class-based middleware > Class-based middleware

```text
- state_schema — extend the agent state with custom fields. See Custom state schema .
```

---

## v2-E-019（multi-hop）

**问题**：评测 agent 的解题轨迹：既想比对它是否严格按参考顺序调了工具，又想整体判断轨迹质量，两个评测器分别怎么建、各吃什么输入？

**gold**：严格比对用 create_trajectory_match_evaluator(trajectory_match_mode="strict")，传 outputs=result["messages"] 与 reference_outputs=参考轨迹（HumanMessage → 带 tool_calls 的 AIMessage → ToolMessage → AIMessage 的结构）。质量评估用 create_trajectory_llm_as_judge(model=..., prompt=TRAJECTORY_ACCURACY_PROMPT)，只传 outputs 就能拿到 score。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

需要两个不同的评测器：

1. **严格按参考顺序比对工具调用** → 用 **trajectory match evaluator**，`trajectory_match_mode="strict"`。strict 模式要求消息结构和工具调用顺序完全一致（消息内容可以不同）[5]。它需要传入 `outputs`（agent 实际轨迹）和 `reference_outputs`（参考轨迹）[7]。
2. **整体判断轨迹质量** → 用 **LLM-as-judge evaluator**（`create_trajectory_llm_as_judge`）。它只需要 `outputs`；若想带参考轨迹一起评判，则改用 `TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE` 并额外传 `reference_outputs` [1][6]。

**最小可用示例（Python）**

```python
from agentevals.trajectory.llm import (
    create_trajectory_llm_as_judge,
    TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
)
from agentevals.trajectory.match import create_trajectory_match_evaluator

# 1) 严格顺序比对
match_evaluator = create_trajectory_match_evaluator(
    trajectory_match_mode="strict",
)

# 2) 整体质量评判（带参考轨迹）
judge = create_trajectory_llm_as_judge(
    model="openai:gpt-5.4-mini",
    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,
)

result = agent.invoke({
    "messages": [HumanMessage(content="What's the weather in Boston?")]
})

# strict 比对：outputs + reference_outputs
match_eval = match_evaluator(
    outputs=result["messages"],
    reference_outputs=reference_trajectory,
)
assert match_eval["score"] is True

# 质量评判：outputs + reference_outputs
judge_eval = judge(
    outputs=result["messages"],
    reference_outputs=reference_trajectory,
)
```

**输入对照**

| 评测器 | 构造 | 调用输入 |
| --- | --- | --- |
| trajectory match（strict） | `create_trajectory_match_evaluator(trajectory_match_mode="strict")` [5] | `outputs`、`reference_outputs` [7] |
| LLM-as-judge（无参考） | `create_trajectory_llm_as_judge(model=..., prompt=TRAJECTORY_ACCURACY_PROMPT)` [1] | 仅 `outputs` [1] |
| LLM-as-judge（带参考） | `create_trajectory_llm_as_judge(model=..., prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE)` [6] | `outputs`、`reference_outputs` [6] |

**补充说明**

- strict 模式的定义是「消息结构和工具调用顺序完全一致，消息内容可以不同」[5]；若顺序不重要，可考虑 `unordered`，只要求工具集合一致、顺序任意 [5]。
- 异步场景有对应的 `create_async_trajectory_llm_as_judge` 和 `create_async_trajectory_match_evaluator`，调用时需 `await` [2]。
- JavaScript 侧对应 `createTrajectoryLLMAsJudge`，带参考时传 `referenceOutputs` [3][9]。

**top5 片段**：

片段[1] `oss__python__langchain__test__evals#011` ｜ Agent Evals ｜ LLM-as-judge evaluator

```text
```

from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT



evaluator = create_trajectory_llm_as_judge(

    model="openai:gpt-5.4-mini",

    prompt=TRAJECTORY_ACCURACY_PROMPT,

)



def test_trajectory_quality():

    result = agent.invoke({

        "messages": [HumanMessage(content="What's the weather in Seattle?")]

    })



    evaluation = evaluator(

        outputs=result["messages"],

    )

    assert evaluation["score"] is True

```
```

片段[2] `oss__python__langchain__test__evals#012` ｜ Agent Evals ｜ LLM-as-judge evaluator

```text
```

from agentevals.trajectory.llm import create_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE



evaluator = create_trajectory_llm_as_judge(

    model="openai:gpt-5.4-mini",

    prompt=TRAJECTORY_ACCURACY_PROMPT_WITH_REFERENCE,

)

evaluation = evaluator(

    outputs=result["messages"],

    reference_outputs=reference_trajectory,

)

```
```

片段[3] `oss__python__langchain__test__evals#013` ｜ Agent Evals ｜ LLM-as-judge evaluator > Async support

```text
```

from agentevals.trajectory.llm import create_async_trajectory_llm_as_judge, TRAJECTORY_ACCURACY_PROMPT

from agentevals.trajectory.match import create_async_trajectory_match_evaluator



async_judge = create_async_trajectory_llm_as_judge(

    model="openai:gpt-5.4-mini",

    prompt=TRAJECTORY_ACCURACY_PROMPT,

)



async_evaluator = create_async_trajectory_match_evaluator(

    trajectory_match_mode="strict",

)



async def test_async_evaluation():

    result = await agent.ainvoke({

        "messages": [HumanMessage(content="What's the weather?")]

    })



    evaluation = await async_judge(outputs=result["messages"])

    assert evaluation["score"] is True

```
```

片段[4] `oss__javascript__langchain__test__evals#011` ｜ Agent Evals ｜ LLM-as-judge evaluator

```text
```

import { createTrajectoryLLMAsJudge, TRAJECTORY_ACCURACY_PROMPT } from "agentevals";



const evaluator = createTrajectoryLLMAsJudge({

  model: "openai:gpt-5.4-mini",

  prompt: TRAJECTORY_ACCURACY_PROMPT,

});



async function testTrajectoryQuality() {

  const result = await agent.invoke({

    messages: [new HumanMessage("What's the weather in Seattle?")]

  });



  const evaluation = await evaluator({

    outputs: result.messages,

  });

  expect(evaluation.score).toBe(true);

}

```
```

片段[5] `oss__javascript__langchain__test__evals#010` ｜ Agent Evals ｜ Trajectory match evaluator

```text
t = await agent.invoke({ messages: [new HumanMessage("What's the weather in Boston?")] }); const referenceTrajectory = [ new HumanMessage("What's the weather in Boston?"), new AIMessage({ content: "", tool_calls: [ { id: "call_1", name: "get_weather", args: { city: "Boston" } }, ] }), new ToolMessage({ content: "It's 75 degrees and sunny in Boston.", tool_call_id: "call_1" }), new AIMessage("The weather in Boston is 75 degrees and sunny."), ]; const evaluation = await evaluator({ outputs: result.messages, referenceOutputs: referenceTrajectory, }); expect(evaluation.score).toBe(true); } ```
```

---

## v2-E-020（multi-hop）

**问题**：我想自己写一个 agent 说完话之后才跑的安全审查中间件：类怎么写、审查完怎么把不合格的回答替换掉？

**gold**：继承 AgentMiddleware 写类，在 __init__ 里 init_chat_model("gpt-5.4-mini") 建审查用小模型，方法上加 @hook_config(can_jump_to=["end"]) 并实现 after_agent(self, state, runtime)。审查时取 state["messages"][-1] 并确认 isinstance(last_message, AIMessage)，用 prompt 让模型只回 'SAFE' 或 'UNSAFE'，命中 UNSAFE 就把 last_message 内容改成 "I cannot provide that response. Please rephrase your request." 再 return None。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

可以。文档给出的做法是：继承 `AgentMiddleware`，用 `@hook_config(can_jump_to=["end"])` 装饰 `after_agent` 钩子，在钩子里取最后一条 `AIMessage`，调用一个模型做安全判定；若判定为 `UNSAFE`，直接改写 `last_message.content` 为拒答文案 [3][5]。

注意两点与常见说法的差异：
- 钩子名是 `after_agent`（不是 `after_model` 之类），且需要 `@hook_config(can_jump_to=["end"])` 才能跳到结束 [3]。
- 文档里判定用的是字符串匹配 `if "UNSAFE" in result.content`，而不是结构化输出；片段 [4] 里另有一个用 Pydantic `ResponseSafety` 做结构化判定的版本，但那是 streaming 页面的示例 [4]。

## 最小可用示例（Python）

```python
from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langgraph.runtime import Runtime
from langchain.messages import AIMessage
from langchain.chat_models import init_chat_model

class SafetyGuardrailMiddleware(AgentMiddleware):
    """Model-based guardrail: Use an LLM to evaluate response safety."""
    def __init__(self):
        super().__init__()
        self.safety_model = init_chat_model("gpt-5.4-mini")

    @hook_config(can_jump_to=["end"])
    def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
        if not state["messages"]:
            return None
        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage):
            return None

        safety_prompt = f"""Evaluate if this response is safe and appropriate.
Respond with only 'SAFE' or 'UNSAFE'.
Response: {last_message.content}"""
        result = self.safety_model.invoke([{"role": "user", "content": safety_prompt}])

        if "UNSAFE" in result.content:
            last_message.content = "I cannot provide that response. Please rephrase your request."
        return None
```

挂到 agent 上：

```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-6.1-sol",
    tools=[search_tool, calculator_tool],
    middleware=[SafetyGuardrailMiddleware()],
)
```

## 替换不合格回答的方式

文档的做法是**原地改写最后一条消息的 `content`**：`last_message.content = "I cannot provide that response. Please rephrase your request."`，然后 `return None` [5]。也就是说，不是返回一个新状态，而是直接修改 `state["messages"][-1]` 的内容。

## 补充说明

- 片段 [3] 的类定义只展示到取 `last_message` 为止，具体的判定与替换逻辑在片段 [5] 中给出，两者属于同一页面（After agent guardrails）[3][5]。
- 片段 [1][7] 展示了把该中间件作为「Layer 4」与其他中间件（内容过滤、PII、人工审批）组合的写法 [1][7]；JS 版本对应 `safetyGuardrailMiddleware()` [2][8]。
- 片段 [4] 的 `@after_agent(can_jump_to=["end"])` 是函数式写法，与类式写法并存，但片段未说明两者是否完全等价，此处不做推断 [4]。

**top5 片段**：

片段[1] `oss__python__langchain__guardrails#018` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
eware(interrupt_on={"send_email": True}), # Layer 4: Model-based safety check (after agent) SafetyGuardrailMiddleware(), ], ) ```
```

片段[2] `oss__javascript__langchain__guardrails#012` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
il: { allowAccept: true, allowEdit: true, allowRespond: true }, } }), // Layer 4: Model-based safety check (after agent) safetyGuardrailMiddleware(), ], }); ```
```

片段[3] `oss__python__langchain__guardrails#011` ｜ Guardrails ｜ Custom guardrails > After agent guardrails

```text
``` from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config from langgraph.runtime import Runtime from langchain.messages import AIMessage from langchain.chat_models import init_chat_model from typing import Any class SafetyGuardrailMiddleware(AgentMiddleware): """Model-based guardrail: Use an LLM to evaluate response safety.""" def __init__(self): super().__init__() self.safety_model = init_chat_model("gpt-5.4-mini") @hook_config(can_jump_to=["end"]) def after_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None: # Get the final AI response if not state["messages"]: return None last_message = state["messages"][-1]
```

片段[4] `oss__python__langchain__streaming#040` ｜ Streaming ｜ View example trace > Streaming tool calls > Accessing completed messages

```text
``` from typing import Any, Literal from langchain.agents.middleware import after_agent, AgentState from langgraph.runtime import Runtime from langchain.messages import AIMessage from langchain.chat_models import init_chat_model from langgraph.config import get_stream_writer from pydantic import BaseModel class ResponseSafety(BaseModel): """Evaluate a response as safe or unsafe.""" evaluation: Literal["safe", "unsafe"] safety_model = init_chat_model("openai:gpt-6.1-sol") @after_agent(can_jump_to=["end"]) def safety_guardrail(state: AgentState, runtime: Runtime) -> dict[str, Any] | None: """Model-based guardrail: Use an LLM to evaluate response safety.""" stream_writer = get_stream_writer()
```

片段[5] `oss__python__langchain__guardrails#015` ｜ Guardrails ｜ Custom guardrails > After agent guardrails

```text
message = state["messages"][-1] if not isinstance(last_message, AIMessage): return None # Use a model to evaluate safety safety_prompt = f"""Evaluate if this response is safe and appropriate. Respond with only 'SAFE' or 'UNSAFE'. Response: {last_message.content}""" result = safety_model.invoke([{"role": "user", "content": safety_prompt}]) if "UNSAFE" in result.content: last_message.content = "I cannot provide that response. Please rephrase your request." return None # Use the safety guardrail from langchain.agents import create_agent agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, calculator_tool], middleware=[safety_guardrail], ) result = agent.invoke({ "messages": [{"role":
```

---
