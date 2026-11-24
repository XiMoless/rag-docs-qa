### 51. v1-C-001 [single-hop] score=1.0
Q: JS 版 LangGraph 里给节点配 retryPolicy 时，默认最多尝试几次、第一次重试前等多久？
GOLD: 默认 maxAttempts 是 3，表示包含第一次在内的最多尝试次数；initialInterval 默认 500 毫秒，是第一次重试前的等待时间。backoffFactor 默认 2.0，按倍数放大每次重试的间隔，maxInterval 默认 128000 毫秒，jitter 默认 true 会给间隔加随机抖动。
ANSWER: 结论：JS 版 LangGraph 的 `retryPolicy` 默认 `maxAttempts` 为 3（含首次尝试），`initialInterval` 为 500 毫秒（第一次重试前的等待时间）[5]。

最小可用示例（沿用片段中的 JS 写法）：

```javascript
import { StateGraph, START } from "@langchain/langgraph";

const graph = new StateGraph(State)
  .setNodeDefaults({
    retryPolicy: { maxAttempts: 3 }, // 默认值即 3
  })
  .addNode("a", nodeA)
  .addNode("b", nodeB, { retryPolicy: { maxAttempts: 5 } }) // 覆盖默认
  .addEdge(START, "a")
  .compile();
```

补充说明（均来自 [5]）：
- `maxAttempts`：最大尝试次数，包含第一次，默认 3。
- `initialInterval`：第一次重试前的毫秒数，默认 500。
- 其他默认：`backoffFactor` 2.0、`maxInterval` 128000、`jitter` true。

注意：片段 [5] 是 JS 版 `retryPolicy` 的参数表；Python 版对应写法使用 `RetryPolicy(max_attempts=...)` [2][3][4]，参数命名风格不同（snake_case），请勿混用。
--- 片段[1] oss__javascript__langgraph__graph-api-nodes#018 ---
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
--- 片段[2] oss__python__langgraph__graph-api-nodes#014 ---
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
--- 片段[3] oss__python__langgraph__fault-tolerance#020 ---
```

from langgraph.types import RetryPolicy, TimeoutPolicy



builder.add_node(

    "call_model",

    call_model,

    timeout=TimeoutPolicy(idle_timeout=30),

    retry_policy=RetryPolicy(max_attempts=3),

)

```
--- 片段[4] oss__python__langgraph__fault-tolerance#032 ---
```

from langgraph.errors import NodeError

from langgraph.types import RetryPolicy, TimeoutPolicy

from langgraph.graph import StateGraph, START

from typing_extensions import TypedDict



class State(TypedDict):

    status: str



def default_error_handler(state: State, error: NodeError) -> State:

    return {"status": f"handled: {error.error}"}



graph = (

    StateGraph(State)

    .set_node_defaults(

        retry_policy=RetryPolicy(max_attempts=3),

        error_handler=default_error_handler,

        timeout=TimeoutPolicy(run_timeout=30),

    )

    .add_node("step_a", step_a)

    .add_node("step_b", step_b)

    .add_edge(START, "step_a")

    .compile()

)

```
--- 片段[5] oss__javascript__langgraph__fault-tolerance#005 ---
| Parameter | Type | Default | Description | | --- | --- | --- | --- | | maxAttempts | number | 3 | Maximum number of attempts, including the first. | | initialInterval | number | 500 | Milliseconds before the first retry. | | backoffFactor | number | 2.0 | Multiplier applied to the interval after each retry. | | maxInterval | number | 128000 | Maximum milliseconds between retries. | | jitter | boolean | true | Add random jitter to the interval. | | retryOn | (error: unknown) => boolean | built-in handler (when policy is set) | Callable returning true for retryable exceptions. Only used when retryPolicy is configured. |

### 52. v1-C-002 [single-hop] score=0.5
Q: JS 里把子图当工具调用时，checkpointer 传 false 会失去什么？
GOLD: 传 false 是 stateless 模式：子图完全不 checkpoint，像普通函数调用一样运行，因此没有 interrupts，也没有 durable execution。作为对比，传 true 是 per-thread 模式，状态会跨同一 thread 的多次调用累积；默认（None）则每次调用都全新开始，但会继承父图的 checkpointer，只为单次调用内的中断和 durable execution 服务。
ANSWER: 结论：在 JS 里把子图编译为无状态（`checkpointer: false`）后，会失去中断（HITL）、多轮记忆和状态查看能力；但多次调用（不同子图或同一子图）仍然可用 [5]。

具体对照表（Stateless 列）[5]：
- Interrupts (HITL)：❌ 不支持
- Multi-turn memory：❌ 不支持
- Multiple calls (different subgraphs)：✅ 支持
- Multiple calls (same subgraph)：✅ 支持
- State inspection：❌ 不支持

另外注意 API 写法差异：JS 里是 `builder.compile({ checkpointer: false })`，传的是对象参数 [2][3]；Python 里是 `compile(checkpointer=False)` 关键字参数 [1]。你问题里说的「checkpointer 传 false」在 JS 中应写成 `{ checkpointer: false }`。

最小可用示例（JS）：

```javascript
const subgraphBuilder = new StateGraph(...);

const subgraph = subgraphBuilder.compile({ checkpointer: false });
```

补充：片段 [2] 还提到该参数可以是 `false`、`true` 或 `null` [2]，但片段未进一步说明 `null` 的具体语义。
--- 片段[1] oss__python__langgraph__use-subgraphs#036 ---
```

subgraph_builder = StateGraph(...)

subgraph = subgraph_builder.compile(checkpointer=False)

```
--- 片段[2] oss__javascript__langgraph__use-subgraphs#043 ---
```

const subgraph = builder.compile({ checkpointer: false });  // or true, or null

```
--- 片段[3] oss__javascript__langgraph__use-subgraphs#042 ---
```

const subgraphBuilder = new StateGraph(...);

const subgraph = subgraphBuilder.compile({ checkpointer: false });

```
--- 片段[4] oss__python__langgraph__use-subgraphs#037 ---
| Feature | Per-invocation (default) | Per-thread | Stateless |

| --- | --- | --- | --- |

| checkpointer= | None | True | False |

| Interrupts (HITL) | ✅ | ✅ | ❌ |

| Multi-turn memory | ❌ | ✅ | ❌ |

| Multiple calls (different subgraphs) | ✅ |  | ✅ |

| Multiple calls (same subgraph) | ✅ | ❌ | ✅ |

| State inspection |  | ✅ | ❌ |
--- 片段[5] oss__javascript__langgraph__use-subgraphs#044 ---
| Feature | Per-invocation (default) | Per-thread | Stateless |

| --- | --- | --- | --- |

| checkpointer= | None | True | False |

| Interrupts (HITL) | ✅ | ✅ | ❌ |

| Multi-turn memory | ❌ | ✅ | ❌ |

| Multiple calls (different subgraphs) | ✅ |  | ✅ |

| Multiple calls (same subgraph) | ✅ | ❌ | ✅ |

| State inspection |  | ✅ | ❌ |

### 53. v1-C-003 [single-hop] score=0.5
Q: JS 里图跑到一半报错，想从最近一次检查点接着跑、不要重新提交输入，graph.invoke 该怎么传？
GOLD: 调 await graph.invoke(null, config)：它会加载最新的 checkpoint 并重试没做完的工作，而且不要传 checkpoint_id。如果要回应中断，则改成 await graph.invoke(new Command({ resume: answer }), config)，answer 会成为该 interrupt 的返回值。
ANSWER: 结论：在 JS 里从最近一次检查点继续执行（不重新提交输入），应调用 `await graph.invoke(null, config)`，并省略 `checkpoint_id` [3]。

最小可用示例：

```javascript
// 继续执行：加载最新检查点并重试未完成的工作
await graph.invoke(null, config);
```

补充说明：
- 片段 [3] 明确写的是 `await graph.invoke(null, config)`，用于「Continue after an error」，执行语义是「Loads the latest checkpoint and retries unfinished work. Omit checkpoint_id.」[3]。
- 注意与「提交新输入」区分：提交新输入应传 `input`，即 `await graph.invoke(input, config)`，它会从入口点重新开始 [3]。
- 另外，片段 [1] 中恢复图用的是 `await graph.invoke(null, config)`，与 [3] 的写法一致 [1][3]。
--- 片段[1] oss__javascript__langgraph__interrupts#080 ---
```

// Run the graph until the breakpoint

graph.invoke(inputs, {

    interruptBefore: ["node_a"],

    interruptAfter: ["node_b", "node_c"],

    configurable: {

        thread_id: "some_thread"

    }

});



// Resume the graph

await graph.invoke(null, config);

```
--- 片段[2] oss__python__langgraph__checkpointers#006 ---
| Goal | Invocation | Execution |

| --- | --- | --- |

| Submit new input | graph.invoke(input, config) | Applies the input to saved state and starts from the entry point. |

| Continue after an error | graph.invoke(None, config) | Loads the latest checkpoint and retries unfinished work. Omit checkpoint_id . |

| Answer an interrupt() | graph.invoke(Command(resume=answer), config) | Supplies the interrupt’s return value. The interrupted node starts again from its beginning. |

| Replay history | graph.invoke(None, snapshot.config) | Uses a snapshot from get_state_history() and re-executes nodes after that checkpoint. |
--- 片段[3] oss__javascript__langgraph__checkpointers#006 ---
| Goal | Invocation | Execution |

| --- | --- | --- |

| Submit new input | await graph.invoke(input, config) | Applies the input to saved state and starts from the entry point. |

| Continue after an error | await graph.invoke(null, config) | Loads the latest checkpoint and retries unfinished work. Omit checkpoint_id . |

| Answer an interrupt() | await graph.invoke(new Command({ resume: answer }), config) | Supplies the interrupt’s return value. The interrupted node starts again from its beginning. |

| Replay history | await graph.invoke(null, snapshot.config) | Uses a snapshot from getStateHistory() and re-executes nodes after that checkpoint. |
--- 片段[4] oss__python__langgraph__graph-api#017 ---
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
--- 片段[5] oss__javascript__langgraph__graph-api#023 ---
```

// Wrong: resumes from the latest checkpoint

await graph.invoke(new Command({ update: { messages: [{ role: "user", content: "follow up" }] } }), config);



// Correct: plain object restarts from START

await graph.invoke({ messages: [{ role: "user", content: "follow up" }] }, config);

```

### 54. v1-C-004 [single-hop] score=0.5
Q: JS 的 streamMode 里 updates 和 values 有什么区别？
GOLD: values 在每一步之后给出完整的状态；updates 给出每一步之后的状态更新，而且同一步里的多个更新会被分别流式发出。
ANSWER: 给出的文档里没有找到能直接回答「JS 的 streamMode 里 updates 和 values 有什么区别」的完整内容。

现有片段能确认的部分：

- `updates` 模式表示「每一步之后的状态更新」，同一 step 内的多个更新会分别流式输出 [2]。
- `values` 模式表示「每一步之后的完整状态快照」[2]。
- 在 Python 的 v2 流式格式中，`values` 对应 `ValuesStreamPart`，`updates` 对应 `UpdatesStreamPart` [1]。
- JS 侧片段只展示了 `streamMode: "updates"` 的用法，没有展示 `values` 的 JS 示例 [4][5]。

缺少的内容：文档片段里没有 JS 版 `values` 模式的示例或说明，也没有专门对比 JS 下 `updates` 与 `values` 的差异。因此无法仅凭这些片段给出 JS 侧的完整区别说明。

最小可用示例（仅 `updates`，来自 JS 片段 [4]）：

```js
const stream = await graph.stream(
  { topic: "animals" },
  { streamMode: "updates" }
);

for await (const chunk of stream) {
  console.log(chunk);
}
```
--- 片段[1] oss__python__langgraph__streaming#008 ---
``` for part in graph.stream( {"topic": "ice cream"}, stream_mode=["values", "updates", "messages", "custom"], version="v2", ): if part["type"] == "values": # ValuesStreamPart — full state snapshot after each step print(f"State: topic={part['data']['topic']}") elif part["type"] == "updates": # UpdatesStreamPart — only the changed keys from each node for node_name, state in part["data"].items(): print(f"Node `{node_name}` updated: {state}") elif part["type"] == "messages": # MessagesStreamPart — (message_chunk, metadata) from LLM calls msg, metadata = part["data"] print(msg.content, end="", flush=True) elif part["type"] == "custom": # CustomStreamPart — arbitrary data from get_stream_writer()
--- 片段[2] oss__python__langgraph__streaming#010 ---
| Mode | Type | Description | | --- | --- | --- | | values | ValuesStreamPart | Full state after each step. | | updates | UpdatesStreamPart | State updates after each step. Multiple updates in the same step are streamed separately. | | messages | MessagesStreamPart | 2-tuples of (LLM token, metadata) from LLM calls. | | custom | CustomStreamPart | Custom data emitted from nodes via get_stream_writer . | | checkpoints | CheckpointStreamPart | Checkpoint events (same format as get_state() ). Requires a checkpointer. | | tasks | TasksStreamPart | Task start/finish events with results and errors. Requires a checkpointer. |
--- 片段[3] oss__python__langgraph__streaming#013 ---
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
--- 片段[4] oss__javascript__langgraph__graph-api-send-command#005 ---
```

const stream = await graph.stream(

  { topic: "animals" },

  { streamMode: "updates" }

);

for await (const chunk of stream) {

  console.log(chunk);

}

```
--- 片段[5] oss__javascript__langgraph__graph-api-nodes#028 ---
ART, "expensive_node") .addEdge("expensive_node", END) .compile({ cache: new InMemoryCache() }); await graph.invoke({ x: 5 }, { streamMode: "updates" }); // [{"expensive_node": {"result": 10}}] await graph.invoke({ x: 5 }, { streamMode: "updates" }); // [{"expensive_node": {"result": 10}, "__metadata__": {"cached": true}}] ```

### 55. v1-C-005 [single-hop] score=1.0
Q: JS 的 createAgent 里 responseFormat 能直接接受哪几种 schema？
GOLD: 可以接 ZodSchema，也可以接任何 Standard Schema 库的 schema，或者用 Record<string, unknown> 表示的 JSON Schema；responseFormat 还能写成这几种的数组。
ANSWER: 结论：在 JS 的 `createAgent` 里，`responseFormat` 可以直接接受三种 schema 形式：Zod schema、任意 Standard Schema 库的 schema、JSON Schema（以 `Record<string, unknown>` 表示）；此外 `responseFormat` 还支持传入单个或数组形式 [1]。

最小可用示例（依据片段 [1] 的类型定义）：

```ts
type ResponseFormat = (
  | ZodSchema<StructuredResponseT>        // a Zod schema
  | StandardSchema<StructuredResponseT>   // any Standard Schema library
  | Record<string, unknown>               // a JSON Schema
)

const agent = createAgent({
  // ...
  responseFormat: ResponseFormat | ResponseFormat[]
})
```

补充说明：片段 [3] 展示了用 `toolStrategy(OutputSchema)` 包装 Zod schema 后传给 `responseFormat` 的用法，这属于对 schema 的进一步策略包装，而非 `responseFormat` 直接接受的原始 schema 类型 [3]。
--- 片段[1] oss__javascript__langchain__structured-output#000 ---
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
--- 片段[2] oss__javascript__langchain__frontend__integrations__copilotkit#012 ---
``` import { createAgent, createMiddleware, toolStrategy } from "langchain"; import { z } from "zod"; import { deepSearchTool, searchWebTool } from "../tools/index.js"; const contextSchema = z.object({ output_schema: z.unknown().optional(), }); const structuredOutputMiddleware = createMiddleware({ name: "CopilotKitStructuredOutput", contextSchema, wrapModelCall: async (request, handler) => { const rawOutputSchema = getRuntimeOutputSchema(request.runtime); const schema = normalizeOutputSchema(rawOutputSchema); if (!schema) { return handler(request); } const responseFormat = toolStrategy( schema as unknown as Parameters<typeof toolStrategy>[0], { toolMessageContent:
--- 片段[3] oss__javascript__migrate__langchain-v1#024 ---
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
--- 片段[4] oss__javascript__deepagents__customization#009 ---
gents stack | | interruptOn | Pause before tool calls for human approval | | responseFormat | Structured output schema | | contextSchema | Per-run runtime context schema (user IDs, API keys, feature flags) |
--- 片段[5] oss__python__migrate__langchain-v1#036 ---
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

### 56. v1-C-006 [single-hop] score=1.0
Q: JS 里断言 Agent 输出时，怎么检查一条消息是不是 AIMessage、以及它带的 tool calls 对不对？
GOLD: 用 toBeAIMessage(expected?) 检查这个值是不是 AIMessage，还可以顺带匹配 content 或字段；用 toHaveToolCalls(expected) 检查 AIMessage 是否恰好带有给定的 tool calls，且与顺序无关。如果要核对工具结果消息，toBeToolMessage 还能匹配 tool_call_id。
ANSWER: 结论：在 JS 集成测试里，可以用自定义 matcher 检查消息类型和 tool calls。判断是否为 AIMessage 用 `toBeAIMessage()` [3]；检查 tool calls 有 `toHaveToolCalls(expected)`（精确匹配、顺序无关）、`toHaveToolCallCount(n)`（数量）、`toContainToolCall(expected)`（至少一个匹配，支持 `.not`）[1][2][3]。

注意：`toHaveToolCalls` 在片段 [2] 和 [3] 中的描述都是「exactly the given tool calls（order-independent）」，即精确匹配而非包含匹配；若只想验证存在某个调用，应使用 `toContainToolCall` [1][2]。

最小可用示例（来自片段 [1]）：

```javascript
const response = await agent.invoke({
  messages: [new HumanMessage("Weather in SF and NYC?")]
});

const aiMsg = response.messages.find(
  (m) => AIMessage.isInstance(m) && m.tool_calls?.length
);

// 精确匹配（顺序无关）
expect(aiMsg).toHaveToolCalls([
  { name: "get_weather", args: { city: "San Francisco" } },
  { name: "get_weather", args: { city: "New York" } },
]);

// 只检查数量
expect(aiMsg).toHaveToolCallCount(2);

// 至少一个匹配（支持 .not）
expect(aiMsg).toContainToolCall({ name: "get_weather" });
expect(aiMsg).not.toContainToolCall({ name: "send_email" });
```

补充：片段 [3] 还提供了 `toBeAIMessage(expected?)`，可选择性匹配 content 或字段 [3]。片段 [4][5] 是 Python 流式示例，与 JS 断言问题无关。
--- 片段[1] oss__javascript__langchain__test__integration-testing#010 ---
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
--- 片段[2] oss__javascript__langchain__test__integration-testing#015 ---
all_id . | | toHaveToolCalls(expected) | Check that an AIMessage has exactly the given tool calls (order-independent). | | toHaveToolCallCount(n) | Check that an AIMessage has exactly n tool calls. | | toContainToolCall(expected) | Check that an AIMessage contains at least one matching tool call. Supports .not . | | toHaveToolMessages(expected) | Check that a message array contains the given ToolMessage instances, in order. | | toHaveBeenInterrupted(value?) | Check that a result has an __interrupt__ . Optionally match the interrupt value. | | toHaveStructuredResponse(expected?) | Check that a result has a structuredResponse . Optionally match specific fields. |
--- 片段[3] oss__javascript__langchain__test__integration-testing#014 ---
| Matcher | Description | | --- | --- | | toBeHumanMessage(expected?) | Check that the value is a HumanMessage . Optionally match content (string) or fields (object). | | toBeAIMessage(expected?) | Check that the value is an AIMessage . Optionally match content or fields. | | toBeSystemMessage(expected?) | Check that the value is a SystemMessage . Optionally match content or fields. | | toBeToolMessage(expected?) | Check that the value is a ToolMessage . Optionally match content or fields like tool_call_id . | | toHaveToolCalls(expected) | Check that an AIMessage has exactly the given tool calls (order-independent). |
--- 片段[4] oss__python__langchain__streaming#044 ---
nyMessage) -> None: if isinstance(message, AIMessage) and message.tool_calls: print(f"Tool calls: {message.tool_calls}") if isinstance(message, ToolMessage): print(f"Tool response: {message.content_blocks}") input_message = {"role": "user", "content": "What is the weather in Boston?"} for chunk in agent.stream( {"messages": [input_message]}, stream_mode=["messages", "updates", "custom"], version="v2", ): if chunk["type"] == "messages": token, metadata = chunk["data"] if isinstance(token, AIMessageChunk): _render_message_chunk(token) elif chunk["type"] == "updates": for source, update in chunk["data"].items(): if source in ("model", "tools"): _render_completed_message(update["messages"][-1])
--- 片段[5] oss__python__langchain__streaming#036 ---
eted_message(message: AnyMessage) -> None: if isinstance(message, AIMessage) and message.tool_calls: print(f"Tool calls: {message.tool_calls}") if isinstance(message, ToolMessage): print(f"Tool response: {message.content_blocks}") input_message = {"role": "user", "content": "What is the weather in Boston?"} for chunk in agent.stream( {"messages": [input_message]}, stream_mode=["messages", "updates"], version="v2", ): if chunk["type"] == "messages": token, metadata = chunk["data"] if isinstance(token, AIMessageChunk): _render_message_chunk(token) elif chunk["type"] == "updates": for source, update in chunk["data"].items(): if source in ("model", "tools"): # `source` captures node name

### 57. v1-C-007 [single-hop] score=1.0
Q: JS 里调 maxMarginalRelevanceSearch 时，lambda 调大是更偏向相关性还是多样性？
GOLD: lambda 为 1.0 时偏向相关性（relevance），为 0.0 时偏向多样性（diversity），示例里取 0.5 是折中。另外 k 是要返回的文档数，fetchK 是挑选之前先考虑的候选数。
ANSWER: **结论：在 JS 里 `lambda` 调大更偏向相关性，调小更偏向多样性。** 片段中注释明确写着 `1.0 favors relevance, 0.0 favors diversity` [2]。

**最小可用示例：**

```javascript
const docs = await vectorStore.maxMarginalRelevanceSearch(query, {
  k: 4, // number of documents to return
  fetchK: 20, // number of candidates to consider before selecting
  lambda: 0.5, // 1.0 favors relevance, 0.0 favors diversity
});
```

补充说明（以片段为准）：
- JS 侧参数名是 `lambda`、`fetchK` [2]；Python 侧对应的是 `lambda_mult`、`fetch_k` [1]，如果你看到的是 Python 写法，注意命名差异。
- MMR 的作用是「balance similarity with diversity」[3][4]，即平衡相似性与多样性。
--- 片段[1] oss__python__langchain__retrieval-optimization#010 ---
```

docs = vector_store.max_marginal_relevance_search(

    query,

    k=4,  # number of documents to return

    fetch_k=20,  # number of candidates to consider before selecting

    lambda_mult=0.5,  # 1.0 favors relevance, 0.0 favors diversity

)

```
--- 片段[2] oss__javascript__langchain__retrieval-optimization#011 ---
```

const docs = await vectorStore.maxMarginalRelevanceSearch(query, {

  k: 4, // number of documents to return

  fetchK: 20, // number of candidates to consider before selecting

  lambda: 0.5, // 1.0 favors relevance, 0.0 favors diversity

});

```
--- 片段[3] oss__javascript__langchain__knowledge-base#017 ---
- By similarity and maximum marginal relevance (to balance similarity with diversity)
--- 片段[4] oss__python__langchain__knowledge-base#031 ---
- By similarity and maximum marginal relevance (to balance similarity with diversity)
--- 片段[5] oss__python__langchain__retrieval-optimization#000 ---
Improve retrieval quality Improve RAG retrieval quality in LangChain with metadata filtering, query transformation, hybrid search, maximal marginal relevance, and reranking.

### 58. v1-C-008 [single-hop] score=1.0
Q: JS 里想对用户输入和模型输出都做邮箱脱敏，piiMiddleware 要怎么配？
GOLD: 对输入调 piiMiddleware("email", { strategy: "redact", applyToInput: true })，对输出再调一次 piiMiddleware("email", { strategy: "redact", applyToOutput: true })，然后把这两个都放进 createAgent 的 middleware 数组里。
ANSWER: ## 结论

在 JS 里用 `piiMiddleware` 对邮箱做脱敏，需要**分别注册两个中间件**：一个用 `applyToInput: true` 处理用户输入，另一个用 `applyToOutput: true` 处理模型输出，两者 `strategy` 都设为 `"redact"` [5]。

注意：JS 版本的参数名是驼峰式 `applyToInput` / `applyToOutput`（不是 Python 的 `apply_to_input` / `apply_to_output`）[4][5]。

## 最小可用示例

```javascript
import { createAgent, piiMiddleware } from "langchain";

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [],
  middleware: [
    // 处理用户输入
    piiMiddleware("email", {
      strategy: "redact",
      applyToInput: true,
    }),
    // 处理模型输出
    piiMiddleware("email", {
      strategy: "redact",
      applyToOutput: true,
    }),
  ],
});
```

## 说明

- 片段 [5] 的示例正是把输入和输出拆成两个 `piiMiddleware` 调用，分别设置 `applyToInput: true` 和 `applyToOutput: true` [5]。
- 片段 [4] 也展示了 `piiMiddleware("email", { strategy: "redact", applyToInput: true })` 的写法，可作为输入侧配置的参考 [4]。
- 片段中未出现把输入和输出合并到同一个 `piiMiddleware` 调用的写法，因此按片段应分开配置。
--- 片段[1] oss__python__langchain__event-streaming#016 ---
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
--- 片段[2] oss__python__langchain__guardrails#017 ---
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, send_email_tool], middleware=[ # Layer 1: Deterministic input filter (before agent) ContentFilterMiddleware(banned_keywords=["hack", "exploit"]), # Layer 2: PII protection (before and after model) PIIMiddleware("email", strategy="redact", apply_to_input=True), PIIMiddleware("email", strategy="redact", apply_to_output=True), # Layer 3: Human approval for sensitive tools HumanInTheLoopMiddleware(interrupt_on={"send_email": True}), # Layer 4: Model-based safety check (after agent) SafetyGuardrailMiddleware(),
--- 片段[3] oss__python__langchain__middleware__built-in#042 ---
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
--- 片段[4] oss__javascript__deepagents__going-to-production#055 ---
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
--- 片段[5] oss__javascript__langchain__guardrails#011 ---
``` import { createAgent, piiMiddleware, humanInTheLoopMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, sendEmailTool], middleware: [ // Layer 1: Deterministic input filter (before agent) contentFilterMiddleware(["hack", "exploit"]), // Layer 2: PII protection (before and after model) piiMiddleware("email", { strategy: "redact", applyToInput: true, }), piiMiddleware("email", { strategy: "redact", applyToOutput: true, }), // Layer 3: Human approval for sensitive tools humanInTheLoopMiddleware({ interruptOn: { send_email: { allowAccept: true, allowEdit: true, allowRespond: true }, } }), // Layer 4: Model-based safety check (after agent)

### 59. v1-C-009 [single-hop] score=1.0
Q: JS 里用 summarizationMiddleware 压缩历史时，trigger 和 keep 分别控制什么？
GOLD: trigger: { tokens: 4000 } 表示对话接近 4000 token 时就触发摘要；keep: { messages: 20 } 表示保留最近 20 条消息不动。还需要用 model 指定真正执行摘要的模型。
ANSWER: **结论**

在 JS 版本里，`summarizationMiddleware` 的 `trigger` 控制**何时触发摘要压缩**，`keep` 控制**压缩后保留多少历史消息** [5]。

- `trigger`：可以是单个对象（多个条件之间是 **AND 逻辑**），也可以是数组（多个条件之间是 **OR 逻辑**）。例如 `{ tokens: 4000, messages: 10 }` 表示 tokens ≥ 4000 **且** messages ≥ 10 才触发；`[{ tokens: 3000 }, { messages: 6 }]` 表示 tokens ≥ 3000 **或** messages ≥ 6 就触发 [5]。
- `keep`：指定压缩后保留的历史量，示例中为 `{ messages: 20 }`，即保留 20 条消息 [5]。

**最小可用示例**

```javascript
import { createAgent, summarizationMiddleware } from "langchain";

// 单条件（AND 逻辑）：tokens >= 4000 且 messages >= 10 时触发
const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [weatherTool, calculatorTool],
  middleware: [
    summarizationMiddleware({
      model: "gpt-5.4-mini",
      trigger: { tokens: 4000, messages: 10 },
      keep: { messages: 20 },
    }),
  ],
});

// 多条件（OR 逻辑）：tokens >= 3000 或 messages >= 6 时触发
const agent2 = createAgent({
  model: "gpt-6.1-sol",
  tools: [weatherTool, calculatorTool],
  middleware: [
    summarizationMiddleware({
      model: "gpt-5.4-mini",
      trigger: [{ tokens: 3000 }, { messages: 6 }],
      keep: { messages: 20 },
    }),
  ],
});
```

**需要注意的差异**

- 你问的是 JS 的 `summarizationMiddleware`（小驼峰），片段 [5] 确实是这个命名；而 Python 片段 [1][2][3][4] 用的是 `SummarizationMiddleware`（大驼峰），且 Python 的 `trigger` 写法是元组/列表形式（如 `("tokens", 4000)`），与 JS 的对象写法不同，不要混用 [1][4][5]。
- 片段 [3] 中 Python 示例把 `trigger` 写成字典 `{"tokens": 4000}`，与 [1][4] 的元组写法不一致，以各自片段为准 [1][3][4]。
--- 片段[1] oss__python__langchain__middleware__built-in#023 ---
```

from langchain.agents import create_agent

from langchain.agents.middleware import SummarizationMiddleware



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[your_weather_tool, your_calculator_tool],

    middleware=[

        SummarizationMiddleware(

            model="gpt-5.4-mini",

            trigger=("tokens", 4000),

            keep=("messages", 20),

        ),

    ],

)

```
--- 片段[2] oss__python__langchain__multi-agent__handoffs-customer-support#034 ---
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
--- 片段[3] oss__python__langchain__context-engineering#052 ---
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
--- 片段[4] oss__python__langchain__middleware__built-in#028 ---
``` from langchain.agents import create_agent from langchain.agents.middleware import SummarizationMiddleware # Single condition: trigger if tokens >= 4000 agent = create_agent( model="gpt-6.1-sol", tools=[your_weather_tool, your_calculator_tool], middleware=[ SummarizationMiddleware( model="gpt-5.4-mini", trigger=("tokens", 4000), keep=("messages", 20), ), ], ) # Multiple conditions: trigger if number of tokens >= 3000 OR messages >= 6 agent2 = create_agent( model="gpt-6.1-sol", tools=[your_weather_tool, your_calculator_tool], middleware=[ SummarizationMiddleware( model="gpt-5.4-mini", trigger=[ ("tokens", 3000), ("messages", 6), ], keep=("messages", 20), ), ], ) # AND logic:
--- 片段[5] oss__javascript__langchain__middleware__built-in#031 ---
``` import { createAgent, summarizationMiddleware } from "langchain"; // Single condition (AND logic): trigger if tokens >= 4000 AND messages >= 10 const agent = createAgent({ model: "gpt-6.1-sol", tools: [weatherTool, calculatorTool], middleware: [ summarizationMiddleware({ model: "gpt-5.4-mini", trigger: { tokens: 4000, messages: 10 }, keep: { messages: 20 }, }), ], }); // Multiple conditions (OR logic): trigger if tokens >= 3000 OR messages >= 6 const agent2 = createAgent({ model: "gpt-6.1-sol", tools: [weatherTool, calculatorTool], middleware: [ summarizationMiddleware({ model: "gpt-5.4-mini", trigger: [ { tokens: 3000 }, { messages: 6 }, ], keep: { messages: 20 }, }), ], });

### 60. v1-C-010 [single-hop] score=1.0
Q: JS 里通过 MCPAdapter 接进来的工具在服务端报错时，Agent 那边会看到什么？
GOLD: 服务端错误（isError: true）会作为一条失败的 ToolMessage 传给模型，所以 Agent 能读到服务端自己的报错信息并尝试恢复。默认情况下 createAgent 也会把传输层失败转成错误的 tool message。
ANSWER: 结论：在 JS 版本里，MCP 服务端返回错误（`isError: true`）时，会以一条失败的 `ToolMessage` 形式到达模型，Agent 可以读到服务端自己的错误消息并据此恢复；默认情况下，`createAgent` 还会把传输层失败也转换成错误工具消息 [1]。

需要注意的差异：Python 片段里说传输失败仍然会抛出（"Transport failures still raise"）[3]，而 JS 片段说默认 `createAgent` 会把传输失败也转成错误工具消息 [1]。两者行为描述不一致，以各自语言片段为准。

最小可用示例（JS）[1]：

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

    // A server error (isError: true) reaches the model as a failed ToolMessage,
    // so the agent can read the server's own message and recover. By default,
    // createAgent also converts transport failures into error tool messages.
  }
}
```

补充：`MCPAdapter` 会从目标推断传输方式（URL、stdio 本地脚本、进程内 server、多 server 的 `MCPConfig` dict，或预构建的 `fastmcp.Client`），`await adapter.listTools()` 返回可直接交给 `createAgent` 的 LangChain 工具 [5]。
--- 片段[1] oss__javascript__langchain__mcp__tools#006 ---
``` import { MCPAdapter } from "@langchain/mcp-adapters"; import { createAgent, ToolMessage } from "langchain"; async function divideByZero(serverUrl: string) { const adapter = new MCPAdapter({ servers: { calculator: { url: serverUrl } }, }); try { const tools = await adapter.listTools(); const agent = createAgent({ model: "claude-sonnet-5", tools }); const result = await agent.invoke({ messages: [{ role: "user", content: "What is 10 divided by 0?" }], }); // A server error (isError: true) reaches the model as a failed ToolMessage, // so the agent can read the server's own message and recover. By default, // createAgent also converts transport failures into error tool messages.
--- 片段[2] oss__python__langchain__mcp__tools#001 ---
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
--- 片段[3] oss__python__langchain__mcp__tools#006 ---
``` from langchain.agents import create_agent from langchain.mcp import MCPAdapter from langchain.messages import ToolMessage async def divide_by_zero(server) -> dict: async with MCPAdapter(server) as adapter: tools = await adapter.list_tools() agent = create_agent("claude-sonnet-5", tools) result = await agent.ainvoke( { "messages": [ { "role": "user", "content": "Use the divide tool to calculate 10 divided by 0.", } ] } ) # A server error (isError=True) reaches the model as a failed ToolMessage, # so the agent can read the server's own message and recover. Transport # failures still raise, because a model cannot act on those. for message in result["messages"]:
--- 片段[4] oss__javascript__langchain__mcp__tools#001 ---
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
--- 片段[5] oss__python__releases__changelog#013 ---
- One adapter, any transport : MCPAdapter infers the transport from its target — a URL, a local script over stdio, an in-process server, an MCPConfig dict for multiple servers , or a pre-built fastmcp.Client . await adapter.list_tools() returns LangChain tools ready for create_agent . See the MCP overview .

### 61. v1-C-011 [single-hop] score=1.0
Q: subagents 和 router 这两种多 Agent 模式，在路由上有什么不同？
GOLD: subagents 模式让主 Agent 把子 Agent 当工具来协调，所有路由都经过主 Agent，由它决定何时、怎样调用每个子 Agent；router 模式则用一个路由步骤先给输入分类，再把请求分发给一个或多个专门 Agent，最后把各自结果合成一个回复。
ANSWER: **结论：** 两者的核心区别在于「谁来做路由决策、路由是否集中」。

- **Subagents**：由一个主 Agent 把各个子 Agent 当作工具来协调，**所有路由都经过主 Agent**，由主 Agent 决定何时、如何调用每个子 Agent [1][2]。
- **Router**：是一个**独立的路由步骤**，先对输入进行分类，再把它导向一个或多个专用 Agent，最后把结果综合成一个合并的响应 [1][2]。

也就是说，Subagents 的路由是「主 Agent 在对话/执行过程中动态决定调用哪个子 Agent 工具」；Router 的路由是「先分类、再分发、最后汇总」的独立环节 [1][2]。

另外补充一点相关差异：Subagents 模式下子 Agent **不直接与用户交互**，结果返回给主 Agent 而非用户（不过可以在子 Agent 内使用 interrupt 允许用户交互）[3][4]。

**最小示例（示意，非文档原文）：**

```text
# Subagents：主 Agent 决定调用哪个子 Agent 工具
main_agent -> tool(subagent_A) -> 结果回到 main_agent -> main_agent 回复用户

# Router：先分类，再分发，最后汇总
input -> router(分类) -> [agent_A, agent_B] -> 汇总 -> 合并响应
```

（上面代码块只是对片段描述的示意，文档片段中未给出具体代码示例。）

**关于性能：** 在 Multi-domain 场景下，Subagents 与 Router 的模型调用次数均为 5、总 token 均约 ~9K，且都被标为最适用（✅）[5]。
--- 片段[1] oss__javascript__langchain__multi-agent#003 ---
| Pattern | How it works | | --- | --- | | Subagents | A main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent. | | Handoffs | Behavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt. | | Skills | Specialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed. | | Router | A routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response. |
--- 片段[2] oss__python__langchain__multi-agent#003 ---
| Pattern | How it works | | --- | --- | | Subagents | A main agent coordinates subagents as tools. All routing passes through the main agent, which decides when and how to invoke each subagent. | | Handoffs | Behavior changes dynamically based on state. Tool calls update a state variable that triggers routing or configuration changes, switching agents or adjusting the current agent’s tools and prompt. | | Skills | Specialized prompts and knowledge loaded on-demand. A single agent stays in control while loading context from skills as needed. | | Router | A routing step classifies input and directs it to one or more specialized agents. Results are synthesized into a combined response. |
--- 片段[3] oss__python__langchain__multi-agent__subagents#000 ---
- No direct user interaction: Subagents return results to the main agent, not the user (though you can use interrupts within a subagent to allow user interaction)
--- 片段[4] oss__javascript__langchain__multi-agent__subagents#000 ---
- No direct user interaction: Subagents return results to the main agent, not the user (though you can use interrupts within a subagent to allow user interaction)
--- 片段[5] oss__javascript__langchain__multi-agent#013 ---
| Pattern | Model calls | Total tokens | Best fit |

| --- | --- | --- | --- |

| Subagents | 5 | ~9K | ✅ |

| Handoffs | 7+ | ~14K+ |  |

| Skills | 3 | ~15K |  |

| Router | 5 | ~9K | ✅ |

### 62. v1-C-012 [single-hop] score=0.5
Q: 内置的 model retry 和 model fallback 两个 middleware 分别做什么？
GOLD: Model retry 对失败的模型调用按 exponential backoff 自动重试；Model fallback 在主模型失败时自动切到备用的其他模型。同一张表里 Model refusal 的差别是：模型拒答时直接抛错，而不是把拒答当成最终答案。
ANSWER: **结论**

- **Model retry**：自动重试失败的模型调用，采用可配置的指数退避（exponential backoff）[1][2][3][4]。
- **Model fallback**：当主模型失败时，自动回退到备选模型 [3][4]。

**最小可用示例**

片段 [5] 只给出了 `modelRetryMiddleware` 的用法，没有给出 `modelFallback` 的示例，因此这里只展示 retry 部分：

```javascript
import {
  createAgent,
  modelRetryMiddleware,
} from "langchain";

const agent = createAgent({
  model: "google:gemini-4-hydrogen",
  middleware: [
    // Retry model calls on rate limits, timeouts, and 5xx errors
    modelRetryMiddleware({ maxRetries: 3, backoffFactor: 2.0, initialDelayMs: 1000 }),
  ],
});
```

**说明与差异提示**

- 片段中该 middleware 的名称写作 `modelRetryMiddleware`（驼峰式函数名），而表格里写作 “Model retry” [3][4][5]，二者指同一能力，只是文档中展示形式不同。
- 关于 `modelFallback` 的具体参数或代码示例，给出的文档里没有找到，无法提供。
--- 片段[1] oss__javascript__releases__changelog#026 ---
- Model retry middleware : New middleware for automatically retrying failed model calls with configurable exponential backoff, improving agent reliability.
--- 片段[2] oss__python__releases__changelog#053 ---
- Model retry middleware : New middleware for automatically retrying failed model calls with configurable exponential backoff.
--- 片段[3] oss__python__langchain__middleware__built-in#000 ---
| Middleware | Description | | --- | --- | | Tool error | Catch tool execution exceptions and convert them to error messages for the model. | | Tool retry | Automatically retry failed tool calls with exponential backoff. | | Model retry | Automatically retry failed model calls with exponential backoff. | | Model fallback | Automatically fallback to alternative models when primary fails. | | Model refusal | Raise an error when the model refuses, instead of treating the refusal as a final answer. | | Summarization | Automatically summarize conversation history when approaching token limits. | | Human-in-the-loop | Pause execution for human approval of tool calls. |
--- 片段[4] oss__javascript__langchain__middleware__built-in#000 ---
| Middleware | Description | | --- | --- | | Tool retry | Automatically retry failed tool calls with exponential backoff. | | Model retry | Automatically retry failed model calls with exponential backoff. | | Model fallback | Automatically fallback to alternative models when primary fails. | | Model refusal | Throw an error when the model refuses, instead of treating the refusal as a final answer. | | Summarization | Automatically summarize conversation history when approaching token limits. | | Human-in-the-loop | Pause execution for human approval of tool calls. | | Model call limit | Limit the number of model calls to prevent excessive costs. |
--- 片段[5] oss__javascript__deepagents__fault-tolerance#008 ---
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

### 63. v1-C-013 [single-hop] score=0.0
Q: 在 LangGraph 节点里，普通函数和 Task 在恢复时的重跑行为差在哪？
GOLD: 节点里的普通函数不单独 checkpoint，它跑在节点的 super-step 里，节点重跑时它就跟着重跑；Task 不会产生新的图 checkpoint，结果存在运行中的 entrypoint 或父 checkpoint 里，恢复时外层 entrypoint 或节点从头重放，已完成的 Task 直接返回存下的结果。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

片段只涉及以下相关点，但没有对比「普通函数」与「Task」在恢复时的重跑行为：

- [1][2] 只说明：在 resume point 之前新增、删除或重排 `@task` 调用或 `interrupt` 调用会破坏确定性，因为 LangGraph 按调用在 replay 中的位置来匹配缓存结果和 resume 值。
- [3][4] 只说明 checkpointers 的 pending writes：某个 super-step 中某节点失败时，同一步内已成功完成的其他节点的写入会被保存，从该 super-step 恢复时不会重跑已成功的节点。
- [5] 只说明重命名或删除节点会导致恢复失败。

缺少的内容：没有片段说明普通函数（非 `@task`）在恢复时是否重跑、是否被缓存，也没有与 `@task` 的重跑/缓存行为做对比。
--- 片段[1] oss__python__langgraph__backward-compatibility#016 ---
- Adding, removing, or reordering @task calls or interrupt calls that come before the resume point. LangGraph matches cached results and resume values to calls by their position in the replay, so shifting that position can cause the wrong cached value to be replayed against a different call.
--- 片段[2] oss__javascript__langgraph__backward-compatibility#013 ---
- Adding, removing, or reordering @task calls or interrupt calls that come before the resume point. LangGraph matches cached results and resume values to calls by their position in the replay, so shifting that position can cause the wrong cached value to be replayed against a different call.
--- 片段[3] oss__python__langgraph__checkpointers#005 ---
- Pending writes : When a graph node fails mid-execution at a given super-step , LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that super-step. When you resume graph execution from that super-step you don’t re-run the successful nodes.
--- 片段[4] oss__javascript__langgraph__checkpointers#005 ---
- Pending writes : When a graph node fails mid-execution at a given super-step , LangGraph stores pending checkpoint writes from any other nodes that completed successfully at that super-step. When you resume graph execution from that super-step you don’t re-run the successful nodes.
--- 片段[5] oss__python__langgraph__backward-compatibility#003 ---
- Renaming or removing a node while threads are paused at or about to enter that node, for example at an interrupt or via a checkpointed conditional edge that still routes to the old name. On resume, LangGraph cannot find the node by its saved name and the run fails. The starting point for resuming a run is the beginning of the node where execution stopped, so a missing node has nowhere to resume from.

### 64. v1-C-014 [multi-hop] score=0.5
Q: 在 JS SDK 里，短期记忆和长期记忆分别由哪个组件负责，作用范围有什么不同？
GOLD: Checkpointer 保存图状态快照，作用范围是单个 thread，属于线程内的短期记忆，用于对话连续、human-in-the-loop、time travel 和容错；Store 保存应用自定义的 key-value 数据，跨 thread 共享，属于长期记忆。用 Store 时通常把 userId 和业务上下文组成 namespace 数组，再调 store.put(namespace, key, value) 写入。
ANSWER: 结论：在 JS SDK 中，短期记忆由 checkpointer 负责，长期记忆由 store 负责 [1]。作用范围上，长期记忆跨会话保存、跨对话线程共享，可在任意线程任意时间读取，并按自定义 namespace 划分范围，而不局限于单个 thread ID [5]；短期记忆则对应当前对话内存在的数据（如消息、计数器、自定义字段）[3]。注意：片段 [3] 是 Python 文档，但其中对 State/Store 的定位与 [1][5] 一致，可作为概念参考。

最小示例（概念示意，片段未给出具体 JS API 代码）：

```javascript
// 短期记忆：通过 checkpointer 保存当前对话状态 [1]
// 长期记忆：通过 store 保存跨会话数据 [1][5]
```

补充说明：片段 [1] 只说明了两者的分工，没有给出 JS 侧 checkpointer/store 的具体类名、参数或初始化代码；这部分内容给出的文档里没有找到。
--- 片段[1] oss__javascript__langgraph__persistence#000 ---
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
--- 片段[2] oss__python__langgraph__persistence#000 ---
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
--- 片段[3] oss__python__langchain__tools#008 ---
| Component | Description | Use case | | --- | --- | --- | | State | Short-term memory - mutable data that exists for the current conversation (messages, counters, custom fields) | Access conversation history, track tool call counts | | Context | Immutable configuration passed at invocation time (user IDs, session info) | Personalize responses based on user identity | | Store | Long-term memory - persistent data that survives across conversations | Save user preferences, maintain knowledge base | | Stream Writer | Emit real-time updates during tool execution | Show progress for long-running operations |
--- 片段[4] oss__python__concepts__memory#001 ---
- Long-term memory stores user-specific or application-level data across sessions and is shared across conversational threads. It can be recalled at any time and in any thread . Memories are scoped to any custom namespace, not just within a single thread ID. LangGraph provides stores ( reference doc ) to let you save and recall long-term memories.
--- 片段[5] oss__javascript__concepts__memory#001 ---
- Long-term memory stores user-specific or application-level data across sessions and is shared across conversational threads. It can be recalled at any time and in any thread . Memories are scoped to any custom namespace, not just within a single thread ID. LangGraph provides stores ( reference doc ) to let you save and recall long-term memories.

### 65. v1-C-015 [multi-hop] score=0.5
Q: Agent 要执行敏感工具前我想停下来等人审，人能给出哪几种决定，之后又怎么让同一条对话继续？
GOLD: 审批型中断有四种决定：approve 按 Agent 提议的原参数执行，edit 先改工具参数再执行，reject 整个跳过这次工具调用并把拒绝意见回传给 Agent，respond 则把人的回复当成合成的工具结果、不真正执行。恢复时对同一个会话调 await graph.invoke(new Command({ resume: answer }), config)，answer 会成为该 interrupt 的返回值。
ANSWER: ## 结论

**能给出的决定类型**（片段中出现的）：`approve`、`respond`、`edit`、`reject` 四种 [1][2][3][5]。

**如何让同一条对话继续**：用同一个 `thread_id` 的 config 再次调用 `agent.invoke`，并传入 `Command(resume=...)`，其中 `resume` 里放 `decisions` 列表 [1][2][3][5]。`decisions` 是列表，每个待审动作对应一个决定，**顺序必须与 interrupt 请求中动作的顺序一致** [2][3][5]。

**注意点**：
- Human-in-the-loop 需要持久化，因此必须提供 thread ID（片段示例为 `config = {"configurable": {"thread_id": "some_id"}}`）[1]。
- 各决定类型的字段不同：`respond` 用 `message` 直接作为工具结果返回 [2]；`edit` 用 `editedAction`（JS）/ `edited_action`（Python）携带 `name` 和 `args` [3][4]；`reject` 可选 `message` 说明拒绝原因 [5]；`approve` 在片段 [1] 中仅以 `{"type": "approve"}` 出现，未展示其他字段。

## 最小可用示例

**Python — 暂停后批准** [1]：

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

**Python — 编辑动作** [4]：

```python
agent.invoke(
    Command(
        resume={
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": {
                        "name": "new_tool_name",
                        "args": {"key1": "new_value", "key2": "original_value"},
                    }
                }
            ]
        }
    ),
    config=config,  # Same thread ID to resume the paused conversation
    version="v2",
)
```

**JavaScript — 直接回复 / 拒绝** [2][5]：

```javascript
await agent.invoke(
    new Command({
        resume: {
            decisions: [
                { type: "respond", message: "Blue." }
            ]
        }
    }),
    config  // Same thread ID to resume the paused conversation
);

await agent.invoke(
    new Command({
        resume: {
            decisions: [
                {
                    type: "reject",
                    message: "User rejected this action. Do not retry this tool call."
                }
            ]
        }
    }),
    config  // Same thread ID to resume the paused conversation
);
```

## 与用户说法的差异提示

片段中 Python 的 `edit` 决定字段名是 `edited_action`（下划线）[4]，而 JavaScript 是 `editedAction`（驼峰）[3]；若你按另一种命名书写会不匹配，请以对应语言的片段为准。
--- 片段[1] oss__python__langchain__guardrails#005 ---
ySaver(), ) # Human-in-the-loop requires a thread ID for persistence config = {"configurable": {"thread_id": "some_id"}} # Agent will pause and wait for approval before executing sensitive tools result = agent.invoke( {"messages": [{"role": "user", "content": "Send an email to the team"}]}, config=config ) result = agent.invoke( Command(resume={"decisions": [{"type": "approve"}]}), config=config  # Same thread ID to resume the paused conversation ) ```
--- 片段[2] oss__javascript__langchain__human-in-the-loop#042 ---
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
--- 片段[3] oss__javascript__langchain__human-in-the-loop#040 ---
``` await agent.invoke( new Command({ // Decisions are provided as a list, one per action under review. // The order of decisions must match the order of actions // in the interrupt request. resume: { decisions: [ { type: "edit", // Edited action with tool name and args editedAction: { // Tool name to call. // Will usually be the same as the original action. name: "new_tool_name", // Arguments to pass to the tool. args: { key1: "new_value", key2: "original_value" }, } } ] } }), config  // Same thread ID to resume the paused conversation ); ```
--- 片段[4] oss__python__langchain__human-in-the-loop#042 ---
``` agent.invoke( Command( # Decisions are provided as a list, one per action under review. # The order of decisions must match the order of actions # in the interrupt request. resume={ "decisions": [ { "type": "edit", # Edited action with tool name and args "edited_action": { # Tool name to call. # Will usually be the same as the original action. "name": "new_tool_name", # Arguments to pass to the tool. "args": {"key1": "new_value", "key2": "original_value"}, } } ] } ), config=config,  # Same thread ID to resume the paused conversation version="v2", ) ```
--- 片段[5] oss__javascript__langchain__human-in-the-loop#041 ---
```

await agent.invoke(

    new Command({

        // Decisions are provided as a list, one per action under review.

        // The order of decisions must match the order of actions

        // in the interrupt request.

        resume: {

            decisions: [

                {

                    type: "reject",

                    // Optional: explain why the action was rejected

                    // and whether the agent should retry a different approach.

                    message: "User rejected this action. Do not retry this tool call.",

                }

            ]

        }

    }),

    config  // Same thread ID to resume the paused conversation

);

```

### 66. v1-C-016 [multi-hop] score=0.5
Q: JS 里流式跑一个可能被打断的 Agent，怎么判断这次是暂停在 interrupt 上还是已经跑完，暂停了又从哪里取中断信息？
GOLD: 先看 stream.interrupted，它表示这次运行是否为等人输入而暂停；暂停时用 stream.interrupts 取中断 payload，示例里是 stream.interrupts[0].payload。另外 stream.messages 流出聊天模型消息和 token 增量，stream.values 迭代状态快照并可以 await 最终值。
ANSWER: ## 结论

在 JS 里用流式方式跑 Agent 时，判断是否暂停在 interrupt 上，看流对象上的 `stream.interrupted` 布尔标志；中断的具体信息（payload）从 `stream.interrupts` 里读取 [1][2][3]。每次 run 结束后检查这两个字段即可 [2][3]。

注意：片段里出现的字段是 `stream.interrupted` / `stream.interrupts`（复数），不是 `stream.interrupt` 之类的单数写法，以片段为准 [1][2][3]。

另外，片段 [5] 展示的是**非流式** `invoke` 场景下，中断信息从返回结果的 `__interrupt__` 字段读取（`result.__interrupt__`），这与流式场景的 `stream.interrupts` 是不同入口，不要混用 [5]。

## 最小可用示例（流式）

```javascript
import { Command } from "@langchain/langgraph";

const config = { configurable: { thread_id: "some_id" } };

// 流式跑 agent，直到 interrupt 或结束
const stream = await agent.streamEvents(
  { messages: [{ role: "user", content: "Delete old records from the database" }] },
  { ...config, version: "v3" }
);

for await (const message of stream.messages) {
  for await (const token of message.text) {
    process.stdout.write(token);
  }
}

// 判断这次是暂停在 interrupt 上，还是已经跑完
if (stream.interrupted) {
  console.log(`\n\nInterrupt: ${JSON.stringify(stream.interrupts)}`);
}
```

## 补充说明

- 片段 [1] 的示例在检查完 `stream.interrupted` 后，还展示了「人工决策后用流式恢复」的开头（`const resumeStream = await agent.streamEvents(`），但该片段在此处被截断，**恢复调用的完整参数没有给出**，因此无法从现有片段确认恢复时具体传什么。
- 片段 [5] 给出了非流式恢复的写法：`await graph.invoke(new Command({ resume: true }), config)`，即用 `Command({ resume })` 把人工响应回传给 `interrupt()` [5]。这是 `invoke` 场景，是否同样适用于 `streamEvents` 的恢复，片段未明确说明。
- 片段 [4] 展示了另一种基于 `mode === "updates"` 且数据里出现 `__interrupt__` 时取 `data.__interrupt__[0]` 的写法，属于 deepagents 的流式处理路径 [4]，与 [1] 的 `stream.interrupted` / `stream.interrupts` 是不同 API 形态，使用时注意区分来源。
--- 片段[1] oss__javascript__langchain__human-in-the-loop#044 ---
``` import { Command } from "@langchain/langgraph"; const config = { configurable: { thread_id: "some_id" } }; // Stream agent progress and LLM tokens until interrupt const stream = await agent.streamEvents( { messages: [{ role: "user", content: "Delete old records from the database" }] }, { ...config, version: "v3" } ); for await (const message of stream.messages) { for await (const token of message.text) { process.stdout.write(token); } } // Check whether the run paused for human input if (stream.interrupted) { console.log(`\n\nInterrupt: ${JSON.stringify(stream.interrupts)}`); } // Resume with streaming after human decision const resumeStream = await agent.streamEvents(
--- 片段[2] oss__python__langgraph__interrupts#025 ---
- stream.interrupted / stream.interrupts : After each run, check whether the graph paused; read payloads from stream.interrupts
--- 片段[3] oss__javascript__langgraph__interrupts#026 ---
- stream.interrupted / stream.interrupts : After each run, check whether the graph paused; read payloads from stream.interrupts
--- 片段[4] oss__javascript__deepagents__human-in-the-loop#012 ---
ns in real time if (token.text) { process.stdout.write(token.text); } } if (mode === "updates" && data?.__interrupt__) { pendingInterrupt = data.__interrupt__[0]; } } // If no interrupt occurred, the agent finished if (!pendingInterrupt) break; const interruptValue = pendingInterrupt.value; const actionRequests = interruptValue.actionRequests; const reviewConfigs = interruptValue.reviewConfigs; const configMap = Object.fromEntries( reviewConfigs.map((cfg: any) => [cfg.actionName, cfg]) ); for (const action of actionRequests) { const review = configMap[action.name]; console.log(`\nTool: ${action.name}`); console.log(`Arguments: ${JSON.stringify(action.args)}`); console.log(`Allowed:
--- 片段[5] oss__javascript__langgraph__interrupts#009 ---
```

import { Command } from "@langchain/langgraph";



// Initial run - hits the interrupt and pauses

// thread_id is the durable pointer back to the saved checkpoint

const config = { configurable: { thread_id: "thread-1" } };

const result = await graph.invoke({ input: "data" }, config);



// Check what was interrupted

// __interrupt__ mirrors every payload you passed to interrupt()

console.log(result.__interrupt__);

// [{ value: 'Do you approve this action?', ... }]



// Resume with the human's response

// Command({ resume }) returns that value from interrupt() in the node

await graph.invoke(new Command({ resume: true }), config);

```

### 67. v1-C-017 [multi-hop] score=0.5
Q: JS LangGraph 的服务要优雅停机时，正在跑的节点会怎么处理，什么情况下会抛 GraphDrained？
GOLD: 优雅停机时，正在执行的节点会跑到完，drain 到下一个 superstep 才生效；如果节点上有 retry policy 且正在重试，重试循环会跑完或耗尽后 drain 才生效。如果还剩 superstep，就会抛 GraphDrained(reason) ，此时 checkpoint 已保存、可以恢复。
ANSWER: ## 结论

在 JS LangGraph 中做优雅停机时，正在运行的图不会立刻被强杀，而是**协作式地（cooperatively）在当前 superstep 完成后停止**，并保存一个可恢复的 checkpoint [2]。具体机制是：创建一个 `RunControl`，在信号处理器或 supervisor 中调用 `requestDrain(...)`；当 drain 生效、图提前停止时，`graph.invoke(...)` 会抛出 `GraphDrained` 异常 [1][3]。

关于「什么情况下会抛 `GraphDrained`」：文档片段只说明当图因 drain 请求而提前停止、并保存了 checkpoint 时会抛出该异常 [1][2][3]。片段没有进一步细化触发条件（例如是否只在某个 superstep 边界、是否有其他前置条件），因此更细的判定规则在给出的文档里没有找到。

## 最小可用示例（SIGTERM 钩子）

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

来源：[3]（另见 [1] 的非信号处理器版本）。

## 需要指出的差异

- 你问的是「JS」，片段中 JS 的 API 是 `RunControl`、`requestDrain(...)`、`GraphDrained`，通过 `graph.invoke(inputs, { ...config, control })` 传入 control [1][3]。
- 片段 [2][4][5] 是 **Python** 版本，对应 API 为 `request_drain()`、`GraphDrained`，且 `graph.invoke(inputs, config, control=control)` 的传参形式不同 [4][5]。若你参考的是 Python 写法，请注意 JS 侧是 `requestDrain` 且 control 放在 options 对象里 [1][3]。

## 补充说明（片段未覆盖的部分）

- 片段提到「Resume later with the same config」[1][3]，但没有给出恢复（resume）的具体 API 或代码，因此恢复方式在给出的文档里没有找到。
- 片段 [2] 提到「after the current superstep completes」，但未说明节点内部正在执行的长任务是否会被中断，这一点片段未涉及。
--- 片段[1] oss__javascript__langgraph__fault-tolerance#041 ---
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
--- 片段[2] oss__python__releases__changelog#033 ---
- Graceful shutdown : Stop an in-flight run cooperatively after the current superstep completes, and save a resumable checkpoint. Create a RunControl and call request_drain() from any thread; the run raises GraphDrained and can be resumed later with the same config.
--- 片段[3] oss__javascript__langgraph__fault-tolerance#044 ---
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
--- 片段[4] oss__python__langgraph__fault-tolerance#038 ---
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
--- 片段[5] oss__python__langgraph__fault-tolerance#041 ---
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

### 68. v1-C-018 [multi-hop] score=0.0
Q: JS 里子图的持久化模式和把一段逻辑做成普通图节点，在 checkpoint 上有什么区别？
GOLD: 子图按模式不同：checkpointer 传 true 时状态跨调用累积，传 false 时完全不 checkpoint、像普通函数调用，默认则继承父图的 checkpointer。把逻辑做成 Graph node 时，checkpoint 跟着它所在的 super-step 走，恢复从该节点开始，前面的节点不会重跑。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体缺少：
- 关于「把一段逻辑做成普通图节点」时 checkpoint 行为（是否继承父图 checkpointer、是否单独产生 checkpoint、状态如何合并）的说明。
- 子图与普通节点在 checkpoint 粒度/命名空间上的对比说明。

现有片段只覆盖了子图自身的三种持久化模式（Per-invocation / Per-thread / Stateless）[1]，以及 checkpointing 的一般作用（保存状态以便恢复、线程级短期记忆）[3][5]，没有与「普通图节点」做 checkpoint 层面的对照，因此无法给出结论。
--- 片段[1] oss__javascript__langgraph__use-subgraphs#024 ---
| Mode | checkpointer= | Behavior |

| --- | --- | --- |

| Per-invocation | None (default) | Each call starts fresh and inherits the parent’s checkpointer to support interrupts and durable execution within a single call. |

| Per-thread | True | State accumulates across calls on the same thread. Each call picks up where the last one left off. |

| Stateless | False | No checkpointing at all—runs like a plain function call. No interrupts or durable execution. |
--- 片段[2] oss__python__langgraph__use-subgraphs#020 ---
| Mode | checkpointer= | Behavior |

| --- | --- | --- |

| Per-invocation | None (default) | Each call starts fresh and inherits the parent’s checkpointer to support interrupts and durable execution within a single call. |

| Per-thread | True | State accumulates across calls on the same thread. Each call picks up where the last one left off. |

| Stateless | False | No checkpointing at all—runs like a plain function call. No interrupts or durable execution. |
--- 片段[3] oss__javascript__langgraph__interrupts#000 ---
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
--- 片段[4] oss__python__langgraph__interrupts#000 ---
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
--- 片段[5] oss__javascript__langgraph__persistence#001 ---
- Checkpointers persist a thread’s graph state as checkpoints. Use them for short-term, thread-scoped memory, including conversation continuity, human-in-the-loop workflows, time travel, and fault tolerance.

### 69. v1-C-019 [multi-hop] score=0.0
Q: skills 这种多 Agent 模式里，单个 Agent 怎么保持控制权？skills 还能不能嵌套？
GOLD: skills 模式下不会把控制权交给别的 Agent：单个 Agent 始终在控制，只是按需加载 specialized prompts 和知识。而且 skills 可以在树状结构里定义其他 skills，形成 hierarchical skills，例如加载 data_science 这个 skill 会带出 pandas_expert、visualization、statistical_analysis 等子 skill，每个都能独立按需加载。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：
- 关于「多 Agent 模式下单个 Agent 如何保持控制权」：片段 [1]–[5] 均未涉及控制权、多 Agent 协作或调度机制。
- 关于「skills 能否嵌套」：片段 [1]–[5] 均未提及 skill 的嵌套能力。

片段中与 skills 相关的内容仅有：
- 排查「skill 未激活」时，建议减少 skill 之间的描述重叠，避免 Agent 跳过正确的 skill 或选错 [1][2]。
- skill 的工具是「门控」的：在 Agent 读取该 skill 的 `SKILL.md` 之前，调用其工具会作为未知工具失败，即使模型猜到了名称和参数 [3][4]。
- 一个 `create_deep_agent` 的配置示例，通过 `skills=["/skills/"]` 指定 skills 目录 [5]。

如果你能提供涉及多 Agent 控制权或 skill 嵌套的文档片段，我可以据此再回答。
--- 片段[1] oss__javascript__deepagents__skills#121 ---
2. Reduce overlap between skills. If multiple skills have similar descriptions, the agent may skip the right one or pick the wrong one. Differentiate descriptions or consolidate related skills .
--- 片段[2] oss__python__deepagents__skills#120 ---
2. Reduce overlap between skills. If multiple skills have similar descriptions, the agent may skip the right one or pick the wrong one. Differentiate descriptions or consolidate related skills .
--- 片段[3] oss__python__deepagents__skills#022 ---
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
--- 片段[4] oss__javascript__deepagents__skills#022 ---
- Skill tools are gated. Until the agent reads the skill’s SKILL.md , a call to one fails as an unknown tool, even if the model guesses its name and arguments.
--- 片段[5] oss__python__deepagents__context-engineering#019 ---
```

agent = create_deep_agent(

    model="anthropic:claude-sonnet-5",

    skills=["/skills/"],

)

```

### 70. v1-C-020 [paraphrase] score=0.0
Q: Agent 准备执行删库操作，我怎么让整条流程卡在这儿、等我点头之后才真的跑？
GOLD: 在 interrupt 配置里用 descriptionPrefix 给出统一的中断提示文案，单个 tool 还能用自己的 description 覆盖它；要让流程真的停住还必须配 checkpointer。原文注明 Human-in-the-loop requires checkpointing to handle interrupts，生产环境要用 AsyncPostgresSaver 或 MongoDBSaver 这类 persistent checkpointer，而不是示例里的 MemorySaver。
ANSWER: 给出的文档里没有找到能直接回答「删库操作前暂停等待人工批准」这一完整场景的内容，但片段里确实有可复用的「中断 + 恢复」机制，下面只基于片段说明。

**结论：**

1. 要让流程暂停等待人工批准，需要一个 checkpointer（持久化），并且恢复时必须使用同一个 `thread_id`。片段 [1] 明确写了 “Human-in-the-loop requires a thread ID for persistence”，并用相同 `config`（同一 `thread_id`）来 resume 暂停的对话 [1]。

2. 恢复时通过 `Command(resume=...)` 传入决定，决定里用 `{"type": "approve"}` 表示批准 [1]。片段 [3] 还展示了按 interrupt 的 `id` 逐条给出决定，并且可以用 `{"type": "reject", "message": "..."}` 拒绝并附带说明 [3]。

3. 对于「写敏感路径前暂停」这类场景，片段 [2][4] 展示了用 `FilesystemPermission(operations=["write"], paths=["/secrets/**"], mode="interrupt")` 配合 checkpointer 实现暂停等待批准 [2][4]。注意：这是文件系统写权限的中断，片段里**没有**出现「删库 / 数据库删除」相关的权限或工具配置，所以不能据此断言删库操作也走同一配置。

**最小可用示例（基于片段 [1] 的 Python 形式）：**

```python
# Human-in-the-loop requires a thread ID for persistence
config = {"configurable": {"thread_id": "some_id"}}

# Agent will pause and wait for approval before executing sensitive tools
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Send an email to the team"}]},
    config=config,
)

# Same thread ID to resume the paused conversation
result = agent.invoke(
    Command(resume={"decisions": [{"type": "approve"}]}),
    config=config,
)
```

**与你的说法可能不一致之处：**

- 片段 [1] 的示例是「发送邮件」这类敏感工具，不是删库；片段中没有出现「删库」或数据库删除工具的具体名称/参数，因此无法确认你的删库工具是否会自动触发中断。
- 片段 [2][4] 的中断配置针对的是 `FilesystemPermission` 的 `write` 操作与 `/secrets/**` 路径 [2][4]，与数据库删除无关。

**缺失的信息：** 片段里没有说明「如何让某个具体的删库工具进入 interrupt 模式」的配置方式（例如该工具是否属于 sensitive tools、如何声明），也没有删库场景的示例。要回答你的问题，需要补充关于工具级中断/审批配置的文档内容。
--- 片段[1] oss__python__langchain__guardrails#005 ---
ySaver(), ) # Human-in-the-loop requires a thread ID for persistence config = {"configurable": {"thread_id": "some_id"}} # Agent will pause and wait for approval before executing sensitive tools result = agent.invoke( {"messages": [{"role": "user", "content": "Send an email to the team"}]}, config=config ) result = agent.invoke( Command(resume={"decisions": [{"type": "approve"}]}), config=config  # Same thread ID to resume the paused conversation ) ```
--- 片段[2] oss__python__deepagents__human-in-the-loop#043 ---
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
--- 片段[3] oss__javascript__langchain__human-in-the-loop#030 ---
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
--- 片段[4] oss__python__deepagents__permissions#003 ---
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
--- 片段[5] oss__python__langchain__mcp__tools#015 ---
= await adapter.list_tools() # Resuming a paused run needs persistence, so the interrupted run has # somewhere to wait. agent = create_agent("claude-sonnet-5", tools, checkpointer=InMemorySaver()) config: Any = {"configurable": {"thread_id": "booking-1"}} paused = await agent.ainvoke( {"messages": [{"role": "user", "content": "Book a table for 4."}]}, config ) [interrupt] = paused["__interrupt__"] [question] = interrupt.value["requests"] # Answers are keyed by the server's own request key, so nothing has to # be tracked across the pause. `decline` or `cancel` would refuse. answer = {"action": "accept", "content": {"date": "2026-09-14"}} return await agent.ainvoke(

### 71. v1-C-021 [paraphrase] score=0.0
Q: 我想把对话退回三步之前的某个状态，从那儿改一句话再往下跑，SDK 里靠什么实现？
GOLD: 用 getStateHistory() 拿到某个 checkpoint 的 snapshot，再调 await graph.invoke(null, snapshot.config)，它会基于那个 checkpoint 之后重新执行节点，这就是 replay history 的用法。
ANSWER: 给出的文档里没有找到能完整回答这个问题的内容。

片段 [1] 确实展示了「回到某个历史状态 → 修改状态 → 从该点重新运行」的流程（用 `StateHistory` 取历史、`graph.updateState` 分叉、再 `graph.invoke` 重跑），但它属于 **JavaScript/TypeScript 版 LangGraph** 的 time travel 文档，且片段是截断的代码，没有给出完整的 API 说明。而问题问的是「SDK 里靠什么实现」，如果你指的是 Python SDK，片段里没有任何 Python 版的 time travel / 状态回退 API 说明。

具体缺失的内容：
- 没有 Python 版对应的历史状态查询、状态更新（分叉）、从指定 checkpoint 重跑的 API 名称与用法。
- 片段 [1] 只出现了 `StateHistory`、`updateState`、`invoke(null, config)`、`Command({ resume: ... })` 等 JS 写法，且上下文不完整，无法据此给出可靠的最小示例。

另外提示一处可能的名称差异：片段 [1] 中出现的是 `StateHistory(config)` 和 `graph.updateState(...)`（JS 风格），若你预期的是其他命名（如 `get_state_history` 之类），片段中并未出现，无法确认。

如果你能提供 Python 版 time travel 相关文档片段，我可以据此给出结论和最小示例。
--- 片段[1] oss__javascript__langgraph__use-time-travel#010 ---
StateHistory(config)) { states.push(state); } const beforeAsk = states.filter((s) => s.next.includes("askHuman")).pop(); const replayResult = await graph.invoke(null, beforeAsk.config); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Fork from before askHuman const forkConfig = await graph.updateState(beforeAsk.config, { value: ["forked"] }); const forkResult = await graph.invoke(null, forkConfig); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Resume the forked interrupt with a different answer await graph.invoke(new Command({ resume: "Bob" }), forkConfig); // Result: { value: ["forked", "Hello, Bob!", "Done"] } ```
--- 片段[2] oss__python__langchain__middleware__custom#037 ---
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
--- 片段[3] oss__python__langchain__context-engineering#018 ---
- Use life-cycle hooks like before_model , after_model , or wrap_tool_call (for tool returns) to update the conversation history. See the middleware documentation for more details.
--- 片段[4] oss__python__langchain__middleware__custom#036 ---
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
--- 片段[5] oss__python__langchain__short-term-memory#038 ---
window.""" messages = state["messages"] if len(messages) <= 3: return None  # No changes needed first_msg = messages[0] recent_messages = messages[-3:] if len(messages) % 2 == 0 else messages[-4:] new_messages = [first_msg] + recent_messages return { "messages": [ RemoveMessage(id=REMOVE_ALL_MESSAGES), *new_messages ] } agent = create_agent( "gpt-5-nano", tools=[], middleware=[trim_messages], checkpointer=InMemorySaver() ) config: RunnableConfig = {"configurable": {"thread_id": "1"}} agent.invoke({"messages": "hi, my name is bob"}, config) agent.invoke({"messages": "write a short poem about cats"}, config) agent.invoke({"messages": "now do the same but for dogs"}, config)

### 72. v1-C-022 [paraphrase] score=1.0
Q: 检索出来的段落老是半句话就断了、前后文接不上，调哪些参数比较对症？
GOLD: 如果返回的片段缺上下文、答不出问题，就增大 chunk size 或 overlap；如果是相关概念被切到两个 chunk 里，就增加 overlap，或者按文档结构切分。反过来，返回的长 chunk 里塞满无关文本时应该减小 chunk size。
ANSWER: **结论：** 检索结果“半句话就断、前后文接不上”，文档给出的对症调整是**增大 chunk size 或 overlap**；如果问题是“相关想法被切到两个 chunk 里”，则**增大 overlap，或按结构切分** [1][2]。

文档里的对照表如下（Python 与 JS 文档内容一致）：

| 检索表现 | 调整方式 |
| --- | --- |
| 返回的片段缺少回答所需的上下文 | 增大 chunk size 或 overlap [1][2] |
| 返回的长 chunk 里塞满无关文本 | 减小 chunk size [1][2] |
| 把相关的想法切分到两个 chunk 中 | 增大 overlap，或按结构切分 [1][2] |

**最小可用示例（示意，参数名以你实际使用的 splitter 为准）：**

```python
# 针对“片段缺上下文 / 半句断开”：增大 chunk_size 和 chunk_overlap
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,      # 比原来更大
    chunk_overlap=200,    # 比原来更大
)
```

```javascript
// 针对“相关想法被切成两块”：增大 overlap，或按结构切分
const splitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1200,
  chunkOverlap: 200,
});
```

**需要说明的差异/限制：**
- 片段 [1][2] 只给出了“调整方向”（增大/减小 chunk size 或 overlap、按结构切分），**没有给出具体参数名、默认值或推荐数值**；上面的 `chunk_size` / `chunk_overlap` / `chunkSize` / `chunkOverlap` 是示例写法，文档片段中并未出现这些参数名，请以你所用 splitter 的实际 API 为准。
- 片段 [3][4] 讲的是 subagent 返回结果过于冗长导致上下文膨胀时，让子代理只返回精简摘要（如限制在 500 词以内），**与 chunk 切分参数无关**，不适用于本问题。
- 片段 [5] 是 OpenUI 渐进渲染相关代码，**与检索切分无关**。
--- 片段[1] oss__python__langchain__chunking#003 ---
| If retrieval | Adjust |

| --- | --- |

| Returns fragments that lack context to answer | Increase chunk size or overlap |

| Returns long chunks padded with irrelevant text | Decrease chunk size |

| Cuts related ideas across two chunks | Increase overlap, or split on structure |
--- 片段[2] oss__javascript__langchain__chunking#003 ---
| If retrieval | Adjust |

| --- | --- |

| Returns fragments that lack context to answer | Increase chunk size or overlap |

| Returns long chunks padded with irrelevant text | Decrease chunk size |

| Cuts related ideas across two chunks | Increase overlap, or split on structure |
--- 片段[3] oss__python__deepagents__subagents#138 ---
1. Instruct subagent to return concise results: system_prompt = """... IMPORTANT: Return only the essential summary. Do NOT include raw data, intermediate search results, or detailed tool outputs. Your response should be under 500 words."""
--- 片段[4] oss__javascript__deepagents__subagents#160 ---
1. Instruct subagent to return concise results: const systemPrompt = `... IMPORTANT: Return only the essential summary. Do NOT include raw data, intermediate search results, or detailed tool outputs. Your response should be under 500 words.` ;
--- 片段[5] oss__python__langchain__frontend__integrations__openui#026 ---
^([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)?.[1]; const stripped = line.replace(/"(?:[^"\\]|\\.)*"/g, '""'); for (const v of defs) { if (v !== thisVar && new RegExp(`\\b${v}\\b`).test(stripped)) referenced.add(v); } } const topLevel = defs.filter((v) => !referenced.has(v)); const rootVars = topLevel.length > 0 ? topLevel : defs; return `${safe.trimEnd()}\nroot = Stack([${rootVars.join(", ")}], "column", "l")`; } /** * Gate Renderer updates to moments when at least one new *complete* statement * has arrived. This eliminates hundreds of no-op re-parses during streaming. * * Special case: TextContent lines update token-by-token (via closeOrTruncate)

### 73. v1-C-023 [paraphrase] score=0.0
Q: 做一个能打电话点三明治的语音助手，一次请求要经过哪几段处理？
GOLD: 整条 pipeline 分三步：STT 把音频转给语音转文字供应商（例如 AssemblyAI）拿回 transcript；LangChain agent 处理 transcript 并流式输出回复 token；最后 TTS 把回复交给语音合成供应商（例如 Cartesia）拿回音频块。
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

现有片段只包含多智能体模式的性能对比表（调用次数/token 数）[1][2]、Router 重复请求的一次调用链示例 [3]，以及子图（subgraph）消息累积的示例 [4][5]。这些都没有描述「语音助手打电话点三明治」所需的语音链路环节（如语音识别、对话/工具调用、语音合成等），也没有任何关于电话/语音接口的说明。

缺失的内容：语音助手的端到端处理流程（ASR → agent/工具调用 → TTS 等）以及电话集成方式。
--- 片段[1] oss__python__langchain__multi-agent#014 ---
| Pattern | One-shot | Repeat request | Multi-domain |

| --- | --- | --- | --- |

| Subagents | 4 calls | 8 calls (4+4) | 5 calls, 9K tokens |

| Handoffs | 3 calls | 5 calls (3+2) | 7+ calls, 14K+ tokens |

| Skills | 3 calls | 5 calls (3+2) | 3 calls, 15K tokens |

| Router | 3 calls | 6 calls (3+3) | 5 calls, 9K tokens |
--- 片段[2] oss__javascript__langchain__multi-agent#014 ---
| Pattern | One-shot | Repeat request | Multi-domain |

| --- | --- | --- | --- |

| Subagents | 4 calls | 8 calls (4+4) | 5 calls, 9K tokens |

| Handoffs | 3 calls | 5 calls (3+2) | 7+ calls, 14K+ tokens |

| Skills | 3 calls | 5 calls (3+2) | 3 calls, 15K tokens |

| Router | 3 calls | 6 calls (3+3) | 5 calls, 9K tokens |
--- 片段[3] oss__python__langchain__multi-agent#012 ---
- Turn 2: Router LLM call (1) → Milk agent calls buy_coffee (2) → Milk agent responds (3)
--- 片段[4] oss__python__langgraph__use-subgraphs#035 ---
gie_agent", tools=[veggie_info], system_prompt="...", checkpointer=True, ) config = {"configurable": {"thread_id": "1"}} # First call - LLM calls both fruit and veggie experts response = agent.invoke( {"messages": [{"role": "user", "content": "Tell me about cherries and broccoli"}]}, config=config, ) # Fruit subagent message count: 4 # Veggie subagent message count: 4 # Second call - both agents accumulate independently response = agent.invoke( {"messages": [{"role": "user", "content": "Now tell me about oranges and carrots"}]}, config=config, ) # Fruit subagent message count: 8 (remembers cherries!) # Veggie subagent message count: 8 (remembers broccoli!) ```
--- 片段[5] oss__python__langgraph__use-subgraphs#033 ---
```

config = {"configurable": {"thread_id": "1"}}



# First call

response = agent.invoke(

    {"messages": [{"role": "user", "content": "Tell me about apples"}]},

    config=config,

)

# Subagent message count: 4



# Second call - subagent REMEMBERS apples conversation

response = agent.invoke(

    {"messages": [{"role": "user", "content": "Now tell me about bananas"}]},

    config=config,

)

# Subagent message count: 8 (accumulated!)

```

### 74. v1-C-024 [no-answer] score=None
Q: DSPy 的 BootstrapFewShot 优化器默认会编译几轮？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。所有片段都没有提到 DSPy，也没有提到 BootstrapFewShot 优化器或其编译轮数，因此无法根据这些片段回答。
--- 片段[1] oss__javascript__concepts__human-in-the-loop#014 ---
|  | Per-call | Batched (default) |

| --- | --- | --- |

| When it pauses | As each gated tool call starts | After the model responds, before any tool runs |

| Interrupts per turn | One per gated tool call | One for the whole turn |

| Ungated calls in the turn | Run right away | Wait for the review |

| Answer | One decision per interrupt, keyed by interrupt ID | A list of decisions, matched by position |

| Best for | New agents, one approval card or message per call, forms built from the schema | Approval UIs that already read actionRequests |
--- 片段[2] oss__javascript__langchain__frontend__integrations__openui#026 ---
^([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)?.[1]; const stripped = line.replace(/"(?:[^"\\]|\\.)*"/g, '""'); for (const v of defs) { if (v !== thisVar && new RegExp(`\\b${v}\\b`).test(stripped)) referenced.add(v); } } const topLevel = defs.filter((v) => !referenced.has(v)); const rootVars = topLevel.length > 0 ? topLevel : defs; return `${safe.trimEnd()}\nroot = Stack([${rootVars.join(", ")}], "column", "l")`; } /** * Gate Renderer updates to moments when at least one new *complete* statement * has arrived. This eliminates hundreds of no-op re-parses during streaming. * * Special case: TextContent lines update token-by-token (via closeOrTruncate)
--- 片段[3] oss__python__langchain__frontend__integrations__openui#026 ---
^([a-zA-Z_][a-zA-Z0-9_]*)\s*=/)?.[1]; const stripped = line.replace(/"(?:[^"\\]|\\.)*"/g, '""'); for (const v of defs) { if (v !== thisVar && new RegExp(`\\b${v}\\b`).test(stripped)) referenced.add(v); } } const topLevel = defs.filter((v) => !referenced.has(v)); const rootVars = topLevel.length > 0 ? topLevel : defs; return `${safe.trimEnd()}\nroot = Stack([${rootVars.join(", ")}], "column", "l")`; } /** * Gate Renderer updates to moments when at least one new *complete* statement * has arrived. This eliminates hundreds of no-op re-parses during streaming. * * Special case: TextContent lines update token-by-token (via closeOrTruncate)
--- 片段[4] oss__javascript__concepts__human-in-the-loop#011 ---
| In batched mode | What happens | In per-call mode | | --- | --- | --- | | Decisions match calls by position | A reviewer means to approve write_file and reject execute_sql , but sends [reject, approve] . The rejection goes to write_file . | Each decision is keyed by its call’s interrupt ID. | | Allowed decisions live in reviewConfigs | Clients pair two lists by position and hardcode a button for each decision type. | Each interrupt’s response_schema lists its decisions and edit arguments. | | An answer is saved before it is checked | One decision for two calls throws Error: Number of human decisions (1) does not match number of hanging tool calls (2).
--- 片段[5] oss__javascript__deepagents__sandboxes#009 ---
eTtlSeconds: 3600, // TTL: clean up when idle })); return createDeepAgent({ model: "anthropic:claude-sonnet-5", backend: new LangSmithSandbox({ sandbox: lsSandbox }), }); } ```

### 75. v1-C-025 [no-answer] score=None
Q: LangChain JS SDK 的 createSupervisorAgent 是从哪个包导出的？
GOLD: 本题无答案
ANSWER: 给出的文档里没有找到能回答这个问题的内容。

片段中没有出现 `createSupervisorAgent` 这个 API，也没有说明它从哪个包导出。现有片段只涉及：

- 从 `langgraph-supervisor` 包迁移到 `create_agent` + 工具包装子代理的模式 [1]
- 使用 `deepagents` 的 `createDeepAgent`，以及通过 `@langchain/langgraph-sdk` 的 `Client` 查询子代理线程 [2][3][4][5]

缺少的内容是：关于 `createSupervisorAgent` 的导出包信息（例如 import 语句或包名说明）。另外需指出：你问的是 `createSupervisorAgent`，但片段里出现的相关 API 是 `createDeepAgent`（来自 `deepagents`）[2][3][4][5]，二者名称不一致，请以片段为准。
--- 片段[1] oss__python__migrate__langgraph-supervisor#000 ---
Migrate from langgraph-supervisor Migrate from the langgraph-supervisor package to the subagents pattern with create_agent and tool-wrapped subagents.
--- 片段[2] oss__javascript__deepagents__async-subagents#022 ---
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
--- 片段[3] oss__javascript__deepagents__async-subagents#026 ---
``` import { Client } from "@langchain/langgraph-sdk"; import type { LangGraphRunnableConfig } from "@langchain/langgraph"; import { createDeepAgent } from "deepagents"; async function findSubagentThreads(parentThreadId: string) { const client = new Client(); return client.threads.search({ metadata: { parent_thread_id: parentThreadId } }); } function researcher(config: LangGraphRunnableConfig) { // Set when a supervisor launched this run with `start_async_task` const parentThreadId = config.metadata?.parent_thread_id; return createDeepAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", systemPrompt: "You research topics thoroughly.", }); } ```
--- 片段[4] oss__javascript__deepagents__async-subagents#025 ---
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
--- 片段[5] oss__javascript__deepagents__async-subagents#023 ---
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
