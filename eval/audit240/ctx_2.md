# 审计材料 2/8（30 条，明细文件第 31–60 行）

## v1-B-006（single-hop）

**问题**：默认情况下 interpreter 里能读文件、发网络请求、执行 shell 吗？如果确实需要放开这些能力，正确做法是什么？

**gold**：按安全能力表，JavaScript 执行、top-level await、console.log/warn/error 捕获默认可用；而 agent 工具、filesystem 访问、network 访问、wall-clock 或 datetime 访问默认都不可用。放开的方式各不相同：加 PTC allowlist 暴露 agent 工具，设 fs 或通过 PTC allowlist 加内置文件工具，通过 PTC 暴露某个具体网络工具，需要时间就显式提供一个时间工具。至于 shell 命令、装包、跑测试这类 OS 级执行，正确的方向是用 sandbox backend，而不是在 interpreter 里开开关。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：默认都不能。** 文件系统访问、网络访问、Shell 命令/包安装/测试/OS 级执行，在 interpreter 中默认均不可用 [1][2]。

具体来说：

- **文件系统访问**：默认 No。要放开，需设置 `fs`，或通过 PTC allowlist 添加内置文件系统工具 [1][2]。Python 侧配置项 `fs` 默认 `None`，设为 `True` 时使用 `create_deep_agent` 的后端 [5]。
- **网络访问**：默认 No。需通过 PTC 暴露一个特定的网络工具 [1][2]。
- **Shell 命令、包安装、测试、OS 级执行**：默认 No。需使用 sandbox 后端 [1][2]。

另外，按“选择模式”的指引：需要 Shell 命令、包安装、测试或完整 OS 文件系统访问时，应使用 **Sandboxes** [3][4]。

**最小可用示例（Python，放开文件系统）：**

```python
from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    middleware=[CodeInterpreterMiddleware(fs=True)],
)
```

说明：`fs=True` 表示让 interpreter 代码获得基于 `create_deep_agent` 后端的 Node 风格 `fs` 全局对象 [5]。网络与 Shell 则分别走“通过 PTC 暴露特定网络工具”和“使用 sandbox 后端”的路径 [1][2]。

**一处命名差异提醒**：控制台捕获的关闭参数在 Python 文档中是 `capture_console=False` [1][9]，在 JavaScript 文档中是 `captureConsole: false` [2]；同理 PTC 上限参数 Python 为 `max_ptc_calls` [5]，JavaScript 为 `maxPtcCalls` [8]。使用时请按对应语言选择参数名。

**top5 片段**：

片段[1] `oss__python__deepagents__interpreters#057` ｜ Interpreters ｜ Security

```text
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
```

片段[2] `oss__javascript__deepagents__interpreters#025` ｜ Interpreters ｜ Security

```text
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
```

片段[3] `oss__python__deepagents__interpreters#001` ｜ Interpreters ｜ Choose a pattern

```text
| Need | Use |

| --- | --- |

| One or two simple external calls | Normal tool calling |

| Pure in-memory JavaScript: loops, branches, retries, or data transforms (no external tools) | Interpreter |

| Many external tool calls orchestrated from code (requires PTC ) | Interpreter with programmatic tool calling (PTC) |

| Many independent units of work, multiple perspectives, or recursive analysis over large inputs | Interpreter with dynamic subagents |

| Shell commands, package installs, tests, or full OS filesystem access | Sandboxes |
```

片段[4] `oss__javascript__deepagents__interpreters#001` ｜ Interpreters ｜ Choose a pattern

```text
| Need | Use |

| --- | --- |

| One or two simple external calls | Normal tool calling |

| Pure in-memory JavaScript: loops, branches, retries, or data transforms (no external tools) | Interpreter |

| Many external tool calls orchestrated from code (requires PTC ) | Interpreter with programmatic tool calling (PTC) |

| Many independent units of work, multiple perspectives, or recursive analysis over large inputs | Interpreter with dynamic subagents |

| Shell commands, package installs, tests, or full OS filesystem access | Sandboxes |
```

片段[5] `oss__python__deepagents__interpreters#059` ｜ Interpreters ｜ Configuration

```text
wlist of tool names or BaseTool instances exposed as tools.* inside the interpreter. Omit to disable. See Enable PTC . | | max_ptc_calls | 256 | Maximum tools.* calls allowed per eval . Set to None only in trusted environments. See Programmatic tool calling (PTC) and Security . | | subagents | True | Expose the built-in task() global when the agent has subagents. Set to False to require dispatch through the normal task tool. See Dynamic subagents . | | fs | None | Give interpreter code a Node-style fs global over a backend. True uses the backend from create_deep_agent . See Files ( fs ) . | | mode | "thread" | Control interpreter persistence:
```

---

## v1-B-007（single-hop）

**问题**：deep agent 默认把文件写在哪？为什么同一个 agent 换个线程就读不到之前写的文件了？

**gold**：默认后端是 thread-scoped 的：文件存在 langgraph state 里，靠你的 checkpointer 在同一个线程内跨轮次保留，但不跨线程共享，所以换一个线程就看不到之前写的文件。想真正落到本地磁盘可以换成 FilesystemBackend，注意任何提供的 root_dir 都必须是绝对路径。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. Deep Agent 的默认文件系统后端是 **thread-scoped（线程作用域）** 的，文件存储在 **LangGraph state** 中，通过 checkpointer 在同一线程内的多轮对话之间持久化，但**不跨线程共享** [1][2]。
2. 因此换一个线程就读不到之前写的文件——因为默认后端的数据是按线程隔离的，新线程没有旧线程的 state [1][2]。
3. 如果需要跨线程持久化（例如长期记忆），应改用 **Durable store（LangGraph store）** 后端，它能在多个线程之间持久保存 [9]。

**最小可用示例：**

默认（线程内持久，不跨线程）：

```python
agent = create_deep_agent(model="google_genai:gemini-4-hydrogen")
```

跨线程持久（Durable store）：

```python
agent = create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    backend=StoreBackend(namespace=lambda rt: (rt.server_info.user.identity,)),
    store=InMemoryStore(),
)
```

**补充说明：**

- 文档还提到，Deep Agents 会把内部数据（如 offloaded tool results、conversation history）写入默认后端；若希望这些产物是临时的、不落盘，可用 `StateBackend` 作为默认后端 [3][4]。
- 若想让 agent 访问本地机器文件系统，可用 `FilesystemBackend(root_dir=...)`，且 `root_dir` 必须是绝对路径 [1][2]；文档建议通常用 `CompositeBackend` 把内部 agent 数据与项目文件分开 [9]。

**与提问措辞的差异提示：** 你问的是「默认把文件写在哪」，文档原文表述为默认后端存储在 langgraph state、按 thread 作用域持久化 [1][2]，并未给出一个具体的磁盘路径；具体落盘位置取决于你配置的 checkpointer。

**top5 片段**：

片段[1] `oss__python__deepagents__backends#001` ｜ Backends ｜ Quickstart

```text
| Built-in backend | Description | | --- | --- | | Default | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen") Thread-scoped. The default filesystem backend for an agent is stored in langgraph state. Files persist across turns within a thread (via your checkpointer) and are not shared across threads. | | Local filesystem persistence | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")) This gives the deep agent access to your local machine’s filesystem. You can specify the root directory that the agent has access to. Note that any provided root_dir must be an absolute path.
```

片段[2] `oss__javascript__deepagents__backends#001` ｜ Backends ｜ Quickstart

```text
| Built-in backend | Description | | --- | --- | | Default | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen") Thread-scoped. The default filesystem backend for an agent is stored in langgraph state. Files persist across turns within a thread (via your checkpointer) and are not shared across threads. | | Local filesystem persistence | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=FilesystemBackend(root_dir="/Users/nh/Desktop/")) This gives the deep agent access to your local machine’s filesystem. You can specify the root directory that the agent has access to. Note that any provided root_dir must be an absolute path.
```

片段[3] `oss__javascript__deepagents__backends#072` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[4] `oss__python__deepagents__backends#087` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[5] `oss__python__deepagents__overview#019` ｜ Deep Agents overview ｜ Execution environment > Virtual filesystem access

```text
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
```

---

## v1-B-008（single-hop）

**问题**：同步子智能体和异步子智能体在「谁来等结果」「能不能中途追加指令」「能不能取消」上有什么不同？

**gold**：同步模式由 supervisor 阻塞等待子智能体完成，异步模式则立刻返回一个 task ID、supervisor 继续往下走。中途追加指令同步做不到，异步可以用 update_async_task 补充后续指令；取消方面同步只能把 supervisor 一起停掉，异步可以用 cancel_async_task 取消任务。状态上前者是无状态的、调用之间不留状态，后者有状态，在服务器自己的线程上跨交互保持状态。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. **谁来等结果**：同步子智能体由主智能体（supervisor）阻塞等待其完成，结果作为工具结果返回；异步子智能体立即返回 task ID，主智能体继续运行，结果由子智能体通知主智能体，或由主智能体调用 `check_async_task` 获取 [7][9]。同步模式下主智能体等待子智能体完成，适合主智能体需要结果才能继续的场景；异步模式下子智能体在后台运行、主智能体继续，适合独立任务 [3][4]。

2. **能不能中途追加指令**：同步子智能体不支持中途更新（Not possible）；异步子智能体可以通过 `update_async_task` 发送后续指令 [1][2][7][9]。

3. **能不能取消**：同步子智能体无法在不停止主智能体的情况下取消（Not possible without stopping the supervisor）；异步子智能体可以通过 `cancel_async_task` 取消任务 [1][2]。

**补充差异（片段中同时给出）**：同步子智能体是无状态的（调用之间无持久状态），异步子智能体是有状态的（在自己的线程上跨交互维护状态）[1][2]。

**最小可用示例（异步子智能体配置，JavaScript）：**

```javascript
import { createDeepAgent, type AsyncSubAgent } from "deepagents";

const asyncSubagents: AsyncSubAgent[] = [
  {
    name: "researcher",
    description: "Research agent for information gathering and synthesis",
    graphId: "researcher",
    // No url → ASGI transport (co-deployed in the same deployment)
  },
];

const agent = createDeepAgent({
  model: "google:gemini-4-hydrogen",
  subagents: [...asyncSubagents],
});
```
[6]

（Python 对应写法见 [8]。）

**top5 片段**：

片段[1] `oss__javascript__deepagents__async-subagents#002` ｜ Async subagents ｜ Compare sync and async subagents

```text
ervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task | | Cancellation | Not possible without stopping the supervisor | Cancel a task via cancel_async_task | | Statefulness | Stateless — no persistent state between invocations | Stateful — maintains state on its own thread across interactions | | Best for | Tasks where the agent should wait for results before continuing | Long-running, complex tasks managed interactively in a chat |
```

片段[2] `oss__python__deepagents__async-subagents#002` ｜ Async subagents ｜ Compare sync and async subagents

```text
ervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task | | Cancellation | Not possible without stopping the supervisor | Cancel a task via cancel_async_task | | Statefulness | Stateless — no persistent state between invocations | Stateful — maintains state on its own thread across interactions | | Best for | Tasks where the agent should wait for results before continuing | Long-running, complex tasks managed interactively in a chat |
```

片段[3] `oss__python__langchain__multi-agent__subagents#004` ｜ Subagents ｜ Sync vs. async

```text
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
```

片段[4] `oss__javascript__langchain__multi-agent__subagents#004` ｜ Subagents ｜ Sync vs. async

```text
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
```

片段[5] `oss__javascript__langgraph__interrupts#067` ｜ Interrupts ｜ Rules of interrupts > Side effects called before interrupt must be idempotent

```text
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
```

---

## v1-B-009（single-hop）

**问题**：LangGraph 文档把长期记忆分成 semantic、episodic、procedural 三类，各自存什么，对应到 agent 上又是什么例子？

**gold**：按表，semantic 存的是 Facts（人类类比是学校里学到的东西），落到 agent 上就是 Facts about a user；episodic 存的是 Experiences（做过的事），对应 agent 的 Past agent actions；procedural 存的是 Instructions（本能或运动技能），在 agent 上就是 agent 的 system prompt。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 文档把长期记忆分为三类，存储内容和 agent 示例对应如下 [3][4]：

| 记忆类型 | 存储内容 | Agent 示例 |
| --- | --- | --- |
| Semantic（语义记忆） | 事实（Facts） | 关于用户的事实（Facts about a user）[3][4] |
| Episodic（情景记忆） | 经历/经验（Experiences） | 过去的 agent 动作（Past agent actions）[3][4] |
| Procedural（程序记忆） | 指令（Instructions） | Agent 的系统提示词（Agent system prompt）[3][4] |

文档还给出人类类比：语义记忆对应“在学校学到的东西”，情景记忆对应“我做过的事”，程序记忆对应“本能或运动技能” [3][4]。另外，文档说明人类用记忆来记住事实、经历和规则，AI agent 也可以用同样的方式使用记忆，例如记住关于用户的特定事实来完成任务 [1][2]。

**最小示例（仅示意三类记忆的归类，非文档中的完整可运行代码）：**

```python
memories = {
    "semantic": "用户偏好中文回答",          # 事实 -> Facts about a user
    "episodic": "上一轮调用了搜索工具",       # 经历 -> Past agent actions
    "procedural": "你是一个问答助手……",      # 指令 -> Agent system prompt
}
```

补充：文档提到长期记忆存储跨会话的用户级或应用级数据，并在会话线程之间共享，可按自定义 namespace 作用域保存和召回，LangGraph 通过 stores 实现 [10][12]；持久化层则用 checkpointer 提供短期记忆、用 store 提供长期记忆 [5][6]。

如果你问的是“三类记忆分别怎么写入/更新”，给出的片段只提到记忆可在 agent 应用逻辑中（hot path）更新，或作为后台任务异步生成 [9][11]，没有给出三类各自的完整写入 API 细节。

**top5 片段**：

片段[1] `oss__python__concepts__memory#002` ｜ Memory overview ｜ Long-term memory

```text
- What is the type of memory? Humans use memories to remember facts ( semantic memory ), experiences ( episodic memory ), and rules ( procedural memory ). AI agents can use memory in the same ways. For example, AI agents can use memory to remember specific facts about a user to accomplish a task.
```

片段[2] `oss__javascript__concepts__memory#002` ｜ Memory overview ｜ Long-term memory

```text
- What is the type of memory? Humans use memories to remember facts ( semantic memory ), experiences ( episodic memory ), and rules ( procedural memory ). AI agents can use memory in the same ways. For example, AI agents can use memory to remember specific facts about a user to accomplish a task.
```

片段[3] `oss__python__concepts__memory#004` ｜ Memory overview ｜ Long-term memory

```text
| Memory Type | What is Stored | Human Example | Agent Example |

| --- | --- | --- | --- |

| Semantic | Facts | Things I learned in school | Facts about a user |

| Episodic | Experiences | Things I did | Past agent actions |

| Procedural | Instructions | Instincts or motor skills | Agent system prompt |
```

片段[4] `oss__javascript__concepts__memory#004` ｜ Memory overview ｜ Long-term memory

```text
| Memory Type | What is Stored | Human Example | Agent Example |

| --- | --- | --- | --- |

| Semantic | Facts | Things I learned in school | Facts about a user |

| Episodic | Experiences | Things I did | Past agent actions |

| Procedural | Instructions | Instincts or motor skills | Agent system prompt |
```

片段[5] `oss__python__langgraph__persistence#000` ｜ Persistence ｜ ROOT

```text
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
```

---

## v1-B-010（single-hop）

**问题**：从老的 langgraph.prebuilt 迁到 LangChain v1 的 create_agent，import 路径、提示词参数和原来的 pre-model/post-model hook 分别怎么变？

**gold**：按迁移表的 TL;DR：import 路径从 langgraph.prebuilt 换成 langchain.agents；提示词参数改名为 system_prompt，动态提示词改用 middleware；pre-model hook 由 middleware 的 before_model 方法取代，post-model hook 由 after_model 取代。另外自定义 state 只支持 TypedDict（可通过 state_schema 或 middleware 定义），结构化输出移除了 prompted output，要改用 ToolStrategy 或 ProviderStrategy。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

1. **Import 路径**：从 `langgraph.prebuilt` 迁移到 `langchain.agents` [1]。
2. **提示词参数**：`prompt` 参数改名为 `system_prompt`；动态提示词改用 middleware 实现 [1]。
3. **Pre-model hook**：被 middleware 取代，使用 middleware 的 `before_model` 方法 [1]。
4. **Post-model hook**：被 middleware 取代，使用 middleware 的 `after_model` 方法 [1]。

补充说明（片段中提到的其他相关变化）：
- 自定义 state 仅支持 `TypedDict`，可通过 `state_schema` 或 middleware 定义 [1]。
- 模型动态选择通过 middleware 实现，不再支持 pre-bound models [1]。
- 工具错误处理移到 middleware 的 `wrap_tool_call` [1]。
- 结构化输出移除了 prompted output，改用 `ToolStrategy` / `ProviderStrategy` [1]。
- 流式节点名从 `"agent"` 改为 `"model"` [9]。
- 运行时上下文改为通过 `context` 参数注入，而不是 `config["configurable"]` [9]。

最小可用示例（旧写法，来自片段）：

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model="claude-sonnet-4-6",
    tools=[check_weather],
    prompt="You are a helpful assistant"
)
```

```python
from langgraph.prebuilt import create_react_agent, AgentState

def custom_summarization_function(state: AgentState):
    """Custom logic for message summarization."""
    ...

agent = create_react_agent(
    model="claude-sonnet-4-6",
    tools=tools,
    pre_model_hook=custom_summarization_function
)
```

```python
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

注意：给出的文档片段只说明了迁移后的**变化项**（import 路径、参数改名、hook 由 middleware 的 `before_model`/`after_model` 取代），但**没有给出 `create_agent` 新写法的完整代码示例**，也没有给出 middleware 中 `before_model`/`after_model` 的具体定义代码。因此无法根据现有片段提供迁移后的最小可运行示例。

**top5 片段**：

片段[1] `oss__python__migrate__langchain-v1#004` ｜ LangChain v1 migration guide ｜ Migrate to create_agent

```text
| Section | TL;DR - What’s changed | | --- | --- | | Import path | Package moved from langgraph.prebuilt to langchain.agents | | Prompts | Parameter renamed to system_prompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with before_model method | | Post-model hook | Replaced by middleware with after_model method | | Custom state | TypedDict only, can be defined via state_schema or middleware | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrap_tool_call | | Structured output | prompted output removed, use ToolStrategy / ProviderStrategy |
```

片段[2] `oss__javascript__migrate__langchain-v1#000` ｜ LangChain v1 migration guide ｜ createAgent

```text
| Section | What changed | | --- | --- | | Import path | Package moved from @langchain/langgraph/prebuilts to langchain | | Prompts | Parameter renamed to systemPrompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with beforeModel method | | Post-model hook | Replaced by middleware with afterModel method | | Custom state | Defined in middleware, zod objects only | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrapToolCall | | Structured output | prompted output removed, use toolStrategy / providerStrategy | | Streaming node name | Node name changed from "agent" to "model" |
```

片段[3] `oss__python__migrate__langgraph-supervisor#016` ｜ Migrate from langgraph-supervisor ｜ See also

```text
- LangGraph v1 migration guide : Migrate from create_react_agent to create_agent
```

片段[4] `oss__python__migrate__langchain-v1#018` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Post-model hook

```text
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
```

片段[5] `oss__python__migrate__langchain-v1#016` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Pre-model hook

```text
```

from langgraph.prebuilt import create_react_agent, AgentState



def custom_summarization_function(state: AgentState):

    """Custom logic for message summarization."""

    ...



agent = create_react_agent(

    model="claude-sonnet-4-6",

    tools=tools,

    pre_model_hook=custom_summarization_function

)

```
```

---

## v1-B-011（single-hop）

**问题**：LangChain v1 的 middleware 提供了哪些 hook？before_model、wrap_model_call、after_model 分别在什么时机跑？

**gold**：文档列了六个 hook：before_agent 在调用 agent 之前（加载记忆、校验输入）、before_model 在每次 LLM 调用之前（更新提示词、裁剪消息）、wrap_model_call 包住每次 LLM 调用（拦截并修改请求与响应）、wrap_tool_call 包住每次工具调用、after_model 在每次 LLM 响应之后（校验输出、加护栏）、after_agent 在 agent 结束后（保存结果、清理）。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

LangChain v1 的 `create_agent` 中间件提供 6 个 hook：`before_agent`、`before_model`、`wrap_model_call`、`wrap_tool_call`、`after_model`、`after_agent` [3]。

各 hook 的运行时机与典型用途 [3]：

| Hook | 运行时机 | 典型用途 |
| --- | --- | --- |
| `before_agent` | 调用 agent 之前 | 加载记忆、校验输入 |
| `before_model` | 每次 LLM 调用之前 | 更新 prompt、裁剪消息 |
| `wrap_model_call` | 包裹每次 LLM 调用 | 拦截并修改请求/响应 |
| `wrap_tool_call` | 包裹每次工具调用 | 拦截并修改工具执行 |
| `after_model` | 每次 LLM 响应之后 | 校验输出、施加 guardrail |
| `after_agent` | agent 完成后 | 保存结果、清理 |

补充：多个中间件的 `wrap_model_call` 按顺序嵌套执行，即 `middleware1.wrap_model_call() → middleware2.wrap_model_call() → middleware3.wrap_model_call() → model` [7]。

**最小可用示例**

```python
from langchain.agents.middleware import (
    before_model,
    wrap_model_call,
    AgentState,
    ModelRequest,
    ModelResponse,
)
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

以上示例来自文档片段 [5]；`after_model` 的类式写法可参考 [8]（`def after_model(self, state, runtime)`）。

**与用户说法的差异**

用户提到的 `before_model`、`wrap_model_call`、`after_model` 三个名称与片段一致，无差异；但片段中 hook 总数为 6 个，除这三个外还包括 `before_agent`、`wrap_tool_call`、`after_agent` [3]。

**top5 片段**：

片段[1] `oss__python__langchain__context-engineering#018` ｜ Context engineering in agents ｜ Response Format > Messages

```text
- Use life-cycle hooks like before_model , after_model , or wrap_tool_call (for tool returns) to update the conversation history. See the middleware documentation for more details.
```

片段[2] `oss__python__langchain__runtime#007` ｜ Runtime ｜ Access > Inside middleware

```text
``` from dataclasses import dataclass from langchain.messages import AnyMessage from langchain.agents import create_agent, AgentState from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model from langgraph.runtime import Runtime @dataclass class Context: user_name: str # Dynamic prompts @dynamic_prompt def dynamic_system_prompt(request: ModelRequest) -> str: user_name = request.runtime.context.user_name system_prompt = f"You are a helpful assistant. Address the user as {user_name}." return system_prompt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
```

片段[3] `oss__python__releases__langchain-v1#002` ｜ What's new in LangChain v1 ｜ create_agent > Middleware > Custom middleware

```text
| Hook | When it runs | Use cases |

| --- | --- | --- |

| before_agent | Before calling the agent | Load memory, validate input |

| before_model | Before each LLM call | Update prompts, trim messages |

| wrap_model_call | Around each LLM call | Intercept and modify requests/responses |

| wrap_tool_call | Around each tool call | Intercept and modify tool execution |

| after_model | After each LLM response | Validate output, apply guardrails |

| after_agent | After agent completes | Save results, cleanup |
```

片段[4] `oss__python__langchain__middleware__custom#003` ｜ Custom middleware ｜ Wrap-style hooks > Node-style hooks

```text
``` from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config from langchain.messages import AIMessage from langgraph.runtime import Runtime from typing import Any class MessageLimitMiddleware(AgentMiddleware): def __init__(self, max_messages: int = 50): super().__init__() self.max_messages = max_messages @hook_config(can_jump_to=["end"]) def before_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None: if len(state["messages"]) >= self.max_messages: return { "messages": [AIMessage("Conversation limit reached.")], "jump_to": "end" } return None def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
```

片段[5] `oss__python__langchain__middleware__custom#017` ｜ Custom middleware ｜ Class-based middleware > Decorator-based middleware

```text
``` from langchain.agents.middleware import ( before_model, wrap_model_call, AgentState, ModelRequest, ModelResponse, ) from langchain.agents import create_agent from langgraph.runtime import Runtime from typing import Any, Callable @before_model def log_before_model(state: AgentState, runtime: Runtime) -> dict[str, Any] | None: print(f"About to call model with {len(state['messages'])} messages") return None @wrap_model_call def retry_model( request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse], ) -> ModelResponse: for attempt in range(3): try: return handler(request) except Exception as e: if attempt == 2: raise print(f"Retry {attempt + 1}/3 after error: {e}")
```

---

## v1-B-012（single-hop）

**问题**：deep agent 自带的文件工具里，读大文件、改文件内容、删目录分别该用哪个，有什么值得注意的行为？

**gold**：读用 read_file：它带行号，支持 offset/limit 读取大文件，还能对非文本文件（图片、视频、音频、文档）返回多模态 content block。改内容用 edit_file，它做精确字符串替换，并带 global replace 模式。删用 delete，既可以删单个文件，也可以把目录连同它的内容递归删除。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

- **读大文件**：用 `read_file`，它支持分页（pagination）和多模态内容 [4]。
- **改文件内容**：用 `edit_file`，它做的是**精确字符串替换**（exact string replacements），不是整文件重写 [4]。
- **删目录**：用 `delete`，它会**递归删除目录及其内容**；注意该工具要求 `deepagents>=0.7` [4]。

**值得注意的行为：**

1. `delete` 是递归删除，风险较高；文档建议把 agent 限制在特定目录、只允许读写安全的文件，并考虑用容器进一步沙箱化 [2][3]。
2. 如果不想让 agent 拥有写/删能力，可以在 `FilesystemMiddleware` 里只暴露部分工具，例如只给 `read_file`、`ls`、`glob`、`grep`，这样 `write_file`、`edit_file`、`delete`、`execute` 根本不会出现 [6]。
3. 对删除这类敏感操作，可以用 `interrupt_on` 要求人工审批，例如 `"delete_file": True` [8]；子 agent 还可以单独覆盖审批策略 [8]。
4. 补充：`write_file` 是新建文件或覆盖已有文件 [4]；`execute` 仅在 sandbox 后端可用 [4]。

**最小可用示例（只读 agent，不暴露写/删工具）：**

```python
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
[6]

**与用户说法的一致性说明：** 片段中的工具名是 `read_file`、`edit_file`、`delete`（不是 `read`/`edit`/`rm` 之类），参数细节片段未给出，故不补充 [4]。

**top5 片段**：

片段[1] `oss__python__deepagents__frontend__sandbox#000` ｜ Sandbox ｜ Architecture

```text
1. Deep agent with a sandbox backend: The agent gets filesystem tools ( read_file , write_file , edit_file , delete , execute ) automatically from the sandbox
```

片段[2] `oss__javascript__security-policy#003` ｜ Security policy ｜ Best practices

```text
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
```

片段[3] `oss__python__security-policy#003` ｜ Security policy ｜ Best practices

```text
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
```

片段[4] `oss__python__deepagents__tools#022` ｜ Tools ｜ Built-in harness tools

```text
| Tool | Description |

| --- | --- |

| ls | List files in a directory. |

| read_file | Read file contents (with pagination and multimodal support). |

| write_file | Create a new file, or overwrite an existing one. |

| edit_file | Perform exact string replacements in files. |

| delete | Delete a file, or a directory and its contents recursively. The delete tool requires deepagents>=0.7 . |

| glob | Find files matching a glob pattern. |

| grep | Search file contents. |

| execute | Run shell commands (sandbox backends only). |

| task | Spawn a subagent to handle a delegated task. |
```

片段[5] `oss__javascript__deepagents__human-in-the-loop#018` ｜ Human-in-the-loop ｜ Subagent interrupts > Interrupts on tool calls

```text
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
```

---

## v1-B-013（single-hop）

**问题**：图里的循环快撞上递归上限了，RemainingSteps 和 GraphRecursionError 这两种处理方式在检测时机和掌控流程上有什么不同？

**gold**：按表，Proactive（用 RemainingSteps）是在到达上限之前就检测到，处理逻辑写在图里面、走条件路由，图会继续走向一条正常结束的路径；Reactive（GraphRecursionError）是在超过上限之后才检测，只能在图外用 try/except 兜住，图执行直接停止。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- **RemainingSteps（主动式）**：在**达到上限之前**就能检测到剩余步数，处理逻辑在**图内部**通过条件路由完成，图会继续走到一条“收尾/兜底”的完成路径，而不是直接中断 [1]。
- **GraphRecursionError（被动式）**：在**超过上限之后**才检测到，处理逻辑在**图外部**用 `try/except` 捕获，图执行会**停止** [1]。

也就是说：前者是“提前预判、图内转向、正常收尾”，后者是“事后捕获、图外处理、执行终止” [1]。

**最小可用示例：**

主动式（Python，用 `RemainingSteps` 在图内路由到兜底节点）[3][8]：

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

被动式（Python，图外捕获异常）[5][7]：

```python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke({"aggregate": []}, {"recursion_limit": 4})
except GraphRecursionError:
    print("Recursion Error")
```

被动式（JavaScript，图外捕获异常）[2][4]：

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

**补充说明（以片段为准）：** 两种语言的参数命名不同——Python 用 `recursion_limit`（下划线）[5][7]，JavaScript 用 `recursionLimit`（驼峰）[2][4]；异常类在 Python 从 `langgraph.errors` 导入 [5][7]，在 JavaScript 从 `@langchain/langgraph` 导入 [2][4]。

**top5 片段**：

片段[1] `oss__python__langgraph__graph-api-control-flow#040` ｜ Build sequences, branches, and loops ｜ Create and control loops > Access and handle the recursion counter > Handle recursion with RemainingSteps

```text
| Approach | Detection | Handling | Control flow |

| --- | --- | --- | --- |

| Proactive ( RemainingSteps ) | Before the limit | Inside the graph via conditional routing | Graph continues to a completion path |

| Reactive ( GraphRecursionError ) | After the limit | Outside the graph in try / except | Graph execution stops |
```

片段[2] `oss__python__langgraph__graph-api-control-flow#039` ｜ Build sequences, branches, and loops ｜ Create and control loops > Access and handle the recursion counter > Handle recursion with RemainingSteps

```text
f state["remaining_steps"] <= 2: return "fallback_node" return "reasoning_node" def fallback_node(state: State) -> dict: return {"messages": ["Reached complexity limit, providing best effort answer"]} builder = StateGraph(State) builder.add_node("reasoning_node", reasoning_node) builder.add_node("fallback_node", fallback_node) builder.add_edge(START, "reasoning_node") builder.add_conditional_edges("reasoning_node", route_decision) builder.add_edge("fallback_node", END) graph = builder.compile() result = graph.invoke({"messages": []}, {"recursion_limit": 10}) ```
```

片段[3] `oss__javascript__langgraph__graph-api-control-flow#033` ｜ Build sequences, branches, and loops ｜ Create and control loops > Impose a recursion limit

```text
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
```

片段[4] `oss__python__langgraph__graph-api-control-flow#038` ｜ Build sequences, branches, and loops ｜ Create and control loops > Access and handle the recursion counter > Handle recursion with RemainingSteps

```text
``` import operator from typing import Annotated, Literal from typing_extensions import TypedDict from langgraph.graph import END, START, StateGraph from langgraph.managed.is_last_step import RemainingSteps class State(TypedDict): messages: Annotated[list, operator.add] remaining_steps: RemainingSteps def reasoning_node(state: State) -> dict: remaining = state["remaining_steps"] if remaining <= 2: return {"messages": ["Approaching limit, wrapping up..."]} return {"messages": ["thinking..."]} def route_decision(state: State) -> Literal["reasoning_node", "fallback_node"]: if state["remaining_steps"] <= 2: return "fallback_node" return "reasoning_node" def fallback_node(state: State) -> dict:
```

片段[5] `oss__javascript__langgraph__graph-api-control-flow#028` ｜ Build sequences, branches, and loops ｜ Create and control loops

```text
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
```

---

## v1-B-014（multi-hop）

**问题**：我想一边把图每一步的变化当事件流给前端，一边保证服务重启后同一会话还能接着聊，这两件事对 checkpointer 的要求是同一件事吗？

**gold**：两处都落在 checkpointer 上：流模式对照表里 checkpoints 和 tasks 两种模式都标注 Requires a checkpointer，因为它们输出的是检查点事件和任务起止事件。而短期记忆（线程作用域记忆）正是把 State 通过 checkpointer 持久化到数据库，这样线程才能随时被恢复。也就是说，要让「状态变化可流式观察」和「会话可恢复」同时成立，就得给图配上 checkpointer。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：不是同一件事，但两者都依赖 checkpointer，只是用途不同。**

1. **“把图每一步的变化当事件流给前端”** 属于流式输出/事件推送，文档片段里没有直接描述这种“事件流”机制，因此无法从给出的片段确认它是否由 checkpointer 提供。给出的文档里没有找到能回答“事件流是否由 checkpointer 实现”的内容，缺少关于 streaming / events 的片段。

2. **“服务重启后同一会话还能接着聊”** 属于 checkpointer 的短期、线程级记忆能力：checkpointer 会把某个 thread 的图状态持久化为 checkpoint，用于对话连续性、human-in-the-loop、time travel 和容错 [1][2]；它能在交互之间保留“记忆”，后续消息发到同一 thread 时可以延续之前的记忆 [6][7]；并且会写入精确的图状态，以便之后恢复，即使处于错误状态也可以恢复 [4][5]。

3. 因此，从片段能确认的是：**会话续聊依赖 checkpointer 的 thread 级状态持久化** [1][2][6][7]；而**事件流给前端**在给出的片段中没有对应说明，不能据此认定二者是同一项要求。

4. 另外，片段区分了短期记忆与长期记忆：checkpointer 提供短期、thread-scoped memory，store 提供长期、跨 thread 记忆 [8][9][10][11]。所以“同一会话接着聊”对应的是 checkpointer，而不是 store。

**最小可用示例（仅体现会话续聊所需的 thread_id 配置）：**

```python
config = {"configurable": {"thread_id": "conversation-1"}}

response = graph.invoke(
    {"messages": [{"role": "user", "content": "继续刚才的话题"}]},
    config=config,
)
```

片段说明：`thread_id` 用来告诉 checkpointer 加载哪个状态 [15]；外层调用需要包含 `thread_id` 才能 checkpoint 和 resume [12]。

**差异提示：** 你问的是“事件流”和“重启续聊”是否同一件事；给出的片段只覆盖了 checkpointer 的持久化/恢复/记忆用途 [1][2][4][5][6][7]，没有覆盖“把每一步变化作为事件流推给前端”的 API 或机制，因此不能把两者等同。

**top5 片段**：

片段[1] `oss__python__langgraph__persistence#001` ｜ Persistence ｜ ROOT

```text
- Checkpointers persist a thread’s graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
```

片段[2] `oss__javascript__langgraph__persistence#001` ｜ Persistence ｜ ROOT

```text
- Checkpointers persist a thread’s graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.
```

片段[3] `oss__python__migrate__langgraph-supervisor#009` ｜ Migrate from langgraph-supervisor ｜ Migrate interrupt and resume flows > Requirements for interrupt propagation

```text
1. Compile only the outermost graph with a checkpointer. Leave subagents without checkpointer=... so they use per-invocation persistence and inherit the parent’s checkpointer at runtime.
```

片段[4] `oss__javascript__langgraph__interrupts#000` ｜ Interrupts ｜ ROOT

```text
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
```

片段[5] `oss__python__langgraph__interrupts#000` ｜ Interrupts ｜ ROOT

```text
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
```

---

## v1-B-015（multi-hop）

**问题**：迁移文档说 pre-model hook 换成了 before_model，那这个 before_model 到底在什么时刻跑、能拿它干什么？顺便确认一下 v1 里 create_agent 的 import 路径。

**gold**：迁移表写明 import 路径从 langgraph.prebuilt 变成 langchain.agents，pre-model hook 由 middleware 的 before_model 方法取代。middleware hook 表进一步说明 before_model 在每次 LLM 调用之前运行，典型用途是更新提示词和裁剪消息；作为对照，after_model 在每次 LLM 响应之后运行，用来校验输出、加护栏。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

1. `before_model` 在**每次调用 LLM 之前**运行 [3][4]。Python 侧对应 `before_model`，JS 侧对应 `beforeModel` [6][7]。
2. 典型用途是**更新提示词、裁剪消息**（update prompts, trim messages）[3][7]。
3. 迁移文档确实说 pre-model hook 被 middleware 的 `before_model` 方法取代 [5]（JS 侧为 `beforeModel` [2]）。
4. v1 里 `create_agent` 的 import 路径：Python 从 `langgraph.prebuilt` 移到 `langchain.agents` [5]；JS 从 `@langchain/langgraph/prebuilts` 移到 `langchain` [2]。

最小可用示例（Python，来自片段 [1][8]）：

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
```

需要指出的差异/补充：

- 你问的是 `before_model`，片段中 Python 用下划线命名 `before_model` [1][3][5]，JS 用驼峰 `beforeModel` [2][6][7]，注意语言差异。
- 片段 [3][4] 还列出了其他 hook（`before_agent`、`wrap_model_call`、`wrap_tool_call`、`after_model`、`after_agent`），但未给出 `before_model` 的返回值语义细节；片段 [1][8] 的示例返回 `None`，仅作日志用途。

**top5 片段**：

片段[1] `oss__python__langchain__runtime#007` ｜ Runtime ｜ Access > Inside middleware

```text
``` from dataclasses import dataclass from langchain.messages import AnyMessage from langchain.agents import create_agent, AgentState from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model from langgraph.runtime import Runtime @dataclass class Context: user_name: str # Dynamic prompts @dynamic_prompt def dynamic_system_prompt(request: ModelRequest) -> str: user_name = request.runtime.context.user_name system_prompt = f"You are a helpful assistant. Address the user as {user_name}." return system_prompt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
```

片段[2] `oss__python__langchain__runtime#008` ｜ Runtime ｜ Access > Inside middleware

```text
mpt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Processing request for user: {runtime.context.user_name}") return None # After model hook @after_model def log_after_model(state: AgentState, runtime: Runtime[Context]) -> dict | None: print(f"Completed request for user: {runtime.context.user_name}") return None agent = create_agent( model="gpt-5-nano", tools=[...], middleware=[dynamic_system_prompt, log_before_model, log_after_model], context_schema=Context ) agent.invoke( {"messages": [{"role": "user", "content": "What's my name?"}]}, context=Context(user_name="John Smith") ) ```
```

片段[3] `oss__javascript__migrate__langchain-v1#000` ｜ LangChain v1 migration guide ｜ createAgent

```text
| Section | What changed | | --- | --- | | Import path | Package moved from @langchain/langgraph/prebuilts to langchain | | Prompts | Parameter renamed to systemPrompt , dynamic prompts use middleware | | Pre-model hook | Replaced by middleware with beforeModel method | | Post-model hook | Replaced by middleware with afterModel method | | Custom state | Defined in middleware, zod objects only | | Model | Dynamic selection via middleware, pre-bound models not supported | | Tools | Tool error handling moved to middleware with wrapToolCall | | Structured output | prompted output removed, use toolStrategy / providerStrategy | | Streaming node name | Node name changed from "agent" to "model" |
```

片段[4] `oss__python__releases__langchain-v1#002` ｜ What's new in LangChain v1 ｜ create_agent > Middleware > Custom middleware

```text
| Hook | When it runs | Use cases |

| --- | --- | --- |

| before_agent | Before calling the agent | Load memory, validate input |

| before_model | Before each LLM call | Update prompts, trim messages |

| wrap_model_call | Around each LLM call | Intercept and modify requests/responses |

| wrap_tool_call | Around each tool call | Intercept and modify tool execution |

| after_model | After each LLM response | Validate output, apply guardrails |

| after_agent | After agent completes | Save results, cleanup |
```

片段[5] `oss__python__langchain__middleware__custom#000` ｜ Custom middleware ｜ Wrap-style hooks > Node-style hooks

```text
| Hook | When it runs |

| --- | --- |

| before_agent | Before agent starts (once per invocation) |

| before_model | Before each model call |

| after_model | After each model response |

| after_agent | After agent completes (once per invocation) |
```

---

## v1-B-016（multi-hop）

**问题**：我给主 agent 配了一堆技能，为什么派出去的子智能体一个都用不上？技能在运行期又是按什么规则被加载的？

**gold**：按 SubAgent 的 skills 字段说明，技能不会从主 agent 继承，只有 general-purpose 子智能体才继承主 agent 的技能；子智能体一旦配了 skills，就会跑自己独立的 SkillsMiddleware 实例，技能状态完全隔离——子智能体加载的技能父 agent 看不到，反之亦然。而技能在运行期的加载规则是 progressive disclosure：只在 agent 判断相关时才读取，格式是放在具名目录里的 SKILL.md。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. 子智能体默认**不继承**主 agent 的技能。`skills` 参数是子智能体自己的技能源路径列表，文档明确写了「Does not inherit from main agent」，只有 general-purpose 子智能体是例外，会自动继承主 agent 通过 `create_deep_agent` 传入的技能 [1][8]。
2. 技能只从「创建 agent 时传入的路径」或「子智能体专属的 skills 参数」加载，所以要确认技能确实在 skills 数组里 [2][3]。
3. 子智能体一旦有自己的 skills，会运行独立的 SkillsMiddleware 实例，技能状态完全隔离——子智能体加载的技能对父级不可见，反之亦然 [1]。
4. 运行期加载规则：技能工具只有在 agent **读取了 SKILL.md 之后**才出现，并且当摘要（summarization）把这次读取丢掉时，这些工具会消失 [4][5]。也就是说技能不是常驻的，是「读了才有、被摘要挤掉就没」。
5. 如果技能没被激活，还可以排查：多个技能描述重叠会导致 agent 跳过或选错，需要区分描述或合并相关技能 [12]；已知该用哪个技能时可以直接 pin 住，让 agent 不必自己挑 [11][13]。

**最小可用示例（Python，按片段中的字典式 SubAgent 写法）**

```python
subagent = {
    "name": "researcher",
    # 关键：子智能体要单独声明 skills，不会自动继承主 agent 的
    "skills": ["/skills/researcher/"],
    # 其他字段略
}
```

注意差异点：你说法是「主 agent 配了技能，子智能体应该能用」，但片段里 `skills` 的语义是**子智能体自己的技能源路径**，且明确「Does not inherit from main agent」，只有 general-purpose 子智能体例外 [1][8]。所以要么给子智能体显式传 `skills`，要么改用 general-purpose 子智能体。

**片段未覆盖的部分**：主 agent 侧 `create_deep_agent` 的具体参数签名、pin 技能的具体 API 写法，给出的文档里没有找到能回答这些的内容。

**top5 片段**：

片段[1] `oss__python__deepagents__subagents#007` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
```

片段[2] `oss__javascript__deepagents__skills#122` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
3. Confirm the skill is in the skills array. Skills load only from paths you pass at agent creation or from subagent-specific skills parameters.
```

片段[3] `oss__python__deepagents__skills#121` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
3. Confirm the skill is in the skills array. Skills load only from paths you pass at agent creation or from subagent-specific skills parameters.
```

片段[4] `oss__python__deepagents__skills#131` ｜ Skills ｜ Troubleshooting > Skill tool not available

```text
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
```

片段[5] `oss__javascript__deepagents__skills#131` ｜ Skills ｜ Troubleshooting > Skill tool not available

```text
1. Check that the agent read the skill. Skill tools appear only after the agent reads SKILL.md , and disappear when summarization drops that read. See Add tools to skills .
```

---

## v1-B-017（multi-hop）

**问题**：同一次运行里的中间结果、以及要跨会话复用的用户偏好，这两类数据在 LangGraph 里分别归到哪种 context、由谁承载？

**gold**：按 context 类型表，动态运行时上下文（state）是在一次运行中演化的可变数据，生命周期是单次运行，载体是 LangGraph 的 state 对象；跨会话的动态上下文（store）是跨对话共享的持久数据，载体是 LangGraph store。长期记忆正是跨会话共享的那一类：它能在任何线程里被召回，作用域是任意自定义 namespace 而不只是一个 thread ID，LangGraph 用 stores 来保存和召回。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

- **同一次运行里的中间结果**：属于 **Dynamic runtime context (state)**，由 **LangGraph state 对象**承载，生命周期是单次运行（Single run），可变（Dynamic）[1]。
- **跨会话复用的用户偏好**：属于 **Dynamic cross-conversation context (store)**，由 **LangGraph store** 承载，生命周期是跨会话（Cross-conversation），可变（Dynamic）[1]。

补充对应关系（不同页面用词略有差异，但指向同一分层）：
- 在 context-engineering 页面里，State 也被称为「Short-term memory」，Scope 为 Conversation-scoped，示例包括当前消息、上传文件、工具结果等 [3][4]；Store 被称为「Long-term memory」，Scope 为 Cross-conversation，示例包括用户偏好、提取的洞察、记忆、历史数据 [3][4]。
- 注意用词差异：概念页把 State 的 Lifetime 写作「Single run」[1]，而 context-engineering 页把 State 的 Scope 写作「Conversation-scoped」[3][4]；两处描述的是同一类 State，只是维度（运行 vs 会话）表述不同，以片段原文为准。

**最小可用示例**

静态 runtime context 通过 `context` 参数传入（注意：这是 Static runtime context，不是 state）[9]：

```python
@dataclass
class ContextSchema:
    user_name: str

graph.invoke(
    {"messages": [{"role": "user", "content": "hi!"}]},
    context={"user_name": "John Smith"}
)
```

在 Functional API 中，store 通过注入参数 `config.store` 获取，用于长期记忆 [8]：

```python
# config.store — A store instance for long-term memory [8]
```

**说明**：给出的片段没有提供「如何显式读写 state 对象」或「store 的 put/get 具体 API」的代码示例，这部分内容在片段中缺失。

**top5 片段**：

片段[1] `oss__python__concepts__context#003` ｜ Context overview ｜ ROOT

```text
| Context type | Description | Mutability | Lifetime | Access method |

| --- | --- | --- | --- | --- |

| Static runtime context | User metadata, tools, db connections passed at startup | Static | Single run | context argument to invoke / stream |

| Dynamic runtime context (state) | Mutable data that evolves during a single run | Dynamic | Single run | LangGraph state object |

| Dynamic cross-conversation context (store) | Persistent data shared across conversations | Dynamic | Cross-conversation | LangGraph store |
```

片段[2] `oss__python__deepagents__backends#054` ｜ Backends ｜ Built-in backends > StoreBackend (LangGraph store) > Namespace factories

```text
- rt.context —User-supplied context passed via LangGraph’s context schema (for example, user_id )
```

片段[3] `oss__python__langchain__context-engineering#003` ｜ Context engineering in agents ｜ Persistent context > Data sources

```text
| Data Source | Also Known As | Scope | Examples |

| --- | --- | --- | --- |

| Runtime Context | Static configuration | Conversation-scoped | User ID, API keys, database connections, permissions, environment settings |

| State | Short-term memory | Conversation-scoped | Current messages, uploaded files, authentication status, tool results |

| Store | Long-term memory | Cross-conversation | User preferences, extracted insights, memories, historical data |
```

片段[4] `oss__javascript__langchain__context-engineering#003` ｜ Context engineering in agents ｜ Persistent context > Data sources

```text
| Data Source | Also Known As | Scope | Examples |

| --- | --- | --- | --- |

| Runtime Context | Static configuration | Conversation-scoped | User ID, API keys, database connections, permissions, environment settings |

| State | Short-term memory | Conversation-scoped | Current messages, uploaded files, authentication status, tool results |

| Store | Long-term memory | Cross-conversation | User preferences, extracted insights, memories, historical data |
```

片段[5] `oss__javascript__deepagents__skills#005` ｜ Skills ｜ Usage

```text
```

const result = await agent.invoke(

  { messages: [{ role: "user", content: "What is LangGraph?" }] },

  { configurable: { thread_id: "1" } },

);

```
```

---

## v1-B-018（multi-hop）

**问题**：默认后端明明是 thread-scoped 的，为什么特性对照表里 Deep Agents 的短期记忆又写成 StateBackend？这两处矛盾吗？

**gold**：不矛盾，说的是一回事：默认后端把文件存在 langgraph state 里，靠 checkpointer 在同一个线程内跨轮次保留，且不跨线程共享，这正是 thread-scoped 的含义；特性对照表里 Deep Agents 的 Short-term memory 一栏写的也正是 StateBackend，而 LangGraph 和 LangChain 两栏写的都是 Short-term memory。也就是说 Deep Agents 默认用 state 承载短期记忆，这也解释了为什么默认后端换线程就看不到文件。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：
- 没有任何片段提到「thread-scoped」这一说法，也没有说明默认后端与 thread 作用域之间的关系。
- 片段 [1][2] 只说 Deep Agents 会把内部数据写到默认后端，并建议用 `StateBackend` 作为默认以保持这些产物是临时的（ephemeral），但没有解释它与「短期记忆」的对应关系，也没有出现「特性对照表」。
- 片段 [3]–[7] 展示的是 `CompositeBackend` 搭配 `StateBackend` 作为 default、`StoreBackend` 做路由的用法，以及按 user / assistant / org 划分 namespace 的示例，但没有讨论「默认后端是否 thread-scoped」或「短期记忆为何写作 StateBackend」。
- 片段 [8]–[10] 是后端协议方法表，与作用域问题无关。

因此无法判断这两处是否矛盾，也无法确认「默认后端是 thread-scoped」这一前提是否成立。需要补充说明默认后端作用域、以及特性对照表原文的文档片段。

**top5 片段**：

片段[1] `oss__javascript__deepagents__backends#072` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[2] `oss__python__deepagents__backends#087` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[3] `oss__python__deepagents__customization#142` ｜ Customize Deep Agents ｜ Backends

```text
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
```

片段[4] `oss__python__deepagents__customization#143` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="fireworks:accounts/fireworks/models/glm-5p2",

    backend=CompositeBackend(

        default=StateBackend(),

        routes={

            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),

        },

    ),

    store=InMemoryStore(),  # Store passed to create_deep_agent, not backend

)

```
```

片段[5] `oss__python__deepagents__memory#008` ｜ Memory ｜ Scoped memory > User-scoped memory

```text
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend



agent = create_deep_agent(

    model="google_genai:gemini-4-hydrogen",

    memory=["/memories/preferences.md"],

    skills=["/skills/"],

    backend=CompositeBackend(

        default=StateBackend(),

        routes={

            "/memories/": StoreBackend(

                namespace=lambda rt: (rt.server_info.user.identity,),

            ),

            "/skills/": StoreBackend(

                namespace=lambda rt: (rt.server_info.user.identity,),

            ),

        },

    ),

)

```
```

---

## v1-B-019（multi-hop）

**问题**：我想让 deep agent 在解释器里直接跑 shell 命令装依赖，这条路能走通吗？如果不能，官方建议用什么、对应哪个工具？

**gold**：走不通：安全能力表里「Shell commands, package installs, tests, OS-level execution」默认不可用，给出的解法不是给 interpreter 加开关，而是 Use a sandbox backend。文件工具表也印证了这一点——execute 用来在环境里跑 shell 命令，但它只在 sandbox backends 下可用。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：能走通，但不是在“解释器”里直接跑，而是通过 Sandbox（沙箱）提供的 `execute` 工具来运行 shell 命令。**

- 如果 agent 需要运行代码、安装依赖，或做文件 I/O 之外的事情，应使用 sandbox；sandbox 会提供一个隔离容器，并附带一个用于运行 shell 命令的 `execute` 工具 [1][2]。
- 如果 agent 只需要读写文件，则 filesystem backend 就够了，不需要 sandbox [8][10]。

**最小可用示例（Python，来自文档片段）：**

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-6.1-sol",
    tools=[search, fetch_url, run_query],
)
```

说明：片段 [3] 只展示了 `create_deep_agent` 的基本用法，**没有给出 sandbox / `execute` 工具的具体接入代码**。片段 [6] 展示了 JS 侧通过 `backend` 传入 sandbox 的写法：

```javascript
import { createDeepAgent } from "deepagents";
import type { LangGraphRunnableConfig } from "@langchain/langgraph";

import { getOrCreateSandboxForThread } from "./api/utils.js";

export async function agent(config: LangGraphRunnableConfig) {
  const threadId = config.configurable?.thread_id;
  if (!threadId) throw new Error("No thread_id — agent must run on a thread");

  const backend = await getOrCreateSandboxForThread(threadId);

  return createDeepAgent({
    model: "google:gemini-4-hydrogen",
    backend,
    systemPrompt: "You are an expert developer working on a project in /app.",
  });
}
```

**需要指出的差异 / 缺口：**
- 你的说法是“在解释器里直接跑 shell 命令”，文档的说法是 **sandbox 容器 + `execute` 工具**，并非解释器内建能力 [1][2]。
- 片段中没有 Python 侧 sandbox backend 的完整配置示例，也没有 `execute` 工具的参数说明；这部分内容给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__python__deepagents__going-to-production#032` ｜ Going to production ｜ Execution environment

```text
- Sandboxes add an isolated container with an execute tool for running shell commands. Use a sandbox if your agent needs to run code, install packages, or do anything beyond file I/O.
```

片段[2] `oss__javascript__deepagents__going-to-production#033` ｜ Going to production ｜ Execution environment

```text
- Sandboxes add an isolated container with an execute tool for running shell commands. Use a sandbox if your agent needs to run code, install packages, or do anything beyond file I/O.
```

片段[3] `oss__python__deepagents__tools#002` ｜ Tools ｜ ROOT

```text
```

from deepagents import create_deep_agent



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    tools=[search, fetch_url, run_query],

)

```
```

片段[4] `oss__python__deepagents__customization#004` ｜ Customize Deep Agents ｜ ROOT

```text
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
```

片段[5] `oss__python__deepagents__customization#005` ｜ Customize Deep Agents ｜ ROOT

```text
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
```

---

## v1-B-020（paraphrase）

**问题**：agent 跑到一半崩了，我重跑一次它又把前面干过的活重做一遍，有没有办法让它接着上次断的地方继续跑？

**gold**：用 graph.invoke(None, config)：它会加载最新的检查点并重试未完成的工作，而且不要再传 checkpoint_id。注意这跟「回答一个 interrupt()」不是一回事——后者要用 graph.invoke(Command(resume=answer), config)，被中断的节点会从节点开头重新执行。如果只是想回放历史，则用 get_state_history() 拿到的 snapshot.config 调 graph.invoke(None, snapshot.config)。

**judge 分**：0.0　**拒答标记**：None

**回答**：

结论：可以。文档里给出的机制是 **checkpointer 保存 agent 状态**，让运行可以停下来、之后再恢复，甚至可以在另一个进程里恢复 [1][2]。恢复时用 `Command(resume=...)`（Python）或 `new Command({ resume })`（JavaScript）把决定交回给 middleware，agent 就会继续往下跑 [3][4]。

需要注意的差异/前提：
- 片段只说明了「用 checkpointer 保存状态 → 之后 resume」这条链路，**没有**说明崩溃后自动续跑的具体配置项或异常恢复 API；能确认的是状态由 checkpointer 持久化，恢复靠 `Command(resume=...)` [1][2][3][4]。
- Python 写法是 `Command(resume=...)` [3]，JavaScript 写法是 `new Command({ resume })` [4]，两者参数形式不同，别混用。
- 片段 [5] 展示了 `checkpointer=InMemorySaver()` 的用法，但 `InMemorySaver` 是内存型，进程崩溃后内存状态会丢；片段没有给出跨进程持久化 checkpointer 的具体类名，这一点文档片段里没有覆盖。

最小可用示例（Python，按片段 [3] 的恢复方式）：

```python
# 前提：agent 构建时传入了 checkpointer，状态才会被保存 [1][2]
agent = create_agent(
    model=...,
    tools=[...],
    middleware=[...],
    checkpointer=...,   # 片段 [5] 示例用的是 InMemorySaver()
)

config = {"configurable": {"thread_id": thread_id}}

# 第一次运行，中途被 interrupt 暂停
agent.invoke({"messages": [...]}, config)

# 之后（可在另一个进程）用 Command(resume=...) 继续 [3]
from langchain_core.messages import Command  # 具体导入路径片段未给出
agent.invoke(Command(resume=decision), config)
```

JavaScript 对应恢复写法为 `new Command({ resume })` [4]。

补充：暂停发生在 middleware 按 `interrupt_on`（Python）/ `interruptOn`（JavaScript）策略检查到需要审核的调用时 [12][10]；审核方对每个待定调用给出决定，决定类型包括 approve / edit / reject / respond [13][14]。这些片段能佐证「暂停—决定—恢复」的流程，但没有提供崩溃自动续跑的实现细节。

**top5 片段**：

片段[1] `oss__javascript__concepts__human-in-the-loop#003` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
```

片段[2] `oss__python__concepts__human-in-the-loop#003` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
```

片段[3] `oss__python__concepts__human-in-the-loop#005` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
5. You resume the agent with a Command(resume=...) . The middleware applies each decision, and the agent continues.
```

片段[4] `oss__javascript__concepts__human-in-the-loop#005` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
5. You resume the agent with a new Command({ resume }) . The middleware applies each decision, and the agent continues.
```

片段[5] `oss__python__langchain__multi-agent__handoffs-customer-support#048` ｜ Build customer support with handoffs ｜ Complete example

```text
reate_agent( model, tools=all_tools, state_schema=SupportState, middleware=[ apply_step_config, SummarizationMiddleware( model="gpt-5.4-mini", trigger=("tokens", 4000), keep=("messages", 10) ) ], checkpointer=InMemorySaver(), ) # ============================================================================ # Test the workflow # ============================================================================ if __name__ == "__main__": thread_id = str(uuid7()) config = {"configurable": {"thread_id": thread_id}} result = agent.invoke( {"messages": [HumanMessage("Hi, my phone screen is cracked")]}, config ) result = agent.invoke( {"messages": [HumanMessage("Yes, it's still under warranty")]}, config
```

---

## v1-B-021（paraphrase）

**问题**：我想让 agent 真去删文件之前先拦一下，最好我还能顺手把它填的参数改掉再放行，这套人工决策一共有哪几种？

**gold**：决策类型有四种：approve 按 agent 提出的原始参数直接执行；edit 在执行前修改工具参数；reject 完全跳过这次工具调用，并把拒绝反馈返还给 agent；respond 则把人的消息直接当作合成的工具结果返回、跳过执行，用于「问用户」这类工具。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：人工决策（interrupt decision）一共有 4 种：✅ approve、✏️ edit、❌ reject、💬 respond [3][4][5][6]。其中你要的「先拦一下、还能改参数再放行」对应的是 **edit**——它在工具执行前修改工具参数 [3][4][5][6]；如果只是想原样放行用 **approve**，想直接拦掉用 **reject**（文档给的示例正是「拒绝文件删除并说明原因」）[3][4][5][6]。

各类型说明（以片段为准）：

| 决策类型 | 说明 | 示例 |
| --- | --- | --- |
| ✅ approve | 按 agent 提议的原始参数执行工具 | 按原稿发送邮件草稿 [3][4][5][6] |
| ✏️ edit | 执行前修改工具参数 | 发送邮件前改收件人 [3][4][5][6] |
| ❌ reject | 完全跳过该工具调用，并把拒绝反馈返回给 agent | 拒绝文件删除并解释原因 [3][4][5][6] |
| 💬 respond | 直接把人的消息作为合成的工具结果返回，跳过执行，用于「ask user」类工具 | 用直接回复回答 "ask_user" 提示 [3][4][5][6] |

补充两点片段里的相关信息：
- 可以按工具限制允许的决策集合，例如 `delete_file` 允许 `["approve", "edit", "reject"]`，`write_file` 只允许 `["approve", "reject"]`，`critical_operation` 只允许 `["approve"]` [8]。
- 安全实践上，建议把 agent 限制在特定目录、只允许读写安全的文件，并考虑用容器进一步沙箱化 [1][2]；另外可叠加多层防御，例如同时使用只读权限和沙箱 [10]。

最小可用示例（按工具调用 ID 逐条恢复，含 reject 的写法；片段中未给出 edit 的代码示例，故不臆造）：

```python
from langgraph.types import Command

decisions = {}
for interrupt in result.interrupts:
    if interrupt.value["name"] == "execute_sql":
        decisions[interrupt.id] = {
            "type": "reject",
            "message": "Archive the rows before deleting them.",
        }
    else:
        decisions[interrupt.id] = {"type": "approve"}

result = agent.invoke(Command(resume=decisions), config=config, version="v2")
```
[7]

需要说明的差异/缺口：片段只给出了 reject 与 approve 的恢复代码示例 [7]，以及按工具配置 `allowedDecisions` 的示例 [8]，**没有给出 edit 决策在恢复时具体如何传修改后参数的可运行代码**；这部分给出的文档里没有找到能回答的内容。

**top5 片段**：

片段[1] `oss__python__security-policy#003` ｜ Security policy ｜ Best practices

```text
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
```

片段[2] `oss__javascript__security-policy#003` ｜ Security policy ｜ Best practices

```text
- A user may ask an agent with access to the file system to delete files that should not be deleted or read the content of files that contain sensitive information. To mitigate, limit the agent to only use a specific directory and only allow it to read or write files that are safe to read or write. Consider further sandboxing the agent by running it in a container.
```

片段[3] `oss__javascript__concepts__human-in-the-loop#006` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
```

片段[4] `oss__python__langchain__human-in-the-loop#000` ｜ Human-in-the-loop ｜ Interrupt decision types

```text
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
```

片段[5] `oss__javascript__langchain__human-in-the-loop#000` ｜ Human-in-the-loop ｜ Interrupt decision types

```text
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
```

---

## v1-B-022（paraphrase）

**问题**：我按文档写了个 skill 放进去，agent 就是不激活它，怎么才能让它被用上？

**gold**：关键在于 description：agent 在发现阶段只根据 description 字段来挑技能，所以要把技能做什么、什么时候该用、以及 agent 能匹配上的关键词都写进去。文档给的好例子是 Search the arXiv preprint repository for research papers 这种具体描述，而 Helps with research 这类太泛的写法就选不中。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：skill 没被激活，文档给出的排查方向有 4 条：把 description 写具体、减少 skill 之间的描述重叠、确认 skill 在 skills 数组/路径里、必要时直接 pin 住 skill。** 另外要注意：skill 里的工具是「门控」的，agent 没读过该 skill 的 SKILL.md 之前，调用会以 unknown tool 失败 [1][2]。

具体排查项：

1. **description 写具体**：agent 在发现阶段只根据 description 字段来选 skill，所以要写清「做什么、什么时候用、可匹配的关键词」[3][4]。
2. **减少 skill 间重叠**：多个 skill 描述相似时，agent 可能跳过正确的那个或选错，需要区分描述或合并相关 skill [12][14]。
3. **确认 skill 在 skills 数组里**：skill 只会从 agent 创建时传入的路径、或 subagent 专属的 skills 参数加载 [5][6]。
4. **pin 住 skill**：当用户或应用已经知道该用哪个 skill 时，直接 pin，agent 无需自己选择就能拿到该 skill 的指令 [16]。

**最小可用示例（Python，来自文档片段）：**

```python
backend.upload_files(
    [("/skills/langgraph-docs/SKILL.md", skill_content.encode("utf-8"))]
)
agent = create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    backend=backend,
    skills=["/skills/"],
    interrupt_on={
        "write_file": True,
        "read_file": False,
        "edit_file": True,
    },
    checkpointer=checkpointer,  # Required for filesystem operations!
)
result = agent.invoke(
    {"messages": [{"role": "user", "content": "What is langgraph?"}]},
    config={"configurable": {"thread_id": "12345"}},
)
```
[7]

**补充提醒（与你的说法可能相关的差异）：**
- 片段里 skill 的工具是通过 middleware 注册的，例如 Python 用 `SkillsMiddleware(backend=backend, sources=["/skills/"], tools=[list_issues, create_issue])` [11]，JS 用 `createSkillsMiddleware({ backend, sources: ["/skills/"], tools: [listIssues, createIssue] })` [9]。如果你只把工具挂在别处而没走这个 middleware，片段没有说明它能被 skill 使用。
- 即使 skill 被激活，若对话摘要（summarization）把「读取 SKILL.md」这一步丢掉了，工具会再次不可用，直到 agent 重新读取该 skill [8][10]。

如果你能说明是「skill 完全没被选中」还是「skill 选了但工具调用报 unknown tool」，可以对应上面第 1–4 条或门控说明进一步定位；片段里没有更多关于具体配置错误的细节。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[2] `oss__python__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[3] `oss__javascript__deepagents__skills#120` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
1. Make the description more specific. The agent selects skills from the description field alone at discovery . Include what the skill does, when to use it, and keywords the agent can match: # Good description : >- Search the arXiv preprint repository for research papers. Use when the user asks about academic papers, recent research, or scientific literature. # Poor description : Helps with research.
```

片段[4] `oss__python__deepagents__skills#119` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
1. Make the description more specific. The agent selects skills from the description field alone at discovery . Include what the skill does, when to use it, and keywords the agent can match: # Good description : >- Search the arXiv preprint repository for research papers. Use when the user asks about academic papers, recent research, or scientific literature. # Poor description : Helps with research.
```

片段[5] `oss__python__deepagents__skills#121` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
3. Confirm the skill is in the skills array. Skills load only from paths you pass at agent creation or from subagent-specific skills parameters.
```

---

## v1-B-023（paraphrase）

**问题**：想让 agent 回到之前某一步的状态、从那儿岔开再试另一条路，checkpointer 支持这种事吗？

**gold**：支持，这就是文档说的 time travel：checkpointer 允许重放之前的图执行，用来复查或调试特定步骤；更进一步，它还能在任意检查点上 fork 图状态，去探索不同的轨迹。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：支持。** checkpointer 允许“时间旅行”（time travel）：可以重放之前的图执行过程来复查/调试特定步骤，也可以在任意 checkpoint 处 fork 图状态，探索替代路径 [3][4]。此外，可以从更早保存的状态继续，而不删除原始 checkpoint [6][7]；也可以基于先前的 checkpoint 修改状态后分叉，探索另一条路径 [8]。

**最小示例（示意，片段未给出完整可运行代码）：**

```python
# 概念示意：从某个历史 checkpoint 分叉
# 片段仅说明能力，未提供具体 API 调用代码
forked_state = graph.get_state(config, checkpoint_id=prior_checkpoint_id)
# 修改状态后从该点继续，探索另一条路径
```

**补充说明：**
- 片段中只描述了“可以 fork / 从更早状态继续”的能力 [3][6][8]，没有给出具体的函数名、参数或完整示例代码，因此上面的代码只是概念示意，不能当作片段中的 API 用法。
- 若涉及 human-in-the-loop 的暂停/恢复，片段提到 checkpointer 保存 agent 状态，使运行可以停止并在之后恢复，甚至可在另一个进程中恢复 [1][2]；并且只为顶层 agent 添加 checkpointer 是暂停和恢复所必需的 [5]。

**top5 片段**：

片段[1] `oss__python__concepts__human-in-the-loop#003` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
```

片段[2] `oss__javascript__concepts__human-in-the-loop#003` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
3. The checkpointer saves the agent’s state, so the run can stop and resume later, even in another process.
```

片段[3] `oss__python__langgraph__checkpointers#003` ｜ Checkpointers ｜ Why use checkpointers

```text
- Time travel : Checkpointers allow for “time travel” , allowing users to replay prior graph executions to review and / or debug specific graph steps. In addition, checkpointers make it possible to fork the graph state at arbitrary checkpoints to explore alternative trajectories.
```

片段[4] `oss__javascript__langgraph__checkpointers#003` ｜ Checkpointers ｜ Why use checkpointers

```text
- Time travel : Checkpointers allow for “time travel” , allowing users to replay prior graph executions to review and / or debug specific graph steps. In addition, checkpointers make it possible to fork the graph state at arbitrary checkpoints to explore alternative trajectories.
```

片段[5] `oss__python__langchain__multi-agent__subagents-personal-assistant#049` ｜ Build a personal assistant with subagents ｜ 6. Add human-in-the-loop review

```text
- We add a checkpointer only to the top-level agent . This is required to pause and resume execution.
```

---

## v1-B-024（no-answer）

**问题**：我们打算把模型后端换成 vLLM，它启动参数里的 --gpu-memory-utilization 默认值是多少？调到多少容易 OOM？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少：
- 关于 vLLM 服务端启动参数（如 `--gpu-memory-utilization`）的默认值说明；
- 关于该参数调高后与 OOM 风险关系的任何说明。

现有片段中，[4] 仅在聊天模型集成表格里列出了 `vLLM` 一行（且该行各能力列均为空），没有涉及 vLLM 的启动参数或显存配置；其余片段分别讲的是 DeepAgents 解释器配置 [1][2][9]、模型初始化示例 [3]、NVIDIA 组件 [5][6]、DeepAgents 记忆 [7]、向量库嵌入 [8]，均与 vLLM 启动参数无关。

**top5 片段**：

片段[1] `oss__javascript__deepagents__interpreters#026` ｜ Interpreters ｜ Configuration

```text
| Option | Default | Purpose | | --- | --- | --- | | memoryLimitBytes | 64 * 1024 * 1024 (64 MB) | Cap QuickJS heap memory per session. | | maxStackSizeBytes | 320 * 1024 | Cap QuickJS stack size per session. | | executionTimeoutMs | 5000 | Timeout limit in milliseconds for each eval call. Negative values disable the timeout. | | toolName | "eval" | Name of the interpreter tool exposed to the model. | | captureConsole | true | Capture console.log , console.warn , and console.error in the tool response. Set to false to discard console output. | | maxResultChars | 4000 | Truncate result, error, and console output returned to the model to a maximum character count. |
```

片段[2] `oss__python__deepagents__interpreters#058` ｜ Interpreters ｜ Configuration

```text
| Kwarg | Default | Purpose | | --- | --- | --- | | memory_limit | 64 * 1024 * 1024 (64 MB) | Cap QuickJS heap memory per thread. | | timeout | 5.0 | Timeout limit in seconds for each eval call. | | tool_name | "eval" | Name of the interpreter tool exposed to the model. | | capture_console | True | Capture console.log , console.warn , and console.error in the tool response. Set to False to discard console output. | | max_result_chars | 4000 | Truncate result, error, and stdout text returned to the model to a maximum character count. | | ptc | None | Allowlist of tool names or BaseTool instances exposed as tools.* inside the interpreter. Omit to disable. See Enable PTC . |
```

片段[3] `oss__python__langchain__models#016` ｜ Models ｜ Basic usage > Initialize a model

```text
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
```

片段[4] `oss__python__integrations__chat#003` ｜ Chat model integrations ｜ All chat models

```text
| Model | Stream | Tool calling | Structured output | Multimodal | Downloads | | --- | --- | --- | --- | --- | --- | | AzureChatOpenAI | ✅ | ✅ | ✅ | ✅ |  | | ChatOpenAI | ✅ | ✅ | ✅ | ✅ |  | | vLLM |  |  |  |  |  | | ChatAnthropicVertex |  |  |  |  |  | | ChatVertexAI (deprecated) | ✅ | ✅ | ✅ | ✅ |  | | ChatAnthropic | ✅ | ✅ | ✅ | ✅ |  | | ChatAnthropicTools |  |  |  |  |  | | ChatGoogleGenerativeAI | ✅ | ✅ | ✅ | ✅ |  | | ChatBedrock | ✅ | ✅ | ✅ | ✅ |  | | ChatOllama | ✅ | ✅ | ✅ | ✅ |  | | ChatGroq | ✅ | ✅ | ✅ | ✅ |  | | ChatHuggingFace | ❌ | ✅ | ✅ | ✅ |  | | ChatLiteLLM | ✅ | ✅ | ✅ | ✅ |  | | ChatMistralAI | ✅ | ✅ | ✅ | ❌ |  | | ChatXAI | ✅ | ✅ | ✅ | ❌ |  |
```

片段[5] `oss__python__integrations__providers__nvidia#005` ｜ NVIDIA ｜ Components > Reranking: NVIDIARerank

```text
```

from langchain_core.documents import Document

from langchain_nvidia_ai_endpoints import NVIDIARerank



ranker = NVIDIARerank(model="nvidia/llama-3.2-nv-rerankqa-1b-v1")

docs = ranker.compress_documents(

    query="What is GPU memory bandwidth?",

    documents=[Document(page_content=p) for p in passages],

)

```
```

---

## v1-B-025（no-answer）

**问题**：LlamaIndex 里 QueryEngine 的 similarity_top_k 默认取几？和 Haystack 的 Pipeline 比，哪个召回效果更好？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少：
- 关于 LlamaIndex `QueryEngine` 的 `similarity_top_k` 参数及其默认值的任何说明（片段 [3][4] 只在产品对比表里把 LlamaIndex 列为 Framework 选项，没有 API 细节）。
- 关于 Haystack `Pipeline` 的任何内容（所有片段均未提及 Haystack）。
- 关于两者召回效果对比的任何评测或说明。

片段 [5][6] 只提到向量库可按 similarity 和 maximum marginal relevance 查询，[8] 只列出了一些 provider 包名，都不足以回答默认值或效果对比问题。

**top5 片段**：

片段[1] `oss__python__langgraph__frontend__overview#001` ｜ Overview ｜ Architecture

```text
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
```

片段[2] `oss__javascript__langgraph__frontend__overview#001` ｜ Overview ｜ Architecture

```text
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
```

片段[3] `oss__python__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[4] `oss__javascript__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[5] `oss__python__langchain__knowledge-base#031` ｜ Build a semantic search engine with LangChain ｜ Query the vector store

```text
- By similarity and maximum marginal relevance (to balance similarity with diversity)
```

---

## v1-C-001（single-hop）

**问题**：JS 版 LangGraph 里给节点配 retryPolicy 时，默认最多尝试几次、第一次重试前等多久？

**gold**：默认 maxAttempts 是 3，表示包含第一次在内的最多尝试次数；initialInterval 默认 500 毫秒，是第一次重试前的等待时间。backoffFactor 默认 2.0，按倍数放大每次重试的间隔，maxInterval 默认 128000 毫秒，jitter 默认 true 会给间隔加随机抖动。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：JS 版 LangGraph 的 `retryPolicy` 默认 `maxAttempts` 为 3（含首次尝试），`initialInterval` 为 500 毫秒（即第一次重试前等 500ms）[4]。

补充说明：
- `maxAttempts` 是「最大尝试次数，包含第一次」，所以默认 3 次意味着首次 + 2 次重试 [4]。
- `initialInterval` 默认 500ms，是第一次重试前的等待时间；后续重试间隔会按 `backoffFactor`（默认 2.0）递增，并有 `maxInterval`（默认 128000ms）上限和默认开启的 `jitter` [4]。

最小可用示例（JS）：

```javascript
import { StateGraph } from "@langchain/langgraph";

const graph = new StateGraph(State)
  .addNode("callApi", callApi, { retryPolicy: { maxAttempts: 3 } })
  .compile();
```

上面示例显式写了 `maxAttempts: 3`，与默认值一致 [8]；若想用默认值，也可以只写 `retryPolicy: {}`（片段未展示该写法，仅按参数默认值推断，谨慎使用）。

**top5 片段**：

片段[1] `oss__javascript__langgraph__graph-api-nodes#018` ｜ Configure nodes ｜ Set graph-wide node defaults

```text
```

import { StateGraph, START } from "@langchain/langgraph";



const graph = new StateGraph(State)

  .setNodeDefaults({

    retryPolicy: { maxAttempts: 3 },

    timeout: { runTimeout: 30_000 },

    errorHandler: fallbackHandler,

  })

  .addNode("a", nodeA)

  .addNode("b", nodeB, { retryPolicy: { maxAttempts: 5 } }) // overrides default

  .addEdge(START, "a")

  .compile();

```
```

片段[2] `oss__python__langgraph__graph-api-nodes#014` ｜ Configure nodes ｜ Set graph-wide node defaults

```text
```

from langgraph.types import RetryPolicy, TimeoutPolicy



graph = (

    StateGraph(State)

    .set_node_defaults(

        retry_policy=RetryPolicy(max_attempts=3),

        timeout=TimeoutPolicy(run_timeout=30),

        error_handler=fallback_handler,

    )

    .add_node("a", node_a)

    .add_node("b", node_b, retry_policy=RetryPolicy(max_attempts=5))  # overrides default

    .add_edge(START, "a")

    .compile()

)

```
```

片段[3] `oss__python__langgraph__fault-tolerance#020` ｜ Fault tolerance ｜ Timeouts > NodeTimeoutError

```text
```

from langgraph.types import RetryPolicy, TimeoutPolicy



builder.add_node(

    "call_model",

    call_model,

    timeout=TimeoutPolicy(idle_timeout=30),

    retry_policy=RetryPolicy(max_attempts=3),

)

```
```

片段[4] `oss__javascript__langgraph__fault-tolerance#005` ｜ Fault tolerance ｜ Retries > Parameters

```text
| Parameter | Type | Default | Description | | --- | --- | --- | --- | | maxAttempts | number | 3 | Maximum number of attempts, including the first. | | initialInterval | number | 500 | Milliseconds before the first retry. | | backoffFactor | number | 2.0 | Multiplier applied to the interval after each retry. | | maxInterval | number | 128000 | Maximum milliseconds between retries. | | jitter | boolean | true | Add random jitter to the interval. | | retryOn | (error: unknown) => boolean | built-in handler (when policy is set) | Callable returning true for retryable exceptions. Only used when retryPolicy is configured. |
```

片段[5] `oss__javascript__langgraph__fault-tolerance#036` ｜ Fault tolerance ｜ Graph defaults

```text
```

import { StateGraph, START, NodeError } from "@langchain/langgraph";



const defaultErrorHandler = (

  state: typeof State.State,

  error: NodeError

) => ({ status: `handled: ${error.error.message}` });



const graph = new StateGraph(State)

  .setNodeDefaults({

    retryPolicy: { maxAttempts: 3 },

    errorHandler: defaultErrorHandler,

    timeout: { runTimeout: 30_000 },

    cachePolicy: { ttl: 60 },

  })

  .addNode("stepA", stepA)

  .addNode("stepB", stepB)

  .addEdge(START, "stepA")

  .compile();

```
```

---

## v1-C-002（single-hop）

**问题**：JS 里把子图当工具调用时，checkpointer 传 false 会失去什么？

**gold**：传 false 是 stateless 模式：子图完全不 checkpoint，像普通函数调用一样运行，因此没有 interrupts，也没有 durable execution。作为对比，传 true 是 per-thread 模式，状态会跨同一 thread 的多次调用累积；默认（None）则每次调用都全新开始，但会继承父图的 checkpointer，只为单次调用内的中断和 durable execution 服务。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：在 JS 里把子图编译为 `checkpointer: false`（即 Stateless 模式）时，会失去 **Interrupts（HITL，人机交互中断）**、**Multi-turn memory（多轮记忆）** 和 **State inspection（状态检查）** 这三项能力 [8]。同时，同一子图的多次调用之间不会保留状态（Per-thread 模式下同一子图多次调用是 ❌，而 Stateless 是 ✅，说明 Stateless 下每次调用独立、不共享线程状态）[8]。

补充说明：
- 片段中 JS 的写法是 `builder.compile({ checkpointer: false })` [2][9]，与 Python 的 `compile(checkpointer=False)` [1] 参数名一致，只是 JS 用对象形式传参。
- 对照表显示：`checkpointer=` 取值 `None`（默认，Per-invocation）、`True`（Per-thread）、`False`（Stateless）[8]。所以 `false` 明确对应 Stateless 列。
- 另外，checkpointer 的作用是保存精确的图状态以便后续恢复（即使处于错误状态）[5]；`thread_id` 用于告诉 checkpointer 加载哪份状态 [14]。传 `false` 后这些基于线程的状态持久化能力也就不适用了。

最小可用示例（JS，Stateless 子图）：

```javascript
const subgraphBuilder = new StateGraph(...);

const subgraph = subgraphBuilder.compile({ checkpointer: false });
```

如果你需要子图支持中断审批或多轮记忆，应改用 `checkpointer: true`（Per-thread）[8]。

**top5 片段**：

片段[1] `oss__python__langgraph__use-subgraphs#036` ｜ Subgraphs ｜ View example trace > Stateless

```text
```

subgraph_builder = StateGraph(...)

subgraph = subgraph_builder.compile(checkpointer=False)

```
```

片段[2] `oss__javascript__langgraph__use-subgraphs#043` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
```

const subgraph = builder.compile({ checkpointer: false });  // or true, or null

```
```

片段[3] `oss__javascript__langgraph__use-subgraphs#042` ｜ Subgraphs ｜ Subgraph persistence > Stateless

```text
```

const subgraphBuilder = new StateGraph(...);

const subgraph = subgraphBuilder.compile({ checkpointer: false });

```
```

片段[4] `oss__python__langgraph__use-subgraphs#037` ｜ Subgraphs ｜ View example trace > Checkpointer reference

```text
| Feature | Per-invocation (default) | Per-thread | Stateless |

| --- | --- | --- | --- |

| checkpointer= | None | True | False |

| Interrupts (HITL) | ✅ | ✅ | ❌ |

| Multi-turn memory | ❌ | ✅ | ❌ |

| Multiple calls (different subgraphs) | ✅ |  | ✅ |

| Multiple calls (same subgraph) | ✅ | ❌ | ✅ |

| State inspection |  | ✅ | ❌ |
```

片段[5] `oss__javascript__langgraph__use-subgraphs#044` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
| Feature | Per-invocation (default) | Per-thread | Stateless |

| --- | --- | --- | --- |

| checkpointer= | None | True | False |

| Interrupts (HITL) | ✅ | ✅ | ❌ |

| Multi-turn memory | ❌ | ✅ | ❌ |

| Multiple calls (different subgraphs) | ✅ |  | ✅ |

| Multiple calls (same subgraph) | ✅ | ❌ | ✅ |

| State inspection |  | ✅ | ❌ |
```

---

## v1-C-003（single-hop）

**问题**：JS 里图跑到一半报错，想从最近一次检查点接着跑、不要重新提交输入，graph.invoke 该怎么传？

**gold**：调 await graph.invoke(null, config)：它会加载最新的 checkpoint 并重试没做完的工作，而且不要传 checkpoint_id。如果要回应中断，则改成 await graph.invoke(new Command({ resume: answer }), config)，answer 会成为该 interrupt 的返回值。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 JS 里要从最近一次检查点继续（例如出错后重试未完成的工作），应调用 `await graph.invoke(null, config)`，即第一个参数传 `null`，并省略 `checkpoint_id` [3]。

最小可用示例：

```javascript
// 出错后从最近一次检查点继续，不重新提交输入
await graph.invoke(null, config);
```

补充说明（均来自片段）：
- 该调用会「加载最新检查点并重试未完成的工作」，且要省略 `checkpoint_id` [3]。
- 注意与「提交新输入」区分：提交新输入是 `await graph.invoke(input, config)`，会把输入应用到已保存状态并从入口点开始 [3]。
- 另外，若想「回答 interrupt()」，应使用 `await graph.invoke(new Command({ resume: answer }), config)`，而不是传 `null` [3]。
- 片段还提示：用 `Command(update=...)` 会从最新检查点恢复，而传普通对象会从 START 重新开始；若你的目的是「接着跑」而非「重新开始」，不要误传普通输入对象 [6]。

**top5 片段**：

片段[1] `oss__python__langgraph__interrupts#077` ｜ Interrupts ｜ Debugging with interrupts

```text
```

graph = builder.compile(

    interrupt_before=["node_a"],

    interrupt_after=["node_b", "node_c"],

    checkpointer=checkpointer,

)



# Pass a thread ID to the graph

config = {

    "configurable": {

        "thread_id": "some_thread"

    }

}



# Run the graph until the breakpoint

graph.invoke(inputs, config=config)



# Resume the graph

graph.invoke(None, config=config)

```
```

片段[2] `oss__python__langgraph__checkpointers#006` ｜ Checkpointers ｜ Core concepts > Threads > Choose how to continue a thread

```text
| Goal | Invocation | Execution |

| --- | --- | --- |

| Submit new input | graph.invoke(input, config) | Applies the input to saved state and starts from the entry point. |

| Continue after an error | graph.invoke(None, config) | Loads the latest checkpoint and retries unfinished work. Omit checkpoint_id . |

| Answer an interrupt() | graph.invoke(Command(resume=answer), config) | Supplies the interrupt’s return value. The interrupted node starts again from its beginning. |

| Replay history | graph.invoke(None, snapshot.config) | Uses a snapshot from get_state_history() and re-executes nodes after that checkpoint. |
```

片段[3] `oss__javascript__langgraph__checkpointers#006` ｜ Checkpointers ｜ Core concepts > Threads > Choose how to continue a thread

```text
| Goal | Invocation | Execution |

| --- | --- | --- |

| Submit new input | await graph.invoke(input, config) | Applies the input to saved state and starts from the entry point. |

| Continue after an error | await graph.invoke(null, config) | Loads the latest checkpoint and retries unfinished work. Omit checkpoint_id . |

| Answer an interrupt() | await graph.invoke(new Command({ resume: answer }), config) | Supplies the interrupt’s return value. The interrupted node starts again from its beginning. |

| Replay history | await graph.invoke(null, snapshot.config) | Uses a snapshot from getStateHistory() and re-executes nodes after that checkpoint. |
```

片段[4] `oss__python__langgraph__graph-api#017` ｜ Graph API overview ｜ Command > Input to invoke or stream

```text
```

# Wrong: resumes from the latest checkpoint

graph.invoke(Command(update={

    "messages": [{"role": "user", "content": "follow up"}]

}), config)



# Correct: plain dict restarts from START

graph.invoke({

    "messages": [{"role": "user", "content": "follow up"}]

}, config)

```
```

片段[5] `oss__python__langgraph__use-time-travel#011` ｜ Use time-travel ｜ Interrupts

```text
{"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human history = list(graph.get_state_history(config)) before_ask = [s for s in history if s.next == ("ask_human",)][-1] replay_result = graph.invoke(None, before_ask.config) # Pauses at interrupt — waiting for new Command(resume=...) # Fork from before ask_human fork_config = graph.update_state(before_ask.config, {"value": ["forked"]}) fork_result = graph.invoke(None, fork_config) # Pauses at interrupt — waiting for new Command(resume=...) # Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value":
```

---

## v1-C-004（single-hop）

**问题**：JS 的 streamMode 里 updates 和 values 有什么区别？

**gold**：values 在每一步之后给出完整的状态；updates 给出每一步之后的状态更新，而且同一步里的多个更新会被分别流式发出。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 片段中关于 `values` 与 `updates` 区别的说明只出现在 Python 侧（LangGraph 的 stream modes 表 [2] 和 LangChain 的 supported stream modes 表 [7]），其中 `values` 是「每步之后的完整状态」，`updates` 是「每步之后的状态更新，同一步内的多个更新会分别流式输出」[2][7]。
- 但没有任何片段说明 JS 的 `streamMode` 支持哪些取值、`values` 在 JS 中是否存在或行为如何。JS 相关片段 [5][6][8] 只出现了 `streamMode: "updates"` 的用法示例，没有 `values` 的说明，也没有 JS 侧的模式对照表。

因此无法基于给定片段确认 JS 中 `updates` 与 `values` 的差异。

**top5 片段**：

片段[1] `oss__python__langgraph__streaming#008` ｜ Streaming ｜ Get started > Stream output format (v2)

```text
``` for part in graph.stream( {"topic": "ice cream"}, stream_mode=["values", "updates", "messages", "custom"], version="v2", ): if part["type"] == "values": # ValuesStreamPart — full state snapshot after each step print(f"State: topic={part['data']['topic']}") elif part["type"] == "updates": # UpdatesStreamPart — only the changed keys from each node for node_name, state in part["data"].items(): print(f"Node `{node_name}` updated: {state}") elif part["type"] == "messages": # MessagesStreamPart — (message_chunk, metadata) from LLM calls msg, metadata = part["data"] print(msg.content, end="", flush=True) elif part["type"] == "custom": # CustomStreamPart — arbitrary data from get_stream_writer()
```

片段[2] `oss__python__langgraph__streaming#010` ｜ Streaming ｜ Stream modes

```text
| Mode | Type | Description | | --- | --- | --- | | values | ValuesStreamPart | Full state after each step. | | updates | UpdatesStreamPart | State updates after each step. Multiple updates in the same step are streamed separately. | | messages | MessagesStreamPart | 2-tuples of (LLM token, metadata) from LLM calls. | | custom | CustomStreamPart | Custom data emitted from nodes via get_stream_writer . | | checkpoints | CheckpointStreamPart | Checkpoint events (same format as get_state() ). Requires a checkpointer. | | tasks | TasksStreamPart | Task start/finish events with results and errors. Requires a checkpointer. |
```

片段[3] `oss__python__langgraph__streaming#005` ｜ Streaming ｜ Get started > Stream output format (v2)

```text
```

{

    "type": "values" | "updates" | "messages" | "custom" | "checkpoints" | "tasks" | "debug",

    "ns": (),           # namespace tuple, populated for subgraph events

    "data": ...,        # the actual payload (type varies by stream mode)

}

```
```

片段[4] `oss__python__langgraph__streaming#013` ｜ Streaming ｜ Stream modes > Graph state

```text
```

for chunk in graph.stream(

    {"topic": "ice cream"},

    stream_mode="updates",

    version="v2",

):

    if chunk["type"] == "updates":

        for node_name, state in chunk["data"].items():

            print(f"Node `{node_name}` updated: {state}")

```
```

片段[5] `oss__javascript__langgraph__graph-api-send-command#005` ｜ Use Send and Command ｜ Use Send for map-reduce

```text
```

const stream = await graph.stream(

  { topic: "animals" },

  { streamMode: "updates" }

);

for await (const chunk of stream) {

  console.log(chunk);

}

```
```

---

## v1-C-005（single-hop）

**问题**：JS 的 createAgent 里 responseFormat 能直接接受哪几种 schema？

**gold**：可以接 ZodSchema，也可以接任何 Standard Schema 库的 schema，或者用 Record<string, unknown> 表示的 JSON Schema；responseFormat 还能写成这几种的数组。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 JS 的 `createAgent` 里，`responseFormat` 可以直接接受三种 schema 形式：Zod schema、任意 Standard Schema 库的 schema、JSON Schema（以 `Record<string, unknown>` 表示）；此外还可以传一个数组（`ResponseFormat[]`）[1]。另外，也可以用 `toolStrategy(...)` 或 `providerStrategy(...)` 包装 schema 来显式指定策略 [9]。

最小可用示例：

```javascript
import { createAgent } from "langchain";
import { z } from "zod";

const agent = createAgent({
  // ...
  responseFormat: z.object({ summary: z.string() }), // Zod schema
});
```

补充说明：
- 片段 [1] 给出的类型定义是 `ZodSchema | StandardSchema | Record<string, unknown>`，并允许 `ResponseFormat | ResponseFormat[]` [1]。
- 若想显式选择策略，片段 [9] 展示了 `responseFormat: providerStrategy(z.object({ ... }))` 或 `responseFormat: toolStrategy(z.object({ ... }))` [9]；片段 [3] 也给出了 `responseFormat: toolStrategy(OutputSchema)` 的用法 [3]。
- 注意：片段中未出现“直接传 Pydantic 模型”之类的 Python 写法用于 JS；Python 侧的 `response_format=OutputSchema` 属于另一套 API [5]，与 JS 的 `responseFormat` 不是同一接口。

**top5 片段**：

片段[1] `oss__javascript__langchain__structured-output#000` ｜ Structured output ｜ ROOT

```text
```

type ResponseFormat = (

    | ZodSchema<StructuredResponseT> // a Zod schema

    | StandardSchema<StructuredResponseT> // any Standard Schema library

    | Record<string, unknown> // a JSON Schema

)



const agent = createAgent({

    // ...

    responseFormat: ResponseFormat | ResponseFormat[]

})

```
```

片段[2] `oss__javascript__langchain__frontend__integrations__copilotkit#012` ｜ CopilotKit ｜ Extend the LangGraph deployment with a custom endpoint

```text
``` import { createAgent, createMiddleware, toolStrategy } from "langchain"; import { z } from "zod"; import { deepSearchTool, searchWebTool } from "../tools/index.js"; const contextSchema = z.object({ output_schema: z.unknown().optional(), }); const structuredOutputMiddleware = createMiddleware({ name: "CopilotKitStructuredOutput", contextSchema, wrapModelCall: async (request, handler) => { const rawOutputSchema = getRuntimeOutputSchema(request.runtime); const schema = normalizeOutputSchema(rawOutputSchema); if (!schema) { return handler(request); } const responseFormat = toolStrategy( schema as unknown as Parameters<typeof toolStrategy>[0], { toolMessageContent:
```

片段[3] `oss__javascript__migrate__langchain-v1#024` ｜ LangChain v1 migration guide ｜ createAgent > Structured output > Tool and provider strategies

```text
```

import { createAgent, toolStrategy } from "langchain";

import * as z from "zod";



const OutputSchema = z.object({

  summary: z.string(),

  sentiment: z.string(),

});



const agent = createAgent({

  model: "gpt-5.4-mini",

  tools,

  // explicitly using tool strategy

  responseFormat: toolStrategy(OutputSchema),

});

```
```

片段[4] `oss__javascript__deepagents__customization#009` ｜ Customize Deep Agents ｜ ROOT

```text
gents stack | | interruptOn | Pause before tool calls for human approval | | responseFormat | Structured output schema | | contextSchema | Per-run runtime context schema (user IDs, API keys, feature flags) |
```

片段[5] `oss__python__migrate__langchain-v1#036` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Structured output > Tool and provider strategies

```text
```

from langgraph.prebuilt import create_react_agent

from pydantic import BaseModel



class OutputSchema(BaseModel):

    summary: str

    sentiment: str



agent = create_react_agent(

    model="gpt-5.4-mini",

    tools=tools,

    # using tool strategy by default with no option for provider strategy

    response_format=OutputSchema  

)



# OR



agent = create_react_agent(

    model="gpt-5.4-mini",

    tools=tools,

    # using a custom prompt to instruct the model to generate the output schema

    response_format=("please generate ...", OutputSchema)

)

```
```

---

## v1-C-006（single-hop）

**问题**：JS 里断言 Agent 输出时，怎么检查一条消息是不是 AIMessage、以及它带的 tool calls 对不对？

**gold**：用 toBeAIMessage(expected?) 检查这个值是不是 AIMessage，还可以顺带匹配 content 或字段；用 toHaveToolCalls(expected) 检查 AIMessage 是否恰好带有给定的 tool calls，且与顺序无关。如果要核对工具结果消息，toBeToolMessage 还能匹配 tool_call_id。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 JS 里可以用自定义 matcher 检查 AIMessage 及其 tool calls。`toHaveToolCalls(expected)` 检查 AIMessage 是否**恰好**包含给定的 tool calls（与顺序无关）[2]；`toHaveToolCallCount(n)` 检查 tool call 数量恰好为 n [2]；`toContainToolCall(expected)` 检查是否**至少包含一个**匹配的 tool call，且支持 `.not` [2]。另外 `toBeAIMessage(...)` 可用于断言消息类型 [9]。

最小可用示例（来自文档片段）：

```javascript
const response = await agent.invoke({
  messages: [new HumanMessage("Weather in SF and NYC?")]
});

const aiMsg = response.messages.find(
  (m) => AIMessage.isInstance(m) && m.tool_calls?.length
);

// 检查特定 tool calls 是否存在（顺序无关）
expect(aiMsg).toHaveToolCalls([
  { name: "get_weather", args: { city: "San Francisco" } },
  { name: "get_weather", args: { city: "New York" } },
]);

// 只检查数量
expect(aiMsg).toHaveToolCallCount(2);

// 检查至少一个 tool call 匹配（支持 .not）
expect(aiMsg).toContainToolCall({ name: "get_weather" });
expect(aiMsg).not.toContainToolCall({ name: "send_email" });
```

补充：断言消息类型可用 `expect(lastMessage).toBeAIMessage({ name: "weather-bot" })` [9]。

需要注意的差异/限制：
- 片段 [2] 的 matcher 参考表里，`toHaveToolCalls` 的描述是“exactly the given tool calls（顺序无关）”，即**恰好匹配**，不是“包含”；若要“至少一个匹配”应使用 `toContainToolCall` [2]。
- 片段中未给出 `toBeAIMessage` 的完整参数说明，只出现了一个带 `{ name: "weather-bot" }` 的调用示例 [9]。
- 片段 [3][6] 是 Python 写法（如 `isinstance(m, AIMessage)`、`tc["name"]`），与 JS 的 `AIMessage.isInstance(m)`、matcher 写法不同，不要混用 [3][6]。

**top5 片段**：

片段[1] `oss__javascript__langchain__test__integration-testing#010` ｜ Integration testing ｜ Use custom test matchers > Assert on tool calls

```text
```

const response = await agent.invoke({

  messages: [new HumanMessage("Weather in SF and NYC?")]

});

const aiMsg = response.messages.find(

  (m) => AIMessage.isInstance(m) && m.tool_calls?.length

);



// Check that specific tool calls are present (order-independent)

expect(aiMsg).toHaveToolCalls([

  { name: "get_weather", args: { city: "San Francisco" } },

  { name: "get_weather", args: { city: "New York" } },

]);



// Check only the count

expect(aiMsg).toHaveToolCallCount(2);



// Check that at least one tool call matches (supports .not)

expect(aiMsg).toContainToolCall({ name: "get_weather" });

expect(aiMsg).not.toContainToolCall({ name: "send_email" });

```
```

片段[2] `oss__javascript__langchain__test__integration-testing#015` ｜ Integration testing ｜ Use custom test matchers > Matcher reference

```text
all_id . | | toHaveToolCalls(expected) | Check that an AIMessage has exactly the given tool calls (order-independent). | | toHaveToolCallCount(n) | Check that an AIMessage has exactly n tool calls. | | toContainToolCall(expected) | Check that an AIMessage contains at least one matching tool call. Supports .not . | | toHaveToolMessages(expected) | Check that a message array contains the given ToolMessage instances, in order. | | toHaveBeenInterrupted(value?) | Check that a result has an __interrupt__ . Optionally match the interrupt value. | | toHaveStructuredResponse(expected?) | Check that a result has a structuredResponse . Optionally match specific fields. |
```

片段[3] `oss__python__langchain__test__integration-testing#005` ｜ Integration testing ｜ Assert on structure, not content

```text
```

from langchain.agents import create_agent

from langchain.messages import AIMessage, HumanMessage



def test_agent_calls_weather_tool():

    agent = create_agent("claude-sonnet-4-6", tools=[get_weather])

    result = agent.invoke({

        "messages": [HumanMessage(content="What's the weather in SF?")]

    })



    messages = result["messages"]

    tool_calls = [

        tc

        for msg in messages

        if hasattr(msg, "tool_calls")

        for tc in (msg.tool_calls or [])

    ]



    assert any(tc["name"] == "get_weather" for tc in tool_calls)

    assert isinstance(messages[-1], AIMessage)

    assert len(messages[-1].content) > 0

```
```

片段[4] `oss__javascript__langchain__test__integration-testing#014` ｜ Integration testing ｜ Use custom test matchers > Matcher reference

```text
| Matcher | Description | | --- | --- | | toBeHumanMessage(expected?) | Check that the value is a HumanMessage . Optionally match content (string) or fields (object). | | toBeAIMessage(expected?) | Check that the value is an AIMessage . Optionally match content or fields. | | toBeSystemMessage(expected?) | Check that the value is a SystemMessage . Optionally match content or fields. | | toBeToolMessage(expected?) | Check that the value is a ToolMessage . Optionally match content or fields like tool_call_id . | | toHaveToolCalls(expected) | Check that an AIMessage has exactly the given tool calls (order-independent). |
```

片段[5] `oss__python__langchain__frontend__headless-tools#014` ｜ Headless tools ｜ Render tool activity inline

```text
```

import type { ToolCallWithResult, DefaultToolCall } from "@langchain/react";



function Message({ message, toolCalls }: {

  message: AIMessage,

  toolCalls: ToolCallWithResult[]

}) {

  const messageToolCalls = toolCalls.filter((tc) =>

    message.tool_calls?.some((call) => call.id === tc.call.id),

  );



  return (

    <div>

      {message.text && <p>{message.text}</p>}

      {messageToolCalls.map((tc) => (

        <HeadlessToolCard key={tc.call.id} toolCall={tc} />

      ))}

    </div>

  );

}

```
```

---

## v1-C-007（single-hop）

**问题**：JS 里调 maxMarginalRelevanceSearch 时，lambda 调大是更偏向相关性还是多样性？

**gold**：lambda 为 1.0 时偏向相关性（relevance），为 0.0 时偏向多样性（diversity），示例里取 0.5 是折中。另外 k 是要返回的文档数，fetchK 是挑选之前先考虑的候选数。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：在 JS 里调大 `lambda` 是更偏向相关性，调小则更偏向多样性。** 文档注释明确写着 `lambda: 0.5, // 1.0 favors relevance, 0.0 favors diversity` [2]。

需要注意的 API 差异（以片段为准）：
- JS 方法名是 `maxMarginalRelevanceSearch`（驼峰），参数是 `fetchK` 和 `lambda` [2]。
- Python 对应方法名是 `max_marginal_relevance_search`，参数是 `fetch_k` 和 `lambda_mult` [1]。如果你看到的是 `lambda_mult`，那是 Python 侧的写法，不是 JS 的。

最小可用示例（JS）：

```javascript
const docs = await vectorStore.maxMarginalRelevanceSearch(query, {
  k: 4, // number of documents to return
  fetchK: 20, // number of candidates to consider before selecting
  lambda: 0.9, // 调大 → 更偏向相关性；1.0 favors relevance, 0.0 favors diversity
});
```

补充：MMR 的作用是「在相似度和多样性之间做平衡」[3][4]，属于提升检索质量的手段之一 [5][6]。

**top5 片段**：

片段[1] `oss__python__langchain__retrieval-optimization#010` ｜ Improve retrieval quality ｜ Diversify results with maximal marginal relevance

```text
```

docs = vector_store.max_marginal_relevance_search(

    query,

    k=4,  # number of documents to return

    fetch_k=20,  # number of candidates to consider before selecting

    lambda_mult=0.5,  # 1.0 favors relevance, 0.0 favors diversity

)

```
```

片段[2] `oss__javascript__langchain__retrieval-optimization#011` ｜ Improve retrieval quality ｜ Diversify results with maximal marginal relevance

```text
```

const docs = await vectorStore.maxMarginalRelevanceSearch(query, {

  k: 4, // number of documents to return

  fetchK: 20, // number of candidates to consider before selecting

  lambda: 0.5, // 1.0 favors relevance, 0.0 favors diversity

});

```
```

片段[3] `oss__python__langchain__knowledge-base#031` ｜ Build a semantic search engine with LangChain ｜ Query the vector store

```text
- By similarity and maximum marginal relevance (to balance similarity with diversity)
```

片段[4] `oss__javascript__langchain__knowledge-base#017` ｜ Build a semantic search engine with LangChain ｜ Query the vector store

```text
- By similarity and maximum marginal relevance (to balance similarity with diversity)
```

片段[5] `oss__python__langchain__retrieval-optimization#000` ｜ Improve retrieval quality ｜ ROOT

```text
Improve retrieval quality Improve RAG retrieval quality in LangChain with metadata filtering, query transformation, hybrid search, maximal marginal relevance, and reranking.
```

---

## v1-C-008（single-hop）

**问题**：JS 里想对用户输入和模型输出都做邮箱脱敏，piiMiddleware 要怎么配？

**gold**：对输入调 piiMiddleware("email", { strategy: "redact", applyToInput: true })，对输出再调一次 piiMiddleware("email", { strategy: "redact", applyToOutput: true })，然后把这两个都放进 createAgent 的 middleware 数组里。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 JS 里用 `piiMiddleware`，对输入和输出都做邮箱脱敏，需要分别注册两个中间件实例，一个设 `applyToInput: true`，一个设 `applyToOutput: true`，`strategy` 都用 `"redact"` [5]。注意 JS 版参数是驼峰命名 `applyToInput` / `applyToOutput`，不是 Python 版的 `apply_to_input` / `apply_to_output` [5][2]。

最小可用示例（JS）：

```javascript
import { createAgent, piiMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [searchTool, sendEmailTool],
  middleware: [
    // 输入侧：脱敏用户输入中的邮箱
    piiMiddleware("email", {
      strategy: "redact",
      applyToInput: true,
    }),
    // 输出侧：脱敏模型输出中的邮箱
    piiMiddleware("email", {
      strategy: "redact",
      applyToOutput: true,
    }),
  ],
});
```

补充说明：
- 片段 [5] 正是「组合多个 guardrail」的示例，其中对 email 分别配置了 `applyToInput: true` 和 `applyToOutput: true` 两个 `piiMiddleware` [5]。
- 片段 [4] 也展示了 JS 版 `piiMiddleware` 的驼峰参数写法（`applyToInput: true`），但只覆盖输入侧 [4]。
- 片段 [7] 出现了另一个名字 `piiRedactionMiddleware({ patterns: [...] })`，与 `piiMiddleware` 不是同一个 API，若你看到的是这个名称，请以对应片段为准，不要混用 [7]。

**top5 片段**：

片段[1] `oss__python__langchain__event-streaming#016` ｜ Event streaming ｜ Custom updates > Register transformers on middleware

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import PIIMiddleware



agent = create_agent(

    model="gpt-5-nano",

    tools=[],

    middleware=[

        PIIMiddleware("email", strategy="redact", apply_to_output=True),

    ],

)

```
```

片段[2] `oss__python__langchain__guardrails#017` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, send_email_tool], middleware=[ # Layer 1: Deterministic input filter (before agent) ContentFilterMiddleware(banned_keywords=["hack", "exploit"]), # Layer 2: PII protection (before and after model) PIIMiddleware("email", strategy="redact", apply_to_input=True), PIIMiddleware("email", strategy="redact", apply_to_output=True), # Layer 3: Human approval for sensitive tools HumanInTheLoopMiddleware(interrupt_on={"send_email": True}), # Layer 4: Model-based safety check (after agent) SafetyGuardrailMiddleware(),
```

片段[3] `oss__python__langchain__middleware__built-in#042` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > PII detection

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import PIIMiddleware



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[],

    middleware=[

        PIIMiddleware("email", strategy="redact", apply_to_input=True),

        PIIMiddleware("credit_card", strategy="mask", apply_to_input=True),

    ],

)

```
```

片段[4] `oss__javascript__deepagents__going-to-production#055` ｜ Going to production ｜ Guardrails > Data privacy

```text
```

import { createAgent, piiMiddleware } from "langchain";



const agent = createAgent({

  model: "google:gemini-4-hydrogen",

  middleware: [

    piiMiddleware("email", { strategy: "redact", applyToInput: true }),

    piiMiddleware("credit_card", { strategy: "mask", applyToInput: true }),

  ],

});

```
```

片段[5] `oss__javascript__langchain__guardrails#011` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` import { createAgent, piiMiddleware, humanInTheLoopMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, sendEmailTool], middleware: [ // Layer 1: Deterministic input filter (before agent) contentFilterMiddleware(["hack", "exploit"]), // Layer 2: PII protection (before and after model) piiMiddleware("email", { strategy: "redact", applyToInput: true, }), piiMiddleware("email", { strategy: "redact", applyToOutput: true, }), // Layer 3: Human approval for sensitive tools humanInTheLoopMiddleware({ interruptOn: { send_email: { allowAccept: true, allowEdit: true, allowRespond: true }, } }), // Layer 4: Model-based safety check (after agent)
```

---

## v1-C-009（single-hop）

**问题**：JS 里用 summarizationMiddleware 压缩历史时，trigger 和 keep 分别控制什么？

**gold**：trigger: { tokens: 4000 } 表示对话接近 4000 token 时就触发摘要；keep: { messages: 20 } 表示保留最近 20 条消息不动。还需要用 model 指定真正执行摘要的模型。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- `trigger` 控制**何时触发摘要压缩**（达到阈值就压缩）。可以是单个条件，也可以是多个条件组合 [4][5]。
- `keep` 控制**压缩后保留多少历史**（保留最近的消息数量）[4][5]。

**关于 trigger 的细节（JS 版）：**

- 单个条件用对象形式，如 `{ tokens: 4000 }`，表示 token 数达到 4000 时触发 [5]。
- 多个条件用数组形式，如 `[{ tokens: 3000 }, { messages: 6 }]`，文档注释说明这是 **OR 逻辑**（token ≥ 3000 或消息数 ≥ 6 就触发）[4]。
- 注意：文档里 JS 版把 `trigger: { tokens: 4000, messages: 10 }` 这种对象内多字段描述为 **AND 逻辑**（token ≥ 4000 且消息数 ≥ 10）[4]。这与 Python 版用元组/列表表达条件的写法不同，以片段为准。

**关于 keep 的细节：**

- JS 版用对象形式，如 `{ messages: 20 }`，表示压缩后保留最近 20 条消息 [4][5]。

**最小可用示例（JS）：**

```javascript
import { createAgent, summarizationMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [weatherTool, calculatorTool],
  middleware: [
    summarizationMiddleware({
      model: "gpt-5.4-mini",
      trigger: { tokens: 4000 },   // token 达到 4000 时触发压缩
      keep: { messages: 20 },      // 压缩后保留最近 20 条消息
    }),
  ],
});
```

来源：[4][5]

**需要指出的差异：** 你问的是 JS 的 `summarizationMiddleware`，片段 [4][5] 正是 JS 版；而片段 [1][2][3][7] 是 Python 版 `SummarizationMiddleware`，写法不同（如 `trigger=("tokens", 4000)`、`keep=("messages", 20)`），不要混用 [1][3]。

**top5 片段**：

片段[1] `oss__python__langchain__multi-agent__handoffs-customer-support#034` ｜ Build customer support with handoffs ｜ 8. Manage message history

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import SummarizationMiddleware  

from langgraph.checkpoint.memory import InMemorySaver



agent = create_agent(

    model,

    tools=all_tools,

    state_schema=SupportState,

    middleware=[

        apply_step_config,

        SummarizationMiddleware(

            model="gpt-5.4-mini",

            trigger=("tokens", 4000),

            keep=("messages", 10)

        )

    ],

    checkpointer=InMemorySaver(),

)

```
```

片段[2] `oss__python__langchain__context-engineering#052` ｜ Context engineering in agents ｜ Life-cycle context > Example: Summarization

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import SummarizationMiddleware



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[...],

    middleware=[

        SummarizationMiddleware(

            model="gpt-5.4-mini",

            trigger={"tokens": 4000},

            keep=("messages", 20),

        ),

    ],

)

```
```

片段[3] `oss__python__langchain__middleware__built-in#028` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Summarization

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import SummarizationMiddleware # Single condition: trigger if tokens >= 4000 agent = create_agent( model="gpt-6.1-sol", tools=[your_weather_tool, your_calculator_tool], middleware=[ SummarizationMiddleware( model="gpt-5.4-mini", trigger=("tokens", 4000), keep=("messages", 20), ), ], ) # Multiple conditions: trigger if number of tokens >= 3000 OR messages >= 6 agent2 = create_agent( model="gpt-6.1-sol", tools=[your_weather_tool, your_calculator_tool], middleware=[ SummarizationMiddleware( model="gpt-5.4-mini", trigger=[ ("tokens", 3000), ("messages", 6), ], keep=("messages", 20), ), ], ) # AND logic:
```

片段[4] `oss__javascript__langchain__middleware__built-in#031` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Summarization

```text
``` import { createAgent, summarizationMiddleware } from "langchain"; // Single condition (AND logic): trigger if tokens >= 4000 AND messages >= 10 const agent = createAgent({ model: "gpt-6.1-sol", tools: [weatherTool, calculatorTool], middleware: [ summarizationMiddleware({ model: "gpt-5.4-mini", trigger: { tokens: 4000, messages: 10 }, keep: { messages: 20 }, }), ], }); // Multiple conditions (OR logic): trigger if tokens >= 3000 OR messages >= 6 const agent2 = createAgent({ model: "gpt-6.1-sol", tools: [weatherTool, calculatorTool], middleware: [ summarizationMiddleware({ model: "gpt-5.4-mini", trigger: [ { tokens: 3000 }, { messages: 6 }, ], keep: { messages: 20 }, }), ], });
```

片段[5] `oss__javascript__langchain__middleware__built-in#025` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Summarization

```text
```

import { createAgent, summarizationMiddleware } from "langchain";



const agent = createAgent({

  model: "gpt-6.1-sol",

  tools: [weatherTool, calculatorTool],

  middleware: [

    summarizationMiddleware({

      model: "gpt-5.4-mini",

      trigger: { tokens: 4000 },

      keep: { messages: 20 },

    }),

  ],

});

```
```

---

## v1-C-010（single-hop）

**问题**：JS 里通过 MCPAdapter 接进来的工具在服务端报错时，Agent 那边会看到什么？

**gold**：服务端错误（isError: true）会作为一条失败的 ToolMessage 传给模型，所以 Agent 能读到服务端自己的报错信息并尝试恢复。默认情况下 createAgent 也会把传输层失败转成错误的 tool message。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

在 JS 里通过 `MCPAdapter` 接入的工具，当服务端返回 `isError: true` 时，Agent 会收到一条 **`status: "error"` 的 `ToolMessage`**（即“失败的 ToolMessage”），模型可以读到服务端自己的错误文本并据此恢复 [1][5][6]。

补充要点：

- 默认情况下，`createAgent` 还会把**传输层失败**也转换成 error tool message [1][9]。
- 这类错误是“返回”而不是“抛出”的，因此**不会**触发基于异常的处理逻辑（例如 `toolRetryMiddleware` 或 `ToolNode` 的 `handleToolErrors`）；要重试需检查 `ToolMessage.status`（例如在 `wrapToolCall` 中）[5]。
- 服务端的错误文本**总是**会发送给模型，即使 `outputHandling` 把文本路由到 artifact [5]。
- 注意区分：**直接调用**（plain arguments）仍然会抛出 `ToolException`，MCP 响应在 `error.result` 里 [5][6]。

> 与用户说法可能不一致之处：用户问的是“Agent 那边会看到什么”，片段明确的是 Agent 的工具调用路径下得到 `ToolMessage`（`status: "error"`）；而“直接调用”路径是抛异常，两者行为不同 [5][6]。

## 最小可用示例（JS）

```javascript
import { MCPAdapter } from "@langchain/mcp-adapters";
import { createAgent, ToolMessage } from "langchain";

async function divideByZero(serverUrl: string) {
  const adapter = new MCPAdapter({
    servers: { calculator: { url: serverUrl } },
  });
  try {
    const tools = await adapter.listTools();
    const agent = createAgent({ model: "claude-sonnet-5", tools });
    const result = await agent.invoke({
      messages: [{ role: "user", content: "What is 10 divided by 0?" }],
    });

    // 服务端错误（isError: true）以失败的 ToolMessage 形式到达模型
    for (const message of result.messages) {
      if (ToolMessage.isInstance(message) && message.status === "error") {
        console.log(`Tool error: ${message.text}`);
      }
    }
  } finally {
    await adapter.close();
  }
}
```

来源：[1]（错误以失败 ToolMessage 到达模型、默认转换传输失败）、[9]（遍历 `result.messages` 并按 `status === "error"` 打印）、[5]（`status: "error"`、不触发异常式处理、错误文本总发给模型）、[6]（`isError` 返回 error message，直接调用仍抛出）。

**top5 片段**：

片段[1] `oss__javascript__langchain__mcp__tools#006` ｜ Tools ｜ View example trace > Errors

```text
``` import { MCPAdapter } from "@langchain/mcp-adapters"; import { createAgent, ToolMessage } from "langchain"; async function divideByZero(serverUrl: string) { const adapter = new MCPAdapter({ servers: { calculator: { url: serverUrl } }, }); try { const tools = await adapter.listTools(); const agent = createAgent({ model: "claude-sonnet-5", tools }); const result = await agent.invoke({ messages: [{ role: "user", content: "What is 10 divided by 0?" }], }); // A server error (isError: true) reaches the model as a failed ToolMessage, // so the agent can read the server's own message and recover. By default, // createAgent also converts transport failures into error tool messages.
```

片段[2] `oss__python__langchain__mcp__tools#001` ｜ Tools ｜ Use MCP tools in an agent

```text
```

from langchain.agents import create_agent

from langchain.mcp import MCPAdapter



async def run_agent(server) -> dict:

    # Discover the server's tools, then hand them to the agent like any other

    # LangChain tools. The tools hold the client, so the agent stays usable

    # for the life of the adapter context.

    async with MCPAdapter(server) as adapter:

        tools = await adapter.list_tools()

        agent = create_agent("claude-sonnet-5", tools)

        return await agent.ainvoke(

            {

                "messages": [

                    {"role": "user", "content": "What is the forecast for Oslo?"}

                ]

            }

        )

```
```

片段[3] `oss__python__langchain__mcp__tools#006` ｜ Tools ｜ View example trace > Errors

```text
``` from langchain.agents import create_agent from langchain.mcp import MCPAdapter from langchain.messages import ToolMessage async def divide_by_zero(server) -> dict: async with MCPAdapter(server) as adapter: tools = await adapter.list_tools() agent = create_agent("claude-sonnet-5", tools) result = await agent.ainvoke( { "messages": [ { "role": "user", "content": "Use the divide tool to calculate 10 divided by 0.", } ] } ) # A server error (isError=True) reaches the model as a failed ToolMessage, # so the agent can read the server's own message and recover. Transport # failures still raise, because a model cannot act on those. for message in result["messages"]:
```

片段[4] `oss__javascript__langchain__mcp__tools#001` ｜ Tools ｜ Use MCP tools in an agent

```text
```

import { MCPAdapter } from "@langchain/mcp-adapters";

import { createAgent } from "langchain";



async function main(server: string) {

  const adapter = new MCPAdapter({

    servers: { weather: { url: server } },

  });



  try {

    // Discover the server's tools, then hand them to the agent like any other

    // LangChain tools. Keep the adapter open while the agent calls its tools.

    const tools = await adapter.listTools();

    const agent = createAgent({ model: "claude-sonnet-5", tools });



    await agent.invoke({

      messages: [{ role: "user", content: "What is the forecast for Oslo?" }],

    });

  } finally {

    await adapter.close();

  }

}

```
```

片段[5] `oss__javascript__migrate__langchain-mcp-adapters#044` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ Tool results

```text
- Tool errors : When a server returns a result with isError , the adapter returns a ToolMessage with status: "error" for an agent’s tool call. Direct invocation with plain arguments still throws a ToolException , with the MCP response in error.result . Because these results are returned rather than thrown, they no longer trigger exception-based handling such as toolRetryMiddleware or a ToolNode handleToolErrors function. Check ToolMessage.status (for example in wrapToolCall ) to retry them. The server’s error text is always sent to the model, even when outputHandling routes text to the artifact.
```

---
