### 26. v1-B-001 [single-hop] score=1.0
Q: LangGraph 的流式输出里 values、updates、messages 这几种 stream mode 到底差在哪？另外哪些模式必须先有 checkpointer 才能用？
GOLD: 按流模式对照表，values 模式在每个步骤之后给出完整 state（ValuesStreamPart）；updates 模式只给出该步的状态更新（UpdatesStreamPart），同一步里的多个更新会被分别流式输出；messages 模式给出 LLM 调用产生的 (LLM token, metadata) 二元组（MessagesStreamPart），custom 模式则承载节点通过 get_stream_writer 发出的自定义数据。checkpoints 和 tasks 两种模式都标注了 Requires a checkpointer，没有 checkpointer 就用不了。
ANSWER: 结论：

- `values`：每一步之后输出**完整状态**（Full state after each step）[1]。
- `updates`：每一步之后输出**状态更新**；同一步里的多个更新会**分别**流式输出 [1]。
- `messages`：输出 LLM 调用产生的 **(LLM token, metadata) 二元组** [1]。
- 需要 checkpointer 才能用的模式：`checkpoints` 和 `tasks` [1]。

补充说明（以片段为准）：

- 片段里 `messages` 的描述是 “2-tuples of (LLM token, metadata) from LLM calls” [1]；而在示例代码中，使用 `version="v2"` 时结构变为 `chunk["type"] == "messages"`、`chunk["data"]` 解包为 `(msg, metadata)` [5]。也就是说，v2 统一 StreamPart 格式下取数方式与默认二元组形式不同，注意按版本区分。
- `custom` 模式用于节点通过 `get_stream_writer` 发出的自定义数据 [1]，不属于你问的三种，但同表列出。

最小可用示例（Python，按片段 [5] 的写法）：

```python
# messages 模式：流式拿到 LLM token 与 metadata
for chunk in graph.stream(
    inputs,
    stream_mode="messages",
    version="v2",
):
    if chunk["type"] == "messages":
        msg, metadata = chunk["data"]
        if msg.content and metadata["langgraph_node"] == "some_node_name":
            ...
```

```python
# 同时订阅多种模式（参考片段 [4] 的 JS 用法，Python 侧对应 stream_mode 传列表）
for chunk in graph.stream(inputs, stream_mode=["messages", "updates"]):
    mode, data = chunk
    ...
```

如果你要的是 `values` / `updates` 的具体返回结构示例，给出的文档片段里只有表格描述，没有对应代码示例，这部分无法据片段展开。
--- 片段[1] oss__python__langgraph__streaming#010 ---
| Mode | Type | Description | | --- | --- | --- | | values | ValuesStreamPart | Full state after each step. | | updates | UpdatesStreamPart | State updates after each step. Multiple updates in the same step are streamed separately. | | messages | MessagesStreamPart | 2-tuples of (LLM token, metadata) from LLM calls. | | custom | CustomStreamPart | Custom data emitted from nodes via get_stream_writer . | | checkpoints | CheckpointStreamPart | Checkpoint events (same format as get_state() ). Requires a checkpointer. | | tasks | TasksStreamPart | Task start/finish events with results and errors. Requires a checkpointer. |
--- 片段[2] oss__javascript__langchain__streaming#041 ---
- LangGraph streaming —Advanced streaming options including values , debug modes, and subgraph streaming
--- 片段[3] oss__python__langchain__streaming#081 ---
- LangGraph streaming —Advanced streaming options including values , debug modes, and subgraph streaming
--- 片段[4] oss__javascript__deepagents__human-in-the-loop#011 ---
``` import { v7 as uuid7 } from "uuid"; import { Command } from "@langchain/langgraph"; const config = { configurable: { thread_id: uuid7() } }; let streamInput: Record<string, any> | Command = { messages: [{ role: "user", content: "Delete the file temp.txt" }], }; while (true) { let pendingInterrupt: { value: any } | undefined; for await (const chunk of await agent.stream( streamInput, { streamMode: ["messages", "updates"], ...config, } )) { const [mode, data] = chunk; if (mode === "messages") { const [token] = data; // Display tokens in real time if (token.text) { process.stdout.write(token.text); } } if (mode === "updates" && data?.__interrupt__) {
--- 片段[5] oss__python__langgraph__streaming#030 ---
```

# The "messages" stream mode streams LLM tokens with metadata

# Use version="v2" for a unified StreamPart format

for chunk in graph.stream(

    inputs,

    stream_mode="messages",

    version="v2",

):

    if chunk["type"] == "messages":

        msg, metadata = chunk["data"]

        # Filter the streamed tokens by the langgraph_node field in the metadata

        # to only include the tokens from the specified node

        if msg.content and metadata["langgraph_node"] == "some_node_name":

            ...

```

### 27. v1-B-002 [single-hop] score=0.0
Q: 我用 get_state() 拿到一个状态快照，想确认图是不是已经跑完、以及这个检查点是被输入还是被循环触发的，应该看哪些字段？
GOLD: 先看 next 字段：它是接下来要执行的节点名元组，空元组 () 表示整张图已经完成。再看 metadata，它记录执行元数据，其中 source 的取值是 "input"、"loop" 或 "update"，另外还包含 writes（节点输出）和 step（super-step 计数）。此外 config 里带 thread_id、checkpoint_ns 和 checkpoint_id，parent_config 在第一个检查点时为 None。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 片段 [1][4][5] 只说明 `graph.get_state(config)` 返回最新检查点（或指定 `checkpoint_id` 的检查点），[1] 提到它包含线程暂停在哪个节点以及待处理的 interrupt，但没有说明如何判断「图是否已跑完」。
- 片段 [3] 展示了 `StateSnapshot` 上可访问的字段：`next`、`metadata.step`、`metadata.source`（示例中 `"update"` 表示由 `updateState` 创建）、`tasks[].interrupts`。但片段没有解释「输入触发」与「循环触发」分别对应 `metadata.source` 的哪个取值，也没有说明判断「已跑完」应看 `next` 为空还是别的条件。
- 因此无法根据现有片段给出「看哪些字段判断是否跑完 / 是输入还是循环触发」的结论。

另外提示一处可能的差异：你问的是 `get_state()`，片段中 Python 写法是 `graph.get_state(config)` [4][5]，JS 写法是 `graph.getStateHistory(config)` 用于历史 [3]；片段里没有出现无参数的 `get_state()` 调用形式。
--- 片段[1] oss__python__langgraph__backward-compatibility#011 ---
- graph.get_state(config) returns the latest checkpoint, including which node the thread is paused at and any pending interrupts.
--- 片段[2] oss__python__langgraph__backward-compatibility#010 ---
- Use time travel and graph.get_state to spot-check existing threads against the new code in a staging deployment before rolling out.
--- 片段[3] oss__javascript__langgraph__checkpointers#023 ---
```

const history: StateSnapshot[] = [];

for await (const state of graph.getStateHistory(config)) {

  history.push(state);

}



// Find the checkpoint before a specific node executed

const beforeNodeB = history.find((s) => s.next.includes("nodeB"));



// Find a checkpoint by step number

const step2 = history.find((s) => s.metadata.step === 2);



// Find checkpoints created by updateState

const forks = history.filter((s) => s.metadata.source === "update");



// Find the checkpoint where an interrupt occurred

const interrupted = history.find(

  (s) => s.tasks.length > 0 && s.tasks.some((t) => t.interrupts.length > 0)

);

```
--- 片段[4] oss__python__langgraph__checkpointers#014 ---
```

# get the latest state snapshot

config = {"configurable": {"thread_id": "1"}}

graph.get_state(config)



# get a state snapshot for a specific checkpoint_id

config = {"configurable": {"thread_id": "1", "checkpoint_id": "1ef663ba-28fe-6528-8002-5a559208592c"}}

graph.get_state(config)

```
--- 片段[5] oss__python__langgraph__add-memory#086 ---
```

config = {

    "configurable": {

        "thread_id": "1",

        # optionally provide an ID for a specific checkpoint,

        # otherwise the latest checkpoint is shown

        # "checkpoint_id": "1f029ca3-1f5b-6704-8004-820c16b69a5a"  



    }

}

graph.get_state(config)

```

### 28. v1-B-003 [single-hop] score=1.0
Q: durability 设成 "exit" 的时候，图的状态到底什么时候才落盘？为什么文档说它对长跑图性能最好，却要小心进程被杀？
GOLD: "exit" 模式下 LangGraph 只在图执行退出时才持久化变更——无论是正常成功、以错误结束，还是因为 human-in-the-loop 中断而退出，都算一次退出。这样对长时间运行的图性能最好，但代价是中间状态不会被保存，所以进程崩溃这类系统故障发生时，无法在执行中途恢复。
ANSWER: 结论：`"exit"` 模式下，LangGraph 只在图执行**退出**时才持久化变更——即成功结束、出错结束，或因为 human-in-the-loop 中断而退出 [1][2]。执行过程中的中间状态不会保存，所以进程崩溃这类系统故障发生在执行中途时无法恢复 [1][2]。在新线程上，运行结束前根本不存在 checkpoint，运行期间崩溃则不会留下该线程的任何记录 [3][4]。

关于“对长跑图性能最好却要小心进程被杀”：片段只说明该模式对长跑图提供最佳性能，原因是它不在中途写状态；代价正是中间状态不落盘，进程崩溃无法从执行中途恢复 [1][2]。片段没有进一步解释性能优势的实现细节。

最小示例（片段未给出代码，以下仅为模式取值示意，非文档原文）：

```python
# durability="exit"
graph.invoke(inputs, config={"durability": "exit"})
```

补充说明：片段中只出现了 `"exit"` 和 `"async"` 两种取值；`"async"` 是在下一步执行时异步持久化，性能与持久性较好，但进程在执行期间崩溃时仍有小概率不写 checkpoint [5]。
--- 片段[1] oss__python__langgraph__checkpointers#025 ---
- "exit" : LangGraph persists changes only when graph execution exits — successfully, with an error, or due to a human-in-the-loop interrupt. This provides the best performance for long-running graphs but means intermediate state is not saved, so you cannot recover from system failures (like process crashes) mid-execution.
--- 片段[2] oss__javascript__langgraph__checkpointers#026 ---
- "exit" : LangGraph persists changes only when graph execution exits — successfully, with an error, or due to a human-in-the-loop interrupt. This provides the best performance for long-running graphs but means intermediate state is not saved, so you cannot recover from system failures (like process crashes) mid-execution.
--- 片段[3] oss__python__langgraph__checkpointers#028 ---
- "exit" : No checkpoint exists until the run ends. A crash during the run leaves no record of the thread.
--- 片段[4] oss__javascript__langgraph__checkpointers#029 ---
- "exit" : No checkpoint exists until the run ends. A crash during the run leaves no record of the thread.
--- 片段[5] oss__javascript__langgraph__checkpointers#027 ---
- "async" : LangGraph persists changes asynchronously while the next step executes. This provides good performance and durability, but there is a small risk that LangGraph does not write checkpoints if the process crashes during execution.

### 29. v1-B-004 [single-hop] score=0.5
Q: 给 deep agents 的子智能体配 mode 时，isolated 和 fork 该怎么选？fork 会不会把父 agent 的技能和提示词一起带过去？
GOLD: 按 Isolated（默认）与 Forked 的对照表，isolated 只把你在任务里传进去的那段描述给子智能体，系统提示和技能由你自己在子智能体上设；fork 则拿到父 agent 当前生效的对话历史和继承状态，并继承技能与父 agent 的基础提示词，可选的 system_prompt 会随 task 消息一起送达，以保留缓存复用。两者还有个关键差别：isolated 子智能体可以继续用 task 工具再派活，而 forked 不能再调用 task，必须自己把工作做完。
ANSWER: **结论**

1. `mode` 默认是 `"isolated"`：每次调用都会创建一个新的 agent 实例，子智能体只看到被委派的任务，看不到父 agent 的对话历史 [1][2][3][4][5]。
2. 设为 `"fork"` 时，子智能体会继承父 agent 的完整对话历史；在 Deep Agents 里还会继承父 agent 的 system prompt [3][4][5]。
3. 选择建议：任务需要很少的先前上下文、希望保持上下文隔离时，用 `isolated`；要接着父 agent 已经开始的活干时，用 `fork`。代价是 `fork` 的 prompt 更大、隔离性更弱 [5]。
4. 关于“技能和提示词”：片段只明确说 `fork` 会继承父 agent 的**对话历史**和 **system prompt** [3][4][5]。至于“技能”（tools）是否随 `fork` 一起带过去，片段没有直接说明；片段只提到 `tools` 字段本身的行为（JS 版默认继承主 agent 的工具，显式指定则完全覆盖 [4]；Python 版要求子智能体自己定义、不从主 agent 继承 [3]）。因此不能据片段断定 `fork` 会带上父 agent 的技能。

**最小可用示例**（字段名以片段为准）

```python
subagent = {
    "name": "researcher",
    "description": "...",
    "instructions": "...",   # fork 时父 system prompt 保持不变，这段指令在继承的对话之后随任务消息传入 [3]
    "mode": "fork",          # 省略则默认 "isolated" [3][4]
    "tools": [...],          # 可选，保持最小化 [3][4]
}
```

**差异提示**：你问的是“技能和提示词一起带过去”。片段能确认的是 `fork` 会带 **system prompt** 和对话历史 [3][4][5]；**技能/工具**是否随 `fork` 继承，给出的文档里没有找到能回答这个问题的内容，缺少对 `mode: "fork"` 与 `tools` 继承关系之间交互的说明。
--- 片段[1] oss__javascript__deepagents__overview#028 ---
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
--- 片段[2] oss__python__deepagents__overview#036 ---
- Isolated or inherited context : By default, each invocation creates a new agent instance with its own context ( mode: "isolated" ). Use mode: "fork" to inherit the parent’s full conversation history instead. See Forked subagents .
--- 片段[3] oss__python__deepagents__subagents#003 ---
nts must define their own. Include tool usage guidance and output format requirements. Does not inherit from main agent. For mode: "fork" , the fork keeps the parent’s system prompt unchanged and delivers these instructions with the task message after the inherited conversation, preserving the parent’s cached prompt prefix. See Forked subagents . | | mode | "isolated" \| "fork" | Optional. Context mode. Defaults to "isolated" , where the subagent only sees the delegated task. Set to "fork" to inherit the parent’s conversation and system prompt instead. See Forked subagents . | | tools | list[Callable] | Optional. Tools the subagent can use. Keep this minimal and include only what’s needed.
--- 片段[4] oss__javascript__deepagents__subagents#003 ---
nts must define their own. Include tool usage guidance and output format requirements. Does not inherit from main agent. For mode: "fork" , omit this field unless you need a fork-only addendum. See Forked subagents . | | mode | "isolated" \| "fork" | Optional. Context mode. Defaults to "isolated" , where the subagent only sees the delegated task. Set to "fork" to inherit the parent’s conversation and system prompt instead. See Forked subagents . | | tools | StructuredTool[] | Optional. Tools the subagent can use. Keep this minimal and include only what’s needed. Inherits from main agent by default. When specified, overrides the inherited tools entirely. |
--- 片段[5] oss__javascript__langchain__multi-agent__subagents#041 ---
| Mode | Subagent receives | Best for | Tradeoff |

| --- | --- | --- | --- |

| Isolated (default) | Only the task description | Focused work that needs little prior context | Context isolation, but re-derives everything the parent already did |

| Forked | The parent’s conversation history (and, in Deep Agents, the system prompt) | Continuing a task the parent already started | Seeded with prior context, at the cost of a larger prompt and less isolation |

### 30. v1-B-005 [single-hop] score=1.0
Q: Deep Agents 里的 skills、memory、tools 经常被混着提，它们在用途、加载时机、文件格式和覆盖顺序上分别有什么不同？
GOLD: 按对照表，用途上 skills 是通过 progressive disclosure 按需发现的能力，memory 是启动时加载的持久上下文，tools 是 agent 每轮都能调用的程序化动作。加载时机上 skills 只在 agent 判断相关时才读取，memory 在 agent 启动时加载，tools 则每轮都可用；格式上 skills 是放在具名目录里的 SKILL.md，memory 是 AGENTS.md 文件，tools 是绑定到 agent 的函数。覆盖顺序上两者都是先用户级再项目级，但 skills 是后者覆盖前者（last wins），memory 是两者合并（combined）。
ANSWER: **结论：** 三者定位不同——skills 是按需发现的能力，memory 是启动时加载的持久上下文，tools 是每轮都可调用的程序化动作 [1][2]。

| 维度 | Skills | Memory | Tools |
|---|---|---|---|
| 用途 | 通过渐进式披露按需发现的能力 [1][2] | 启动时加载的持久上下文 [1][2] | Agent 可调用的程序化动作 [1][2] |
| 加载时机 | 仅当 agent 判断相关时才读取 [1][2] | agent 启动时加载 [1][2] | 每一轮都可用 [1][2] |
| 文件格式 | 命名目录中的 `SKILL.md` [1][2] | `AGENTS.md` 文件 [1][2] | 绑定到 agent 的函数 [1][2] |
| 覆盖顺序 | 先 user，再 project（后者胜出）[1][2] | 先 user，再 project（合并）[1][2] | 在 agent 创建时定义 [1][2] |

**最小可用示例（JavaScript 配置项）：**

```javascript
const agent = {
  model: "...",
  systemPrompt: "...",
  tools: [/* 域工具 */],
  memory: ["AGENTS.md"],        // 启动时加载
  skills: ["./skills"],         // 按需读取的 SKILL.md 目录
};
```

配置参数中 `memory` 描述为“启动时加载的 AGENTS.md 文件”，`skills` 描述为“用于按需知识的 skills 目录” [3]；ACP 的 agent 配置里 `skills` 是技能源路径数组、`memory` 是记忆源路径数组（AGENTS.md）[4]。

**注意差异：** 你提到“覆盖顺序”，片段中只有 skills 和 memory 有分层/覆盖说明（skills 后者胜出、memory 合并），tools 没有覆盖顺序概念，它是在 agent 创建时定义的 [1][2]。
--- 片段[1] oss__python__deepagents__skills#134 ---
|  | Skills | Memory | Tools | | --- | --- | --- | --- | | Purpose | On-demand capabilities discovered through progressive disclosure | Persistent context loaded at startup | Programmatic actions the agent can call | | Loading | Read only when the agent determines relevance | Loaded at agent start | Available every turn | | Format | SKILL.md in named directories | AGENTS.md files | Functions bound to the agent | | Layering | User, then project (last wins) | User, then project (combined) | Defined at agent creation |
--- 片段[2] oss__javascript__deepagents__skills#134 ---
|  | Skills | Memory | Tools | | --- | --- | --- | --- | | Purpose | On-demand capabilities discovered through progressive disclosure | Persistent context loaded at startup | Programmatic actions the agent can call | | Loading | Read only when the agent determines relevance | Loaded at agent start | Available every turn | | Format | SKILL.md in named directories | AGENTS.md files | Functions bound to the agent | | Layering | User, then project (last wins) | User, then project (combined) | Defined at agent creation |
--- 片段[3] oss__javascript__deepagents__customization#008 ---
| Parameter | What it does | | --- | --- | | model | Which model to use | | systemPrompt | Custom instructions for the agent | | tools | Domain tools the agent can call | | memory | AGENTS.md files loaded at startup | | skills | Skills directory for on-demand knowledge | | backend | Filesystem backend (StateBackend by default) | | permissions | Path-level access control for the filesystem | | subagents | Custom subagents for delegated tasks | | middleware | Extra middleware appended to the Deep Agents stack | | interruptOn | Pause before tool calls for human approval | | responseFormat | Structured output schema |
--- 片段[4] oss__javascript__deepagents__acp#017 ---
| Option | Type | Description | | --- | --- | --- | | name | string | Unique agent name (required) | | description | string | Agent description | | model | string | LLM model (default: "claude-sonnet-4-5-20250929" ) | | tools | StructuredTool[] | Custom LangChain tools | | systemPrompt | string | Custom system prompt | | middleware | AgentMiddleware[] | Custom middleware appended to the Deep Agents stack | | backend | AnyBackendProtocol | Filesystem backend | | skills | string[] | Skill source paths | | memory | string[] | Memory source paths (AGENTS.md) | | interruptOn | Record<string, boolean \| InterruptOnConfig> | Tools requiring user approval (HITL) |
--- 片段[5] oss__python__langchain__quickstart#050 ---
- Deep Agents : Customization options , persistent memory , deploy to production

### 31. v1-B-006 [single-hop] score=0.5
Q: 默认情况下 interpreter 里能读文件、发网络请求、执行 shell 吗？如果确实需要放开这些能力，正确做法是什么？
GOLD: 按安全能力表，JavaScript 执行、top-level await、console.log/warn/error 捕获默认可用；而 agent 工具、filesystem 访问、network 访问、wall-clock 或 datetime 访问默认都不可用。放开的方式各不相同：加 PTC allowlist 暴露 agent 工具，设 fs 或通过 PTC allowlist 加内置文件工具，通过 PTC 暴露某个具体网络工具，需要时间就显式提供一个时间工具。至于 shell 命令、装包、跑测试这类 OS 级执行，正确的方向是用 sandbox backend，而不是在 interpreter 里开开关。
ANSWER: **结论：默认都不能。** 文件系统访问、网络访问、Shell 命令/包安装/测试/OS 级执行，在 interpreter 中默认均不可用 [1][2]。

具体默认状态与放开方式：

| 能力 | 默认可用 | 放开方式 |
| --- | --- | --- |
| 文件系统访问 | 否 | 设置 `fs`，或通过 PTC allowlist 添加内置文件系统工具 [1][2] |
| 网络访问 | 否 | 通过 PTC 暴露特定的网络工具 [1][2] |
| Shell 命令、包安装、测试、OS 级执行 | 否 | 使用 sandbox 后端 [1][2] |

另外，若需求本身就是 Shell 命令、包安装、测试或完整 OS 文件系统访问，文档建议直接选用 **Sandboxes** 模式 [3][4]。

**最小示例（Python，示意配置项）：**

```python
# 放开文件系统：设置 fs（True 表示复用 create_deep_agent 的后端）
interpreter = ...  # 具体构造方式片段未给出
# fs=True

# 放开网络：通过 PTC allowlist 暴露特定网络工具
# ptc=["your_network_tool"]

# Shell / 包安装 / 测试 / OS 级执行：使用 sandbox 后端
```

**需要指出的差异/缺口：**
- 片段只给出了配置项名称（`fs`、PTC allowlist、sandbox 后端），**没有给出完整的构造代码**，因此上面的示例仅为配置项示意，不能当作可直接运行的完整代码。
- Python 与 JavaScript 版本在 `console` 捕获参数上命名不同：Python 为 `capture_console=False` [1]，JavaScript 为 `captureConsole: false` [2]；提问未涉及，但若你混用两版文档需注意。
- 片段 [5] 提到 `max_ptc_calls` 默认 256，且 `None` 仅应在可信环境使用 [5]，这与“放开能力需谨慎”的安全取向一致，但片段未展开更多安全细节。
--- 片段[1] oss__python__deepagents__interpreters#057 ---
| Capability | Available by default | How to expose it |

| --- | --- | --- |

| JavaScript execution | Yes | Add interpreter middleware |

| Top-level await | Yes | Use promises in interpreter code |

| console.log , warn , error capture | Yes | Disable with capture_console=False |

| Agent tools | No | Add a PTC allowlist |

| Filesystem access | No | Set fs , or add the built-in filesystem tools via the PTC allowlist |

| Network access | No | Expose a specific network tool through PTC |

| Wall-clock or datetime access | No | Expose an explicit time tool if needed |

| Shell commands, package installs, tests, OS-level execution | No | Use a sandbox backend |
--- 片段[2] oss__javascript__deepagents__interpreters#025 ---
| Capability | Available by default | How to expose it |

| --- | --- | --- |

| JavaScript execution | Yes | Add interpreter middleware |

| Top-level await | Yes | Use promises in interpreter code |

| console.log , warn , error capture | Yes | Disable with captureConsole: false |

| Agent tools | No | Add a PTC allowlist |

| Filesystem access | No | Add the built-in filesystem tools via the PTC allowlist |

| Network access | No | Expose a specific network tool through PTC |

| Wall-clock or datetime access | No | Expose an explicit time tool if needed |

| Shell commands, package installs, tests, OS-level execution | No | Use a sandbox backend |
--- 片段[3] oss__python__deepagents__interpreters#001 ---
| Need | Use |

| --- | --- |

| One or two simple external calls | Normal tool calling |

| Pure in-memory JavaScript: loops, branches, retries, or data transforms (no external tools) | Interpreter |

| Many external tool calls orchestrated from code (requires PTC ) | Interpreter with programmatic tool calling (PTC) |

| Many independent units of work, multiple perspectives, or recursive analysis over large inputs | Interpreter with dynamic subagents |

| Shell commands, package installs, tests, or full OS filesystem access | Sandboxes |
--- 片段[4] oss__javascript__deepagents__interpreters#001 ---
| Need | Use |

| --- | --- |

| One or two simple external calls | Normal tool calling |

| Pure in-memory JavaScript: loops, branches, retries, or data transforms (no external tools) | Interpreter |

| Many external tool calls orchestrated from code (requires PTC ) | Interpreter with programmatic tool calling (PTC) |

| Many independent units of work, multiple perspectives, or recursive analysis over large inputs | Interpreter with dynamic subagents |

| Shell commands, package installs, tests, or full OS filesystem access | Sandboxes |
--- 片段[5] oss__python__deepagents__interpreters#059 ---
wlist of tool names or BaseTool instances exposed as tools.* inside the interpreter. Omit to disable. See Enable PTC . | | max_ptc_calls | 256 | Maximum tools.* calls allowed per eval . Set to None only in trusted environments. See Programmatic tool calling (PTC) and Security . | | subagents | True | Expose the built-in task() global when the agent has subagents. Set to False to require dispatch through the normal task tool. See Dynamic subagents . | | fs | None | Give interpreter code a Node-style fs global over a backend. True uses the backend from create_deep_agent . See Files ( fs ) . | | mode | "thread" | Control interpreter persistence:

### 32. v1-B-007 [single-hop] score=1.0
Q: deep agent 默认把文件写在哪？为什么同一个 agent 换个线程就读不到之前写的文件了？
GOLD: 默认后端是 thread-scoped 的：文件存在 langgraph state 里，靠你的 checkpointer 在同一个线程内跨轮次保留，但不跨线程共享，所以换一个线程就看不到之前写的文件。想真正落到本地磁盘可以换成 FilesystemBackend，注意任何提供的 root_dir 都必须是绝对路径。
ANSWER: **结论：**

1. 默认后端是 **thread 作用域**的，文件存储在 **LangGraph state** 里，通过 checkpointer 在同一线程的多个轮次之间持久化，但**不跨线程共享** [1][2]。所以换一个线程就读不到之前写的文件——因为默认后端的数据本来就绑定在单个 thread 上。

2. 如果希望 agent 访问本地机器文件系统并跨线程持久化，需要显式传入 `FilesystemBackend(root_dir=...)`，且 `root_dir` 必须是**绝对路径** [1][2]。

3. 另外，Deep Agents 会把内部数据（offloaded tool results、conversation history）写到默认后端；若想让这些产物是临时的、不落盘，可用 `StateBackend` 作为默认后端 [3][4]。

**最小可用示例（默认，thread 作用域）：**

```python
agent = create_deep_agent(model="google_genai:gemini-4-hydrogen")
```

**改为本地文件系统持久化（跨线程可读）：**

```python
agent = create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")
)
```

**说明与差异提示：**
- 片段中示例的模型名是 `"google_genai:gemini-4-hydrogen"` [1][2]，与常见模型命名可能不同，请以片段为准。
- 片段 [2] 来源标注为 JavaScript 文档，但示例代码写法与 Python 片段 [1] 一致，此处按片段原文呈现，未做改写。
--- 片段[1] oss__python__deepagents__backends#001 ---
| Built-in backend | Description | | --- | --- | | Default | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen") Thread-scoped. The default filesystem backend for an agent is stored in langgraph state. Files persist across turns within a thread (via your checkpointer) and are not shared across threads. | | Local filesystem persistence | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")) This gives the deep agent access to your local machine’s filesystem. You can specify the root directory that the agent has access to. Note that any provided root_dir must be an absolute path.
--- 片段[2] oss__javascript__deepagents__backends#001 ---
| Built-in backend | Description | | --- | --- | | Default | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen") Thread-scoped. The default filesystem backend for an agent is stored in langgraph state. Files persist across turns within a thread (via your checkpointer) and are not shared across threads. | | Local filesystem persistence | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")) This gives the deep agent access to your local machine’s filesystem. You can specify the root directory that the agent has access to. Note that any provided root_dir must be an absolute path.
--- 片段[3] oss__javascript__deepagents__backends#072 ---
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
--- 片段[4] oss__python__deepagents__backends#087 ---
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
--- 片段[5] oss__python__deepagents__overview#019 ---
```

from deepagents import create_deep_agent

from deepagents.middleware import FilesystemMiddleware



# Read-only agent: write_file, edit_file, delete, and execute are never shown

agent = create_deep_agent(

    model="claude-sonnet-4-6",

    middleware=[

        FilesystemMiddleware(backend=backend, tools=["read_file", "ls", "glob", "grep"]),

    ],

)

```

### 33. v1-B-008 [single-hop] score=1.0
Q: 同步子智能体和异步子智能体在「谁来等结果」「能不能中途追加指令」「能不能取消」上有什么不同？
GOLD: 同步模式由 supervisor 阻塞等待子智能体完成，异步模式则立刻返回一个 task ID、supervisor 继续往下走。中途追加指令同步做不到，异步可以用 update_async_task 补充后续指令；取消方面同步只能把 supervisor 一起停掉，异步可以用 cancel_async_task 取消任务。状态上前者是无状态的、调用之间不留状态，后者有状态，在服务器自己的线程上跨交互保持状态。
ANSWER: **结论：**

1. **谁来等结果**：同步模式下，主智能体（supervisor）会等待子智能体完成后才继续；异步模式下，主智能体在子智能体后台运行时继续做别的事 [3][4]。异步子智能体是有状态的，会在自己的线程上跨交互维护状态；同步子智能体是无状态的，调用之间没有持久状态 [1][2]。

2. **能不能中途追加指令**：同步模式不支持中途更新；异步模式可以通过 `update_async_task` 发送后续指令 [1][2]。

3. **能不能取消**：同步模式无法取消（除非停掉 supervisor）；异步模式可以通过 `cancel_async_task` 取消任务 [1][2]。

**最小可用示例（示意，片段未给出完整调用代码）：**

```python
# 异步子智能体（Python 侧，片段 [1] 提到的能力）
# 中途追加指令
update_async_task(task_id, "请补充导出 CSV 的步骤")

# 取消任务
cancel_async_task(task_id)
```

```javascript
// 异步子智能体（JavaScript 侧，片段 [2] 提到的能力）
update_async_task(taskId, "请补充导出 CSV 的步骤");
cancel_async_task(taskId);
```

**差异提示**：你问的是「同步子智能体和异步子智能体」，片段 [1][2] 的对比表正是 sync vs async subagents，API 名称以片段为准：追加指令是 `update_async_task`，取消是 `cancel_async_task`，检查状态是 `check_async_task` [1][2]。片段 [3][4] 只补充了「谁等结果」这一维度，没有提到追加指令和取消的具体 API。
--- 片段[1] oss__python__deepagents__async-subagents#002 ---
ervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task | | Cancellation | Not possible without stopping the supervisor | Cancel a task via cancel_async_task | | Statefulness | Stateless — no persistent state between invocations | Stateful — maintains state on its own thread across interactions | | Best for | Tasks where the agent should wait for results before continuing | Long-running, complex tasks managed interactively in a chat |
--- 片段[2] oss__javascript__deepagents__async-subagents#002 ---
ervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task | | Cancellation | Not possible without stopping the supervisor | Cancel a task via cancel_async_task | | Statefulness | Stateless — no persistent state between invocations | Stateful — maintains state on its own thread across interactions | | Best for | Tasks where the agent should wait for results before continuing | Long-running, complex tasks managed interactively in a chat |
--- 片段[3] oss__javascript__langchain__multi-agent__subagents#004 ---
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
--- 片段[4] oss__python__langchain__multi-agent__subagents#004 ---
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
--- 片段[5] oss__javascript__langgraph__interrupts#067 ---
```

const nodeA: GraphNode<typeof State> = async (state) => {

  // ✅ Good: using upsert operation which is idempotent

  // Running this multiple times will have the same result

  await db.upsertUser({

    userId: state.userId,

    status: "pending_approval"

  });



  const approved = interrupt("Approve this change?");



  return { approved };

}

```

### 34. v1-B-009 [single-hop] score=1.0
Q: LangGraph 文档把长期记忆分成 semantic、episodic、procedural 三类，各自存什么，对应到 agent 上又是什么例子？
GOLD: 按表，semantic 存的是 Facts（人类类比是学校里学到的东西），落到 agent 上就是 Facts about a user；episodic 存的是 Experiences（做过的事），对应 agent 的 Past agent actions；procedural 存的是 Instructions（本能或运动技能），在 agent 上就是 agent 的 system prompt。
ANSWER: 结论：文档把长期记忆分为三类——Semantic 存事实，Episodic 存经历，Procedural 存指令；对应到 agent 分别是「关于用户的事实」「过去的 agent 动作」「agent 的 system prompt」[3][4]。另外，LangGraph 的持久化层通过 stores 提供长期记忆 [5]。

| Memory Type | What is Stored | Agent Example |
| --- | --- | --- |
| Semantic | Facts | Facts about a user |
| Episodic | Experiences | Past agent actions |
| Procedural | Instructions | Agent system prompt |

[3][4]

最小示例（仅示意三类记忆的归类，非文档中的可运行代码）：

```python
long_term_memory = {
    "semantic": "Facts about a user",      # 事实
    "episodic": "Past agent actions",      # 经历
    "procedural": "Agent system prompt",   # 指令
}
```

补充说明：片段 [1][2] 也提到人类用记忆记住事实（semantic）、经历（episodic）和规则（procedural），AI agent 可以同样使用记忆 [1][2]。片段 [5] 只说明长期记忆通过 stores 实现，未展开三类记忆的具体 API 细节 [5]。
--- 片段[1] oss__python__concepts__memory#002 ---
- What is the type of memory? Humans use memories to remember facts ( semantic memory ), experiences ( episodic memory ), and rules ( procedural memory ). AI agents can use memory in the same ways. For example, AI agents can use memory to remember specific facts about a user to accomplish a task.
--- 片段[2] oss__javascript__concepts__memory#002 ---
- What is the type of memory? Humans use memories to remember facts ( semantic memory ), experiences ( episodic memory ), and rules ( procedural memory ). AI agents can use memory in the same ways. For example, AI agents can use memory to remember specific facts about a user to accomplish a task.
--- 片段[3] oss__python__concepts__memory#004 ---
| Memory Type | What is Stored | Human Example | Agent Example |

| --- | --- | --- | --- |

| Semantic | Facts | Things I learned in school | Facts about a user |

| Episodic | Experiences | Things I did | Past agent actions |

| Procedural | Instructions | Instincts or motor skills | Agent system prompt |
--- 片段[4] oss__javascript__concepts__memory#004 ---
| Memory Type | What is Stored | Human Example | Agent Example |

| --- | --- | --- | --- |

| Semantic | Facts | Things I learned in school | Facts about a user |

| Episodic | Experiences | Things I did | Past agent actions |

| Procedural | Instructions | Instincts or motor skills | Agent system prompt |
--- 片段[5] oss__python__langgraph__persistence#000 ---
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.

### 35. v1-B-010 [single-hop] score=1.0
Q: 从老的 langgraph.prebuilt 迁到 LangChain v1 的 create_agent，import 路径、提示词参数和原来的 pre-model/post-model hook 分别怎么变？
GOLD: 按迁移表的 TL;DR：import 路径从 langgraph.prebuilt 换成 langchain.agents；提示词参数改名为 system_prompt，动态提示词改用 middleware；pre-model hook 由 middleware 的 before_model 方法取代，post-model hook 由 after_model 取代。另外自定义 state 只支持 TypedDict（可通过 state_schema 或 middleware 定义），结构化输出移除了 prompted output，要改用 ToolStrategy 或 ProviderStrategy。
ANSWER: 结论：

- **Import 路径**：从 `langgraph.prebuilt` 迁移到 `langchain.agents` [1]。
- **提示词参数**：参数改名为 `system_prompt`；动态提示词改用 middleware 实现 [1]。
- **Pre-model hook**：由 middleware 的 `before_model` 方法替代 [1]。
- **Post-model hook**：由 middleware 的 `after_model` 方法替代 [1]。

最小可用示例（Python，基于片段中的旧写法对照）：

```python
# 旧写法（片段 [4] 展示的形式）
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt import AgentState

def custom_human_in_the_loop_hook(state: AgentState):
    """Custom logic for human in the loop approval."""
    ...

agent = create_react_agent(
    model="claude-sonnet-4-6",
    tools=[read_email, send_email],
    post_model_hook=custom_human_in_the_loop_hook
)
```

迁移要点（按片段 [1]）：
- 改为从 `langchain.agents` 导入 `create_agent`。
- 提示词参数使用 `system_prompt`。
- 原来的 `post_model_hook` 逻辑改写到 middleware 的 `after_model` 方法中；`pre_model_hook` 逻辑改写到 middleware 的 `before_model` 方法中。

补充说明（片段中提到的差异/额外变化）：
- 自定义 state 仅支持 `TypedDict`，可通过 `state_schema` 或 middleware 定义 [1]。
- 模型动态选择通过 middleware 实现，不支持 pre-bound models [1]。
- 工具错误处理移到 middleware 的 `wrap_tool_call` [1]。
- 结构化输出移除了 prompted output，改用 `ToolStrategy` / `ProviderStrategy` [1]。

如果你还需要 JavaScript 版本的对应变化（`createAgent`、`systemPrompt`、`beforeModel`/`afterModel`、`wrapToolCall`、`toolStrategy`/`providerStrategy`，以及流式节点名从 `"agent"` 改为 `"model"`），可参考片段 [2]。
--- 片段[1] oss__python__migrate__langchain-v1#004 ---
| Section | TL;DR - What’s changed | | --- | --- | | Import path | Package moved from langgraph.prebuilt to langchain.agents | | Prompts | Parameter renamed to system_prompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with before_model method | | Post-model hook | Replaced by middleware with after_model method | | Custom state | TypedDict only, can be defined via state_schema or middleware | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrap_tool_call | | Structured output | prompted output removed, use ToolStrategy / ProviderStrategy |
--- 片段[2] oss__javascript__migrate__langchain-v1#000 ---
| Section | What changed | | --- | --- | | Import path | Package moved from @langchain/langgraph/prebuilts to langchain | | Prompts | Parameter renamed to systemPrompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with beforeModel method | | Post-model hook | Replaced by middleware with afterModel method | | Custom state | Defined in middleware, zod objects only | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrapToolCall | | Structured output | prompted output removed, use toolStrategy / providerStrategy | | Streaming node name | Node name changed from "agent" to "model" |
--- 片段[3] oss__python__migrate__langgraph-supervisor#016 ---
- LangGraph v1 migration guide : Migrate from create_react_agent to create_agent
--- 片段[4] oss__python__migrate__langchain-v1#018 ---
```

from langgraph.prebuilt import create_react_agent

from langgraph.prebuilt import AgentState



def custom_human_in_the_loop_hook(state: AgentState):

    """Custom logic for human in the loop approval."""

    ...



agent = create_react_agent(

    model="claude-sonnet-4-6",

    tools=[read_email, send_email],

    post_model_hook=custom_human_in_the_loop_hook

)

```
--- 片段[5] oss__javascript__migrate__langchain-v1#014 ---
```

import { createReactAgent } from "@langchain/langgraph/prebuilts";



function customHumanInTheLoopHook(state) {

  // Custom approval logic

}



const agent = createReactAgent({

  model: "claude-sonnet-4-6",

  tools: [readEmail, sendEmail],

  postModelHook: customHumanInTheLoopHook,

});

```

### 36. v1-B-011 [single-hop] score=1.0
Q: LangChain v1 的 middleware 提供了哪些 hook？before_model、wrap_model_call、after_model 分别在什么时机跑？
GOLD: 文档列了六个 hook：before_agent 在调用 agent 之前（加载记忆、校验输入）、before_model 在每次 LLM 调用之前（更新提示词、裁剪消息）、wrap_model_call 包住每次 LLM 调用（拦截并修改请求与响应）、wrap_tool_call 包住每次工具调用、after_model 在每次 LLM 响应之后（校验输出、加护栏）、after_agent 在 agent 结束后（保存结果、清理）。
ANSWER: ## 结论

LangChain v1 的 middleware 提供 6 个 hook：`before_agent`、`before_model`、`wrap_model_call`、`wrap_tool_call`、`after_model`、`after_agent` [4]。

各 hook 的运行时机与典型用途 [4]：

| Hook | 运行时机 | 典型用途 |
| --- | --- | --- |
| `before_agent` | 调用 agent 之前 | 加载记忆、校验输入 |
| `before_model` | 每次 LLM 调用之前 | 更新 prompt、裁剪消息 |
| `wrap_model_call` | 包裹每次 LLM 调用 | 拦截并修改请求/响应 |
| `wrap_tool_call` | 包裹每次工具调用 | 拦截并修改工具执行 |
| `after_model` | 每次 LLM 响应之后 | 校验输出、施加 guardrail |
| `after_agent` | agent 完成后 | 保存结果、清理 |

补充：`before_model`、`after_model`、`wrap_tool_call` 这类生命周期 hook 也可用于更新对话历史 [1]。

## 最小可用示例

下面示例同时使用 `before_model` 和 `wrap_model_call`（`after_model` 用法与 `before_model` 类似，只是运行在模型响应之后）[5]：

```python
from langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langchain.agents import create_agent
from langgraph.runtime import Runtime
from typing import Any, Callable

@before_model
def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    print(f"About to call model with {len(state['messages'])} messages")
    return None

@wrap_model_call
def retry_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    for attempt in range(3):
        try:
            return handler(request)
        except Exception as e:
            if attempt == 2:
                raise
            print(f"Retry {attempt + 1}/3 after error: {e}")
```

`after_model` 的签名形式可参考片段 [3] 中的 `log_after_model(state, runtime)`，它在每次模型响应后运行并返回 `None` 或状态更新字典 [3]。

## 与用户说法的差异

用户提到的 `before_model`、`wrap_model_call`、`after_model` 三个名称与文档一致，无差异；但文档中 hook 总数为 6 个，除这三个外还包括 `before_agent`、`wrap_tool_call`、`after_agent` [4]。
--- 片段[1] oss__python__langchain__context-engineering#018 ---
- Use life-cycle hooks like before_model , after_model , or wrap_tool_call (for tool returns) to update the conversation history. See the middleware documentation for more details.
--- 片段[2] oss__python__langchain__runtime#007 ---
``` from dataclasses import dataclass from langchain.messages import AnyMessage from langchain.agents import create_agent, AgentState from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model from langgraph.runtime import Runtime @dataclass class Context: user_name: str # Dynamic prompts @dynamic_prompt def dynamic_system_prompt(request: ModelRequest) -> str: user_name = request.runtime.context.user_name system_prompt = f"You are a helpful assistant. Address the user as {user_name}." return system_prompt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
--- 片段[3] oss__python__langchain__runtime#008 ---
mpt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Processing request for user: {runtime.context.user_name}") return None # After model hook @after_model def log_after_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Completed request for user: {runtime.context.user_name}") return None agent = create_agent( model="gpt-5-nano", tools=[...], middleware=[dynamic_system_prompt, log_before_model, log_after_model], context_schema=Context ) agent.invoke( {"messages": [{"role": "user", "content": "What's my name?"}]}, context=Context(user_name="John Smith") ) ```
--- 片段[4] oss__python__releases__langchain-v1#002 ---
| Hook | When it runs | Use cases |

| --- | --- | --- |

| before_agent | Before calling the agent | Load memory, validate input |

| before_model | Before each LLM call | Update prompts, trim messages |

| wrap_model_call | Around each LLM call | Intercept and modify requests/responses |

| wrap_tool_call | Around each tool call | Intercept and modify tool execution |

| after_model | After each LLM response | Validate output, apply guardrails |

| after_agent | After agent completes | Save results, cleanup |
--- 片段[5] oss__python__langchain__middleware__custom#017 ---
``` from langchain.agents.middleware import ( before_model, wrap_model_call, AgentState, ModelRequest, ModelResponse, ) from langchain.agents import create_agent from langgraph.runtime import Runtime from typing import Any, Callable @before_model def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None: print(f"About to call model with {len(state['messages'])} messages") return None @wrap_model_call def retry_model( request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse], ) -> ModelResponse: for attempt in range(3): try: return handler(request) except Exception as e: if attempt == 2: raise print(f"Retry {attempt + 1}/3 after error: {e}")

### 37. v1-B-012 [single-hop] score=0.0
Q: deep agent 自带的文件工具里，读大文件、改文件内容、删目录分别该用哪个，有什么值得注意的行为？
GOLD: 读用 read_file：它带行号，支持 offset/limit 读取大文件，还能对非文本文件（图片、视频、音频、文档）返回多模态 content block。改内容用 edit_file，它做精确字符串替换，并带 global replace 模式。删用 delete，既可以删单个文件，也可以把目录连同它的内容递归删除。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：

1. **读大文件**：片段 [1] 只列出了沙箱后端会自动提供 `read_file`、`write_file`、`edit_file`、`delete`、`execute` 这些工具名 [1]，但没有说明 `read_file` 对大文件的处理行为（如分页、截断、流式读取等）。
2. **改文件内容**：片段只提到存在 `edit_file` 工具 [1]，以及片段 [5] 展示了可以通过 `FilesystemMiddleware(tools=[...])` 限制可用工具（示例中只保留 `read_file`、`ls`、`glob`、`grep`）[5]，但没有说明 `edit_file` 的具体语义（是整文件覆盖、局部替换还是 diff 应用）。
3. **删目录**：片段 [1] 只列出 `delete` 工具，未说明它是否支持删除目录、是否递归、是否有确认机制。片段 [4] 只展示了用 `interruptOn` 对 `delete_file` 工具要求人工审批的配置方式 [4]，但那是 JavaScript 侧 `createDeepAgent` 的示例，且工具名写作 `delete_file`，与片段 [1] 中的 `delete` 名称不一致——按规则以片段为准，这里存在命名差异，需要文档进一步澄清。
4. **值得注意的行为**：片段 [2][3] 只给出通用安全建议——限制 agent 只能访问特定目录、只读写安全文件、考虑用容器进一步沙箱化 [2][3]，并未针对上述三个具体工具描述行为细节。

建议查阅 deepagents 的 filesystem 工具参考页或 `FilesystemMiddleware` 的 API 文档，以获取各工具的参数与边界行为说明。
--- 片段[1] oss__python__deepagents__frontend__sandbox#000 ---
1. Deep agent with a sandbox backend: The agent gets filesystem tools ( read_file , write_file , edit_file , delete , execute ) automatically from the sandbox
--- 片段[2] oss__python__security-policy#003 ---
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
--- 片段[3] oss__javascript__security-policy#003 ---
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
--- 片段[4] oss__javascript__deepagents__human-in-the-loop#018 ---
```

const agent = createDeepAgent({

  tools: [deleteFile, readFile],

  interruptOn: {

    delete_file: true,

    read_file: false,

  },

  subagents: [{

    name: "file-manager",

    description: "Manages file operations",

    systemPrompt: "You are a file management assistant.",

    tools: [deleteFile, readFile],

    interruptOn: {

      // Override: require approval for reads in this subagent

      delete_file: true,

      read_file: true,  // Different from main agent!

    }

  }],

  checkpointer

});

```
--- 片段[5] oss__python__deepagents__overview#019 ---
```

from deepagents import create_deep_agent

from deepagents.middleware import FilesystemMiddleware



# Read-only agent: write_file, edit_file, delete, and execute are never shown

agent = create_deep_agent(

    model="claude-sonnet-4-6",

    middleware=[

        FilesystemMiddleware(backend=backend, tools=["read_file", "ls", "glob", "grep"]),

    ],

)

```

### 38. v1-B-013 [single-hop] score=1.0
Q: 图里的循环快撞上递归上限了，RemainingSteps 和 GraphRecursionError 这两种处理方式在检测时机和掌控流程上有什么不同？
GOLD: 按表，Proactive（用 RemainingSteps）是在到达上限之前就检测到，处理逻辑写在图里面、走条件路由，图会继续走向一条正常结束的路径；Reactive（GraphRecursionError）是在超过上限之后才检测，只能在图外用 try/except 兜住，图执行直接停止。
ANSWER: **结论：** 两者核心差异在于「检测时机」和「流程掌控位置」——RemainingSteps 是**主动式**，在到达上限**之前**检测，并在图**内部**通过条件路由把流程导向完成路径；GraphRecursionError 是**被动式**，在超过上限**之后**才检测，在图**外部**用 try/except 捕获，此时图执行已经停止 [1]。

具体对比（依据片段 [1] 的表格）：

| 方式 | 检测时机 | 处理位置 | 控制流结果 |
| --- | --- | --- | --- |
| 主动式（RemainingSteps） | 到达上限之前 | 图内部，通过条件路由 | 图继续走向完成路径 [1] |
| 被动式（GraphRecursionError） | 超过上限之后 | 图外部，try/except | 图执行停止 [1] |

**最小可用示例（Python，RemainingSteps 主动式）：**

```python
import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.managed.is_last_step import RemainingSteps

class State(TypedDict):
    messages: Annotated[list, operator.add]
    remaining_steps: RemainingSteps

def reasoning_node(state: State) -> dict:
    remaining = state["remaining_steps"]
    if remaining <= 2:
        return {"messages": ["Approaching limit, wrapping up..."]}
    return {"messages": ["thinking..."]}

def route_decision(state: State) -> Literal["reasoning_node", "fallback_node"]:
    if state["remaining_steps"] <= 2:
        return "fallback_node"
    return "reasoning_node"

def fallback_node(state: State) -> dict:
    return {"messages": ["Reached complexity limit, providing best effort answer"]}

builder = StateGraph(State)
builder.add_node("reasoning_node", reasoning_node)
builder.add_node("fallback_node", fallback_node)
builder.add_edge(START, "reasoning_node")
builder.add_conditional_edges("reasoning_node", route_decision)
builder.add_edge("fallback_node", END)
graph = builder.compile()
result = graph.invoke({"messages": []}, {"recursion_limit": 10})
```

[2][4]

**最小可用示例（JavaScript，GraphRecursionError 被动式）：**

```javascript
import { GraphRecursionError } from "@langchain/langgraph";

try {
  await graph.invoke({ aggregate: [] }, { recursionLimit: 4 });
} catch (error) {
  if (error instanceof GraphRecursionError) {
    console.log("Recursion Error");
  }
}
```

[3][5]

**关于参数命名的一致性提示：** 片段中 Python 侧使用 `recursion_limit`（下划线）[2]，JavaScript 侧使用 `recursionLimit`（驼峰）[3][5]，两者写法不同，使用时需按语言区分。
--- 片段[1] oss__python__langgraph__graph-api-control-flow#040 ---
| Approach | Detection | Handling | Control flow |

| --- | --- | --- | --- |

| Proactive ( RemainingSteps ) | Before the limit | Inside the graph via conditional routing | Graph continues to a completion path |

| Reactive ( GraphRecursionError ) | After the limit | Outside the graph in try / except | Graph execution stops |
--- 片段[2] oss__python__langgraph__graph-api-control-flow#039 ---
f state["remaining_steps"] <= 2: return "fallback_node" return "reasoning_node" def fallback_node(state: State) -> dict: return {"messages": ["Reached complexity limit, providing best effort answer"]} builder = StateGraph(State) builder.add_node("reasoning_node", reasoning_node) builder.add_node("fallback_node", fallback_node) builder.add_edge(START, "reasoning_node") builder.add_conditional_edges("reasoning_node", route_decision) builder.add_edge("fallback_node", END) graph = builder.compile() result = graph.invoke({"messages": []}, {"recursion_limit": 10}) ```
--- 片段[3] oss__javascript__langgraph__graph-api-control-flow#033 ---
```

import { GraphRecursionError } from "@langchain/langgraph";



try {

  await graph.invoke({ aggregate: [] }, { recursionLimit: 4 });

} catch (error) {

  if (error instanceof GraphRecursionError) {

    console.log("Recursion Error");

  }

}

```
--- 片段[4] oss__python__langgraph__graph-api-control-flow#038 ---
``` import operator from typing import Annotated, Literal from typing_extensions import TypedDict from langgraph.graph import END, START, StateGraph from langgraph.managed.is_last_step import RemainingSteps class State(TypedDict): messages: Annotated[list, operator.add] remaining_steps: RemainingSteps def reasoning_node(state: State) -> dict: remaining = state["remaining_steps"] if remaining <= 2: return {"messages": ["Approaching limit, wrapping up..."]} return {"messages": ["thinking..."]} def route_decision(state: State) -> Literal["reasoning_node", "fallback_node"]: if state["remaining_steps"] <= 2: return "fallback_node" return "reasoning_node" def fallback_node(state: State) -> dict:
--- 片段[5] oss__javascript__langgraph__graph-api-control-flow#028 ---
```

import { GraphRecursionError } from "@langchain/langgraph";



try {

  await graph.invoke(inputs, { recursionLimit: 3 });

} catch (error) {

  if (error instanceof GraphRecursionError) {

    console.log("Recursion Error");

  }

}

```

### 39. v1-B-014 [multi-hop] score=0.5
Q: 我想一边把图每一步的变化当事件流给前端，一边保证服务重启后同一会话还能接着聊，这两件事对 checkpointer 的要求是同一件事吗？
GOLD: 两处都落在 checkpointer 上：流模式对照表里 checkpoints 和 tasks 两种模式都标注 Requires a checkpointer，因为它们输出的是检查点事件和任务起止事件。而短期记忆（线程作用域记忆）正是把 State 通过 checkpointer 持久化到数据库，这样线程才能随时被恢复。也就是说，要让「状态变化可流式观察」和「会话可恢复」同时成立，就得给图配上 checkpointer。
ANSWER: **结论：不是同一件事。** 给出的文档片段里，checkpointer 的职责被描述为**持久化线程的图状态（checkpoints）**，用于短期、线程范围的记忆，包括对话连续性、human-in-the-loop、time travel 和容错 [1][2]；它还能在出错状态下保存精确的图状态以便之后恢复 [3][4]。片段中没有提到 checkpointer 负责把“每一步变化当事件流推给前端”这件事，因此不能把“事件流”和“重启后继续会话”视为对 checkpointer 的同一个要求。

具体来说：

- **重启后同一会话还能接着聊**：这属于 checkpointer 的持久化/记忆能力。片段说明 checkpointer 会把线程的图状态持久化为 checkpoint，用于对话连续性等短期线程记忆 [1][2]；并且会写入精确的图状态以便之后恢复，即使处于错误状态也可以 [3][4]；还允许交互之间保留“记忆”，后续消息发送到同一 thread 时会保留之前消息的记忆 [5]。
- **把图每一步的变化当事件流给前端**：给出的文档片段里没有找到能说明 checkpointer 负责事件流/流式输出的内容。缺的是：关于“事件流”“streaming events”“把每一步变化推送给前端”与 checkpointer 关系的说明。

因此，按现有片段只能回答：**checkpointer 与“重启后继续同一会话”直接相关；但“每一步变化作为事件流给前端”在给出的文档里没有依据，不能判定为对 checkpointer 的同一项要求。**

最小可用示例（仅体现片段支持的“同一 thread 保留记忆/可恢复”语义，不涉及事件流）：

```python
# 片段未给出具体 API 用法；这里仅示意“同一 thread 复用 checkpointer 以保留记忆”的概念
# 具体接口请以对应版本文档为准
config = {"configurable": {"thread_id": "conversation-1"}}
graph.invoke(inputs, config=config)
```

再次说明：给出的文档里没有找到能回答“事件流是否也由 checkpointer 承担”的内容，缺少 streaming/events 相关片段。
--- 片段[1] oss__python__langgraph__persistence#001 ---
- Checkpointers persist a thread’s graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
--- 片段[2] oss__javascript__langgraph__persistence#001 ---
- Checkpointers persist a thread’s graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
--- 片段[3] oss__javascript__langgraph__interrupts#000 ---
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
--- 片段[4] oss__python__langgraph__interrupts#000 ---
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
--- 片段[5] oss__python__langgraph__checkpointers#002 ---
- Memory : Checkpointers allow for “memory” between interactions. In the case of repeated human interactions (like conversations) any follow up messages can be sent to that thread, which will retain its memory of previous ones. See Add memory for information on how to add and manage conversation memory using checkpointers.

### 40. v1-B-015 [multi-hop] score=0.5
Q: 迁移文档说 pre-model hook 换成了 before_model，那这个 before_model 到底在什么时刻跑、能拿它干什么？顺便确认一下 v1 里 create_agent 的 import 路径。
GOLD: 迁移表写明 import 路径从 langgraph.prebuilt 变成 langchain.agents，pre-model hook 由 middleware 的 before_model 方法取代。middleware hook 表进一步说明 before_model 在每次 LLM 调用之前运行，典型用途是更新提示词和裁剪消息；作为对照，after_model 在每次 LLM 响应之后运行，用来校验输出、加护栏。
ANSWER: ## 结论

**1. `before_model` 的运行时机**：在每次调用 LLM 之前运行 [4][5]。注意是"每次模型调用前"，不是每次 agent 调用前（那是 `before_agent`）[4][5]。

**2. `before_model` 的用途**：可用于更新提示词、裁剪消息（trim messages）[4]。在示例中它被用来在模型调用前打印/记录当前用户信息 [1][2]。

**3. 关于"pre-model hook 换成 before_model"的说法**：迁移文档 [3] 的原文是 "Pre-model hook | Replaced by middleware with `beforeModel` method"——即被**中间件中的 `beforeModel` 方法**替代。而 Python 侧示例里用的是 `@before_model` 装饰器形式的中间件函数 [1][2]。两者是同一钩子的不同写法（方法 vs 装饰器），并非名称不一致，但需注意 [3] 是 JS 迁移文档、用的是驼峰 `beforeModel`。

**4. `create_agent` 的 import 路径**：给出的片段中，Python 侧示例从 `langchain.agents` 导入 `create_agent` [1]；JS 迁移文档 [3] 说明包从 `@langchain/langgraph/prebuilts` 移到了 `langchain`。**片段中没有直接给出 Python 的 import 语句原文**，只能从 [1] 的 `from langchain.agents import create_agent, AgentState` 推断。

## 最小可用示例（Python，来自片段 [1][2]）

```python
from dataclasses import dataclass
from langchain.agents import create_agent, AgentState
from langchain.agents.middleware import before_model
from langgraph.runtime import Runtime

@dataclass
class Context:
    user_name: str

@before_model
def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
    print(f"Processing request for user: {runtime.context.user_name}")
    return None

agent = create_agent(
    model="gpt-5-nano",
    tools=[...],
    middleware=[log_before_model],
    context_schema=Context,
)

agent.invoke(
    {"messages": [{"role": "user", "content": "What's my name?"}]},
    context=Context(user_name="John Smith"),
)
```

## 需要说明的缺口

- 片段 [1] 的 import 行被截断（`from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model` 出现在 [1] 中，但 `create_agent` 的完整 import 语句在片段里只以 `from langchain.agents import create_agent, AgentState` 形式出现），若需确认官方推荐的完整 import 路径，给出的文档里没有更明确的独立说明。
--- 片段[1] oss__python__langchain__runtime#007 ---
``` from dataclasses import dataclass from langchain.messages import AnyMessage from langchain.agents import create_agent, AgentState from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model from langgraph.runtime import Runtime @dataclass class Context: user_name: str # Dynamic prompts @dynamic_prompt def dynamic_system_prompt(request: ModelRequest) -> str: user_name = request.runtime.context.user_name system_prompt = f"You are a helpful assistant. Address the user as {user_name}." return system_prompt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
--- 片段[2] oss__python__langchain__runtime#008 ---
mpt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Processing request for user: {runtime.context.user_name}") return None # After model hook @after_model def log_after_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Completed request for user: {runtime.context.user_name}") return None agent = create_agent( model="gpt-5-nano", tools=[...], middleware=[dynamic_system_prompt, log_before_model, log_after_model], context_schema=Context ) agent.invoke( {"messages": [{"role": "user", "content": "What's my name?"}]}, context=Context(user_name="John Smith") ) ```
--- 片段[3] oss__javascript__migrate__langchain-v1#000 ---
| Section | What changed | | --- | --- | | Import path | Package moved from @langchain/langgraph/prebuilts to langchain | | Prompts | Parameter renamed to systemPrompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with beforeModel method | | Post-model hook | Replaced by middleware with afterModel method | | Custom state | Defined in middleware, zod objects only | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrapToolCall | | Structured output | prompted output removed, use toolStrategy / providerStrategy | | Streaming node name | Node name changed from "agent" to "model" |
--- 片段[4] oss__python__releases__langchain-v1#002 ---
| Hook | When it runs | Use cases |

| --- | --- | --- |

| before_agent | Before calling the agent | Load memory, validate input |

| before_model | Before each LLM call | Update prompts, trim messages |

| wrap_model_call | Around each LLM call | Intercept and modify requests/responses |

| wrap_tool_call | Around each tool call | Intercept and modify tool execution |

| after_model | After each LLM response | Validate output, apply guardrails |

| after_agent | After agent completes | Save results, cleanup |
--- 片段[5] oss__python__langchain__middleware__custom#000 ---
| Hook | When it runs |

| --- | --- |

| before_agent | Before agent starts (once per invocation) |

| before_model | Before each model call |

| after_model | After each model response |

| after_agent | After agent completes (once per invocation) |

### 41. v1-B-016 [multi-hop] score=0.5
Q: 我给主 agent 配了一堆技能，为什么派出去的子智能体一个都用不上？技能在运行期又是按什么规则被加载的？
GOLD: 按 SubAgent 的 skills 字段说明，技能不会从主 agent 继承，只有 general-purpose 子智能体才继承主 agent 的技能；子智能体一旦配了 skills，就会跑自己独立的 SkillsMiddleware 实例，技能状态完全隔离——子智能体加载的技能父 agent 看不到，反之亦然。而技能在运行期的加载规则是 progressive disclosure：只在 agent 判断相关时才读取，格式是放在具名目录里的 SKILL.md。
ANSWER: ## 结论

**子智能体用不上主 agent 的技能，是因为技能默认不继承。** 只有 `general-purpose` 子智能体会自动继承主 agent 通过 `create_deep_agent` 传入的 skills，其他子智能体需要自己通过 `skills` 参数指定技能路径 [1][5]。

**运行期加载规则：**
- 技能只从「创建 agent 时传入的路径」或「子智能体专属的 `skills` 参数」加载 [2][3]。
- 子智能体指定 `skills` 后，会运行自己独立的 `SkillsMiddleware` 实例，技能状态完全隔离——子智能体加载的技能对父级不可见，反之亦然 [1]。
- 子智能体的 `skills` 值会覆盖默认值，且**不从主 agent 继承**（`general-purpose` 除外）[1]。

## 最小可用示例

给子智能体单独配置技能路径（Python 文档中的字典式 `SubAgent`）：

```python
subagent = {
    "name": "researcher",
    # ... 其他配置 ...
    "skills": ["/skills/researcher/"],  # 子智能体专属技能目录
}
```

注意：`skills` 是 `list[str]`，指向技能源路径；示例中 `/skills/researcher/` 是一个容器，其子目录才是各个技能 [1]。

## 排查建议

如果技能没被激活，先确认该技能是否在 `skills` 数组里——技能只从创建时传入的路径或子智能体专属 `skills` 参数加载 [2][3]。

## 与提问的差异说明

你提到「给主 agent 配了一堆技能」，但片段中并未出现「主 agent 技能自动下发给所有子智能体」的机制；相反，片段明确说子智能体**默认不继承**，仅 `general-purpose` 子智能体自动继承 [1][5]。
--- 片段[1] oss__python__deepagents__subagents#007 ---
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
--- 片段[2] oss__javascript__deepagents__skills#122 ---
3. Confirm the skill is in the skills array. Skills load only from paths you pass at agent creation or from subagent-specific skills parameters.
--- 片段[3] oss__python__deepagents__skills#121 ---
3. Confirm the skill is in the skills array. Skills load only from paths you pass at agent creation or from subagent-specific skills parameters.
--- 片段[4] oss__javascript__langchain__multi-agent__skills-sql-assistant#037 ---
d, }), ], skillsLoaded: [skillName], }, }); } // Skill not found const available = SKILLS.map((s) => s.name).join(", "); return new Command({ update: { messages: [ new ToolMessage({ content: `Skill '${skillName}' not found. Available skills: ${available}`, tool_call_id: runtime.toolCallId, }), ], }, }); }, { name: "load_skill", description: `Load the full content of a skill into the agent's context.`, schema: z.object({ skillName: z.string().describe("The name of the skill to load"), }), } ); ```
--- 片段[5] oss__python__deepagents__skills#067 ---
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.

### 42. v1-B-017 [multi-hop] score=1.0
Q: 同一次运行里的中间结果、以及要跨会话复用的用户偏好，这两类数据在 LangGraph 里分别归到哪种 context、由谁承载？
GOLD: 按 context 类型表，动态运行时上下文（state）是在一次运行中演化的可变数据，生命周期是单次运行，载体是 LangGraph 的 state 对象；跨会话的动态上下文（store）是跨对话共享的持久数据，载体是 LangGraph store。长期记忆正是跨会话共享的那一类：它能在任何线程里被召回，作用域是任意自定义 namespace 而不只是一个 thread ID，LangGraph 用 stores 来保存和召回。
ANSWER: **结论**

- **同一次运行里的中间结果**属于 **Dynamic runtime context (state)**：它是单次运行内会变化（Mutable）的动态数据，生命周期为 Single run，由 **LangGraph state object** 承载 [1]。
- **要跨会话复用的用户偏好**属于 **Dynamic cross-conversation context (store)**：它是跨会话共享的持久数据，生命周期为 Cross-conversation，由 **LangGraph store** 承载 [1]。
- 另外，启动时传入的用户元数据、工具、数据库连接属于 **Static runtime context**，是静态的、单次运行有效，通过 `invoke` / `stream` 的 `context` 参数访问 [1]——注意它和上面两类不同，不要混淆。

**最小可用示例**（跨会话记忆的读取，来自文档片段）

```python
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore
from langgraph.runtime import Runtime

model = init_chat_model(model="claude-haiku-4-5-20251001")

@dataclass
class Context:
    user_id: str

def call_model(
    state: MessagesState,
    runtime: Runtime[Context],
):
    user_id = runtime.context.user_id
    namespace = ("memories", user_id)
    memories = runtime.store.search(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories])
```

片段中该示例展示了：用户标识通过 `runtime.context`（静态运行时上下文）取得，而跨会话记忆通过 `runtime.store` 按 `("memories", user_id)` 命名空间检索 [2]。异步版本使用 `await runtime.store.asearch(...)` [3][4]。

**说明**：片段只给出了 store 的读取用法，没有给出 state 对象的具体字段定义或写入 store 的代码，这部分无法从给出的文档中确认。
--- 片段[1] oss__python__concepts__context#003 ---
| Context type | Description | Mutability | Lifetime | Access method |

| --- | --- | --- | --- | --- |

| Static runtime context | User metadata, tools, db connections passed at startup | Static | Single run | context argument to invoke / stream |

| Dynamic runtime context (state) | Mutable data that evolves during a single run | Dynamic | Single run | LangGraph state object |

| Dynamic cross-conversation context (store) | Persistent data shared across conversations | Dynamic | Cross-conversation | LangGraph store |
--- 片段[2] oss__python__langgraph__add-memory#050 ---
``` from dataclasses import dataclass from langchain.chat_models import init_chat_model from langgraph.graph import StateGraph, MessagesState, START from langgraph.checkpoint.redis import RedisSaver from langgraph.store.redis import RedisStore from langgraph.runtime import Runtime model = init_chat_model(model="claude-haiku-4-5-20251001") @dataclass class Context: user_id: str def call_model( state: MessagesState, runtime: Runtime[Context], ): user_id = runtime.context.user_id namespace = ("memories", user_id) memories = runtime.store.search(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories])
--- 片段[3] oss__python__langgraph__add-memory#028 ---
``` from dataclasses import dataclass from langchain.chat_models import init_chat_model from langgraph.graph import StateGraph, MessagesState, START from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver from langgraph.store.postgres.aio import AsyncPostgresStore from langgraph.runtime import Runtime model = init_chat_model(model="claude-haiku-4-5-20251001") @dataclass class Context: user_id: str async def call_model( state: MessagesState, runtime: Runtime[Context], ): user_id = runtime.context.user_id namespace = ("memories", user_id) memories = await runtime.store.asearch(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories])
--- 片段[4] oss__python__langgraph__add-memory#046 ---
``` from dataclasses import dataclass from langchain.chat_models import init_chat_model from langgraph.graph import StateGraph, MessagesState, START from langgraph.checkpoint.redis.aio import AsyncRedisSaver from langgraph.store.redis.aio import AsyncRedisStore from langgraph.runtime import Runtime model = init_chat_model(model="claude-haiku-4-5-20251001") @dataclass class Context: user_id: str async def call_model( state: MessagesState, runtime: Runtime[Context], ): user_id = runtime.context.user_id namespace = ("memories", user_id) memories = await runtime.store.asearch(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories])
--- 片段[5] oss__python__langgraph__add-memory#032 ---
``` from dataclasses import dataclass from langchain.chat_models import init_chat_model from langgraph.graph import StateGraph, MessagesState, START from langgraph.checkpoint.postgres import PostgresSaver from langgraph.store.postgres import PostgresStore from langgraph.runtime import Runtime model = init_chat_model(model="claude-haiku-4-5-20251001") @dataclass class Context: user_id: str def call_model( state: MessagesState, runtime: Runtime[Context], ): user_id = runtime.context.user_id namespace = ("memories", user_id) memories = runtime.store.search(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories])

### 43. v1-B-018 [multi-hop] score=0.5
Q: 默认后端明明是 thread-scoped 的，为什么特性对照表里 Deep Agents 的短期记忆又写成 StateBackend？这两处矛盾吗？
GOLD: 不矛盾，说的是一回事：默认后端把文件存在 langgraph state 里，靠 checkpointer 在同一个线程内跨轮次保留，且不跨线程共享，这正是 thread-scoped 的含义；特性对照表里 Deep Agents 的 Short-term memory 一栏写的也正是 StateBackend，而 LangGraph 和 LangChain 两栏写的都是 Short-term memory。也就是说 Deep Agents 默认用 state 承载短期记忆，这也解释了为什么默认后端换线程就看不到文件。
ANSWER: 结论：不矛盾。给出的片段里，StateBackend 本身就是默认后端，而它被描述为 thread-scoped（线程范围内）的临时空间，这正好对应“短期记忆”的定位，所以“默认后端是 thread-scoped”和“短期记忆用 StateBackend”说的是同一件事，不是两套说法 [1][2]。

具体依据：
- StateBackend 是默认后端，文件在同一个 thread 内跨轮次保留（依赖 checkpointer），但不跨 thread 共享，且每一步都会 checkpoint，因此不建议写大文件 [1][2]。
- Deep Agents 会把内部数据（offloaded tool results、conversation history）写到默认后端；用 StateBackend 作默认可以让这些产物保持 ephemeral，避免落到磁盘或持久存储 [3][4]。
- 需要跨会话持久化时，片段给出的做法是用 CompositeBackend 把特定路径（如 `/memories/`）路由到 StoreBackend，而默认仍是 StateBackend [5]。

最小可用示例（来自片段 [5]，Python）：

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),
        },
    ),
    store=InMemoryStore(),  # Store passed to create_deep_agent, not backend
)
```

补充说明：片段中没有出现“特性对照表”这一具体表格，因此无法核对表格里的原文措辞；但就片段能覆盖的部分看，StateBackend = 默认 = thread-scoped = 短期，三者一致 [1][2][3][4]。
--- 片段[1] oss__javascript__deepagents__going-to-production#034 ---
- StateBackend (default): thread-scoped scratch space. Files persist across turns within a thread via your checkpointer but are not shared across threads. Checkpointed at every step, so avoid writing large files.
--- 片段[2] oss__python__deepagents__going-to-production#033 ---
- StateBackend (default): thread-scoped scratch space. Files persist across turns within a thread via your checkpointer but are not shared across threads. Checkpointed at every step, so avoid writing large files.
--- 片段[3] oss__javascript__deepagents__backends#072 ---
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
--- 片段[4] oss__python__deepagents__backends#087 ---
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
--- 片段[5] oss__python__deepagents__customization#142 ---
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="openrouter:z-ai/glm-5.2",

    backend=CompositeBackend(

        default=StateBackend(),

        routes={

            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),

        },

    ),

    store=InMemoryStore(),  # Store passed to create_deep_agent, not backend

)

```

### 44. v1-B-019 [multi-hop] score=0.0
Q: 我想让 deep agent 在解释器里直接跑 shell 命令装依赖，这条路能走通吗？如果不能，官方建议用什么、对应哪个工具？
GOLD: 走不通：安全能力表里「Shell commands, package installs, tests, OS-level execution」默认不可用，给出的解法不是给 interpreter 加开关，而是 Use a sandbox backend。文件工具表也印证了这一点——execute 用来在环境里跑 shell 命令，但它只在 sandbox backends 下可用。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：
- 没有任何片段提到 deep agent 在解释器中执行 shell 命令、安装依赖的能力或限制。
- 没有任何片段提到官方对此的替代建议或对应的工具名称。

现有片段 [1]–[5] 只展示了 `create_deep_agent` 的调用方式，涉及的参数仅有 `model`、`system_prompt`、`tools`、`memory`、`skills`，示例中的工具是 `search`、`fetch_url`、`run_query`，均未说明其用途或与 shell/依赖安装的关系。因此无法判断这条路是否可行，也无法给出官方建议的工具。
--- 片段[1] oss__python__deepagents__tools#002 ---
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    tools=[search, fetch_url, run_query],

)

```
--- 片段[2] oss__python__deepagents__customization#004 ---
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="openrouter:z-ai/glm-5.2",

    system_prompt="You are a helpful assistant.",

    tools=[search, fetch_url],

    memory=["./AGENTS.md"],

    skills=["./skills/"],

)

```
--- 片段[3] oss__python__deepagents__customization#005 ---
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="fireworks:accounts/fireworks/models/glm-5p2",

    system_prompt="You are a helpful assistant.",

    tools=[search, fetch_url],

    memory=["./AGENTS.md"],

    skills=["./skills/"],

)

```
--- 片段[4] oss__python__deepagents__customization#001 ---
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="google_genai:gemini-4-hydrogen",

    system_prompt="You are a helpful assistant.",

    tools=[search, fetch_url],

    memory=["./AGENTS.md"],

    skills=["./skills/"],

)

```
--- 片段[5] oss__python__deepagents__customization#002 ---
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    system_prompt="You are a helpful assistant.",

    tools=[search, fetch_url],

    memory=["./AGENTS.md"],

    skills=["./skills/"],

)

```

### 45. v1-B-020 [paraphrase] score=0.0
Q: agent 跑到一半崩了，我重跑一次它又把前面干过的活重做一遍，有没有办法让它接着上次断的地方继续跑？
GOLD: 用 graph.invoke(None, config)：它会加载最新的检查点并重试未完成的工作，而且不要再传 checkpoint_id。注意这跟「回答一个 interrupt()」不是一回事——后者要用 graph.invoke(Command(resume=answer), config)，被中断的节点会从节点开头重新执行。如果只是想回放历史，则用 get_state_history() 拿到的 snapshot.config 调 graph.invoke(None, snapshot.config)。
ANSWER: 结论：可以。文档里给出的机制是 **checkpointer 保存 agent 状态**，因此运行可以停下来、之后再恢复，甚至可以在另一个进程里恢复 [1][2]。恢复时用 `Command(resume=...)`（Python）或 `new Command({ resume })`（JavaScript）把决定交回给 middleware，agent 就会继续往下跑 [3][4]。

需要注意的差异/限制：
- 片段只说明了「用 checkpointer 保存状态 + 用 Command(resume=...) 恢复」这一条路径，**没有**给出「崩溃后自动从断点续跑」的通用 API 或参数；恢复动作需要你显式发起 [3][4]。
- 片段里没有说明 checkpointer 的具体配置方式（除了 [5] 示例中出现 `checkpointer=InMemorySaver()`），也没有说明崩溃场景下如何定位到同一个 thread。缺这些内容，无法从片段确认完整做法。

最小可用示例（依据 [5] 的写法，Python）：

```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model,
    tools=all_tools,
    checkpointer=InMemorySaver(),
)

thread_id = str(uuid7())
config = {"configurable": {"thread_id": thread_id}}

# 第一次运行（中途暂停/中断）
agent.invoke({"messages": [HumanMessage("...")]}, config)

# 之后用同一个 thread_id 恢复
agent.invoke(Command(resume=...), config)
```

其中 `Command(resume=...)` 的用法来自 [3]；JavaScript 对应写法是 `new Command({ resume })` [4]。`InMemorySaver()` 与 `thread_id` 的写法来自 [5] 的示例片段。

补充：给出的文档里没有找到「崩溃后如何自动检测并续跑」的内容，也没有 checkpointer 持久化后端（如数据库）的配置说明，这部分无法根据片段回答。
--- 片段[1] oss__python__concepts__human-in-the-loop#003 ---
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
--- 片段[2] oss__javascript__concepts__human-in-the-loop#003 ---
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
--- 片段[3] oss__python__concepts__human-in-the-loop#005 ---
5. You resume the agent with a Command(resume=...) . The middleware applies each decision, and the agent continues.
--- 片段[4] oss__javascript__concepts__human-in-the-loop#005 ---
5. You resume the agent with a new Command({ resume }) . The middleware applies each decision, and the agent continues.
--- 片段[5] oss__python__langchain__multi-agent__handoffs-customer-support#048 ---
reate_agent( model, tools=all_tools, state_schema=SupportState, middleware=[ apply_step_config, SummarizationMiddleware( model="gpt-5.4-mini", trigger=("tokens", 4000), keep=("messages", 10) ) ], checkpointer=InMemorySaver(), ) # ============================================================================ # Test the workflow # ============================================================================ if __name__ == "__main__": thread_id = str(uuid7()) config = {"configurable": {"thread_id": thread_id}} result = agent.invoke( {"messages": [HumanMessage("Hi, my phone screen is cracked")]}, config ) result = agent.invoke( {"messages": [HumanMessage("Yes, it's still under warranty")]}, config

### 46. v1-B-021 [paraphrase] score=1.0
Q: 我想让 agent 真去删文件之前先拦一下，最好我还能顺手把它填的参数改掉再放行，这套人工决策一共有哪几种？
GOLD: 决策类型有四种：approve 按 agent 提出的原始参数直接执行；edit 在执行前修改工具参数；reject 完全跳过这次工具调用，并把拒绝反馈返还给 agent；respond 则把人的消息直接当作合成的工具结果返回、跳过执行，用于「问用户」这类工具。
ANSWER: 结论：人工决策（interrupt decision）一共有 4 种：approve、edit、reject、respond [3][4]。其中你要的「删文件前拦一下、还能改参数再放行」对应的是 **edit**（执行前修改工具参数）[3][4]；如果只想拦下不执行，用 **reject**（跳过执行并把拒绝反馈给 agent，文档示例正是「拒绝文件删除并说明原因」）[3][4]。

四种决策说明（以片段为准）[3][4]：

| 决策类型 | 说明 | 示例用途 |
| --- | --- | --- |
| ✅ approve | 按 agent 提议的原始参数执行工具 | 按原稿发送邮件草稿 |
| ✏️ edit | 执行前修改工具参数 | 发送邮件前修改收件人 |
| ❌ reject | 完全跳过该工具调用，并向 agent 返回拒绝反馈 | 拒绝文件删除并解释原因 |
| 💬 respond | 把人的消息直接作为合成的工具结果返回，跳过执行，用于「ask user」类工具 | 直接回复 "ask_user" 提示 |

另外，片段 [5] 给出了按工具配置允许决策的写法（JavaScript），其中 `delete_file` 允许 `["approve", "edit", "reject"]`，正好覆盖你「先拦、可改参数、也可拒绝」的需求 [5]：

```javascript
const interruptOn = {
  // Sensitive operations: allow all options
  delete_file: { allowedDecisions: ["approve", "edit", "reject"] },

  // Moderate risk: approval or rejection only
  write_file: { allowedDecisions: ["approve", "reject"] },

  // Must approve (no rejection allowed)
  critical_operation: { allowedDecisions: ["approve"] },
};
```

补充说明（与你的说法可能存在的差异）：你提到「改掉参数再放行」，片段里的对应术语是 **edit**，描述为「Modify the tool arguments before execution」[3][4]；片段中没有出现其他决策类型名称，也没有给出 Python 版的 `interruptOn` 配置示例，只有 JavaScript 版 [5]。此外，片段 [1][2] 建议对文件系统访问做目录限制与容器沙箱，可作为删除类操作之外的额外缓解措施 [1][2]。
--- 片段[1] oss__python__security-policy#003 ---
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
--- 片段[2] oss__javascript__security-policy#003 ---
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
--- 片段[3] oss__python__langchain__human-in-the-loop#000 ---
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
--- 片段[4] oss__javascript__langchain__human-in-the-loop#000 ---
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
--- 片段[5] oss__javascript__deepagents__human-in-the-loop#007 ---
```

const interruptOn = {

  // Sensitive operations: allow all options

  delete_file: { allowedDecisions: ["approve", "edit", "reject"] },



  // Moderate risk: approval or rejection only

  write_file: { allowedDecisions: ["approve", "reject"] },



  // Must approve (no rejection allowed)

  critical_operation: { allowedDecisions: ["approve"] },

};

```

### 47. v1-B-022 [paraphrase] score=0.0
Q: 我按文档写了个 skill 放进去，agent 就是不激活它，怎么才能让它被用上？
GOLD: 关键在于 description：agent 在发现阶段只根据 description 字段来挑技能，所以要把技能做什么、什么时候该用、以及 agent 能匹配上的关键词都写进去。文档给的好例子是 Search the arXiv preprint repository for research papers 这种具体描述，而 Helps with research 这类太泛的写法就选不中。
ANSWER: 结论：按给出的片段，skill 的工具是「门控」的——agent 必须先读取该 skill 的 `SKILL.md`，其 skill 工具才会出现；在读取之前，即使模型猜对了工具名和参数，调用也会作为未知工具失败 [5]。另外，如果摘要（summarization）把这次读取丢掉，skill 工具会再次消失 [1][2]。若想让工具直接可用，可以「pin」该 skill，pin 之后其 skill 工具对 agent 可用，效果等同于 agent 读取了它的 `SKILL.md` [3][4]。

最小可用做法（示意，片段未给出具体 API 名称，故不写具体调用代码）：

1. 确保 agent 实际读取了该 skill 的 `SKILL.md`，读取后工具才会出现 [5]。
2. 若对话被摘要压缩，检查是否把这次读取丢掉了，丢了工具就会消失 [1][2]。
3. 或者直接 pin 这个 skill，使其 skill 工具无需读取即可用 [3][4]。

需要说明的差异/缺口：片段只描述了机制，没有给出 pin 的具体函数名、参数或配置写法，因此无法提供可运行的代码示例；这部分内容在给出的文档里没有找到。
--- 片段[1] oss__javascript__deepagents__skills#131 ---
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
--- 片段[2] oss__python__deepagents__skills#131 ---
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
--- 片段[3] oss__python__deepagents__skills#065 ---
- When you pin a skill, its skill tools become available to the agent, the same as when the agent reads its SKILL.md .
--- 片段[4] oss__javascript__deepagents__skills#052 ---
- When you pin a skill, its skill tools become available to the agent, the same as when the agent reads its SKILL.md .
--- 片段[5] oss__javascript__deepagents__skills#022 ---
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.

### 48. v1-B-023 [paraphrase] score=0.5
Q: 想让 agent 回到之前某一步的状态、从那儿岔开再试另一条路，checkpointer 支持这种事吗？
GOLD: 支持，这就是文档说的 time travel：checkpointer 允许重放之前的图执行，用来复查或调试特定步骤；更进一步，它还能在任意检查点上 fork 图状态，去探索不同的轨迹。
ANSWER: 结论：支持。文档把这种用法称为 “Trying another path”：可以从更早保存的状态继续，而且不会删除原来的 checkpoints [4][5]。另外，checkpointer 会保存 agent 状态，使运行可以停止并在之后恢复，甚至可以在另一个进程中恢复 [1][2]。

最小示例（文档未给出具体 API 代码，这里只示意流程，不虚构接口）：

```text
1. 运行 agent，checkpointer 持续保存状态 [1][2]
2. 选择之前某一步的已保存状态
3. 从该状态继续执行，尝试另一条路径 [4][5]
4. 原有 checkpoints 保留，不被删除 [4][5]
```

补充说明：片段 [3] 提到在多 agent 场景中，只为顶层 agent 添加 checkpointer，这是暂停和恢复执行所必需的。若你的场景涉及子 agent，需注意 checkpointer 的挂载位置。
--- 片段[1] oss__javascript__concepts__human-in-the-loop#003 ---
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
--- 片段[2] oss__python__concepts__human-in-the-loop#003 ---
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
--- 片段[3] oss__python__langchain__multi-agent__subagents-personal-assistant#049 ---
- We add a checkpointer only to the top-level agent . This is required to pause and resume execution.
--- 片段[4] oss__javascript__langchain__frontend__time-travel#019 ---
- Trying another path : continue from an earlier saved state without deleting the original checkpoints
--- 片段[5] oss__python__langchain__frontend__time-travel#019 ---
- Trying another path : continue from an earlier saved state without deleting the original checkpoints

### 49. v1-B-024 [no-answer] score=None
Q: 我们打算把模型后端换成 vLLM，它启动参数里的 --gpu-memory-utilization 默认值是多少？调到多少容易 OOM？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

缺什么：
- 片段 [4] 只在聊天模型集成表里列出了 `vLLM` 这一行，但该行的 Stream / Tool calling / Structured output / Multimodal / Downloads 列均为空，没有任何关于 vLLM 启动参数的信息。
- 其余片段分别讲的是 JavaScript/Python 版 deepagents 解释器配置（[1][2]）、HuggingFace 模型初始化示例（[3]）、NVIDIA 重排序组件（[5]），都不涉及 vLLM 的 `--gpu-memory-utilization` 默认值或 OOM 阈值。

因此无法根据给定片段给出该参数的默认值，也无法判断调到多少容易 OOM。
--- 片段[1] oss__javascript__deepagents__interpreters#026 ---
| Option | Default | Purpose | | --- | --- | --- | | memoryLimitBytes | 64 * 1024 * 1024 (64 MB) | Cap QuickJS heap memory per session. | | maxStackSizeBytes | 320 * 1024 | Cap QuickJS stack size per session. | | executionTimeoutMs | 5000 | Timeout limit in milliseconds for each eval call. Negative values disable the timeout. | | toolName | "eval" | Name of the interpreter tool exposed to the model. | | captureConsole | true | Capture console.log , console.warn , and console.error in the tool response. Set to false to discard console output. | | maxResultChars | 4000 | Truncate result, error, and console output returned to the model to a maximum character count. |
--- 片段[2] oss__python__deepagents__interpreters#058 ---
| Kwarg | Default | Purpose | | --- | --- | --- | | memory_limit | 64 * 1024 * 1024 (64 MB) | Cap QuickJS heap memory per thread. | | timeout | 5.0 | Timeout limit in seconds for each eval call. | | tool_name | "eval" | Name of the interpreter tool exposed to the model. | | capture_console | True | Capture console.log , console.warn , and console.error in the tool response. Set to False to discard console output. | | max_result_chars | 4000 | Truncate result, error, and stdout text returned to the model to a maximum character count. | | ptc | None | Allowlist of tool names or BaseTool instances exposed as tools.* inside the interpreter. Omit to disable. See Enable PTC . |
--- 片段[3] oss__python__langchain__models#016 ---
```

import os

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint



os.environ["HUGGINGFACEHUB_API_TOKEN"] = "hf_..."



llm = HuggingFaceEndpoint(

    repo_id="microsoft/Phi-3-mini-4k-instruct",

    temperature=0.7,

    max_length=1024,

)

model = ChatHuggingFace(llm=llm)

```
--- 片段[4] oss__python__integrations__chat#003 ---
| Model | Stream | Tool calling | Structured output | Multimodal | Downloads | | --- | --- | --- | --- | --- | --- | | AzureChatOpenAI | ✅ | ✅ | ✅ | ✅ |  | | ChatOpenAI | ✅ | ✅ | ✅ | ✅ |  | | vLLM |  |  |  |  |  | | ChatAnthropicVertex |  |  |  |  |  | | ChatVertexAI (deprecated) | ✅ | ✅ | ✅ | ✅ |  | | ChatAnthropic | ✅ | ✅ | ✅ | ✅ |  | | ChatAnthropicTools |  |  |  |  |  | | ChatGoogleGenerativeAI | ✅ | ✅ | ✅ | ✅ |  | | ChatBedrock | ✅ | ✅ | ✅ | ✅ |  | | ChatOllama | ✅ | ✅ | ✅ | ✅ |  | | ChatGroq | ✅ | ✅ | ✅ | ✅ |  | | ChatHuggingFace | ❌ | ✅ | ✅ | ✅ |  | | ChatLiteLLM | ✅ | ✅ | ✅ | ✅ |  | | ChatMistralAI | ✅ | ✅ | ✅ | ❌ |  | | ChatXAI | ✅ | ✅ | ✅ | ❌ |  |
--- 片段[5] oss__python__integrations__providers__nvidia#005 ---
```

from langchain_core.documents import Document

from langchain_nvidia_ai_endpoints import NVIDIARerank



ranker = NVIDIARerank(model="nvidia/llama-3.2-nv-rerankqa-1b-v1")

docs = ranker.compress_documents(

    query="What is GPU memory bandwidth?",

    documents=[Document(page_content=p) for p in passages],

)

```

### 50. v1-B-025 [no-answer] score=None
Q: LlamaIndex 里 QueryEngine 的 similarity_top_k 默认取几？和 Haystack 的 Pipeline 比，哪个召回效果更好？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

缺少的内容：
- 关于 LlamaIndex `QueryEngine` 及其 `similarity_top_k` 默认值的任何说明（片段 [3][4] 只提到向量库可按 similarity 和 MMR 查询，未涉及 LlamaIndex 或该参数默认值）。
- 关于 Haystack `Pipeline` 的任何说明，以及两者召回效果的对比（全部片段均未提及 Haystack）。

另外提示一处名称差异：片段 [1][2] 中出现的是 LangGraph 前端的 `useStream`（来自 `@langchain/react`），与问题中的 LlamaIndex `QueryEngine`、Haystack `Pipeline` 并非同一套 API，不能据此推断答案。
--- 片段[1] oss__javascript__langgraph__frontend__overview#001 ---
```

import { useStream } from "@langchain/react";



function Pipeline() {

  const stream = useStream<typeof graph>({

    apiUrl: "http://localhost:2024",

    assistantId: "pipeline",

  });



  const classification = stream.values?.classification;

  const research = stream.values?.research;

  const analysis = stream.values?.analysis;

  const graphNodes = [...stream.subgraphs.values()];

}

```
--- 片段[2] oss__python__langgraph__frontend__overview#001 ---
```

import { useStream } from "@langchain/react";



function Pipeline() {

  const stream = useStream<typeof graph>({

    apiUrl: "http://localhost:2024",

    assistantId: "pipeline",

  });



  const classification = stream.values?.classification;

  const research = stream.values?.research;

  const analysis = stream.values?.analysis;

  const graphNodes = [...stream.subgraphs.values()];

}

```
--- 片段[3] oss__javascript__langchain__knowledge-base#017 ---
- By similarity and maximum marginal relevance (to balance similarity with diversity)
--- 片段[4] oss__python__langchain__knowledge-base#031 ---
- By similarity and maximum marginal relevance (to balance similarity with diversity)
--- 片段[5] oss__javascript__integrations__chat__google#015 ---
```

const llmWithLogprobs = new ChatGoogle({

  model: "gemini-4-hydrogen",

  logprobs: 2, // Number of top candidates to return

});



const resWithLogprobs = await llmWithLogprobs.invoke("Hello");



console.log(resWithLogprobs.response_metadata.logprobs_result);

```
