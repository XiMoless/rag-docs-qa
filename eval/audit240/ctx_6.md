# 审计材料 6/8（30 条，明细文件第 151–180 行）

## v2-F-023（paraphrase）

**问题**：图跑到一半停下来等我回答，我该从哪里读出它到底问了什么？回答完又怎么让它接着往下跑？

**gold**：第一次 invoke 返回的是 GraphOutput，里面的 .interrupts 装着传给 interrupt() 的 payload；恢复时再 invoke 一次，传 Command(resume=True)，这个 resume 值会成为节点里 interrupt() 的返回值。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

1. 图暂停后，`interrupt()` 里传入的内容会以 `__interrupt__` 字段返回给调用方，从那里就能读到它到底问了什么 [6]。
2. 如果用流式方式运行，每次 run 结束后检查 `stream.interrupted` / `stream.interrupts` 判断是否暂停，并从 `stream.interrupts` 读取 payload [4][5]。
3. 回答完之后，用 `Command(resume=...)` 作为下一次调用的输入让它继续跑；循环直到某次运行不再中断为止 [13]。Python 写法是 `graph.invoke(Command(resume="Alice"), config)` [8]，JS 写法是 `graph.invoke(new Command({ resume: "Alice" }), config)` [12]。

**最小可用示例（Python）**

```python
from langgraph.types import interrupt, Command

def ask_human(state):
    answer = interrupt("What is your name?")   # 这里的问题会以 __interrupt__ 返回
    return {"value": [f"Hello, {answer}!"]}

config = {"configurable": {"thread_id": "1"}}

# 第一次运行：停在 interrupt
graph.invoke({"value": []}, config)

# 回答后继续
graph.invoke(Command(resume="Alice"), config)
```

**补充说明（来自片段）**

- 恢复后如果还想从暂停点之前重放或分叉，可以用 `graph.get_state_history(config)` 找到 `next` 为对应节点的状态，再用 `graph.update_state(...)` 分叉，然后用 `Command(resume=...)` 恢复分叉后的中断 [1][3][7]。
- 片段中 Python 用 `Command(resume="Alice")`，JS 用 `new Command({ resume: "Alice" })`，两者参数形式不同，注意按语言区分 [8][12]。

**top5 片段**：

片段[1] `oss__python__langgraph__use-time-travel#011` ｜ Use time-travel ｜ Interrupts

```text
{"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human history = list(graph.get_state_history(config)) before_ask = [s for s in history if s.next == ("ask_human",)][-1] replay_result = graph.invoke(None, before_ask.config) # Pauses at interrupt — waiting for new Command(resume=...) # Fork from before ask_human fork_config = graph.update_state(before_ask.config, {"value": ["forked"]}) fork_result = graph.invoke(None, fork_config) # Pauses at interrupt — waiting for new Command(resume=...) # Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value":
```

片段[2] `oss__python__langgraph__use-time-travel#010` ｜ Use time-travel ｜ Interrupts

```text
``` from langgraph.types import interrupt, Command class State(TypedDict): value: list[str] def ask_human(state: State): answer = interrupt("What is your name?") return {"value": [f"Hello, {answer}!"]} def final_step(state: State): return {"value": ["Done"]} graph = ( StateGraph(State) .add_node("ask_human", ask_human) .add_node("final_step", final_step) .add_edge(START, "ask_human") .add_edge("ask_human", "final_step") .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # First run: hits interrupt graph.invoke({"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human
```

片段[3] `oss__python__langgraph__use-time-travel#012` ｜ Use time-travel ｜ Interrupts

```text
Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value": ["forked", "Hello, Bob!", "Done"]} ```
```

片段[4] `oss__python__releases__changelog#014` ｜ Changelog ｜ langchain v1.4.0 > Features

```text
- Interrupt-driven elicitation : when a server asks for input mid-call, MCPAdapter surfaces the question as a LangGraph interrupt() , so a human answers and the run resumes. See Elicitation .
```

片段[5] `oss__javascript__langgraph__use-time-travel#010` ｜ Use time-travel ｜ Interrupts

```text
StateHistory(config)) { states.push(state); } const beforeAsk = states.filter((s) => s.next.includes("askHuman")).pop(); const replayResult = await graph.invoke(null, beforeAsk.config); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Fork from before askHuman const forkConfig = await graph.updateState(beforeAsk.config, { value: ["forked"] }); const forkResult = await graph.invoke(null, forkConfig); // Pauses at interrupt — waiting for new Command({ resume: ... }) // Resume the forked interrupt with a different answer await graph.invoke(new Command({ resume: "Bob" }), forkConfig); // Result: { value: ["forked", "Hello, Bob!", "Done"] } ```
```

---

## v2-F-024（paraphrase）

**问题**：线上那些用来恢复对话的历史记录越攒越多、占满磁盘，官方在常见问题里建议怎么处理？

**gold**：先用 PostgresSaver.from_conn_string 拿到 checkpointer 并调用 setup()，它会建好带索引的表；然后考虑加一个 cron job，定期删掉 N 天以前的 checkpoints。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：现有片段只说明 Deep Agents 会把内部数据（卸载的工具结果、对话历史）写入默认后端，并建议用 StateBackend 作为默认后端让这些产物保持临时性、避免写入磁盘或持久化存储 [1][2]；片段 [3]–[8] 是后台记忆整合（consolidation agent）的示例代码，[9][10] 是自定义后端协议与 StoreBackend 路由的说明。没有任何片段涉及「线上历史记录越攒越多、占满磁盘」这一常见问题，也没有给出对应的清理/归档/保留策略建议。因此无法据此回答，也不做推测。

**top5 片段**：

片段[1] `oss__python__deepagents__backends#087` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[2] `oss__javascript__deepagents__backends#072` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[3] `oss__python__deepagents__memory#028` ｜ Memory ｜ Advanced usage > Background consolidation > Consolidation agent

```text
ata={"user_id": user_id}, sort_by="updated_at", sort_order="desc", limit=20, ) conversations = [] for thread in threads: if datetime.fromisoformat(thread["updated_at"]) < since: break state = await sdk_client.threads.get_state(thread_id=thread["thread_id"]) conversations.append(state["values"]["messages"]) return str(conversations) agent = create_deep_agent( model="fireworks:accounts/fireworks/models/glm-5p2", system_prompt="""Review recent conversations and update the user's memory file. Merge new facts, remove outdated information, and keep it concise.""", tools=[search_recent_conversations], ) ```
```

片段[4] `oss__python__deepagents__memory#026` ｜ Memory ｜ Advanced usage > Background consolidation > Consolidation agent

```text
ata={"user_id": user_id}, sort_by="updated_at", sort_order="desc", limit=20, ) conversations = [] for thread in threads: if datetime.fromisoformat(thread["updated_at"]) < since: break state = await sdk_client.threads.get_state(thread_id=thread["thread_id"]) conversations.append(state["values"]["messages"]) return str(conversations) agent = create_deep_agent( model="openrouter:z-ai/glm-5.2", system_prompt="""Review recent conversations and update the user's memory file. Merge new facts, remove outdated information, and keep it concise.""", tools=[search_recent_conversations], ) ```
```

片段[5] `oss__python__deepagents__memory#020` ｜ Memory ｜ Advanced usage > Background consolidation > Consolidation agent

```text
ata={"user_id": user_id}, sort_by="updated_at", sort_order="desc", limit=20, ) conversations = [] for thread in threads: if datetime.fromisoformat(thread["updated_at"]) < since: break state = await sdk_client.threads.get_state(thread_id=thread["thread_id"]) conversations.append(state["values"]["messages"]) return str(conversations) agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", system_prompt="""Review recent conversations and update the user's memory file. Merge new facts, remove outdated information, and keep it concise.""", tools=[search_recent_conversations], ) ```
```

---

## v2-F-025（paraphrase）

**问题**：想让 agent 每次回答都遵守我们团队写好的做事规矩，这些规矩该存在哪、每次调用模型前又怎么取出来用？

**gold**：把规矩当成 instructions 存进 store：用 store.get(namespace, key='agent_a') 取出条目，再把 instructions.value['instructions'] 填进 prompt_template；更新侧用 store.search(namespace) 找到现有条目，让 LLM 结合对话产出 new_instructions 再写回。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答这个问题的内容。

具体缺什么：

1. **“团队做事规矩”该存在哪**：片段 [6] 只展示了用 `StoreBackend` + `memory=["/AGENTS.md"]` 把 `AGENTS.md` 作为记忆文件挂载的写法，但它是 deepagents 的 Memory 机制示例，片段没有说明这就是“团队规矩”的推荐存放位置，也没有对比其他存放方式（如 skills、middleware 常量等）。片段 [1][2] 提到 skills 会在“agent 读取 skill 后每次模型调用时运行”，但同样没有说明规矩应写成 skill 还是 memory。

2. **每次调用模型前怎么取出来用**：片段 [3] 展示了一个 middleware（`inject_compliance_rules`）在请求末尾追加合规规则消息、并通过 `request.override(messages=...)` 注入的做法，这是最接近“每次调用模型前注入规矩”的示例；但它讲的是合规规则注入的上下文工程，并未说明如何与团队规矩文件（如 AGENTS.md）结合读取。片段 [4][5] 只是中间件清单条目（如 BastionGuardrailMiddleware、TurnWindowMiddleware 等），没有给出“读取团队规矩并在每次模型调用前注入”的具体实现。

另外需要指出的差异/注意点：
- 片段 [3] 中模型名写作 `"gpt-6.1-sol"`，片段 [6] 写作 `"fireworks:accounts/fireworks/models/glm-5p2"`，片段 [9] 写作 `"anthropic:claude-sonnet-4-6"`，这些是各示例自带的模型标识，不能据此推断你环境中的可用模型名。
- 片段 [1][2] 的原文是 “Keep it fast. It runs on every model call after the agent reads the skill, and again before each skill tool call.”，描述的是某个钩子的执行时机，片段未给出该钩子的名称与签名，无法据此写出可运行代码。

如果你能补充“团队规矩”是希望以文件（AGENTS.md）、skill 还是 middleware 形式管理，以及使用的是 Python 还是 JavaScript 版本，我可以基于对应片段再给最小示例。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#029` ｜ Skills ｜ View example trace

```text
- Keep it fast. It runs on every model call after the agent reads the skill, and again before each skill tool call.
```

片段[2] `oss__python__deepagents__skills#029` ｜ Skills ｜ Add tools to skills > Resolve tools at runtime

```text
- Keep it fast. It runs on every model call after the agent reads the skill, and again before each skill tool call.
```

片段[3] `oss__python__langchain__context-engineering#016` ｜ Context engineering in agents ｜ Response Format > Messages

```text
ation") if industry == "finance": rules.append("- Cannot provide financial advice without proper disclaimers") if rules: compliance_context = f"""Compliance requirements for {jurisdiction}: {chr(10).join(rules)}""" # Append at end - models pay more attention to final messages messages = [ *request.messages, {"role": "user", "content": compliance_context} ] request = request.override(messages=messages) return handler(request) agent = create_agent( model="gpt-6.1-sol", tools=[...], middleware=[inject_compliance_rules], context_schema=Context ) ```
```

片段[4] `oss__python__integrations__middleware#015` ｜ Middleware integrations ｜ All middleware

```text
scoping, dynamic prompt injection, and composable completion validation. | edvinhallvaxhiu/langchain-task-steering |  | | TurnWindowMiddleware | Cross-provider LangChain agent middleware that retains the most recent human-anchored conversation turns before each model call while keeping tool-call and tool-result messages together. | bharatkhanna-dev/langchain-turn-window |  | | BastionGuardrailMiddleware | Prompt-injection and jailbreak detection. Screens user input and tool results, including indirect injection through retrieved content, before the model runs. Runs locally on your own hardware. | bastion-soft/bastion-prompt-protection |  |
```

片段[5] `oss__python__integrations__middleware#030` ｜ Middleware integrations ｜ All middleware

```text
| ATR Guardrail | Runtime detection of prompt injection, tool poisoning, and unsafe tool calls using Agent Threat Rules. Halts the agent or blocks the tool call on a critical finding and keeps an audit trail. | Agent-Threat-Rule/agent-threat-rules | N/A | | BhivedMiddleware | Recalls shared lessons from the bhived network before model calls and adds tools to write verified lessons back. | ArtKeyAi/bhived-python | N/A | | eager-tools | Reduces agent wall-clock latency by dispatching each tool call the moment its streaming block closes, overlapping tool execution with LLM generation. | cloudthinker-ai/eager-tools | N/A |
```

---

## v2-F-026（paraphrase）

**问题**：服务要发版重启，正在跑的图会被硬中断吗？怎么才能停在安全的地方、之后还能接着跑？

**gold**：按 drain 语义表，正在执行的节点会跑完，drain 到下一个 superstep 才生效；如果还有 superstep 要跑，会抛 GraphDrained(reason)，同时保存检查点、之后可以恢复。正在重试的节点会把重试跑到成功或耗尽，drain 在其后生效；子图请求 drain 会向上冒泡，在父图自己的下一个 superstep 边界停下。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：不会（也不应该）被硬中断——LangGraph 提供了「优雅停机（Graceful shutdown）」机制：在**当前 superstep 执行完之后**协作式地停下来，并保存一个可恢复的 checkpoint，之后用同样的 config 就能接着跑 [5][10]。

要点：
- 用 `RunControl` 创建控制器，调用 `request_drain()` 请求停机；运行中的图会抛出 `GraphDrained`，checkpoint 已保存、可恢复 [5][6]。
- 停机语义：节点执行到一半会**跑完**，drain 在下一个 superstep 生效；正在重试的节点会重试到成功或耗尽后再生效；若同一 tick 图自然结束则正常返回（可用 `control.drainRequested` 区分）；若还有 superstep 则抛 `GraphDrained(reason)` 并保存可恢复 checkpoint；子图请求 drain 会向上冒泡到父图的下一个 superstep 边界停止 [10]。
- 典型做法是把 `request_drain` 挂在 SIGTERM 信号处理里，捕获 `GraphDrained` 后记录日志，下次启动用相同 config 恢复 [6][3]。

最小可用示例（Python，SIGTERM 钩子）[6]：

```python
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

JavaScript 版本同理（`RunControl` + `GraphDrained`，`control.requestDrain("sigterm")`）[3]。

补充说明（与问题相关的差异/边界）：
- 片段里 Python 的 API 是 `request_drain()`（下划线），JS 是 `requestDrain()`（驼峰），注意别混用 [5][3]。
- 这套机制解决的是「停机后能续跑」；如果你说的「停在安全的地方」是指**等人审批**，那是另一套 `interrupt()` / `Command(resume=...)` 机制（含多中断并行恢复），与优雅停机不是同一件事 [4][1][7]。

**top5 片段**：

片段[1] `oss__python__langgraph__interrupts#028` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
dge("a", END) .add_edge("b", END) .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Step 1: stream events to drive the run; both parallel nodes hit interrupt() and pause stream = graph.stream_events({"vals": []}, config, version="v3") _ = stream.output  # drive the stream to completion # stream.interrupts contains the pending Interrupt payloads print(stream.interrupts) # > (Interrupt(value='question_a', id='...'), Interrupt(value='question_b', id='...')) # Step 2: resume all pending interrupts at once resume_map = { i.id: f"answer for {i.value}" for i in stream.interrupts } resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")
```

片段[2] `oss__javascript__langgraph__fault-tolerance#041` ｜ Fault tolerance ｜ Graceful shutdown

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

片段[4] `oss__javascript__langgraph__interrupts#009` ｜ Interrupts ｜ Resuming interrupts

```text
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
```

片段[5] `oss__python__releases__changelog#033` ｜ Changelog ｜ langgraph v1.2.0

```text
- Graceful shutdown : Stop an in-flight run cooperatively after the current superstep completes, and save a resumable checkpoint. Create a RunControl and call request_drain() from any thread; the run raises GraphDrained and can be resumed later with the same config.
```

---

## v2-F-027（no-answer）

**问题**：DSPy 里 BootstrapFewShot 优化器的 max_bootstrapped_demos 默认取几？它和 max_labeled_demos 有什么区别？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段中没有任何关于 DSPy、`BootstrapFewShot` 优化器、`max_bootstrapped_demos` 或 `max_labeled_demos` 的说明，因此无法给出默认值，也无法说明两者区别。

补充说明：片段 [1][2][10] 中出现的 `maxResults`（默认 1）是 deep-research 示例里 `tavily_search` 工具的参数，与 DSPy 的 `max_bootstrapped_demos` 无关，不要混淆。

**top5 片段**：

片段[1] `oss__javascript__deepagents__deep-research#035` ｜ Build a deep research agent ｜ Choose your path > Build the agent

```text
maxResults: z .number() .optional() .default(1) .describe("Maximum number of results to return (default: 1)"), topic: z .enum(["general", "news", "finance"]) .optional() .default("general") .describe( "Topic filter - 'general', 'news', or 'finance' (default: 'general')", ), }), }, ); ```
```

片段[2] `oss__javascript__deepagents__deep-research#007` ｜ Build a deep research agent ｜ Choose your path > Build the agent

```text
chema: z.object({ query: z.string().describe("Search query to execute"), maxResults: z .number() .optional() .default(1) .describe("Maximum number of results to return (default: 1)"), topic: z .enum(["general", "news", "finance"]) .optional() .default("general") .describe( "Topic filter - 'general', 'news', or 'finance' (default: 'general')", ), }), }, ); ```
```

片段[3] `oss__python__deepagents__backends#041` ｜ Backends ｜ Built-in backends > LocalShellBackend (local shell)

```text
- Supports timeout (default 120s), max_output_bytes (default 100,000), env , and inherit_env for environment variables.
```

片段[4] `oss__javascript__deepagents__backends#035` ｜ Backends ｜ Built-in backends > LocalShellBackend (local shell)

```text
- Supports timeout (default 120s), max_output_bytes (default 100,000), env , and inherit_env for environment variables.
```

片段[5] `oss__javascript__langchain__models#054` ｜ Models ｜ Advanced topics > Model profiles

```text
```

model.profile;

// {

//   maxInputTokens: 400000,

//   imageInputs: true,

//   reasoningOutput: true,

//   toolCalling: true,

//   ...

// }

```
```

---

## v2-F-028（no-answer）

**问题**：AutoGen 的 GroupChat 里 speaker_selection_method 默认是哪种？怎么改成按轮次轮流发言？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

所有片段都来自 LangChain 文档（涉及动态模型选择、`initChatModel`、`create_agent`、`wrap_model_call` 等），没有任何片段提到 AutoGen、`GroupChat` 或 `speaker_selection_method`。因此无法根据这些片段回答该参数的默认值，也无法给出改为按轮次轮流发言的方法。

缺失的内容是：AutoGen `GroupChat` 的 API 文档，特别是 `speaker_selection_method` 参数的默认值说明，以及按轮次轮流发言（如 `round_robin`）的配置示例。

**top5 片段**：

片段[1] `oss__javascript__langchain__models#072` ｜ Models ｜ Advanced topics > Dynamic model selection

```text
``` import { ChatOpenAI } from "@langchain/openai"; import { createAgent, createMiddleware } from "langchain"; const basicModel = new ChatOpenAI({ model: "gpt-5.4-mini" }); const advancedModel = new ChatOpenAI({ model: "gpt-6.1-sol" }); const dynamicModelSelection = createMiddleware({ name: "DynamicModelSelection", wrapModelCall: (request, handler) => { // Choose model based on conversation complexity const messageCount = request.messages.length; return handler({ ...request, model: messageCount > 10 ? advancedModel : basicModel, }); }, }); const agent = createAgent({ model: "gpt-5.4-mini", // Base model (used when messageCount ≤ 10) tools: [], middleware: [dynamicModelSelection], }); ```
```

片段[2] `oss__python__langchain__models#093` ｜ Models ｜ Advanced topics > Dynamic model selection

```text
``` from langchain_openai import ChatOpenAI from langchain.agents import create_agent from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse basic_model = ChatOpenAI(model="gpt-5.4-mini") advanced_model = ChatOpenAI(model="gpt-6.1-sol") @wrap_model_call def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse: """Choose model based on conversation complexity.""" message_count = len(request.state["messages"]) if message_count > 10: # Use an advanced model for longer conversations model = advanced_model else: model = basic_model return handler(request.override(model=model)) agent = create_agent( model=basic_model,  # Default model tools=[],
```

片段[3] `oss__javascript__langchain__multi-agent__handoffs-customer-support#003` ｜ Build customer support with handoffs ｜ Setup > Select an LLM

```text
```

import { initChatModel } from "langchain";



process.env.ANTHROPIC_API_KEY = "your-api-key";



const model = await initChatModel("claude-sonnet-4-6");

```
```

片段[4] `oss__javascript__langchain__multi-agent__skills-sql-assistant#011` ｜ Build a SQL assistant with on-demand skills ｜ Setup > Select an LLM

```text
```

import { initChatModel } from "langchain";



process.env.ANTHROPIC_API_KEY = "your-api-key";



const model = await initChatModel("claude-sonnet-4-6");

```
```

片段[5] `oss__javascript__langchain__multi-agent__router-knowledge-base#008` ｜ Build a multi-source knowledge base with routing ｜ Setup > Select an LLM

```text
```

import { initChatModel } from "langchain";



process.env.ANTHROPIC_API_KEY = "your-api-key";



const model = await initChatModel("claude-sonnet-4-6");

```
```

---

## v2-G-001（single-hop）

**问题**：节点里写了 `const approved = interrupt("Do you approve this action?")`，之后外部执行 `await graph.invoke(new Command({ resume: true }), config)`，恢复后 approved 拿到的是什么？

**gold**：approved 拿到的是恢复时 Command 中 resume 传入的值。interrupt 在暂停那一刻并不会返回，只有恢复之后这个值才被当作该次 interrupt 调用的返回值赋给 approved。所以节点可以继续执行，并用 return { approved } 把它写回图状态。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 恢复后 `approved` 拿到的是 `true`（即 `Command({ resume: ... })` 里传入的 resume 值），而不是原始字符串 `"Do you approve this action?"`。`interrupt()` 的返回值就是恢复时提供的 resume payload [2][5]。

**最小可用示例（JavaScript）：**

```javascript
import { interrupt, Command } from "@langchain/langgraph";

async function approvalNode(state: State) {
    // 暂停，payload 会出现在 result.__interrupt__ 中
    const approved = interrupt("Do you approve this action?");

    // 恢复时 Command({ resume: true }) 的值会赋给 approved
    return { approved };
}

// 首次运行：命中 interrupt 并暂停
const config = { configurable: { thread_id: "thread-1" } };
const result = await graph.invoke({ input: "data" }, config);
console.log(result.__interrupt__);
// [{ value: 'Do you approve this action?', ... }]

// 恢复：resume 的值成为 interrupt() 的返回值
await graph.invoke(new Command({ resume: true }), config);
// 此时节点内 approved === true
```

**补充说明：**
- 首次运行时，传给 `interrupt()` 的字符串会作为 payload 出现在 `result.__interrupt__` 中（形如 `[{ value: 'Do you approve this action?', ... }]`）[5]。
- 恢复时 `Command({ resume: true })` 中的 `true` 会作为 `interrupt()` 的返回值赋给 `approved` [2][5]。
- 恢复需要依赖 checkpointer 保存的状态，`thread_id` 是指回已保存检查点的持久指针 [5][11]。

**top5 片段**：

片段[1] `oss__python__langgraph__interrupts#005` ｜ Interrupts ｜ Pause using interrupt

```text
```

from langgraph.types import interrupt



def approval_node(state: State):

    # Pause and ask for approval

    approved = interrupt("Do you approve this action?")



    # When you resume, Command(resume=...) returns that value here

    return {"approved": approved}

```
```

片段[2] `oss__javascript__langgraph__interrupts#005` ｜ Interrupts ｜ Pause using interrupt

```text
```

import { interrupt } from "@langchain/langgraph";



async function approvalNode(state: State) {

    // Pause and ask for approval

    const approved = interrupt("Do you approve this action?");



    // Command({ resume: ... }) provides the value returned into this variable

    return { approved };

}

```
```

片段[3] `oss__javascript__langgraph__interrupts#037` ｜ Interrupts ｜ View example trace > Review and edit state

```text
```

await graph.invoke(

  new Command({ resume: "The edited and improved text" }), // Value becomes the return from interrupt()

  config

);

```
```

片段[4] `oss__javascript__langgraph__interrupts#031` ｜ Interrupts ｜ View example trace > Approve or reject

```text
```

import { interrupt, Command } from "@langchain/langgraph";



const approvalNode: typeof State.Node = (state) => {

  // Pause execution; payload surfaces in result.__interrupt__

  const isApproved = interrupt({

    question: "Do you want to proceed?",

    details: state.actionDetails

  });



  // Route based on the response

  if (isApproved) {

    return new Command({ goto: "proceed" }); // Runs after the resume payload is provided

  } else {

    return new Command({ goto: "cancel" });

  }

}

```
```

片段[5] `oss__javascript__langgraph__interrupts#009` ｜ Interrupts ｜ Resuming interrupts

```text
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
```

---

## v2-G-002（single-hop）

**问题**：两个并行节点各自调用 `interrupt()` 之后，第一次 `graph.invoke()` 返回的 `__interrupt__` 是数组；恢复时为什么要把答案整理成一个以 id 为键的对象，再执行 `new Command({ resume: resumeMap })`？

**gold**：两个并行中断各自带独立的 id，恢复时必须按 id 逐个对上号，才能把答案分别送回正确的节点。示例先用 isInterrupted 判断结果里有没有中断，再遍历 interruptedResult[INTERRUPT] 把每个 i.id 作为键、把答案写进 resumeMap。最后 graph.invoke(new Command({ resume: resumeMap }), config) 一次性恢复全部中断，两个节点分别收到自己的答案。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：因为并行节点会同时产生多个待恢复的 interrupt，每个 interrupt 都有自己的 `id`；恢复时需要用「以 interrupt id 为键、答案值为内容」的映射对象一次性恢复全部挂起的 interrupt，而不是只传一个标量答案。片段中明确展示了这种 `resumeMap` 的构造与使用方式 [1][8][9]。

具体来说：

- 第一次 `graph.invoke()` 时，两个并行节点都命中 `interrupt()` 并暂停，返回结果里的 `__interrupt__` 是一个数组，包含多个带 `id` 和 `value` 的条目 [1]。
- 恢复时片段构造了 `resumeMap: Record<string, string>`，遍历 `interruptedResult[INTERRUPT]`，把每个 `i.id` 作为键、`answer for ${i.value}` 作为值填入，然后执行 `new Command({ resume: resumeMap })` [8]。
- 这样做的效果是「resume all pending interrupts at once」（一次性恢复所有挂起的 interrupt）[1][8]，最终状态里两个节点的答案都被正确写回：`{ vals: ['a:answer for question_a', 'b:answer for question_b'] }` [8]。

最小可用示例（JavaScript，摘自片段）：

```javascript
const resumeMap: Record<string, string> = {};
if (isInterrupted(interruptedResult)) {
  for (const i of interruptedResult[INTERRUPT]) {
    if (i.id != null) {
      resumeMap[i.id] = `answer for ${i.value}`;
    }
  }
}
const result = await graph.invoke(new Command({ resume: resumeMap }), config);
```

补充说明（以片段为准的差异点）：

- 片段里 `Command` 的用法是 `new Command({ resume: ... })`（JavaScript）[2][8]，Python 片段则是 `Command(resume=...)` [3][6]；如果你看到的是别的写法，以片段为准。
- 单个 interrupt 的恢复可以直接传标量，例如 `new Command({ resume: true })` [2] 或 `Command(resume=True)` [6]；只有在多个并行 interrupt 同时挂起时，才需要按 id 组织成映射对象来分别恢复 [1][8]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__interrupts#029` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
const graph = new StateGraph(State) .addNode("a", nodeA) .addNode("b", nodeB) .addEdge(START, "a") .addEdge(START, "b") .addEdge("a", END) .addEdge("b", END) .compile({ checkpointer: new MemorySaver() }); const config = { configurable: { thread_id: "1" } }; async function main() { // Step 1: invoke - both parallel nodes hit interrupt() and pause const interruptedResult = await graph.invoke({ vals: [] }, config); console.log(interruptedResult); /* { vals: [], __interrupt__: [ { id: '...', value: 'question_a' }, { id: '...', value: 'question_b' } ] } */ // Step 2: resume all pending interrupts at once const resumeMap: Record<string, string> = {}; if (isInterrupted(interruptedResult)) {
```

片段[2] `oss__javascript__langgraph__interrupts#030` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
ume all pending interrupts at once const resumeMap: Record<string, string> = {}; if (isInterrupted(interruptedResult)) { for (const i of interruptedResult[INTERRUPT]) { if (i.id != null) { resumeMap[i.id] = `answer for ${i.value}`; } } } const result = await graph.invoke(new Command({ resume: resumeMap }), config); console.log("Final state:", result); //> Final state: { vals: ['a:answer for question_a', 'b:answer for question_b'] } } main().catch(console.error); ```
```

片段[3] `oss__javascript__langgraph__interrupts#009` ｜ Interrupts ｜ Resuming interrupts

```text
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
```

片段[4] `oss__python__langgraph__use-time-travel#011` ｜ Use time-travel ｜ Interrupts

```text
{"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human history = list(graph.get_state_history(config)) before_ask = [s for s in history if s.next == ("ask_human",)][-1] replay_result = graph.invoke(None, before_ask.config) # Pauses at interrupt — waiting for new Command(resume=...) # Fork from before ask_human fork_config = graph.update_state(before_ask.config, {"value": ["forked"]}) fork_result = graph.invoke(None, fork_config) # Pauses at interrupt — waiting for new Command(resume=...) # Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value":
```

片段[5] `oss__python__langgraph__interrupts#028` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
dge("a", END) .add_edge("b", END) .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Step 1: stream events to drive the run; both parallel nodes hit interrupt() and pause stream = graph.stream_events({"vals": []}, config, version="v3") _ = stream.output  # drive the stream to completion # stream.interrupts contains the pending Interrupt payloads print(stream.interrupts) # > (Interrupt(value='question_a', id='...'), Interrupt(value='question_b', id='...')) # Step 2: resume all pending interrupts at once resume_map = { i.id: f"answer for {i.value}" for i in stream.interrupts } resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")
```

---

## v2-G-003（single-hop）

**问题**：在 `collectAge` 节点里用 `interrupt(question)` 收年龄，用户先回 `new Command({ resume: "thirty" })` 再回 `new Command({ resume: 30 })`，两次的结果差别是怎么产生的？

**gold**：节点把 interrupt 的返回值当年龄校验：只有 typeof answer === "number" 且大于 0 才返回 age 并清空 pendingQuestion，否则把 pendingQuestion 改成「is not a valid age」的提示。配合 addConditionalEdges 里 state.age !== null ? END : "collectAge" 的判断，非法输入会让流程回到同一个节点重新提问，所以第二次调用返回的仍是 __interrupt__，只是提示变成了报错文案。等 resume 传 30 时才写入年龄并路由到 END，final.age 为 30。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

- `new Command({ resume: ... })` 传入的值会成为 `interrupt(question)` 的返回值 [1]。
- 第一次 resume `"thirty"` 时，`interrupt` 返回字符串 `"thirty"`，节点里的校验 `typeof answer === "number" && answer > 0` 不通过，于是返回 `pendingQuestion: "'thirty' is not a valid age. Please enter a positive number."`，并通过条件边路由回 `collectAge`，再次触发 interrupt，所以你会看到 `retry.__interrupt__` 里是这条错误提示 [3][9][10]。
- 第二次 resume `30` 时，`interrupt` 返回数字 `30`，校验通过，节点返回 `{ age: 30, pendingQuestion: null }`，条件边 `state.age !== null ? END : "collectAge"` 走到 `END`，图结束，`final.age` 为 `30` [2][9][10]。
- 另外注意：恢复时节点会从调用 interrupt 的那个节点开头重新执行，interrupt 之前的代码会再跑一遍 [7]；并且恢复必须使用与中断发生时相同的 thread ID [8]。

最小可用示例（JavaScript，摘自片段）：

```javascript
const retry = await graph.invoke(new Command({ resume: "thirty" }), config);
console.log(retry.__interrupt__);
// -> [{ value: "'thirty' is not a valid age...", ... }]

const final = await graph.invoke(new Command({ resume: 30 }), config);
console.log(final.age);
// -> 30
```

差异来源一句话：resume 的值原样成为 `interrupt` 的返回值，节点内对返回值做了类型/正数校验，`"thirty"` 不合法所以重新中断并提示，`30` 合法所以写入 `age` 并结束 [1][3][9][10]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__interrupts#011` ｜ Interrupts ｜ Resuming interrupts

```text
- The value passed to new Command({ resume: ... }) becomes the return value of the interrupt call
```

片段[2] `oss__javascript__langgraph__interrupts#052` ｜ Interrupts ｜ View example trace

```text
{ pendingQuestion: `'${answer}' is not a valid age. Please enter a positive number.` }; }) .addEdge(START, "collectAge") .addConditionalEdges("collectAge", (state) => state.age !== null ? END : "collectAge" ); const checkpointer = new MemorySaver(); const graph = builder.compile({ checkpointer }); const config = { configurable: { thread_id: "form-1" } }; const first = await graph.invoke({ age: null, pendingQuestion: null }, config); console.log(first.__interrupt__); // -> [{ value: "What is your age?", ... }] // Provide invalid data; the node re-prompts via the conditional edge const retry = await graph.invoke(new Command({ resume: "thirty" }), config);
```

片段[3] `oss__javascript__langgraph__interrupts#053` ｜ Interrupts ｜ View example trace

```text
he node re-prompts via the conditional edge const retry = await graph.invoke(new Command({ resume: "thirty" }), config); console.log(retry.__interrupt__); // -> [{ value: "'thirty' is not a valid age...", ... }] // Provide valid data; route returns END and the graph finishes const final = await graph.invoke(new Command({ resume: 30 }), config); console.log(final.age); // -> 30 ```
```

片段[4] `oss__javascript__langgraph__interrupts#050` ｜ Interrupts ｜ View example trace > Validating human input

```text
```

import { interrupt } from "@langchain/langgraph";



const getAgeNode: typeof State.Node = (state) => {

  const question = state.pendingQuestion ?? "What is your age?";

  const answer = interrupt(question); // called exactly once per invocation



  if (typeof answer === "number" && answer > 0) {

    return { age: answer, pendingQuestion: null };

  }

  return {

    pendingQuestion: `'${answer}' is not a valid age. Please enter a positive number.`,

  };

};



// builder.addConditionalEdges("collectAge", (state) =>

//   state.age !== null ? END : "collectAge"

// );

```
```

片段[5] `oss__python__langgraph__interrupts#054` ｜ Interrupts ｜ View example trace > Validating human input

```text
{"age": None, "pending_question": None}, config=config, version="v3") _ = first.output  # drive the stream to completion print(first.interrupts)  # -> (Interrupt(value='What is your age?', ...),) # Provide invalid data; the node re-prompts via the conditional edge retry = graph.stream_events(Command(resume="thirty"), config=config, version="v3") _ = retry.output print(retry.interrupts)  # -> (Interrupt(value="'thirty' is not a valid age...", ...),) # Provide valid data; route() returns END and the graph finishes final = graph.stream_events(Command(resume=30), config=config, version="v3") print(final.output["age"])  # -> 30 ```
```

---

## v2-G-004（single-hop）

**问题**：用 tools 流模式看工具进度时，`on_tool_start`、`on_tool_event`、`on_tool_end` 三个事件的载荷分别是什么？想拿到工具中途 yield 出来的进度该看哪个？

**gold**：on_tool_start 在工具开始调用时发出，载荷是 name、input、toolCallId；on_tool_end 在工具返回最终结果时发出，载荷是 name、output、toolCallId。中途进度要看 on_tool_event：工具每 yield 一次中间数据就发一个，载荷是 name、data、toolCallId。此外工具抛错时会发 on_tool_error，载荷换成 error。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：三个事件的载荷如下（均含 `toolCallId`）[2]：

- `on_tool_start`：`name`、`input`、`toolCallId`（工具调用开始时）[2]
- `on_tool_event`：`name`、`data`、`toolCallId`（工具 yield 中间数据时）[2]
- `on_tool_end`：`name`、`output`、`toolCallId`（工具返回最终结果时）[2]

想拿工具中途 yield 出来的进度，应看 `on_tool_event` 的 `data` 字段 [2]。工具里每次 `yield` 都会发出一个 `on_tool_event` [10]。

最小可用示例（服务端消费，`streamMode` 含 `"tools"`）[3]：

```javascript
for await (const [mode, chunk] of await graph.stream(
  { messages: [{ role: "user", content: "Find flights to Tokyo" }] },
  { streamMode: ["updates", "tools"] }
)) {
  if (mode === "tools") {
    switch (chunk.event) {
      case "on_tool_start":
        console.log(`Tool started: ${chunk.name}`, chunk.input);
        break;
      case "on_tool_event":
        console.log(`Tool progress: ${chunk.name}`, chunk.data);
        break;
      case "on_tool_end":
        console.log(`Tool finished: ${chunk.name}`, chunk.output);
        break;
      case "on_tool_error":
        console.error(`Tool failed: ${chunk.name}`, chunk.error);
        break;
    }
  }
}
```

补充：`tools` 模式会自动发出这些结构化生命周期事件，工具侧只需用 `async function*` 即可，无需额外改动 [1]；在 React 中 `useStream` 直接提供 `toolProgress` 数组 [1][7]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__streaming#040` ｜ Streaming ｜ View example trace > Tool progress > tools vs custom stream mode

```text
- tools —automatically emits structured lifecycle events ( on_tool_start , on_tool_event , on_tool_end , on_tool_error ) with no code changes needed in your tools beyond using async function* . The useStream hook provides the reactive toolProgress array out of the box.
```

片段[2] `oss__javascript__langgraph__streaming#029` ｜ Streaming ｜ View example trace > Tool progress

```text
| Event | When | Payload |

| --- | --- | --- |

| on_tool_start | Tool invocation begins | name , input , toolCallId |

| on_tool_event | Tool yields intermediate data | name , data , toolCallId |

| on_tool_end | Tool returns its final result | name , output , toolCallId |

| on_tool_error | Tool throws an error | name , error , toolCallId |
```

片段[3] `oss__javascript__langgraph__streaming#032` ｜ Streaming ｜ View example trace > Tool progress > Consume tool events server-side

```text
```

for await (const [mode, chunk] of await graph.stream(

  { messages: [{ role: "user", content: "Find flights to Tokyo" }] },

  { streamMode: ["updates", "tools"] }

)) {

  if (mode === "tools") {

    switch (chunk.event) {

      case "on_tool_start":

        console.log(`Tool started: ${chunk.name}`, chunk.input);

        break;

      case "on_tool_event":

        console.log(`Tool progress: ${chunk.name}`, chunk.data);

        break;

      case "on_tool_end":

        console.log(`Tool finished: ${chunk.name}`, chunk.output);

        break;

      case "on_tool_error":

        console.error(`Tool failed: ${chunk.name}`, chunk.error);

        break;

    }

  }

}

```
```

片段[4] `oss__javascript__langgraph__streaming#001` ｜ Streaming ｜ Stream modes

```text
| Mode | Description |

| --- | --- |

| values | Full state after each step. |

| updates | State updates after each step. Multiple updates in the same step are streamed separately. |

| messages | 2-tuples of (LLM token, metadata) from LLM calls. |

| custom | Custom data emitted from nodes via the writer config parameter. |

| tools | Tool-call lifecycle events ( on_tool_start , on_tool_event , on_tool_end , on_tool_error ). |

| debug | All available info throughout graph execution. |
```

片段[5] `oss__javascript__langgraph__streaming#033` ｜ Streaming ｜ View example trace > Tool progress > Use tool progress in React with useStream

```text
| Field | Description |

| --- | --- |

| name | The tool name |

| state | Current lifecycle state: "starting" , "running" , "completed" , or "error" |

| toolCallId | The tool call ID from the LLM |

| input | The tool’s input arguments |

| data | The most recent yielded data from on_tool_event |

| result | The final result, set on on_tool_end |

| error | The error, set on on_tool_error |
```

---

## v2-G-005（single-hop）

**问题**：React 里用 `useStream` 的 `toolProgress` 数组渲染工具进度条，`data` 和 `result` 两个字段分别在什么时候有值？`state` 可能取哪些值？

**gold**：data 存的是最近一次 on_tool_event 产出的中间数据，result 则是 on_tool_end 时才写入的最终结果。state 表示当前生命周期状态，取值有 starting、running、completed、error 四种。每项还带 name、toolCallId、input，出错时 error 字段由 on_tool_error 填充。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

- `state` 的取值是 `"starting"`、`"running"`、`"completed"`、`"error"` 四种 [9]。
- `data` 是工具最近一次 yield 出来的数据（来自 `on_tool_event`），因此在工具执行过程中、有 yield 时会有值 [9]；示例里用它读取 `message`、`progress`、`completed` 来渲染进度条 [2][10]。
- `result` 是最终结果，在 `on_tool_end` 时才被设置 [9]。
- 注意：片段中 `data` 的说明写的是来自 `on_tool_event`，而 `result` 来自 `on_tool_end`、`error` 来自 `on_tool_error`，这些是片段原文的写法 [9]。

最小可用示例（基于片段中的 React 用法）：

```tsx
import { useStream } from "@langchain/langgraph-sdk/react";

function TravelPlanner() {
  const stream = useStream<typeof agent>({
    assistantId: "travel-agent",
    streamMode: ["values", "tools"],
  });

  const activeTools = stream.toolProgress.filter(
    (t) => t.state === "starting" || t.state === "running"
  );

  return (
    <div>
      {stream.messages.map((msg) => (
        <div key={msg.id}>{msg.content}</div>
      ))}
      {activeTools.map((tool) => {
        const data = tool.data as
          | { message?: string; progress?: number; completed?: string[] }
          | undefined;
        return (
          <div key={tool.toolCallId ?? tool.name}>
            <strong>{tool.name}</strong>
            {data?.message && <p>{data.message}</p>}
            {data?.progress != null && (
              <div style={{ width: "100%", background: "#eee" }}>
                <div
                  style={{
                    width: `${data.progress * 100}%`,
                    background: "#4CAF50",
                    height: 8,
                    transition: "width 0.3s ease",
                  }}
                />
              </div>
            )}
            {data?.completed?.map((step, i) => (
              <div key={i}>&#10003; {step}</div>
            ))}
          </div>
        );
      })}
    </div>
  );
}
```

补充：片段只给出了 `toolProgress` 各字段的含义表 [9] 和 React 渲染示例 [1][2][10]，没有进一步说明 `data`/`result` 在时间线上的精确先后细节，以上仅按字段描述作答。

**top5 片段**：

片段[1] `oss__javascript__langgraph__streaming#034` ｜ Streaming ｜ View example trace > Tool progress > Use tool progress in React with useStream

```text
``` import { useStream } from "@langchain/langgraph-sdk/react"; function Chat() { const stream = useStream({ assistantId: "my-agent", streamMode: ["values", "tools"], }); // Filter for actively running tools const activeTools = stream.toolProgress.filter( (t) => t.state === "starting" || t.state === "running" ); return ( <div> {stream.messages.map((msg) => ( <MessageBubble key={msg.id} message={msg} /> ))} {/* Show progress cards for running tools */} {activeTools.map((tool) => ( <ToolProgressCard key={tool.toolCallId ?? tool.name} name={tool.name} state={tool.state} data={tool.data} /> ))} </div> ); } ```
```

片段[2] `oss__javascript__langgraph__streaming#038` ｜ Streaming ｜ View example trace > Tool progress > Use tool progress in React with useStream

```text
``` import { useStream } from "@langchain/langgraph-sdk/react"; function TravelPlanner() { const stream = useStream<typeof agent>({ assistantId: "travel-agent", streamMode: ["values", "tools"], }); const activeTools = stream.toolProgress.filter( (t) => t.state === "starting" || t.state === "running" ); return ( <div> {stream.messages.map((msg) => ( <div key={msg.id}>{msg.content}</div> ))} {activeTools.map((tool) => { const data = tool.data as { message?: string; progress?: number; completed?: string[]; } | undefined; return ( <div key={tool.toolCallId ?? tool.name}> <strong>{tool.name}</strong> {data?.message && <p>{data.message}</p>} {data?.progress != null && ( <div style={{ width:
```

片段[3] `oss__javascript__langgraph__streaming#033` ｜ Streaming ｜ View example trace > Tool progress > Use tool progress in React with useStream

```text
| Field | Description |

| --- | --- |

| name | The tool name |

| state | Current lifecycle state: "starting" , "running" , "completed" , or "error" |

| toolCallId | The tool call ID from the LLM |

| input | The tool’s input arguments |

| data | The most recent yielded data from on_tool_event |

| result | The final result, set on on_tool_end |

| error | The error, set on on_tool_error |
```

片段[4] `oss__python__langchain__streaming#005` ｜ Streaming ｜ Agent progress

```text
on="v3", ) for kind, item in stream.interleave("messages", "tool_calls"): if kind == "messages": for token in item.text: print(token, end="", flush=True) elif kind == "tool_calls": print(f"\nTool call: {item.tool_name}({item.input})") for delta in item.output_deltas: print(delta, end="", flush=True) print(f"\nTool result: {item.output}") final_state = stream.output ```
```

片段[5] `oss__python__langchain__streaming#013` ｜ Streaming ｜ Agent progress

```text
on="v3", ) for kind, item in stream.interleave("messages", "tool_calls"): if kind == "messages": for token in item.text: print(token, end="", flush=True) elif kind == "tool_calls": print(f"\nTool call: {item.tool_name}({item.input})") for delta in item.output_deltas: print(delta, end="", flush=True) print(f"\nTool result: {item.output}") final_state = stream.output ```
```

---

## v2-G-006（single-hop）

**问题**：用 `graph.streamEvents(input, { version: "v3" })` 跑到一半被中断了，怎么判断这次流是不是停在中断上、又该怎么续跑？

**gold**：消费完 stream.messages 之后，可以看 stream.interrupted 判断这次是否停在中断上，中断内容在 stream.interrupts 里。续跑时重新调用 graph.streamEvents，并把 new Command({ resume: { decisions: [{ type: "approve" }] } }) 当输入传进去。最终状态要用 await stream.output 取。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. 用 `stream.interrupted` 判断这次流是否停在中断上；为 `true` 时，待处理的 payload 在 `stream.interrupts` 里 [1][8]。
2. 续跑时，把 `new Command({ resume: ... })` 作为新的输入再次调用 `graph.streamEvents(..., { version: "v3" })` [5][7]。
3. 注意：你写的 `graph.streamEvents(input, { version: "v3" })` 与片段一致（JS 侧）[5]；但片段里读取中断 payload 的字段在 JS 与 Python 示例中不一致——JS 的 HITL 模式片段用 `stream.interrupts[0].payload` [6]，而 Python 片段用 `stream.interrupts[0].value` [3]。以你所用语言的片段为准，不要混用。

**最小可用示例（JavaScript，依据 [5]）**

```javascript
import { Command } from "@langchain/langgraph";

let stream = await graph.streamEvents(input, { version: "v3" });

for await (const message of stream.messages) {
  console.log(await message.text);
}

// 判断是否停在中断上
if (stream.interrupted) {
  console.log(stream.interrupts); // 待处理的 Interrupt payload
}

// 续跑：用 Command(resume=...) 作为新的输入
stream = await graph.streamEvents(
  new Command({ resume: { decisions: [{ type: "approve" }] } }),
  { version: "v3" }
);
const finalState = await stream.output;
```

补充：若一次有多个并行中断，Python 片段展示了用 `{ i.id: ... }` 映射一次性 resume 全部 pending interrupts 的写法 [2][11]；该片段未给出 JS 等价写法，故此处不臆测。

**top5 片段**：

片段[1] `oss__python__langgraph__interrupts#002` ｜ Interrupts ｜ ROOT

```text
- Interrupt payloads surface via stream.interrupts : when using event streaming ( graph.stream_events(..., version="v3") ), the values you pass to interrupt() appear on stream.interrupts , and stream.interrupted is True when the run pauses for input.
```

片段[2] `oss__python__langgraph__interrupts#028` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
dge("a", END) .add_edge("b", END) .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Step 1: stream events to drive the run; both parallel nodes hit interrupt() and pause stream = graph.stream_events({"vals": []}, config, version="v3") _ = stream.output  # drive the stream to completion # stream.interrupts contains the pending Interrupt payloads print(stream.interrupts) # > (Interrupt(value='question_a', id='...'), Interrupt(value='question_b', id='...')) # Step 2: resume all pending interrupts at once resume_map = { i.id: f"answer for {i.value}" for i in stream.interrupts } resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")
```

片段[3] `oss__python__langgraph__interrupts#023` ｜ Interrupts ｜ Common patterns > Stream with human-in-the-loop (HITL) interrupts

```text
```

from langgraph.types import Command



stream_input: dict | Command = initial_input



while True:

    stream = graph.stream_events(stream_input, config=config, version="v3")



    # Stream LLM message chunks (including any in subgraphs) as they arrive.

    for message in stream.messages:

        for token in message.text:

            display_streaming_content(token)



    # After the run finishes (or pauses), check for interrupts and resume.

    if not stream.interrupted:

        final_state = stream.output

        break



    interrupt_info = stream.interrupts[0].value

    user_response = get_user_input(interrupt_info)

    stream_input = Command(resume=user_response)

```
```

片段[4] `oss__python__langgraph__event-streaming#006` ｜ Event streaming ｜ Stream state

```text
```

stream = graph.stream_events(input, version="v3")



for snapshot in stream.values:

    print(snapshot)



final_state = stream.output

```
```

片段[5] `oss__javascript__langgraph__event-streaming#008` ｜ Event streaming ｜ Resume after an interrupt

```text
```

import { Command } from "@langchain/langgraph";



let stream = await graph.streamEvents(input, { version: "v3" });



for await (const message of stream.messages) {

  console.log(await message.text);

}



if (stream.interrupted) {

  console.log(stream.interrupts);

}



stream = await graph.streamEvents(

  new Command({ resume: { decisions: [{ type: "approve" }] } }),

  { version: "v3" }

);

const finalState = await stream.output;

```
```

---

## v2-G-007（single-hop）

**问题**：父图和子图共享同一批 state key 时，为什么可以直接把编译好的子图传给 `add_node`，而不用像另一种写法那样包一层函数？

**gold**：因为共享 state key 时，子图读写的通道与父图一致，不需要在两边做状态转换。这种情况的做法是把 compiled 子图直接传给 add_node，no wrapper function needed。另一种「在节点里调用子图」适用于父子 state schema 不同、没有共享键或需要转换状态的场景，那时才必须自己写 wrapper。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：因为父图和子图共享同一批 state key（子图读写的是与父图相同的 channel），所以不需要做状态映射，直接把编译好的子图传给 `add_node` 即可，无需包装函数 [1][2]。相反，当父图与子图 state schema 不同（没有共享 key）或需要在两者之间转换状态时，才需要写一个包装函数，把父图 state 映射为子图输入、再把子图输出映射回父图 state [1][2]。

最小可用示例（共享 key，直接传编译后的子图）：

```python
from typing_extensions import TypedDict
from langgraph.graph.state import StateGraph, START

class SubgraphState(TypedDict):
    foo: str  # shared with parent graph state
    bar: str  # private to SubgraphState

def subgraph_node_1(state: SubgraphState):
    return {"bar": "bar"}

def subgraph_node_2(state: SubgraphState):
    # 使用仅子图可用的 'bar'，并更新共享 key 'foo'
    return {"foo": state["foo"] + state["bar"]}

subgraph_builder = StateGraph(SubgraphState)
subgraph_builder.add_node(subgraph_node_1)
# ...（其余节点与边定义见片段）
```

片段 [6] 展示了共享 key 的子图定义，片段 [5] 说明做法是“把编译后的子图传给 `add_node` 方法” [5]；片段 [4] 则展示了另一种写法——传入的是函数（`call_child_graph`）而非编译后的图，用于需要转换状态的场景 [4]。

补充说明（以片段为准的 API 差异）：JavaScript 版本中对应方法是 `.addNode`，而非 `add_node` [8]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__use-subgraphs#001` ｜ Subgraphs ｜ Define subgraph communication

```text
| Pattern | When to use | State schemas |

| --- | --- | --- |

| Call a subgraph inside a node | Parent and subgraph have different state schemas (no shared keys), or you need to transform state between them | You write a wrapper function that maps parent state to subgraph input and subgraph output back to parent state |

| Add a subgraph as a node | Parent and subgraph share state keys —the subgraph reads from and writes to the same channels as the parent | You pass the compiled subgraph directly to add_node —no wrapper function needed |
```

片段[2] `oss__python__langgraph__use-subgraphs#001` ｜ Subgraphs ｜ Define subgraph communication

```text
| Pattern | When to use | State schemas |

| --- | --- | --- |

| Call a subgraph inside a node | Parent and subgraph have different state schemas (no shared keys), or you need to transform state between them | You write a wrapper function that maps parent state to subgraph input and subgraph output back to parent state |

| Add a subgraph as a node | Parent and subgraph share state keys —the subgraph reads from and writes to the same channels as the parent | You pass the compiled subgraph directly to add_node —no wrapper function needed |
```

片段[3] `oss__python__langgraph__use-subgraphs#009` ｜ Subgraphs ｜ Define subgraph communication > Call a subgraph inside a node

```text
grandchild_1", END) grandchild_graph = grandchild.compile() # Child graph class ChildState(TypedDict): my_child_key: str def call_grandchild_graph(state: ChildState) -> ChildState: # NOTE: parent or grandchild keys won't be accessible here grandchild_graph_input = {"my_grandchild_key": state["my_child_key"]} grandchild_graph_output = grandchild_graph.invoke(grandchild_graph_input) return {"my_child_key": grandchild_graph_output["my_grandchild_key"] + " today?"} child = StateGraph(ChildState) # We're passing a function here instead of just compiled graph (`grandchild_graph`) child.add_node("child_1", call_grandchild_graph) child.add_edge(START, "child_1") child.add_edge("child_1", END)
```

片段[4] `oss__python__langgraph__use-subgraphs#011` ｜ Subgraphs ｜ Define subgraph communication > Call a subgraph inside a node

```text
_key"]} child_graph_output = child_graph.invoke(child_graph_input) return {"my_key": child_graph_output["my_child_key"]} parent = StateGraph(ParentState) parent.add_node("parent_1", parent_1) # We're passing a function here instead of just a compiled graph (`child_graph`) parent.add_node("child", call_child_graph) parent.add_node("parent_2", parent_2) parent.add_edge(START, "parent_1") parent.add_edge("parent_1", "child") parent.add_edge("child", "parent_2") parent.add_edge("parent_2", END) parent_graph = parent.compile() stream = parent_graph.stream_events({"my_key": "Bob"}, version="v3", transformers=[UpdatesTransformer]) for event in stream: if event["method"] == "updates":
```

片段[5] `oss__python__langgraph__use-subgraphs#015` ｜ Subgraphs ｜ Define subgraph communication > Add a subgraph as a node

```text
2. Pass compiled subgraph to the add_node method when defining the parent graph workflow
```

---

## v2-G-008（single-hop）

**问题**：想让助手记住跨多次会话的用户偏好和事实，官方建议用 store 而不是按会话存的 checkpointer，理由是什么？

**gold**：Stores 持久化的是 graph state 之外的、由应用自己定义的数据。它的定位是 long-term、cross-thread 记忆，适合放 user preferences、facts 和 shared knowledge 这类要跨会话复用的内容。相比之下，按 thread 存的图状态属于短期记忆，只能支撑单条会话内的连续性，不适合承担长期偏好。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 官方把长期、跨线程的记忆交给 store，把短期、线程内的记忆交给 checkpointer，两者分工不同。

- Store 用于持久化「应用自定义数据」，这些数据存放在图状态（graph state）之外，适合长期、跨线程的记忆，包括用户偏好、事实和共享知识 [2][3]。
- Store 提供的是跨线程的长期记忆，与按线程持久化的 checkpointer 互补 [5][6]。
- Checkpointer 持久化的是某个线程的图状态（checkpoint），用于短期、线程范围内的记忆，包括对话连续性、human-in-the-loop、time travel 和容错 [12]；它让重复交互（如对话）中后续消息发到同一线程时能保留对先前消息的记忆 [7][8]。

所以「跨多次会话的用户偏好和事实」属于跨线程长期记忆，应使用 store；checkpointer 只保证同一线程内的连续性。

**最小可用示例（Python，摘自文档片段）：**

```python
def call_model(
    state: MessagesState,
    config: RunnableConfig,
    *,
    store: BaseStore,
):
    user_id = config["configurable"]["user_id"]
    namespace = ("memories", user_id)
    memories = store.search(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories])
    system_msg = f"You are a helpful assistant talking to the user. User info: {info}"

    # Store new memories if the user asks the model to remember
    last_message = state["messages"][-1]
    if "remember" in last_message.content.lower():
        memory = "User name is Bob"
        await store.aput(namespace, str(uuid7()), {"data": memory})

    response = await model.ainvoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )
    return {"messages": response}

builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")
graph = builder.compile(
    checkpointer=checkpointer,
    store=store,
)
config = {
    "configurable": {
        "thread_id": "1",
        "user_id": "1",
    }
}
```

注意：片段中 `store.search(...)` 为同步写法 [4]，异步版本使用 `await store.asearch(...)` [10]；示例里 `namespace` 按 `user_id` 划分，因此不同 `thread_id`（如 "1" 和 "2"）也能共享同一用户的记忆 [9]。

**top5 片段**：

片段[1] `oss__python__langgraph__add-memory#060` ｜ Memory ｜ Add long-term memory > Use in production

```text
a helpful assistant talking to the user. User info: {info}" # Store new memories if the user asks the model to remember last_message = state["messages"][-1] if "remember" in last_message.content.lower(): memory = "User name is Bob" await store.aput(namespace, str(uuid7()), {"data": memory}) response = await model.ainvoke( [{"role": "system", "content": system_msg}] + state["messages"] ) return {"messages": response} builder = StateGraph(MessagesState) builder.add_node(call_model) builder.add_edge(START, "call_model") graph = builder.compile( checkpointer=checkpointer, store=store, ) config = { "configurable": { "thread_id": "1", "user_id": "1", } } stream = await graph.astream_events(
```

片段[2] `oss__javascript__langgraph__persistence#002` ｜ Persistence ｜ ROOT

```text
- Stores persist application-defined data outside the graph state. Use them for long-term, cross-thread memory, including user preferences, facts, and shared knowledge.
```

片段[3] `oss__python__langgraph__persistence#002` ｜ Persistence ｜ ROOT

```text
- Stores persist application-defined data outside the graph state. Use them for long-term, cross-thread memory, including user preferences, facts, and shared knowledge.
```

片段[4] `oss__python__langgraph__add-memory#055` ｜ Memory ｜ Add long-term memory > Use in production

```text
ng( DB_URI, index={"embed": embeddings, "dims": 1536}, ) as store, OracleSaver.from_conn_string(DB_URI) as checkpointer, ): store.setup() checkpointer.setup() def call_model( state: MessagesState, config: RunnableConfig, *, store: BaseStore, ): user_id = config["configurable"]["user_id"] namespace = ("memories", user_id) memories = store.search(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories]) system_msg = f"You are a helpful assistant talking to the user. User info: {info}" # Store new memories if the user asks the model to remember last_message = state["messages"][-1] if "remember" in last_message.content.lower():
```

片段[5] `oss__python__langgraph__stores#000` ｜ Stores ｜ ROOT

```text
Stores LangGraph stores provide cross-thread long-term memory, complementing per-thread checkpointer persistence.
```

---

## v2-G-009（single-hop）

**问题**：模型在一轮里同时调了三个工具，其中只有两个标了 `returnDirect`（文档里写作 `return_direct=True`），这一轮结束后会怎样？并行调用是等最慢的一个还是各自跑完？

**gold**：多个并行工具调用会先全部执行，也就是 all of them execute first，而不是串行等待某一个。等这批工具都结束之后，只有当该批里每一个工具都设了 return_direct=True 时，agent 才会路由到 END。本例有两个没设，所以不会直接结束，最终响应里会包含这一步所有工具返回的 ToolMessage 内容。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. **并行调用会先全部执行完**：当模型在一步里调用多个工具时，所有工具都会先执行，等这一批全部结束后才做路由判断 [1][2]。
2. **不会因为部分工具标了 `return_direct=True` 就提前结束**：只有当这一批里**每一个**工具都是 `return_direct=True` 时，agent 才会路由到 END [1][2]。你描述的场景是三个里只有两个标了，不满足"全部"条件，所以**不会**直接路由到 END，会继续走后续流程（例如再调用模型）。
3. **最终响应会包含该步中所有被调用工具的 ToolMessage 输出**，包括那两个标了 `return_direct=True` 的工具的输出 [1][2]。
4. **关于"等最慢的一个还是各自跑完"**：文档只说明"all of them execute first. After all tools finish..."，即这一批工具全部执行完成后才继续 [1][2]；文档没有进一步说明是同步等待最慢者还是异步并行调度。示例代码里注释写的是 "can be done in parallel with async"（可用 async 并行执行）[5][8]，但这属于示例注释，不是对调度语义的规范描述。

**参数名差异提示：** 你写的是 `returnDirect`，文档片段中写作 `return_direct=True` [1][2]，以文档为准。

**最小示例（Python，来自文档片段 [5]）：**

```python
tools = [get_weather]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

response = model_with_tools.invoke("What's the weather in Boston and Tokyo?")

# The model may generate multiple tool calls
print(response.tool_calls)
# [
#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},
#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'}
# ]

# Execute all tools (can be done in parallel with async)
results = []
for tool_call in response.tool_calls:
    tool = tools_by_name[tool_call["name"]]
    result = tool.invoke(tool_call)
    results.append(result)
```

**补充说明（缺什么）：** 片段没有给出"部分工具 `return_direct=True`、部分不是"时具体的路由目标细节（例如是否一定回到模型节点），只明确了"全部为 True 才到 END"这一否定性条件 [1][2]；也没有给出并行调度的具体实现语义。

**top5 片段**：

片段[1] `oss__javascript__langchain__tools#020` ｜ Tools ｜ View example trace

```text
- Multiple parallel tool calls: When the model calls several tools in one step, all of them execute first. After all tools finish, the agent routes to END only if every tool in that batch has return_direct=True . The final response includes the ToolMessage outputs of every tool that was called in that step.
```

片段[2] `oss__python__langchain__tools#031` ｜ Tools ｜ View example trace

```text
- Multiple parallel tool calls: When the model calls several tools in one step, all of them execute first. After all tools finish, the agent routes to END only if every tool in that batch has return_direct=True . The final response includes the ToolMessage outputs of every tool that was called in that step.
```

片段[3] `oss__javascript__releases__langchain-v1#009` ｜ What's new in LangChain v1 ｜ Time travel > Structured output

```text
- Multiple tool calls : Model generates 2+ tool calls for structured output schemas
```

片段[4] `oss__python__releases__langchain-v1#008` ｜ What's new in LangChain v1 ｜ Time travel > Structured output

```text
- Multiple tool calls : Model generates 2+ tool calls for structured output schemas
```

片段[5] `oss__python__langchain__models#036` ｜ Models ｜ Tool calling

```text
```

tools = [get_weather]

tools_by_name = {tool.name: tool for tool in tools}

model_with_tools = model.bind_tools(tools)



response = model_with_tools.invoke(

    "What's the weather in Boston and Tokyo?"

)



# The model may generate multiple tool calls

print(response.tool_calls)

# [

#   {'name': 'get_weather', 'args': {'location': 'Boston'}, 'id': 'call_1'},

#   {'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_2'},

# ]



# Execute all tools (can be done in parallel with async)

results = []

for tool_call in response.tool_calls:

    tool = tools_by_name[tool_call["name"]]

    result = tool.invoke(tool_call)

    results.append(result)

```
```

---

## v2-G-010（single-hop）

**问题**：工具函数除了返回字符串，还能 `return new Command({ update: { ... } })` 直接改图状态吗？这时工具消息的 `tool_call_id` 从哪来？

**gold**：可以，示例里的 set_language 工具就返回 new Command({ update: { preferredLanguage: language, messages: [...] } })，用一次状态更新把结果写回图。它同时构造了一条 ToolMessage 放进 messages，content 是提示文案。tool_call_id 取自 config.toolCallId，所以这条工具消息能对上模型发起的那次调用。

**judge 分**：1.0　**拒答标记**：None

**回答**：

可以。工具函数可以返回 `Command`，通过 `update` 直接更新图状态（包括 `messages` 等）[2][3][5][6]。返回 `Command` 时，为了让消息历史保持有效，需要同时往 `messages` 里放一条 `ToolMessage`，其 `tool_call_id` 要对应本次工具调用 [2][3][5]。

关于 `tool_call_id` 的来源，片段里给出的做法是：在 Python 工具中通过 `ToolRuntime` 参数取 `runtime.tool_call_id` [2][3][5][6]；在 JS 工具中通过 `runtime.tool_call.id` 取 [4]。另外片段 [1] 展示了另一种写法：用 `Annotated[str, InjectedToolCallId]` 注入 `tool_call_id` 参数 [1]。

注意与用户说法的差异：用户写的是 `return new Command({ update: { ... } })`（JS 风格），片段 [4] 的 JS 示例确实是 `new Command({ update: {...} })` [4]；而 Python 片段用的是 `Command(update={...})`，没有 `new` [2][3][5][6]。请按所用语言选择对应写法。

最小可用示例（Python，来自片段 [5]）：

```python
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.types import Command

@tool
def set_language(language: str, runtime: ToolRuntime) -> Command:
    """Set the preferred response language."""
    return Command(
        update={
            "preferred_language": language,
            "messages": [
                ToolMessage(
                    content=f"Language set to {language}.",
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
```

最小可用示例（JS，来自片段 [4]）：

```javascript
import { tool } from "@langchain/core/tools";
import { Command } from "@langchain/langgraph";
import * as z from "zod";

const lookupUserInfo = tool(
  async (_input, runtime) => {
    const userId = runtime.serverInfo?.user?.identity as string | undefined;
    const userInfo = getUserInfo(userId);
    return new Command({
      update: {
        userInfo,
        messages: [
          {
            role: "tool",
            content: "Successfully looked up user information",
            tool_call_id: runtime.tool_call.id,
          },
        ],
      },
    });
  },
  {
    name: "lookupUserInfo",
    description: "Look up user information to better assist with questions.",
    schema: z.object({}),
  }
);
```

**top5 片段**：

片段[1] `oss__python__langchain__multi-agent__subagents#037` ｜ Subagents ｜ Context engineering > Subagent outputs

```text
``` from typing import Annotated from langchain.agents import AgentState from langchain.tools import InjectedToolCallId from langgraph.types import Command @tool( "subagent1_name", description="subagent1_description" ) def call_subagent1( query: str, tool_call_id: Annotated[str, InjectedToolCallId], ) -> Command: result = subagent1.invoke({ "messages": [{"role": "user", "content": query}] }) return Command(update={ # Pass back additional state from the subagent "example_state_key": result["example_state_key"], "messages": [ ToolMessage( content=result["messages"][-1].content, tool_call_id=tool_call_id ) ] }) ```
```

片段[2] `oss__python__langchain__tools#034` ｜ Tools ｜ View example trace > Return a Command with return_direct

```text
``` from langchain.messages import ToolMessage from langchain.tools import ToolRuntime, tool from langgraph.types import Command @tool(return_direct=True) def fetch_and_store_order(order_id: str, runtime: ToolRuntime) -> Command: """Fetch order status and store it in state.""" status = f"Order {order_id} is shipped and will arrive in 2 days." return Command( update={ "last_order_status": status, # Must include a ToolMessage so the message history stays valid "messages": [ ToolMessage( content=status, tool_call_id=runtime.tool_call_id, ) ], } ) ```
```

片段[3] `oss__python__langchain__tools#011` ｜ Tools ｜ Access context > Short-term memory (State) > Update state

```text
```

from langchain.agents import AgentState

from langchain.messages import ToolMessage

from langchain.tools import ToolRuntime, tool

from langgraph.types import Command



class CustomState(AgentState):

    user_name: str



@tool

def set_user_name(new_name: str, runtime: ToolRuntime[None, CustomState]) -> Command:

    """Set the user's name in the conversation state."""

    return Command(

        update={

            "user_name": new_name,

            "messages": [

                ToolMessage(

                    content=f"User name set to {new_name}.",

                    tool_call_id=runtime.tool_call_id,

                )

            ],

        }

    )

```
```

片段[4] `oss__javascript__langgraph__graph-api-send-command#014` ｜ Use Send and Command ｜ Combine control flow and state updates with Command > Use inside tools

```text
``` import { tool } from "@langchain/core/tools"; import { Command } from "@langchain/langgraph"; import * as z from "zod"; const lookupUserInfo = tool( async (_input, runtime) => { const userId = runtime.serverInfo?.user?.identity as string | undefined; const userInfo = getUserInfo(userId); return new Command({ update: { userInfo, messages: [ { role: "tool", content: "Successfully looked up user information", tool_call_id: runtime.toolCall.id, }, ], }, }); }, { name: "lookupUserInfo", description: "Look up user information to better assist with questions.", schema: z.object({}), } ); ```
```

片段[5] `oss__python__langchain__tools#028` ｜ Tools ｜ View example trace > Return a Command

```text
```

from langchain.messages import ToolMessage

from langchain.tools import ToolRuntime, tool

from langgraph.types import Command



@tool

def set_language(language: str, runtime: ToolRuntime) -> Command:

    """Set the preferred response language."""

    return Command(

        update={

            "preferred_language": language,

            "messages": [

                ToolMessage(

                    content=f"Language set to {language}.",

                    tool_call_id=runtime.tool_call_id,

                )

            ],

        }

    )

```
```

---

## v2-G-011（single-hop）

**问题**：`toolCallLimitMiddleware` 能不能只限制某一个工具、并且超限时直接抛错而不是静默截断？同时挂多个限流器时它们是怎么叠加的？

**gold**：可以。传 toolName 就只作用于该工具，例如 { toolName: "search", threadLimit: 5, runLimit: 3 } 只限制 search；不传 toolName 的实例是全局计数，示例里是 threadLimit: 20、runLimit: 10。超限默认不是抛错，要显式写 exitBehavior: "error"，例如 { toolName: "scrape_webpage", runLimit: 2, exitBehavior: "error" }。多个限流器一起放进 middleware 数组即可同时生效。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：可以。** 用 `toolName` 指定单个工具，并把 `exitBehavior` 设为 `"error"` 即可在超限时抛错；多个限流器同时挂载时会各自独立生效（全局 + 各工具专属），文档示例中就是全局限流器与多个工具专属限流器并列放在 `middleware` 数组里 [2][3]。

需要注意的几点（以片段为准）：

1. **只限制某一个工具**：通过 `toolName` 参数指定，例如 `toolCallLimitMiddleware({ toolName: "search", threadLimit: 5, runLimit: 3 })` [3][4]。
2. **超限直接抛错**：`exitBehavior: "error"`，示例为 `toolCallLimitMiddleware({ toolName: "scrape_webpage", runLimit: 2, exitBehavior: "error" })` [3]。默认行为是 `'continue'`，即用错误消息阻断超限调用、让模型和其他工具继续 [9][12]。
3. **多个限流器叠加**：文档示例把 `globalLimiter`、`searchLimiter`、`databaseLimiter`、`strictLimiter` 一起放进 `middleware` 数组 [2][3]，说明全局限制与工具级限制是分别配置、共同挂载的；片段没有进一步说明优先级或合并算法，这部分文档里没有给出。
4. **API 名称差异**：你写的是 `toolCallLimitMiddleware`（camelCase），这在 JavaScript 版本中是正确的 [3][4]；Python 版本对应的是 `ToolCallLimitMiddleware`（PascalCase）[1][2]。请按所用语言选择。
5. **`'end'` 行为的限制**：`'end'` 会立即停止执行并返回 ToolMessage 和 AI message，但**仅在限制单个工具时有效**；若还有其他工具处于 pending 调用状态，Python 版会抛 `NotImplementedError` [6]，JS 版会抛错 [5]。这与你要的 `"error"` 是不同选项，别混淆。

**最小可用示例（JavaScript）：**

```javascript
import { createAgent, toolCallLimitMiddleware } from "langchain";

const searchLimiter = toolCallLimitMiddleware({
  toolName: "search",
  threadLimit: 5,
  runLimit: 3,
  exitBehavior: "error", // 超限直接抛错
});

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [searchTool, databaseTool],
  middleware: [searchLimiter],
});
```

**Python 等价写法：**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

agent = create_agent(
    model="gpt-6.1-sol",
    tools=[search_tool, database_tool],
    middleware=[
        ToolCallLimitMiddleware(
            tool_name="search",
            thread_limit=5,
            run_limit=3,
            exit_behavior="error",
        ),
    ],
)
```

（Python 的 `exit_behavior="error"` 在片段 [2] 中只出现了 `"error"` 用于 `strict_limiter` 的写法，参数名按 Python 版命名习惯为 `exit_behavior`；片段 [2] 原文即为 `exit_behavior="error"`。）

**top5 片段**：

片段[1] `oss__python__langchain__middleware__built-in#035` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool call limit

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import ToolCallLimitMiddleware



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[search_tool, database_tool],

    middleware=[

        # Global limit

        ToolCallLimitMiddleware(thread_limit=20, run_limit=10),

        # Tool-specific limit

        ToolCallLimitMiddleware(

            tool_name="search",

            thread_limit=5,

            run_limit=3,

        ),

    ],

)

```
```

片段[2] `oss__python__langchain__middleware__built-in#041` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool call limit

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import ToolCallLimitMiddleware



global_limiter = ToolCallLimitMiddleware(thread_limit=20, run_limit=10)

search_limiter = ToolCallLimitMiddleware(tool_name="search", thread_limit=5, run_limit=3)

database_limiter = ToolCallLimitMiddleware(tool_name="query_database", thread_limit=10)

strict_limiter = ToolCallLimitMiddleware(tool_name="scrape_webpage", run_limit=2, exit_behavior="error")



agent = create_agent(

    model="gpt-6.1-sol",

    tools=[search_tool, database_tool, scraper_tool],

    middleware=[global_limiter, search_limiter, database_limiter, strict_limiter],

)

```
```

片段[3] `oss__javascript__langchain__middleware__built-in#042` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool call limit

```text
```

import { createAgent, toolCallLimitMiddleware } from "langchain";



const globalLimiter = toolCallLimitMiddleware({ threadLimit: 20, runLimit: 10 });

const searchLimiter = toolCallLimitMiddleware({ toolName: "search", threadLimit: 5, runLimit: 3 });

const databaseLimiter = toolCallLimitMiddleware({ toolName: "query_database", threadLimit: 10 });

const strictLimiter = toolCallLimitMiddleware({ toolName: "scrape_webpage", runLimit: 2, exitBehavior: "error" });



const agent = createAgent({

  model: "gpt-6.1-sol",

  tools: [searchTool, databaseTool, scraperTool],

  middleware: [globalLimiter, searchLimiter, databaseLimiter, strictLimiter],

});

```
```

片段[4] `oss__javascript__langchain__middleware__built-in#036` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool call limit

```text
```

import { createAgent, toolCallLimitMiddleware } from "langchain";



const agent = createAgent({

  model: "gpt-6.1-sol",

  tools: [searchTool, databaseTool],

  middleware: [

    toolCallLimitMiddleware({ threadLimit: 20, runLimit: 10 }),

    toolCallLimitMiddleware({

      toolName: "search",

      threadLimit: 5,

      runLimit: 3,

    }),

  ],

});

```
```

片段[5] `oss__javascript__langchain__middleware__built-in#039` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool call limit

```text
- 'end' - Stop execution immediately with a ToolMessage and AI message for the exceeded tool call. Only works when limiting a single tool; throws error if other tools have pending calls.
```

---

## v2-G-012（single-hop）

**问题**：MCP 连接默认的缓存模式 `"use"` 到底是什么行为？和 `"bypass"` 的差别在哪？

**gold**：use 是默认值：能拿到有效的 cached tool list 就直接用缓存，拿不到才去拉取并把结果写进缓存。bypass 则是每次 fetch 一份新的工具列表，既不读缓存也不更新缓存。所以想强制刷新又不想污染缓存时用 bypass。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：

- `"use"` 是默认缓存模式：当存在有效的缓存工具列表时直接返回缓存，否则去拉取并存入缓存 [10]。
- `"bypass"` 则完全不读缓存、也不更新缓存，直接拉取一份全新的工具列表 [1]。
- 两者差别可以概括为：`"use"` 会复用有效缓存（缓存缺失时才请求），`"bypass"` 强制跳过缓存、每次都重新获取 [10][1]。
- 补充：文档里还提到 `"refresh"` 用于刷新发现缓存，且刷新失败时之前返回的工具仍可继续使用 [3]；这与 `"bypass"` 不是同一个模式，注意区分。

最小可用示例（Python，来自片段 [2]）：

```python
async with MCPAdapter(config) as adapter:
    tools = await adapter.list_tools(cache_mode="use")
    return create_agent("claude-sonnet-5", tools)
```

说明：片段 [2] 的注释也印证了 `"use"` 的语义——在服务器 TTL 内提供缓存的工具列表，而不是每次运行都重新列举 [2]。

需要提醒的差异点：你问的是 `"use"` 和 `"bypass"`，片段中 `"use"` 的完整定义出现在 [10]（标注为同页相邻片段·非检索命中），`"bypass"` 的定义在 [1]；两者分别来自 JavaScript 文档页面的 Caching 小节，Python 侧片段 [2] 只给了 `"use"` 的用法示例，未给出 `"bypass"` 的 Python 写法。

**top5 片段**：

片段[1] `oss__javascript__langchain__mcp__connections#006` ｜ Connections ｜ Caching

```text
- "bypass" : Fetch a fresh tool list without reading or updating the response cache.
```

片段[2] `oss__python__langchain__mcp__connections#007` ｜ Connections ｜ Scale a deployment

```text
```

SERVERS = {

    "weather": "http://localhost:8001/mcp",

    "calc": "http://localhost:8002/mcp",

}



async def make_graph():

    """Build an agent over an MCP fleet. Called once per run by `langgraph dev`."""

    config = {"mcpServers": {name: {"url": url} for name, url in SERVERS.items()}}

    # A long-lived deployment discovers per run, but reuses one HTTP connection

    # pool underneath. `cache_mode="use"` serves a cached tool list within the

    # server's TTL instead of re-listing on every run.

    async with MCPAdapter(config) as adapter:

        tools = await adapter.list_tools(cache_mode="use")

        return create_agent("claude-sonnet-5", tools)

```
```

片段[3] `oss__javascript__migrate__langchain-mcp-adapters#052` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ Lifecycle

```text
- Discovery cache : listTools([], { cacheMode: "refresh" }) refreshes discovery; cacheMode: "bypass" skips the cache. A failed refresh keeps previously returned tools usable.
```

片段[4] `oss__javascript__integrations__tools__anthropic#031` ｜ Anthropic integration ｜ MCP toolset

```text
```

const response = await llm.invoke("Use tools from both servers", {

  mcp_servers: [

    {

      type: "url",

      url: "https://mcp.example1.com/sse",

      name: "mcp-server-1",

      authorization_token: "TOKEN1",

    },

    {

      type: "url",

      url: "https://mcp.example2.com/sse",

      name: "mcp-server-2",

      authorization_token: "TOKEN2",

    },

  ],

  tools: [

    tools.mcpToolset_20251120({ serverName: "mcp-server-1" }),

    tools.mcpToolset_20251120({

      serverName: "mcp-server-2",

      defaultConfig: { deferLoading: true },

    }),

  ],

});

```
```

片段[5] `oss__python__langchain__mcp__connections#011` ｜ Connections ｜ Protocol eras

```text
``` from fastmcp.client import Client async def agent_across_eras(legacy_target, modern_target): # MCP has two protocol eras. FastMCP negotiates per connection, so a # separate adapter per server lets each keep the best era its own server # supports. `mode="legacy"` pins the handshake era; `mode="auto"` (the # default) negotiates the newest the server understands. legacy = Client(legacy_target, mode="legacy") modern = Client(modern_target, mode="auto") async with ( MCPAdapter(legacy) as legacy_adapter, MCPAdapter(modern) as modern_adapter, ): tools = await legacy_adapter.list_tools() + await modern_adapter.list_tools() return create_agent("claude-sonnet-5", tools) ```
```

---

## v2-G-013（single-hop）

**问题**：用 `CompiledSubAgent` 挂一个已有图当子代理时，`runnable` 字段有什么硬性要求？它的 `mode` 默认是什么？

**gold**：runnable 必须是已经 compile 过的 LangGraph 图，也就是先调用 .compile() 再传进来。name 和 description 都是必填，name 会成为 AIMessage 与流式输出上的元数据，便于区分是哪个 agent。mode 可选 isolated 或 fork，默认 isolated；设成 fork 才会继承父级的 message history，但那个 compiled 图仍然用自己的 system prompt。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- `runnable` 是必填字段（Required），类型为 `Runnable`，且必须是一个**已经调用过 `.compile()` 编译好的 LangGraph 图** [1][2]。
- `mode` 是可选字段（Optional），**默认值为 `"isolated"`**；设为 `"fork"` 时会继承父代理的消息历史，但无论哪种模式，编译好的图都保留自己的 system prompt [1][2]。

**最小可用示例（Python）：**

```python
from deepagents import CompiledSubAgent
from langchain.agents import create_agent

custom_graph = create_agent(
    model="openai:gpt-6.1-sol",
    tools=[],
    system_prompt="You are a specialized agent for data analysis...",
)

custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="Specialized agent for complex data analysis tasks",
    runnable=custom_graph,  # 需为已 compile 的图
)
```

[3]

**补充说明：** 片段中 `runnable` 的描述是「A compiled LangGraph graph (must call `.compile()` first)」[1][2]，示例里传入的是 `create_agent(...)` 的返回值 [3]；若你手写 StateGraph，需自行先 `.compile()` 再传入（片段 [5] 中 `weather_graph = create_weather_graph()` 内部即 `return workflow.compile()`）[5]。

**top5 片段**：

片段[1] `oss__python__deepagents__subagents#009` ｜ Subagents ｜ Custom subagents > CompiledSubAgent

```text
| Field | Type | Description |

| --- | --- | --- |

| name | str | Required. Unique identifier for the subagent. The subagent name becomes metadata for AIMessage s and for streaming, which helps to differentiate between agents. |

| description | str | Required. What this subagent does. |

| runnable | Runnable | Required. A compiled LangGraph graph (must call .compile() first). |

| mode | "isolated" \| "fork" | Optional. Defaults to "isolated" . Set to "fork" to inherit the parent’s message history. The compiled graph keeps its own system prompt either way. See Forked subagents . |
```

片段[2] `oss__javascript__deepagents__subagents#008` ｜ Subagents ｜ Custom subagents > CompiledSubAgent

```text
| Field | Type | Description |

| --- | --- | --- |

| name | str | Required. Unique identifier for the subagent. The subagent name becomes metadata for AIMessage s and for streaming, which helps to differentiate between agents. |

| description | str | Required. What this subagent does. |

| runnable | Runnable | Required. A compiled LangGraph graph (must call .compile() first). |

| mode | "isolated" \| "fork" | Optional. Defaults to "isolated" . Set to "fork" to inherit the parent’s message history. The compiled graph keeps its own system prompt either way. See Forked subagents . |
```

片段[3] `oss__python__deepagents__subagents#014` ｜ Subagents ｜ Using CompiledSubAgent

```text
``` from deepagents import CompiledSubAgent, create_deep_agent from langchain.agents import create_agent def internet_search(query: str) -> str: """Run a web search.""" return f"search results for {query}" research_instructions = "You are a research coordinator." your_model = "openai:gpt-6.1-sol" specialized_tools: list = [] # Create a custom agent graph custom_graph = create_agent( model=your_model, tools=specialized_tools, system_prompt="You are a specialized agent for data analysis...", ) # Use it as a custom subagent custom_subagent = CompiledSubAgent( name="data-analyzer", description="Specialized agent for complex data analysis tasks", runnable=custom_graph, )
```

片段[4] `oss__javascript__deepagents__subagents#033` ｜ Subagents ｜ Using CompiledSubAgent

```text
Agent({ model: yourModel, tools: specializedTools, systemPrompt: "You are a specialized agent for data analysis...", }); // Use it as a custom subagent const customSubagent: CompiledSubAgent = { name: "data-analyzer", description: "Specialized agent for complex data analysis tasks", runnable: customGraph, }; const subagents = [customSubagent]; const agent = createDeepAgent({ model: "openai:gpt-6.1-sol", tools: [internetSearch], systemPrompt: researchInstructions, subagents: subagents, }); ```
```

片段[5] `oss__python__langchain__middleware__built-in#072` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Subagent

```text
dge(START, "respond") workflow.add_edge("respond", END) return workflow.compile() weather_graph = create_weather_graph() # Wrap it in a CompiledSubAgent weather_subagent = CompiledSubAgent( name="weather", description="This subagent can get weather in cities.", runnable=weather_graph, ) agent = create_agent( model="google_genai:gemini-4-hydrogen", middleware=[ SubAgentMiddleware( backend=StateBackend(), subagents=[weather_subagent], ) ], ) ```
```

---

## v2-G-014（single-hop）

**问题**：用 `CompositeBackend` 把记忆和文档分别挂到不同后端之后，deep agent 自己产生的中间数据（比如被 offload 的工具结果）会落到哪里？官方建议默认后端用哪个？

**gold**：deep agent 会把内部数据写到默认后端，包括 offloaded tool results 和 conversation history。官方建议默认后端用 StateBackend，这样这些中间产物只存在于本次运行、保持 ephemeral，不会写进磁盘或持久化存储。真正要长期保留的内容再通过路由指到别的后端。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. Deep Agents 会把内部数据（被 offload 的工具结果、对话历史等）写到**默认后端（default backend）** [1][2]。
2. 官方建议把 `StateBackend` 作为默认后端，让这些中间产物保持临时性（ephemeral），避免写入磁盘或持久化存储 [1][2]。
3. 在 `CompositeBackend` 里，`default=StateBackend()` 就是承担这个角色的位置；`routes` 里配置的 `StoreBackend` 只负责匹配到的路径前缀（如 `/memories/`、`/policies/`）[3][5][6]。
4. 补充注意：使用 `StoreBackend` 路由时，需要确保通过 `create_deep_agent(model=..., store=...)` 提供了 store，或由平台提供 [8][10]。片段 [5][6] 的注释也强调 store 是传给 `create_deep_agent`，而不是传给 backend。

**最小可用示例**（来自片段 [5]，Python）：

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),
        },
    ),
    store=InMemoryStore(),  # Store passed to create_deep_agent, not backend
)
```

在这个例子里：`/memories/` 下的内容走 `StoreBackend` 持久化，其余路径（包括 agent 自身的中间数据）落到 `default=StateBackend()`，保持临时 [1][2][5]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__backends#072` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[2] `oss__python__deepagents__backends#087` ｜ Backends ｜ Route to different backends

```text
- Deep Agents write internal data (offloaded tool results, conversation history) to the default backend. Use StateBackend as the default to keep these artifacts ephemeral and avoid writing them to disk or a persistent store. See the FilesystemBackend tip for a complete example.
```

片段[3] `oss__python__deepagents__memory#016` ｜ Memory ｜ Advanced usage > Organization-level memory

```text
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend



agent = create_deep_agent(

    model="google_genai:gemini-4-hydrogen",

    memory=[

        "/memories/preferences.md",

        "/policies/compliance.md",

    ],

    backend=CompositeBackend(

        default=StateBackend(),

        routes={

            "/memories/": StoreBackend(

                namespace=lambda rt: (rt.server_info.user.identity,),

            ),

            "/policies/": StoreBackend(

                namespace=lambda rt: (rt.context.org_id,),

            ),

        },

    ),

)

```
```

片段[4] `oss__python__deepagents__going-to-production#027` ｜ Going to production ｜ Memory > Configuration

```text
``` from deepagents import create_deep_agent from deepagents.backends import CompositeBackend, StateBackend, StoreBackend agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", backend=CompositeBackend( default=StateBackend(), routes={ "/memories/": StoreBackend( namespace=lambda rt: ( rt.server_info.assistant_id, rt.server_info.user.identity, ), ), }, ), system_prompt="""You have persistent memory at /memories/. Read /memories/instructions.txt at the start of each conversation for accumulated knowledge and preferences. When you learn something that should persist, update that file.""", ) ```
```

片段[5] `oss__python__deepagents__backends#077` ｜ Backends ｜ Built-in backends > CompositeBackend (router)

```text
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="baseten:zai-org/GLM-5.2",

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

---

## v2-G-015（multi-hop）

**问题**：有人在 A 机器上把图跑到 `interrupt` 暂停，隔天在 B 机器上用同一个 `config = { configurable: { thread_id: "thread-1" } }` 继续 `await graph.invoke(new Command({ resume: true }), config)`，为什么能接上？

**gold**：因为 thread_id 是回到已保存 checkpoint 的 durable pointer，恢复时按它把那条线程的状态取回来。而 Checkpointers 的作用正是把一个 thread 的 graph state 按 checkpoint 持久化。两者配合，暂停点与已完成步骤才能跨进程、跨机器延续下去。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：能接上，是因为 `thread_id` 是持久化指针，指向保存下来的 checkpoint；恢复时必须使用与中断发生时相同的 thread ID。** [1][7]

具体来说：

1. **`thread_id` 是持久化指针**：文档注释明确写着 `thread_id is the durable pointer back to the saved checkpoint` [1]，Python 版也说明它是 `the persistent pointer (stores a stable ID in production)` [4]。所以只要 checkpoint 存储本身是跨机器可访问的（例如共享的持久化存储），B 机器用同一个 `thread_id` 就能定位到 A 机器中断时保存的那份状态。

2. **恢复时必须用同一个 thread ID**：文档明确要求 `You must use the same thread ID when resuming that was used when the interrupt occurred` [7]。你给的 `thread-1` 与中断时一致，满足这个条件。

3. **`Command({ resume })` 的作用**：它把 resume 的值作为节点内 `interrupt()` 的返回值，被中断的节点会从头重新开始执行 [6][8]。所以恢复动作本身不依赖是哪台机器，只依赖 checkpoint 和 thread ID。

**最小可用示例（JavaScript，与片段一致）：**

```javascript
import { Command } from "@langchain/langgraph";

// A 机器：跑到 interrupt 暂停
const config = { configurable: { thread_id: "thread-1" } };
const result = await graph.invoke({ input: "data" }, config);
console.log(result.__interrupt__);
// [{ value: 'Do you approve this action?', ... }]

// B 机器：用同一个 thread_id 恢复
await graph.invoke(new Command({ resume: true }), config);
```

**需要指出的差异/前提：**

- 片段只说明了 `thread_id` 是“指向已保存 checkpoint 的持久指针” [1][4]，以及恢复必须用同一 thread ID [7]。**片段没有说明 checkpoint 具体存在哪里、是否默认跨机器共享**。因此“B 机器能接上”隐含的前提是：B 机器能访问到 A 机器写入的同一份 checkpoint 存储——这一点文档片段里没有展开，属于片段未覆盖的内容。
- 另外注意 API 版本差异：Python 片段中出现了 `version="v2"` 参数，且返回值是 `GraphOutput`，用 `result.interrupts` 读取中断信息 [4]；而 JavaScript 片段用 `result.__interrupt__` [1]。如果你在 Python 侧照搬 JS 的 `__interrupt__` 写法，会与片段 [4] 不一致。

**top5 片段**：

片段[1] `oss__javascript__langgraph__interrupts#009` ｜ Interrupts ｜ Resuming interrupts

```text
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
```

片段[2] `oss__python__langgraph__use-time-travel#011` ｜ Use time-travel ｜ Interrupts

```text
{"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human history = list(graph.get_state_history(config)) before_ask = [s for s in history if s.next == ("ask_human",)][-1] replay_result = graph.invoke(None, before_ask.config) # Pauses at interrupt — waiting for new Command(resume=...) # Fork from before ask_human fork_config = graph.update_state(before_ask.config, {"value": ["forked"]}) fork_result = graph.invoke(None, fork_config) # Pauses at interrupt — waiting for new Command(resume=...) # Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value":
```

片段[3] `oss__python__langgraph__streaming#063` ｜ Streaming ｜ Advanced > Migrate to v2 > v2 invoke format

```text
```

config = {"configurable": {"thread_id": "thread-1"}}

result = graph.invoke(inputs, config=config)



if "__interrupt__" in result:

    print(result["__interrupt__"][0].value)

    graph.invoke(Command(resume=True), config=config)

```
```

片段[4] `oss__python__langgraph__streaming#062` ｜ Streaming ｜ Advanced > Migrate to v2 > v2 invoke format

```text
```

config = {"configurable": {"thread_id": "thread-1"}}

result = graph.invoke(inputs, config=config, version="v2")



if result.interrupts:

    print(result.interrupts[0].value)

    graph.invoke(Command(resume=True), config=config, version="v2")

```
```

片段[5] `oss__python__langgraph__interrupts#009` ｜ Interrupts ｜ Resuming interrupts

```text
```

from langgraph.types import Command



# Initial run - hits the interrupt and pauses

# thread_id is the persistent pointer (stores a stable ID in production)

config = {"configurable": {"thread_id": "thread-1"}}

result = graph.invoke({"input": "data"}, config=config, version="v2")



# result is a GraphOutput with .value and .interrupts

# .interrupts contains the payloads passed to interrupt()

print(result.interrupts)

# > (Interrupt(value='Do you approve this action?'),)



# Resume with the human's response

# The resume payload becomes the return value of interrupt() inside the node

resumed = graph.invoke(Command(resume=True), config=config, version="v2")

```
```

---

## v2-G-016（multi-hop）

**问题**：只想把某个节点吐出的 token 打出来：用 `{ streamMode: "messages" }` 时靠什么字段过滤？换成 v3 的 streamEvents 之后，同样的文本增量又该从哪个事件里取？

**gold**：messages 模式下每个元素是 [messageChunk, metadata] 元组，metadata 里的 langgraph_node 就是发起这次模型调用的节点名，用它比对目标节点即可只保留该节点的 token。改成事件流接口之后，先筛 event.method 为 messages，再取 event.params.data，并且只处理 data.event 为 content-block-delta 的事件。其中 block.type 为 text-delta 时文本在 block.text。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. 用 `{ streamMode: "messages" }` 时，`messages` 模式返回 `[messageChunk, metadata]` 元组，其中 `metadata` 里带有 `langgraph_node` 字段，用它来判断 token 来自哪个节点 [3][4]。Python 侧在 `version="v2"` 下是 `chunk["type"] == "messages"` 时取 `chunk["data"]` 得到 `(msg, metadata)`，再判断 `metadata["langgraph_node"] == "some_node_name"` [4]；JS 侧直接 `for await (const [msg, metadata] of ...)`，判断 `metadata.langgraph_node === "some_node_name"` [3]。
2. 换成 v3 的 `stream_events` 后，文本增量从 `stream.messages` 里取，每条消息用 `message.text` 拿文本、`message.output.usage_metadata` 拿用量 [6]。注意片段 [6] 只展示了 `stream.messages` 与 `message.text`，**没有**展示按节点过滤的字段，所以 v3 下如何按节点过滤，给出的文档里没有找到能回答这个问题的内容。

**最小可用示例（messages 模式，按节点过滤）：**

Python [4]：
```python
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

JS [3]：
```javascript
for await (const [msg, metadata] of await graph.stream(
  inputs,
  { streamMode: "messages" }
)) {
  if (msg.content && metadata.langgraph_node === "some_node_name") {
    // ...
  }
}
```

**v3 取文本增量（片段未含节点过滤）：**

Python [6]：
```python
stream = graph.stream_events(input, version="v3")

for message in stream.messages:
    text = str(message.text)
    usage = message.output.usage_metadata
    print(text)
    print(usage)
```

**补充说明（与问题相关的差异）：** 片段里还出现了按 `metadata["tags"]` 过滤 LLM 调用的写法（给模型打 `tags=["joke"]`，再判断 `metadata["tags"] == ["joke"]`）[1][8][9]，这是按 LLM 调用标签过滤，不是按节点过滤；按节点过滤要用 `langgraph_node` [3][4]。

**top5 片段**：

片段[1] `oss__python__langgraph__streaming#022` ｜ Streaming ｜ Stream modes > LLM tokens > Filter by LLM invocation

```text
"messages": msg, metadata = chunk["data"] # Filter the streamed tokens by the tags field in the metadata to only include # the tokens from the LLM invocation with the "joke" tag if metadata["tags"] == ["joke"]: print(msg.content, end="|", flush=True) ```
```

片段[2] `oss__javascript__langgraph__streaming#010` ｜ Streaming ｜ Stream modes > LLM tokens > Filter by LLM invocation

```text
cats" }, { streamMode: "messages" } )) { // Filter the streamed tokens by the tags field in the metadata to only include // the tokens from the LLM invocation with the "joke" tag if (metadata.tags?.includes("joke")) { console.log(msg.content + "|"); } } ```
```

片段[3] `oss__javascript__langgraph__streaming#019` ｜ Streaming ｜ View example trace > Filter by node

```text
```

// The "messages" stream mode returns a tuple of [messageChunk, metadata]

// where messageChunk is the token streamed by the LLM and metadata is a dictionary

// with information about the graph node where the LLM was called and other information

for await (const [msg, metadata] of await graph.stream(

  inputs,

  { streamMode: "messages" }

)) {

  // Filter the streamed tokens by the langgraph_node field in the metadata

  // to only include the tokens from the specified node

  if (msg.content && metadata.langgraph_node === "some_node_name") {

    // ...

  }

}

```
```

片段[4] `oss__python__langgraph__streaming#030` ｜ Streaming ｜ View example trace > Filter by node

```text
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
```

片段[5] `oss__javascript__langgraph__streaming#018` ｜ Streaming ｜ Stream modes > LLM tokens > Omit messages from the stream

```text
okens from this model are omitted from streamMode: "messages" because of nostream const r = await internalModel.invoke([ { role: "user", content: `Private notes on ${state.topic}` }, ]); return { notes: contentToText(r.content) }; }; const graph = new StateGraph(State) .addNode("writeAnswer", writeAnswer) .addNode("internal_notes", internalNotes) .addEdge(START, "writeAnswer") .addEdge("writeAnswer", "internal_notes") .compile(); const stream = await graph.streamEvents( { topic: "AI", answer: "", notes: "" }, { version: "v3" }, ); ```
```

---

## v2-G-017（multi-hop）

**问题**：用 `streamEvents` 观察子图进度时，如果中断发生在某个子图内部，外层要怎么同时拿到子图事件和中断信息，之后又怎么续跑？

**gold**：streamEvents(input, { version: "v3" }) 返回的对象上有 stream.subgraphs，可以用 for await 遍历，每项带 subgraph.name 与 subgraph.path，内层还能继续读 subgraph.messages。中断状态在外层流上判断：stream.interrupted 为真时，中断内容在 stream.interrupts。续跑时把 new Command({ resume: ... }) 作为新的输入再调一次 streamEvents，最终状态取 stream.output。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答这个问题的内容。

具体缺口：

1. **“同时拿到子图事件和中断信息”**：片段 [3] 只展示了 JS 侧 `streamEvents` 里遍历 `stream.messages`（注释提到“including any in subgraphs”）以及读取 `stream.interrupts[0].payload` 的写法，但没有说明子图内部中断时外层如何同时获取子图事件与中断信息；片段 [5] 只说明 `stream.interrupts` 会承载 `interrupt()` 的 payload、`stream.interrupted` 为 True，未涉及子图场景。片段 [4] 提到“the subagent's tool calls interrupt()”，但只给了 `stream.output` 驱动和 `stream.interrupts` 存在的注释，没有展开子图事件与外层中断的合并获取方式。

2. **“之后怎么续跑”**：片段 [1]/[8] 给出的是**多个并行中断**用 `Command(resume=resume_map)` 一次性续跑的写法（`resume_map = {i.id: ... for i in stream.interrupts}`），片段 [4] 给出的是单个中断 `Command(resume=True)` 的续跑，片段 [7] 给出的是子图带独立 checkpointer 时逐次 `invoke(Command(resume=...))` 的续跑。但没有片段说明“子图内部中断、外层 streamEvents 观察”这一组合下的续跑方式（例如续跑时是否仍用外层 `stream_events`、resume 值如何对应子图中断）。

3. **片段 [2] 只提到**外层 `invoke()`/`stream_events()` 必须带 `thread_id` 以便 checkpoint 和 resume [2]，这是前提条件，但不构成对上述两个问题的回答。

另外提示一处可能的名称差异：你问的是 `streamEvents`，Python 片段中对应写法是 `graph.stream_events(..., version="v3")` [1][4][5][6]，JS 片段中才是 `graph.streamEvents(..., { version: "v3" })` [3]；两者不是同一个 API 名，请按所用语言区分。

**top5 片段**：

片段[1] `oss__python__langgraph__interrupts#028` ｜ Interrupts ｜ View example trace > Handling multiple interrupts

```text
dge("a", END) .add_edge("b", END) .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Step 1: stream events to drive the run; both parallel nodes hit interrupt() and pause stream = graph.stream_events({"vals": []}, config, version="v3") _ = stream.output  # drive the stream to completion # stream.interrupts contains the pending Interrupt payloads print(stream.interrupts) # > (Interrupt(value='question_a', id='...'), Interrupt(value='question_b', id='...')) # Step 2: resume all pending interrupts at once resume_map = { i.id: f"answer for {i.value}" for i in stream.interrupts } resumed = graph.stream_events(Command(resume=resume_map), config, version="v3")
```

片段[2] `oss__python__migrate__langgraph-supervisor#010` ｜ Migrate from langgraph-supervisor ｜ Migrate interrupt and resume flows > Requirements for interrupt propagation

```text
2. Pass thread_id in configurable . The outer invoke() or stream_events() call must include a thread_id so the graph can checkpoint and resume.
```

片段[3] `oss__javascript__langgraph__interrupts#023` ｜ Interrupts ｜ Common patterns > Stream with human-in-the-loop (HITL) interrupts

```text
``` import { Command } from "@langchain/langgraph"; let streamInput: Record<string, unknown> | Command = initialInput; while (true) { const stream = await graph.streamEvents(streamInput, { ...config, version: "v3", }); // Stream LLM message chunks (including any in subgraphs) as they arrive. for await (const message of stream.messages) { for await (const token of message.text) { displayStreamingContent(token); } } // After the run finishes (or pauses), check for interrupts and resume. if (!stream.interrupted) { const finalState = await stream.output; break; } const interruptInfo = stream.interrupts[0].payload; const userResponse = await getUserInput(interruptInfo);
```

片段[4] `oss__python__langgraph__use-subgraphs#025` ｜ Subgraphs ｜ Subgraph persistence > Stateful > Per-invocation (default)

```text
```

from langgraph.types import Command



config = {"configurable": {"thread_id": "1"}}



# Stream events - the subagent's tool calls interrupt()

stream = agent.stream_events(

    {"messages": [{"role": "user", "content": "Tell me about apples"}]},

    config=config,

    version="v3",

)

output = stream.output  # drive the stream to completion

# stream.interrupts contains pending interrupts (and stream.interrupted is True)



# Resume - approve the interrupt

resumed = agent.stream_events(Command(resume=True), config=config, version="v3")

final = resumed.output

```
```

片段[5] `oss__python__langgraph__interrupts#002` ｜ Interrupts ｜ ROOT

```text
- Interrupt payloads surface via stream.interrupts : when using event streaming ( graph.stream_events(..., version="v3") ), the values you pass to interrupt() appear on stream.interrupts , and stream.interrupted is True when the run pauses for input.
```

---

## v2-G-018（multi-hop）

**问题**：给每个终端用户传自己的 `Authorization` header 去连 MCP，同时 server 配置里也写了同名 header，谁生效？不同用户之间的工具列表缓存会不会串？

**gold**：Server-configured headers 会压过同名的 method-level header，且不分大小写；provider token 又压过这两者。所以既要按用户传 Authorization，就应该把这个 header 从 server 配置里删掉，否则用户自己的凭证会被配置值盖住。缓存侧则是隔离的：Catalogs 按 provider object 与 headers 索引，一个用户不会拿到另一个用户缓存的工具列表。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. **同名 header 谁生效**：server 配置里的 header 优先于方法级传入的同名 header，且不区分大小写。所以如果你在 server 配置里也写了 `Authorization`，方法级传的同名 header 会被覆盖。要按用户传 `Authorization`，应当把它从 server 配置里省略掉 [1]。另外，一旦 provider 拿到了 token，token 会优先于配置的 `Authorization` header；在拿到 token 之前，则发送配置的 header [4]。
2. **不同用户之间缓存会不会串**：不会。工具目录（catalogs）按 provider 对象和 headers 作为键来隔离，因此一个用户不会拿到另一个用户缓存的工具列表 [3]。但要注意：当同一个 provider 对象背后的账号发生变化时，需要重建 adapter [3]；并且每个不同的 provider 对象各自拥有独立连接，应「每个用户复用一个 provider 对象」，而不是每次调用都新建 [9]。
3. **一个容易踩的坑**：方法级 options 里的 `authProvider` 或 `headers` 会作用于该 adapter 持有的**所有** HTTP 和 SSE server，而不只是你指定的那个；当不同用户需要不同凭据时，应使用单 server 的 adapter [10]。方法级 `authProvider` 会替换掉配置的那个，方法级 headers 会被加到每个 server 的配置 headers 上，同名时配置的 header 获胜 [2]。

**最小可用示例**（单 server adapter + 每用户复用一个 provider 对象，server 配置中不写 `Authorization`）

```ts
import { MCPAdapter, type AuthProvider } from "@langchain/mcp-adapters";

// 单 server adapter：每个用户带不同凭据
const crm = new MCPAdapter({
  servers: {
    crm: { url: "https://crm.example.com/mcp" }, // 不要在这里配置 Authorization
  },
});

// 每个用户复用一个 provider 对象：每个对象各自开一条连接
const providers = new Map<string, AuthProvider>();

function providerFor(userId: string): AuthProvider {
  let provider = providers.get(userId);
  if (!provider) {
    provider = { token: async () => tokenFor(userId) };
    providers.set(userId, provider);
  }
  return provider;
}

const tools = await crm.listTools(["crm"], {
  authProvider: providerFor(userId),
});
```

（示例结构来自 [8]，配合 [1][3][9][10] 的约束。）

**与提问说法的差异提示**：你问的是「传 `Authorization` header」，而片段中按用户鉴权的主推方式是传 `authProvider`（provider 的 token）[8]；若确实要传 header，需注意 server 配置同名 header 会赢 [1]，且方法级 headers 会作用于 adapter 下所有 server [10]。

**top5 片段**：

片段[1] `oss__javascript__langchain__mcp__auth#017` ｜ Authentication ｜ Per-user authentication

```text
- Header precedence : Server-configured headers take precedence over same-named method-level headers, regardless of capitalization. When passing a per-user Authorization header, omit that header from the server configuration. A provider token still takes precedence over either header.
```

片段[2] `oss__javascript__migrate__langchain-mcp-adapters#034` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ Authentication

```text
- Overrides : Tool catalogs are separate for different headers and provider objects. Recreate the adapter when the account behind a provider object changes. A method-level authProvider replaces the configured one, and method-level headers are added to each server’s configured headers, where a configured header with the same name wins. Both apply to every HTTP/SSE server, even when you select tools from only one server.
```

片段[3] `oss__javascript__langchain__mcp__auth#019` ｜ Authentication ｜ Per-user authentication

```text
- Isolated catalogs : Catalogs are keyed by provider object and headers, so one user never receives another user’s cached tool list. Recreate the adapter when the account behind the same provider object changes.
```

片段[4] `oss__javascript__migrate__langchain-mcp-adapters#030` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ Authentication

```text
- Header precedence : Once a provider has a token, it takes precedence over a configured Authorization header. Until then, the configured header is sent.
```

片段[5] `oss__javascript__integrations__tools__anthropic#031` ｜ Anthropic integration ｜ MCP toolset

```text
```

const response = await llm.invoke("Use tools from both servers", {

  mcp_servers: [

    {

      type: "url",

      url: "https://mcp.example1.com/sse",

      name: "mcp-server-1",

      authorization_token: "TOKEN1",

    },

    {

      type: "url",

      url: "https://mcp.example2.com/sse",

      name: "mcp-server-2",

      authorization_token: "TOKEN2",

    },

  ],

  tools: [

    tools.mcpToolset_20251120({ serverName: "mcp-server-1" }),

    tools.mcpToolset_20251120({

      serverName: "mcp-server-2",

      defaultConfig: { deferLoading: true },

    }),

  ],

});

```
```

---

## v2-G-019（multi-hop）

**问题**：想让模型直接按 schema 出结构化结果，同时又要兜住偶发的格式错误，官方给的组合拳是什么？

**gold**：首选模型级结构化输出：用 withStructuredOutput 把 schema 绑到模型上，provider 支持原生结构化输出时会强制 schema，从而避免大部分 parsing failures。如果仍然拿到坏格式，就在外面套 OutputFixingParser.fromLLM(model, baseParser)，让一个模型去修。baseParser 可以用 StructuredOutputParser.fromZodSchema(...) 构造。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：官方文档给出的组合思路是——**优先用模型级结构化输出（把 schema 绑定到模型上），让 provider 原生强制 schema、从源头避免大多数解析失败；对仍然出现的格式错误，再用修复/重试机制兜底**。具体分两条线：

1. **首选：模型级结构化输出**
   - Python 用 `with_structured_output` 把 schema 绑定到模型；当 provider 支持原生结构化输出时，会强制 schema 并避免大多数解析失败，模型支持时就用这种方式 [1]。
   - JavaScript 对应的是 `withStructuredOutput`，说明相同 [2]。

2. **兜底：解析失败后的修复/重试**
   - 用 `OutputFixingParser`（来自 `langchain-classic`）包住输出解析器：解析失败时，把畸形输出、解析器的格式说明和错误信息一起发给模型，再解析修正后的响应 [7]；JS 版来自 `@langchain/classic` [9]。
   - 工具调用策略下可用 `ToolStrategy(..., handle_errors=...)` 控制只对特定异常重试，例如只对 `ValueError` 重试、其他异常直接抛出 [3]；也可传元组同时重试多种异常，如 `(ValueError, TypeError)` [11]。
   - 模型拒答场景可加 `ModelRefusalMiddleware`（Python `create_agent` 的 `middleware` 参数）[8]；JS 为 `modelRefusalMiddleware()` [10]。

最小可用示例（Python，模型级结构化 + 解析失败修复）：

```python
from langchain_classic.output_parsers import OutputFixingParser

# 1) 模型级结构化输出：schema 绑定到模型，provider 原生支持时强制 schema
structured_llm = model.with_structured_output(ProductRating)  # [1]

# 2) 兜底：解析失败时让模型修正畸形输出
fixing_parser = OutputFixingParser.from_llm(  # [7]
    parser=base_parser,
    llm=model,
)
```

最小可用示例（Python，工具调用策略下限定重试的异常类型）：

```python
ToolStrategy(
    schema=ProductRating,
    handle_errors=ValueError  # 只对 ValueError 重试，其他异常抛出 [3]
)
```

需要指出的差异/注意点：
- 片段中 Python 的模型级方法是 `with_structured_output` [1]，JS 是 `withStructuredOutput` [2]，两者命名风格不同，不要混用。
- `OutputFixingParser` 明确来自 `langchain-classic`（Python）[7] / `@langchain/classic`（JS）[9]，不是主包。
- 片段 [4][5][6][14] 展示的是 `createAgent` + `responseFormat` 的 agent 级结构化输出写法（结果取 `result.structuredResponse`），与 [1][2] 的“模型级绑定”是不同层面的做法；文档在“处理解析错误”一节推荐的是模型级绑定 [1][2]。

给出的文档里没有找到能说明“模型级结构化输出 + OutputFixingParser 必须同时使用”的明确组合示例，上述组合是按片段 [1][2] 的推荐做法与 [7][9] 的修复机制归纳的；若需要官方给出的单一“组合拳”代码，片段中未提供。

**top5 片段**：

片段[1] `oss__python__langchain__structured-output#053` ｜ Structured output ｜ Handle parsing errors in chains

```text
- Model-level structured output : Bind the schema to the model with with_structured_output . When the provider supports native structured output, it enforces the schema and avoids most parsing failures. See Models - Structured output . Use this approach when the model supports it.
```

片段[2] `oss__javascript__langchain__structured-output#035` ｜ Structured output ｜ Handle parsing errors in chains

```text
- Model-level structured output : Bind the schema to the model with withStructuredOutput . When the provider supports native structured output, it enforces the schema and avoids most parsing failures. See Models - Structured output . Use this approach when the model supports it.
```

片段[3] `oss__python__langchain__structured-output#044` ｜ Structured output ｜ Tool calling strategy > Error handling > Error handling strategies

```text
```

ToolStrategy(

    schema=ProductRating,

    handle_errors=ValueError  # Only retry on ValueError, raise others

)

```
```

片段[4] `oss__python__langchain__structured-output#045` ｜ Structured output ｜ Tool calling strategy > Error handling > Error handling strategies

```text
```

ToolStrategy(

    schema=ProductRating,

    handle_errors=(ValueError, TypeError)  # Retry on ValueError and TypeError

)

```
```

片段[5] `oss__javascript__langchain__agents#035` ｜ Agents ｜ Core components > Structured output

```text
```

const Answer = z.object({ summary: z.string(), confidence: z.number() });



var agent = createAgent({

  model: "ollama:north-mini-code-1.0",

  tools,

  responseFormat: Answer,

});

const result = await agent.invoke({

  messages: [{ role: "user", content: "Summarize AI trends" }],

});

result.structuredResponse; // { summary: ..., confidence: ... }

```
```

---

## v2-G-020（multi-hop）

**问题**：既要把技能库放到按用户隔离的存储里，又不想让 agent 看到两套文件系统，`new CompositeBackend(new StateBackend(), { "/skills/": ... })` 这种写法解决了什么？

**gold**：CompositeBackend 让你把多个来源挂进同一个 filesystem，比如长期记忆在 Store 的 /memories/ 下、自定义文档在 /docs/ 下，agent 侧仍然只有一条路径体系。技能库这种场景把它写成默认 StateBackend 加 /skills/ 指向 StoreBackend，并在 namespace 里拼上 assistantId 与 user_id。这样技能文件按用户落在独立命名空间，agent 却只按 /skills/ 前缀访问。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

`new CompositeBackend(new StateBackend(), { "/skills/": ... })` 这种写法解决的是：**把 `/skills/` 这个虚拟路径挂载到独立的持久化存储（StoreBackend）上，而其余路径仍走默认的 StateBackend，从而对 agent 呈现为单一文件系统视图**——agent 只看到一套路径，不需要感知背后是两套存储 [2][6]。

具体来说：

1. **单一虚拟文件系统视图**：`CompositeBackend` 的第一个参数是默认后端（这里是 `StateBackend`），第二个参数是路径前缀到后端的映射。`/skills/` 前缀下的读写被路由到 `StoreBackend`，其他路径仍由 `StateBackend` 处理，agent 侧只看到统一的虚拟路径 [2][6]。

2. **按用户隔离**：`StoreBackend` 的 `namespace` 回调可以按用户维度划分存储，例如 `ctx.config?.configurable?.user_id ?? "anonymous"` [2]，或 `rt.serverInfo.user.identity` [6]。这样不同用户的技能库落在不同命名空间里。

3. **技能库与记忆等可共用同一隔离维度**：片段 [6] 中 `/memories/` 和 `/skills/` 都映射到同一个按用户身份划分的 `StoreBackend` 命名空间，说明这种写法能让多个虚拟路径共享同一套隔离存储，同时对外仍是统一路径空间 [6]。

4. **配合只读/权限控制**：如果希望 agent 使用技能库但不修改，片段建议配合只读技能设置 [11]；在可写技能场景下，可用 `permissions` 的 `deny` 规则把某些路径（如 `/skills/approved/**`）设为只读，并注意规则顺序（更具体的规则放在更宽泛的 deny 规则之前）[1][9][10]。

## 最小可用示例

```javascript
import {
  createDeepAgent,
  CompositeBackend,
  StateBackend,
  StoreBackend,
} from "deepagents";

const agent = await createDeepAgent({
  model: "anthropic:claude-sonnet-4-6",
  skills: ["/skills/"],
  backend: new CompositeBackend(new StateBackend(), {
    "/skills/": new StoreBackend({
      namespace: (ctx) => [
        ctx.assistantId ?? "default",
        ctx.config?.configurable?.user_id ?? "anonymous",
      ],
    }),
  }),
});
```

来源：[2]

## 需要指出的差异/注意点

- 你问题里写的是 `"/skills/": ...`，片段 [1] 的可写技能示例用的是两个更细的前缀 `"/skills/approved/"` 和 `"/skills/editable/"`，并配合 `permissions` 做写保护 [1][9]。若需要区分只读/可写技能库，应按 [1] 的写法拆分前缀，而不是单一 `/skills/`。
- 片段 [1] 的 `namespace` 回调参数命名不一致：`/skills/approved/` 用 `(rt) => [...]`，`/skills/editable/` 用 `(ctx) => [...]`，以片段原文为准 [1]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__skills#065` ｜ Skills ｜ Skill permissions > Writable skills

```text
``` import { InMemoryStore } from "@langchain/langgraph"; import { createDeepAgent, CompositeBackend, StateBackend, StoreBackend, } from "deepagents"; const store = new InMemoryStore(); // Use for local dev; omit for LangSmith Agent Server const agent = await createDeepAgent({ model: "anthropic:claude-sonnet-4-6", backend: new CompositeBackend(new StateBackend(), { "/skills/approved/": new StoreBackend({ namespace: (rt) => ["approved-skills", rt.context.orgId], }), "/skills/editable/": new StoreBackend({ namespace: (ctx) => [ "editable-skills", ctx.config?.configurable?.user_id ?? "anonymous", ], }), }), skills: ["/skills/approved/", "/skills/editable/"], permissions: [ { operations:
```

片段[2] `oss__javascript__deepagents__skills#042` ｜ Skills ｜ Skill availability > Isolate skill libraries

```text
```

import {

  createDeepAgent,

  CompositeBackend,

  StateBackend,

  StoreBackend,

} from "deepagents";



const agent = await createDeepAgent({

  model: "anthropic:claude-sonnet-4-6",

  skills: ["/skills/"],

  backend: new CompositeBackend(new StateBackend(), {

    "/skills/": new StoreBackend({

      namespace: (ctx) => [

        ctx.assistantId ?? "default",

        ctx.config?.configurable?.user_id ?? "anonymous",

      ],

    }),

  }),

});

```
```

片段[3] `oss__python__deepagents__customization#169` ｜ Customize Deep Agents ｜ Skills

```text
file_data(skill_content), } agent = create_deep_agent( model="openai:gpt-6.1-sol", backend=backend, skills=["/skills/"], checkpointer=checkpointer, ) result = agent.invoke( { "messages": [{"role": "user", "content": "What is langgraph?"}], # Seed the default StateBackend's in-state filesystem (virtual paths must start with "/"). "files": skills_files, }, config={"configurable": {"thread_id": "12345"}}, ) ```
```

片段[4] `oss__python__deepagents__customization#177` ｜ Customize Deep Agents ｜ Skills

```text
data(skill_content), } agent = create_deep_agent( model="baseten:zai-org/GLM-5.2", backend=backend, skills=["/skills/"], checkpointer=checkpointer, ) result = agent.invoke( { "messages": [{"role": "user", "content": "What is langgraph?"}], # Seed the default StateBackend's in-state filesystem (virtual paths must start with "/"). "files": skills_files, }, config={"configurable": {"thread_id": "12345"}}, ) ```
```

片段[5] `oss__python__deepagents__customization#173` ｜ Customize Deep Agents ｜ Skills

```text
data(skill_content), } agent = create_deep_agent( model="openrouter:z-ai/glm-5.2", backend=backend, skills=["/skills/"], checkpointer=checkpointer, ) result = agent.invoke( { "messages": [{"role": "user", "content": "What is langgraph?"}], # Seed the default StateBackend's in-state filesystem (virtual paths must start with "/"). "files": skills_files, }, config={"configurable": {"thread_id": "12345"}}, ) ```
```

---

## v2-G-021（multi-hop）

**问题**：回复里偶尔冒出一些带 `addNotificationMetadata` 标记的消息，内置的 source 都有哪些、分别在什么时机加上？

**gold**：内置 source 按来源分：hitl_interrupt_decision 在 human-in-the-loop 中间件对拒绝或作答生成 tool message 时加，data 里带 decision；summarization 在摘要中间件压缩对话历史时加。另有 async_subagent 在异步子任务完成、失败或等待输入时加，data 是 task 事件；pinned_skill 在把置顶技能加入对话时加。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：
- 片段里只出现了 `addNotificationMetadata` / `add_notification_metadata` 的调用示例，示例中 `source` 是调用方自己传入的字符串（如 `"background_job"`）[1][2]，并没有列出「内置 source 有哪些」的清单。
- 片段里唯一出现的另一个 source 值是 `"async_subagent"`，但它出现在**读取**通知元数据的示例中（`getNotificationMetadata` / `get_notification_metadata` 后判断 `source === "async_subagent"`）[3][4]，片段并未说明这个 source 是在什么时机、由哪个组件自动加上的。
- 关于「分别在什么时机加上」，片段中没有任何描述通知元数据写入时机的说明；[12][14] 讲的是 async subagent 任务列表的状态获取与缓存策略，与通知元数据的添加时机无关。

另外提示一处命名差异：JavaScript 侧是 `addNotificationMetadata` / `getNotificationMetadata` [1][3][7]，Python 侧是 `add_notification_metadata` / `get_notification_metadata` [2][4][9]，且 Python 版以关键字参数 `source=`、`data=` 传入 [2]。若你要查内置 source 全集与注入时机，需要补充 Notifications 章节中关于 source 取值和触发条件的原文。

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

片段[3] `oss__javascript__langchain__messages#034` ｜ Messages ｜ Notifications

```text
```

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
```

片段[4] `oss__javascript__deepagents__async-subagents#019` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
```

import { getNotificationMetadata } from "@langchain/core/messages";



for (const message of state.messages) {

  const metadata = getNotificationMetadata(message);

  if (metadata?.source === "async_subagent") {

    const event = metadata.data as { agent_name: string; status: string };

    console.log(event.agent_name, event.status); // success, error, timeout, cancelled, or waiting

  }

}

```
```

片段[5] `oss__python__deepagents__async-subagents#013` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
```

from langchain_core.messages import get_notification_metadata



for message in state["messages"]:

    metadata = get_notification_metadata(message)

    if metadata and metadata["source"] == "async_subagent":

        event = metadata["data"]

        print(event["agent_name"], event["status"])  # success, error, timeout, cancelled, or waiting

```
```

---

## v2-G-022（paraphrase）

**问题**：我把同一段已经打包好的流程在一次步骤里连着调了两次，结果两次的记忆互相踩，第二次写进去的东西盖掉了第一次，这是为什么？该怎么改？

**gold**：同一个已编译实例在一次节点执行里被多次调用时，若开着有状态持久化，这几次调用会写进同一个 checkpoint namespace，于是互相冲突。解决办法是改用 per-invocation persistence，让每次调用各自独立保存，而不是共享同一份持久化位置。文档把这个现象列成「Multiple calls (same subgraph)」一行，per-thread 那一列是打叉的。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 片段里没有任何关于「同一节点内连续调用同一子图实例导致记忆互相覆盖」的原因说明。
- 片段 [9] 和 [11] 只提到「多个**不同**子图实例可以在单个节点内被调用而不产生 checkpoint 命名空间冲突」，这说的是不同子图，不是同一子图被连续调用两次的场景，无法据此推断你遇到的覆盖问题。
- 片段 [1][2] 只说明子图在同一 thread 内多次调用会保留状态、接着上次继续，但没有说明同一节点内连续两次调用同一实例时状态如何隔离或冲突。
- 片段 [3][4] 讲的是子图是否自带 checkpointer（`compile()` 继承父级 vs `compile(checkpointer=True)` 拥有自己的 checkpoint 历史），但没有涉及「同一节点内重复调用同一子图」的覆盖行为。
- 片段 [5][6] 是 checkpointer 的基础用法和 AgentCore 配置，[7][8] 是 HITL 写入校验，[10][12] 是 interrupt 恢复，[13] 是子图时间旅行限制，均不涉及该问题。

因此无法根据现有片段判断原因，也无法给出修改方案。建议补充检索以下方向的文档：同一节点内多次调用同一子图实例时的 checkpoint 命名空间/状态隔离规则，或子图实例复用与状态覆盖相关的说明。

**top5 片段**：

片段[1] `oss__javascript__langgraph__use-subgraphs#046` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
- Multi-turn memory : The subgraph retains its state across multiple invocations within the same thread . Each call picks up where the last one left off rather than starting fresh.
```

片段[2] `oss__python__langgraph__use-subgraphs#039` ｜ Subgraphs ｜ View example trace > Checkpointer reference

```text
- Multi-turn memory : The subgraph retains its state across multiple invocations within the same thread . Each call picks up where the last one left off rather than starting fresh.
```

片段[3] `oss__python__langgraph__use-time-travel#014` ｜ Use time-travel ｜ Subgraphs

```text
``` # Subgraph without its own checkpointer (default) subgraph = ( StateGraph(State) .add_node("step_a", step_a)       # Has interrupt() .add_node("step_b", step_b)       # Has interrupt() .add_edge(START, "step_a") .add_edge("step_a", "step_b") .compile()  # No checkpointer — inherits from parent ) graph = ( StateGraph(State) .add_node("subgraph_node", subgraph) .add_edge(START, "subgraph_node") .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Complete both interrupts graph.invoke({"value": []}, config)            # Hits step_a interrupt graph.invoke(Command(resume="Alice"), config)  # Hits step_b interrupt
```

片段[4] `oss__python__langgraph__use-time-travel#016` ｜ Use time-travel ｜ Subgraphs

```text
``` # Subgraph with its own checkpointer subgraph = ( StateGraph(State) .add_node("step_a", step_a)       # Has interrupt() .add_node("step_b", step_b)       # Has interrupt() .add_edge(START, "step_a") .add_edge("step_a", "step_b") .compile(checkpointer=True)  # Own checkpoint history ) graph = ( StateGraph(State) .add_node("subgraph_node", subgraph) .add_edge(START, "subgraph_node") .compile(checkpointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} # Run until step_a interrupt graph.invoke({"value": []}, config) # Resume step_a -> hits step_b interrupt graph.invoke(Command(resume="Alice"), config) # Get the subgraph's own checkpoint (between step_a and step_b)
```

片段[5] `oss__python__langgraph__checkpointers#008` ｜ Checkpointers ｜ Core concepts > Checkpoints > Super-steps

```text
e(START, "node_a") workflow.add_edge("node_a", "node_b") workflow.add_edge("node_b", END) checkpointer = InMemorySaver() graph = workflow.compile(checkpointer=checkpointer) config: RunnableConfig = {"configurable": {"thread_id": "1"}} graph.invoke({"foo": "", "bar":[]}, config) ```
```

---

## v2-G-023（paraphrase）

**问题**：对话越跑越长，里面塞满了以前工具调用留下的输出；我想只在超过某个体量时才动手清理，最近几条要留着，被清掉的位置还得有个占位说明——该配哪些参数？

**gold**：用 contextEditingMiddleware 包一个 ClearToolUsesEdit，写在 edits 数组里。触发阈值是 triggerTokens，示例给的是 2000；保留最近几条用 keep，示例是 3。清掉的内容默认显示 placeholder，示例写成 "[cleared]"。还可以用 clearToolInputs 决定是否连工具入参一起清，excludeTools 用来排除特定工具。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：

1. **“只在超过某个体量时才动手清理”的阈值参数**：片段 [3][4] 只描述了 deep agents 的默认行为——当会话上下文超过模型可用窗口的 85% 时，会截断较早的工具调用，并用磁盘文件指针替换 [3][4]。但片段里没有给出可配置的阈值参数名（比如类似 `context_threshold` 之类的 kwarg），也没有说明如何自定义这个触发比例。

2. **“最近几条要留着”的保留条数参数**：片段 [8] 展示了一个摘要节点里手动 `slice(0, -2)` 删除除最后两条以外消息的示例代码 [8]，但这是示例代码里的硬编码逻辑，不是可配置参数，也没有说明对应的配置项名称。

3. **“被清掉的位置还得有个占位说明”的占位配置**：片段 [3][4] 提到截断后会用“指向磁盘文件的指针”替换 [3][4]，片段 [11] 提到结果超限时会替换为“文件路径引用 + 前 10 行预览” [11]，但这些都是 deep agents 的固定行为描述，片段中没有暴露控制占位内容/格式的参数。

4. 片段 [7] 列出的配置项（`memory_limit`、`timeout`、`tool_name`、`capture_console`、`max_result_chars`、`ptc`）是 QuickJS 解释器工具的配置 [7]，其中 `max_result_chars` 只截断返回给模型的单次结果文本长度 [7]，与“按会话体量触发、保留最近几条、插入占位”的清理策略不是同一回事，不能拿来回答本问题。

另外提示一处可能的名称差异：你描述的“超过某个体量才清理 + 保留最近几条 + 占位说明”听起来像消息裁剪/摘要策略，但片段 [8] 里出现的是 `RemoveMessage` 配合摘要节点的手写实现 [8]，片段中没有出现可直接配置“保留条数”或“触发阈值”的 API 名称，因此无法确认你预期的参数名是否存在于文档中。

**top5 片段**：

片段[1] `oss__python__langchain__frontend__tool-calling#016` ｜ Tool calling ｜ Best practices

```text
- Keep cards compact . Tool cards sit inline with chat messages. Avoid overwhelming the conversation with oversized widgets.
```

片段[2] `oss__javascript__langchain__frontend__tool-calling#016` ｜ Tool calling ｜ Best practices

```text
- Keep cards compact . Tool cards sit inline with chat messages. Avoid overwhelming the conversation with oversized widgets.
```

片段[3] `oss__python__deepagents__context-engineering#048` ｜ Context engineering in Deep Agents ｜ Summarization > Offloading

```text
1. Tool call inputs exceed 20,000 tokens : File write and edit operations leave behind tool calls containing the complete file content in the agent’s conversation history. Since this content is already persisted to the filesystem, it’s often redundant. As the session context crosses 85% of the model’s available window, deep agents truncate older tool calls, replacing them with a pointer to the file on disk and reducing the size of the active context.
```

片段[4] `oss__javascript__deepagents__context-engineering#044` ｜ Context engineering in Deep Agents ｜ Summarization > Offloading

```text
1. Tool call inputs exceed 20,000 tokens : File write and edit operations leave behind tool calls containing the complete file content in the agent’s conversation history. Since this content is already persisted to the filesystem, it’s often redundant. As the session context crosses 85% of the model’s available window, deep agents truncate older tool calls, replacing them with a pointer to the file on disk and reducing the size of the active context.
```

片段[5] `oss__javascript__langchain__frontend__integrations__ai-elements#008` ｜ AI Elements ｜ Wiring useStream

```text
{getToolCalls(msg).map((tc) => ( <Tool key={tc.id} defaultOpen> <ToolHeader type={`tool-${tc.name}`} state={tc.state} /> <ToolContent> <ToolInput input={tc.args} /> {tc.output && ( <ToolOutput output={tc.output} errorText={undefined} /> )} </ToolContent> </Tool> ))} {/* Streamed text response */} <Message from="assistant"> <MessageContent> <MessageResponse>{getTextContent(msg)}</MessageResponse> </MessageContent> </Message> </div> ); } })} </ConversationContent> <ConversationScrollButton /> </Conversation> <PromptInput onSubmit={({ text }) => stream.submit({ messages: [{ type: "human", content: text }] }) } > <PromptInputBody> <PromptInputTextarea placeholder="Ask me something..." />
```

---

## v2-G-024（paraphrase）

**问题**：工具函数里想知道这次调用属于哪个会话、哪次运行、以及当前是第几次尝试，能从哪儿读到？

**gold**：从工具的 runtime.executionInfo 上读。它带 threadId、runId，以及 nodeAttempt，后者表示当前是第几次尝试。示例里就是把这些字段 console.log 出来，做一次执行身份的记录。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在工具函数里通过 `ToolRuntime` 的 `runtime.execution_info` 读取，其中包含 `thread_id`（会话）、`run_id`（运行）和 `node_attempt`（尝试次数）[2]。

最小可用示例：

```python
from langchain.tools import tool, ToolRuntime

@tool
def log_execution_context(runtime: ToolRuntime) -> str:
    """Log execution identity information."""
    info = runtime.execution_info
    print(f"Thread: {info.thread_id}, Run: {info.run_id}")
    print(f"Attempt: {info.node_attempt}")
    return "done"
```

补充说明：片段中只展示了 `execution_info` 的这三个字段（`thread_id`、`run_id`、`node_attempt`）[2]；如果你还想读每次调用传入的业务数据（如 `user_id`、API keys），那是另一套机制——用 `context_schema` 定义结构，并在工具里通过 `runtime.context` 访问 [1][5]。

**top5 片段**：

片段[1] `oss__python__deepagents__going-to-production#009` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
- context : per-run data your tools and middleware read at invocation time, for example user_id , API keys, feature flags, or session metadata. Define the shape with context_schema and access it via runtime.context . See Runtime context .
```

片段[2] `oss__python__langchain__tools#018` ｜ Tools ｜ View example trace > Execution info

```text
```

from langchain.tools import tool, ToolRuntime



@tool

def log_execution_context(runtime: ToolRuntime) -> str:

    """Log execution identity information."""

    info = runtime.execution_info

    print(f"Thread: {info.thread_id}, Run: {info.run_id}")

    print(f"Attempt: {info.node_attempt}")

    return "done"

```
```

片段[3] `oss__python__migrate__langchain-v1#039` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Runtime context

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

片段[4] `oss__javascript__deepagents__streaming#016` ｜ Streaming ｜ Namespaces

```text
```

for await (const [namespace, chunk] of await agent.stream(

  { messages: [{ role: "user", content: "Plan my vacation" }] },

  { streamMode: "updates", subgraphs: true },

)) {

  // Check if this event came from a subagent

  const isSubagent = namespace.some((segment: string) =>

    segment.startsWith("tools:"),

  );



  if (isSubagent) {

    // Extract the tool call ID from the namespace

    const toolCallId = namespace

      .find((s: string) => s.startsWith("tools:"))

      ?.split(":")[1];

    console.log(`Subagent ${toolCallId}:`, chunk);

  } else {

    console.log("Main agent:", chunk);

  }

}

```
```

片段[5] `oss__python__deepagents__subagents#101` ｜ Subagents ｜ Context management

```text
``` from dataclasses import dataclass from deepagents import create_deep_agent from langchain.messages import HumanMessage from langchain.tools import ToolRuntime, tool @dataclass class Context: user_id: str session_id: str @tool def get_user_data(query: str, runtime: ToolRuntime[Context]) -> str: """Fetch data for the current user.""" user_id = runtime.context.user_id return f"Data for user {user_id}: {query}" research_subagent = { "name": "researcher", "description": "Conducts research for the current user", "system_prompt": "You are a research assistant.", "tools": [get_user_data], } agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", subagents=[research_subagent],
```

---
