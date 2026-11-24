### 76. v1-D-001 [single-hop] score=1.0
Q: 子 agent 没有单独配置 tools 的时候，会自动拿到主 agent 的工具吗？如果我自己传了 tools 呢？
GOLD: 不传 tools 时，子 agent 默认从主 agent 继承工具。一旦显式指定 tools，就会完全覆盖掉继承来的那一套，不会两边合并，所以只放它真正需要的几个工具即可。
ANSWER: 结论：会。子 agent 默认继承主 agent 的工具；一旦你自己传了 `tools`，就会**完全覆盖**继承来的工具，而不是合并。[5]

具体来说，`tools` 字段是可选的结构化工具数组，默认从主 agent 继承；显式指定时，会整体覆盖继承的工具集。[5]

最小示例（JavaScript，字段名以片段为准）：

```javascript
const subagent = {
  name: "researcher",
  description: "Researches topics",
  // 不写 tools：默认继承主 agent 的工具
};

const subagentWithTools = {
  name: "researcher",
  description: "Researches topics",
  tools: [mySearchTool], // 指定后完全覆盖继承的工具，不会与主 agent 的工具合并
};
```

补充说明：片段里 `tools` 的类型写作 `StructuredTool[]`，出现在 JavaScript 文档路径下 [5]；如果你使用的是 Python 版本，片段中未给出对应字段的类型说明，需以 Python 文档为准。
--- 片段[1] oss__javascript__deepagents__skills#054 ---
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.
--- 片段[2] oss__python__deepagents__skills#067 ---
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.
--- 片段[3] oss__python__deepagents__subagents#007 ---
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
--- 片段[4] oss__javascript__deepagents__subagents#006 ---
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
--- 片段[5] oss__javascript__deepagents__subagents#003 ---
nts must define their own. Include tool usage guidance and output format requirements. Does not inherit from main agent. For mode: "fork" , omit this field unless you need a fork-only addendum. See Forked subagents . | | mode | "isolated" \| "fork" | Optional. Context mode. Defaults to "isolated" , where the subagent only sees the delegated task. Set to "fork" to inherit the parent’s conversation and system prompt instead. See Forked subagents . | | tools | StructuredTool[] | Optional. Tools the subagent can use. Keep this minimal and include only what’s needed. Inherits from main agent by default. When specified, overrides the inherited tools entirely. |

### 77. v1-D-002 [single-hop] score=1.0
Q: 子 agent 会继承主 agent 配的 skills 吗？它加载的 skill 会不会反过来影响主 agent？
GOLD: 不会继承：skills 默认不从主 agent 继承，只有 general-purpose 这个子 agent 会继承主 agent 的 skills。子 agent 一旦有自己的 skills，会运行独立的 SkillsMiddleware 实例，状态完全隔离，子 agent 加载过的 skill 对父 agent 不可见，反之亦然。
ANSWER: **结论：**

1. **自定义子 agent 默认不继承主 agent 的 skills**，需要在每个子 agent 定义里单独用 `skills` 参数指定自己的 skill 源路径 [1][2][3][4]。
2. **只有 general-purpose 子 agent 会自动继承主 agent 的 skills**（当给 `create_deep_agent` 传入 skills 时），无需额外配置 [1][2][5]。
3. **子 agent 加载的 skill 不会反过来影响主 agent**：子 agent 有 skills 时会运行自己独立的 `SkillsMiddleware` 实例，skill 状态完全隔离，子 agent 加载的 skills 对父 agent 不可见，反之亦然 [1][2]。

**最小可用示例（JavaScript，自定义子 agent 指定 skills）：**

```javascript
const subagent = {
  name: "researcher",
  description: "...",
  skills: ["/skills/research/", "/skills/web-search/"], // 不继承主 agent，需显式指定
};
```

**参数命名差异提示：** 你问的是「skills」，片段中确实叫 `skills`（Python 与 JavaScript 一致）[1][2]；但结构化输出参数在 JS 片段里写作 `responseFormat` [1]，在 Python 片段里写作 `response_format` [2]，两者命名不同，使用时需按对应语言区分。
--- 片段[1] oss__javascript__deepagents__subagents#006 ---
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
--- 片段[2] oss__python__deepagents__subagents#007 ---
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
--- 片段[3] oss__javascript__deepagents__skills#055 ---
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
--- 片段[4] oss__python__deepagents__skills#068 ---
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
--- 片段[5] oss__javascript__deepagents__skills#054 ---
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.

### 78. v1-D-003 [single-hop] score=0.5
Q: deep agents 的 skill 是一次性整份读进上下文，还是分阶段加载的？每一级分别读什么？
GOLD: 分三级按需加载：第一级是 SKILL.md frontmatter 里的 name 和 description，在 agent 启动时对所有已配置 skill 加载；第二级是完整的 SKILL.md 正文，在 skill 被调用时才读；第三级是 scripts/、references/、assets/ 里的支撑文件，只在正文用到它们时才读。
ANSWER: **结论：是分阶段加载的，不是一次性整份读入。** 片段只覆盖到第 2 级（Read），第 1 级及更高层级的内容在给出的文档里没有出现。

- 第 2 级 Read：当 agent 调用某个 skill 时，它通过 `read_file` 读取完整的 `SKILL.md` 内容 [1][2]。也就是说，完整正文是在“调用时”才读入的，而不是在发现阶段就整份塞进上下文。

**最小示例（示意调用时的读取动作）：**

```python
# 片段未给出调用代码，仅说明第 2 级通过 read_file 读取完整 SKILL.md
read_file(".../SKILL.md")
```

**需要说明的缺口：**
- 片段里没有描述第 1 级（以及是否存在第 3 级及以上）分别读什么，只出现了“2. Read (level 2)”这一条 [1][2]。因此“每一级分别读什么”无法完整回答，缺少第 1 级及后续层级的定义。
- 另外补充一条相关限制：发现阶段会跳过超过 10 MB 的 `SKILL.md` 文件 [4]，这与“调用时才读全文”是两回事，不要混淆。
--- 片段[1] oss__python__deepagents__skills#008 ---
2. Read (level 2): When the agent invokes a skill, it reads the full SKILL.md content via read_file .
--- 片段[2] oss__javascript__deepagents__skills#008 ---
2. Read (level 2): When the agent invokes a skill, it reads the full SKILL.md content via read_file .
--- 片段[3] oss__python__deepagents__skills#076 ---
``` from deepagents import FilesystemPermission, create_deep_agent from deepagents.backends import CompositeBackend, StateBackend, StoreBackend from langgraph.store.memory import InMemoryStore store = InMemoryStore()  # Good for local dev; omit for LangSmith Agent Server agent = create_deep_agent( model="ollama:north-mini-code-1.0", backend=CompositeBackend( default=StateBackend(), routes={ "/skills/": StoreBackend( namespace=lambda rt: ("curated-skills", rt.context.org_id), ), }, ), skills=["/skills/"], permissions=[ FilesystemPermission( operations=["write"], paths=["/skills/**"], mode="deny", ), ], store=store, ) ```
--- 片段[4] oss__javascript__deepagents__skills#126 ---
3. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
--- 片段[5] oss__python__deepagents__skills#071 ---
``` from deepagents import FilesystemPermission, create_deep_agent from deepagents.backends import CompositeBackend, StateBackend, StoreBackend from langgraph.store.memory import InMemoryStore store = InMemoryStore()  # Good for local dev; omit for LangSmith Agent Server agent = create_deep_agent( model="openai:gpt-6.1-sol", backend=CompositeBackend( default=StateBackend(), routes={ "/skills/": StoreBackend( namespace=lambda rt: ("curated-skills", rt.context.org_id), ), }, ), skills=["/skills/"], permissions=[ FilesystemPermission( operations=["write"], paths=["/skills/**"], mode="deny", ), ], store=store, ) ```

### 79. v1-D-004 [single-hop] score=0.0
Q: 为什么 deep agents 启动时只把 skill 的名字和描述放进 system prompt，而不是直接塞整份 skill 文件？
GOLD: 这是刻意保持上下文精简的设计：skills 采用 on-demand loading，启动时只读 skill 描述，等某个 skill 和当前任务匹配了才读完整文件。文档的说法是这样能在真正需要某项能力之前一直让 context 保持精简。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

片段只说明了「启动时扫描 skill 路径、解析 SKILL.md frontmatter，并把 name 和 description 注入 system prompt」这一行为 [1][2]，但没有解释**为什么**只注入名字和描述、而不注入整份文件（例如是否出于上下文长度、渐进式加载/按需读取等设计考虑）。片段 [3][4] 只提到超过 10 MB 的 SKILL.md 会在发现阶段被跳过，[5] 只给出配置 skills 路径的示例，均未涉及该设计动机。

缺失的是：关于 skills 分层加载（discovery 之后的后续层级）或设计理由的说明文档。
--- 片段[1] oss__javascript__deepagents__skills#007 ---
1. Discovery (level 1): At agent start, the middleware scans the configured skill paths, parses each SKILL.md frontmatter , and injects the name and description fields into the system prompt.
--- 片段[2] oss__python__deepagents__skills#007 ---
1. Discovery (level 1): At agent start, the middleware scans the configured skill paths, parses each SKILL.md frontmatter , and injects the name and description fields into the system prompt.
--- 片段[3] oss__javascript__deepagents__skills#126 ---
3. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
--- 片段[4] oss__python__deepagents__skills#126 ---
4. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
--- 片段[5] oss__javascript__deepagents__acp#024 ---
```

import { startServer } from "deepagents-acp";



await startServer({

  agents: {

    name: "project-agent",

    description: "Agent with project-specific knowledge",

    skills: ["./skills/", "~/.deepagents/skills/"],

    memory: ["./.deepagents/AGENTS.md"],

  },

  workspaceRoot: process.cwd(),

});

```

### 80. v1-D-005 [single-hop] score=1.0
Q: ContextHubBackend 和 Sandbox 这两种 backend 各自解决什么问题？
GOLD: ContextHubBackend 把文件持久化存进 LangSmith Hub repo，好处是不需要另外开一个 LangGraph store。Sandbox backend 则是在隔离环境里执行代码，除了文件系统工具还额外提供 execute 工具来跑 shell 命令，LangSmith、AgentCore、Daytona 等都是可选的实现。
ANSWER: **结论：**

- **ContextHubBackend** 解决的是「持久化存储」问题：它把 agent 的文件（skills、memories 等持久化上下文）存到 LangSmith Hub 仓库里，每次写入都有版本历史，并且无需额外单独配置 LangGraph store [1][2]。
- **Sandbox** 解决的是「隔离执行」问题：它在隔离环境中执行代码，提供文件系统工具以及用于运行 shell 命令的 `execute` 工具 [2][4]。

**最小可用示例（来自片段）：**

```python
# ContextHubBackend：持久化存储到 LangSmith Hub
agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=ContextHubBackend("my-agent"))
```

```python
# Sandbox：隔离环境执行代码
agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox)
```

**补充说明：** 片段中 Sandbox 的可选集成包括 LangSmith、AgentCore、Daytona 等 [2]。另外片段 [5] 提到，可通过 thread metadata 在 agent backend 与 API server 之间共享 sandbox 解析结果，确保两者解析到同一环境 [5]。
--- 片段[1] oss__python__releases__changelog#029 ---
- ContextHubBackend ( blog ): A new filesystem backend backed by LangSmith Hub. Agent files — skills, memories, and other persisted context — are stored as Hub commits, giving you version history on every write and LangSmith-native durability without provisioning a separate LangGraph store.
--- 片段[2] oss__python__deepagents__backends#003 ---
s is great for storing longer term memories or instructions that are applicable to the agent over multiple executions. | | Context Hub | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=ContextHubBackend("my-agent")) Stores files durably in a LangSmith Hub repo, without provisioning a separate LangGraph store. | | Sandbox | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox) Execute code in isolated environments. Sandboxes provide filesystem tools plus the execute tool for running shell commands. Choose from LangSmith, AgentCore, Daytona, or other sandbox integrations . |
--- 片段[3] oss__javascript__deepagents__backends#003 ---
s is great for storing longer term memories or instructions that are applicable to the agent over multiple executions. | | Context Hub | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=ContextHubBackend("my-agent")) Stores files durably in a LangSmith Hub repo, without provisioning a separate LangGraph store. | | Sandbox | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox) Execute code in isolated environments. Sandboxes provide filesystem tools plus the execute tool for running shell commands. Choose from LangSmith, AgentCore, Daytona, or other sandbox integrations . |
--- 片段[4] oss__python__deepagents__overview#020 ---
- Sandbox backends expose an execute tool for shell commands in an isolated environment.
--- 片段[5] oss__python__deepagents__frontend__sandbox#045 ---
- Share sandbox resolution between the agent backend and the API server via thread metadata so both resolve the same environment with no in-memory caches.

### 81. v1-D-006 [single-hop] score=0.5
Q: 多轮对话里 thread_id 到底管什么？我想另起一个全新会话该怎么弄？
GOLD: thread_id 通过 config 里的 configurable 传入，是这段对话的稳定标识，checkpointer 用它持久化和恢复消息历史，所以后续轮次还能接上同一个会话。想开新对话就生成一个新的 thread_id。
ANSWER: ## 结论

**thread_id 的作用**：它是这段对话的稳定标识符。checkpointer 用它来持久化和恢复消息历史，因此后续轮次能延续同一段对话；生成一个新的 thread_id 就会开启一段全新对话 [1][2]。

**另起全新会话的做法**：把 thread_id 置为 `null`（前端 `useStream` / `injectStream` 场景），即可开始新对话 [3][4][5]。

## 最小可用示例

前端（Svelte 风格，Python/JS 文档片段内容一致）：

```ts
let threadId = $state<string | null>(null);

const stream = useStream<typeof myAgent>({
  threadId: () => threadId,
  onThreadId: (id) => (threadId = id),
});
```

```html
<button onclick={() => (threadId = null)}>New conversation</button>
```

Angular 风格：

```ts
threadId = signal<string | null>(null);

stream = injectStream<typeof myAgent>({
  threadId: this.threadId,
  onThreadId: (id) => this.threadId.set(id),
});

// In template:
// <button (click)="threadId.set(null)">New conversation</button>
```

## 说明与差异提示

- 片段中参数写作 `thread_id`，通过 `config={"configurable": {"thread_id": ...}}` 传入 [1][2]；而前端示例里 `useStream` / `injectStream` 的选项名是 `threadId`（驼峰）[3][4][5]。两者是不同层面的写法，注意不要混用。
- 片段只覆盖了「thread_id 的语义」和「前端如何重置为新会话」，**没有**给出后端/服务端直接新建 thread_id 的具体 API 或生成规则，这部分给出的文档里没有找到能回答的内容。
--- 片段[1] oss__python__deepagents__going-to-production#008 ---
- thread_id (passed via config={"configurable": {"thread_id": ...}} ): a stable identifier for the conversation. The checkpointer uses it to persist and resume message history, so follow-up turns continue the same conversation. Generate a new thread_id to start a fresh conversation.
--- 片段[2] oss__javascript__deepagents__going-to-production#008 ---
- thread_id (passed via config={"configurable": {"thread_id": ...}} ): a stable identifier for the conversation. The checkpointer uses it to persist and resume message history, so follow-up turns continue the same conversation. Generate a new thread_id to start a fresh conversation.
--- 片段[3] oss__python__langchain__frontend__message-queues#015 ---
```

<script lang="ts">

  let threadId = $state<string | null>(null);

  const stream = useStream<typeof myAgent>({

    threadId: () => threadId,

    onThreadId: (id) => (threadId = id),

  });

</script>



<button onclick={() => (threadId = null)}>New conversation</button>

```
--- 片段[4] oss__javascript__langchain__frontend__message-queues#015 ---
```

<script lang="ts">

  let threadId = $state<string | null>(null);

  const stream = useStream<typeof myAgent>({

    threadId: () => threadId,

    onThreadId: (id) => (threadId = id),

  });

</script>



<button onclick={() => (threadId = null)}>New conversation</button>

```
--- 片段[5] oss__python__langchain__frontend__message-queues#016 ---
```

threadId = signal<string | null>(null);

stream = injectStream<typeof myAgent>({

  threadId: this.threadId,

  onThreadId: (id) => this.threadId.set(id),

});



// In template:

// <button (click)="threadId.set(null)">New conversation</button>

```

### 82. v1-D-007 [single-hop] score=1.0
Q: 开启摘要压缩之后，之前对话里的图片还会留在上下文里吗？
GOLD: 不会。Summarization 会把较早的消息压成纯文本摘要，落在这个范围内的 image、audio、video、file 块都不会被带过去，模型只能看到摘要里写的内容；低于 keep threshold 的近期消息不受影响。原始对话本身仍会以文本形式写到文件系统。
ANSWER: **结论：不会。摘要压缩运行时，旧消息里的图片（以及音频、视频、文件块）不会保留在活动上下文中，模型只能看到摘要器写下的文字描述。** [1][2]

具体要点：

- 摘要会把较旧的消息压缩成**纯文本摘要**；该范围内的 image / audio / video / file 块不会被带过去，模型只看到摘要器对它们的文字描述 [1][2]。
- 低于 keep 阈值的**近期消息保持不变** [1][2]。
- 压缩后，那些轮次会坍缩成文本，image 块消失 [3][4]。
- 原始对话仍会以文本形式写入文件系统 [3][4]。

最小示例（Python，示意压缩前后的变化）[1][4]：

```python
# Before — 模型能在旧轮次收到 image 块
HumanMessage(content=[
    {"type": "text", "text": "What trends do you see in this chart?"},
    {"type": "image", "base64": IMG, "mime_type": "image/png"},
])

# After — 这些轮次坍缩为文本；image 块不再存在
{
    "content": (
        "User asked about trends in a chart screenshot. "
        "Tool returned an updated chart. Agent identified Q3 revenue growth."
    )
}
```

补充一个容易混淆的点：**offloading（卸载）只计量文本 token**，非文本块（包括图片）在替换消息中会被保留而不是被压缩；仅含图片的消息不会仅因图片大小而被 offload [5]。也就是说，“图片不留在上下文”这一结论针对的是**摘要压缩**，不要和 offloading 的行为混为一谈 [1][5]。

另外提示一处命名差异：你问的是“摘要压缩”，文档中的对应机制名为 **Summarization**；触发条件、keep 阈值和完整流程需参见 Summarization 文档，给出的片段里没有展开这些细节 [3][4]。
--- 片段[1] oss__python__deepagents__multimodal#005 ---
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: # Before — model receives image blocks in older turns [ HumanMessage ( content = [ { "type" : "text" , "text" : "What trends do you see in this chart?" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ] ), ToolMessage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" :
--- 片段[2] oss__javascript__deepagents__multimodal#005 ---
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: // Before — model receives image blocks in older turns void { role : "user" , content : [ { type : "text" , text : "What trends do you see in this chart?" }, { type : "image" , url : "https://example.com/chart.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url :
--- 片段[3] oss__javascript__deepagents__multimodal#006 ---
.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url : "https://example.com/chart-v2.png" }, ] , }; // After — those turns collapse to text; image blocks are gone void { content : "User asked about trends in a chart screenshot. " + "Tool returned an updated chart. Agent identified Q3 revenue growth." , }; The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
--- 片段[4] oss__python__deepagents__multimodal#006 ---
ssage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ], tool_call_id = "call_chart_1" , ), AIMessage ( content = "Revenue rose in Q3 based on the chart trend." ), HumanMessage ( content = "Reply with one sentence summarizing our analysis." ), ] # After — those turns collapse to text; image blocks are gone { "content" : ( "User asked about trends in a chart screenshot. " "Tool returned an updated chart. Agent identified Q3 revenue growth." )} The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
--- 片段[5] oss__python__deepagents__multimodal#004 ---
- Offloading measures text tokens only. Non-text blocks (including images) are preserved in replacement messages rather than compressed. A message that contains only an image is not offloaded based on image size alone.

### 83. v1-D-008 [single-hop] score=0.5
Q: openwiki 支持哪些模型提供方？openai 和 bob 分别要配什么凭据？
GOLD: openai 用 OPENAI_API_KEY，另外可选 OPENAI_BASE_URL，用来指向暴露 Responses API 的 OpenAI 兼容网关；bob 用 BOB_API_KEY，可选 BOB_BASE_URL，它的模型 ID 是固定的 premium，没有 model picker。copilot 可以用 GitHub CLI session 或 COPILOT_API_KEY，但 CI 里必须用 OAuth token，不能用 classic PAT。
ANSWER: **结论：** 文档列出的提供方有 openai、openai-chatgpt、copilot、openrouter、anthropic、bob、gemini [1]。其中 openai 使用 `OPENAI_API_KEY`（可选 `OPENAI_BASE_URL`，用于暴露 Responses API 的 OpenAI 兼容网关）[1]；bob 使用 `BOB_API_KEY`（可选 `BOB_BASE_URL`，模型 ID 固定为 premium，无模型选择器）[1]。

**最小示例（环境变量）：**

```bash
# openai
OPENAI_API_KEY=your-openai-key
# 可选：OPENAI_BASE_URL=https://your-gateway.example.com

# bob
BOB_API_KEY=your-bob-key
# 可选：BOB_BASE_URL=https://your-bob-endpoint.example.com
```

补充说明：片段 [2]–[5] 还给出了 `openai-compatible` 这种通用接入方式（含 Opper、Requesty、Entra 认证等示例），但它属于“OpenAI 兼容端点”配置，不在 [1] 的 Provider 表格清单里，因此不计入上面的提供方列表。
--- 片段[1] oss__openwiki__providers#000 ---
| Provider | Credential | Notes | | --- | --- | --- | | openai | OPENAI_API_KEY | Optional OPENAI_BASE_URL for OpenAI-compatible gateways that expose the Responses API | | openai-chatgpt | ChatGPT OAuth tokens | Sign in with ChatGPT; usage draws on Plus/Pro/Team Codex allowance | | copilot | GitHub CLI session or COPILOT_API_KEY | Optional COPILOT_BASE_URL . CI needs an OAuth token, not a classic PAT | | openrouter | OPENROUTER_API_KEY | Optional OPENWIKI_OPENROUTER_PROVIDER_ONLY allowlist | | anthropic | ANTHROPIC_API_KEY | Optional ANTHROPIC_BASE_URL | | bob | BOB_API_KEY | Optional BOB_BASE_URL . Fixed model ID premium ; no model picker | | gemini | GEMINI_API_KEY | Google AI Studio |
--- 片段[2] oss__openwiki__providers#017 ---
```

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-gateway-key

OPENAI_COMPATIBLE_BASE_URL=https://your-gateway.example.com/v1

OPENWIKI_MODEL_ID=your-gateway-model-name

```
--- 片段[3] oss__openwiki__providers#009 ---
```

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_AUTH=entra-id

OPENAI_COMPATIBLE_BASE_URL=https://gateway.example.com/openai/v1

OPENAI_COMPATIBLE_ENTRA_SCOPE=api://gateway-application-id/.default

OPENWIKI_MODEL_ID=your-gateway-model

```
--- 片段[4] oss__openwiki__providers#019 ---
```

# Opper

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-opper-key

OPENAI_COMPATIBLE_BASE_URL=https://api.opper.ai/v3/compat

OPENWIKI_MODEL_ID=claude-sonnet-4-6

```
--- 片段[5] oss__openwiki__providers#018 ---
```

# Requesty

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-gateway-key

OPENAI_COMPATIBLE_BASE_URL=https://router.requesty.ai/v1

OPENWIKI_MODEL_ID=openai/gpt-6.1-sol

```

### 84. v1-D-009 [single-hop] score=1.0
Q: openwiki 里不同 provider 能调的 reasoning effort 档位一样吗？这些档位最后落到请求的哪个字段上？
GOLD: 不一样。openai 和 openai-chatgpt 下的 gpt-5.6-terra/luna/sol 支持 none、low、medium、high、xhigh、max，映射到 Responses API 的 reasoning.effort；nvidia 的 nemotron 只有 none、low、high，走 Chat Completions 的 reasoning_effort；gemini-4-hydrogen 只有 low、medium、high、xhigh，对应 Gemini 的 thinking level。
ANSWER: 不一样。不同 provider 支持的档位和映射到的请求字段都不同。

**档位差异：**
- openai / openai-chatgpt：`none, low, medium, high, xhigh, max` [1]
- nvidia：`none, low, high`（没有 medium/xhigh/max）[1]
- gemini：`low, medium, high, xhigh`（没有 none/max）[1]
- openai-compatible（启用时）：`none, low, medium, high, xhigh, max` [5]

**请求字段映射：**
- openai / openai-chatgpt → Responses API 的 `reasoning.effort` [1]
- nvidia → Chat Completions 的 `reasoning_effort` [1]
- gemini → Gemini thinking level [1]
- openai-compatible → Responses API 的 `reasoning.effort` 或 Chat Completions 的 `reasoning_effort` [5]

**需要注意的差异：**
- 你问的是「openwiki 里」，但片段 [3] 是 JavaScript Google 集成文档，它列出的 gemini 档位是 `minimal, low, medium, high, xhigh`，比 openwiki 表格 [1] 多了 `minimal`。两者来源不同，以各自文档为准；若按 openwiki 的表格，gemini 档位是 `low, medium, high, xhigh` [1]。
- 片段 [4] 用的是 `gpt-6.1-sol` 和 `reasoning_effort` 参数，与 openwiki 表格里的模型名（`gpt-5.6-*`）不一致，属于不同文档/场景，不能直接套用 [1][4]。

**最小示例（openwiki 交互命令）：**
```text
/effort high
/effort default
```
`/effort` 用于为支持的 OpenAI GPT-5.6、NVIDIA NIM、Gemini 及 opted-in 的 openai-compatible 模型设置 reasoning effort，`/effort default` 恢复 provider 默认值 [2]。
--- 片段[1] oss__openwiki__providers#006 ---
| Provider | Model | Supported values | Request mapping | | --- | --- | --- | --- | | openai | gpt-5.6-terra , gpt-5.6-luna , gpt-5.6-sol | none , low , medium , high , xhigh , max | Responses API reasoning.effort | | openai-chatgpt | gpt-5.6-terra , gpt-5.6-luna , gpt-5.6-sol | none , low , medium , high , xhigh , max | Responses API reasoning.effort | | nvidia | nvidia/nemotron-3-super-120b-a12b | none , low , high | Chat Completions reasoning_effort | | gemini | gemini-4-hydrogen | low , medium , high , xhigh | Gemini thinking level |
--- 片段[2] oss__openwiki__cli-reference#011 ---
- /effort : Set reasoning effort for supported OpenAI GPT-5.6, NVIDIA NIM, Gemini, and opted-in openai-compatible models, or /effort default to restore the provider default
--- 片段[3] oss__javascript__integrations__chat__google#029 ---
- reasoningEffort (or thinkingLevel ): Sets the relative effort. Values: "minimal" , "low" , "medium" , "high" , "xhigh" (supported on gemini-4-hydrogen and gemini-4-neon ; gemini-4-neon requires @langchain/google 0.2.16 or later).
--- 片段[4] oss__python__deepagents__models#007 ---
```

from deepagents import ProviderProfile, register_provider_profile



# Provider-wide default: every openai model gets temperature=0.

register_provider_profile(

    "openai",

    ProviderProfile(init_kwargs={"temperature": 0}),

)



# Model-level override: gpt-6.1-sol additionally gets a specific reasoning effort.

# Inherits temperature=0 from the provider-level profile above.

register_provider_profile(

    "openai:gpt-6.1-sol",

    ProviderProfile(init_kwargs={"reasoning_effort": "medium"}),

)

```
--- 片段[5] oss__openwiki__providers#007 ---
Chat Completions reasoning_effort | | gemini | gemini-4-hydrogen | low , medium , high , xhigh | Gemini thinking level | | openai-compatible | Any model ID, when enabled | none , low , medium , high , xhigh , max | Responses API reasoning.effort or Chat Completions reasoning_effort |

### 85. v1-D-010 [single-hop] score=1.0
Q: 已经生成过 wiki 了，我再跑一次 --init 会把之前的全清空吗？--init 能和 --update 一起用吗？
GOLD: 重跑 --init 会从零重新生成仓库 wiki，但会保留 openwiki/INSTRUCTIONS.md。--init 和 --update 不能组合使用。另外在 TTY 里不带 --print 时，它会流式打印 agent 输出并在成功后自动退出。
ANSWER: **结论：**

1. 会重新生成。再次运行 `--init` 会「from scratch」重新生成仓库 wiki，但会保留 `openwiki/INSTRUCTIONS.md` [1]。
2. `--init` 和 `--update` 不能一起用 [1]。

**最小可用示例：**

```bash
# 重新生成（保留 openwiki/INSTRUCTIONS.md）
openwiki code --init

# 更新已有文档
openwiki code --update
```

补充说明：`--init` 和 `--update` 默认都是 code mode；在 TTY 且未加 `--print` 时会流式输出 agent 内容并在成功后自动退出 [1]。另外 `openwiki/INSTRUCTIONS.md` 是用户编写的范围与优先级说明，正常的 `--init` 和 `--update` 运行不会重写它 [2]。
--- 片段[1] oss__openwiki__cli-reference#002 ---
| Flag | Description | | --- | --- | | --init | Generate initial documentation. Defaults to code mode. Re-running regenerates the repository wiki from scratch while preserving openwiki/INSTRUCTIONS.md . In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | --update | Update existing documentation. Defaults to code mode. In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | -l , --language <locale> | Generate wiki documentation in the given BCP-47 locale, for example ko , zh-CN , or pt-BR . Unrecognized values are rejected. |
--- 片段[2] oss__openwiki__code-mode#003 ---
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
--- 片段[3] oss__openwiki__code-mode#001 ---
```

openwiki code --init

openwiki code --update

openwiki code --update --print

```
--- 片段[4] oss__openwiki__personal-mode#001 ---
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
--- 片段[5] oss__javascript__deepagents__async-subagents#017 ---
- Update creates a new run on the same thread. By default it interrupts the previous run, and the subagent restarts with the full conversation history plus the new instructions. The task ID stays the same.

### 86. v1-D-011 [single-hop] score=1.0
Q: personal mode 里接 custom-mcp 这类自定义 MCP 服务，openwiki 会把它所有工具都放开吗？
GOLD: 不会。custom-mcp 源默认不需要凭据，可以连任意配置好的 HTTP 或 stdio MCP server，但只允许那些明确安全、只读的工具。相比之下 git-repo 源只读本地仓库路径并写出紧凑的 manifest。
ANSWER: **结论：不会全部放开。** custom-mcp 默认不需要凭据，它会连接到任何已配置的 HTTP 或 stdio MCP 服务器，但**只允许明确标记为安全、只读的工具** [1]。

也就是说，openwiki 对 custom-mcp 的工具是白名单式限制（仅显式安全的只读工具），不是全量放开 [1]。

**最小可用示例（基于片段可确认的部分）：**

```bash
# 查看 MCP-backed provider 的实时 MCP 工具列表
openwiki auth tools <provider>
```

说明：片段 [3] 提供了 `openwiki auth tools <provider>` 用于列出 MCP-backed provider 的实时工具，但片段中**没有**给出 custom-mcp 的具体配置写法或工具白名单的配置语法，因此这里无法给出完整的 custom-mcp 接入配置示例。

**补充差异提示：** 你的说法是「自定义 MCP 服务」，片段中的来源名是 `custom-mcp`，行为描述为「Connects to any configured HTTP or stdio MCP server and permits only explicitly safe, read-only tools」[1]，以片段为准。
--- 片段[1] oss__openwiki__personal-mode#003 ---
| Source | Credentials | Behavior | | --- | --- | --- | | custom-mcp | None required by default | Connects to any configured HTTP or stdio MCP server and permits only explicitly safe, read-only tools | | git-repo | Local paths | Reads configured local repository paths and writes compact manifests | | x | OAuth user-context credentials | Home timeline, user posts, mentions, bookmarks, and list posts via the X API | | notion | Notion OAuth (hosted MCP) | Authenticate through Notion OAuth instead of pasting a Notion token | | google | Gmail OAuth | Fetches recent mail via the Gmail API after openwiki auth gmail | | web-search | TAVILY_API_KEY | Uses Tavily through LangChain |
--- 片段[2] oss__openwiki__personal-mode#000 ---
Personal mode Build a local personal brain wiki from configured sources with OpenWiki.
--- 片段[3] oss__openwiki__cli-reference#007 ---
```

# List supported auth providers and status

openwiki auth



# Browser OAuth; save tokens to ~/.openwiki/.env and create connector config when possible

openwiki auth gmail

openwiki auth notion

openwiki auth slack

openwiki auth x



# Regenerate connector config from saved auth env vars

openwiki auth configure <provider> [--force]



# List live MCP tools for MCP-backed providers

openwiki auth tools <provider>



# Run source-specific connector ingestion

openwiki ingest <source|source-instance|all>



# HTTPS tunnel for Slack OAuth; saves OPENWIKI_HTTPS_OAUTH_REDIRECT_URI

openwiki ngrok start [url] [--port <port>]

```
--- 片段[4] oss__openwiki__personal-mode#001 ---
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
--- 片段[5] oss__openwiki__personal-mode#007 ---
- After openwiki auth gmail , the Google connector can ingest Gmail directly with no MCP transport setup

### 87. v1-D-012 [single-hop] score=1.0
Q: 自己在本机跑开源 embedding 模型，跟调托管 API 比要付出什么代价？
GOLD: 本地开源方案（BAAI/bge-*、Qwen/Qwen3-Embedding-*、sentence-transformers/all-* 这类）下载一次就能到处跑，没有按调用计费，数据也不离开自己的环境。代价是在小规模下 CPU 上大概率比托管 API 慢，有 GPU 才可能追平或更快。
ANSWER: **结论：** 本机跑开源 embedding 模型的主要代价是**小规模下 CPU 推理可能比托管 API 慢**；好处是没有按调用计费、数据不出本地环境 [1]。另外，如果要在生产规模自托管，需要额外用 TEI 或 Ollama 之类的服务来获得水平扩展和 API 易用性 [2]。

具体对比：

- 本地/开源模型（如 BAAI/bge-*、mixedbread-ai/mxbai-embed-*、Qwen/Qwen3-Embedding-* 等）：一次下载、随处运行，无按调用成本，数据不离开你的环境；**小规模时在 CPU 上很可能比托管 API 慢**，有 GPU 时则有竞争力或更快 [1]。
- 托管旗舰模型（如 OpenAI text-embedding-3-large、Cohere embed-english-v3 等）：一次 API 调用、开箱即用的最佳质量、无需本地基础设施；代价是**按调用计费**和**数据出境依赖** [3]。
- 生产规模自托管：用 TEI 或 Ollama 提供同样的开源模型（基础或微调版），兼具本地推理的经济性和托管提供商的水平扩展与 API 易用性 [2]。

**最小可用示例（本地开源模型思路）：** 给出的片段里没有本地开源 embedding 模型的具体实例化代码，只有托管/自托管服务的说明 [1][2]，因此无法给出可运行的本地示例。片段中仅有的代码示例是托管 API 的用法，例如：

```javascript
import { OpenAIEmbeddings } from "@langchain/openai";

const embeddings = new OpenAIEmbeddings({
  apiKey: "YOUR-API-KEY", // In Node.js defaults to process.env.OPENAI_API_KEY
  batchSize: 512, // Default value if omitted is 512. Max is 2048
  model: "text-embedding-3-large",
});
```
[5]

**补充说明：** 片段 [4] 展示的是 `AzureOpenAIEmbeddings` 的参数（`azureOpenAIApiKey`、`azureOpenAIApiInstanceName`、`azureOpenAIApiEmbeddingsDeploymentName`、`azureOpenAIApiVersion`）[4]，与本地开源模型无关；若你想找本地模型的 LangChain 集成写法，给出的文档里没有找到能回答这个问题的内容，缺少本地开源 embedding 模型的具体类名与参数示例。
--- 片段[1] oss__python__integrations__embeddings#007 ---
2. Local, open-source: BAAI/bge-* , mixedbread-ai/mxbai-embed-* , Qwen/Qwen3-Embedding-* , nomic-ai/modernbert-embed-* , sentence-transformers/all-* . Download once, run anywhere. No per-call cost, data never leaves your environment. Likely slower on CPU than a hosted API at small scale; competitive or faster with a GPU.
--- 片段[2] oss__python__integrations__embeddings#009 ---
4. Self-hosted at production scale: the same open models (base or fine-tuned) served via Text Embeddings Inference (TEI) or Ollama. Gives you the economics of local inference with the horizontal scaling and API ergonomics of a hosted provider.
--- 片段[3] oss__python__integrations__embeddings#006 ---
1. Hosted, flagship: OpenAI text-embedding-3-large , Cohere embed-english-v3 , Google gemini-embedding-001 , Voyage voyage-3 . One API call, best-in-class quality out of the box, no local infrastructure. Per-call cost and a data-egress dependency.
--- 片段[4] oss__javascript__integrations__providers__microsoft#006 ---
```

import { AzureOpenAIEmbeddings } from "@langchain/openai";



const model = new AzureOpenAIEmbeddings({

  azureOpenAIApiKey: "<your_key>", // In Node.js defaults to process.env.AZURE_OPENAI_API_KEY

  azureOpenAIApiInstanceName: "<your_instance_name>", // In Node.js defaults to process.env.AZURE_OPENAI_API_INSTANCE_NAME

  azureOpenAIApiEmbeddingsDeploymentName: "<your_embeddings_deployment_name>", // In Node.js defaults to process.env.AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME

  azureOpenAIApiVersion: "<api_version>", // In Node.js defaults to process.env.AZURE_OPENAI_API_VERSION

});

```
--- 片段[5] oss__javascript__integrations__embeddings__openai#003 ---
```

import { OpenAIEmbeddings } from "@langchain/openai";



const embeddings = new OpenAIEmbeddings({

  apiKey: "YOUR-API-KEY", // In Node.js defaults to process.env.OPENAI_API_KEY

  batchSize: 512, // Default value if omitted is 512. Max is 2048

  model: "text-embedding-3-large",

});

```

### 88. v1-D-013 [single-hop] score=0.0
Q: 供应商整体挂掉、或者 agent 陷入死循环疯狂调工具时，fault tolerance 文档分别建议加什么中间件？
GOLD: provider 整体不可用时用 modelFallbackMiddleware 自动回退到备选模型；调用次数失控（runaway loops）时用 ModelCallLimitMiddleware 和 ToolCallLimitMiddleware 限制每次运行的模型调用与工具调用。至于意料之外的错误，文档建议不加中间件，让异常直接冒泡。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体来说：

- 片段 [1][2] 只是 fault-tolerance 页面的标题和一句话简介（“Make your deep agent resilient with rate limiting, retries, fallbacks, and error handling”），没有给出针对“供应商整体挂掉”或“agent 死循环疯狂调工具”的具体中间件建议。
- 片段 [3][4][5] 讲的是 `ToolErrorMiddleware` 和 `ToolRetryMiddleware`（Python）/ `toolRetryMiddleware`（JS）的用法，属于工具级错误处理与重试，但片段中没有出现“供应商整体挂掉”或“死循环/循环调用”对应的中间件名称或配置说明。

缺少的内容：fault-tolerance 文档正文中关于 fallback（供应商故障切换）和循环/调用次数限制（如循环检测或调用上限）的具体中间件名称与示例。
--- 片段[1] oss__python__deepagents__fault-tolerance#000 ---
Fault tolerance Make your deep agent resilient with rate limiting, retries, fallbacks, and error handling
--- 片段[2] oss__javascript__deepagents__fault-tolerance#000 ---
Fault tolerance Make your deep agent resilient with rate limiting, retries, fallbacks, and error handling
--- 片段[3] oss__python__langchain__middleware__built-in#007 ---
onError): return f"Tool `{request.tool_call['name']}` encountered a connection error." return None agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, database_tool], middleware=[ # Place retry inner so exceptions reach ToolErrorMiddleware after retries are exhausted ToolErrorMiddleware(on_error=on_error, tools=["search_tool"]), ToolRetryMiddleware(max_retries=3, on_failure="error"), ], ) # Async-only: pass aon_error alone (do not pass on_error) async_agent = create_agent( model="gpt-6.1-sol", tools=[api_tool], middleware=[ToolErrorMiddleware(aon_error=aon_error)], ) ```
--- 片段[4] oss__python__langchain__middleware__built-in#011 ---
```

from langchain.agents import create_agent

from langchain.agents.middleware import ToolRetryMiddleware



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[search_tool, database_tool, api_tool],

    middleware=[

        ToolRetryMiddleware(

            max_retries=3,

            backoff_factor=2.0,

            initial_delay=1.0,

            max_delay=60.0,

            jitter=True,

            tools=["api_tool"],

            retry_on=(ConnectionError, TimeoutError),

            on_failure="continue",

        ),

    ],

)

```
--- 片段[5] oss__javascript__langchain__middleware__built-in#006 ---
``` import { createAgent, toolRetryMiddleware } from "langchain"; import { tool } from "@langchain/core/tools"; import { z } from "zod"; // Basic usage with default settings (2 retries, exponential backoff) const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, databaseTool], middleware: [toolRetryMiddleware()], }); // Retry specific exceptions only const retry = toolRetryMiddleware({ maxRetries: 4, retryOn: [TimeoutError, NetworkError], backoffFactor: 1.5, }); // Custom exception filtering function shouldRetry(error: Error): boolean { // Only retry on 5xx errors if (error.name === "HTTPError" && "statusCode" in error) { const statusCode = (error as any).statusCode;

### 89. v1-D-014 [multi-hop] score=0.5
Q: 同步子 agent 和异步子 agent 在跑到一半还能不能改这件事上差在哪？异步任务启动时又会带上哪些上下文？
GOLD: 同步子 agent 任务进行中无法追加指令，也不能取消（除非把 supervisor 停掉），调用之间没有持久状态；异步子 agent 可以用 update_async_task 送后续指令、用 cancel_async_task 取消，并在自己的 thread 上跨交互保持状态。异步任务启动时会在 server 上新建一个 thread，isolated 模式只发任务描述，fork 模式额外带上父 agent 的对话历史，start_async_task 返回的 thread ID 就是任务 ID。
ANSWER: **结论：**

1. **跑到一半能否修改**：同步子 agent **不支持**中途更新（Mid-task updates: Not possible）；异步子 agent **支持**，可以通过 `update_async_task` 发送后续指令 [1][2]。
2. **异步任务启动时的上下文**：给出的文档片段里**没有**说明异步任务启动时会带上哪些上下文。片段 [5] 只提到主 agent 会维护对话上下文，而子 agent 每次都是全新开始（"subagents start fresh each time"），但这条并未区分同步/异步，也没有具体列出异步任务启动时携带的上下文内容。

**最小示例（基于片段中出现的 API 名称）：**

```text
# 异步子 agent 中途更新（片段中提到的 API）
update_async_task(...)   # 用于向运行中的异步子 agent 发送后续指令 [1][2]

# 非 Agent Server 场景下获取异步结果
check_async_task(...)    # supervisor 主动查询异步任务结果 [1][2]
```

**需要补充的内容**：若要回答"异步任务启动时带哪些上下文"，需要文档中关于异步子 agent 创建/调用参数（如 task 描述、消息历史、状态传递等）的片段，当前给出的片段未覆盖。
--- 片段[1] oss__python__deepagents__async-subagents#001 ---
| Dimension | Sync subagents | Async subagents | | --- | --- | --- | | Execution model | Supervisor blocks until subagent completes | Returns a task ID immediately; supervisor continues | | Where it runs | Inside the supervisor’s run | On its own thread on a server (Agent Server or another Agent Protocol server) | | Concurrency | Parallel but blocking | Parallel and non-blocking | | Results | Returned as the tool result | On Agent Server, the subagent notifies the supervisor; otherwise the supervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task |
--- 片段[2] oss__javascript__deepagents__async-subagents#001 ---
| Dimension | Sync subagents | Async subagents | | --- | --- | --- | | Execution model | Supervisor blocks until subagent completes | Returns a task ID immediately; supervisor continues | | Where it runs | Inside the supervisor’s run | On its own thread on a server (Agent Server or another Agent Protocol server) | | Concurrency | Parallel but blocking | Parallel and non-blocking | | Results | Returned as the tool result | On Agent Server, the subagent notifies the supervisor; otherwise the supervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task |
--- 片段[3] oss__python__langchain__multi-agent__subagents#004 ---
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
--- 片段[4] oss__javascript__langchain__multi-agent__subagents#004 ---
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
--- 片段[5] oss__python__langchain__multi-agent#011 ---
- The main agent maintains conversation context, but subagents start fresh each time

### 90. v1-D-015 [multi-hop] score=0.5
Q: 能不能让某个子 agent 用一套和主 agent 完全不同的 skills？这些 skill 文件实际存在哪由什么决定？
GOLD: 可以，给子 agent 传 skills（例如 /skills/research/、/skills/web-search/），它就从这些目录加载，不继承主 agent 的 skills，只有 general-purpose 子 agent 才继承主 agent 的 skills；它还会跑独立的 SkillsMiddleware，加载状态与父 agent 互相不可见。skills 属于 procedural memory，通过 skills= 传入，而文件究竟存在哪里、谁有权访问，由 backend 决定。
ANSWER: ## 结论

**可以。** 自定义子 agent 默认**不继承**主 agent 的 skills，需要在该子 agent 的定义里显式传入 `skills` 参数（一组 skill 源路径），从而让它使用与主 agent 不同的一套 skills [1][2][3][4]。只有 general-purpose 子 agent 会继承主 agent 的 skills [1][2]。

关于「skill 文件实际存在哪由什么决定」：给出的片段只说明 `skills` 是「Skills source paths / 一组目录路径」（例如 `["/skills/research/", "/skills/web-search/"]`，或 Python 版示例 `["/skills/researcher/"]`，即一个其子目录为各 skill 的容器目录）[1][2][5]。**片段没有说明这些路径如何解析到实际存储位置（例如是否相对某个根目录、是否在容器内挂载等）**，因此无法据此回答「实际存在哪」的完整机制——缺的是关于 skills 路径解析/存储位置规则的说明。

另外，片段指出：当子 agent 配置了 skills 时，它会运行自己独立的 `SkillsMiddleware` 实例，skill 状态完全隔离，子 agent 加载的 skills 对父 agent 不可见，反之亦然 [1][2]。

## 最小可用示例

JavaScript（参数名为 `skills`，类型 `string[]`）[1][5]：

```javascript
const researchSubagent = {
  name: "researcher",
  description: "Researches topics using its own skill set",
  skills: ["/skills/research/", "/skills/web-search/"],
};
```

Python（参数名为 `skills`，类型 `list[str]`）[2][4]：

```python
research_subagent = {
    "name": "researcher",
    "description": "Researches topics using its own skill set",
    "skills": ["/skills/researcher/"],
}
```

## 需要指出的差异

- 参数名在 JS 与 Python 片段中都是 `skills` [1][2][5]，与问题中的说法一致；但同页另一个结构化输出参数在 JS 里叫 `responseFormat` [1]，在 Python 里叫 `response_format` [2]，命名风格不同，使用时注意区分。
- 片段只给出路径示例，未给出路径的解析规则，故「文件实际存在哪」这一点无法从现有片段确定 [1][2][5]。
--- 片段[1] oss__javascript__deepagents__subagents#006 ---
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
--- 片段[2] oss__python__deepagents__subagents#007 ---
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
--- 片段[3] oss__javascript__deepagents__skills#055 ---
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
--- 片段[4] oss__python__deepagents__skills#068 ---
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
--- 片段[5] oss__javascript__deepagents__subagents#005 ---
| Optional. Additional middleware for custom behavior, logging, or rate limiting. Does not inherit from the main agent. Appended to the synchronous subagent stack . | | interruptOn | Record<string, boolean \| InterruptOnConfig> | Optional. Configure human-in-the-loop for specific tools. Options: True , False . or an InterruptOnConfig with allowed_decisions . Requires checkpointer. Inherits from main agent by default. Subagent value overrides the default. | | skills | string[] | Optional. Skills source paths. When specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ).

### 91. v1-D-016 [multi-hop] score=0.5
Q: LocalShellBackend 和我在生产里用的 sandbox，在执行环境上最关键的区别是什么？
GOLD: LocalShellBackend 直接在宿主机上做文件系统操作和 shell 执行，没有任何隔离，只适合受控的开发环境。sandbox 是隔离环境，而且有生命周期：换一个新会话就是一个全新的 sandbox，文档示例里第二个会话里 pandas 都没装、上一个会话的文件也不在。
ANSWER: 给出的文档里没有找到能直接回答「LocalShellBackend 与生产 sandbox 在执行环境上最关键区别」的完整内容。片段只提供了 LocalShellBackend 一侧的信息，缺少 sandbox backend 的执行环境细节，因此无法做对比结论。

能确认的、与执行环境相关的信息如下：

- LocalShellBackend 的命令是直接在你的机器上通过 `subprocess.run(shell=True)` 执行的，并且没有沙箱隔离 [3][4]。
- 文档建议：在生产环境需要文件系统交互时，使用 sandbox backend [1][2]。但片段没有说明 sandbox backend 具体如何隔离执行环境。

最小可用示例（仅展示 LocalShellBackend 的用法，来自片段 [5]）：

```python
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

agent = create_deep_agent(
    model="openai:gpt-6.1-sol",
    backend=LocalShellBackend(root_dir=".", virtual_mode=True, env={"PATH": "/usr/bin:/bin"}),
)
```

缺失的内容：sandbox backend 的执行环境描述（例如是否容器化、隔离边界、文件系统与网络策略等），因此无法给出「最关键区别」的对比结论。
--- 片段[1] oss__javascript__deepagents__backends#011 ---
3. Use a sandbox backend for production environments requiring filesystem interaction.
--- 片段[2] oss__python__deepagents__backends#017 ---
3. Use a sandbox backend for production environments requiring filesystem interaction.
--- 片段[3] oss__javascript__deepagents__backends#034 ---
- Commands run directly on your machine using subprocess.run(shell=True) with no sandboxing.
--- 片段[4] oss__python__deepagents__backends#040 ---
- Commands run directly on your machine using subprocess.run(shell=True) with no sandboxing.
--- 片段[5] oss__python__deepagents__backends#033 ---
```

from deepagents import create_deep_agent

from deepagents.backends import LocalShellBackend



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    backend=LocalShellBackend(root_dir=".", virtual_mode=True, env={"PATH": "/usr/bin:/bin"}),

)

```

### 92. v1-D-017 [multi-hop] score=0.5
Q: 怎么让 agent 在调用某个工具之前停下来等我批准？我批准之后又该怎么让它继续跑？
GOLD: 在配置里给对应工具打开 interruptOn，工具调用前就会暂停、等人工批准。中断后按顺序给每个 actionRequest 一个 decision（比如 approve），再用 Command 带上 resume 的 decisions 恢复执行。
ANSWER: 结论：可以用 `interrupt()` 原语在工具内部暂停执行，等人工批准后再用 `Command(resume=...)` 恢复运行；并且必须配置 checkpointer（如 `InMemorySaver()`）才能暂停和恢复 [3][4]。在 DeepAgents 里也可以用 `FilesystemPermission(mode="interrupt")` 让写操作前暂停等待批准，同样需要 checkpointer [2]。

最小可用示例（工具内 `interrupt()` + `Command(resume=...)`）：

```python
from langchain.tools import tool
from langgraph.types import Command, interrupt

@tool(description="Request human approval before proceeding with an action.")
def request_approval(action_description: str) -> str:
    """Request human approval using the interrupt() primitive."""
    # interrupt() 暂停执行，并返回传给 Command(resume=...) 的值
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

创建 agent 时需要 checkpointer（片段示例）：

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
# ... 创建 agent 时传入 checkpointer=checkpointer
```

恢复时用 `Command(resume=...)`，例如片段中演示的 `new Command({ resume: ... })` [5]；Python 侧对应 `Command(resume=...)` [3][4]。

补充说明（以片段为准）：
- 片段 [1] 展示的是 MCP elicitation 场景下的暂停/恢复：`paused["__interrupt__"]` 取出中断，答案按服务器自己的 request key 组织，`action` 可为 `accept`/`decline`/`cancel`，恢复同样是再次 `ainvoke` [1]。这与“工具前人工批准”是不同机制，注意不要混用。
- 片段 [2] 的 `FilesystemPermission(operations=["write"], paths=["/secrets/**"], mode="interrupt")` 是 DeepAgents 的权限中断方式，注释明确“Interrupt mode requires a checkpointer to pause and resume” [2]。

给出的文档里没有找到能回答这个问题的内容的部分：片段未给出完整的“批准后恢复”的 Python 端到端调用代码（例如 `agent.invoke(new Command(resume=...), config)` 的完整 Python 写法），只给出了 JS 侧的 `new Command({ resume: ... })` 片段 [5] 和工具内 `interrupt()` 的用法 [3][4]。
--- 片段[1] oss__python__langchain__mcp__tools#015 ---
= await adapter.list_tools() # Resuming a paused run needs persistence, so the interrupted run has # somewhere to wait. agent = create_agent("claude-sonnet-5", tools, checkpointer=InMemorySaver()) config: Any = {"configurable": {"thread_id": "booking-1"}} paused = await agent.ainvoke( {"messages": [{"role": "user", "content": "Book a table for 4."}]}, config ) [interrupt] = paused["__interrupt__"] [question] = interrupt.value["requests"] # Answers are keyed by the server's own request key, so nothing has to # be tracked across the pause. `decline` or `cancel` would refuse. answer = {"action": "accept", "content": {"date": "2026-09-14"}} return await agent.ainvoke(
--- 片段[2] oss__python__deepagents__permissions#003 ---
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
--- 片段[3] oss__python__deepagents__human-in-the-loop#037 ---
``` from langchain.agents import create_agent from langchain_anthropic import ChatAnthropic from langchain.messages import HumanMessage from langchain.tools import tool from langgraph.checkpoint.memory import InMemorySaver from langgraph.types import Command, interrupt from deepagents.graph import create_deep_agent from deepagents.middleware.subagents import CompiledSubAgent @tool(description="Request human approval before proceeding with an action.") def request_approval(action_description: str) -> str: """Request human approval using the interrupt() primitive.""" # interrupt() pauses execution and returns the value passed to Command(resume=...) approval = interrupt({ "type":
--- 片段[4] oss__python__deepagents__human-in-the-loop#038 ---
ve.""" # interrupt() pauses execution and returns the value passed to Command(resume=...) approval = interrupt({ "type": "approval_request", "action": action_description, "message": f"Please approve or reject: {action_description}", }) if approval.get("approved"): return f"Action '{action_description}' was APPROVED. Proceeding..." else: return f"Action '{action_description}' was REJECTED. Reason: {approval.get('reason', 'No reason provided')}" def main(): checkpointer = InMemorySaver() model = ChatAnthropic( model_name="claude-sonnet-4-6", max_tokens=4096, ) compiled_subagent = create_agent( model=model, tools=[request_approval], name="approval-agent", ) parent_agent = create_deep_agent(
--- 片段[5] oss__javascript__deepagents__human-in-the-loop#022 ---
ntAgent.invoke( { messages: [ new HumanMessage({ content: "Use the task tool to launch the approval-agent sub-agent. " + "Tell it to use the request_approval tool to request approval for 'deploying to production'.", }), ], }, config ); if (result.__interrupt__) { const interruptValue = result.__interrupt__[0].value as { type?: string; action?: string; message?: string; }; console.log("\nInterrupt received!"); console.log(`  Type: ${interruptValue.type}`); console.log(`  Action: ${interruptValue.action}`); console.log(`  Message: ${interruptValue.message}`); console.log("\nResuming with Command(resume={'approved': true})..."); const result2 = await parentAgent.invoke( new Command({ resume:

### 93. v1-D-018 [multi-hop] score=0.5
Q: openwiki 的 --init 和 --update 到底该在什么时候用？是不是有些选项只能配在 update 上？
GOLD: --init 用于生成初始文档（默认 code mode），重跑会从零重建 wiki 但保留 openwiki/INSTRUCTIONS.md；--update 只更新已有文档，两者不能同时使用。确实有只在 update 上有效的选项：deferUnplannedClaimIssues 默认 false，开启后跳过给有 Claim 问题的未规划页面自动建任务，在 init run 上设置会返回 invalid_input 错误。
ANSWER: ## 结论

**1. `--init` 和 `--update` 的用途区分：**
- `--init`：生成初始文档，默认使用 code mode。重新运行会**从头重新生成**仓库 wiki，但会保留 `openwiki/INSTRUCTIONS.md` [1]。
- `--update`：更新已有文档，默认使用 code mode [1]。
- 两者**不能同时使用**（`--init` 和 `--update` cannot be combined）[1]。

**2. 关于「有些选项只能配在 update 上」：**
给出的文档片段里**没有找到**任何说明某个选项只能用于 `--update` 的内容。片段中出现的选项（`--init`、`--update`、`-l/--language`、`--print`、`-p`）都没有标注「仅限 update」的限制 [1][4][5]。因此无法确认存在「只能配在 update 上」的选项。

**3. 补充说明（片段中出现的相关行为）：**
- 在 TTY 中且不加 `--print` 时，`--init` 和 `--update` 都会流式输出 agent 内容并在成功后自动退出 [1]。
- `-l, --language <locale>` 用于按 BCP-47 语言生成 wiki 文档（如 `ko`、`zh-CN`、`pt-BR`），无法识别的值会被拒绝 [1]。
- `openwiki/INSTRUCTIONS.md` 是用户编写的范围与优先级说明，OpenWiki 在 init 和 update 时都会读取它；正常的 `--init` 和 `--update` 运行**不会重写**它 [2]。

## 最小可用示例

```bash
# 初始化（默认 code mode）
openwiki --init

# 更新（默认 code mode）
openwiki --update

# 指定语言初始化
openwiki --init --language ko

# 显式 code mode 下更新并打印
openwiki code --update --print
```

> 注意：片段 [1] 中 `--init` 与 `--update` 明确「cannot be combined」，不要同时传入。
--- 片段[1] oss__openwiki__cli-reference#002 ---
| Flag | Description | | --- | --- | | --init | Generate initial documentation. Defaults to code mode. Re-running regenerates the repository wiki from scratch while preserving openwiki/INSTRUCTIONS.md . In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | --update | Update existing documentation. Defaults to code mode. In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | -l , --language <locale> | Generate wiki documentation in the given BCP-47 locale, for example ko , zh-CN , or pt-BR . Unrecognized values are rejected. |
--- 片段[2] oss__openwiki__code-mode#003 ---
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
--- 片段[3] oss__openwiki__personal-mode#001 ---
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
--- 片段[4] oss__openwiki__code-mode#001 ---
```

openwiki code --init

openwiki code --update

openwiki code --update --print

```
--- 片段[5] oss__openwiki__cli-reference#000 ---
``` # Interactive chat in code mode (current repository) openwiki openwiki "Please generate documentation for this repository" # Personal mode openwiki personal openwiki personal --init openwiki personal --update # Explicit code mode openwiki code --init openwiki code --update openwiki code --update --print # Defaults to code mode and specify a language openwiki --init openwiki --update openwiki --init --language ko # One-shot print mode openwiki -p "Summarize what you can do" # Explore the wiki locally or export a static visualizer openwiki visualize openwiki visualize openwiki --port 4400 --no-open openwiki visualize openwiki --export docs/openwiki-visualizer

### 94. v1-D-019 [multi-hop] score=0.0
Q: deep agents 做文档 RAG 时检索环节有哪几种做法？示例代码里的切分和向量库是怎么配的？
GOLD: 一种做法是 skills-guided retrieval：agent 先加载一个描述该怎么搜这个语料的 skill（用哪个 index、query 怎么组织、引用格式），再按这份指引调用检索工具并综合作答。示例代码里用 RecursiveCharacterTextSplitter 按 chunkSize 1000、chunkOverlap 200 切分文档，用 text-embedding-3-small 做 embedding 存进 MemoryVectorStore，检索时 similaritySearch 取 4 条。
ANSWER: 结论：给出的文档只能确认 Deep Agents 的 RAG 页面提到了一些 RAG 模式名称，但**没有说明检索环节具体有哪几种做法**；示例代码片段里也**没有出现切分（chunking）配置或向量库配置**。

1. 关于检索做法：片段只说明 Deep Agents 的 RAG 模式包括 “skills-guided retrieval、rubric grading”，并提到一个教程会索引 LangChain 文档、把 chunks 卸载到文件系统、把分析委派给 subagents [1][2]。这只是模式/教程概述，没有展开“检索环节有哪几种做法”的具体分类或实现方式。

2. 关于示例代码里的切分配置：给出的代码片段 [3] 只包含 `max_concurrent_analysts = 3`、`INSTRUCTIONS` 拼接、`chunk_analyst_subagent` 定义、`init_chat_model(...)` 和 `create_deep_agent(...)` 等内容，**没有出现任何 chunking / splitter 的配置**。

3. 关于向量库配置：片段 [3] 中同样**没有出现向量库（vector store）的初始化或配置**。片段 [4][5] 只是 chunking 文档页面的摘要，提到可选策略包括 recursive、token-based、structure-aware、semantic chunking、small-to-big retrieval 和 chunk metadata，但**没有给出具体配置代码**，也不是 Deep Agents 示例里的配置。

缺失的内容：
- Deep Agents RAG 检索环节的具体做法清单/对比；
- 示例代码中文档切分的具体参数（chunk size、overlap、splitter 类型等）；
- 示例代码中向量库的类型、embedding 模型、索引/检索参数等配置。

因此，按现有片段无法回答“检索环节有哪几种做法”以及“示例代码里的切分和向量库是怎么配的”。
--- 片段[1] oss__javascript__deepagents__rag#000 ---
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
--- 片段[2] oss__python__deepagents__rag#000 ---
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
--- 片段[3] oss__python__deepagents__rag#088 ---
lapping facts and deduplicate source URLs. - Prefer concrete steps and code-oriented guidance from the documentation.""" max_concurrent_analysts = 3 INSTRUCTIONS = ( RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.format( max_concurrent_analysts=max_concurrent_analysts, ) ) chunk_analyst_subagent = { "name": "chunk-analyst", "description": ( "Analyze one retrieved documentation chunk file. " "Pass the user question and a single file path under /retrieved/." ), "system_prompt": CHUNK_ANALYST_INSTRUCTIONS, } model = init_chat_model(model="anthropic:claude-sonnet-4-6") agent = create_deep_agent( model=model, tools=[search_documentation],
--- 片段[4] oss__javascript__langchain__chunking#000 ---
Chunk documents for retrieval Choose a chunking strategy for RAG in LangChain, including recursive and token-based splitting, structure-aware and semantic chunking, small-to-big retrieval, and chunk metadata.
--- 片段[5] oss__python__langchain__chunking#000 ---
Chunk documents for retrieval Choose a chunking strategy for RAG in LangChain, including recursive and token-based splitting, structure-aware and semantic chunking, small-to-big retrieval, and chunk metadata.

### 95. v1-D-020 [paraphrase] score=1.0
Q: 我不想让派出去的子 agent 看到主对话里那一大段历史，最好它只看见我这次交给它的活，默认是这样吗？
GOLD: 是的，默认就是。子 agent 的 mode 默认为 isolated，这种情况下它只能看到被委派的那项任务；如果想让它继承父 agent 的对话和 system prompt，才需要显式设成 fork。
ANSWER: **结论：是的，默认就是这样。** 默认模式为 `"isolated"`，子 agent 只会收到本次委派的任务描述，不会看到父对话的历史，相当于全新开始 [1][2][3][4]。如果你希望它继承父对话历史，需要显式改成 `"fork"` [3][4]。

补充一点差异说明：你问的是「只看见这次交给它的活」，这与片段中 `"isolated"` 的描述一致 [1][2]；片段 [5] 也把该模式概括为「只接收任务描述」，并指出代价是子 agent 需要重新推导父级已经做过的工作 [5]。

最小可用示例（以片段中的模式取值为准）：

```python
# 默认即为 isolated，无需额外配置
subagent = {
    "name": "worker",
    "mode": "isolated",  # 只发送任务描述，不带父对话历史
}

# 若想继承父对话历史，则改为：
# "mode": "fork"
```

如果你需要的是具体某个语言/框架下的完整调用代码，给出的文档片段里没有提供，无法据此补全。
--- 片段[1] oss__javascript__deepagents__async-subagents#030 ---
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
--- 片段[2] oss__python__deepagents__async-subagents#018 ---
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
--- 片段[3] oss__python__deepagents__overview#036 ---
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
--- 片段[4] oss__javascript__deepagents__overview#028 ---
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
--- 片段[5] oss__python__langchain__multi-agent__subagents#034 ---
| Mode | Subagent receives | Best for | Tradeoff |

| --- | --- | --- | --- |

| Isolated (default) | Only the task description | Focused work that needs little prior context | Context isolation, but re-derives everything the parent already did |

| Forked | The parent’s conversation history (and, in Deep Agents, the system prompt) | Continuing a task the parent already started | Seeded with prior context, at the cost of a larger prompt and less isolation |

### 96. v1-D-021 [paraphrase] score=1.0
Q: 我在 skill 里挂的自定义工具，模型要是不先读 SKILL.md、直接猜工具名硬调，会怎么样？
GOLD: 会失败。skill 里的工具是 gated 的：在 agent 读到那个 skill 的 SKILL.md 之前，调用会被当成 unknown tool，即使模型猜对了名字和参数也一样。
ANSWER: **结论：会失败。** 在 agent 读取该 skill 的 `SKILL.md` 之前，对 skill 工具的调用会作为「未知工具」失败——即使模型猜对了工具名和参数也一样 [1][2]。

补充两点相关行为：
- skill 工具只有在 agent 读取 `SKILL.md` 之后才会出现；如果摘要（summarization）把这次读取丢弃，工具会再次消失 [3][4]。
- 另外，固定（pinning）一个 skill 也能让其工具可用，效果等同于读取其 `SKILL.md`；这些工具会一直可用，直到摘要丢弃被固定 skill 的消息 [5]。

**最小示例（示意，非片段原文代码）：**

```python
# 伪代码：未读 SKILL.md 前直接调用 skill 工具
agent.invoke("调用 my_skill_tool(query='...')")
# 结果：unknown tool 错误（因为尚未读取该 skill 的 SKILL.md）[1][2]

# 正确顺序：先让 agent 读取 SKILL.md，再调用工具
agent.invoke("读取 my_skill 的 SKILL.md，然后调用 my_skill_tool(query='...')")
```

> 说明：片段中未给出具体 API 名称或参数签名，因此示例仅为流程示意；实际接口请以文档为准。
--- 片段[1] oss__python__deepagents__skills#022 ---
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
--- 片段[2] oss__javascript__deepagents__skills#022 ---
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
--- 片段[3] oss__python__deepagents__skills#131 ---
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
--- 片段[4] oss__javascript__deepagents__skills#131 ---
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
--- 片段[5] oss__javascript__deepagents__skills#024 ---
- Pinning a skill makes its tools available the same way reading its SKILL.md does. They stay available until summarization drops the pinned skill’s message.

### 97. v1-D-022 [paraphrase] score=0.5
Q: 整页网页原文丢给模型太烧 token 了，有没有现成的 loader 能顺手把网页压小一点？
GOLD: 有，DomPruner 就是干这个的：它做 DOM AST 剪枝，把网页加载成紧凑的 Markdown，文档说能做到 97%+ 的 token reduction，而且不需要 API key。同一类需求里 Firecrawl 走另一条路，直接把网站变成 LLM-ready 的数据，支持 scrape、crawl、map、extract、search。
ANSWER: 结论：给出的文档里确实提到一个面向“把网页压小”的现成 loader——**DomPruner**，它做 DOM AST 剪枝，把网页加载为紧凑 Markdown，宣称 97%+ token 削减，且不需要 API key [4]。不过片段只给了它的定位描述，没有给出具体调用代码，所以下面只能给“按片段信息能确定的最小示例形态”，实际导入路径/参数需以官方页面为准。

最小可用示例（示意，片段未提供确切 API）：

```python
# 片段 [4] 仅说明 DomPruner 是 Package 类型、无需 API key、输出紧凑 Markdown
# 具体类名与参数片段中未给出，请勿照抄为已确认 API
from langchain_community.document_loaders import DomPrunerLoader  # 名称未在片段中确认

loader = DomPrunerLoader(url="https://example.com")
docs = loader.load()
```

需要指出的差异与缺口：

- 你问的是“整页网页原文丢给模型太烧 token”，片段 [4] 里符合“压缩网页”的描述只有 DomPruner（DOM AST 剪枝 → 紧凑 Markdown，97%+ token 削减，无需 API key）[4]。
- 片段 [1][3] 只是 loader 名称清单，其中出现了 `DomPrunerLoader` 字样 [1][3]，但没有它的导入路径、构造参数或 `load()` 用法。
- 片段 [4] 的表格里 DomPruner 一行只写了“Package”和功能描述，没有代码示例；因此无法从给出的文档确认类名到底是 `DomPrunerLoader` 还是别的名字，也无法确认参数名（如 `url`）。
- 另外片段 [2] 是 JavaScript 的 `TokenTextSplitter`，属于“文本切分”而非“网页加载压缩”，不能直接回答“网页原文压小”的 loader 需求 [2]。

如果你要的是“能直接复制运行的 DomPruner 用法”，给出的文档里没有找到能回答这个问题的内容，缺的是 DomPruner 的具体导入路径、类名和参数说明。
--- 片段[1] oss__python__integrations__document_loaders#013 ---
ader |  | | DiffbotCrawlLoader |  | | DiffbotExtractLoader |  | | DomPrunerLoader |  | | PolarisAIDataInsightLoader |  | | ProxmintLoader |  | | Google memorystore for Redis |  | | PyMuPDFLayoutLoader |  | | OpeddFeedLoader |  | | langchain_box |  | | AnyToMarkdownLoader |  | | Web2MDLoader |  | | PaddleOCR-VL |  | | AlfrescoLoader |  | | OpenDMALoader |  | | CommentScraperLoader |  | | Google Classroom |  | | Google cloud SQL for mysql |  | | Kinetica document loader |  | | Google firestore in datastore mode |  | | AgentQLLoader |  | | CVFileLoader |  | | ProxyHatLoader |  | | AirbyteLoader |  | | CapslaneLoader |  | | PdfmuseLoader |  | | LyrenthLoader |  | | PlasmateSOMLLoader |  |
--- 片段[2] oss__javascript__integrations__splitters#009 ---
```

import { TokenTextSplitter } from "@langchain/textsplitters";



const splitter = new TokenTextSplitter({ encodingName: "cl100k_base", chunkSize: 100, chunkOverlap: 0 })

const texts = splitter.splitText(document)

```
--- 片段[3] oss__python__integrations__document_loaders#012 ---
DoclingLoader |  | | Azure blob storage loader |  | | FlatmarkLoader |  | | FirecrawlLoader |  | | OpenDocKitLoader |  | | OpenDataLoader PDF |  | | AnakinLoader |  | | Docugami |  | | HwpHwpxLoader |  | | PDFParser |  | | SingleStoreLoader |  | | YoutubeLoaderDL |  | | SuperPDFLoader |  | | MeshArcLoader |  | | HyperbrowserLoader |  | | FastOCRLoader |  | | ReplyLayerLoader |  | | HydrafetchLoader |  | | SecureLangChainLoader |  | | SpidraLoader |  | | PdfInspectorLoader |  | | WebCrawlerAPILoader |  | | CrwLoader |  | | Google bigtable |  | | Outline |  | | MinerULoader |  | | DiffbotCrawlLoader |  | | DiffbotExtractLoader |  | | DomPrunerLoader |  | | PolarisAIDataInsightLoader |  |
--- 片段[4] oss__python__integrations__document_loaders#004 ---
fbot Extract API | API | | Docling | Uses Docling to load and parse web pages | Package | | DomPruner | DOM AST pruning: loads web pages as compact Markdown with 97%+ token reduction, no API key | Package | | Firecrawl | Turns websites into clean, LLM-ready data via scrape/crawl/map/extract/search | API | | Hyperbrowser | Platform for running and scaling headless browsers, can be used to scrape/crawl any site | API | | OpeddFeedLoader | Load a licensed Opedd content catalog as Documents with licensing provenance | API | | ProxyHatLoader | Load web pages through ProxyHat residential proxies as Documents | API |
--- 片段[5] oss__javascript__langchain__quickstart#037 ---
"fetch_text_from_url", description: "Fetch the document from a URL.", schema: z.object({ url: z.string().url() }), }, ); const model = await initChatModel("gemini-3.1-pro-preview", { modelProvider: "google", temperature: 0.5, timeout: 600_000, maxTokens: 25000, streaming: true, }); const checkpointer = new MemorySaver(); async function main() { const agent = createAgent({ model, tools: [fetchTextFromUrl], systemPrompt: SYSTEM_PROMPT, checkpointer, }); const deepAgent = createDeepAgent({ model, tools: [fetchTextFromUrl], systemPrompt: SYSTEM_PROMPT, checkpointer, }); const content = `Project Gutenberg hosts a full plain-text copy of F. Scott Fitzgerald's The Great Gatsby. URL:

### 98. v1-D-023 [paraphrase] score=1.0
Q: openwiki 页面上的生成时间戳，如果我只改了 frontmatter、正文一个字没动，它会往前走吗？
GOLD: 不会。更新时只要正文有变化（哪怕只是空白字符）时间戳就会前进；正文没变则保留之前那次事件，只改 front-matter 不推进它。新页面和刚初始化的页面会带上 generated: {by, at}，producer 记为 openwiki/<version>。
ANSWER: 结论：不会。只改 front-matter、正文没变时，生成时间戳不会前进；只有正文发生变化（包括空白字符变化）才会推进时间戳 [1]。

补充说明：
- 正文有任何改动（哪怕只是空白）都会推进 stamp；正文不变则保留之前的事件 [1]。
- 仅 front-matter 的改动不会推进它 [1]。
- 生产者会被标记为 `openwiki/<version>`（或 coding-agent host）[1]。

给出的文档片段里没有提供可直接运行的示例代码，因此这里不附代码示例。
--- 片段[1] oss__openwiki__code-mode#010 ---
- New and freshly initialized pages receive generated: {by, at} . During updates, any body change, including whitespace, advances the stamp; an unchanged body retains its prior event, and front-matter-only changes do not advance it. The producer is stamped as openwiki/<version> (or the coding-agent host)
--- 片段[2] oss__openwiki__code-mode#003 ---
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
--- 片段[3] oss__openwiki__customize#002 ---
- AGENTS.md : Created when missing. OpenWiki rewrites only the <!-- OPENWIKI:START --> … <!-- OPENWIKI:END --> block and leaves the rest of your content untouched
--- 片段[4] oss__openwiki__cli-reference#000 ---
``` # Interactive chat in code mode (current repository) openwiki openwiki "Please generate documentation for this repository" # Personal mode openwiki personal openwiki personal --init openwiki personal --update # Explicit code mode openwiki code --init openwiki code --update openwiki code --update --print # Defaults to code mode and specify a language openwiki --init openwiki --update openwiki --init --language ko # One-shot print mode openwiki -p "Summarize what you can do" # Explore the wiki locally or export a static visualizer openwiki visualize openwiki visualize openwiki --port 4400 --no-open openwiki visualize openwiki --export docs/openwiki-visualizer
--- 片段[5] oss__openwiki__integrations#008 ---
- deferUnplannedClaimIssues (optional boolean , default false ): When true , OpenWiki skips inserting automatic jobs for unplanned pages with Claim issues. Those pages are recorded as deferred, and the run finishes in an interrupted state until a future full update reconciles them. When true , OpenWiki skips inserting automatic jobs for unplanned pages with Claim issues. Those pages are left untouched, and the run completes but records its update metadata as interrupted until a future full update reconciles them. This option is valid only on update runs. Setting it on an init run returns an invalid_input error.

### 99. v1-D-024 [no-answer] score=None
Q: Haystack 2.x 里 Pipeline.run 的 include_outputs_from 参数该怎么写？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

现有片段只涉及 LangGraph 前端（`PipelineProgress` 组件、`injectStream`/`useStream` 的 Angular 用法）以及 LangChain 模型结构化输出中的 `include_raw=True`，没有任何关于 Haystack 2.x 或 `Pipeline.run` 的 `include_outputs_from` 参数的说明，因此无法给出写法或示例。

另外提示一处名称差异：片段 [3] 中出现的是 LangChain 的 `include_raw=True`（用于同时获取解析结果和原始 AI 消息），与您问的 Haystack `include_outputs_from` 不是同一个 API，请勿混淆。
--- 片段[1] oss__python__langgraph__frontend__graph-execution#008 ---
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
--- 片段[2] oss__javascript__langgraph__frontend__graph-execution#008 ---
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
--- 片段[3] oss__python__langchain__models#044 ---
- Include raw : Set include_raw=True to get both the parsed output and the raw AI message.
--- 片段[4] oss__javascript__langgraph__frontend__graph-execution#005 ---
``` import { Component, computed } from "@angular/core"; import { injectStream } from "@langchain/angular"; const AGENT_URL = "http://localhost:2024"; @Component({ selector: "app-pipeline-chat", template: ` <div> <app-pipeline-progress [nodes]="graphNodes()" [isLoading]="stream.isLoading()" /> <app-node-card-list [nodes]="graphNodes()" [stream]="stream" [isLoading]="stream.isLoading()" /> </div> `, }) export class PipelineChatComponent { stream = injectStream<typeof myAgent>({ apiUrl: AGENT_URL, assistantId: "graph_execution_cards", }); graphNodes = computed(() => [...this.stream.subgraphs().values()]); } ```
--- 片段[5] oss__python__langgraph__frontend__graph-execution#005 ---
``` import { Component, computed } from "@angular/core"; import { injectStream } from "@langchain/angular"; const AGENT_URL = "http://localhost:2024"; @Component({ selector: "app-pipeline-chat", template: ` <div> <app-pipeline-progress [nodes]="graphNodes()" [isLoading]="stream.isLoading()" /> <app-node-card-list [nodes]="graphNodes()" [stream]="stream" [isLoading]="stream.isLoading()" /> </div> `, }) export class PipelineChatComponent { stream = injectStream<typeof myAgent>({ apiUrl: AGENT_URL, assistantId: "graph_execution_cards", }); graphNodes = computed(() => [...this.stream.subgraphs().values()]); } ```

### 100. v1-D-025 [no-answer] score=None
Q: LangSmith 企业版的 SLA 承诺几个 9？超时赔付怎么算？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

现有片段只涉及 LangSmith tracing 的可选配置（如设置 `LANGSMITH_TRACING`、`LANGSMITH_API_KEY`）[1][2][4]，以及一处提到 LangSmith 用于 tracing 的可选/必需场景 [5]，但都没有提及「企业版 SLA 承诺几个 9」或「超时赔付计算方式」的任何信息。

要回答这个问题，需要补充包含 LangSmith 企业版服务等级协议（SLA）、可用性承诺（如 99.9% 等）以及违约赔付条款的文档片段。
--- 片段[1] oss__python__langgraph__quickstart#014 ---
n "tool_node" # Otherwise, we stop (reply to the user) return END # Step 7: Build and compile the agent # Build workflow agent_builder = StateGraph(MessagesState) # Add nodes agent_builder.add_node("llm_call", llm_call) agent_builder.add_node("tool_node", tool_node) # Add edges to connect nodes agent_builder.add_edge(START, "llm_call") agent_builder.add_conditional_edges( "llm_call", should_continue, ["tool_node", END] ) agent_builder.add_edge("tool_node", "llm_call") # Compile the agent agent = agent_builder.compile() # Step 8: Set up LangSmith tracing (optional) # export LANGSMITH_TRACING=true # export LANGSMITH_API_KEY="your-langsmith-api-key" # Step 9: Run the agent
--- 片段[2] oss__javascript__langgraph__quickstart#017 ---
t = new StateGraph(MessagesState) .addNode("llmCall", llmCall) .addNode("toolNode", toolNode) .addEdge(START, "llmCall") .addConditionalEdges("llmCall", shouldContinue, ["toolNode", END]) .addEdge("toolNode", "llmCall") .compile(); // Step 8: Set up LangSmith tracing (optional) // export LANGSMITH_TRACING=true // export LANGSMITH_API_KEY="your-langsmith-api-key" // Step 9: Run the agent const result = await agent.invoke({ messages: [new HumanMessage("Add 3 and 4.")], }); for (const message of result.messages) { console.log(`[${message.type}]: ${message.text}`); } ```
--- 片段[3] oss__javascript__langchain__multi-agent__skills-sql-assistant#031 ---
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
--- 片段[4] oss__python__langgraph__quickstart#015 ---
g (optional) # export LANGSMITH_TRACING=true # export LANGSMITH_API_KEY="your-langsmith-api-key" # Step 9: Run the agent from langchain.messages import HumanMessage messages = [HumanMessage(content="Add 3 and 4.")] messages = agent.invoke({"messages": messages}) for m in messages["messages"]: m.pretty_print() ```
--- 片段[5] oss__javascript__deepagents__deep-research#001 ---
- LangSmith for tracing (optional if you are using the SDK; required for Managed Deep Agents)
