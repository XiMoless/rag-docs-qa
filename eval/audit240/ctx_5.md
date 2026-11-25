# 审计材料 5/8（30 条，明细文件第 121–150 行）

## v2-E-021（multi-hop）

**问题**：想让 agent 跨会话记住项目约定文档、按需加载技能目录，同时在对话太长时自动压缩历史：middleware 怎么配，压缩的触发和保留怎么定？

**gold**：跨会话记忆用 MemoryMiddleware(backend=backend, sources=["./AGENTS.md"])，技能加载用 SkillsMiddleware(backend=backend, sources=["./skills/"])；历史压缩用 SummarizationMiddleware(model="gpt-5.4-mini", trigger=("tokens", 4000), keep=("messages", 20))，多轮场景还需 checkpointer=InMemorySaver() 配 thread_id。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：给出的文档里没有找到能完整回答这个问题的内容。**

具体缺什么：

1. **跨会话记住项目约定文档**：片段 [14]/[16] 只提到 Memory 是「启动时从 AGENTS.md 文件加载的持久指令和偏好」，但没有说明如何通过 middleware 配置它，也没有给出相关 API 名称或参数。
2. **按需加载技能目录**：片段 [5] 只说明 `SkillsMiddleware` 在「传入 skills 时」才启用，运行在你的 middleware 之后、prompt caching 之前，且传入同名 middleware 会原地替换它；但没有说明 skills 目录如何声明、如何「按需加载」。
3. **压缩历史的触发与保留配置**：这部分片段是够的，见下。

---

**能回答的部分：对话过长时自动压缩历史**

- 压缩由 `SummarizationMiddleware` 负责，作用是压缩消息历史以保持在上下文限制内 [1][2]；Deep Agents 内置的 offloading 与 summarization 会压缩对话历史和大型中间结果 [7][8]。
- Python 侧通过 `create_summarization_middleware` 创建 [2]；JavaScript 侧对应 `createSummarizationMiddleware` [1]。
- 触发与保留用 `trigger` 和 `keep` 两个参数控制：`trigger=("tokens", 100000)` 表示对话超过 10 万 token 时触发摘要，`keep=("messages", 20)` 表示最近 20 条消息原样保留 [6]。

最小可用示例（Python，来自片段 [6]）：

```python
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from deepagents.middleware import SummarizationMiddleware

backend = StateBackend()
model = "anthropic:claude-sonnet-4-6"

agent = create_deep_agent(
    model=model,
    middleware=[
        SummarizationMiddleware(
            model=model,
            backend=backend,
            trigger=("tokens", 100000),  # summarize once the conversation exceeds 100k tokens
            keep=("messages", 20),  # keep the most recent 20 messages verbatim
        ),
    ],
)
```

**与用户说法可能不一致之处**：你问的是「middleware 怎么配」来同时实现记忆与技能加载，但片段中只出现了 `SummarizationMiddleware`、`SkillsMiddleware` 的名称与执行顺序 [1][2][5]，没有出现负责「跨会话记忆」的 middleware 名称或配置方式，因此无法给出三者合并的完整配置。

**top5 片段**：

片段[1] `oss__javascript__deepagents__customization#060` ｜ Customize Deep Agents ｜ Middleware > Deep Agents stack > Full stack

```text
3. SummarizationMiddleware : Condenses message history to stay within context limits when conversations grow long (via createSummarizationMiddleware ).
```

片段[2] `oss__python__deepagents__customization#061` ｜ Customize Deep Agents ｜ Middleware > Deep Agents stack > Full stack

```text
3. SummarizationMiddleware : Condenses message history to stay within context limits when conversations grow long (via create_summarization_middleware ).
```

片段[3] `oss__python__deepagents__overview#023` ｜ Deep Agents overview ｜ Context management

```text
- Summarization and context offloading : automatic compression of conversation history and large tool results
```

片段[4] `oss__javascript__deepagents__overview#015` ｜ Deep Agents overview ｜ Context management

```text
- Summarization and context offloading : automatic compression of conversation history and large tool results
```

片段[5] `oss__python__deepagents__customization#065` ｜ Customize Deep Agents ｜ Middleware > Deep Agents stack > Full stack

```text
8. SkillsMiddleware : Only when you pass skills . Runs after your middleware and directly before prompt caching, so it sees the summarized conversation and the model that is actually called. Passing a middleware named SkillsMiddleware replaces it in place.
```

---

## v2-E-022（multi-hop）

**问题**：要打开调用链追踪，环境变量得设哪几个？如果只想让某一次调用被记录、另一次不记录，代码怎么写？

**gold**：需要 LANGSMITH_TRACING=true、LANGSMITH_API_KEY=<your-api-key>，另外两个 LANGSMITH_AGENT_ID 与 LANGSMITH_AGENT_ENVIRONMENT="local" 是配套的 agent 侧变量。只想记录某一段就用 with ls.tracing_context(enabled=True): 把它包起来；注释明确说包外那次 invoke 在 LANGSMITH_TRACING 未设置时不会被记录。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. 打开追踪需要设置的环境变量（Python/JS 的 LangChain 与 LangGraph 文档一致）：
   - `LANGSMITH_AGENT_ID`
   - `LANGSMITH_AGENT_ENVIRONMENT`
   - `LANGSMITH_TRACING=true`
   - `LANGSMITH_API_KEY` [1][2][3][4]

   注意：Google 集成页里只出现了 `LANGSMITH_TRACING` 和 `LANGSMITH_API_KEY` 两个（且是注释形式），与上面四个变量的说法不一致，以 [1][2][3][4] 为准 [5]。

2. 只让某一次调用被记录、另一次不记录：
   - Python（LangGraph）：用 `langsmith.tracing_context(enabled=True)` 包裹需要追踪的调用；未被包裹的调用在未设置 `LANGSMITH_TRACING` 时不会被追踪 [11]。
   - JavaScript（LangGraph）：给需要追踪的那次调用传入 `LangChainTracer` 作为 callback；未传 callback 的调用在未设置 `LANGSMITH_TRACING` 时不会被追踪 [12]。

**最小可用示例：**

环境变量（Python / JS 通用）[1][2][3][4]：

```bash
export LANGSMITH_AGENT_ID="<your-agent-id>"
export LANGSMITH_AGENT_ENVIRONMENT="local"
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY=<your-api-key>
```

Python 选择性追踪 [11]：

```python
import langsmith as ls

# This WILL be traced
with ls.tracing_context(enabled=True):
    agent.invoke({"messages": [{"role": "user", "content": "Send a test email to alice@example.com"}]})

# This will NOT be traced (if LANGSMITH_TRACING is not set)
agent.invoke({"messages": [{"role": "user", "content": "Send another email"}]})
```

JavaScript 选择性追踪 [12]：

```javascript
import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

// This WILL be traced
const tracer = new LangChainTracer();
await agent.invoke(
  {
    messages: [{role: "user", content: "Send a test email to alice@example.com"}]
  },
  { callbacks: [tracer] }
);

// This will NOT be traced (if LANGSMITH_TRACING is not set)
await agent.invoke(
  {
    messages: [{role: "user", content: "Send another email"}]
  }
);
```

补充：文档还提到，默认情况下 agent 的所有步骤会自动被追踪（无需额外代码），例如 `agent.invoke(...)` 后 "all steps will be traced automatically" [9][10]。

**top5 片段**：

片段[1] `oss__python__langchain__observability#000` ｜ LangSmith Observability ｜ Enable tracing

```text
```

export LANGSMITH_AGENT_ID="<your-agent-id>"

export LANGSMITH_AGENT_ENVIRONMENT="local"

export LANGSMITH_TRACING=true

export LANGSMITH_API_KEY=<your-api-key>

```
```

片段[2] `oss__javascript__langchain__observability#000` ｜ LangSmith Observability ｜ Enable tracing

```text
```

export LANGSMITH_AGENT_ID="<your-agent-id>"

export LANGSMITH_AGENT_ENVIRONMENT="local"

export LANGSMITH_TRACING=true

export LANGSMITH_API_KEY=<your-api-key>

```
```

片段[3] `oss__python__langgraph__observability#000` ｜ LangSmith Observability ｜ Enable tracing

```text
```

export LANGSMITH_AGENT_ID="<your-agent-id>"

export LANGSMITH_AGENT_ENVIRONMENT="local"

export LANGSMITH_TRACING=true

export LANGSMITH_API_KEY=<your-api-key>

```
```

片段[4] `oss__javascript__langgraph__observability#000` ｜ LangSmith Observability ｜ Enable tracing

```text
```

export LANGSMITH_AGENT_ID="<your-agent-id>"

export LANGSMITH_AGENT_ENVIRONMENT="local"

export LANGSMITH_TRACING=true

export LANGSMITH_API_KEY=<your-api-key>

```
```

片段[5] `oss__javascript__integrations__chat__google#008` ｜ ChatGoogle integration ｜ Setup > Tracing

```text
```

# export LANGSMITH_TRACING="true"

# export LANGSMITH_API_KEY="your-api-key"

```
```

---

## v2-E-023（paraphrase）

**问题**：我有个查订单状态的工具，返回的那句话本身就是给用户看的成品结论。我不想让它再被模型润色一遍，也不希望它多跑一轮模型——能把这条工具结果直接当成最终答复吗？那样 agent 内部会怎么走？

**gold**：可以，把工具设成一返回就收尾：agent 会停止继续循环，把工具输出直接当作最终回复返回，bypassing any additional model call；也就是不会再多调一轮模型，适合结果本身就是成品、或必须保持原样不能改写的情况。

**judge 分**：1.0　**拒答标记**：None

**回答**：

可以。把该工具配置为 `return_direct=True` 后，agent 会停止循环，直接把工具输出作为最终响应返回，跳过额外的模型调用 [1][2]。也就是说，你那条“订单状态”的成品结论不会再被模型润色，也不会多跑一轮模型。

需要注意一个并行调用的细节：如果模型在一步里同时调用了多个工具，这些工具会先全部执行；只有当这一批里**每个**工具都是 `return_direct=True` 时，agent 才会路由到 END。最终响应会包含该步中所有被调用工具的 `ToolMessage` 输出 [8][10]。

最小可用示例（JavaScript，保留原文）：

```javascript
const result = await agent.invoke({
  messages: [
    { role: "user", content: "What is the status of order #12345?" },
  ],
});
// The agent returns the tool output directly without another LLM call:
// "Order 12345 is shipped and will arrive in 2 days."
```

[9]

补充说明：片段里只出现了 `return_direct=True` 这个参数名（Python 风格写法），JavaScript 侧片段 [8][9] 未展示工具定义处的具体参数写法，因此这里不臆测 JS 的参数拼写；以你所用语言版本的文档为准。

**top5 片段**：

片段[1] `oss__javascript__langchain__tools#019` ｜ Tools ｜ View example trace

```text
- The agent stops looping and returns the tool’s output as the final response, bypassing any additional model call.
```

片段[2] `oss__python__langchain__tools#030` ｜ Tools ｜ View example trace

```text
- The agent stops looping and returns the tool’s output as the final response, bypassing any additional model call.
```

片段[3] `oss__javascript__langchain__tools#018` ｜ Tools ｜ View example trace > Return directly from a tool

```text
const result = await agent.invoke({ messages: [ { role: "user", content: "What is the status of order #12345?" }, ], }); // The agent returns the tool output directly without another LLM call: // "Order 12345 is shipped and will arrive in 2 days." ```
```

片段[4] `oss__python__concepts__human-in-the-loop#006` ｜ Human-in-the-loop overview ｜ Follow an approval from pause to resume

```text
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
```

片段[5] `oss__javascript__deepagents__human-in-the-loop#006` ｜ Human-in-the-loop ｜ Decision types

```text
| Decision Type | Description | Example Use Case |

| --- | --- | --- |

| ✅ approve | Execute the tool with the original arguments as proposed by the agent. | Send an email draft exactly as written |

| ✏️ edit | Modify the tool arguments before execution. | Change the recipient before sending an email |

| ❌ reject | Skip executing this tool call entirely and return rejection feedback to the agent. | Deny file deletion and explain why |

| 💬 respond | Return the human’s message directly as a synthetic tool result, skipping execution, for “ask user” style tools. | Answer an "ask_user" prompt with a direct reply |
```

---

## v2-E-024（paraphrase）

**问题**：有几个测试非得打真模型才能验证端到端，跑一次又慢又花钱，我不想让它们混在日常快测里一起跑，怎么分开？

**gold**：给这类用例加 @pytest.mark.integration 标记，里面直接用 create_agent("claude-sonnet-4-6", tools=[get_weather]) 打真模型，断言也放宽成 len(result["messages"]) > 1 这样的弱条件；日常不带这个标记的用例就不跑真模型。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：用 pytest 的 marker 把「打真模型」的集成测试单独标记，并在默认 `addopts` 里排除掉，这样日常快测不会跑它们，只在 CI 或部署前显式跑集成测试 [3][1]。

最小可用示例（Python）：

```toml
[tool.pytest.ini_options]
markers = [
  "integration: tests that call real LLM APIs"
]
addopts = "-m 'not integration'"
```

```python
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

说明：
- 默认 `addopts = "-m 'not integration'"` 会让普通 `pytest` 跳过所有 `integration` 标记的用例 [3]。
- 需要跑集成测试时，用 `-m integration` 显式选中（这是基于 marker 机制的常规用法，片段里只给了排除写法，未直接给出选中命令）。
- 文档还建议这类测试只在 CI 或部署前跑，不要每次保存文件都跑 [1]。
- 片段里另有一处等价写法 `addopts = -m "not integration"`（引号风格不同）[12]，两者含义一致。

补充降本建议（片段中给出）：集成测试可换更小的模型（如 `gemini-3.1-flash-lite`）[4][7]、限制输出 token 数 [13]、每个测试只验证一个行为 [8]。

**top5 片段**：

片段[1] `oss__python__langchain__test__integration-testing#009` ｜ Integration testing ｜ Reduce cost and latency

```text
- Run selectively : Use the test separation from above to run integration tests only in CI or before deploy, not on every file save.
```

片段[2] `oss__javascript__langchain__test__integration-testing#019` ｜ Integration testing ｜ Reduce cost and latency

```text
- Run selectively : Use the test separation from above to run integration tests only in CI or before deploy, not on every file save.
```

片段[3] `oss__python__langchain__test__integration-testing#003` ｜ Integration testing ｜ Separate unit and integration tests

```text
```

[tool.pytest.ini_options]

markers = [

  "integration: tests that call real LLM APIs"

]

addopts = "-m 'not integration'"

```
```

片段[4] `oss__javascript__langchain__test__integration-testing#018` ｜ Integration testing ｜ Reduce cost and latency

```text
- Limit test scope : Test one behavior per test. Avoid end-to-end scenarios that chain many LLM calls when a single-turn test suffices.
```

片段[5] `oss__python__langchain__test__integration-testing#008` ｜ Integration testing ｜ Reduce cost and latency

```text
- Limit test scope : Test one behavior per test. Avoid end-to-end scenarios that chain many LLM calls when a single-turn test suffices.
```

---

## v2-E-025（paraphrase）

**问题**：用户输入里只要出现几个黑名单词，我希望在动手干活之前就把这轮对话掐掉，并直接回一句固定话术，而不是先让模型跑一轮再拦。该怎么写？

**gold**：在拦截逻辑里遍历 banned_keywords，命中就 return {"messages": [{"role": "assistant", "content": "I cannot process requests containing inappropriate content. Please rephrase your request."}], "jump_to": "end"}——注释写的就是 Block execution before any processing，即任何处理之前结束这一轮。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：用 **before_agent** 钩子（Python 里是 `before_agent`，JS 里是 `beforeAgent`）在 agent 启动前拦截，并配置 `can_jump_to=["end"]` 直接结束本轮，返回固定话术即可，不需要先跑模型 [1][3][5]。

注意命名差异：Python 用下划线 `before_agent` [3][5]，JS 用驼峰 `beforeAgent` [2][4]；片段里没有出现 `beforeAgent` 之外的写法，若你写的是别的名字请以片段为准。

最小可用示例（Python，来自片段 [5] 的结构）：

```python
from typing import Any
from langchain.agents.middleware import before_agent, AgentState, hook_config
from langgraph.runtime import Runtime

banned_keywords = ["hack", "exploit", "malware"]

@before_agent(can_jump_to=["end"])
def content_filter(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Deterministic guardrail: Block requests containing banned keywords."""
    if not state["messages"]:
        return None
    first_message = state["messages"][0]
    if first_message.type != "human":
        return None
    content = first_message.content.lower()
    for keyword in banned_keywords:
        if keyword in content:
            # Block execution before any processing
            ...
```

说明：
- `before_agent` 在 agent 启动时运行，每次调用一次 [1][4]，符合“动手干活之前掐掉”的时机。
- `can_jump_to=["end"]` 用于直接跳到结束 [3][5]；片段 [5] 的代码在命中关键词处被截断（`# Block execution before any processing` 之后的内容未给出），因此**返回固定话术的具体写法在给出的文档里没有完整示例**，需要你按 `can_jump_to=["end"]` 的语义自行补全返回结构。
- 若想用类式写法，片段 [3] 展示了 `AgentMiddleware` + `@hook_config(can_jump_to=["end"])` 的 `before_agent` 方法，同样在命中处被截断。
- JS 侧对应 `createMiddleware({ name, beforeAgent: { hook: (state) => {...} } })`，片段 [2] 同样在 `return { messages: [` 处截断，固定话术的返回体未给出。

缺失内容：命中关键词后“返回固定话术”的确切返回字段/结构，三个片段都在关键处被截断，无法从给出的文档确认。

**top5 片段**：

片段[1] `oss__python__langchain__middleware__custom#000` ｜ Custom middleware ｜ Wrap-style hooks > Node-style hooks

```text
| Hook | When it runs |

| --- | --- |

| before_agent | Before agent starts (once per invocation) |

| before_model | Before each model call |

| after_model | After each model response |

| after_agent | After agent completes (once per invocation) |
```

片段[2] `oss__javascript__langchain__guardrails#006` ｜ Guardrails ｜ Custom guardrails > Before agent guardrails

```text
``` import { createMiddleware, AIMessage } from "langchain"; const contentFilterMiddleware = (bannedKeywords: string[]) => { const keywords = bannedKeywords.map(kw => kw.toLowerCase()); return createMiddleware({ name: "ContentFilterMiddleware", beforeAgent: { hook: (state) => { // Get the first user message if (!state.messages || state.messages.length === 0) { return; } const firstMessage = state.messages[0]; if (firstMessage._getType() !== "human") { return; } const content = firstMessage.content.toString().toLowerCase(); // Check for banned keywords for (const keyword of keywords) { if (content.includes(keyword)) { // Block execution before any processing return { messages: [
```

片段[3] `oss__python__langchain__guardrails#006` ｜ Guardrails ｜ Custom guardrails > Before agent guardrails

```text
``` from typing import Any from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config from langgraph.runtime import Runtime class ContentFilterMiddleware(AgentMiddleware): """Deterministic guardrail: Block requests containing banned keywords.""" def __init__(self, banned_keywords: list[str]): super().__init__() self.banned_keywords = [kw.lower() for kw in banned_keywords] @hook_config(can_jump_to=["end"]) def before_agent(self, state: AgentState, runtime: Runtime) -> dict[str, Any] | None: # Get the first user message if not state["messages"]: return None first_message = state["messages"][0] if first_message.type != "human": return None
```

片段[4] `oss__javascript__langchain__middleware__custom#000` ｜ Custom middleware ｜ Wrap-style hooks > Node-style hooks

```text
| Hook | When it runs |

| --- | --- |

| beforeAgent | Before agent starts (once per invocation) |

| beforeModel | Before each model call |

| afterModel | After each model response |

| afterAgent | After agent completes (once per invocation) |
```

片段[5] `oss__python__langchain__guardrails#009` ｜ Guardrails ｜ Custom guardrails > Before agent guardrails

```text
``` from typing import Any from langchain.agents.middleware import before_agent, AgentState, hook_config from langgraph.runtime import Runtime banned_keywords = ["hack", "exploit", "malware"] @before_agent(can_jump_to=["end"]) def content_filter(state: AgentState, runtime: Runtime) -> dict[str, Any] | None: """Deterministic guardrail: Block requests containing banned keywords.""" # Get the first user message if not state["messages"]: return None first_message = state["messages"][0] if first_message.type != "human": return None content = first_message.content.lower() # Check for banned keywords for keyword in banned_keywords: if keyword in content: # Block execution before any processing
```

---

## v2-E-026（paraphrase）

**问题**：用户之前发过的几封邮件我想让 agent 学着那个语气来写。把这段风格说明塞进消息列表时，放开头还是末尾更好、为什么？风格数据又按什么取的？

**gold**：放末尾：代码把 style_context 追加到最后（注释 Append at end - models pay more attention to final messages），因为模型对最后几条消息更敏感。风格数据按 store.get(("writing_style",), user_id) 取出，再拼成 tone、greeting、sign_off、example_email 四项的说明。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：应把风格说明**追加到消息列表末尾**，而不是放开头，因为文档明确说模型更关注最后几条消息（"models pay more attention to final messages"）[2][5][7]。风格数据是从 **Store** 里按 `user_id` 读取的，`user_id` 来自 `request.runtime.context.user_id` [1][7]。

具体取值方式（以 Python 片段为准）：
- 通过 `request.runtime.context.user_id` 拿到用户 ID [1][7]
- 用 `request.runtime.store.get(("writing_style",), user_id)` 从 Store 读取该用户的写作风格记录 [1][7]
- 取到后读 `writing_style.value`，再拼成风格说明文本 [1][7]

最小可用示例（Python，来自片段）：

```python
@wrap_model_call
def inject_writing_style(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """Inject user's email writing style from Store."""
    user_id = request.runtime.context.user_id  # Read from Store: get user's writing style examples
    store = request.runtime.store
    writing_style = store.get(("writing_style",), user_id)
    if writing_style:
        style = writing_style.value
        # Build style guide from stored examples
        style_context = f"""Your writing style:
- Tone: {style.get('tone', 'professional')}
- Typical greeting: "{style.get('greeting', 'Hi')}"
- Typical sign-off: "{style.get('sign_off', 'Best')}"
- Example email you've written: {style.get('example_email', '')}"""
        # Append at end - models pay more attention to final messages
        messages = [
            *request.messages,
            {"role": "user", "content": style_context}
        ]
        request = request.override(messages=messages)
    return handler(request)
```

需要指出的差异/注意点：
- 你问的是"放开头还是末尾"，片段里只出现了"追加到末尾"的做法，并给出理由（模型更关注末尾消息）[2][5][7]；片段中没有出现"放开头"的写法或对比论证，因此无法从片段确认放开头的效果。
- 片段中 Store 的键是元组 `("writing_style",)` 加 `user_id` 作为命名空间/键的组合 [1][7]，若你原本以为只用一个字符串键，请以片段为准。
- 片段里模型名写作 `"gpt-6.1-sol"` [3][5][6]，与常见模型名不同，这里按片段原样保留。

**top5 片段**：

片段[1] `oss__python__langchain__context-engineering#011` ｜ Context engineering in agents ｜ Response Format > Messages

```text
``` from dataclasses import dataclass from langchain.agents import create_agent from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse from typing import Callable from langgraph.store.memory import InMemoryStore @dataclass class Context: user_id: str @wrap_model_call def inject_writing_style( request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse] ) -> ModelResponse: """Inject user's email writing style from Store.""" user_id = request.runtime.context.user_id # Read from Store: get user's writing style examples store = request.runtime.store writing_style = store.get(("writing_style",), user_id) if writing_style: style = writing_style.value
```

片段[2] `oss__python__langchain__context-engineering#012` ｜ Context engineering in agents ｜ Response Format > Messages

```text
quest.runtime.store writing_style = store.get(("writing_style",), user_id) if writing_style: style = writing_style.value # Build style guide from stored examples style_context = f"""Your writing style: - Tone: {style.get('tone', 'professional')} - Typical greeting: "{style.get('greeting', 'Hi')}" - Typical sign-off: "{style.get('sign_off', 'Best')}" - Example email you've written: {style.get('example_email', '')}""" # Append at end - models pay more attention to final messages messages = [ *request.messages, {"role": "user", "content": style_context} ] request = request.override(messages=messages) return handler(request) agent = create_agent( model="gpt-6.1-sol", tools=[...],
```

片段[3] `oss__javascript__langchain__context-engineering#012` ｜ Context engineering in agents ｜ Response Format > Messages

```text
om stored examples const styleContext = `Your writing style: - Tone: ${style.tone || 'professional'} - Typical greeting: "${style.greeting || 'Hi'}" - Typical sign-off: "${style.signOff || 'Best'}" - Example email you've written: ${style.exampleEmail || ''}`; // Append at end - models pay more attention to final messages const messages = [ ...request.messages, new HumanMessage(styleContext) ]; request = { ...request, messages }; } return handler(request); }, }); ```
```

片段[4] `oss__javascript__langchain__context-engineering#011` ｜ Context engineering in agents ｜ Response Format > Messages

```text
``` import * as z from "zod"; import { createMiddleware, HumanMessage } from "langchain"; const contextSchema = z.object({ userId: z.string(), }); const injectWritingStyle = createMiddleware({ name: "InjectWritingStyle", contextSchema, wrapModelCall: async (request, handler) => { const userId = request.runtime.context.userId; // Read from Store: get user's writing style examples const store = request.runtime.store; const writingStyle = await store.get(["writing_style"], userId); if (writingStyle) { const style = writingStyle.value; // Build style guide from stored examples const styleContext = `Your writing style: - Tone: ${style.tone || 'professional'} - Typical greeting:
```

片段[5] `oss__python__langchain__context-engineering#006` ｜ Context engineering in agents ｜ Response Format > System Prompt

```text
anced") base += f"\nUser prefers {style} responses." return base agent = create_agent( model="gpt-6.1-sol", tools=[...], middleware=[store_aware_prompt], context_schema=Context, store=InMemoryStore() ) ```
```

---

## v2-E-027（no-answer）

**问题**：LlamaIndex 的 IngestionPipeline 里 docstore_strategy 有哪几种取值？跟 LangChain 这套 ingest 做法的主要差别是什么？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 没有任何片段提到 LlamaIndex 的 `IngestionPipeline`，也没有提到 `docstore_strategy` 这个参数及其取值 [1][2][3][4][5][6][7][8][9]。
- 片段中也没有 LangChain 侧“ingest”流程的说明；现有片段只涉及长期记忆存储（`PostgresStore` / `InMemoryStore` 的 `put`/`get`/`search`）、产品分层表、前端 `useStream` 以及 Deep Agents 的 scoped memory [1][4][5][8]，无法据此与 LlamaIndex 的摄取管线做对比。

另外提示一处可能的名称差异：片段里出现的存储接口是 `store.put(...)`、`store.get(...)`、`store.search(...)`，并未出现名为 `ingest` 的 API [1][4][9]；如果你指的是某个具体 LangChain ingest 接口，需要补充对应文档片段才能比对。

**top5 片段**：

片段[1] `oss__python__langchain__long-term-memory#005` ｜ Long-term memory ｜ Memory storage

```text
``` from collections.abc import Sequence from langgraph.store.base import IndexConfig from langgraph.store.postgres import PostgresStore  # type: ignore[import-not-found] def embed(texts: Sequence[str]) -> list[list[float]]: # Replace with an actual embedding function or LangChain embeddings object return [[1.0, 2.0] for _ in texts] DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable" with PostgresStore.from_conn_string( DB_URI, index=IndexConfig(embed=embed, dims=2),  # type: ignore[arg-type] ) as store: store.setup() user_id = "my-user" application_context = "chitchat" namespace = (user_id, application_context) store.put( namespace, "a-memory", { "rules": [
```

片段[2] `oss__python__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[3] `oss__javascript__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[4] `oss__python__concepts__memory#007` ｜ Memory overview ｜ Long-term memory > Memory storage

```text
``` from langgraph.store.memory import InMemoryStore def embed(texts: list[str]) -> list[list[float]]: # Replace with an actual embedding function or LangChain embeddings object return [[1.0, 2.0] * len(texts)] # InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production use. store = InMemoryStore(index={"embed": embed, "dims": 2}) user_id = "my-user" application_context = "chitchat" namespace = (user_id, application_context) store.put( namespace, "a-memory", { "rules": [ "User likes short, direct language", "User only speaks English & python", ], "my-key": "my-value", }, ) # get the "memory" by ID item = store.get(namespace, "a-memory")
```

片段[5] `oss__javascript__concepts__memory#007` ｜ Memory overview ｜ Long-term memory > Memory storage

```text
``` import { InMemoryStore } from "@langchain/langgraph"; const embed = (texts: string[]): number[][] => { // Replace with an actual embedding function or LangChain embeddings object return texts.map(() => [1.0, 2.0]); }; // InMemoryStore saves data to an in-memory dictionary. Use a DB-backed store in production use. const store = new InMemoryStore({ index: { embed, dims: 2 } }); const userId = "my-user"; const applicationContext = "chitchat"; const namespace = [userId, applicationContext]; await store.put( namespace, "a-memory", { rules: [ "User likes short, direct language", "User only speaks English & TypeScript", ], "my-key": "my-value", } ); // get the "memory" by ID
```

---

## v2-E-028（no-answer）

**问题**：create_agent 支持 cost_limit 参数吗？传一个美元上限进去，超预算就自动中止并回退到便宜模型，应该怎么配？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少的信息：
- 没有任何片段提到 `create_agent` 有 `cost_limit` 参数，也没有提到按美元金额设置预算上限的机制。
- 没有片段说明「超预算自动中止」的配置方式。
- 关于「回退到便宜模型」，片段 [7] 只展示了 `ModelFallbackMiddleware` 的用法（按顺序指定备用模型），但没有任何内容说明它能与成本/预算阈值联动触发；片段 [2] 只有调用次数上限（`modelCallLimitMiddleware` 的 `runLimit`、`toolCallLimitMiddleware` 的 `runLimit`），不是费用上限。

另外需要指出的差异：你提到的 `cost_limit` 参数在给出的片段中并不存在；片段里与「限制」相关的只有基于调用次数的 `runLimit` [2]，与「回退模型」相关的只有 `ModelFallbackMiddleware` [7]，二者都不是按美元计费上限工作的。

如果你能提供涉及成本/预算控制或 `ModelFallbackMiddleware` 触发条件的文档片段，我可以再据此回答。

**top5 片段**：

片段[1] `oss__python__langchain__middleware__built-in#015` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model retry

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import ModelRetryMiddleware # Basic usage with default settings (2 retries, exponential backoff) agent = create_agent( model="gpt-6.1-sol", tools=[search_tool], middleware=[ModelRetryMiddleware()], ) # Custom exception filtering class TimeoutError(Exception): """Custom exception for timeout errors.""" pass class ConnectionError(Exception): """Custom exception for connection errors.""" pass # Retry specific exceptions only retry = ModelRetryMiddleware( max_retries=4, retry_on=(TimeoutError, ConnectionError), backoff_factor=1.5, ) def should_retry(error: Exception) -> bool: # Only retry on rate limit errors
```

片段[2] `oss__javascript__deepagents__fault-tolerance#007` ｜ Fault tolerance ｜ Rate limiting > Call limits

```text
```

import { createAgent, modelCallLimitMiddleware, toolCallLimitMiddleware } from "langchain";



const agent = createAgent({

  model: "google:gemini-4-hydrogen",

  middleware: [

    modelCallLimitMiddleware({ runLimit: 50 }),

    toolCallLimitMiddleware({ runLimit: 200 }),

  ],

});

```
```

片段[3] `oss__python__migrate__langchain-v1#027` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Model > Dynamic model selection

```text
ced_model else: model = basic_model return handler(request.override(model=model)) def __init__(self, messages_threshold: int) -> None: self.messages_threshold = messages_threshold agent = create_agent( model=basic_model, tools=tools, middleware=[DynamicModelMiddleware(messages_threshold=10)] ) ```
```

片段[4] `oss__python__langchain__multi-agent__skills-sql-assistant#046` ｜ Build a SQL assistant with on-demand skills ｜ 6. Advanced: Add constraints with custom state > Update middleware and agent

```text
```

agent = create_agent(

    model,

    system_prompt=(

        "You are a SQL query assistant that helps users "

        "write queries against business databases."

    ),

    middleware=[SkillMiddleware()],

    checkpointer=InMemorySaver(),

)

```
```

片段[5] `oss__python__langchain__middleware__custom#029` ｜ Custom middleware ｜ Custom state schema

```text
{"jump_to": "end"} return None @after_model(state_schema=CustomState) def increment_counter(state: CustomState, runtime: Runtime) -> dict[str, Any] | None: return {"model_call_count": state.get("model_call_count", 0) + 1} agent = create_agent( model="gpt-6.1-sol", middleware=[check_call_limit, increment_counter], tools=[], ) # Invoke with custom state result = agent.invoke({ "messages": [HumanMessage("Hello")], "model_call_count": 0, "user_id": "user-123", }) ```
```

---

## v2-F-001（single-hop）

**问题**：普通节点和子图在 checkpoint 与恢复上的行为不一样，具体差在哪？子图想彻底不落检查点又该怎么编译？

**gold**：按需要选择工作单元的表格，子图只在有状态模式下为节点做检查点，检查点挂在父线程的 namespace 下，编译时用 checkpointer=False 可以完全关掉子图检查点；恢复时它从子图内部被中断或失败的节点继续。图节点则在所在的 super-step 之后一定落检查点，恢复从该节点开始，更早的节点不会重跑。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

普通节点（graph node）和子图（subgraph）在 checkpoint 与恢复上的差异，文档里是这样描述的：

- **普通节点**：会 checkpoint，且 checkpoint 跟随它所在的 super-step；恢复时从该节点开始，之前的节点不会重跑 [2][3]。
- **子图**：在有状态模式下也会 checkpoint，但节点是在**父线程的命名空间（namespace）下**做 checkpoint；有状态模式下恢复会**在子图内部**从被中断或失败的节点继续 [2][3]。
- **子图想彻底不落检查点**：编译时用 `checkpointer=False` [2][3]。另外 [1] 展示了另一种默认情形——子图**不传 checkpointer**（`compile()` 不带参数）时会**继承父图的 checkpointer**，这与「彻底不落检查点」不是一回事，注意区分。

**最小可用示例**

子图彻底不落检查点（按 [2][3] 的 `checkpointer=False`）：

```python
subgraph = (
    StateGraph(State)
    .add_node("step_a", step_a)
    .add_node("step_b", step_b)
    .add_edge(START, "step_a")
    .add_edge("step_a", "step_b")
    .compile(checkpointer=False)  # 子图不落检查点
)
```

对比：子图不传 checkpointer 时继承父图（[1] 的 JS 示例）：

```javascript
const subgraph = new StateGraph(StateAnnotation)
  .addNode("stepA", stepA)
  .addNode("stepB", stepB)
  .addEdge(START, "stepA")
  .addEdge("stepA", "stepB")
  .compile();  // No checkpointer — inherits from parent

const graph = new StateGraph(StateAnnotation)
  .addNode("subgraphNode", subgraph)
  .addEdge(START, "subgraphNode")
  .compile({ checkpointer });
```

**需要指出的差异/注意点**

- 你问的是「子图想彻底不落检查点怎么编译」，片段给出的写法是 `checkpointer=False` [2][3]；而 [1] 里的 `compile()`（不传参）是**继承父图 checkpointer**，并非「不落检查点」，两者不要混淆。
- 关于「普通节点 vs 子图」的对比，片段 [2][3] 是表格残片（开头有截断），只覆盖了 checkpoint 位置、恢复行为、适用场景三列，没有更多细节；若你需要更完整的对比维度，给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__javascript__langgraph__use-time-travel#012` ｜ Use time-travel ｜ Subgraphs

```text
``` // Subgraph without its own checkpointer (default) const subgraph = new StateGraph(StateAnnotation) .addNode("stepA", stepA)       // Has interrupt() .addNode("stepB", stepB)       // Has interrupt() .addEdge(START, "stepA") .addEdge("stepA", "stepB") .compile();  // No checkpointer — inherits from parent const graph = new StateGraph(StateAnnotation) .addNode("subgraphNode", subgraph) .addEdge(START, "subgraphNode") .compile({ checkpointer }); // Complete both interrupts await graph.invoke({ value: [] }, config); await graph.invoke(new Command({ resume: "Alice" }), config); await graph.invoke(new Command({ resume: "30" }), config); // Time travel from before the subgraph
```

片段[2] `oss__python__langgraph__graph-api#012` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
st not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread. Compile with checkpointer=False for no subgraph checkpoints. | Stateful modes resume inside the subgraph at the interrupted or failed node. | The unit has its own routing or state schema, or more than one parent graph reuses it. | | Graph node | Yes. A checkpoint follows the super-step it runs in. | Resume starts at that node. Earlier nodes do not re-run. | A routing fork is possible after the step, or you need an interrupt, resume, or time travel boundary. |
```

片段[3] `oss__javascript__langgraph__graph-api#015` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
st not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread. Compile with checkpointer=False for no subgraph checkpoints. | Stateful modes resume inside the subgraph at the interrupted or failed node. | The unit has its own routing or state schema, or more than one parent graph reuses it. | | Graph node | Yes. A checkpoint follows the super-step it runs in. | Resume starts at that node. Earlier nodes do not re-run. | A routing fork is possible after the step, or you need an interrupt, resume, or time travel boundary. |
```

片段[4] `oss__python__langgraph__interrupts#000` ｜ Interrupts ｜ ROOT

```text
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
```

片段[5] `oss__javascript__langgraph__interrupts#000` ｜ Interrupts ｜ ROOT

```text
- Checkpointing keeps your place: the checkpointer writes the exact graph state so you can resume later, even when in an error state.
```

---

## v2-F-002（single-hop）

**问题**：节点的函数签名里怎么拿到调用方传进来的运行时配置？调用时又从哪里把它送进去？

**gold**：StateGraph 构造时用 context_schema=ContextSchema 声明配置结构；节点签名写成 (state, runtime: Runtime[ContextSchema])，再通过 runtime.context 读字段，示例读的是 runtime.context.llm_provider。调用时在 graph.invoke 的 context 参数里传值，例如 context={'llm_provider': 'anthropic'}。

**judge 分**：0.0　**拒答标记**：None

**回答**：

**结论：**

1. 在节点函数签名里加一个 `RunnableConfig` 类型的参数，即可拿到运行时配置；节点或条件边都适用 [4][5]。
2. 配置值从 `config["configurable"]` 里读取（Python 用下标，JS 用可选链 `config.configurable?.xxx`）[1][2][3]。
3. 调用时把配置放进 `config` 的 `configurable` 字段传入，例如 `{"configurable": {"thread_id": "1"}}` [9][13]。

**最小可用示例（Python）：**

```python
from langchain_core.runnables import RunnableConfig

def my_node(state: State, config: RunnableConfig):
    checkpoint_ns = config["configurable"]["checkpoint_ns"]
    # "" for the parent graph, "node_name:uuid" for a subgraph
```

[1]

**调用侧传入（Python）：**

```python
config = {"configurable": {"thread_id": "1"}}
graph.get_state(config)
```

[9]

**需要指出的差异 / 注意点：**

- 你问的是「调用方传进来的运行时配置」，片段里能确认的读取位置是 `config["configurable"]` [1][2]；但片段 [8] 展示的运行时传参用的是 `graph.invoke({}, context={"my_runtime_value": "a"})`，即通过 `context=` 传入、配合 `context_schema` 使用 [8]。这两条路径在片段中并未被明确说明是同一机制，片段没有解释 `context` 与 `configurable` 之间的关系，因此不能断言二者等价。
- 片段 [4][5] 只说明「把配置加到节点或条件边的函数签名」，没有给出具体参数名，参数名 `config` 来自 [1][2] 的示例。
- 片段 [2] 读取 `thread_id` 时用的是 `.get("thread_id")`，而 [1] 读取 `checkpoint_ns` 用的是下标 `["checkpoint_ns"]`，写法不同但都是访问 `config["configurable"]`。

**top5 片段**：

片段[1] `oss__python__langgraph__checkpointers#013` ｜ Checkpointers ｜ Core concepts > Checkpoints > Checkpoint namespace

```text
```

from langchain_core.runnables import RunnableConfig



def my_node(state: State, config: RunnableConfig):

    checkpoint_ns = config["configurable"]["checkpoint_ns"]

    # "" for the parent graph, "node_name:uuid" for a subgraph

```
```

片段[2] `oss__python__langgraph__fault-tolerance#036` ｜ Fault tolerance ｜ Graph defaults > Default error handler

```text
```

from langchain_core.runnables import RunnableConfig



def mark_process_failed(

    state: State, error: NodeError, config: RunnableConfig

) -> State:

    thread_id = config["configurable"].get("thread_id")

    return {"status": f"failed on thread {thread_id}: {error.error}"}

```
```

片段[3] `oss__javascript__langgraph__checkpointers#013` ｜ Checkpointers ｜ Core concepts > Checkpoints > Checkpoint namespace

```text
```

import { RunnableConfig } from "@langchain/core/runnables";



function myNode(state: typeof State.Type, config: RunnableConfig) {

  const checkpointNs = config.configurable?.checkpoint_ns;

  // "" for the parent graph, "node_name:uuid" for a subgraph

}

```
```

片段[4] `oss__python__langgraph__graph-api-nodes#001` ｜ Configure nodes ｜ Add runtime configuration

```text
2. Add the configuration to the function signature for nodes or conditional edges
```

片段[5] `oss__javascript__langgraph__graph-api-nodes#001` ｜ Configure nodes ｜ Add runtime configuration

```text
2. Add the configuration to the function signature for nodes or conditional edges
```

---

## v2-F-003（single-hop）

**问题**：messages 字段用 operator.add 做累加，某个节点想整体替换而不是继续追加，怎么写？

**gold**：从 langgraph.types 导入 Overwrite，让节点返回 {'messages': Overwrite(['replacement message'])} 即可。示例注释说明这样会 Bypass the reducer and replace the entire messages list，也就是绕过累加逻辑、把整个列表替换掉。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 LangGraph 里，如果 `messages` 字段用 `operator.add` 作为 reducer，节点默认返回的列表会被**追加**到已有值上。要让某个节点**整体替换**而不是追加，需要用 `Overwrite` 包裹返回值，绕过 reducer [2][10]。

最小可用示例（Python）：

```python
import operator
from langgraph.graph import END, START, StateGraph
from langgraph.types import Overwrite
from typing_extensions import Annotated, TypedDict

class State(TypedDict):
    messages: Annotated[list, operator.add]

def add_message(state: State):
    return {"messages": ["first message"]}  # 走 reducer，追加

def replace_messages(state: State):
    # 绕过 reducer，整体替换 messages 列表
    return {"messages": Overwrite(["replacement message"])}

builder = StateGraph(State)
builder.add_node("add_message", add_message)
builder.add_node("replace_messages", replace_messages)
builder.add_edge(START, "add_message")
builder.add_edge("add_message", "replace_messages")
# ... 继续 add_edge 到 END 并 compile
```

要点：
- 普通返回 `{"messages": [...]}` 会经过 `operator.add` 合并（追加）[2][5]。
- 返回 `{"messages": Overwrite([...])}` 会跳过 reducer，直接替换整个字段 [2][10]。
- 同样的 `Overwrite` 也可用于清空字段，例如 `Overwrite([])` [10]。

补充说明：片段 [2] 的示例只写到 `add_edge("add_message", "replace_messages")`，未展示后续到 `END` 的连边；片段 [9] 显示了 `add_edge("replace_messages", END)` 与 `compile()`，可据此补全。

**top5 片段**：

片段[1] `oss__python__langgraph__quickstart#003` ｜ Quickstart ｜ 2. Define state

```text
```

from langchain.messages import AnyMessage

from typing_extensions import TypedDict, Annotated

import operator



class MessagesState(TypedDict):

    messages: Annotated[list[AnyMessage], operator.add]

    llm_calls: int

```
```

片段[2] `oss__python__langgraph__graph-api-state#019` ｜ Define and update state ｜ Bypass reducers with Overwrite

```text
``` import operator from langgraph.graph import END, START, StateGraph from langgraph.types import Overwrite from typing_extensions import Annotated, TypedDict class State(TypedDict): messages: Annotated[list, operator.add] def add_message(state: State): return {"messages": ["first message"]} def replace_messages(state: State): # Bypass the reducer and replace the entire messages list return {"messages": Overwrite(["replacement message"])} builder = StateGraph(State) builder.add_node("add_message", add_message) builder.add_node("replace_messages", replace_messages) builder.add_edge(START, "add_message") builder.add_edge("add_message", "replace_messages")
```

片段[3] `oss__javascript__integrations__chat__anthropic#012` ｜ ChatAnthropic integration ｜ Content blocks

```text
``` AIMessage { "id": "msg_01DZGs9DyuashaYxJ4WWpWUP", "content": [ { "type": "text", "text": "Here is the calculation for 2 + 2:" }, { "type": "tool_use", "id": "toolu_01SQXBamkBr6K6NdHE7GWwF8", "name": "calculator", "input": { "number1": 2, "number2": 2, "operation": "add" } } ], "additional_kwargs": { "id": "msg_01DZGs9DyuashaYxJ4WWpWUP", "type": "message", "role": "assistant", "model": "claude-haiku-4-5-20251001", "stop_reason": "tool_use", "stop_sequence": null, "usage": { "input_tokens": 449, "output_tokens": 100 } }, "response_metadata": { "id": "msg_01DZGs9DyuashaYxJ4WWpWUP", "model": "claude-haiku-4-5-20251001", "stop_reason": "tool_use", "stop_sequence": null, "usage": {
```

片段[4] `oss__python__langgraph__workflows-agents#033` ｜ Workflows and agents ｜ Agents

```text
= [HumanMessage(content="Add 3 and 4.")] messages = agent.invoke({"messages": messages}) for m in messages["messages"]: m.pretty_print() ```
```

片段[5] `oss__python__langgraph__graph-api-state#008` ｜ Define and update state ｜ Process state updates with reducers

```text
```

from typing_extensions import Annotated



def add(left, right):

    """Can also import `add` from the `operator` built-in."""

    return left + right



class State(TypedDict):

    messages: Annotated[list[AnyMessage], add]

    extra_field: int

```
```

---

## v2-F-004（single-hop）

**问题**：两个节点之间传的中间数据，为什么第三个节点看不到？请按示例的打印输出说明。

**gold**：看示例输出：node_1 的输入只有 {'a': 'set at start'}，返回 {'private_data': 'set by node_1'}；node_2 的输入拿到了 {'private_data': 'set by node_1'}；而 node_3 的输入只有 {'a': 'set by node_2'}，看不到 private_data。最终图输出是 {'a': 'set by node_3'}，说明这类私有数据只在声明了对应输入类型的相邻节点之间流动。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

第三个节点看不到中间数据，是因为**中间数据被定义为「私有状态」（private state），只作为前一个节点的输出类型和后一个节点的输入类型存在，并不属于图的整体状态（OverallState）**。第三个节点声明接收的是 `OverallState`，因此它拿不到这份私有数据 [1][2][5][8]。

具体机制（以示例为准）：

- `node1` 的返回类型是 `Node1Output`（只含 `privateData`），这份数据不属于 `OverallState` [6][8]。
- `node2` 的输入类型被声明为 `Node2Input`（只含 `privateData`），所以它能读到 `node1` 传来的私有数据 [1][2][8]。
- `node3` 的输入类型是 `OverallState`，注释明确写着「Node 3 only has access to the overall state (no access to private data from node1)」[1][2][5]。
- 在 JS 版本里，这个输入类型是通过 `addNode` 的 `input` 选项指定的：`.addNode("node2", node2, { input: Node2Input })`，而 `node3` 没有指定，因此只接收整体状态 [5]。

## 按示例打印输出说明

示例中每个节点都会打印 `Input` 和 `Returned`：

- `node1` 打印：输入是整体状态（如 `{"a": "set at start"}`），返回 `{"privateData": "set by node1"}` [1][8]。
- `node2` 打印：输入是 `{"privateData": "set by node1"}`（只请求私有数据），返回 `{"a": "set by node2"}` [1][2]。
- `node3` 打印：输入是整体状态（含 `a`，但**不含** `privateData`），返回 `{"a": "set by node3"}` [1][2][5]。

也就是说，从打印的 `Input` 就能直接看出：`node2` 的输入里有 `privateData`，而 `node3` 的输入里没有——私有数据在 `node2` 之后就不再向下游传递了 [1][2][5]。

## 最小可用示例（Python，取自片段）

```python
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

class OverallState(TypedDict):
    a: str

class Node1Output(TypedDict):
    private_data: str

def node_1(state: OverallState) -> Node1Output:
    output = {"private_data": "set by node_1"}
    print(f"Entered node `node_1`:\n\tInput: {state}.\n\tReturned: {output}")
    return output

class Node2Input(TypedDict):
    private_data: str

def node_2(state: Node2Input) -> OverallState:
    output = {"a": "set by node_2"}
    print(f"Entered node `node_2`:\n\tInput: {state}.\n\tReturned: {output}")
    return output

def node_3(state: OverallState) -> OverallState:
    output = {"a": "set by node_3"}
    print(f"Entered node `node_3`:\n\tInput: {state}.\n\tReturned: {output}")
    return output

builder = StateGraph(OverallState).add_sequence([node_1, node_2, node_3])
builder.add_edge(START, "node_1")
graph = builder.compile()
response = graph.invoke({"a": "set at start"})
```

（节点定义与连接方式来自 [2][7][8]；JS 版本对应写法见 [5][6]。）

## 需要指出的差异

你的问题里说「两个节点之间传的中间数据」，片段中的术语是 **private state / private data**，并且是通过「节点输出类型 + 下游节点输入类型」来限定可见范围的，而不是一个通用的「中间数据」通道 [1][2][6][8]。另外，JS 版需要用 `addNode` 的 `input` 选项显式声明 `Node2Input`，Python 版则是通过函数参数类型标注 `Node2Input` 来体现 [2][5]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__graph-api-state#022` ｜ Define and update state ｜ Pass private state between nodes

```text
shared between node1 and node2 const node1: GraphNode<typeof OverallState> = (state) => { const output = { privateData: "set by node1" }; console.log(`Entered node 'node1':\n\tInput: ${JSON.stringify(state)}.\n\tReturned: ${JSON.stringify(output)}`); return output; }; const node2: GraphNode<typeof Node2Input> = (state) => { const output = { a: "set by node2" }; console.log(`Entered node 'node2':\n\tInput: ${JSON.stringify(state)}.\n\tReturned: ${JSON.stringify(output)}`); return output; }; // Node 3 only has access to the overall state (no access to private data from node1) const node3: GraphNode<typeof OverallState> = (state) => { const output = { a: "set by node3" };
```

片段[2] `oss__python__langgraph__graph-api-state#025` ｜ Define and update state ｜ Pass private state between nodes

```text
tput # Node 2 input only requests the private data available after node_1 class Node2Input(TypedDict): private_data: str def node_2(state: Node2Input) -> OverallState: output = {"a": "set by node_2"} print(f"Entered node `node_2`:\n\tInput: {state}.\n\tReturned: {output}") return output # Node 3 only has access to the overall state (no access to private data from node_1) def node_3(state: OverallState) -> OverallState: output = {"a": "set by node_3"} print(f"Entered node `node_3`:\n\tInput: {state}.\n\tReturned: {output}") return output # Connect nodes in a sequence # node_2 accepts private data from node_1, whereas # node_3 does not see the private data.
```

片段[3] `oss__python__langgraph__graph-api-state#026` ｜ Define and update state ｜ Pass private state between nodes

```text
# Connect nodes in a sequence # node_2 accepts private data from node_1, whereas # node_3 does not see the private data. builder = StateGraph(OverallState).add_sequence([node_1, node_2, node_3]) builder.add_edge(START, "node_1") graph = builder.compile() # Invoke the graph with the initial state response = graph.invoke( { "a": "set at start", } ) print() print(f"Output of graph invocation: {response}") ```
```

片段[4] `oss__python__deepagents__streaming#059` ｜ Streaming ｜ Stream multiple modes

```text
["data"]: if node_name not in INTERESTING_NODES: continue if mid_line: print() mid_line = False print(f"[{source}] step: {node_name}") elif chunk["type"] == "messages": token, metadata = chunk["data"] if token.content: # Print a header when the source changes if source != last_source: if mid_line: print() mid_line = False print(f"\n[{source}] ", end="") last_source = source print(token.content, end="", flush=True) mid_line = True elif chunk["type"] == "custom": if mid_line: print() mid_line = False print(f"[{source}] custom event:", chunk["data"]) print() ```
```

片段[5] `oss__javascript__langgraph__graph-api-state#023` ｜ Define and update state ｜ Pass private state between nodes

```text
rivate data from node1) const node3: GraphNode<typeof OverallState> = (state) => { const output = { a: "set by node3" }; console.log(`Entered node 'node3':\n\tInput: ${JSON.stringify(state)}.\n\tReturned: ${JSON.stringify(output)}`); return output; }; // Connect nodes in a sequence // node2 accepts private data from node1, whereas // node3 does not see the private data. const graph = new StateGraph(OverallState) .addNode("node1", node1) .addNode("node2", node2, { input: Node2Input }) .addNode("node3", node3) .addEdge(START, "node1") .addEdge("node1", "node2") .addEdge("node2", "node3") .addEdge("node3", END) .compile(); // Invoke the graph with the initial state
```

---

## v2-F-005（single-hop）

**问题**：开了 subgraphs=True 之后，怎么知道一条流事件来自根图还是某个子图？

**gold**：用 graph.stream 时传 subgraphs=True、stream_mode='updates' 和 version='v2'，每条 chunk 里 chunk['ns'] 就是命名空间：根图是 ()，子图是 ('node_2:<task_id>',)。chunk['type'] 是 'updates'，chunk['data'] 是 {node_name: {key: value}} 形式的更新。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 开了 `subgraphs=True` 后，用 `version="v2"` 的流式输出中，每条 chunk 的 `ns` 字段用来区分来源——根图是空元组 `()`，子图是包含节点名和 task_id 的元组（如 `("node_2:<task_id>",)`）[1][2][4]。判断方式就是看 `chunk["ns"]` 是否为空 [4]。

**最小可用示例（Python）：**

```python
for chunk in graph.stream(
    {"foo": "foo"},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            print(f"Subgraph {chunk['ns']}: {chunk['data']}")
        else:
            print(f"Root: {chunk['data']}")
```

**补充说明：**

- `ns` 的取值：根图为 `()`，子图为 `("node_name:<task_id>",)` [1][2][4]。
- 该 `ns` 字段出现在 `version="v2"` 的 `graph.stream(...)` 输出中 [1][2][4]；`stream_mode="messages"` 时同样有 `type`/`ns`/`data` 结构 [7]。
- 注意 API 差异：片段 [3][6] 展示的是 JavaScript 的 `graph.streamEvents(..., { subgraphs: true, version: "v3" })`，[5] 展示的是 Python 的 `graph.stream_events(input, version="v3")` 配合 `stream.subgraphs` 遍历（含 `subgraph.graph_name`、`subgraph.path`）。这些是 `streamEvents`/`stream_events` 的 v3 接口，与上面 `graph.stream(..., version="v2")` 的 `ns` 字段不是同一套用法，请按你实际调用的接口选择对应方式。

**top5 片段**：

片段[1] `oss__python__langgraph__use-subgraphs#047` ｜ Subgraphs ｜ Stream subgraph outputs

```text
```

for chunk in graph.stream(

    {"foo": "foo"},

    subgraphs=True,

    stream_mode="updates",

    version="v2",

):

    print(chunk["type"])  # "updates"

    print(chunk["ns"])    # () for root, ("node_2:<task_id>",) for subgraph

    print(chunk["data"])  # {"node_name": {"key": "value"}}

```
```

片段[2] `oss__python__langgraph__streaming#039` ｜ Streaming ｜ View example trace > Subgraph outputs

```text
```

for chunk in graph.stream(

    {"foo": "foo"},

    subgraphs=True,

    stream_mode="updates",

    version="v2",

):

    print(chunk["type"])  # "updates"

    print(chunk["ns"])    # () for root, ("node_name:<task_id>",) for subgraph

    print(chunk["data"])  # {"node_name": {"key": "value"}}

```
```

片段[3] `oss__javascript__langgraph__use-subgraphs#056` ｜ Subgraphs ｜ Stream subgraph outputs

```text
phNode1") .addEdge("subgraphNode1", "subgraphNode2"); const subgraph = subgraphBuilder.compile(); // Define parent graph const ParentState = new StateSchema({ foo: z.string(), }); const builder = new StateGraph(ParentState) .addNode("node1", (state) => { return { foo: "hi! " + state.foo }; }) .addNode("node2", subgraph) .addEdge(START, "node1") .addEdge("node1", "node2"); const graph = builder.compile(); const stream = await graph.streamEvents( { foo: "foo" }, { subgraphs: true, version: "v3", } ); for await (const snapshot of stream.values) { console.log(snapshot); } ```
```

片段[4] `oss__python__langgraph__streaming#043` ｜ Streaming ｜ View example trace > Subgraph outputs

```text
de_1", "subgraph_node_2") subgraph = subgraph_builder.compile() # Define parent graph class ParentState(TypedDict): foo: str def node_1(state: ParentState): return {"foo": "hi! " + state["foo"]} builder = StateGraph(ParentState) builder.add_node("node_1", node_1) builder.add_node("node_2", subgraph) builder.add_edge(START, "node_1") builder.add_edge("node_1", "node_2") graph = builder.compile() for chunk in graph.stream( {"foo": "foo"}, stream_mode="updates", # Set subgraphs=True to stream outputs from subgraphs subgraphs=True, version="v2", ): if chunk["type"] == "updates": if chunk["ns"]: print(f"Subgraph {chunk['ns']}: {chunk['data']}") else: print(f"Root: {chunk['data']}") ```
```

片段[5] `oss__python__langgraph__event-streaming#005` ｜ Event streaming ｜ Stream subgraphs

```text
```

stream = graph.stream_events(input, version="v3")



for subgraph in stream.subgraphs:

    print(subgraph.graph_name, subgraph.path)



    for message in subgraph.messages:

        print(message.text)

```
```

---

## v2-F-006（single-hop）

**问题**：从历史里挑一个检查点重放，哪些节点会再跑一遍？

**gold**：按示例，找到 write_joke 之前的检查点后调用 graph.invoke(None, before_joke.config)，结果是 write_joke 重新执行，注释写的是 re-executes (runs again)，而 generate_topic 不会重跑。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：从某个检查点重放时，该检查点之后已经执行过的节点会再跑一遍，检查点之前的节点不会重跑。** 也就是说，重放会从你选定的那个快照往后重新执行，而不是从头开始。

具体到文档里的例子：选一个 `next` 为 `("write_joke",)` 的检查点重放，`write_joke` 会重新执行，而它前面的 `generate_topic` 不会重跑 [3][7]。文档明确写道 `writeJoke re-executes (runs again), generateTopic does not` [7]。

另外，重放用的是 `get_state_history()` 拿到的快照配置，调用方式是 `graph.invoke(None, snapshot.config)`，即传入 `None` 作为输入、用快照的 config 来重放 [3][6]。

**最小可用示例（Python，来自 [3]）：**

```python
# Step 2: Find a checkpoint to replay from
history = list(graph.get_state_history(config))

# Step 3: Replay from a specific checkpoint
# Find the checkpoint before write_joke
before_joke = next(s for s in history if s.next == ("write_joke",))
replay_result = graph.invoke(None, before_joke.config)
```

**补充说明（关于“哪些节点会重跑”的边界）：**
- 片段 [4][5] 指出，节点内部的普通函数没有自己的检查点，会随节点一起重跑；`Task` 不会产生新的图检查点，恢复时外层入口或节点会从头重放，但已完成的任务会返回已存结果；子图在有状态模式下有自己的检查点。这影响的是“重跑粒度”，但片段没有进一步说明重放时 Task/子图的具体重跑行为，若你需要这一层的精确结论，给出的文档里没有找到能回答的内容。

**一处说法差异提示：** 你问的是“挑一个检查点重放”，文档示例实际挑的是“某个节点执行之前”的检查点（`s.next == ("write_joke",)`），重放后从该节点开始往后执行 [3][7]；文档没有给出“直接挑任意中间检查点”的额外规则说明。

**top5 片段**：

片段[1] `oss__python__deepagents__going-to-production#024` ｜ Going to production ｜ View example trace > Durability

```text
- Time travel . Every checkpointed step is a snapshot you can rewind to, letting you replay from an earlier state if something goes wrong.
```

片段[2] `oss__javascript__deepagents__going-to-production#025` ｜ Going to production ｜ View example trace > Durability

```text
- Time travel . Every checkpointed step is a snapshot you can rewind to, letting you replay from an earlier state if something goes wrong.
```

片段[3] `oss__python__langgraph__use-time-travel#003` ｜ Use time-travel ｜ Replay

```text
joke) .add_edge(START, "generate_topic") .add_edge("generate_topic", "write_joke") .compile(checkpointer=checkpointer) ) # Step 1: Run the graph config = {"configurable": {"thread_id": str(uuid7())}} result = graph.invoke({}, config) # Step 2: Find a checkpoint to replay from history = list(graph.get_state_history(config)) # History is in reverse chronological order for state in history: print(f"next={state.next}, checkpoint_id={state.config['configurable']['checkpoint_id']}") # Step 3: Replay from a specific checkpoint # Find the checkpoint before write_joke before_joke = next(s for s in history if s.next == ("write_joke",)) replay_result = graph.invoke(None, before_joke.config)
```

片段[4] `oss__python__langgraph__graph-api#011` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
| Primitive | Own checkpoint | On resume or retry | Choose when | | --- | --- | --- | --- | | Plain function inside a node | No. It runs inside the node’s super-step . | Re-runs whenever the node re-runs. | No routing fork after the step, and repeating it with the rest of the node is acceptable. | | Task | No new graph checkpoint. The result is stored with the running entrypoint or parent checkpoint. | The enclosing entrypoint or node replays from the start. Completed tasks return stored results. | The step has a side effect or is expensive, and must not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread.
```

片段[5] `oss__javascript__langgraph__graph-api#014` ｜ Graph API overview ｜ Nodes > Choose the unit of work

```text
| Primitive | Own checkpoint | On resume or retry | Choose when | | --- | --- | --- | --- | | Plain function inside a node | No. It runs inside the node’s super-step . | Re-runs whenever the node re-runs. | No routing fork after the step, and repeating it with the rest of the node is acceptable. | | Task | No new graph checkpoint. The result is stored with the running entrypoint or parent checkpoint. | The enclosing entrypoint or node replays from the start. Completed tasks return stored results. | The step has a side effect or is expensive, and must not repeat on resume. | | Subgraph | Yes for stateful modes: nodes checkpoint under a namespace of the parent thread.
```

---

## v2-F-007（single-hop）

**问题**：想改掉某一步的输入、从那里换一条路继续跑，标准做法是什么？

**gold**：先用 graph.get_state_history(config) 找到 next 等于 ('write_joke',) 的检查点 before_joke，再调用 graph.update_state(before_joke.config, values={'topic': 'chickens'}) 得到 fork_config，最后用 graph.invoke(None, fork_config) 从分叉点继续，write_joke 会用新主题重跑。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：标准做法是**从更早保存的 checkpoint 分叉（fork）出一条新路径**，而不是删除原有 checkpoint；分叉后从该 checkpoint 继续执行，原路径的 checkpoint 保留不动 [1][2][9][11]。如果该处存在 interrupt，则分叉后需要再用 `Command(resume=...)` 恢复，并循环直到运行完成且不再中断 [3][4][5]。

最小可用示例（Python，来自片段 [5]）：

```python
# 先找到想改的那一步之前的 checkpoint
history = list(graph.get_state_history(config))
before_ask = [s for s in history if s.next == ("ask_human",)][-1]

# 从该 checkpoint 分叉，写入新的输入
fork_config = graph.update_state(before_ask.config, {"value": ["forked"]})
fork_result = graph.invoke(None, fork_config)
# Pauses at interrupt — waiting for new Command(resume=...)

# 用不同的回答恢复分叉后的 interrupt
graph.invoke(Command(resume="Bob"), fork_config)
```

补充说明：
- 片段中“换一条路继续跑”的表述是 “continue from an earlier saved state without deleting the original checkpoints” [1][2]，对应 “fork from a mid-conversation checkpoint” [9][11]。
- 恢复 interrupt 的写法在 Python 片段中是 `Command(resume=...)`，作为下一次 `stream_events` 输入传入，并循环直到运行完成且不再中断 [4]；JS 片段同样使用 `Command(resume=...)` [3]。
- 注意 API 差异：片段 [5] 用的是 `graph.update_state(...)` 来分叉，而不是用户可能预期的其他“修改输入”接口；片段 [6] 的 Python 示例使用 `graph.stream_events(..., version="v3")`，与 [5] 的 `graph.invoke(...)` 写法不同，二者分别出现在不同示例中，请按所用版本选择。

**top5 片段**：

片段[1] `oss__python__langchain__frontend__time-travel#019` ｜ Time travel ｜ Use cases

```text
- Trying another path : continue from an earlier saved state without deleting the original checkpoints
```

片段[2] `oss__javascript__langchain__frontend__time-travel#019` ｜ Time travel ｜ Use cases

```text
- Trying another path : continue from an earlier saved state without deleting the original checkpoints
```

片段[3] `oss__javascript__langgraph__interrupts#027` ｜ Interrupts ｜ View example trace

```text
- Command(resume=...) : Pass as the next streamEvents input to resume; loop until the run completes without interrupting
```

片段[4] `oss__python__langgraph__interrupts#026` ｜ Interrupts ｜ View example trace

```text
- Command(resume=...) : Pass as the next stream_events input to resume; loop until the run completes without interrupting
```

片段[5] `oss__python__langgraph__use-time-travel#011` ｜ Use time-travel ｜ Interrupts

```text
{"value": []}, config) # Resume with answer graph.invoke(Command(resume="Alice"), config) # Replay from before ask_human history = list(graph.get_state_history(config)) before_ask = [s for s in history if s.next == ("ask_human",)][-1] replay_result = graph.invoke(None, before_ask.config) # Pauses at interrupt — waiting for new Command(resume=...) # Fork from before ask_human fork_config = graph.update_state(before_ask.config, {"value": ["forked"]}) fork_result = graph.invoke(None, fork_config) # Pauses at interrupt — waiting for new Command(resume=...) # Resume the forked interrupt with a different answer graph.invoke(Command(resume="Bob"), fork_config) # Result: {"value":
```

---

## v2-F-008（single-hop）

**问题**：订阅 checkpoints 这种流模式，图和调用分别要满足什么？

**gold**：图编译时要挂 checkpointer，示例用 MemorySaver()；graph.stream 时传 stream_mode='checkpoints' 和 version='v2'，然后在 chunk['type'] 为 'checkpoints' 时读取 chunk['data']。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：订阅 `checkpoints` 流模式需要图带 checkpointer；文档片段只明确了“需要 checkpointer”这一条件，没有额外说明调用侧必须传什么参数（如 `thread_id`），这部分在给出的片段里没有找到。

- `checkpoints` 模式返回 Checkpoint 事件，格式与 `get_state()` 相同，并且**需要 checkpointer** [4]。
- 片段中未说明调用 `stream`/`stream_events` 时针对 `checkpoints` 模式的具体必填参数；`thread_id` 的要求出现在 interrupt/resume 场景（外层 `invoke()` 或 `stream_events()` 必须包含 `thread_id` 以便 checkpoint 和恢复）[1]，不能直接等同于 `checkpoints` 流模式的调用要求。

最小可用示例（仅体现片段能支撑的部分：图编译时带 checkpointer，并用 `stream_mode="checkpoints"` 订阅；调用参数细节片段未给出）：

```python
# 片段仅能确认：需要 checkpointer [4]
graph = builder.compile(checkpointer=checkpointer)  # [4][11]

# 订阅 checkpoints 模式（模式名来自片段 [4]）
for chunk in graph.stream(inputs, stream_mode="checkpoints"):
    print(chunk)
```

补充说明：片段 [12] 展示的是 `stream_mode="updates"` 配合 `version="v2"` 的调用形式，并非 `checkpoints` 模式的示例，因此不能据此推断 `checkpoints` 模式的调用写法。

缺失内容：给出的文档里没有找到关于“订阅 `checkpoints` 流模式时调用侧（`stream`/`stream_events`）需要满足哪些参数条件”的说明。

**top5 片段**：

片段[1] `oss__python__migrate__langgraph-supervisor#010` ｜ Migrate from langgraph-supervisor ｜ Migrate interrupt and resume flows > Requirements for interrupt propagation

```text
2. Pass thread_id in configurable . The outer invoke() or stream_events() call must include a thread_id so the graph can checkpoint and resume.
```

片段[2] `oss__python__langgraph__interrupts#034` ｜ Interrupts ｜ View example trace > Approve or reject

```text
mpile(checkpointer=checkpointer) config = {"configurable": {"thread_id": "approval-123"}} initial = graph.stream_events( {"action_details": "Transfer $500", "status": "pending"}, config=config, version="v3", ) _ = initial.output  # drive the stream to completion print(initial.interrupts)  # -> (Interrupt(value={'question': ..., 'details': ...}),) # Resume with the decision; True routes to proceed, False to cancel resumed = graph.stream_events(Command(resume=True), config=config, version="v3") print(resumed.output["status"]) ```
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

片段[4] `oss__python__migrate__langgraph-supervisor#009` ｜ Migrate from langgraph-supervisor ｜ Migrate interrupt and resume flows > Requirements for interrupt propagation

```text
1. Compile only the outermost graph with a checkpointer. Leave subagents without checkpointer=... so they use per-invocation persistence and inherit the parent’s checkpointer at runtime.
```

片段[5] `oss__python__langgraph__streaming#010` ｜ Streaming ｜ Stream modes

```text
| Mode | Type | Description | | --- | --- | --- | | values | ValuesStreamPart | Full state after each step. | | updates | UpdatesStreamPart | State updates after each step. Multiple updates in the same step are streamed separately. | | messages | MessagesStreamPart | 2-tuples of (LLM token, metadata) from LLM calls. | | custom | CustomStreamPart | Custom data emitted from nodes via get_stream_writer . | | checkpoints | CheckpointStreamPart | Checkpoint events (same format as get_state() ). Requires a checkpointer. | | tasks | TasksStreamPart | Task start/finish events with results and errors. Requires a checkpointer. |
```

---

## v2-F-009（single-hop）

**问题**：想按调用方传入的用户名动态拼系统提示词，官方示例怎么把这份静态配置送进中间件？

**gold**：先定义 dataclass ContextSchema，里面有 user_name 字段；create_agent 时传 context_schema=ContextSchema 和 middleware=[personalized_prompt]；被 @dynamic_prompt 装饰的 personalized_prompt 通过 request.runtime.context.user_name 取值；调用时用 agent.invoke(..., context=ContextSchema(user_name='John Smith')) 把配置送进去。

**judge 分**：0.0　**拒答标记**：None

**回答**：

结论：官方示例里，用户名不是写死在中间件里，而是通过 `createAgent` 的 `contextSchema` 声明为运行时上下文，再在 `agent.invoke` 的第二个参数 `{ context: { userName: ... } }` 里按调用传入；中间件通过 `runtime.context?.userName` 读取 [1][8]。注意片段 [1] 用的是 `createMiddleware` + `beforeModel`，片段 [2] 用的是 `dynamicSystemPromptMiddleware`，两者写法不同，以片段为准 [1][2]。

最小可用示例（来自片段 [1][8]）：

```javascript
import * as z from "zod";
import { createAgent, createMiddleware, SystemMessage } from "langchain";

const contextSchema = z.object({ userName: z.string() });

const dynamicPromptMiddleware = createMiddleware({
  name: "DynamicPrompt",
  contextSchema,
  beforeModel: (state, runtime) => {
    const userName = runtime.context?.userName;
    if (!userName) {
      throw new Error("userName is required");
    }
    const systemMsg = `You are a helpful assistant. Address the user as ${userName}.`;
    return { messages: [new SystemMessage(systemMsg), ...state.messages] };
  },
});

const agent = createAgent({
  model: "gpt-6.1-sol",
  tools: [ /* ... */ ],
  middleware: [dynamicPromptMiddleware],
  contextSchema,
});

const result = await agent.invoke(
  { messages: [{ role: "user", content: "What's my name?" }] },
  { context: { userName: "John Smith" } }
);
```

补充差异提示：
- 片段 [2] 的示例用 `dynamicSystemPromptMiddleware<ContextSchema>((_, config) => ...)` 并从 `config.context?.userName` 读取，与片段 [1] 的 `runtime.context?.userName` 写法不同 [1][2]。
- 片段 [3] 说明 `dynamicSystemPromptMiddleware` 的返回值是“追加合并”而非替换已有 system message [3]。
- 片段 [5][6] 展示的是把 `userName` 放进 `stateSchema`（自定义 state）而非 `contextSchema`，读取位置是 `state.userName` / `request.state.userName`，与“调用方传入 context”的方式不同，注意区分 [5][6]。

**top5 片段**：

片段[1] `oss__javascript__langchain__runtime#008` ｜ Runtime ｜ Access > Inside middleware

```text
``` import * as z from "zod"; import { createAgent, createMiddleware, SystemMessage } from "langchain"; const contextSchema = z.object({ userName: z.string(), }); // Dynamic prompt middleware const dynamicPromptMiddleware = createMiddleware({ name: "DynamicPrompt", contextSchema, beforeModel: (state, runtime) => { const userName = runtime.context?.userName; if (!userName) { throw new Error("userName is required"); } const systemMsg = `You are a helpful assistant. Address the user as ${userName}.`; return { messages: [new SystemMessage(systemMsg), ...state.messages], }; }, }); // Logging middleware const loggingMiddleware = createMiddleware({ name: "Logging", contextSchema, beforeModel:
```

片段[2] `oss__javascript__langchain__short-term-memory#034` ｜ Short-term memory ｜ Access memory > Prompt

```text
``` import * as z from "zod"; import { createAgent, tool, dynamicSystemPromptMiddleware } from "langchain"; const contextSchema = z.object({ userName: z.string(), }); type ContextSchema = z.infer<typeof contextSchema>; const getWeather = tool( async ({ city }) => { return `The weather in ${city} is always sunny!`; }, { name: "get_weather", description: "Get user info", schema: z.object({ city: z.string(), }), } ); const agent = createAgent({ model: "gpt-5-nano", tools: [getWeather], contextSchema, middleware: [ dynamicSystemPromptMiddleware<ContextSchema>((_, config) => { return `You are a helpful assistant. Address the user as ${config.context?.userName}.`; }), ], });
```

片段[3] `oss__javascript__releases__changelog#031` ｜ Changelog ｜ v1.1.0

```text
- Dynamic system prompt middleware : Return values from dynamicSystemPromptMiddleware are now purely additive. When returning a SystemMessage or string , they are merged with existing system messages rather than replacing them, making it easier to compose multiple middleware that modify the prompt.
```

片段[4] `oss__python__langchain__runtime#007` ｜ Runtime ｜ Access > Inside middleware

```text
``` from dataclasses import dataclass from langchain.messages import AnyMessage from langchain.agents import create_agent, AgentState from langchain.agents.middleware import dynamic_prompt, ModelRequest, before_model, after_model from langgraph.runtime import Runtime @dataclass class Context: user_name: str # Dynamic prompts @dynamic_prompt def dynamic_system_prompt(request: ModelRequest) -> str: user_name = request.runtime.context.user_name system_prompt = f"You are a helpful assistant. Address the user as {user_name}." return system_prompt # Before model hook @before_model def log_before_model(state: AgentState, runtime: Runtime[Context]) -> dict | None:
```

片段[5] `oss__javascript__migrate__langchain-v1#015` ｜ LangChain v1 migration guide ｜ createAgent > Custom state

```text
``` import * as z from "zod"; import { createAgent, createMiddleware, tool } from "langchain"; const UserState = z.object({ userName: z.string(), }); const userState = createMiddleware({ name: "UserState", stateSchema: UserState, beforeModel: (state) => { // Access custom state properties const name = state.userName; // Optionally modify messages/system prompt based on state return; }, }); const greet = tool( async () => { return "Hello!"; }, { name: "greet", description: "Greet the user", schema: z.object({}), } ); const agent = createAgent({ model: "claude-sonnet-4-6", tools: [greet], middleware: [userState], }); await agent.invoke({ messages: [{ role: "user", content: "Hi" }], userName:
```

---

## v2-F-010（single-hop）

**问题**：Runtime、Framework、Harness 三层各自提供什么价值，什么时候该选哪一层？

**gold**：按对照表，Runtime 的价值是 Durable execution、Streaming、HITL、Persistence，适合需要低层控制、长时间运行且有状态的工作流和 agent，选项有 LangGraph、Temporal、Inngest。Framework 提供 Abstractions 和 Integrations，适合快速起步、统一团队的构建方式，选项有 LangChain、Vercel 的 AI SDK、CrewAI、OpenAI Agents SDK、Google ADK、LlamaIndex。Harness 提供 Predefined tools、Prompts、Subagents，适合更自主、面对复杂非确定任务的 agent，选项有 Deep Agents SDK、Claude Agent SDK、Manus。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

文档把产品分为三层，各自的价值与适用场景如下：

- **Runtime**：价值是 Durable execution（持久执行）、Streaming（流式）、HITL（人机协同）、Persistence（持久化）；适用于需要低层控制、长时间运行、有状态的工作流与 agent [1][2]。
- **Framework**：价值是 Abstractions（抽象）、Integrations（集成）；适用于快速上手、统一团队构建方式 [1][2]。
- **Harness**：价值是 Predefined tools（预置工具）、Prompts（提示词）、Subagents（子 agent）；适用于更自主的 agent、面对复杂且非确定性任务的 agent [1][2]。

各层的可选方案（Options）：
- Runtime：LangGraph、Temporal、Inngest [1][2]
- Framework：LangChain、Vercel's AI SDK、CrewAI、OpenAI Agents SDK、Google ADK、LlamaIndex [1][2]
- Harness：Deep Agents SDK、Claude Agent SDK、Manus [1][2]

补充：若只是构建不需要复杂编排的简单 agent 应用，文档建议使用 LangChain 这类 agent framework [7][9]。

**最小可用示例：**

文档片段中没有给出直接演示"如何在三层之间选择"的代码示例。与 Runtime 相关的最小代码示例是 LangGraph 节点接收 `Runtime` 对象（Python）：

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

[11]

**说明：** 片段中未提供 Framework 层与 Harness 层的具体代码示例，因此这两层只能给出上表中的定位与选型依据，无法给出可运行示例。

**top5 片段**：

片段[1] `oss__javascript__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[2] `oss__python__concepts__products#001` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
|  | Runtime | Framework | Harness |

| --- | --- | --- | --- |

| Value add | Durable execution Streaming HITL Persistence | Abstractions Integrations | Predefined tools Prompts Subagents |

| When to use | Low-level control Long running, stateful workflows and agents | Getting started quickly Standardizing how a team builds | More autonomous agents Agents faced with complex, non-deterministic tasks |

| Options | LangGraph Temporal Inngest | LangChain Vercel’s AI SDK CrewAI OpenAI Agents SDK Google ADK LlamaIndex | Deep Agents SDK Claude Agent SDK Manus |
```

片段[3] `oss__javascript__concepts__products#000` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
Runtimes, frameworks, and harnesses Understand the differences between LangChain, LangGraph, and Deep Agents and when to use each one
```

片段[4] `oss__python__concepts__products#000` ｜ Runtimes, frameworks, and harnesses ｜ ROOT

```text
Runtimes, frameworks, and harnesses Understand the differences between LangChain, LangGraph, and Deep Agents and when to use each one
```

片段[5] `oss__python__langgraph__graph-api#009` ｜ Graph API overview ｜ Nodes

```text
3. runtime : A Runtime object with runtime context , store , stream_writer , execution_info , and related helpers
```

---

## v2-F-011（single-hop）

**问题**：trace 里不想留下用户社保号，官方给了什么机制？怎么接到图上？

**gold**：先用 from langsmith.anonymizer 导入 create_anonymizer 建脱敏器，传入 pattern 与 replace 规则，示例把 SSN 匹配替换为 <ssn>；再用 Client(anonymizer=anonymizer) 创建 tracer_client，交给 LangChainTracer(client=tracer_client)，最后在图上用 .with_config({'callbacks': [tracer]}) 挂上。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：官方给了 **anonymizer（匿名化器）** 机制，用正则匹配敏感数据（示例里就是社保号 SSN）并替换成占位符，然后把带 anonymizer 的 LangSmith Client 注入 `LangChainTracer`，再通过 `callbacks` 挂到图上 [4][5]。

- 机制：用 `create_anonymizer` 定义匹配规则（pattern + replace），示例规则匹配 SSN 并替换为 `<ssn>` [4][5]。
- 接入方式：把 anonymizer 传给 LangSmith `Client`，再用该 client 构造 `LangChainTracer`，最后在编译后的图上通过 `with_config` / `withConfig` 的 `callbacks` 挂载 tracer [4][5]。

最小可用示例（Python，来自片段 [5]）：

```python
from langchain_core.tracers.langchain import LangChainTracer
from langgraph.graph import StateGraph, MessagesState
from langsmith import Client
from langsmith.anonymizer import create_anonymizer

anonymizer = create_anonymizer([
    # Matches SSNs
    { "pattern": r"\b\d{3}-?\d{2}-?\d{4}\b", "replace": "<ssn>" }
])

tracer_client = Client(anonymizer=anonymizer)
tracer = LangChainTracer(client=tracer_client)
# Define the graph
graph = (
    StateGraph(MessagesState)
    ...
    .compile()
    .with_config({'callbacks': [tracer]})
)
```

JavaScript 版本（来自片段 [4]）同样是 `createAnonymizer` → `new Client({ anonymizer })` → `new LangChainTracer({ client: langsmithClient })` → `.withConfig({ callbacks: [tracer] })` [4]。

补充说明（与问题相关的其他片段）：
- 如果只是**完全不想把数据发到 LangSmith**，可以在 `.env` 里设 `LANGSMITH_TRACING=false`，这样本地服务器不会有数据外发 [1][2][3]。但这属于“关闭追踪”，不是“追踪里脱敏”，与 anonymizer 是两种不同手段。
- 片段 [6][13] 还提到 middleware 层的 `TracePolicy(process_inputs=omit_payload)` 可省略输入载荷，但那是针对 agent middleware 的追踪策略，不是针对 SSN 的正则替换，且片段未说明如何接到图上，因此不作为本问题的主要答案。

**top5 片段**：

片段[1] `oss__python__langchain__studio#000` ｜ LangSmith Studio ｜ Prerequisites

```text
- If you don’t want data traced to LangSmith, set LANGSMITH_TRACING=false in your agent’s .env file. With tracing disabled, no data leaves your local server.
```

片段[2] `oss__javascript__langchain__studio#000` ｜ LangSmith Studio ｜ Prerequisites

```text
- If you don’t want data traced to LangSmith, set LANGSMITH_TRACING=false in your agent’s .env file. With tracing disabled, no data leaves your local server.
```

片段[3] `oss__python__langgraph__studio#000` ｜ LangSmith Studio ｜ Prerequisites

```text
- If you don’t want data traced to LangSmith, set LANGSMITH_TRACING=false in your agent’s .env file. With tracing disabled, no data leaves your local server.
```

片段[4] `oss__javascript__langgraph__observability#003` ｜ LangSmith Observability ｜ Use anonymizers to prevent logging of sensitive data in traces

```text
```

import { StateGraph } from "@langchain/langgraph";

import { LangChainTracer } from "@langchain/core/tracers/tracer_langchain";

import { StateAnnotation } from "./state.js";

import { createAnonymizer } from "langsmith/anonymizer"

import { Client } from "langsmith"



const anonymizer = createAnonymizer([

  // Matches SSNs

  { pattern: /\b\d{3}-?\d{2}-?\d{4}\b/, replace: "<ssn>" }

])



const langsmithClient = new Client({ anonymizer })

const tracer = new LangChainTracer({

  client: langsmithClient,

});



export const graph = new StateGraph(StateAnnotation)

  .compile()

  .withConfig({ callbacks: [tracer] });

```
```

片段[5] `oss__python__langgraph__observability#004` ｜ LangSmith Observability ｜ Use anonymizers to prevent logging of sensitive data in traces

```text
```

from langchain_core.tracers.langchain import LangChainTracer

from langgraph.graph import StateGraph, MessagesState

from langsmith import Client

from langsmith.anonymizer import create_anonymizer



anonymizer = create_anonymizer([

    # Matches SSNs

    { "pattern": r"\b\d{3}-?\d{2}-?\d{4}\b", "replace": "<ssn>" }

])



tracer_client = Client(anonymizer=anonymizer)

tracer = LangChainTracer(client=tracer_client)

# Define the graph

graph = (

    StateGraph(MessagesState)

    ...

    .compile()

    .with_config({'callbacks': [tracer]})

)

```
```

---

## v2-F-012（single-hop）

**问题**：用命名空间前缀列出 store 条目时，只传 ('alice',) 会不会把子命名空间也算进来？

**gold**：会。namespace_prefix 按前缀匹配而不是精确匹配，('alice',) 也会返回 ('alice', 'memories')、('alice', 'preferences') 这类子命名空间下的条目；要限定只取一层，就传完整 namespace，或者在客户端按 item.namespace 过滤。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：会。** `namespace_prefix` 是**前缀匹配**，不是精确匹配。只传 `("alice",)` 时，也会返回 `("alice", "memories")`、`("alice", "preferences")` 等子命名空间下的条目 [1][2][5]。

如果只想限定在单一层级，需要传入**完整命名空间**，或者在客户端根据 `item.namespace` 过滤返回结果 [1][2]。

**最小可用示例（Python）：**

```python
# 前缀匹配：会包含 ("alice", "memories") 等子命名空间
items = store.search(("alice",), limit=100)

# 只取单一层级：传完整命名空间
items = store.search(("alice", "memories"), limit=100)
```

```javascript
// 前缀匹配：会包含 ["alice", "memories"] 等子命名空间
const items = await store.search(["alice"], { limit: 100 });

// 只取单一层级：传完整命名空间
const items = await store.search(["alice", "memories"], { limit: 100 });
```

补充两点片段中的相关说明：
- 列举命名空间时可用 `prefix` 配合 `maxDepth` 截断层级，例如 `store.list_namespaces(prefix=("alice",), max_depth=2)` [4]（JS 对应 `store.listNamespaces({ prefix: ["alice"], maxDepth: 2 })` [3]）。
- 结果超过 `limit` 会被**静默截断**，没有溢出信号，建议把 `limit` 设得高于预期最大值，或用 `offset` 分页 [7][9][12][14]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__stores#006` ｜ Stores ｜ Listing items in a namespace

```text
- namespace_prefix matches by prefix, not exactly. ("alice",) also returns items under ("alice", "memories") , ("alice", "preferences") , and so on. To restrict to a single level, pass the full namespace or filter the returned items client-side on item.namespace .
```

片段[2] `oss__python__langgraph__stores#006` ｜ Stores ｜ Listing items in a namespace

```text
- namespace_prefix matches by prefix, not exactly. ("alice",) also returns items under ("alice", "memories") , ("alice", "preferences") , and so on. To restrict to a single level, pass the full namespace or filter the returned items client-side on item.namespace .
```

片段[3] `oss__javascript__langgraph__stores#010` ｜ Stores ｜ Listing items in a namespace

```text
```

// All namespaces that start with ["alice"], truncated to two levels deep.

const namespaces = await store.listNamespaces({ prefix: ["alice"], maxDepth: 2 });

```
```

片段[4] `oss__python__langgraph__stores#010` ｜ Stores ｜ Listing items in a namespace

```text
```

# All namespaces that start with ("alice",), truncated to two levels deep.

namespaces = store.list_namespaces(prefix=("alice",), max_depth=2)

```
```

片段[5] `oss__python__langgraph__stores#005` ｜ Stores ｜ Listing items in a namespace

```text
```

# Return up to 100 items stored under ("alice", "memories").

items = store.search(("alice", "memories"), limit=100)

```
```

---

## v2-F-013（single-hop）

**问题**：同样一次列表查询，Postgres 版和内存版 store 返回的顺序一样吗？

**gold**：不一样，顺序取决于后端：PostgresStore 和 AsyncPostgresStore 按 updated_at 倒序返回，最近更新的在前；InMemoryStore 按插入顺序返回，最近插入的在最后。不要依赖跨实现的顺序，需要稳定顺序就在客户端按 item.updated_at 排序。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不一样，不能依赖跨实现的一致顺序。**

- PostgresStore 和 AsyncPostgresStore 默认按 `updated_at` 降序返回（最近更新的在前）[1][2]。
- InMemoryStore 按插入顺序返回（最近插入的在最后）[1][2]。
- 文档明确说不要跨实现依赖特定顺序；如果顺序重要，应在客户端按 `item.updated_at` 自行排序 [1][2]。

**最小示例（客户端排序，JavaScript）：**

```javascript
const page = await store.search(["alice", "memories"], { limit: 50, offset: 0 });
page.sort((a, b) => b.updatedAt - a.updatedAt); // 按 updated_at 降序
```

（分页遍历写法可参考 [9]，但排序仍需自行处理 [1][2]。）

**top5 片段**：

片段[1] `oss__javascript__langgraph__stores#008` ｜ Stores ｜ Listing items in a namespace

```text
- Default ordering depends on the store backend. PostgresStore and AsyncPostgresStore return results ordered by updated_at descending (most recently updated first). InMemoryStore returns results in insertion order (most recently inserted last). Do not rely on a specific order across implementations; sort client-side on item.updated_at if order matters.
```

片段[2] `oss__python__langgraph__stores#008` ｜ Stores ｜ Listing items in a namespace

```text
- Default ordering depends on the store backend. PostgresStore and AsyncPostgresStore return results ordered by updated_at descending (most recently updated first). InMemoryStore returns results in insertion order (most recently inserted last). Do not rely on a specific order across implementations; sort client-side on item.updated_at if order matters.
```

片段[3] `oss__python__langgraph__add-memory#033` ｜ Memory ｜ Add long-term memory > Use in production

```text
.store.search(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories]) system_msg = f"You are a helpful assistant talking to the user. User info: {info}" # Store new memories if the user asks the model to remember last_message = state["messages"][-1] if "remember" in last_message.content.lower(): memory = "User name is Bob" runtime.store.put(namespace, str(uuid7()), {"data": memory}) response = model.invoke( [{"role": "system", "content": system_msg}] + state["messages"] ) return {"messages": response} DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable" with ( PostgresStore.from_conn_string(DB_URI) as store,
```

片段[4] `oss__python__langgraph__add-memory#029` ｜ Memory ｜ Add long-term memory > Use in production

```text
store.asearch(namespace, query=str(state["messages"][-1].content)) info = "\n".join([d.value["data"] for d in memories]) system_msg = f"You are a helpful assistant talking to the user. User info: {info}" # Store new memories if the user asks the model to remember last_message = state["messages"][-1] if "remember" in last_message.content.lower(): memory = "User name is Bob" await runtime.store.aput(namespace, str(uuid7()), {"data": memory}) response = await model.ainvoke( [{"role": "system", "content": system_msg}] + state["messages"] ) return {"messages": response} DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable" async with (
```

片段[5] `oss__python__langchain__long-term-memory#005` ｜ Long-term memory ｜ Memory storage

```text
``` from collections.abc import Sequence from langgraph.store.base import IndexConfig from langgraph.store.postgres import PostgresStore  # type: ignore[import-not-found] def embed(texts: Sequence[str]) -> list[list[float]]: # Replace with an actual embedding function or LangChain embeddings object return [[1.0, 2.0] for _ in texts] DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres?sslmode=disable" with PostgresStore.from_conn_string( DB_URI, index=IndexConfig(embed=embed, dims=2),  # type: ignore[arg-type] ) as store: store.setup() user_id = "my-user" application_context = "chitchat" namespace = (user_id, application_context) store.put( namespace, "a-memory", { "rules": [
```

---

## v2-F-014（single-hop）

**问题**：一个节点要按列表里的每个元素并发派活，和要在同一次返回里边改状态边决定下一步，分别用什么？

**gold**：并发派活用 Send：返回 [Send('generate_joke', {'subject': s}) for s in state['subjects']]，每个元素一个 worker。改状态并路由用 Command：返回 Command(update={'foo': 'bar'}, goto='my_other_node')，需要时把节点返回类型标成 Command[Literal['my_other_node']]。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- 按列表里的每个元素并发派活（每个元素一份输入、数量运行时才知道）→ 用 **`Send`** [8][10]。
- 在同一次返回里既更新状态又决定下一步 → 用 **`Command`** [1][2]。

**最小可用示例（Python）：**

```python
from typing import Literal
from langgraph.types import Command, Send

# Send：按列表每个元素 fan out 一个 worker
def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

# Command：一次返回里更新状态并路由
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        update={"foo": "bar"},
        goto="my_other_node",
    )
```

[7]

**补充说明（以片段为准）：**

- `Command` 的适用场景片段明确列出三种：一步同时更新状态并选择下一节点、在 interrupt 之后恢复、从 tool 更新状态 [1][2]。
- `Send` 的适用场景是「同一个节点对每个 item 各跑一次、每个 item 有自己的输入、item 数量运行时才确定（map-reduce / orchestrator-worker）」[8][10]。
- 片段中未出现与上述 API 名称或参数不一致的说法。

**top5 片段**：

片段[1] `oss__python__langgraph__use-graph-api#007` ｜ Build checklist for the Graph API ｜ Build your graph

```text
- Use Command when one step must both update state and choose the next node, resume after an interrupt , or update state from a tool.
```

片段[2] `oss__javascript__langgraph__use-graph-api#008` ｜ Build checklist for the Graph API ｜ Build your graph

```text
- Use Command when one step must both update state and choose the next node, resume after an interrupt , or update state from a tool.
```

片段[3] `oss__javascript__langgraph__use-graph-api#007` ｜ Build checklist for the Graph API ｜ Build your graph

```text
- Use Send when you must run the same node once per item, each with its own input, and the item count is only known at runtime (map-reduce / orchestrator-worker).
```

片段[4] `oss__python__langgraph__use-graph-api#006` ｜ Build checklist for the Graph API ｜ Build your graph

```text
- Use Send when you must run the same node once per item, each with its own input, and the item count is only known at runtime (map-reduce / orchestrator-worker).
```

片段[5] `oss__python__deepagents__interpreters#032` ｜ Interpreters ｜ Dynamic subagents

```text
- Fan-out and synthesize : Run the same kind of work across many items in parallel, then combine the results.
```

---

## v2-F-015（single-hop）

**问题**：默认的重试策略具体是什么参数？第一次重试前等多久、退避怎么放大？

**gold**：按参数表，max_attempts 默认 3，含第一次尝试；initial_interval 默认 0.5 秒，是第一次重试前的等待；backoff_factor 默认 2.0，每次重试后把间隔乘上它；max_interval 默认 128.0 秒，是重试间隔上限；jitter 默认 True；retry_on 默认 default_retry_on。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：LangGraph 的重试默认参数在 Python 和 JavaScript 两版文档里单位不同，需要区分。默认最多尝试 3 次（含首次），退避按倍数放大，并默认开启抖动。

**Python 版（LangGraph）默认值** [2]：
- `max_attempts` = 3（含首次尝试）
- `initial_interval` = 0.5 **秒**（第一次重试前等待）
- `backoff_factor` = 2.0（每次重试后间隔乘以该系数）
- `max_interval` = 128.0 秒（重试间隔上限）
- `jitter` = True（加入随机抖动）
- `retry_on` 默认 `default_retry_on`

**JavaScript 版（LangGraph）默认值** [1]：
- `maxAttempts` = 3（含首次尝试）
- `initialInterval` = 500 **毫秒**（第一次重试前等待）
- `backoffFactor` = 2.0
- `maxInterval` = 128000 毫秒
- `jitter` = true
- `retryOn` 默认内置处理器（仅在配置了 retryPolicy 时使用）

所以：第一次重试前，Python 等 0.5 秒、JS 等 500 毫秒（两者等价）；之后每次间隔按 2.0 倍放大，直到上限（Python 128 秒 / JS 128000 毫秒），并叠加随机抖动 [1][2]。

注意差异：用户若说“默认等 1 秒”或“退避 1.5 倍”，与片段不符——片段中首次等待是 0.5 秒/500 毫秒，倍数是 2.0 [1][2]。另外 Python 用秒、JS 用毫秒，参数命名风格也不同（snake_case vs camelCase）[1][2]。

最小可用示例（Python，显式写出默认值）[10]：

```python
from langgraph.types import RetryPolicy

builder.add_node(
    "call_api",
    call_api,
    retry_policy=RetryPolicy(max_attempts=3),
)
```

补充：片段 [3][4] 里的 `ModelRetryMiddleware` 是另一套“模型重试中间件”，其参数名（`max_retries`、`initial_delay`/`initialDelayMs`、`backoff_factor`/`backoffFactor`）与 LangGraph 的 `RetryPolicy` 不同，不要混用 [3][4]。

**top5 片段**：

片段[1] `oss__javascript__langgraph__fault-tolerance#005` ｜ Fault tolerance ｜ Retries > Parameters

```text
| Parameter | Type | Default | Description | | --- | --- | --- | --- | | maxAttempts | number | 3 | Maximum number of attempts, including the first. | | initialInterval | number | 500 | Milliseconds before the first retry. | | backoffFactor | number | 2.0 | Multiplier applied to the interval after each retry. | | maxInterval | number | 128000 | Maximum milliseconds between retries. | | jitter | boolean | true | Add random jitter to the interval. | | retryOn | (error: unknown) => boolean | built-in handler (when policy is set) | Callable returning true for retryable exceptions. Only used when retryPolicy is configured. |
```

片段[2] `oss__python__langgraph__fault-tolerance#003` ｜ Fault tolerance ｜ Retries > Parameters

```text
| Parameter | Type | Default | Description |

| --- | --- | --- | --- |

| max_attempts | int | 3 | Maximum number of attempts, including the first. |

| initial_interval | float | 0.5 | Seconds before the first retry. |

| backoff_factor | float | 2.0 | Multiplier applied to the interval after each retry. |

| max_interval | float | 128.0 | Maximum seconds between retries. |

| jitter | bool | True | Add random jitter to the interval. |

| retry_on | type[Exception] \| Sequence[type[Exception]] \| Callable[[Exception], bool] | default_retry_on | Exceptions to retry on, or a callable returning True for retryable exceptions. |
```

片段[3] `oss__python__langgraph__fault-tolerance#004` ｜ Fault tolerance ｜ Retries > Custom retry logic

```text
```

from langgraph.types import RetryPolicy, default_retry_on



def custom_retry_on(exc: BaseException) -> bool:

    if isinstance(exc, MyCustomError):

        return False

    return default_retry_on(exc)



builder.add_node(

    "call_api",

    call_api,

    retry_policy=RetryPolicy(max_attempts=3, retry_on=custom_retry_on),

)

```
```

片段[4] `oss__python__langchain__middleware__built-in#017` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model retry

```text
sage formatting def format_error(error: Exception) -> str: return f"Model call failed: {error}. Please try again later." retry_with_formatter = ModelRetryMiddleware( max_retries=4, on_failure=format_error, ) # Constant backoff (no exponential growth) constant_backoff = ModelRetryMiddleware( max_retries=5, backoff_factor=0.0,  # No exponential growth initial_delay=2.0,  # Always wait 2 seconds ) # Raise exception on failure strict_retry = ModelRetryMiddleware( max_retries=2, on_failure="error",  # Re-raise exception instead of returning message ) ```
```

片段[5] `oss__javascript__langchain__middleware__built-in#017` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model retry

```text
message formatting const formatError = (error: Error) => `Model call failed: ${error.message}. Please try again later.`; const retryWithFormatter = modelRetryMiddleware({ maxRetries: 4, onFailure: formatError, }); // Constant backoff (no exponential growth) const constantBackoff = modelRetryMiddleware({ maxRetries: 5, backoffFactor: 0.0, // No exponential growth initialDelayMs: 2000, // Always wait 2 seconds }); // Raise exception on failure const strictRetry = modelRetryMiddleware({ maxRetries: 2, onFailure: "error", // Re-raise exception instead of returning message }); ```
```

---

## v2-F-016（multi-hop）

**问题**：会话连续性数据和用户偏好这类跨会话的长期数据，分别该由哪个组件存？它们在图里怎么一起接上？

**gold**：按对照表，checkpointer 存的是图状态的快照，作用域是单个线程，属于短期、线程作用域记忆，靠 graph config 里的 thread_id 访问；store 存应用自定义的键值数据，跨线程共享，属于长期记忆，适合用户偏好、事实和共享知识，节点或应用代码可以直接读写。接法是一起交给 compile：示例用 InMemorySaver 作 checkpointer，然后 builder.compile(checkpointer=checkpointer, store=store)；图还可以带 context_schema=Context。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

- **会话连续性数据**（同一线程内的多轮对话、human-in-the-loop、time travel、容错）应由 **Checkpointer** 持久化，它保存的是「图状态快照」，作用域是**单个 thread**，属于**短期、线程级记忆** [7][8]。
- **用户偏好、事实、共享知识这类跨会话长期数据**应由 **Store** 持久化，它保存的是「应用自定义的 key-value 数据」，作用域是**跨 thread**，属于**长期、跨线程记忆** [7][8]；Store 用于把应用定义的数据持久化到图状态之外，适合长期、跨线程记忆 [4][5]。
- 在工具（tool）语境下，长期记忆对应 **Store** 组件，描述为「persistent data that survives across conversations」，用例是保存用户偏好、维护知识库 [1]。
- 两者的接入方式不同：Checkpointer 通过在图 config 里传 `thread_id` 访问；Store 则是在节点或应用代码里读写条目 [7][8]。

**最小可用示例（Python，按片段 [13] 的写法接 Checkpointer）**

```python
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph

checkpointer = InMemorySaver()

builder = StateGraph(...)
graph = builder.compile(checkpointer=checkpointer)

graph.invoke(
    {"messages": [{"role": "user", "content": "hi! i am Bob"}]},
    {"configurable": {"thread_id": "1"}},
)
```

**关于「一起接上」的说明**

给出的片段只明确了：Checkpointer 通过 `thread_id` 访问、Store 在节点或应用代码里读写 [7][8]，以及工具中可通过保留参数 `runtime`（ToolRuntime）访问 state、context、store [10]。但**片段里没有给出「同时编译 checkpointer 与 store 并一起传入」的具体 API 写法**，因此无法据片段给出二者联合接入的完整代码，这部分缺失。

**与用户说法可能不一致之处**

- 用户说「跨会话的长期数据」，片段中对应的组件名是 **Store**（不是 Checkpointer）；Checkpointer 是**线程内短期**记忆 [7][8]。
- 若用户想用「memory」一词统称：片段中短期记忆对应 checkpointer/state [12][14]，长期记忆对应 store [2][3][4][5]，二者是不同组件。

**top5 片段**：

片段[1] `oss__python__langchain__tools#008` ｜ Tools ｜ Access context

```text
| Component | Description | Use case | | --- | --- | --- | | State | Short-term memory - mutable data that exists for the current conversation (messages, counters, custom fields) | Access conversation history, track tool call counts | | Context | Immutable configuration passed at invocation time (user IDs, session info) | Personalize responses based on user identity | | Store | Long-term memory - persistent data that survives across conversations | Save user preferences, maintain knowledge base | | Stream Writer | Emit real-time updates during tool execution | Show progress for long-running operations |
```

片段[2] `oss__javascript__langgraph__add-memory#001` ｜ Memory ｜ ROOT

```text
- Add long-term memory to store user-specific or application-level data across sessions.
```

片段[3] `oss__python__langgraph__add-memory#001` ｜ Memory ｜ ROOT

```text
- Add long-term memory to store user-specific or application-level data across sessions.
```

片段[4] `oss__python__langgraph__persistence#002` ｜ Persistence ｜ ROOT

```text
- Stores persist application-defined data outside the graph state. Use them for long-term, cross-thread memory, including user preferences, facts, and shared knowledge.
```

片段[5] `oss__javascript__langgraph__persistence#002` ｜ Persistence ｜ ROOT

```text
- Stores persist application-defined data outside the graph state. Use them for long-term, cross-thread memory, including user preferences, facts, and shared knowledge.
```

---

## v2-F-017（multi-hop）

**问题**：子图默认的持久化行为是什么？如果希望同一个会话里多次调用累积状态，要开哪个开关、又会失去什么？

**gold**：按模式表，默认 per-invocation 是 checkpointer=None：每次调用都从头开始，但会继承父图的 checkpointer，以便在单次调用内支持中断和 durable execution。要让状态在同一线程的多次调用间累积，得把子图设成 per-thread（checkpointer=True），每次调用接着上次的进度；代价按特性对照表是不能用同一个子图多次调用。若设成 stateless（checkpointer=False）则完全没有检查点，中断和 durable execution 都没有。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

1. 子图默认是 **per-invocation（每次调用）** 持久化：`checkpointer=None`，每次调用都从头开始，但会继承父图的 checkpointer，以支持单次调用内的中断和持久执行 [5][6]。
2. 若希望同一会话（thread）里多次调用累积状态，要把子图的 `checkpointer` 设为 `True`，即 **per-thread** 模式，状态会跨调用累积，每次调用接着上次继续 [5][6][3][4]。
3. 代价是：per-thread 模式下**同一个子图实例在单个节点内被多次调用会冲突**（写入同一 checkpoint namespace），该场景不支持，应改用 per-invocation 持久化 [1][2][7]。

**模式对照（片段原文）**

| 模式 | `checkpointer=` | 行为 |
| --- | --- | --- |
| Per-invocation（默认） | `None` | 每次调用从头开始，继承父 checkpointer 以支持单次调用内的中断与持久执行 [5][6] |
| Per-thread | `True` | 状态在同一 thread 的多次调用间累积，每次接着上次继续 [5][6] |
| Stateless | `False` | 完全不 checkpoint，像普通函数调用，无中断、无持久执行 [5][6] |

能力差异：Multi-turn memory 仅 per-thread 为 ✅；Multiple calls (same subgraph) 在 per-thread 为 ❌，per-invocation 与 stateless 为 ✅ [7]。

**最小示例（Python，per-thread）**

```python
from langgraph.checkpoint.memory import MemorySaver

# 子图编译时开启 per-thread 持久化
subgraph = builder.compile(checkpointer=True)

# 父图侧仍需传入 checkpointer 与 thread 配置
graph = parent_builder.compile(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "thread-1"}}
graph.invoke(inputs, config)  # 同一 thread 内多次调用会累积子图状态
```

注意：片段中 per-invocation 的示例代码是 `create_agent(...)` 不设置 checkpointer（继承父级）[14]，与上表的 `checkpointer=None` 一致；若你的写法与片段中的参数名不一致，以片段为准。

**top5 片段**：

片段[1] `oss__javascript__langgraph__use-subgraphs#048` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
- Multiple calls (same subgraph) : The same subgraph instance can be invoked multiple times within a single node. With stateful persistence, these calls write to the same checkpoint namespace and conflict—use per-invocation persistence instead.
```

片段[2] `oss__python__langgraph__use-subgraphs#041` ｜ Subgraphs ｜ View example trace > Checkpointer reference

```text
- Multiple calls (same subgraph) : The same subgraph instance can be invoked multiple times within a single node. With stateful persistence, these calls write to the same checkpoint namespace and conflict—use per-invocation persistence instead.
```

片段[3] `oss__javascript__langgraph__use-subgraphs#046` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
- Multi-turn memory : The subgraph retains its state across multiple invocations within the same thread . Each call picks up where the last one left off rather than starting fresh.
```

片段[4] `oss__python__langgraph__use-subgraphs#039` ｜ Subgraphs ｜ View example trace > Checkpointer reference

```text
- Multi-turn memory : The subgraph retains its state across multiple invocations within the same thread . Each call picks up where the last one left off rather than starting fresh.
```

片段[5] `oss__javascript__langgraph__use-subgraphs#047` ｜ Subgraphs ｜ Subgraph persistence > Checkpointer reference

```text
- Multiple calls (different subgraphs) : Multiple different subgraph instances can be invoked within a single node without checkpoint namespace conflicts.
```

---

## v2-F-018（multi-hop）

**问题**：一个节点里连续问用户好几个问题，官方对异常捕获和调用顺序有什么硬性要求？为什么？

**gold**：两条规则：不能把 interrupt 包在裸 try/except Exception 里，否则会把中断异常一起吃掉，示例把这种写法标为 Bad；也不能用依赖非确定数据的循环反复调用，包括 while True 校验循环，因为每次执行的中断数量或顺序可能变化。正确做法是改用 conditional edge。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. **不要把 `interrupt` 调用包在 `try/except` 里。** 正确做法是先执行 `interrupt(...)`，再单独用 `try/except` 处理可能失败的业务逻辑（如 `fetch_data()`）[2]。
2. **同一个节点内，`interrupt` 调用的顺序必须每次都一致，不能重排。** 示例中依次 `interrupt("What's your name?")`、`interrupt("What's your age?")`、`interrupt("What's your city?")`，每次运行都保持同样顺序 [6]（JS 版本同样要求 [8]）。

**关于「为什么」：** 给出的文档片段只给出了这两条规则和正例代码，**没有解释原因**。片段里没有出现对「为什么不能包 try/except」「为什么不能重排」的说明文字，因此这部分无法根据现有片段回答。

**最小可用示例（Python，来自片段 [6]）：**

```python
def node_a(state: State):
    # ✅ Good: interrupt calls happen in the same order every time
    name = interrupt("What's your name?")
    age = interrupt("What's your age?")
    city = interrupt("What's your city?")

    return {
        "name": name,
        "age": age,
        "city": city
    }
```

**补充说明（与问题相关的其他片段）：** 片段 [3]/[4] 提到 human-in-the-loop 的 `"batched"`（默认）模式是「每个模型轮次一个 interrupt，列出所有需要审核的调用，按相同顺序用决策列表回答」——这是关于 interrupt 模式的信息，但并未涉及异常捕获或节点内调用顺序的硬性要求，不能用来回答「为什么」。

**缺失内容：** 片段中没有说明这两条规则的底层原因（例如恢复时如何按位置匹配 interrupt），也没有给出「连续问多个问题」场景下的专门指导。

**top5 片段**：

片段[1] `oss__python__langchain__multi-agent__handoffs-customer-support#043` ｜ Build customer support with handoffs ｜ Complete example

```text
record their response and move to the next step Be conversational and friendly. Don't ask multiple questions at once.""" ISSUE_CLASSIFIER_PROMPT = """You are a customer support agent helping with device issues. CURRENT STEP: Issue classification CUSTOMER INFO: Warranty status is {warranty_status} At this step, you need to: 1. Ask the customer to describe their issue 2. Determine if it's a hardware issue (physical damage, broken parts) or software issue (app crashes, performance) 3. Use record_issue_type to record the classification and move to the next step If unclear, ask clarifying questions before classifying."""
```

片段[2] `oss__python__langgraph__interrupts#055` ｜ Interrupts ｜ Rules of interrupts > Do not wrap interrupt calls in try/except

```text
```

def node_a(state: State):

    # ✅ Good: interrupting first, then handling

    # error conditions separately

    interrupt("What's your name?")

    try:

        fetch_data()  # This can fail

    except Exception as e:

        print(e)

    return state

```
```

片段[3] `oss__python__langchain__human-in-the-loop#006` ｜ Human-in-the-loop ｜ Set the interrupt mode

```text
- "batched" (default): One interrupt per model turn lists every call that needs review. You answer with a list of decisions in the same order.
```

片段[4] `oss__javascript__langchain__human-in-the-loop#006` ｜ Human-in-the-loop ｜ Set the interrupt mode

```text
- "batched" (default): One interrupt per model turn lists every call that needs review. You answer with a list of decisions in the same order.
```

片段[5] `oss__python__langchain__mcp__tools#015` ｜ Tools ｜ Server requests during tool execution > Elicitation

```text
= await adapter.list_tools() # Resuming a paused run needs persistence, so the interrupted run has # somewhere to wait. agent = create_agent("claude-sonnet-5", tools, checkpointer=InMemorySaver()) config: Any = {"configurable": {"thread_id": "booking-1"}} paused = await agent.ainvoke( {"messages": [{"role": "user", "content": "Book a table for 4."}]}, config ) [interrupt] = paused["__interrupt__"] [question] = interrupt.value["requests"] # Answers are keyed by the server's own request key, so nothing has to # be tracked across the pause. `decline` or `cancel` would refuse. answer = {"action": "accept", "content": {"date": "2026-09-14"}} return await agent.ainvoke(
```

---

## v2-F-019（multi-hop）

**问题**：想同时订阅节点更新和自定义事件，代码里怎么区分这两种 chunk？tasks 和 debug 模式又分别给什么、有什么前置条件？

**gold**：同时订阅时把 stream_mode 传成列表 ['updates', 'custom']，每个 chunk 看 type 字段分支：updates 的 data 是 {node_name: state}，custom 的 data 是自定义事件。按模式表，tasks 给 Task start/finish events with results and errors，且 Requires a checkpointer；debug 则把所有可用信息合起来，也就是 checkpoints 和 tasks 再加额外 metadata。

**judge 分**：0.5　**拒答标记**：None

**回答**：

结论：同时订阅 `updates` 和 `custom` 时，用 `version="v2"` 后每个 chunk 是带 `type` 字段的字典，通过 `chunk["type"]` 区分；`updates` 的 `chunk["data"]` 是「节点名 → 状态」的映射，`custom` 的 `chunk["data"]` 是自定义事件负载 [1][3][5]。注意：片段 [6] 展示的是另一种不带 `version="v2"` 的写法，此时 chunk 是 `(mode, chunk)` 元组，需要解包成 `for mode, chunk in ...`，与 v2 的字典形式不同，不要混用 [6]。

最小可用示例（v2 字典形式）：

```python
for chunk in graph.stream(
    {"topic": "ice cream"},
    stream_mode=["updates", "custom"],
    version="v2",
):
    if chunk["type"] == "updates":
        for node_name, state in chunk["data"].items():
            print(f"Node {node_name} updated: {state}")
    elif chunk["type"] == "custom":
        print(f"Status: {chunk['data']['status']}")
```

关于 `tasks` 和 `debug`：

- `tasks`：给出的片段只在 v2 输出格式的 `type` 枚举里列出了 `"tasks"`，说明它是可选的流模式之一，但没有片段说明 `tasks` 模式具体返回什么内容、有什么前置条件 [3]。因此这部分无法根据现有片段回答。
- `debug`：片段 [8] 给出了 `stream_mode="debug"` 的用法，chunk 的 `type` 为 `"debug"`，实际数据在 `chunk["data"]` 中 [8]。但片段没有说明 `debug` 模式具体包含哪些字段、以及是否需要额外前置条件（例如是否必须配合 `version="v2"` 之外的其他配置），这部分同样无法根据现有片段确认。

补充：v2 格式的 chunk 还包含 `ns`（命名空间元组，子图事件会填充），可用于判断事件是否来自子代理 [3][4][13]。

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Plan my vacation"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        is_subagent = any(segment.startswith("tools:") for segment in chunk["ns"])
        if is_subagent:
            tool_call_id = next(
                s.split(":")[1] for s in chunk["ns"] if s.startswith("tools:")
            )
            print(f"Subagent {tool_call_id}: {chunk['data']}")
        else:
            print(f"Main agent: {chunk['data']}")
```

缺失说明：现有片段没有解释 `tasks` 模式的数据结构，也没有说明 `debug` 模式的完整字段和前置条件，这两点需要查阅对应文档页面才能回答。

**top5 片段**：

片段[1] `oss__python__langgraph__streaming#048` ｜ Streaming ｜ View example trace > Multiple modes at once

```text
```

for chunk in graph.stream(inputs, stream_mode=["updates", "custom"], version="v2"):

    if chunk["type"] == "updates":

        for node_name, state in chunk["data"].items():

            print(f"Node `{node_name}` updated: {state}")

    elif chunk["type"] == "custom":

        print(f"Custom event: {chunk['data']}")

```
```

片段[2] `oss__python__langgraph__streaming#003` ｜ Streaming ｜ Get started > Basic usage

```text
de=["updates", "custom"], version="v2", ): if chunk["type"] == "updates": for node_name, state in chunk["data"].items(): print(f"Node {node_name} updated: {state}") elif chunk["type"] == "custom": print(f"Status: {chunk['data']['status']}") ```
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

片段[4] `oss__python__deepagents__streaming#009` ｜ Streaming ｜ Namespaces

```text
``` for chunk in agent.stream( {"messages": [{"role": "user", "content": "Plan my vacation"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Check if this event came from a subagent is_subagent = any( segment.startswith("tools:") for segment in chunk["ns"] ) if is_subagent: # Extract the tool call ID from the namespace tool_call_id = next( s.split(":")[1] for s in chunk["ns"] if s.startswith("tools:") ) print(f"Subagent {tool_call_id}: {chunk['data']}") else: print(f"Main agent: {chunk['data']}") ```
```

片段[5] `oss__python__langgraph__streaming#000` ｜ Streaming ｜ Get started > Basic usage

```text
```

for chunk in graph.stream(

    {"topic": "ice cream"},

    stream_mode=["updates", "custom"],

    version="v2",

):

    if chunk["type"] == "updates":

        for node_name, state in chunk["data"].items():

            print(f"Node {node_name} updated: {state}")

    elif chunk["type"] == "custom":

        print(f"Status: {chunk['data']['status']}")

```
```

---

## v2-F-020（multi-hop）

**问题**：默认的审批模式和逐调用模式在暂停时机上差在哪？默认模式最容易出什么错？

**gold**：按选择中断模式的表，batched 是默认：等模型回复完、任何工具执行之前暂停，整轮只有一个中断，没被门控的调用也要等审核，答案是按位置匹配的决策列表。per-call 则在每个被门控的工具调用开始时暂停，每个调用一个中断，未门控的调用立刻执行，答案按 interrupt ID 键控。默认模式的问题在对照表里：决策按位置匹配，审核人想批准 write_file、拒绝 execute_sql，却发成 [reject, approve]，结果 DELETE 真的跑了；两个调用只给一个决策还会抛 ValueError: Number of human decisions (1) does not match number of hanging tool calls (2)。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

1. 默认模式是 **batched（批处理）**，每个模型回合只暂停一次，覆盖该回合内所有需要审核的工具调用 [1][2][7][8]。
2. 暂停时机差异：
   - **Per-call（逐调用）**：每个受门控的工具调用**开始时**就暂停 [5][6]。
   - **Batched（默认）**：**模型响应之后、任何工具运行之前**暂停 [5][6]。
3. 默认模式最容易出的错：**决策按位置匹配调用**。审核者想批准 `write_file`、拒绝 `execute_sql`，却按 `[reject, approve]` 顺序提交，拒绝就会落到 `write_file` 上 [3][4]。另外，若两个调用只给一个决策，会报错（JS 为 `Error: Number of human decisions (1) does not match number of hanging tool calls (2)` [3][13]；Python 为 `ValueError: ...` [4]），且该错误答案会被先保存，修正后仍报同样错误，线程卡住 [13]。

**最小可用示例（batched 模式提交决策，按调用顺序排列）**

```javascript
new Command({
  resume: {
    decisions: [
      { type: "approve" },
      { type: "reject", message: "Archive the rows before deleting them." },
    ],
  },
});
```
[14]

**与用户说法可能不一致之处**：片段中默认模式名为 `"batched"`（默认值），逐调用模式名为 `"per-call"` [5][6][7][8]；若你所说的“逐调用模式”指其他名称，请以片段为准。

**top5 片段**：

片段[1] `oss__javascript__concepts__human-in-the-loop#001` ｜ Human-in-the-loop overview ｜ ROOT

```text
- Batched : One pause per model turn, covering every tool call in that turn. Batched mode is the current default.
```

片段[2] `oss__python__concepts__human-in-the-loop#001` ｜ Human-in-the-loop overview ｜ ROOT

```text
- Batched : One pause per model turn, covering every tool call in that turn. Batched mode is the current default.
```

片段[3] `oss__javascript__concepts__human-in-the-loop#011` ｜ Human-in-the-loop overview ｜ Compare batched-mode problems

```text
| In batched mode | What happens | In per-call mode | | --- | --- | --- | | Decisions match calls by position | A reviewer means to approve write_file and reject execute_sql , but sends [reject, approve] . The rejection goes to write_file . | Each decision is keyed by its call’s interrupt ID. | | Allowed decisions live in reviewConfigs | Clients pair two lists by position and hardcode a button for each decision type. | Each interrupt’s response_schema lists its decisions and edit arguments. | | An answer is saved before it is checked | One decision for two calls throws Error: Number of human decisions (1) does not match number of hanging tool calls (2).
```

片段[4] `oss__python__concepts__human-in-the-loop#011` ｜ Human-in-the-loop overview ｜ Compare batched-mode problems

```text
| In batched mode | What happens | In per-call mode | | --- | --- | --- | | Decisions match calls by position | A reviewer means to approve write_file and reject execute_sql , but sends [reject, approve] . The DELETE runs. | Each decision is keyed by its call’s interrupt ID. | | Allowed decisions live in review_configs | Clients pair two lists by position and hardcode a button for each decision type. | Each interrupt’s response_schema lists its decisions and edit arguments. | | An answer is saved before it is checked | One decision for two calls raises ValueError: Number of human decisions (1) does not match number of hanging tool calls (2).
```

片段[5] `oss__python__concepts__human-in-the-loop#013` ｜ Human-in-the-loop overview ｜ Choose an interrupt mode

```text
|  | Per-call | Batched (default) |

| --- | --- | --- |

| When it pauses | As each gated tool call starts | After the model responds, before any tool runs |

| Interrupts per turn | One per gated tool call | One for the whole turn |

| Ungated calls in the turn | Run right away | Wait for the review |

| Answer | One decision per interrupt, keyed by interrupt ID | A list of decisions, matched by position |

| Best for | New agents, one approval card or message per call, forms built from the schema | Approval UIs that already read action_requests |
```

---

## v2-F-021（multi-hop）

**问题**：用 set_node_defaults 给整张图配默认重试、超时和错误处理时，哪些默认项不会应用到错误处理器节点上，为什么？

**gold**：示例用 set_node_defaults 一次设了 retry_policy、error_handler 和 timeout。按适用性矩阵，retry_policy 和 timeout 对普通节点和错误处理器节点都生效：处理器遇到瞬时失败也该重试，卡住的处理器也该像普通节点一样被取消；但 error_handler 不应用到处理器节点，理由是 handlers must never catch themselves；cache_policy 同样不应用，因为缓存处理器结果不安全。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 `set_node_defaults` 的四个默认项中，**`error_handler` 和 `cache_policy` 不会应用到错误处理器节点上**；`retry_policy` 和 `timeout` 会应用到错误处理器节点上 [1]。

原因（按片段给出的理由）：
- `error_handler` 不应用：错误处理器绝不能捕获自己（Handlers must never catch themselves）[1]。
- `cache_policy` 不应用：缓存错误处理器的结果是不安全的（Caching handler results is unsafe）[1]。
- `retry_policy` 应用：错误处理器在瞬时失败时也应被重试 [1]。
- `timeout` 应用：卡住的错误处理器应像卡住的普通节点一样被取消 [1]。

补充说明：
- 片段中 JavaScript 版本的对应参数名为 `retryPolicy`、`timeout`、`errorHandler`、`cachePolicy`，适用矩阵与 Python 版一致 [6]。若你使用的是 JS 版，请以 `setNodeDefaults` 及驼峰命名为准 [4][6]。
- 另外，`set_node_defaults` 不会被 subgraph 继承，每个图独立管理自己的默认值 [2]（JS 版为 `setNodeDefaults` 不被 subgraph 继承 [4]）。

最小可用示例（Python，展示默认项与节点级覆盖）：

```python
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
[5]

注意：片段 [5] 只演示了 `retry_policy` 的节点级覆盖写法；关于 `error_handler` 的节点级覆盖，片段 [3][7] 给出了示例（如 `add_node("step_b", step_b, error_handler=custom_error_handler)` [3]），但片段未展示 `timeout` 与 `cache_policy` 的节点级覆盖写法。

**top5 片段**：

片段[1] `oss__python__langgraph__fault-tolerance#037` ｜ Fault tolerance ｜ Graph defaults > Applicability matrix

```text
| set_node_defaults parameter | Applies to regular nodes | Applies to error-handler nodes | Reason |

| --- | --- | --- | --- |

| retry_policy | ✅ | ✅ | Handlers should be retried on transient failures |

| timeout | ✅ | ✅ | Stuck handlers should be cancelled like stuck regular nodes |

| error_handler | ✅ | ❌ | Handlers must never catch themselves |

| cache_policy | ✅ | ❌ | Caching handler results is unsafe |
```

片段[2] `oss__python__langgraph__fault-tolerance#044` ｜ Fault tolerance ｜ Limitations

```text
- set_node_defaults is not inherited by subgraphs : each graph manages its own defaults independently.
```

片段[3] `oss__python__langgraph__fault-tolerance#033` ｜ Fault tolerance ｜ Graph defaults > Precedence

```text
```

graph = (

    StateGraph(State)

    .set_node_defaults(error_handler=default_error_handler)

    .add_node("step_a", step_a)                                     # uses default_error_handler

    .add_node("step_b", step_b, error_handler=custom_error_handler) # uses custom_error_handler

    .add_edge(START, "step_a")

    .compile()

)

```
```

片段[4] `oss__javascript__langgraph__fault-tolerance#045` ｜ Fault tolerance ｜ Limitations

```text
- setNodeDefaults is not inherited by subgraphs : each graph manages its own defaults independently.
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

## v2-F-022（multi-hop）

**问题**：长期记忆应该在回复用户之前顺手写，还是放到后台任务里写？写的时候一般怎么组织命名空间和键？

**gold**：两种都行：既可以放在应用逻辑里、在回复用户前由 agent 决定记住哪些事实，也就是 on the hot path，也可以作为后台任务异步生成记忆，文档说两种做法的取舍在下一节展开。存储示例把 user_id 和 application_context 组成 namespace 元组，用 store.put(namespace, key, value) 写入，再用 store.get(namespace, key) 按 ID 取；示例还提醒生产环境要换 DB-backed store。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

1. 两种时机都支持：可以在 agent 的应用逻辑里“顺手写”（on the hot path，即在回复用户前决定记住事实），也可以作为后台任务异步生成记忆；文档说两种方式的权衡在后续章节解释，但给出的片段里没有展开具体权衡内容 [1][2]。
2. 命名空间和键的组织方式：片段中的示例用 `["memories", userId]` 作为 namespace，用 `uuid7()` 生成 key，值以 `{ data: memory }` 形式写入 [3][4][5]。Python 版示例中 namespace 来自 `config["configurable"]` 的 `user_id`（配置里同时有 `thread_id` 和 `user_id`）[4]。

**最小可用示例（JavaScript，摘自片段）**

```javascript
const userId = context?.userId;
const namespace = ["memories", userId];
const memories = await runtime.store?.search(namespace, {
  query: state.messages.at(-1)?.content,
});
const info = memories?.map(d => d.value.data).join("\n") || "";
const systemMsg = `You are a helpful assistant talking to the user. User info: ${info}`;

// Store new memories if the user asks the model to remember
const lastMessage = state.messages.at(-1);
if (lastMessage?.content?.toLowerCase().includes("remember")) {
  const memory = "User name is Bob";
  await runtime.store?.put(namespace, uuid7(), { data: memory });
}
```

**补充说明（以片段为准）**

- 片段中“顺手写”的触发条件是最后一条消息包含 “remember” 时写入 [3][4][5]；这只是示例逻辑，片段未说明这是唯一推荐做法。
- 长期记忆存放在 Store 中（跨线程、应用自定义键值数据），短期记忆由 Checkpointer 按 thread 保存 [6][7]。
- 片段 [9] 只给出记忆类型分类（Semantic/Episodic/Procedural），未涉及命名空间组织。
- 关于“两种时机如何权衡”，给出的文档里没有找到能回答这个问题的内容，缺少 [1][2] 中提到的 “the section below” 的具体权衡说明。

**top5 片段**：

片段[1] `oss__javascript__concepts__memory#003` ｜ Memory overview ｜ Long-term memory

```text
- When do you want to update memories? Memory can be updated as part of an agent’s application logic (e.g., “on the hot path”). In this case, the agent typically decides to remember facts before responding to a user. Alternatively, memory can be updated as a background task (logic that runs in the background / asynchronously and generates memories). We explain the tradeoffs between these approaches in the section below .
```

片段[2] `oss__python__concepts__memory#003` ｜ Memory overview ｜ Long-term memory

```text
- When do you want to update memories? Memory can be updated as part of an agent’s application logic (e.g., “on the hot path”). In this case, the agent typically decides to remember facts before responding to a user. Alternatively, memory can be updated as a background task (logic that runs in the background / asynchronously and generates memories). We explain the tradeoffs between these approaches in the section below .
```

片段[3] `oss__javascript__langgraph__add-memory#019` ｜ Memory ｜ Add long-term memory > Use in production

```text
ontext?.userId; const namespace = ["memories", userId]; const memories = await runtime.store?.search(namespace, { query: state.messages.at(-1)?.content }); const info = memories?.map(d => d.value.data).join("\n") || ""; const systemMsg = `You are a helpful assistant talking to the user. User info: ${info}`; // Store new memories if the user asks the model to remember const lastMessage = state.messages.at(-1); if (lastMessage?.content?.toLowerCase().includes("remember")) { const memory = "User name is Bob"; await runtime.store?.put(namespace, uuid7(), { data: memory }); } const response = await model.invoke([ { role: "system", content: systemMsg }, ...state.messages ]); return { messages:
```

片段[4] `oss__python__langgraph__add-memory#060` ｜ Memory ｜ Add long-term memory > Use in production

```text
a helpful assistant talking to the user. User info: {info}" # Store new memories if the user asks the model to remember last_message = state["messages"][-1] if "remember" in last_message.content.lower(): memory = "User name is Bob" await store.aput(namespace, str(uuid7()), {"data": memory}) response = await model.ainvoke( [{"role": "system", "content": system_msg}] + state["messages"] ) return {"messages": response} builder = StateGraph(MessagesState) builder.add_node(call_model) builder.add_edge(START, "call_model") graph = builder.compile( checkpointer=checkpointer, store=store, ) config = { "configurable": { "thread_id": "1", "user_id": "1", } } stream = await graph.astream_events(
```

片段[5] `oss__javascript__langgraph__add-memory#023` ｜ Memory ｜ Add long-term memory > Use in production

```text
st memories = await runtime.store?.search(namespace); const info = memories?.map(d => d.value.data).join("\n") || "n/a"; const systemMsg = `You are a helpful assistant talking to the user. User info: ${info}`; // Store new memories if the user asks the model to remember const lastMessage = state.messages.at(-1); if (lastMessage?.content?.toLowerCase().includes("remember")) { const memory = "User name is Bob"; await runtime.store?.put(namespace, uuid7(), { data: memory }); } const response = await model.invoke([ { role: "system", content: systemMsg }, ...state.messages ]); return { messages: [response] }; }; const MONGODB_URI = "mongodb://user:password@localhost:27017";
```

---
