# 审计材料 3/8（30 条，明细文件第 61–90 行）

## v1-C-011（single-hop）

**问题**：subagents 和 router 这两种多 Agent 模式，在路由上有什么不同？

**gold**：subagents 模式让主 Agent 把子 Agent 当工具来协调，所有路由都经过主 Agent，由它决定何时、怎样调用每个子 Agent；router 模式则用一个路由步骤先给输入分类，再把请求分发给一个或多个专门 Agent，最后把各自结果合成一个回复。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- **Subagents**：所有路由都经过主 Agent。主 Agent 把子 Agent 当作工具来协调，由它决定何时、如何调用每个子 Agent [1][2]。子 Agent 不直接与用户交互，结果返回给主 Agent [5][6]。
- **Router**：路由是一个独立的预处理步骤（通常是一次 LLM 调用或基于规则的逻辑），负责对输入分类并分发给一个或多个专用 Agent，最后把结果合成为统一回复 [1][2][3][4]。Router 本身通常不维护对话历史，也不做多轮编排 [3][4]。
- 补充对比：Subagents 的主 Agent 会维护上下文、可跨轮调用多个子 Agent 并编排多步流程 [13]；而 Router 是无状态的预处理环节 [3][4]。

**最小示例（示意，非文档原文代码）：**

```text
# Subagents：主 Agent 决定调用哪个子 Agent（子 Agent 作为工具）
main_agent -> decide -> call subagent_A as tool -> subagent_A returns result to main_agent

# Router：先分类，再分发，最后合成
router(classify input) -> dispatch to agent_X / agent_Y -> synthesize combined response
```

**差异提示：** 你问的是「路由上的不同」，文档中 Router 明确被描述为「不维护对话历史、不做多轮编排的预处理步骤」[3][4]，而 Subagents 的路由发生在主 Agent 的持续编排过程中 [1][2][13]——这是两者在路由机制上的核心区别。

**top5 片段**：

片段[1] `oss__javascript__langchain__multi-agent#003` ｜ Multi-agent ｜ Patterns

```text
| Pattern | How it works | | --- | --- | | Subagents | A main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent. | | Handoffs | Behavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt. | | Skills | Specialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed. | | Router | A routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response. |
```

片段[2] `oss__python__langchain__multi-agent#003` ｜ Multi-agent ｜ Patterns

```text
| Pattern | How it works | | --- | --- | | Subagents | A main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent. | | Handoffs | Behavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt. | | Skills | Specialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed. | | Router | A routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response. |
```

片段[3] `oss__python__langchain__multi-agent__router#002` ｜ Router ｜ Stateless

```text
- Router : A dedicated routing step (often a single LLM call or rule-based logic) that classifies the input and dispatches to agents. The router itself typically doesn’t maintain conversation history or perform multi-turn orchestration—it’s a preprocessing step.
```

片段[4] `oss__javascript__langchain__multi-agent__router#002` ｜ Router ｜ Stateless

```text
- Router : A dedicated routing step (often a single LLM call or rule-based logic) that classifies the input and dispatches to agents. The router itself typically doesn’t maintain conversation history or perform multi-turn orchestration—it’s a preprocessing step.
```

片段[5] `oss__python__langchain__multi-agent__subagents#000` ｜ Subagents ｜ Key characteristics

```text
- No direct user interaction: Subagents return results to the main agent, not the user (though you can use interrupts within a subagent to allow user interaction)
```

---

## v1-C-012（single-hop）

**问题**：内置的 model retry 和 model fallback 两个 middleware 分别做什么？

**gold**：Model retry 对失败的模型调用按 exponential backoff 自动重试；Model fallback 在主模型失败时自动切到备用的其他模型。同一张表里 Model refusal 的差别是：模型拒答时直接抛错，而不是把拒答当成最终答案。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

- **Model retry**：自动重试失败的模型调用，采用可配置的指数退避（exponential backoff）[3][4]。
- **Model fallback**：当主模型失败时，自动回退到备选模型 [3][4]。

两者都是 provider-agnostic（与提供商无关）的内置 middleware [3][4]。

**最小可用示例（Model retry，JavaScript）：**

```javascript
import { createAgent, modelRetryMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [searchTool, databaseTool],
  middleware: [
    modelRetryMiddleware({
      maxRetries: 3,
      backoffFactor: 2.0,
      initialDelayMs: 1000,
    }),
  ],
});
```
[7]

**补充说明：**

- 片段 [5] 的示例中同时使用了 `modelRetryMiddleware` 和 `toolRetryMiddleware`，并注明 model retry 用于对 rate limits、timeouts 和 5xx 错误进行重试 [5]。注意这是示例注释里的说明，内置 middleware 表格本身只写了「failed model calls」[3][4]。
- 片段 [8] 提到「使用 fallback models，在主模型失败时自动用另一个模型重试」[8]，与 model fallback 的描述一致，但该片段未给出具体 API 名称或参数。
- 给出的文档片段中**没有** model fallback 的代码示例或参数说明，因此无法提供其最小可用示例。

**top5 片段**：

片段[1] `oss__javascript__releases__changelog#026` ｜ Changelog ｜ v1.1.0

```text
- Model retry middleware : New middleware for automatically retrying failed model calls with configurable exponential backoff, improving agent reliability.
```

片段[2] `oss__python__releases__changelog#053` ｜ Changelog ｜ langchain v1.1.0

```text
- Model retry middleware : New middleware for automatically retrying failed model calls with configurable exponential backoff.
```

片段[3] `oss__python__langchain__middleware__built-in#000` ｜ Prebuilt middleware ｜ Provider-agnostic middleware

```text
| Middleware | Description | | --- | --- | | Tool error | Catch tool execution exceptions and convert them to error messages for the model. | | Tool retry | Automatically retry failed tool calls with exponential backoff. | | Model retry | Automatically retry failed model calls with exponential backoff. | | Model fallback | Automatically fallback to alternative models when primary fails. | | Model refusal | Raise an error when the model refuses, instead of treating the refusal as a final answer. | | Summarization | Automatically summarize conversation history when approaching token limits. | | Human-in-the-loop | Pause execution for human approval of tool calls. |
```

片段[4] `oss__javascript__langchain__middleware__built-in#000` ｜ Prebuilt middleware ｜ Provider-agnostic middleware

```text
| Middleware | Description | | --- | --- | | Tool retry | Automatically retry failed tool calls with exponential backoff. | | Model retry | Automatically retry failed model calls with exponential backoff. | | Model fallback | Automatically fallback to alternative models when primary fails. | | Model refusal | Throw an error when the model refuses, instead of treating the refusal as a final answer. | | Summarization | Automatically summarize conversation history when approaching token limits. | | Human-in-the-loop | Pause execution for human approval of tool calls. | | Model call limit | Limit the number of model calls to prevent excessive costs. |
```

片段[5] `oss__javascript__deepagents__fault-tolerance#008` ｜ Fault tolerance ｜ Retries

```text
```

import {

  createAgent,

  modelRetryMiddleware,

  toolRetryMiddleware,

} from "langchain";



const agent = createAgent({

  model: "google:gemini-4-hydrogen",

  middleware: [

    // Retry model calls on rate limits, timeouts, and 5xx errors

    modelRetryMiddleware({ maxRetries: 3, backoffFactor: 2.0, initialDelayMs: 1000 }),

    // Retry specific tools that hit external APIs (not all tools)

    toolRetryMiddleware({

      maxRetries: 2,

      tools: ["search", "fetch_url"],

      retryOn: [TimeoutError, TypeError],

    }),

  ],

});

```
```

---

## v1-C-013（single-hop）

**问题**：在 LangGraph 节点里，普通函数和 Task 在恢复时的重跑行为差在哪？

**gold**：节点里的普通函数不单独 checkpoint，它跑在节点的 super-step 里，节点重跑时它就跟着重跑；Task 不会产生新的图 checkpoint，结果存在运行中的 entrypoint 或父 checkpoint 里，恢复时外层 entrypoint 或节点从头重放，已完成的 Task 直接返回存下的结果。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：普通函数在节点重跑时会跟着整个节点一起重跑；Task 不会新增图检查点，恢复时外层入口或节点从头重放，但已完成的 Task 会返回已存结果，因此不会重复执行 [1][2]。所以有副作用或开销大的步骤应选 Task [1][2]。

最小示例（片段未给出 Task 的代码写法，这里只示意普通函数节点）：

```python
from dataclasses import dataclass
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

class State(TypedDict):
    input: str
    results: str

@dataclass
class Context:
    user_id: str

builder = StateGraph(State)

def plain_node(state: State):
    return state

def node_with_runtime(state: State, runtime: Runtime[Context]):
    return {"results": f"Hello, {state['input']}!"}

builder.add_node("plain_node", plain_node)
builder.add_node("node_with_runtime", node_with_runtime)
```

补充差异：普通函数没有自己的检查点，运行在节点的 super-step 内，节点重跑它就重跑 [1][2]；Task 没有新的图检查点，结果随运行中的入口或父检查点存储，恢复时外层从头重放、已完成 Task 返回存储结果 [1][2]。另外，片段提到新增、删除或重排 resume 点之前的 `@task` 调用或 interrupt 调用会因按位置匹配缓存结果而导致错配 [3][4]。

**top5 片段**：

片段[1] `oss__python__langgraph__graph-api#011` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
| Primitive | Own checkpoint | On resume or retry | Choose when | | --- | --- | --- | --- | | Plain function inside a node | No. It runs inside the node’s super-step . | Re-runs whenever the node re-runs. | No routing fork after the step, and repeating it with the rest of the node is acceptable. | | Task | No new graph checkpoint. The result is stored with the running entrypoint or parent checkpoint. | The enclosing entrypoint or node replays from the start. Completed tasks return stored results. | The step has a side effect or is expensive, and must not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread.
```

片段[2] `oss__javascript__langgraph__graph-api#014` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
| Primitive | Own checkpoint | On resume or retry | Choose when | | --- | --- | --- | --- | | Plain function inside a node | No. It runs inside the node’s super-step . | Re-runs whenever the node re-runs. | No routing fork after the step, and repeating it with the rest of the node is acceptable. | | Task | No new graph checkpoint. The result is stored with the running entrypoint or parent checkpoint. | The enclosing entrypoint or node replays from the start. Completed tasks return stored results. | The step has a side effect or is expensive, and must not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread.
```

片段[3] `oss__javascript__langgraph__backward-compatibility#013` ｜ Backward compatibility ｜ Non-determinism

```text
- Adding, removing, or reordering @task calls or interrupt calls that come before the resume point. LangGraph matches cached results and resume values to calls by their position in the replay, so shifting that position can cause the wrong cached value to be replayed against a different call.
```

片段[4] `oss__python__langgraph__backward-compatibility#016` ｜ Backward compatibility ｜ Non-determinism

```text
- Adding, removing, or reordering @task calls or interrupt calls that come before the resume point. LangGraph matches cached results and resume values to calls by their position in the replay, so shifting that position can cause the wrong cached value to be replayed against a different call.
```

片段[5] `oss__javascript__langgraph__checkpointers#005` ｜ Checkpointers ｜ Why use checkpointers

```text
- Pending writes : When a graph node fails mid-execution at a given super-step , LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that super-step. When you resume graph execution from that super-step you don’t re-run the successful nodes.
```

---

## v1-C-014（multi-hop）

**问题**：在 JS SDK 里，短期记忆和长期记忆分别由哪个组件负责，作用范围有什么不同？

**gold**：Checkpointer 保存图状态快照，作用范围是单个 thread，属于线程内的短期记忆，用于对话连续、human-in-the-loop、time travel 和容错；Store 保存应用自定义的 key-value 数据，跨 thread 共享，属于长期记忆。用 Store 时通常把 userId 和业务上下文组成 namespace 数组，再调 store.put(namespace, key, value) 写入。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

在 JS SDK 中：

- **短期记忆**由 **checkpointer** 负责，作用范围是**线程（thread）级**，即在一个会话内维护消息历史，让线程可以随时恢复 [1][4][8]。
- **长期记忆**由 **store** 负责，作用范围**跨会话、跨线程**，可按自定义 namespace 作用域保存和召回数据 [1][4][11]。

作用范围差异：短期记忆是 thread-scoped，随线程存在；长期记忆跨会话共享，不局限于单个 thread ID [4][11]。

**最小可用示例**

文档片段中给出的示例是 Python 的（`InMemoryStore` + `create_agent(..., store=store)`）[14]，JS SDK 的具体代码示例在给出的片段里没有出现，因此这里不臆造 JS 代码。

**需要指出的差异/缺口**

- 你问的是「JS SDK」，片段 [1][4][8][11] 确实来自 JavaScript 文档路径，能支撑上述组件与作用范围的结论。
- 但片段中没有 JS 版的 checkpointer / store 初始化代码示例，只有 Python 示例 [14]。若需要 JS 具体写法，给出的文档里没有找到能回答这部分的内容。

**top5 片段**：

片段[1] `oss__javascript__langgraph__persistence#000` ｜ Persistence ｜ ROOT

```text
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
```

片段[2] `oss__python__langgraph__persistence#000` ｜ Persistence ｜ ROOT

```text
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
```

片段[3] `oss__python__concepts__memory#000` ｜ Memory overview ｜ ROOT

```text
- Short-term memory , or thread -scoped memory, tracks the ongoing conversation by maintaining message history within a session. LangGraph manages short-term memory as a part of your agent’s state . State is persisted to a database using a checkpointer so the thread can be resumed at any time. Short-term memory updates when the graph is invoked or a step is completed, and the State is read at the start of each step.
```

片段[4] `oss__javascript__concepts__memory#000` ｜ Memory overview ｜ ROOT

```text
- Short-term memory , or thread -scoped memory, tracks the ongoing conversation by maintaining message history within a session. LangGraph manages short-term memory as a part of your agent’s state . State is persisted to a database using a checkpointer so the thread can be resumed at any time. Short-term memory updates when the graph is invoked or a step is completed, and the State is read at the start of each step.
```

片段[5] `oss__python__langchain__tools#008` ｜ Tools ｜ Access context

```text
| Component | Description | Use case | | --- | --- | --- | | State | Short-term memory - mutable data that exists for the current conversation (messages, counters, custom fields) | Access conversation history, track tool call counts | | Context | Immutable configuration passed at invocation time (user IDs, session info) | Personalize responses based on user identity | | Store | Long-term memory - persistent data that survives across conversations | Save user preferences, maintain knowledge base | | Stream Writer | Emit real-time updates during tool execution | Show progress for long-running operations |
```

---

## v1-C-015（multi-hop）

**问题**：Agent 要执行敏感工具前我想停下来等人审，人能给出哪几种决定，之后又怎么让同一条对话继续？

**gold**：审批型中断有四种决定：approve 按 Agent 提议的原参数执行，edit 先改工具参数再执行，reject 整个跳过这次工具调用并把拒绝意见回传给 Agent，respond 则把人的回复当成合成的工具结果、不真正执行。恢复时对同一个会话调 await graph.invoke(new Command({ resume: answer }), config)，answer 会成为该 interrupt 的返回值。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

根据片段，人审时可以给出的决定类型（`decisions` 列表中的 `type`）包括：

- **`approve`**：批准执行 [1][2]
- **`respond`**：直接以人的回复作为工具结果返回，需带 `message` 字段 [3][4]
- **`edit`**：修改要执行的动作，需带 `editedAction`（JS）/ `edited_action`（Python），内含 `name` 和 `args` [5][6]

注意：片段里没有出现 `reject`/`deny` 之类的类型，只有上述三种。

让同一条对话继续的方式：用**相同的 `thread_id`** 再次调用 `agent.invoke`，传入 `Command`，把决定放在 `resume.decisions` 里 [1][2][3]。片段反复强调「Same thread ID to resume the paused conversation」[1][2][3][5]。

另外，`decisions` 是**列表，每个待审动作一条，顺序必须与 interrupt 请求中动作的顺序一致** [3][5]。

## 最小可用示例

批准（JavaScript）[1]：

```javascript
const config = { configurable: { thread_id: "some_id" } };

let result = await agent.invoke(
  { messages: [{ role: "user", content: "Send an email to the team" }] },
  config
);

result = await agent.invoke(
  new Command({ resume: { decisions: [{ type: "approve" }] } }),
  config // Same thread ID to resume the paused conversation
);
```

直接回复（Python）[4]：

```python
agent.invoke(
    Command(
        resume={
            "decisions": [
                {
                    "type": "respond",
                    "message": "Blue.",
                }
            ]
        }
    ),
    config=config,  # Same thread ID to resume the paused conversation
    version="v2",
)
```

编辑动作（JavaScript）[5]：

```javascript
await agent.invoke(
  new Command({
    resume: {
      decisions: [
        {
          type: "edit",
          editedAction: {
            name: "new_tool_name",
            args: { key1: "new_value", key2: "original_value" },
          },
        },
      ],
    },
  }),
  config // Same thread ID to resume the paused conversation
);
```

## 与用户说法的差异提示

- 用户说「停下来等人审」，片段中的机制名称是 **Human-in-the-loop**，通过 `humanInTheLoopMiddleware({ interruptOn: {...} })` 配置哪些工具需要中断审批（如 `send_email`、`delete_database` 设为需要审批，`search` 设为 `false` 自动放行）[8]。
- 片段中 `edit` 的字段名在 JS 是 `editedAction` [5]，Python 是 `edited_action` [6]，两者不一致，使用时按语言区分。
- 片段 [8] 中模型写作 `"gpt-6.1-sol"`，与常见模型名不同，此处以片段为准。

**top5 片段**：

片段[1] `oss__javascript__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
}); // Human-in-the-loop requires a thread ID for persistence const config = { configurable: { thread_id: "some_id" } }; // Agent will pause and wait for approval before executing sensitive tools let result = await agent.invoke( { messages: [{ role: "user", content: "Send an email to the team" }] }, config ); result = await agent.invoke( new Command({ resume: { decisions: [{ type: "approve" }] } }), config  // Same thread ID to resume the paused conversation ); ```
```

片段[2] `oss__python__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
ySaver(), ) # Human-in-the-loop requires a thread ID for persistence config = {"configurable": {"thread_id": "some_id"}} # Agent will pause and wait for approval before executing sensitive tools result = agent.invoke( {"messages": [{"role": "user", "content": "Send an email to the team"}]}, config=config ) result = agent.invoke( Command(resume={"decisions": [{"type": "approve"}]}), config=config  # Same thread ID to resume the paused conversation ) ```
```

片段[3] `oss__javascript__langchain__human-in-the-loop#042` ｜ Human-in-the-loop ｜ Responding to interrupts > Decision types

```text
```

await agent.invoke(

    new Command({

        // Decisions are provided as a list, one per action under review.

        // The order of decisions must match the order of actions

        // in the interrupt request.

        resume: {

            decisions: [

                {

                    type: "respond",

                    // The human's reply, returned directly as the tool result

                    message: "Blue.",

                }

            ]

        }

    }),

    config  // Same thread ID to resume the paused conversation

);

```
```

片段[4] `oss__python__langchain__human-in-the-loop#044` ｜ Human-in-the-loop ｜ Responding to interrupts > Decision types

```text
```

agent.invoke(

    Command(

        # Decisions are provided as a list, one per action under review.

        # The order of decisions must match the order of actions

        # in the interrupt request.

        resume={

            "decisions": [

                {

                    "type": "respond",

                    # The human's reply, returned directly as the tool result

                    "message": "Blue.",

                }

            ]

        }

    ),

    config=config,  # Same thread ID to resume the paused conversation

    version="v2",

)

```
```

片段[5] `oss__javascript__langchain__human-in-the-loop#040` ｜ Human-in-the-loop ｜ Responding to interrupts > Decision types

```text
``` await agent.invoke( new Command({ // Decisions are provided as a list, one per action under review. // The order of decisions must match the order of actions // in the interrupt request. resume: { decisions: [ { type: "edit", // Edited action with tool name and args editedAction: { // Tool name to call. // Will usually be the same as the original action. name: "new_tool_name", // Arguments to pass to the tool. args: { key1: "new_value", key2: "original_value" }, } } ] } }), config  // Same thread ID to resume the paused conversation ); ```
```

---

## v1-C-016（multi-hop）

**问题**：JS 里流式跑一个可能被打断的 Agent，怎么判断这次是暂停在 interrupt 上还是已经跑完，暂停了又从哪里取中断信息？

**gold**：先看 stream.interrupted，它表示这次运行是否为等人输入而暂停；暂停时用 stream.interrupts 取中断 payload，示例里是 stream.interrupts[0].payload。另外 stream.messages 流出聊天模型消息和 token 增量，stream.values 迭代状态快照并可以 await 最终值。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 用 `agent.streamEvents(..., { version: "v3" })` 流式运行时，跑完后检查 `stream.interrupted` 布尔值判断是否暂停；若为 `true`，中断信息从 `stream.interrupts` 读取 [1][3][7]。

**最小可用示例（JS）：**

```javascript
import { Command } from "@langchain/langgraph";

const config = { configurable: { thread_id: "some_id" } };

const stream = await agent.streamEvents(
  { messages: [{ role: "user", content: "Delete old records from the database" }] },
  { ...config, version: "v3" }
);

for await (const message of stream.messages) {
  for await (const token of message.text) {
    process.stdout.write(token);
  }
}

// 判断是否暂停在 interrupt 上
if (stream.interrupted) {
  console.log(`\n\nInterrupt: ${JSON.stringify(stream.interrupts)}`);
}
```

**要点说明：**

- `stream.interrupted`：每次运行结束后检查图是否暂停 [3][4]。
- `stream.interrupts`：暂停时从中读取中断 payload；使用事件流（`stream_events(..., version="v3")`）时，传给 `interrupt()` 的值会出现在 `stream.interrupts` 上 [7]。
- 恢复时用 `new Command({ resume: ... })` 再次调用 `streamEvents`，并保持同样的 `config`（含 `thread_id`）[1][9]。

**与用户说法的差异：** 用户问的是「从哪里取中断信息」，文档中对应字段名是 `stream.interrupts`（复数），判断标志是 `stream.interrupted`（过去式），两者不要混用 [3][7]。

**top5 片段**：

片段[1] `oss__javascript__langchain__human-in-the-loop#044` ｜ Human-in-the-loop ｜ Streaming with human-in-the-loop

```text
``` import { Command } from "@langchain/langgraph"; const config = { configurable: { thread_id: "some_id" } }; // Stream agent progress and LLM tokens until interrupt const stream = await agent.streamEvents( { messages: [{ role: "user", content: "Delete old records from the database" }] }, { ...config, version: "v3" } ); for await (const message of stream.messages) { for await (const token of message.text) { process.stdout.write(token); } } // Check whether the run paused for human input if (stream.interrupted) { console.log(`\n\nInterrupt: ${JSON.stringify(stream.interrupts)}`); } // Resume with streaming after human decision const resumeStream = await agent.streamEvents(
```

片段[2] `oss__python__langchain__human-in-the-loop#046` ｜ Human-in-the-loop ｜ Streaming with human-in-the-loop

```text
``` from langgraph.types import Command config = {"configurable": {"thread_id": "some_id"}} # Stream agent progress and LLM tokens until interrupt stream = agent.stream_events( {"messages": [{"role": "user", "content": "Delete old records from the database"}]}, config=config, version="v3", ) for message in stream.messages: for token in message.text: print(token, end="", flush=True) # Check whether the run paused for human input if stream.interrupted: print(f"\n\nInterrupt: {stream.interrupts}") # Resume with streaming after human decision stream = agent.stream_events( Command(resume={"decisions": [{"type": "approve"}]}), config=config, version="v3", ) for message in stream.messages:
```

片段[3] `oss__javascript__langgraph__interrupts#026` ｜ Interrupts ｜ View example trace

```text
- stream.interrupted / stream.interrupts : After each run, check whether the graph paused; read payloads from stream.interrupts
```

片段[4] `oss__python__langgraph__interrupts#025` ｜ Interrupts ｜ View example trace

```text
- stream.interrupted / stream.interrupts : After each run, check whether the graph paused; read payloads from stream.interrupts
```

片段[5] `oss__javascript__deepagents__human-in-the-loop#012` ｜ Human-in-the-loop ｜ Handle interrupts with streaming

```text
ns in real time if (token.text) { process.stdout.write(token.text); } } if (mode === "updates" && data?.__interrupt__) { pendingInterrupt = data.__interrupt__[0]; } } // If no interrupt occurred, the agent finished if (!pendingInterrupt) break; const interruptValue = pendingInterrupt.value; const actionRequests = interruptValue.actionRequests; const reviewConfigs = interruptValue.reviewConfigs; const configMap = Object.fromEntries( reviewConfigs.map((cfg: any) => [cfg.actionName, cfg]) ); for (const action of actionRequests) { const review = configMap[action.name]; console.log(`\nTool: ${action.name}`); console.log(`Arguments: ${JSON.stringify(action.args)}`); console.log(`Allowed:
```

---

## v1-C-017（multi-hop）

**问题**：JS LangGraph 的服务要优雅停机时，正在跑的节点会怎么处理，什么情况下会抛 GraphDrained？

**gold**：优雅停机时，正在执行的节点会跑到完，drain 到下一个 superstep 才生效；如果节点上有 retry policy 且正在重试，重试循环会跑完或耗尽后 drain 才生效。如果还剩 superstep，就会抛 GraphDrained(reason) ，此时 checkpoint 已保存、可以恢复。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

1. **正在执行的节点会先跑完，不会被打断。** 优雅停机（drain）只在**下一个 superstep 边界**生效：节点执行到一半会继续跑完；带重试策略且正在重试的节点，重试循环会跑到成功或耗尽后才生效 [9]。
2. **会抛 `GraphDrained` 的情况：** 当 drain 请求生效后**还有剩余的 superstep** 时，会抛出 `GraphDrained(reason)`，同时保存可恢复的 checkpoint，之后可用相同 config 恢复 [9][2]。
3. **不会抛 `GraphDrained` 的情况：** 如果图恰好在同一 tick 自然结束，则正常返回，需要检查 `control.drainRequested` 来区分是否发生过 drain 请求 [9]。
4. **子图请求 drain 时：** `GraphDrained` 会向上冒泡到父图，并在父图自己的下一个 superstep 边界停止它 [9]。
5. **JS 侧 API 名称：** 使用 `RunControl` 和 `GraphDrained`（从 `@langchain/langgraph` 导入），调用 `control.requestDrain("sigterm")`；捕获时用 `e instanceof GraphDrained`，原因在 `e.reason` [1][3]。注意：片段 [2] 是 Python changelog，写的是 `request_drain()`，与 JS 的 `requestDrain()` 存在命名差异，JS 以 [1][3] 为准。

最小可用示例（SIGTERM 钩子模式）[3]：

```javascript
import process from "node:process";
import { RunControl, GraphDrained } from "@langchain/langgraph";

const control = new RunControl();
process.on("SIGTERM", () => control.requestDrain("sigterm"));

try {
  const result = await graph.invoke(inputs, { ...config, control });
} catch (e) {
  if (e instanceof GraphDrained) {
    console.log(`graph drained: ${e.reason}`);
    // Resume on next startup with the same config
  } else {
    throw e;
  }
}
```

补充：drain 保存的 checkpoint 可恢复，恢复时不会重跑同一 superstep 中已成功的节点（pending writes 机制）[7][8]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__fault-tolerance#041` ｜ Fault tolerance ｜ Graceful shutdown

```text
```

import { RunControl, GraphDrained } from "@langchain/langgraph";



const control = new RunControl();



// In a signal handler or supervisor:

// control.requestDrain("sigterm");



try {

  const result = await graph.invoke(inputs, { ...config, control });

} catch (e) {

  if (e instanceof GraphDrained) {

    // The graph stopped early and saved a checkpoint.

    // Resume later with the same config.

    console.log(`Drained: ${e.reason}`);

  } else {

    throw e;

  }

}

```
```

片段[2] `oss__python__releases__changelog#033` ｜ Changelog ｜ langgraph v1.2.0

```text
- Graceful shutdown : Stop an in-flight run cooperatively after the current superstep completes, and save a resumable checkpoint. Create a RunControl and call request_drain() from any thread; the run raises GraphDrained and can be resumed later with the same config.
```

片段[3] `oss__javascript__langgraph__fault-tolerance#044` ｜ Fault tolerance ｜ Graceful shutdown > SIGTERM hook pattern

```text
```

import process from "node:process";

import { RunControl, GraphDrained } from "@langchain/langgraph";



const control = new RunControl();

process.on("SIGTERM", () => control.requestDrain("sigterm"));



try {

  const result = await graph.invoke(inputs, { ...config, control });

} catch (e) {

  if (e instanceof GraphDrained) {

    console.log(`graph drained: ${e.reason}`);

    // Resume on next startup with the same config

  } else {

    throw e;

  }

}

```
```

片段[4] `oss__python__langgraph__fault-tolerance#038` ｜ Fault tolerance ｜ Graceful shutdown

```text
```

from langgraph.runtime import RunControl

from langgraph.errors import GraphDrained



control = RunControl()



# In a signal handler or supervisor:

# control.request_drain("sigterm")



try:

    result = graph.invoke(inputs, config, control=control)

except GraphDrained as e:

    # The graph stopped early and saved a checkpoint.

    # Resume later with the same config.

    print(f"Drained: {e.reason}")

```
```

片段[5] `oss__python__langgraph__fault-tolerance#041` ｜ Fault tolerance ｜ Graceful shutdown > SIGTERM hook pattern

```text
```

import signal

from langgraph.runtime import RunControl

from langgraph.errors import GraphDrained



control = RunControl()

signal.signal(signal.SIGTERM, lambda *_: control.request_drain("sigterm"))



try:

    result = graph.invoke(inputs, config, control=control)

except GraphDrained as e:

    log.info("graph drained: %s", e.reason)

    # Resume on next startup with the same config

```
```

---

## v1-C-018（multi-hop）

**问题**：JS 里子图的持久化模式和把一段逻辑做成普通图节点，在 checkpoint 上有什么区别？

**gold**：子图按模式不同：checkpointer 传 true 时状态跨调用累积，传 false 时完全不 checkpoint、像普通函数调用，默认则继承父图的 checkpointer。把逻辑做成 Graph node 时，checkpoint 跟着它所在的 super-step 走，恢复从该节点开始，前面的节点不会重跑。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. **子图（Subgraph）在“有状态模式”下拥有自己的 checkpoint**，其节点会在父线程的某个 namespace 下做 checkpoint [8]。而**普通图节点里的普通函数没有自己的 checkpoint**，它运行在节点的 super-step 内，节点重跑时它就会重跑 [8]。

2. 子图的持久化模式由 `checkpointer=` 参数决定，共三种 [3]：
   - **Per-invocation（默认，`None`）**：每次调用都重新开始，但会继承父级的 checkpointer，以支持单次调用内的中断和持久执行 [3]。
   - **Per-thread（`True`）**：状态在同一线程的多次调用间累积，每次调用从上一次结束处继续 [3]。
   - **Stateless（`False`）**：完全不做 checkpoint，像普通函数调用一样，没有中断也没有持久执行 [3]。

3. **注意一个冲突点**：同一个子图实例在单个节点内被多次调用时，有状态持久化会让这些调用写入同一个 checkpoint namespace 而产生冲突，文档建议改用 per-invocation 持久化 [2]。而**不同的子图实例**在单个节点内被调用则不会有 namespace 冲突 [12]。

4. 补充：子图状态可通过 `get_state(config, subgraphs=True)` 查看，用于调试和监控 [11]。

**最小可用示例（JS，per-invocation 默认模式）：**

```javascript
import { createAgent, tool } from "langchain";
import { MemorySaver, Command, interrupt } from "@langchain/langgraph";
import * as z from "zod";

const fruitInfo = tool(
  (input) => `Info about ${input.fruitName}`,
  {
    name: "fruit_info",
    description: "Look up fruit info.",
    schema: z.object({ fruitName: z.string() }),
  }
);

// Subagents - no checkpointer setting (inherits parent)
const fruitAgent = createAgent({
  model: "gpt-5.4-mini",
  tools: [fruitInfo],
  systemPrompt: "You are a fruit expert.",
});
```

（示例摘自 [13]，展示了子图不设置 checkpointer 时继承父级、即 per-invocation 默认行为 [3][13]。）

**与用户说法的一致性说明**：片段中未出现“普通图节点”这一术语的独立定义，但 [8] 用 “Plain function inside a node” 描述该情形，并明确其 “Own checkpoint” 为 No；若你指的是把逻辑包成子图再作为节点使用，则属于 “Subgraph” 一行，有状态模式下 Own checkpoint 为 Yes [8]。

**top5 片段**：

片段[1] `oss__python__langgraph__use-subgraphs#041` ｜ Subgraphs ｜ View example trace > Checkpointer reference

```text
- Multiple calls (same subgraph) : The same subgraph instance can be invoked multiple times within a single node. With stateful persistence, these calls write to the same checkpoint namespace and conflict—use per-invocation persistence instead.
```

片段[2] `oss__javascript__langgraph__use-subgraphs#048` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
- Multiple calls (same subgraph) : The same subgraph instance can be invoked multiple times within a single node. With stateful persistence, these calls write to the same checkpoint namespace and conflict—use per-invocation persistence instead.
```

片段[3] `oss__javascript__langgraph__use-subgraphs#024` ｜ Subgraphs ｜ Subgraph persistence

```text
| Mode | checkpointer= | Behavior |

| --- | --- | --- |

| Per-invocation | None (default) | Each call starts fresh and inherits the parent’s checkpointer to support interrupts and durable execution within a single call. |

| Per-thread | True | State accumulates across calls on the same thread. Each call picks up where the last one left off. |

| Stateless | False | No checkpointing at all—runs like a plain function call. No interrupts or durable execution. |
```

片段[4] `oss__python__langgraph__use-subgraphs#020` ｜ Subgraphs ｜ Subgraph persistence

```text
| Mode | checkpointer= | Behavior |

| --- | --- | --- |

| Per-invocation | None (default) | Each call starts fresh and inherits the parent’s checkpointer to support interrupts and durable execution within a single call. |

| Per-thread | True | State accumulates across calls on the same thread. Each call picks up where the last one left off. |

| Stateless | False | No checkpointing at all—runs like a plain function call. No interrupts or durable execution. |
```

片段[5] `oss__python__langgraph__interrupts#000` ｜ Interrupts ｜ ROOT

```text
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
```

---

## v1-C-019（multi-hop）

**问题**：skills 这种多 Agent 模式里，单个 Agent 怎么保持控制权？skills 还能不能嵌套？

**gold**：skills 模式下不会把控制权交给别的 Agent：单个 Agent 始终在控制，只是按需加载 specialized prompts 和知识。而且 skills 可以在树状结构里定义其他 skills，形成 hierarchical skills，例如加载 data_science 这个 skill 会带出 pandas_expert、visualization、statistical_analysis 等子 skill，每个都能独立按需加载。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少：
- 关于「skills 多 Agent 模式下单个 Agent 如何保持控制权」的说明——片段 [5][6] 只提到 skills 模式「支持团队自治、不同团队可独立开发专用 skills」，没有涉及控制权归属或保持机制。
- 关于「skills 能否嵌套」的任何说明——所有片段均未提及嵌套（nesting）能力。

片段中与 skills 相关的内容仅包括：skill 未激活的排查（描述要具体、减少重叠、确认在 skills 数组中）[1][2][9][10][11][12]、skill 工具的门控机制（需先读 SKILL.md，否则调用失败；摘要丢弃该读取后工具不可用直至重读）[3][4][13][15]、只读 skill 的权限配置示例 [7][8]、以及向 skill 添加工具的中间件示例 [14][16]。这些都不足以回答控制权与嵌套的问题。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#121` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
2. Reduce overlap between skills. If multiple skills have similar descriptions, the agent may skip the right one or pick the wrong one. Differentiate descriptions or consolidate related skills .
```

片段[2] `oss__python__deepagents__skills#120` ｜ Skills ｜ Troubleshooting > Skill not activated

```text
2. Reduce overlap between skills. If multiple skills have similar descriptions, the agent may skip the right one or pick the wrong one. Differentiate descriptions or consolidate related skills .
```

片段[3] `oss__python__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[4] `oss__javascript__deepagents__skills#022` ｜ Skills ｜ Add tools to skills

```text
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
```

片段[5] `oss__python__langchain__multi-agent__skills-sql-assistant#001` ｜ Build a SQL assistant with on-demand skills ｜ How it works

```text
- Enables team autonomy - different teams can develop specialized skills independently (similar to other multi-agent architectures)
```

---

## v1-C-020（paraphrase）

**问题**：Agent 准备执行删库操作，我怎么让整条流程卡在这儿、等我点头之后才真的跑？

**gold**：在 interrupt 配置里用 descriptionPrefix 给出统一的中断提示文案，单个 tool 还能用自己的 description 覆盖它；要让流程真的停住还必须配 checkpointer。原文注明 Human-in-the-loop requires checkpointing to handle interrupts，生产环境要用 AsyncPostgresSaver 或 MongoDBSaver 这类 persistent checkpointer，而不是示例里的 MemorySaver。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：文档片段里能确认的做法是「Human-in-the-loop + checkpointer + thread_id」：Agent 会在执行敏感工具前暂停，等你用 `Command(resume=...)` 恢复，并且恢复时必须用同一个 `thread_id` [1][2]。但片段没有给出「专门针对删库/删除类工具」的配置示例，只给了「发送邮件」这类敏感工具的暂停示例 [1][2]，以及按工具名逐个决策的恢复写法（示例里对 `execute_sql` 选择 reject）[4]。

最小可用示例（Python，来自片段 [2] 的结构）：

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

JavaScript 版本同理，恢复时用 `new Command({ resume: { decisions: [{ type: "approve" }] } })`，并复用同一个 `thread_id` [1]。

补充说明与差异提示：
- 片段 [2] 的代码开头是 `ySaver(), )`，看起来是 `MemorySaver()`/`InMemorySaver()` 一类 checkpointer 的截断残片，片段本身没有完整展示 checkpointer 的创建语句；但片段 [3][5][7] 明确写了「pause and resume 需要 checkpointer」[3][5][7]。
- 如果你要按「每个工具调用单独审批」，片段 [4] 展示了按 interrupt id 组织 decisions 的写法，并可对特定工具（示例为 `execute_sql`）返回 `{ type: "reject", message: ... }` [4]。
- 片段 [7] 展示了 `interrupt_on` 按工具名开关中断的配置（`"write_file": True` 等），但这是 deepagents 的 `create_deep_agent` 用法，不是通用 LangChain agent 的参数 [7]。

缺口：给出的文档里没有找到「如何把某个具体删库工具标记为需要人工批准」的完整配置示例（例如在普通 `create_agent` 上指定工具级 interrupt 的写法），也没有删库场景的专门说明；需要补充这部分文档才能给出精确配置。

**top5 片段**：

片段[1] `oss__javascript__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
}); // Human-in-the-loop requires a thread ID for persistence const config = { configurable: { thread_id: "some_id" } }; // Agent will pause and wait for approval before executing sensitive tools let result = await agent.invoke( { messages: [{ role: "user", content: "Send an email to the team" }] }, config ); result = await agent.invoke( new Command({ resume: { decisions: [{ type: "approve" }] } }), config  // Same thread ID to resume the paused conversation ); ```
```

片段[2] `oss__python__langchain__guardrails#005` ｜ Guardrails ｜ Built-in guardrails > Human-in-the-loop

```text
ySaver(), ) # Human-in-the-loop requires a thread ID for persistence config = {"configurable": {"thread_id": "some_id"}} # Agent will pause and wait for approval before executing sensitive tools result = agent.invoke( {"messages": [{"role": "user", "content": "Send an email to the team"}]}, config=config ) result = agent.invoke( Command(resume={"decisions": [{"type": "approve"}]}), config=config  # Same thread ID to resume the paused conversation ) ```
```

片段[3] `oss__python__deepagents__human-in-the-loop#043` ｜ Human-in-the-loop ｜ Filesystem permission interrupts

```text
```

from deepagents import FilesystemPermission, create_deep_agent

from langgraph.checkpoint.memory import MemorySaver



agent = create_deep_agent(

    model=model,

    permissions=[

        FilesystemPermission(

            operations=["write"],

            paths=["/secrets/**"],

            mode="interrupt",

        ),

    ],

    checkpointer=MemorySaver(),  # Required to pause and resume

)

```
```

片段[4] `oss__javascript__langchain__human-in-the-loop#030` ｜ Human-in-the-loop ｜ Pause once per tool call > Resume each call by ID

```text
```

import { Command } from "@langchain/langgraph";



const decisions = Object.fromEntries(

  approvals.map((interrupt) => [

    interrupt.id,

    interrupt.value.name === "execute_sql"

      ? { type: "reject", message: "Archive the rows before deleting them." }

      : { type: "approve" },

  ]),

);



result = await agent.invoke(new Command({ resume: decisions }), config);

```
```

片段[5] `oss__python__deepagents__permissions#003` ｜ Permissions ｜ Pause for human approval

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

---

## v1-C-021（paraphrase）

**问题**：我想把对话退回三步之前的某个状态，从那儿改一句话再往下跑，SDK 里靠什么实现？

**gold**：用 getStateHistory() 拿到某个 checkpoint 的 snapshot，再调 await graph.invoke(null, snapshot.config)，它会基于那个 checkpoint 之后重新执行节点，这就是 replay history 的用法。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接回答「退回三步之前」这个具体步数操作的内容。片段里没有说明如何按“步数”定位历史状态，也没有提供按步数回退的 API。

不过，片段确实说明了“从某个历史检查点分叉并修改状态后继续运行”的机制，可以对应你描述的整体思路：

- 通过 `graph.getStateHistory(config)` 遍历历史状态，再用 `graph.updateState(...)` 修改某个历史检查点的状态，然后用 `graph.invoke(null, forkConfig)` 从该点继续执行 [1][8][9]。
- 分叉后如果遇到 interrupt，可以用 `new Command({ resume: ... })` 传入新的回答继续 [1][9]。
- 文档也把这类能力称为 Time travel：检查、导航并从对话历史中的任意检查点恢复 [7]。

最小示例（JavaScript，来自片段）：

```javascript
const states = [];
for await (const state of graph.getStateHistory(config)) {
  states.push(state);
}

// 选取某个历史检查点（片段示例是按 next 中包含的节点筛选，而非按“三步”）
const beforeAsk = states.filter((s) => s.next.includes("askHuman")).pop();

// 从该检查点分叉并修改状态
const forkConfig = await graph.updateState(beforeAsk.config, { value: ["forked"] });

// 从分叉点继续运行
const forkResult = await graph.invoke(null, forkConfig);

// 若停在 interrupt，可用新的回答恢复
await graph.invoke(new Command({ resume: "Bob" }), forkConfig);
```

需要说明的差异：你问的是“退回三步之前”，但片段中的定位方式是 `states.filter((s) => s.next.includes("askHuman")).pop()` 这类按节点/`next` 筛选 [1][8][9]，并没有出现按“步数”回退的参数或 API。因此“如何精确退回三步”在给出的文档里没有依据。

**top5 片段**：

片段[1] `oss__javascript__langgraph__use-time-travel#010` ｜ Use time-travel ｜ Interrupts

```text
StateHistory(config)) { states.push(state); } const beforeAsk = states.filter((s) => s.next.includes("askHuman")).pop(); const replayResult = await graph.invoke(null, beforeAsk.config); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Fork from before askHuman const forkConfig = await graph.updateState(beforeAsk.config, { value: ["forked"] }); const forkResult = await graph.invoke(null, forkConfig); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Resume the forked interrupt with a different answer await graph.invoke(new Command({ resume: "Bob" }), forkConfig); // Result: { value: ["forked", "Hello, Bob!", "Done"] } ```
```

片段[2] `oss__python__langchain__middleware__custom#037` ｜ Custom middleware ｜ Agent jumps

```text
```

from langchain.agents.middleware import AgentMiddleware, hook_config, AgentState

from langchain.messages import AIMessage

from langgraph.runtime import Runtime

from typing import Any



class BlockedContentMiddleware(AgentMiddleware):

    @hook_config(can_jump_to=["end"])

    def after_model(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None:

        last_message = state["messages"][-1]

        if "BLOCKED" in last_message.content:

            return {

                "messages": [AIMessage("I cannot respond to that request.")],

                "jump_to": "end"

            }

        return None

```
```

片段[3] `oss__python__langchain__context-engineering#018` ｜ Context engineering in agents ｜ Response Format > Messages

```text
- Use life-cycle hooks like before_model , after_model , or wrap_tool_call (for tool returns) to update the conversation history. See the middleware documentation for more details.
```

片段[4] `oss__python__langchain__middleware__custom#036` ｜ Custom middleware ｜ Agent jumps

```text
```

from langchain.agents.middleware import after_model, hook_config, AgentState

from langchain.messages import AIMessage

from langgraph.runtime import Runtime

from typing import Any



@after_model

@hook_config(can_jump_to=["end"])

def check_for_blocked(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:

    last_message = state["messages"][-1]

    if "BLOCKED" in last_message.content:

        return {

            "messages": [AIMessage("I cannot respond to that request.")],

            "jump_to": "end"

        }

    return None

```
```

片段[5] `oss__python__langchain__short-term-memory#038` ｜ Short-term memory ｜ Access memory > Before model

```text
window.""" messages = state["messages"] if len(messages) <= 3: return None  # No changes needed first_msg = messages[0] recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:] new_messages = [first_msg] + recent_messages return { "messages": [ RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages ] } agent = create_agent( "gpt-5-nano", tools=[], middleware=[trim_messages], checkpointer=InMemorySaver() ) config: RunnableConfig = {"configurable": {"thread_id": "1"}} agent.invoke({"messages": "hi, my name is bob"}, config) agent.invoke({"messages": "write a short poem about cats"}, config) agent.invoke({"messages": "now do the same but for dogs"}, config)
```

---

## v1-C-022（paraphrase）

**问题**：检索出来的段落老是半句话就断了、前后文接不上，调哪些参数比较对症？

**gold**：如果返回的片段缺上下文、答不出问题，就增大 chunk size 或 overlap；如果是相关概念被切到两个 chunk 里，就增加 overlap，或者按文档结构切分。反过来，返回的长 chunk 里塞满无关文本时应该减小 chunk size。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 检索结果“半句话断掉、前后文接不上”，文档建议**增大 overlap（重叠）**，或者改为按结构切分；如果同时觉得片段本身缺少回答所需的上下文，也可以增大 chunk size [1][2]。

具体对照文档里的调参表 [1][2]：

| 检索现象 | 调整方式 |
| --- | --- |
| 返回的片段缺少回答所需的上下文 | 增大 chunk size 或 overlap [1][2] |
| 返回的长片段被无关文本填充 | 减小 chunk size [1][2] |
| 把相关的想法切分到两个片段里 | **增大 overlap，或按结构切分** [1][2] |

你描述的“半句话断掉、前后文接不上”最贴近第三行（相关想法被切到两个 chunk），所以首选**增大 `chunk_overlap`**，其次考虑按结构切分 [1][2]。

另外文档提醒：大 chunk 虽然上下文更多，但 embedding 会把多个主题混在一起，更难匹配，且每个检索片段消耗更多 token [9][11]——所以不要一味调大 chunk size。

**最小可用示例（Python）：**

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,     # target chunk size (characters)
    chunk_overlap=200,   # overlap between adjacent chunks (characters)
)
chunks = splitter.split_documents(docs)
```
[8]

**最小可用示例（JavaScript）：**

```javascript
import { RecursiveCharacterTextSplitter } from "@langchain/textsplitters";

const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,    // target chunk size (characters)
  chunkOverlap: 200,  // overlap between adjacent chunks (characters)
});
const chunks = await splitter.splitDocuments(docs);
```
[10]

**参数名差异提示：** 文档中 Python 版参数是 `chunk_size` / `chunk_overlap` [8]，JavaScript 版是 `chunkSize` / `chunkOverlap` [10]，两者写法不同，注意不要混用。

**top5 片段**：

片段[1] `oss__python__langchain__chunking#003` ｜ Chunk documents for retrieval ｜ Balance chunk size and overlap

```text
| If retrieval | Adjust |

| --- | --- |

| Returns fragments that lack context to answer | Increase chunk size or overlap |

| Returns long chunks padded with irrelevant text | Decrease chunk size |

| Cuts related ideas across two chunks | Increase overlap, or split on structure |
```

片段[2] `oss__javascript__langchain__chunking#003` ｜ Chunk documents for retrieval ｜ Balance chunk size and overlap

```text
| If retrieval | Adjust |

| --- | --- |

| Returns fragments that lack context to answer | Increase chunk size or overlap |

| Returns long chunks padded with irrelevant text | Decrease chunk size |

| Cuts related ideas across two chunks | Increase overlap, or split on structure |
```

片段[3] `oss__python__deepagents__subagents#138` ｜ Subagents ｜ Troubleshooting > Context still getting bloated

```text
1. Instruct subagent to return concise results: system_prompt = """... IMPORTANT: Return only the essential summary. Do NOT include raw data, intermediate search results, or detailed tool outputs. Your response should be under 500 words."""
```

片段[4] `oss__javascript__deepagents__subagents#160` ｜ Subagents ｜ Troubleshooting > Context still getting bloated

```text
1. Instruct subagent to return concise results: const systemPrompt = `... IMPORTANT: Return only the essential summary. Do NOT include raw data, intermediate search results, or detailed tool outputs. Your response should be under 500 words.` ;
```

片段[5] `oss__python__langchain__frontend__integrations__openui#026` ｜ OpenUI ｜ Progressive rendering utilities

```text
^([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)?.[1]; const stripped = line.replace(/"(?:[^"\\]|\\.)*"/g, '""'); for (const v of defs) { if (v !== thisVar && new RegExp(`\\b${v}\\b`).test(stripped)) referenced.add(v); } } const topLevel = defs.filter((v) => !referenced.has(v)); const rootVars = topLevel.length > 0 ? topLevel : defs; return `${safe.trimEnd()}\nroot = Stack([${rootVars.join(", ")}], "column", "l")`; } /** * Gate Renderer updates to moments when at least one new *complete* statement * has arrived. This eliminates hundreds of no-op re-parses during streaming. * * Special case: TextContent lines update token-by-token (via closeOrTruncate)
```

---

## v1-C-023（paraphrase）

**问题**：做一个能打电话点三明治的语音助手，一次请求要经过哪几段处理？

**gold**：整条 pipeline 分三步：STT 把音频转给语音转文字供应商（例如 AssemblyAI）拿回 transcript；LangChain agent 处理 transcript 并流式输出回复 token；最后 TTS 把回复交给语音合成供应商（例如 Cartesia）拿回音频块。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答「一次请求要经过哪几段处理」的内容，缺少语音助手单次请求的端到端流程说明。

现有片段只能确认以下部分：

**结论：语音助手由三段流水线组成：STT → Agent → TTS。**

- 编排三段流水线：语音转文字（STT）把音频转发给 STT 提供商（如 AssemblyAI），接收转写事件；Agent 用 LangChain agent 处理转写文本并流式输出响应 token；文字转语音（TTS）把 agent 响应发给 TTS 提供商（如 Cartesia），接收音频块 [5][6]。

**最小可用示例（片段 [3] 中的 agent 构造部分）：**

```python
agent = create_agent(
    model="google_genai:gemini-4-hydrogen",  # Select your model
    tools=[add_to_order, confirm_order],
    system_prompt="""You are a helpful sandwich shop assistant. Your goal is to take the user's order. Be concise and friendly. Do NOT use emojis, special characters, or markdown. Your responses will be read by a text-to-speech engine.""",
    checkpointer=InMemorySaver(),
)
```

**需要指出的差异/缺口：**

- 片段 [3] 只给出了 `create_agent` 的构造和一个 `agent_stream` 函数的签名与 docstring（说明它把上游语音事件透传，并在处理 STT 转写时追加 `agent_chunk` 事件），但没有给出该函数的具体实现，因此无法据此还原「一次请求」内部各步骤的完整调用顺序 [3]。
- 片段 [5][6] 只描述了架构层面的三段流水线，没有说明单次通话请求的触发、事件流转与结束条件 [5][6]。

如果要回答完整流程，还需要：语音助手页面中 `agent_stream` 的完整实现代码，以及 STT/TTS 提供商接入与事件类型定义的相关片段。

**top5 片段**：

片段[1] `oss__python__langchain__multi-agent#014` ｜ Multi-agent ｜ Performance comparison > Summary

```text
| Pattern | One-shot | Repeat request | Multi-domain |

| --- | --- | --- | --- |

| Subagents | 4 calls | 8 calls (4+4) | 5 calls, 9K tokens |

| Handoffs | 3 calls | 5 calls (3+2) | 7+ calls, 14K+ tokens |

| Skills | 3 calls | 5 calls (3+2) | 3 calls, 15K tokens |

| Router | 3 calls | 6 calls (3+3) | 5 calls, 9K tokens |
```

片段[2] `oss__javascript__langchain__multi-agent#014` ｜ Multi-agent ｜ Performance comparison > Summary

```text
| Pattern | One-shot | Repeat request | Multi-domain |

| --- | --- | --- | --- |

| Subagents | 4 calls | 8 calls (4+4) | 5 calls, 9K tokens |

| Handoffs | 3 calls | 5 calls (3+2) | 7+ calls, 14K+ tokens |

| Skills | 3 calls | 5 calls (3+2) | 3 calls, 15K tokens |

| Router | 3 calls | 6 calls (3+3) | 5 calls, 9K tokens |
```

片段[3] `oss__python__langchain__voice-agent#006` ｜ Build a voice agent with LangChain ｜ 2. LangChain agent > Implementation

```text
agent = create_agent( model="google_genai:gemini-4-hydrogen",  # Select your model tools=[add_to_order, confirm_order], system_prompt="""You are a helpful sandwich shop assistant. Your goal is to take the user's order. Be concise and friendly. Do NOT use emojis, special characters, or markdown. Your responses will be read by a text-to-speech engine.""", checkpointer=InMemorySaver(), ) async def agent_stream( event_stream: AsyncIterator[VoiceAgentEvent], ) -> AsyncIterator[VoiceAgentEvent]: """ Transform stream: Voice Events → Voice Events (with Agent Responses) Passes through all upstream events and adds agent_chunk events when processing STT transcripts. """
```

片段[4] `oss__python__langchain__multi-agent#012` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- Turn 2: Router LLM call (1) → Milk agent calls buy_coffee (2) → Milk agent responds (3)
```

片段[5] `oss__python__langchain__voice-agent#000` ｜ Build a voice agent with LangChain ｜ Overview > Architecture

```text
- Orchestrates the three-step pipeline: Speech-to-text (STT) : Forwards audio to the STT provider (e.g., AssemblyAI), receives transcript events Agent : Processes transcripts with LangChain agent, streams response tokens Text-to-speech (TTS) : Sends agent responses to the TTS provider (e.g., Cartesia), receives audio chunks
```

---

## v1-C-024（no-answer）

**问题**：DSPy 的 BootstrapFewShot 优化器默认会编译几轮？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段只涉及 LangGraph 的节点默认配置（重试/超时/错误处理）[3][5]、子图与时间旅行[4]、evaluator-optimizer 工作流[7][8]、deepagents 深度研究中的委派轮次与并行子代理上限[1][2][10]，以及 MCP 协议弃用项[6]，没有任何关于 DSPy 或 `BootstrapFewShot` 优化器编译轮数的说明。

需要补充的是：DSPy `BootstrapFewShot` 的文档片段（尤其是其 `max_rounds` / `max_labeled_demos` 等参数说明及默认值）。另外提醒一点：片段中出现的「3 轮」是 deepagents 研究流程的委派轮次上限 [1][2]，与 DSPy 优化器无关，不要混淆。

**top5 片段**：

片段[1] `oss__python__deepagents__deep-research#016` ｜ Build a deep research agent ｜ Choose your path > Build the agent

```text
returns findings independently ## Research Limits - Stop after 3 delegation rounds if you haven't found adequate sources - Stop when you have sufficient information to answer comprehensively - Bias towards focused research over exhaustive exploration ```
```

片段[2] `oss__javascript__deepagents__deep-research#016` ｜ Build a deep research agent ｜ Choose your path > Build the agent

```text
returns findings independently ## Research Limits - Stop after 3 delegation rounds if you haven't found adequate sources - Stop when you have sufficient information to answer comprehensively - Bias towards focused research over exhaustive exploration ```
```

片段[3] `oss__javascript__langgraph__graph-api-nodes#018` ｜ Configure nodes ｜ Set graph-wide node defaults

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

片段[4] `oss__python__langgraph__use-time-travel#014` ｜ Use time-travel ｜ Subgraphs

```text
``` # Subgraph without its own checkpointer (default) subgraph = ( StateGraph(State) .add_node("step_a", step_a)       # Has interrupt() .add_node("step_b", step_b)       # Has interrupt() .add_edge(START, "step_a") .add_edge("step_a", "step_b") .compile()  # No checkpointer — inherits from parent ) graph = ( StateGraph(State) .add_node("subgraph_node", subgraph) .add_edge(START, "subgraph_node") .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Complete both interrupts graph.invoke({"value": []}, config)            # Hits step_a interrupt graph.invoke(Command(resume="Alice"), config)  # Hits step_b interrupt
```

片段[5] `oss__python__langgraph__graph-api-nodes#014` ｜ Configure nodes ｜ Set graph-wide node defaults

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

---

## v1-C-025（no-answer）

**问题**：LangChain JS SDK 的 createSupervisorAgent 是从哪个包导出的？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

缺少的信息：文档片段中没有出现 `createSupervisorAgent` 这个 API 名称，也没有说明它从哪个包导出。片段 [1] 和 [7] 只提到从 `langgraph-supervisor` 包迁移到 `create_agent` + 工具包装子代理的模式，其中出现的 API 是 `create_supervisor`（Python 风格）和 `create_agent`，与用户所说的 `createSupervisorAgent` 名称不一致，但片段并未给出该 JS API 的导出包信息，因此无法据此回答。

**top5 片段**：

片段[1] `oss__python__migrate__langgraph-supervisor#000` ｜ Migrate from langgraph-supervisor ｜ ROOT

```text
Migrate from langgraph-supervisor Migrate from the langgraph-supervisor package to the subagents pattern with create_agent and tool-wrapped subagents.
```

片段[2] `oss__javascript__deepagents__async-subagents#022` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
```

import { Client } from "@langchain/langgraph-sdk";

import type { LangGraphRunnableConfig } from "@langchain/langgraph";

import { createDeepAgent } from "deepagents";



async function findSubagentThreads(parentThreadId: string) {

  const client = new Client();

  return client.threads.search({ metadata: { parent_thread_id: parentThreadId } });

}



function researcher(config: LangGraphRunnableConfig) {

  // Set when a supervisor launched this run with `start_async_task`

  const parentThreadId = config.metadata?.parent_thread_id;

  return createDeepAgent({

    model: "google:gemini-4-hydrogen",

    systemPrompt: "You research topics thoroughly.",

  });

}

```
```

片段[3] `oss__javascript__deepagents__async-subagents#026` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
``` import { Client } from "@langchain/langgraph-sdk"; import type { LangGraphRunnableConfig } from "@langchain/langgraph"; import { createDeepAgent } from "deepagents"; async function findSubagentThreads(parentThreadId: string) { const client = new Client(); return client.threads.search({ metadata: { parent_thread_id: parentThreadId } }); } function researcher(config: LangGraphRunnableConfig) { // Set when a supervisor launched this run with `start_async_task` const parentThreadId = config.metadata?.parent_thread_id; return createDeepAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", systemPrompt: "You research topics thoroughly.", }); } ```
```

片段[4] `oss__javascript__deepagents__async-subagents#025` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
```

import { Client } from "@langchain/langgraph-sdk";

import type { LangGraphRunnableConfig } from "@langchain/langgraph";

import { createDeepAgent } from "deepagents";



async function findSubagentThreads(parentThreadId: string) {

  const client = new Client();

  return client.threads.search({ metadata: { parent_thread_id: parentThreadId } });

}



function researcher(config: LangGraphRunnableConfig) {

  // Set when a supervisor launched this run with `start_async_task`

  const parentThreadId = config.metadata?.parent_thread_id;

  return createDeepAgent({

    model: "openrouter:z-ai/glm-5.2",

    systemPrompt: "You research topics thoroughly.",

  });

}

```
```

片段[5] `oss__javascript__deepagents__async-subagents#023` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
```

import { Client } from "@langchain/langgraph-sdk";

import type { LangGraphRunnableConfig } from "@langchain/langgraph";

import { createDeepAgent } from "deepagents";



async function findSubagentThreads(parentThreadId: string) {

  const client = new Client();

  return client.threads.search({ metadata: { parent_thread_id: parentThreadId } });

}



function researcher(config: LangGraphRunnableConfig) {

  // Set when a supervisor launched this run with `start_async_task`

  const parentThreadId = config.metadata?.parent_thread_id;

  return createDeepAgent({

    model: "openai:gpt-6.1-sol",

    systemPrompt: "You research topics thoroughly.",

  });

}

```
```

---

## v1-D-001（single-hop）

**问题**：子 agent 没有单独配置 tools 的时候，会自动拿到主 agent 的工具吗？如果我自己传了 tools 呢？

**gold**：不传 tools 时，子 agent 默认从主 agent 继承工具。一旦显式指定 tools，就会完全覆盖掉继承来的那一套，不会两边合并，所以只放它真正需要的几个工具即可。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. 子 agent 没有单独配置 `tools` 时，**默认继承主 agent 的工具** [6]。
2. 如果自己传了 `tools`，则**完全覆盖**继承来的工具（不是合并）[6]。

需要注意：片段 [6] 是 JavaScript 版本文档，Python 版对应片段 [7] 只截到了 `tools` 字段的开头（`list[Callable]`），没有显示继承/覆盖的说明，因此上述结论以 [6] 为准。

**最小可用示例（JavaScript，依据 [6] 的字段说明）：**

```javascript
const subagent = {
  name: "researcher",
  description: "Researches a topic",
  // 不写 tools：默认继承主 agent 的工具
};

const subagentWithTools = {
  name: "researcher",
  description: "Researches a topic",
  // 写了 tools：完全覆盖继承的工具，只保留这里列出的
  tools: [mySearchTool],
};
```

**补充说明（片段中提到的相关差异）：**
- 只有 **general-purpose subagent** 会自动继承主 agent 的 skills [1][2]；自定义 subagent 不继承 skills，需要各自配置 `skills` 参数 [4][5][8][10]。
- 自定义 subagent 的 `middleware` 也是隔离的，isolated 模式不继承主 agent 的自定义 middleware [3]。

如果你问的是 Python 版 `tools` 的继承/覆盖行为，给出的文档片段里没有找到能回答这个问题的内容——[7] 只显示了 `tools` 的类型 `list[Callable]` 和「保持最小化」的建议，缺少继承与覆盖规则的描述。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#054` ｜ Skills ｜ Skills for subagents

```text
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.
```

片段[2] `oss__python__deepagents__skills#067` ｜ Skills ｜ Skills for subagents

```text
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.
```

片段[3] `oss__python__deepagents__subagents#005` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
) ). | | middleware | list[Middleware] | Optional. Additional middleware for custom behavior, logging, or rate limiting. Isolated subagents do not inherit the main agent’s custom middleware. For inheritance and overrides in fork mode, see Configure a forked subagent . Merged into the synchronous subagent stack : an instance whose .name matches a default replaces it in place, anything else lands after the last core middleware entry and before profile, prompt-caching, and memory. See Override a default middleware instance . For example, include a FilesystemMiddleware instance with a tools allowlist here to restrict the subagent’s filesystem tools independently of the main agent.
```

片段[4] `oss__python__deepagents__subagents#007` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
```

片段[5] `oss__javascript__deepagents__subagents#006` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
```

---

## v1-D-002（single-hop）

**问题**：子 agent 会继承主 agent 配的 skills 吗？它加载的 skill 会不会反过来影响主 agent？

**gold**：不会继承：skills 默认不从主 agent 继承，只有 general-purpose 这个子 agent 会继承主 agent 的 skills。子 agent 一旦有自己的 skills，会运行独立的 SkillsMiddleware 实例，状态完全隔离，子 agent 加载过的 skill 对父 agent 不可见，反之亦然。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. **自定义子 agent 默认不继承主 agent 的 skills。** 需要给每个子 agent 定义单独传 `skills` 参数来指定它自己的 skill 源路径 [3][4][5]。只有 **general-purpose 子 agent** 会自动继承主 agent 的 skills（当你在 `create_deep_agent` 里传了 `skills` 时），无需额外配置 [11]。

2. **子 agent 的 skill 状态是完全隔离的，不会反过来影响主 agent。** 子 agent 加载的 skills 对父 agent 不可见，反之亦然 [1][2]。当子 agent 配置了 skills 时，它会运行自己独立的 `SkillsMiddleware` 实例 [1][2]。

**最小可用示例（Python）：**

```python
from deepagents import create_deep_agent

research_subagent = {
    "name": "researcher",
    "description": "Research assistant with specialized skills",
    "system_prompt": "You are a researcher.",
    "tools": [web_search],
    "skills": ["/skills/researcher/"],  # 子 agent 专属 skills
}

agent = create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    skills=["/skills/main/"],          # 主 agent 和 GP 子 agent 用这些
    subagents=[research_subagent],     # researcher 只用它自己的 skills
)
```

**参数命名差异提示：** 片段中 Python 版参数名为 `skills`（`list[str]`）[2][9]，JavaScript 版为 `skills`（`string[]`）[1][7]；结构化输出参数 Python 是 `response_format` [2][8]，JavaScript 是 `responseFormat` [1][6]。若你的说法与这些不一致，以片段为准。

**top5 片段**：

片段[1] `oss__javascript__deepagents__subagents#006` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
```

片段[2] `oss__python__deepagents__subagents#007` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
```

片段[3] `oss__python__deepagents__skills#068` ｜ Skills ｜ Skills for subagents

```text
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
```

片段[4] `oss__javascript__deepagents__skills#055` ｜ Skills ｜ Skills for subagents

```text
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
```

片段[5] `oss__javascript__deepagents__skills#054` ｜ Skills ｜ Skills for subagents

```text
- General-purpose subagent : Automatically inherits skills from the main agent when you pass skills to create_deep_agent . No additional configuration is needed.
```

---

## v1-D-003（single-hop）

**问题**：deep agents 的 skill 是一次性整份读进上下文，还是分阶段加载的？每一级分别读什么？

**gold**：分三级按需加载：第一级是 SKILL.md frontmatter 里的 name 和 description，在 agent 启动时对所有已配置 skill 加载；第二级是完整的 SKILL.md 正文，在 skill 被调用时才读；第三级是 scripts/、references/、assets/ 里的支撑文件，只在正文用到它们时才读。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：是分阶段（渐进式）加载的，不是一次性整份读进上下文。** 共分三级：

1. **Discovery（第 1 级）**：agent 启动时，中间件扫描配置的 skill 路径，解析每个 `SKILL.md` 的 frontmatter，只把 `name` 和 `description` 字段注入系统提示词 [8][10]。
2. **Read（第 2 级）**：当 agent 调用某个 skill 时，才通过 `read_file` 读取完整的 `SKILL.md` 内容 [1][2]。
3. **Execute（第 3 级）**：调用之后，agent 按 skill 的指令执行，并且只在指令要求时才读取支撑文件（scripts、references、assets）[7][9]。

也就是说，启动时只加载名称和描述（轻量），命中后才读整份 `SKILL.md`，支撑文件再按需读取。

**最小示例（示意加载时机，非可运行代码）：**

```text
# 第 1 级：启动时注入系统提示词
- skill: pdf-processing
  description: Extract text and tables from PDF files

# 第 2 级：agent 判断相关并调用后
read_file(".../pdf-processing/SKILL.md")   # 读取完整内容

# 第 3 级：按 SKILL.md 指令按需读取
read_file(".../pdf-processing/scripts/extract.py")
```

**补充说明（与问题相关的差异点）：**
- 片段中该机制称为 “progressive disclosure”，Skills 的 Loading 一栏明确写着 “Read only when the agent determines relevance”，与 Memory（启动时加载）、Tools（每轮可用）不同 [3][4]。
- 片段 [14] 提到 `createSkillsMiddleware`，而片段 [12] 提到 `SkillsMiddleware`，两处命名不一致；若你按名称配置 skill，需以实际使用的中间件名为准 [12][14]。

**top5 片段**：

片段[1] `oss__python__deepagents__skills#008` ｜ Skills ｜ How skills work

```text
2. Read (level 2): When the agent invokes a skill, it reads the full SKILL.md content via read_file .
```

片段[2] `oss__javascript__deepagents__skills#008` ｜ Skills ｜ How skills work

```text
2. Read (level 2): When the agent invokes a skill, it reads the full SKILL.md content via read_file .
```

片段[3] `oss__python__deepagents__skills#134` ｜ Skills ｜ Reference > Skills, memory, and tools

```text
|  | Skills | Memory | Tools | | --- | --- | --- | --- | | Purpose | On-demand capabilities discovered through progressive disclosure | Persistent context loaded at startup | Programmatic actions the agent can call | | Loading | Read only when the agent determines relevance | Loaded at agent start | Available every turn | | Format | SKILL.md in named directories | AGENTS.md files | Functions bound to the agent | | Layering | User, then project (last wins) | User, then project (combined) | Defined at agent creation |
```

片段[4] `oss__javascript__deepagents__skills#134` ｜ Skills ｜ Reference > Skills, memory, and tools

```text
|  | Skills | Memory | Tools | | --- | --- | --- | --- | | Purpose | On-demand capabilities discovered through progressive disclosure | Persistent context loaded at startup | Programmatic actions the agent can call | | Loading | Read only when the agent determines relevance | Loaded at agent start | Available every turn | | Format | SKILL.md in named directories | AGENTS.md files | Functions bound to the agent | | Layering | User, then project (last wins) | User, then project (combined) | Defined at agent creation |
```

片段[5] `oss__python__deepagents__skills#076` ｜ Skills ｜ Skill permissions > Read-only skills

```text
``` from deepagents import FilesystemPermission, create_deep_agent from deepagents.backends import CompositeBackend, StateBackend, StoreBackend from langgraph.store.memory import InMemoryStore store = InMemoryStore()  # Good for local dev; omit for LangSmith Agent Server agent = create_deep_agent( model="ollama:north-mini-code-1.0", backend=CompositeBackend( default=StateBackend(), routes={ "/skills/": StoreBackend( namespace=lambda rt: ("curated-skills", rt.context.org_id), ), }, ), skills=["/skills/"], permissions=[ FilesystemPermission( operations=["write"], paths=["/skills/**"], mode="deny", ), ], store=store, ) ```
```

---

## v1-D-004（single-hop）

**问题**：为什么 deep agents 启动时只把 skill 的名字和描述放进 system prompt，而不是直接塞整份 skill 文件？

**gold**：这是刻意保持上下文精简的设计：skills 采用 on-demand loading，启动时只读 skill 描述，等某个 skill 和当前任务匹配了才读完整文件。文档的说法是这样能在真正需要某项能力之前一直让 context 保持精简。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接回答「为什么这样设计」的内容——片段只描述了「是什么/怎么做」，没有给出设计动机或理由的说明。

片段能确认的相关事实是：

- 启动时（Discovery，level 1）中间件会扫描配置的 skill 路径，解析每个 SKILL.md 的 frontmatter，只把 `name` 和 `description` 注入 system prompt [1][2]。
- 完整 SKILL.md 正文是在 agent 调用该 skill 时才通过 `read_file` 读取的（level 2）[9][11]。
- 分层加载表也印证：Level 1 元数据在 agent 启动时为每个已配置 skill 加载；Level 2 指令在 skill 被调用时加载；Level 3 资源在调用后按需加载 [10][12]。

也就是说，文档描述的是「渐进式披露（progressive disclosure）」的加载行为，但没有解释为何采用这种方式（例如上下文长度、按需加载等理由）。要回答「为什么」，需要文档中关于设计理念/动机的说明，而给出的片段里没有这部分内容。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#007` ｜ Skills ｜ How skills work

```text
1. Discovery (level 1): At agent start, the middleware scans the configured skill paths, parses each SKILL.md frontmatter , and injects the name and description fields into the system prompt.
```

片段[2] `oss__python__deepagents__skills#007` ｜ Skills ｜ How skills work

```text
1. Discovery (level 1): At agent start, the middleware scans the configured skill paths, parses each SKILL.md frontmatter , and injects the name and description fields into the system prompt.
```

片段[3] `oss__javascript__deepagents__skills#126` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
3. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
```

片段[4] `oss__python__deepagents__skills#126` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
4. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
```

片段[5] `oss__javascript__deepagents__acp#024` ｜ Agent Client Protocol (ACP) ｜ Customization > Skills and memory

```text
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
```

---

## v1-D-005（single-hop）

**问题**：ContextHubBackend 和 Sandbox 这两种 backend 各自解决什么问题？

**gold**：ContextHubBackend 把文件持久化存进 LangSmith Hub repo，好处是不需要另外开一个 LangGraph store。Sandbox backend 则是在隔离环境里执行代码，除了文件系统工具还额外提供 execute 工具来跑 shell 命令，LangSmith、AgentCore、Daytona 等都是可选的实现。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

- **ContextHubBackend**：解决的是「持久化存储」问题——把 agent 的文件（skills、memories 等需要长期保留的上下文）以 Hub commit 的形式存到 LangSmith Hub 仓库里，每次写入都有版本历史，并且不需要额外单独部署一个 LangGraph store [1][2]。
- **Sandbox**：解决的是「隔离执行」问题——在隔离环境中执行代码，提供文件系统工具以及用于运行 shell 命令的 `execute` 工具 [2][4]。

**最小可用示例**

ContextHubBackend（Python）[7]：

```python
from deepagents import create_deep_agent
from deepagents.backends import ContextHubBackend

agent = create_deep_agent(
    model="openai:gpt-6.1-sol",
    backend=ContextHubBackend("my-agent"),
)
```

Sandbox（片段中只给出构造方式，未给出完整可运行代码）[2]：

```python
agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox)
```

**补充说明**

- 片段里 Sandbox 的示例用的是 `backend=sandbox`，即传入一个已构建好的 sandbox 对象，而不是像 `ContextHubBackend("my-agent")` 那样直接实例化；具体可选集成包括 LangSmith、AgentCore、Daytona 等 [2]。
- 片段中未说明 ContextHubBackend 与 Sandbox 能否组合使用，也未给出 Sandbox 的完整初始化代码，这些内容在给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__python__releases__changelog#029` ｜ Changelog ｜ deepagents v0.6.0

```text
- ContextHubBackend ( blog ): A new filesystem backend backed by LangSmith Hub. Agent files — skills, memories, and other persisted context — are stored as Hub commits, giving you version history on every write and LangSmith-native durability without provisioning a separate LangGraph store.
```

片段[2] `oss__python__deepagents__backends#003` ｜ Backends ｜ Quickstart

```text
s is great for storing longer term memories or instructions that are applicable to the agent over multiple executions. | | Context Hub | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=ContextHubBackend("my-agent")) Stores files durably in a LangSmith Hub repo, without provisioning a separate LangGraph store. | | Sandbox | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox) Execute code in isolated environments. Sandboxes provide filesystem tools plus the execute tool for running shell commands. Choose from LangSmith, AgentCore, Daytona, or other sandbox integrations . |
```

片段[3] `oss__javascript__deepagents__backends#003` ｜ Backends ｜ Quickstart

```text
s is great for storing longer term memories or instructions that are applicable to the agent over multiple executions. | | Context Hub | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=ContextHubBackend("my-agent")) Stores files durably in a LangSmith Hub repo, without provisioning a separate LangGraph store. | | Sandbox | agent = create_deep_agent(model="google_genai:gemini-4-hydrogen", backend=sandbox) Execute code in isolated environments. Sandboxes provide filesystem tools plus the execute tool for running shell commands. Choose from LangSmith, AgentCore, Daytona, or other sandbox integrations . |
```

片段[4] `oss__python__deepagents__overview#020` ｜ Deep Agents overview ｜ Execution environment > Code execution

```text
- Sandbox backends expose an execute tool for shell commands in an isolated environment.
```

片段[5] `oss__python__deepagents__frontend__sandbox#045` ｜ Sandbox ｜ Best practices

```text
- Share sandbox resolution between the agent backend and the API server via thread metadata so both resolve the same environment with no in-memory caches.
```

---

## v1-D-006（single-hop）

**问题**：多轮对话里 thread_id 到底管什么？我想另起一个全新会话该怎么弄？

**gold**：thread_id 通过 config 里的 configurable 传入，是这段对话的稳定标识，checkpointer 用它持久化和恢复消息历史，所以后续轮次还能接上同一个会话。想开新对话就生成一个新的 thread_id。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. `thread_id` 是对话的稳定标识符，checkpointer 用它来持久化和恢复消息历史，因此后续轮次能继续同一段对话；要开启全新对话，就生成一个新的 `thread_id` [1][2]。
2. 在前端 `useStream` 场景下，"另起新会话"的做法是把 `threadId` 置为 `null`（例如点击 "New conversation" 按钮时），新 id 会通过 `onThreadId` 回调回填 [3][4]。

**最小可用示例（前端，Svelte 写法）：**

```ts
<script lang="ts">
  let threadId = $state<string | null>(null);

  const stream = useStream<typeof myAgent>({
    threadId: () => threadId,
    onThreadId: (id) => (threadId = id),
  });
</script>

<button onclick={() => (threadId = null)}>New conversation</button>
```

[3][4]

**补充说明（以片段为准的差异提示）：**

- 片段中 `thread_id` 的传参形式是 `config={"configurable": {"thread_id": ...}}`（Python 风格字典写法）[1][2]；而前端 `useStream` 里对应的是 `threadId` 选项（驼峰命名）[3][4]，两者命名风格不同，不要混用。
- 片段还提到 `context` 是"每次运行"的数据（如 user_id、API keys、feature flags、session metadata），通过 `context_schema` 定义、经 `runtime.context` 访问 [5][7]——它与 `thread_id` 的职责不同：`thread_id` 管会话历史的持久化与续接，`context` 管单次运行的数据。

**top5 片段**：

片段[1] `oss__javascript__deepagents__going-to-production#008` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- thread_id (passed via config={"configurable": {"thread_id": ...}} ): a stable identifier for the conversation. The checkpointer uses it to persist and resume message history, so follow-up turns continue the same conversation. Generate a new thread_id to start a fresh conversation.
```

片段[2] `oss__python__deepagents__going-to-production#008` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- thread_id (passed via config={"configurable": {"thread_id": ...}} ): a stable identifier for the conversation. The checkpointer uses it to persist and resume message history, so follow-up turns continue the same conversation. Generate a new thread_id to start a fresh conversation.
```

片段[3] `oss__python__langchain__frontend__message-queues#015` ｜ Message queues ｜ Starting a new thread

```text
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
```

片段[4] `oss__javascript__langchain__frontend__message-queues#015` ｜ Message queues ｜ Starting a new thread

```text
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
```

片段[5] `oss__python__langchain__frontend__message-queues#016` ｜ Message queues ｜ Starting a new thread

```text
```

threadId = signal<string | null>(null);

stream = injectStream<typeof myAgent>({

  threadId: this.threadId,

  onThreadId: (id) => this.threadId.set(id),

});



// In template:

// <button (click)="threadId.set(null)">New conversation</button>

```
```

---

## v1-D-007（single-hop）

**问题**：开启摘要压缩之后，之前对话里的图片还会留在上下文里吗？

**gold**：不会。Summarization 会把较早的消息压成纯文本摘要，落在这个范围内的 image、audio、video、file 块都不会被带过去，模型只能看到摘要里写的内容；低于 keep threshold 的近期消息不受影响。原始对话本身仍会以文本形式写到文件系统。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不会。** 摘要压缩会把较早的消息压成纯文本摘要，该范围内的图片、音频、视频和文件块不会被保留下来——模型只能看到摘要器对它们写下的文字描述 [1][2]。只有低于 keep 阈值的近期消息保持不变 [1][2]。

另外需要注意一个容易混淆的点：**offloading（上下文卸载）与摘要压缩的行为不同**。卸载只按文本 token 计量，非文本块（包括图片）会被保留在替换消息中，而不是被压缩；仅包含图片的消息不会仅因图片大小而被卸载 [6][8]。所以「图片是否消失」取决于触发的是摘要压缩还是卸载。

**最小示例（Python，摘要压缩后）：**

```python
# Before — 模型在较早轮次收到图片块
[
    HumanMessage(content=[
        {"type": "text", "text": "What trends do you see in this chart?"},
        {"type": "image", "base64": IMG, "mime_type": "image/png"},
    ]),
    ToolMessage(content=[
        {"type": "text", "text": "Updated chart:"},
        {"type": "image", "base64": IMG, "mime_type": "image/png"},
    ], tool_call_id="call_chart_1"),
    AIMessage(content="Revenue rose in Q3 based on the chart trend."),
    HumanMessage(content="Reply with one sentence summarizing our analysis."),
]

# After — 这些轮次折叠为文本；图片块已消失
{
    "content": (
        "User asked about trends in a chart screenshot. "
        "Tool returned an updated chart. Agent identified Q3 revenue growth."
    )
}
```

原始对话仍会以文本形式写入文件系统 [5][7]。关于触发条件、keep 阈值和完整流程，文档指向 Summarization 一节 [5][7]。

**top5 片段**：

片段[1] `oss__python__deepagents__multimodal#005` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: # Before — model receives image blocks in older turns [ HumanMessage ( content = [ { "type" : "text" , "text" : "What trends do you see in this chart?" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ] ), ToolMessage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" :
```

片段[2] `oss__javascript__deepagents__multimodal#005` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: // Before — model receives image blocks in older turns void { role : "user" , content : [ { type : "text" , text : "What trends do you see in this chart?" }, { type : "image" , url : "https://example.com/chart.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url :
```

片段[3] `oss__javascript__deepagents__multimodal#006` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url : "https://example.com/chart-v2.png" }, ] , }; // After — those turns collapse to text; image blocks are gone void { content : "User asked about trends in a chart screenshot. " + "Tool returned an updated chart. Agent identified Q3 revenue growth." , }; The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
```

片段[4] `oss__python__deepagents__multimodal#006` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
ssage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ], tool_call_id = "call_chart_1" , ), AIMessage ( content = "Revenue rose in Q3 based on the chart trend." ), HumanMessage ( content = "Reply with one sentence summarizing our analysis." ), ] # After — those turns collapse to text; image blocks are gone { "content" : ( "User asked about trends in a chart screenshot. " "Tool returned an updated chart. Agent identified Q3 revenue growth." )} The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
```

片段[5] `oss__python__deepagents__overview#023` ｜ Deep Agents overview ｜ Context management

```text
- Summarization and context offloading : automatic compression of conversation history and large tool results
```

---

## v1-D-008（single-hop）

**问题**：openwiki 支持哪些模型提供方？openai 和 bob 分别要配什么凭据？

**gold**：openai 用 OPENAI_API_KEY，另外可选 OPENAI_BASE_URL，用来指向暴露 Responses API 的 OpenAI 兼容网关；bob 用 BOB_API_KEY，可选 BOB_BASE_URL，它的模型 ID 是固定的 premium，没有 model picker。copilot 可以用 GitHub CLI session 或 COPILOT_API_KEY，但 CI 里必须用 OAuth token，不能用 classic PAT。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：** 文档列出的 OpenWiki 提供方包括 openai、openai-chatgpt、copilot、openrouter、anthropic、bob、gemini、gemini-enterprise、bedrock、baseten、fireworks、mistral、nebius、nvidia [1][8]。其中 openai 使用 `OPENAI_API_KEY`（可选 `OPENAI_BASE_URL`，用于暴露 Responses API 的 OpenAI 兼容网关）[1]；bob 使用 `BOB_API_KEY`（可选 `BOB_BASE_URL`，模型 ID 固定为 premium，无模型选择器）[1][8]。

**最小示例（环境变量）：**

```bash
# openai
OPENAI_API_KEY=your-openai-key
# 可选：OPENAI_BASE_URL=https://your-gateway.example.com

# bob
BOB_API_KEY=your-bob-key
# 可选：BOB_BASE_URL=https://your-bob-endpoint.example.com
```

**说明与差异提示：**
- 片段中 bob 的凭据写作 `BOB_API_KEY`，与 openai 的 `OPENAI_API_KEY` 命名不同，请按片段为准 [1][8]。
- 若使用 OpenAI 兼容网关，文档给出的配置方式是 `OPENWIKI_PROVIDER=openai-compatible` 配合 `OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_BASE_URL`、`OPENWIKI_MODEL_ID`，这与直接使用 `openai` 提供方是两套配置 [2]。

**top5 片段**：

片段[1] `oss__openwiki__providers#000` ｜ Model providers ｜ ROOT

```text
| Provider | Credential | Notes | | --- | --- | --- | | openai | OPENAI_API_KEY | Optional OPENAI_BASE_URL for OpenAI-compatible gateways that expose the Responses API | | openai-chatgpt | ChatGPT OAuth tokens | Sign in with ChatGPT; usage draws on Plus/Pro/Team Codex allowance | | copilot | GitHub CLI session or COPILOT_API_KEY | Optional COPILOT_BASE_URL . CI needs an OAuth token, not a classic PAT | | openrouter | OPENROUTER_API_KEY | Optional OPENWIKI_OPENROUTER_PROVIDER_ONLY allowlist | | anthropic | ANTHROPIC_API_KEY | Optional ANTHROPIC_BASE_URL | | bob | BOB_API_KEY | Optional BOB_BASE_URL . Fixed model ID premium ; no model picker | | gemini | GEMINI_API_KEY | Google AI Studio |
```

片段[2] `oss__openwiki__providers#017` ｜ Model providers ｜ OpenAI-compatible endpoints

```text
```

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-gateway-key

OPENAI_COMPATIBLE_BASE_URL=https://your-gateway.example.com/v1

OPENWIKI_MODEL_ID=your-gateway-model-name

```
```

片段[3] `oss__openwiki__providers#009` ｜ Model providers ｜ Microsoft Entra auth

```text
```

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_AUTH=entra-id

OPENAI_COMPATIBLE_BASE_URL=https://gateway.example.com/openai/v1

OPENAI_COMPATIBLE_ENTRA_SCOPE=api://gateway-application-id/.default

OPENWIKI_MODEL_ID=your-gateway-model

```
```

片段[4] `oss__openwiki__providers#019` ｜ Model providers ｜ OpenAI-compatible endpoints

```text
```

# Opper

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-opper-key

OPENAI_COMPATIBLE_BASE_URL=https://api.opper.ai/v3/compat

OPENWIKI_MODEL_ID=claude-sonnet-4-6

```
```

片段[5] `oss__openwiki__providers#018` ｜ Model providers ｜ OpenAI-compatible endpoints

```text
```

# Requesty

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_API_KEY=your-gateway-key

OPENAI_COMPATIBLE_BASE_URL=https://router.requesty.ai/v1

OPENWIKI_MODEL_ID=openai/gpt-6.1-sol

```
```

---

## v1-D-009（single-hop）

**问题**：openwiki 里不同 provider 能调的 reasoning effort 档位一样吗？这些档位最后落到请求的哪个字段上？

**gold**：不一样。openai 和 openai-chatgpt 下的 gpt-5.6-terra/luna/sol 支持 none、low、medium、high、xhigh、max，映射到 Responses API 的 reasoning.effort；nvidia 的 nemotron 只有 none、low、high，走 Chat Completions 的 reasoning_effort；gemini-4-hydrogen 只有 low、medium、high、xhigh，对应 Gemini 的 thinking level。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不一样。** 不同 provider 支持的档位集合不同，且映射到请求的字段也不同 [1][8]。

按片段 [1] 和 [8] 的表格：

| Provider | 支持档位 | 请求映射字段 |
|---|---|---|
| openai | none, low, medium, high, xhigh, max | Responses API `reasoning.effort` |
| openai-chatgpt | none, low, medium, high, xhigh, max | Responses API `reasoning.effort` |
| nvidia | none, low, high | Chat Completions `reasoning_effort` |
| gemini | low, medium, high, xhigh | Gemini thinking level |
| openai-compatible（启用时） | none, low, medium, high, xhigh, max | Responses API `reasoning.effort` 或 Chat Completions `reasoning_effort` |

要点：
- openai / openai-chatgpt / openai-compatible 档位最全（含 `none`、`max`）[1][8]。
- nvidia 只有 `none, low, high` 三档，且走 Chat Completions 的 `reasoning_effort` [1]。
- gemini 没有 `none` 和 `max`，只有 `low, medium, high, xhigh`，映射到 Gemini 的 thinking level [1]。
- 注意与 JS Google 集成文档的差异：片段 [3] 里 `reasoningEffort`/`thinkingLevel` 的取值是 `"minimal", "low", "medium", "high", "xhigh"`（含 `minimal`、不含 `none`/`max`），与 openwiki 表格 [1] 的 gemini 档位不完全一致，以各自文档为准 [1][3]。

CLI 里可用 `/effort` 设置，`/effort default` 恢复 provider 默认值 [2]。

最小示例（openwiki 环境变量方式，以 openai-compatible 为例）：

```bash
OPENWIKI_PROVIDER=openai-compatible
OPENAI_COMPATIBLE_API_KEY=your-gateway-key
OPENAI_COMPATIBLE_BASE_URL=https://router.requesty.ai/v1
OPENWIKI_MODEL_ID=openai/gpt-6.1-sol
```

（片段 [7] 只给了 provider 配置，未展示 effort 的具体环境变量名，故此处不臆造该变量。）

**top5 片段**：

片段[1] `oss__openwiki__providers#006` ｜ Model providers ｜ Reasoning effort

```text
| Provider | Model | Supported values | Request mapping | | --- | --- | --- | --- | | openai | gpt-5.6-terra , gpt-5.6-luna , gpt-5.6-sol | none , low , medium , high , xhigh , max | Responses API reasoning.effort | | openai-chatgpt | gpt-5.6-terra , gpt-5.6-luna , gpt-5.6-sol | none , low , medium , high , xhigh , max | Responses API reasoning.effort | | nvidia | nvidia/nemotron-3-super-120b-a12b | none , low , high | Chat Completions reasoning_effort | | gemini | gemini-4-hydrogen | low , medium , high , xhigh | Gemini thinking level |
```

片段[2] `oss__openwiki__cli-reference#011` ｜ Command reference ｜ Slash commands (interactive)

```text
- /effort : Set reasoning effort for supported OpenAI GPT-5.6, NVIDIA NIM, Gemini, and opted-in openai-compatible models, or /effort default to restore the provider default
```

片段[3] `oss__javascript__integrations__chat__google#029` ｜ ChatGoogle integration ｜ Reasoning / Thinking

```text
- reasoningEffort (or thinkingLevel ): Sets the relative effort. Values: "minimal" , "low" , "medium" , "high" , "xhigh" (supported on gemini-4-hydrogen and gemini-4-neon ; gemini-4-neon requires @langchain/google 0.2.16 or later).
```

片段[4] `oss__python__deepagents__models#007` ｜ Models ｜ Configure model parameters > Provider profiles

```text
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
```

片段[5] `oss__openwiki__providers#007` ｜ Model providers ｜ Reasoning effort

```text
Chat Completions reasoning_effort | | gemini | gemini-4-hydrogen | low , medium , high , xhigh | Gemini thinking level | | openai-compatible | Any model ID, when enabled | none , low , medium , high , xhigh , max | Responses API reasoning.effort or Chat Completions reasoning_effort |
```

---

## v1-D-010（single-hop）

**问题**：已经生成过 wiki 了，我再跑一次 --init 会把之前的全清空吗？--init 能和 --update 一起用吗？

**gold**：重跑 --init 会从零重新生成仓库 wiki，但会保留 openwiki/INSTRUCTIONS.md。--init 和 --update 不能组合使用。另外在 TTY 里不带 --print 时，它会流式打印 agent 输出并在成功后自动退出。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. 会重新生成：`--init` 会「from scratch」重新生成仓库 wiki，但会保留 `openwiki/INSTRUCTIONS.md` [1]。
2. 不能一起用：`--init` 和 `--update` 不能组合使用 [1]。

**最小可用示例**

```bash
# 重新生成（保留 openwiki/INSTRUCTIONS.md）
openwiki code --init

# 更新已有文档
openwiki code --update
```

**补充说明**

- `--init` 默认是 code mode [1]。
- 在 TTY 中不加 `--print` 时，会流式输出 agent 内容并在成功后自动退出 [1]。
- `openwiki/INSTRUCTIONS.md` 是用户编写的范围与优先级说明，OpenWiki 在 init 和 update 时读取它；正常的 `--init` 和 `--update` 运行不会重写它 [2]。

**top5 片段**：

片段[1] `oss__openwiki__cli-reference#002` ｜ Command reference ｜ Core commands > Common flags

```text
| Flag | Description | | --- | --- | | --init | Generate initial documentation. Defaults to code mode. Re-running regenerates the repository wiki from scratch while preserving openwiki/INSTRUCTIONS.md . In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | --update | Update existing documentation. Defaults to code mode. In a TTY without --print , streams agent output and exits automatically on success. --init and --update cannot be combined. | | -l , --language <locale> | Generate wiki documentation in the given BCP-47 locale, for example ko , zh-CN , or pt-BR . Unrecognized values are rejected. |
```

片段[2] `oss__openwiki__code-mode#003` ｜ Code mode ｜ What code mode produces

```text
- openwiki/INSTRUCTIONS.md : User-authored brief for scope and priorities. OpenWiki reads it on init and update. Edit it yourself, or ask OpenWiki in chat to change it; normal --init and --update runs do not rewrite it
```

片段[3] `oss__openwiki__code-mode#001` ｜ Code mode ｜ ROOT

```text
```

openwiki code --init

openwiki code --update

openwiki code --update --print

```
```

片段[4] `oss__openwiki__personal-mode#001` ｜ Personal mode ｜ ROOT

```text
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
```

片段[5] `oss__javascript__deepagents__async-subagents#017` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
- Update creates a new run on the same thread. By default it interrupts the previous run, and the subagent restarts with the full conversation history plus the new instructions. The task ID stays the same.
```

---

## v1-D-011（single-hop）

**问题**：personal mode 里接 custom-mcp 这类自定义 MCP 服务，openwiki 会把它所有工具都放开吗？

**gold**：不会。custom-mcp 源默认不需要凭据，可以连任意配置好的 HTTP 或 stdio MCP server，但只允许那些明确安全、只读的工具。相比之下 git-repo 源只读本地仓库路径并写出紧凑的 manifest。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不会全部放开。** custom-mcp 默认不需要凭据，连接任意已配置的 HTTP 或 stdio MCP 服务器，但**只允许明确标记为安全、只读的工具** [1]。

也就是说，openwiki 对 custom-mcp 的工具是白名单式限制（safe + read-only），不是把服务器上所有工具都暴露出来 [1]。

**最小可用示例（来自 CLI 参考）：**

```bash
# 列出 MCP 类 provider 的实时工具
openwiki auth tools <provider>

# 运行该 source 的 connector 摄取
openwiki ingest <source|source-instance|all>
```

[3]

**补充说明：**
- 片段里没有给出 custom-mcp 的具体配置字段或“如何把某个工具加入安全白名单”的方法，这部分内容缺失，无法从现有文档回答。
- 另外注意：片段 [4] 里的 `mcpToolset_20251120` / `mcp_servers` 是 **LangChain JS 的 Anthropic 集成**用法，不是 openwiki 的配置方式，两者不要混用 [4]。

**top5 片段**：

片段[1] `oss__openwiki__personal-mode#003` ｜ Personal mode ｜ Connect your sources > Built-in sources

```text
| Source | Credentials | Behavior | | --- | --- | --- | | custom-mcp | None required by default | Connects to any configured HTTP or stdio MCP server and permits only explicitly safe, read-only tools | | git-repo | Local paths | Reads configured local repository paths and writes compact manifests | | x | OAuth user-context credentials | Home timeline, user posts, mentions, bookmarks, and list posts via the X API | | notion | Notion OAuth (hosted MCP) | Authenticate through Notion OAuth instead of pasting a Notion token | | google | Gmail OAuth | Fetches recent mail via the Gmail API after openwiki auth gmail | | web-search | TAVILY_API_KEY | Uses Tavily through LangChain |
```

片段[2] `oss__openwiki__personal-mode#000` ｜ Personal mode ｜ ROOT

```text
Personal mode Build a local personal brain wiki from configured sources with OpenWiki.
```

片段[3] `oss__openwiki__cli-reference#007` ｜ Command reference ｜ Auth and connectors

```text
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
```

片段[4] `oss__openwiki__personal-mode#001` ｜ Personal mode ｜ ROOT

```text
```

openwiki personal

openwiki personal --init

openwiki personal --update

openwiki personal --update "Refresh the wiki from configured connectors"

```
```

片段[5] `oss__javascript__integrations__tools__anthropic#028` ｜ Anthropic integration ｜ MCP toolset

```text
```

import { ChatAnthropic, tools } from "@langchain/anthropic";



const llm = new ChatAnthropic({

  model: "claude-sonnet-4-6",

});



// Basic usage - enable all tools from an MCP server

const response = await llm.invoke("What tools do you have available?", {

  mcp_servers: [

    {

      type: "url",

      url: "https://example-server.modelcontextprotocol.io/sse",

      name: "example-mcp",

      authorization_token: "YOUR_TOKEN",

    },

  ],

  tools: [tools.mcpToolset_20251120({ serverName: "example-mcp" })],

});

```
```

---

## v1-D-012（single-hop）

**问题**：自己在本机跑开源 embedding 模型，跟调托管 API 比要付出什么代价？

**gold**：本地开源方案（BAAI/bge-*、Qwen/Qwen3-Embedding-*、sentence-transformers/all-* 这类）下载一次就能到处跑，没有按调用计费，数据也不离开自己的环境。代价是在小规模下 CPU 上大概率比托管 API 慢，有 GPU 才可能追平或更快。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：本机跑开源 embedding 模型的主要代价是**在小规模下 CPU 推理可能比托管 API 更慢**；换来的是无按次调用费用、数据不出本地环境 [1]。如果要在生产规模自托管，则需要通过 TEI 或 Ollama 之类的服务来补上水平扩展和 API 易用性 [2]。

具体权衡：
- 本地/开源：一次下载、随处运行，无按次调用成本，数据不离开你的环境；但小规模时 CPU 上很可能比托管 API 慢，有 GPU 时才有竞争力或更快 [1]。
- 托管旗舰（对照项）：一次 API 调用、开箱即用的最佳质量、无需本地基础设施；代价是按次计费和对数据出境的依赖 [9]。
- 生产级自托管：用 TEI 或 Ollama 提供同样的开源模型（基座或微调），获得本地推理的经济性，同时具备托管提供商的水平扩展和 API 易用性 [2]。

最小可用示例（本地开源模型，Python，经 HuggingFaceEmbeddings）：
```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
```

补充说明：片段中没有给出本地推理的具体硬件门槛、吞吐数字或成本对比数据，因此无法量化“慢多少”或“省多少”；如需这些，需要额外的基准测试文档。另外，片段 [1] 只列出了模型家族名称（如 BAAI/bge-*、Qwen/Qwen3-Embedding-* 等），并未给出具体的 LangChain 类名，上面的 `HuggingFaceEmbeddings` 仅由片段 [10] 提到“via HuggingFaceEmbeddings”间接支持，具体导入路径请以实际集成为准。

**top5 片段**：

片段[1] `oss__python__integrations__embeddings#007` ｜ Embedding model integrations ｜ Top integrations > Common deployment patterns

```text
2. Local, open-source: BAAI/bge-* , mixedbread-ai/mxbai-embed-* , Qwen/Qwen3-Embedding-* , nomic-ai/modernbert-embed-* , sentence-transformers/all-* . Download once, run anywhere. No per-call cost, data never leaves your environment. Likely slower on CPU than a hosted API at small scale; competitive or faster with a GPU.
```

片段[2] `oss__python__integrations__embeddings#009` ｜ Embedding model integrations ｜ Top integrations > Common deployment patterns

```text
4. Self-hosted at production scale: the same open models (base or fine-tuned) served via Text Embeddings Inference (TEI) or Ollama. Gives you the economics of local inference with the horizontal scaling and API ergonomics of a hosted provider.
```

片段[3] `oss__python__integrations__embeddings#006` ｜ Embedding model integrations ｜ Top integrations > Common deployment patterns

```text
1. Hosted, flagship: OpenAI text-embedding-3-large , Cohere embed-english-v3 , Google gemini-embedding-001 , Voyage voyage-3 . One API call, best-in-class quality out of the box, no local infrastructure. Per-call cost and a data-egress dependency.
```

片段[4] `oss__javascript__integrations__providers__microsoft#006` ｜ Microsoft integrations ｜ Text embedding models > Azure OpenAI

```text
```

import { AzureOpenAIEmbeddings } from "@langchain/openai";



const model = new AzureOpenAIEmbeddings({

  azureOpenAIApiKey: "<your_key>", // In Node.js defaults to process.env.AZURE_OPENAI_API_KEY

  azureOpenAIApiInstanceName: "<your_instance_name>", // In Node.js defaults to process.env.AZURE_OPENAI_API_INSTANCE_NAME

  azureOpenAIApiEmbeddingsDeploymentName: "<your_embeddings_deployment_name>", // In Node.js defaults to process.env.AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME

  azureOpenAIApiVersion: "<api_version>", // In Node.js defaults to process.env.AZURE_OPENAI_API_VERSION

});

```
```

片段[5] `oss__javascript__integrations__embeddings__openai#003` ｜ OpenAIEmbeddings integration ｜ Instantiation

```text
```

import { OpenAIEmbeddings } from "@langchain/openai";



const embeddings = new OpenAIEmbeddings({

  apiKey: "YOUR-API-KEY", // In Node.js defaults to process.env.OPENAI_API_KEY

  batchSize: 512, // Default value if omitted is 512. Max is 2048

  model: "text-embedding-3-large",

});

```
```

---

## v1-D-013（single-hop）

**问题**：供应商整体挂掉、或者 agent 陷入死循环疯狂调工具时，fault tolerance 文档分别建议加什么中间件？

**gold**：provider 整体不可用时用 modelFallbackMiddleware 自动回退到备选模型；调用次数失控（runaway loops）时用 ModelCallLimitMiddleware 和 ToolCallLimitMiddleware 限制每次运行的模型调用与工具调用。至于意料之外的错误，文档建议不加中间件，让异常直接冒泡。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- **供应商整体挂掉（Provider outage）**：文档建议自动回退到备用模型，使用 **`ModelFallbackMiddleware`**（Python 文档写作 `ModelFallbackMiddleware` [7]，JavaScript 文档写作 `modelFallbackMiddleware` [1][10]）。
- **Agent 陷入死循环、疯狂调用工具（Excessive calls / runaway loops）**：文档建议限制每次运行的模型调用和工具调用次数，使用 **`ModelCallLimitMiddleware`** 和 **`ToolCallLimitMiddleware`** [1][7]。

**注意 API 名称差异：** 你问的是"中间件"，片段中 Python 版用大驼峰 `ModelFallbackMiddleware`、`ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` [7]，JavaScript 版用小驼峰 `modelFallbackMiddleware` [1][10]。以片段为准，两种命名分别对应不同语言。

**最小可用示例（Python，来自片段 [8] 的写法风格，仅演示重试类中间件；回退/限流中间件片段未给出完整示例代码）：**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware
from langchain.tools import tool

@tool
def search(query: str) -> str:
    """Search for a query and return a short summary."""
    return f"Search results for: {query}"

agent = create_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    tools=[search],
    middleware=[
        ModelRetryMiddleware(max_retries=3),
        ToolRetryMiddleware(max_retries=2),
    ],
)
```

**补充说明：** 片段 [1][7][10] 只以表格形式列出了 `ModelFallbackMiddleware` / `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` 的用途，**没有给出这三个中间件的具体参数或完整代码示例**；片段 [8][9] 给出的是 `ModelRetryMiddleware` / `ToolRetryMiddleware` 的示例，属于"瞬时错误重试"场景，不是供应商宕机或死循环场景。若需要这三个中间件的具体用法，给出的文档里没有找到相应内容。

**top5 片段**：

片段[1] `oss__javascript__deepagents__fault-tolerance#002` ｜ Fault tolerance ｜ Error handling strategies

```text
man-in-the-loop | | Provider outage | System (automatic) | Fall back to an alternative model | modelFallbackMiddleware | | Excessive calls (runaway loops) | System (automatic) | Cap model and tool calls per run | ModelCallLimitMiddleware , ToolCallLimitMiddleware | | Unexpected errors | Developer | Let them bubble up | No middleware; let the exception propagate |
```

片段[2] `oss__python__langchain__middleware__built-in#007` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool error

```text
onError): return f"Tool `{request.tool_call['name']}` encountered a connection error." return None agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, database_tool], middleware=[ # Place retry inner so exceptions reach ToolErrorMiddleware after retries are exhausted ToolErrorMiddleware(on_error=on_error, tools=["search_tool"]), ToolRetryMiddleware(max_retries=3, on_failure="error"), ], ) # Async-only: pass aon_error alone (do not pass on_error) async_agent = create_agent( model="gpt-6.1-sol", tools=[api_tool], middleware=[ToolErrorMiddleware(aon_error=aon_error)], ) ```
```

片段[3] `oss__python__langchain__middleware__built-in#011` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool retry

```text
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
```

片段[4] `oss__javascript__langchain__middleware__built-in#006` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool retry

```text
``` import { createAgent, toolRetryMiddleware } from "langchain"; import { tool } from "@langchain/core/tools"; import { z } from "zod"; // Basic usage with default settings (2 retries, exponential backoff) const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, databaseTool], middleware: [toolRetryMiddleware()], }); // Retry specific exceptions only const retry = toolRetryMiddleware({ maxRetries: 4, retryOn: [TimeoutError, NetworkError], backoffFactor: 1.5, }); // Custom exception filtering function shouldRetry(error: Error): boolean { // Only retry on 5xx errors if (error.name === "HTTPError" && "statusCode" in error) { const statusCode = (error as any).statusCode;
```

片段[5] `oss__python__langgraph__checkpointers#004` ｜ Checkpointers ｜ Why use checkpointers

```text
- Fault-tolerance : Checkpointing provides fault-tolerance and error recovery: if one or more nodes fail at a given superstep, you can restart your graph from the last successful step.
```

---

## v1-D-014（multi-hop）

**问题**：同步子 agent 和异步子 agent 在跑到一半还能不能改这件事上差在哪？异步任务启动时又会带上哪些上下文？

**gold**：同步子 agent 任务进行中无法追加指令，也不能取消（除非把 supervisor 停掉），调用之间没有持久状态；异步子 agent 可以用 update_async_task 送后续指令、用 cancel_async_task 取消，并在自己的 thread 上跨交互保持状态。异步任务启动时会在 server 上新建一个 thread，isolated 模式只发任务描述，fork 模式额外带上父 agent 的对话历史，start_async_task 返回的 thread ID 就是任务 ID。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. **跑到一半能否修改（Mid-task updates）**：同步子 agent **不支持**中途更新；异步子 agent **支持**，可以通过 `update_async_task` 发送后续指令 [1][2][9][11]。
2. **异步任务启动时带哪些上下文**：给出的文档片段里**没有找到**关于异步任务启动时携带哪些上下文的内容。片段只提到异步子 agent 运行在服务器上自己的线程中、是有状态的（跨交互维护自身线程上的状态）[1][2][9][11]，以及主 agent 维护对话上下文、子 agent 每次都是全新开始 [6][7]，但没有说明启动时具体传入哪些上下文。缺的是「异步子 agent 启动参数/上下文传递」相关的说明。

**最小可用示例（基于片段中出现的 API 名称）：**

```text
# 异步子 agent 中途追加指令（片段中给出的 API 名称）
update_async_task(...)   # 发送 follow-up instructions

# 其他相关异步 API（片段中出现）
check_async_task(...)    # 非 Agent Server 场景下由 supervisor 轮询结果
cancel_async_task(...)   # 取消任务
```

**差异提示**：你问的是「启动时带哪些上下文」，但片段中只出现了 `update_async_task`、`check_async_task`、`cancel_async_task` 这几个异步相关 API，没有出现任何关于启动上下文的 API 或参数说明，因此这部分无法据片段回答 [1][2][9][11]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__async-subagents#001` ｜ Async subagents ｜ Compare sync and async subagents

```text
| Dimension | Sync subagents | Async subagents | | --- | --- | --- | | Execution model | Supervisor blocks until subagent completes | Returns a task ID immediately; supervisor continues | | Where it runs | Inside the supervisor’s run | On its own thread on a server (Agent Server or another Agent Protocol server) | | Concurrency | Parallel but blocking | Parallel and non-blocking | | Results | Returned as the tool result | On Agent Server, the subagent notifies the supervisor; otherwise the supervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task |
```

片段[2] `oss__python__deepagents__async-subagents#001` ｜ Async subagents ｜ Compare sync and async subagents

```text
| Dimension | Sync subagents | Async subagents | | --- | --- | --- | | Execution model | Supervisor blocks until subagent completes | Returns a task ID immediately; supervisor continues | | Where it runs | Inside the supervisor’s run | On its own thread on a server (Agent Server or another Agent Protocol server) | | Concurrency | Parallel but blocking | Parallel and non-blocking | | Results | Returned as the tool result | On Agent Server, the subagent notifies the supervisor; otherwise the supervisor calls check_async_task | | Mid-task updates | Not possible | Send follow-up instructions via update_async_task |
```

片段[3] `oss__javascript__langchain__multi-agent__subagents#033` ｜ Subagents ｜ Context engineering > Subagent specs > Tool-based discovery

```text
``` import { createAgent, tool } from "langchain"; import { z } from "zod"; const listAgents = tool( async ({ query = "" }) => { const agents = searchAgentRegistry(query); return formatAgentList(agents); }, { name: "list_agents", description: "List available subagents, optionally filtered by query.", schema: z.object({ query: z.string().optional() }), } ); const task = tool( async ({ agentName, description }) => { return `Delegated "${description}" to ${agentName}`; }, { name: "task", description: "Launch an ephemeral subagent for a task.", schema: z.object({ agentName: z.string(), description: z.string(), }), } ); const mainAgent = createAgent({ model:
```

片段[4] `oss__python__langchain__multi-agent__subagents#004` ｜ Subagents ｜ Sync vs. async

```text
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
```

片段[5] `oss__javascript__langchain__multi-agent__subagents#004` ｜ Subagents ｜ Sync vs. async

```text
| Mode | Main agent behavior | Best for | Tradeoff |

| --- | --- | --- | --- |

| Sync | Waits for subagent to complete | Main agent needs result to continue | Simple, but blocks the conversation |

| Async | Continues while subagent runs in background | Independent tasks, user shouldn’t wait | Responsive, but more complex |
```

---

## v1-D-015（multi-hop）

**问题**：能不能让某个子 agent 用一套和主 agent 完全不同的 skills？这些 skill 文件实际存在哪由什么决定？

**gold**：可以，给子 agent 传 skills（例如 /skills/research/、/skills/web-search/），它就从这些目录加载，不继承主 agent 的 skills，只有 general-purpose 子 agent 才继承主 agent 的 skills；它还会跑独立的 SkillsMiddleware，加载状态与父 agent 互相不可见。skills 属于 procedural memory，通过 skills= 传入，而文件究竟存在哪里、谁有权访问，由 backend 决定。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：可以。** 自定义子 agent 默认**不继承**主 agent 的 skills，需要在该子 agent 定义里用 `skills` 参数单独指定它自己的 skill 源路径，从而实现与主 agent 完全不同的 skill 集合 [3][4][5][6]。只有 general-purpose 子 agent 会继承主 agent 的 skills [1][2]。

关于「skill 文件实际存在哪由什么决定」：给出的文档片段只说明 `skills` 参数是「Skills source paths（技能源路径）」，即由你在子 agent 定义中传入的路径列表决定（例如 `["/skills/research/", "/skills/web-search/"]`，Python 侧示例为 `["/skills/researcher/"]`，是一个「其子目录即各个 skill」的容器）[1][2][8][10]。片段中**没有**进一步说明这些路径在物理文件系统/存储上的具体落盘位置或解析规则，因此这一点无法根据现有片段回答。

另外注意：子 agent 拥有 skills 时会运行自己独立的 `SkillsMiddleware` 实例，skill 状态完全隔离——子 agent 加载的 skills 对父 agent 不可见，反之亦然 [1][2]。

**最小可用示例（JavaScript，来自片段 [11]）：**

```javascript
import { createDeepAgent } from "deepagents";

const researchSubagent = {
  name: "researcher",
  description: "Research assistant with specialized skills",
  systemPrompt: "You are a researcher.",
  tools: [webSearch],
  skills: ["/skills/research/", "/skills/web-search/"], // Subagent-specific skills
};

const agent = await createDeepAgent({
  model: "google:gemini-4-hydrogen",
  skills: ["/skills/main/"], // Main agent and GP subagent get these
  subagents: [researchSubagent], // Researcher gets only its own skills
});
```

**参数命名差异提示：** 片段中该参数在 JavaScript 与 Python 文档里都叫 `skills`（类型分别为 `string[]` / `list[str]`）[8][10]，与问题中的说法一致，无冲突。

**top5 片段**：

片段[1] `oss__javascript__deepagents__subagents#006` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
n specified, the subagent will load skills from these directories (e.g., ["/skills/research/", "/skills/web-search/"] ). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | responseFormat | ResponseFormat | Optional. Structured output schema for the subagent. When set, the parent receives the subagent’s result as JSON instead of free-form text.
```

片段[2] `oss__python__deepagents__subagents#007` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
rom main agent by default. Subagent value overrides the default. | | skills | list[str] | Optional. Skills source paths. When specified, the subagent loads skills from these directories (for example, ["/skills/researcher/"] , a container whose subdirectories are skills). This allows subagents to have different skill sets than the main agent. Does not inherit from main agent. Only the general-purpose subagent inherits the main agent’s skills. When a subagent has skills, it runs its own independent SkillsMiddleware instance. Skill state is fully isolated—a subagent’s loaded skills are not visible to the parent, and vice versa. | | response_format | ResponseFormat | Optional.
```

片段[3] `oss__javascript__deepagents__skills#055` ｜ Skills ｜ Skills for subagents

```text
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
```

片段[4] `oss__python__deepagents__skills#068` ｜ Skills ｜ Skills for subagents

```text
- Custom subagents : Do not inherit the main agent’s skills. Add a skills parameter to each subagent definition with that subagent’s skill source paths.
```

片段[5] `oss__javascript__deepagents__subagents#112` ｜ Subagents ｜ Example > Skills inheritance

```text
- Custom subagents : Do NOT inherit skills by default—use the skills parameter to give them their own skills
```

---
