# 审计材料 8/8（30 条，明细文件第 211–240 行）

## v2-H-027（no-answer）

**问题**：LlamaIndex 的 SentenceWindowNodeParser 里，window_size 默认是多少？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

所有片段都来自 LangChain / LangGraph / deepagents 的文档（存储、嵌入、沙箱后端等），没有任何片段涉及 LlamaIndex 的 `SentenceWindowNodeParser` 或它的 `window_size` 参数默认值。缺少 LlamaIndex 相关文档片段，因此无法回答。

**top5 片段**：

片段[1] `oss__javascript__langgraph__stores#020` ｜ Stores ｜ Using in LangGraph

```text
```

{

    ...

    "store": {

        "index": {

            "embed": "openai:text-embeddings-3-small",

            "dims": 1536,

            "fields": ["$"]

        }

    }

}

```
```

片段[2] `oss__python__langgraph__stores#020` ｜ Stores ｜ Using in LangGraph

```text
```

{

    ...

    "store": {

        "index": {

            "embed": "openai:text-embeddings-3-small",

            "dims": 1536,

            "fields": ["$"]

        }

    }

}

```
```

片段[3] `oss__javascript__deepagents__sandboxes#017` ｜ Sandboxes ｜ Lifecycle and scoping > Thread-scoped (default)

```text
TtlSeconds: 3600, // TTL: clean up when idle })); return createDeepAgent({ model: "ollama:north-mini-code-1.0", backend: new LangSmithSandbox({ sandbox: lsSandbox }), }); } ```
```

片段[4] `oss__python__langgraph__stores#011` ｜ Stores ｜ Semantic search

```text
```

from langchain.embeddings import init_embeddings



store = InMemoryStore(

    index={

        "embed": init_embeddings("openai:text-embedding-3-small"),  # Embedding provider

        "dims": 1536,                              # Embedding dimensions

        "fields": ["food_preference", "$"]              # Fields to embed

    }

)

```
```

片段[5] `oss__python__deepagents__backends#041` ｜ Backends ｜ Built-in backends > LocalShellBackend (local shell)

```text
- Supports timeout (default 120s), max_output_bytes (default 100,000), env , and inherit_env for environment variables.
```

---

## v2-H-028（no-answer）

**问题**：openwiki 有没有 JetBrains IDE 插件，能在编辑器里直接搜 wiki？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺少：文档片段中没有任何关于 JetBrains IDE 插件（或 IDE 集成）的说明。片段里提到的集成方式只有：

- CLI 命令（如 `openwiki`、`openwiki code`、`openwiki personal`、`openwiki visualize`、`openwiki link`、`openwiki workspace` 等）[3][4][11]
- 通过 MCP 搜索 OpenWiki 页面（`openwiki_read` 等工具）[2][6]
- 编码代理集成安装命令，如 `openwiki integrations install codex` / `omp` / `antigravity` [11]

其中并未出现 JetBrains 相关插件或“在编辑器内直接搜索 wiki”的功能描述，因此无法确认是否存在该插件。

**top5 片段**：

片段[1] `oss__openwiki__quickstart#000` ｜ Quickstart ｜ ROOT

```text
Quickstart Install OpenWiki, configure a model provider, and generate your first wiki.
```

片段[2] `oss__openwiki__search-and-link#000` ｜ Search and link wikis ｜ ROOT

```text
Search and link wikis Search OpenWiki pages over MCP and group related repository wikis into workspaces
```

片段[3] `oss__openwiki__cli-reference#000` ｜ Command reference ｜ Core commands

```text
``` # Interactive chat in code mode (current repository) openwiki openwiki "Please generate documentation for this repository" # Personal mode openwiki personal openwiki personal --init openwiki personal --update # Explicit code mode openwiki code --init openwiki code --update openwiki code --update --print # Defaults to code mode and specify a language openwiki --init openwiki --update openwiki --init --language ko # One-shot print mode openwiki -p "Summarize what you can do" # Explore the wiki locally or export a static visualizer openwiki visualize openwiki visualize openwiki --port 4400 --no-open openwiki visualize openwiki --export docs/openwiki-visualizer
```

片段[4] `oss__openwiki__overview#000` ｜ OpenWiki ｜ Modes

```text
| Mode | Command | Output | Use when |

| --- | --- | --- | --- |

| Code (default) | openwiki / openwiki code | openwiki/ in the current repository | You want repository context and documentation for coding agents |

| Personal | openwiki personal | ~/.openwiki/wiki | You want a local personal brain from configured sources |
```

片段[5] `oss__openwiki__code-mode#002` ｜ Code mode ｜ What code mode produces

```text
- openwiki/ : Generated Markdown wiki (quickstart, architecture, operations, and related topics)
```

---

## v2-I-001（single-hop）

**问题**：想让 StoreBackend 的存储按用户隔离，namespace 工厂里应该取 runtime 上的哪个身份字段？

**gold**：取 rt.server_info.user.identity，写成 namespace=lambda rt: (rt.server_info.user.identity,)，这样每个用户各自一份隔离存储。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：按用户隔离时，Python 版应取 `rt.server_info.user.identity`，把它作为 namespace 元组的一项 [1][3][7][8]。JavaScript 版对应取 `rt.serverInfo.user.identity`（或从 `config.configurable.langgraph_auth_user_id` 派生）[4][5][6]。

注意差异：旧写法 `ctx.runtime.context.user_id` 已废弃，v0.7 移除，应改为 `rt.server_info.user.identity` [1]。

最小可用示例（Python）：

```python
from deepagents.backends import StoreBackend

backend = StoreBackend(
    namespace=lambda rt: (rt.server_info.user.identity,),
)
```

[3]

如果同一部署里有多个 agent、还想按助手再区分，可把 `assistant_id` 也放进 namespace [2]：

```python
StoreBackend(
    namespace=lambda rt: (
        rt.server_info.assistant_id,
        rt.server_info.user.identity,
    ),
)
```

[2]

**top5 片段**：

片段[1] `oss__python__deepagents__backends#103` ｜ Backends ｜ Migrate from backend factories > Migrating from BackendContext

```text
```

# Before (deprecated, removed in v0.7)

StoreBackend(

    namespace=lambda ctx: (ctx.runtime.context.user_id,),

)



# After

StoreBackend(

    namespace=lambda rt: (rt.server_info.user.identity,),

)

```
```

片段[2] `oss__python__deepagents__memory#038` ｜ Memory ｜ Advanced usage > Multiple agents in the same deployment

```text
```

StoreBackend(

    namespace=lambda rt: (

        rt.server_info.assistant_id,

        rt.server_info.user.identity,

    ),

)

```
```

片段[3] `oss__python__deepagents__backends#057` ｜ Backends ｜ Built-in backends > StoreBackend (LangGraph store) > Namespace factories

```text
```

from deepagents.backends import StoreBackend



# Per-user: each user gets their own isolated storage

backend = StoreBackend(

    namespace=lambda rt: (rt.server_info.user.identity,),

)



# Per-assistant: all users of the same assistant share storage

backend = StoreBackend(

    namespace=lambda rt: (

        rt.server_info.assistant_id,

    ),

)



# Per-thread: storage scoped to a single conversation

backend = StoreBackend(

    namespace=lambda rt: (

        rt.execution_info.thread_id,

    ),

)

```
```

片段[4] `oss__javascript__deepagents__backends#049` ｜ Backends ｜ Built-in backends > StoreBackend (LangGraph store) > Namespace factories

```text
```

import { StoreBackend } from "deepagents";



// Per-user: derive from the authenticated Agent Server user

const perUserBackend = new StoreBackend({

  namespace: ({ config }) => [String(config?.configurable?.langgraph_auth_user_id)],

});



// Per-assistant: use the resolved assistant id

const perAssistantBackend = new StoreBackend({

  namespace: ({ assistantId }) => [assistantId ?? "default"],

});



// Static namespace when the scope is known at construction time

const orgId = "acme";

const userId = "user-1";

const staticBackend = new StoreBackend({

  namespace: ["memories", orgId, userId, "filesystem"],

});

```
```

片段[5] `oss__javascript__deepagents__memory#045` ｜ Memory ｜ Advanced usage > Multiple agents in the same deployment

```text
```

new StoreBackend({

  namespace: (rt) => [

    rt.serverInfo.assistantId,

    rt.serverInfo.user.identity,

  ],

})

```
```

---

## v2-I-002（single-hop）

**问题**：SKILL.md frontmatter 里的 name 字段有哪些硬性约束？description 有长度上限吗？

**gold**：name 必填，只能是小写字母、数字和连字符，长度 1-64 个字符，且必须与父目录名一致；description 也必填，上限 1,024 个字符。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- `name` 是必填字段，硬性约束为：小写字母数字加连字符（lowercase alphanumeric with hyphens），长度 1–64 个字符，且必须与父目录名一致 [5][6]。
- `description` 也是必填字段，长度上限为 1,024 个字符 [5][6]。
- 另外，启动时若技能缺失，文档建议校验 SKILL.md frontmatter，确认 `name` 与父目录名匹配并符合 Agent Skills 规范，可用 `skills-ref` 校验工具检查格式 [1][2]。

**最小可用示例（frontmatter 片段）：**

```yaml
---
name: langgraph-docs
description: Use this skill for requests related to LangGraph in order to fetch relevant documentation to provide accurate, up-to-date guidance.
---
```

（示例中 `name` 为小写加连字符，`description` 为一段说明文字，符合上述约束 [15]。）

**top5 片段**：

片段[1] `oss__python__deepagents__skills#125` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
3. Validate SKILL.md frontmatter . The name must match the parent directory name and follow the Agent Skills specification . Use the skills-ref validation tool to check formatting.
```

片段[2] `oss__javascript__deepagents__skills#125` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
2. Validate SKILL.md frontmatter . The name must match the parent directory name and follow the Agent Skills specification . Use the skills-ref validation tool to check formatting.
```

片段[3] `oss__javascript__deepagents__skills#006` ｜ Skills ｜ How skills work

```text
| Level | What loads | When |

| --- | --- | --- |

| 1. Metadata | name and description from SKILL.md frontmatter | Agent startup, for every configured skill |

| 2. Instructions | Full SKILL.md body | When the skill is invoked |

| 3. Resources | Supporting files under scripts/ , references/ , and assets/ | As needed after invocation, when the instructions reference them |
```

片段[4] `oss__python__deepagents__skills#006` ｜ Skills ｜ How skills work

```text
| Level | What loads | When |

| --- | --- | --- |

| 1. Metadata | name and description from SKILL.md frontmatter | Agent startup, for every configured skill |

| 2. Instructions | Full SKILL.md body | When the skill is invoked |

| 3. Resources | Supporting files under scripts/ , references/ , and assets/ | As needed after invocation, when the instructions reference them |
```

片段[5] `oss__javascript__deepagents__skills#007` ｜ Skills ｜ How skills work

```text
1. Discovery (level 1): At agent start, the middleware scans the configured skill paths, parses each SKILL.md frontmatter , and injects the name and description fields into the system prompt.
```

---

## v2-I-003（single-hop）

**问题**：agent 记住新学到的信息时，用什么工具写回记忆文件？写入可以发生在什么时机？

**gold**：用内置的 edit_file 工具更新记忆文件；更新可在对话进行中完成（这是默认方式），也可在对话之间通过 background consolidation 完成，改完下次对话即可用。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

Agent 使用内置的 **`edit_file`** 工具来更新记忆文件 [1][2]。

写入时机有两种 [1][2]：
- **对话过程中**（默认方式）
- **对话之间的后台整理**（background consolidation）

更新会被持久化，并在下一次对话中可用 [1][2]。

另外需要注意：并非所有记忆都可写——开发者定义的 skills 和组织策略通常是**只读**的 [1][2]。

## 最小可用示例

文档片段中没有直接给出「agent 调用 `edit_file` 写记忆」的完整代码，但 [5]/[7] 展示了在 `create_deep_agent` 中通过 `interrupt_on` 对 `edit_file` 设置人工审批的用法，可佐证 `edit_file` 是写文件工具：

```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()
agent = create_deep_agent(
    model="google_genai:gemini-4-hydrogen",
    backend=FilesystemBackend(root_dir="/Users/user/{project}"),
    memory=["./AGENTS.md"],
    interrupt_on={
        "write_file": True,  # Default: approve, edit, reject
        "read_file": False,  # No interrupts needed
        "edit_file": True,   # Default: approve, edit, reject
    },
    checkpointer=checkpointer,  # Required!
)
```

## 与用户说法的差异提示

片段中同时出现了 `write_file` 和 `edit_file` 两个工具名 [5][7]。就「更新记忆文件」这一动作，[1][2] 明确写的是 **`edit_file`**；`write_file` 仅出现在 `interrupt_on` 配置示例里，片段未说明它用于记忆写回。

**top5 片段**：

片段[1] `oss__python__deepagents__memory#003` ｜ Memory ｜ How memory works

```text
3. Agent updates memory (optional). When the agent learns new information, it can use its built-in edit_file tool to update memory files. Updates can happen during the conversation (the default) or in the background between conversations via background consolidation . Changes are persisted and available in the next conversation. Not all memory is writable: developer-defined skills and organization policies are typically read-only. See read-only vs writable memory for details.
```

片段[2] `oss__javascript__deepagents__memory#003` ｜ Memory ｜ How memory works

```text
3. Agent updates memory (optional). When the agent learns new information, it can use its built-in edit_file tool to update memory files. Updates can happen during the conversation (the default) or in the background between conversations via background consolidation . Changes are persisted and available in the next conversation. Not all memory is writable: developer-defined skills and organization policies are typically read-only. See read-only vs writable memory for details.
```

片段[3] `oss__javascript__deepagents__memory#006` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
e: langgraph-docs description: Fetch relevant LangGraph documentation to provide accurate guidance. --- # langgraph-docs Use the fetch_url tool to read https://docs.langchain.com/llms.txt, then fetch relevant pages. `), ); const agent = createDeepAgent({ memory: ["/memories/AGENTS.md"], skills: ["/skills/"], backend: (rt) => new CompositeBackend( new StateBackend(rt), { "/memories/": new StoreBackend(rt, { namespace: (rt) => ["my-agent"], }), "/skills/": new StoreBackend(rt, { namespace: (rt) => ["my-agent"], }), }, ), store, }); // Thread 1: the agent learns a new preference and saves it to memory const config1 = { configurable: { thread_id: uuid7() } }; await agent.invoke({ messages:
```

片段[4] `oss__python__deepagents__memory#007` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
da rt: ("my-agent",) ), "/skills/": StoreBackend( namespace=lambda rt: ("my-agent",) ), }, ), store=store, ) # Thread 1: the agent learns a new preference and saves it to memory config1 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "I prefer detailed explanations. Remember that."}]}, config=config1, ) # Thread 2: the agent reads memory and applies the preference config2 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "Explain how transformers work."}]}, config=config2, ) ```
```

片段[5] `oss__python__deepagents__memory#006` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
a skill store.put( ("my-agent",), "/langgraph-docs/SKILL.md", create_file_data("""--- name: langgraph-docs description: Fetch relevant LangGraph documentation to provide accurate guidance. --- # langgraph-docs Use the fetch_url tool to read https://docs.langchain.com/llms.txt, then fetch relevant pages. """), ) agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", memory=["/memories/AGENTS.md"], skills=["/skills/"], backend=CompositeBackend( default=StateBackend(), routes={ "/memories/": StoreBackend( namespace=lambda rt: ("my-agent",) ), "/skills/": StoreBackend( namespace=lambda rt: ("my-agent",) ), }, ), store=store, ) # Thread 1:
```

---

## v2-I-004（single-hop）

**问题**：deep agents 的人工审批有哪四种 decision？approve、edit、reject、respond 分别做什么？

**gold**：approve 按 agent 原参数执行；edit 先改参数再执行；reject 跳过这次工具调用并把拒绝反馈回给 agent；respond 把人的回复直接当成合成工具结果、跳过执行。

**judge 分**：0.0　**拒答标记**：None

**回答**：

## 结论

**四种 decision 的名称**：文档片段中确实出现了 `approve`、`edit`、`reject`、`respond` 这四个词，作为 `interrupt_on` 中 `True` 的默认允许决策集合 [1][2][4][5][6][7][8][9][10][11]。

**但各 decision 的具体行为，给出的文档里没有找到能回答这个问题的内容。** 片段中只有代码注释 `# Default: approve, edit, reject, respond`，没有对 approve / edit / reject / respond 各自语义的说明。缺的是：每个 decision 触发后系统具体做什么（例如 approve 是否直接执行工具、edit 是否允许修改参数、reject 是否跳过、respond 是否把人工输入回传给模型）的官方描述。

## 片段中能确认的相关信息

- `interrupt_on` 中某工具设为 `True` 时，默认允许的决策为 approve、edit、reject、respond [1][9]。
- 某工具设为 `False` 时不触发中断（`# No interrupts needed`）[1][2]。
- 也可以用对象形式限制允许的决策，例如 `{"allowed_decisions": ["approve", "reject"]}`，注释说明此时不支持编辑（`# No editing`）[1][2][4]。
- 使用 human-in-the-loop 时 `checkpointer` 是必需的（`# Required!`）[1][9]。
- JavaScript 版本使用驼峰命名 `interruptOn` 和 `allowedDecisions`，与 Python 的 `interrupt_on` / `allowed_decisions` 写法不同 [3]。

## 最小可用示例（Python，来自片段）

```python
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

@tool
def remove_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"

@tool
def fetch_file(path: str) -> str:
    """Read a file from the filesystem."""
    return f"Contents of {path}"

@tool
def notify_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    return f"Sent email to {to}"

# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()

agent = create_deep_agent(
    model="openai:gpt-6.1-sol",
    tools=[remove_file, fetch_file, notify_email],
    interrupt_on={
        "remove_file": True,   # Default: approve, edit, reject, respond
        "fetch_file": False,   # No interrupts needed
        "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing
    },
    checkpointer=checkpointer,  # Required!
)
```

[9][1]

## 与用户说法的差异提示

用户问的是「四种 decision 分别做什么」，片段只提供了名称和默认组合，未提供行为定义；因此无法据片段逐一解释这四个 decision 的作用，需查阅该页面对 Human-in-the-loop 决策语义的正文说明。

**top5 片段**：

片段[1] `oss__python__deepagents__customization#153` ｜ Customize Deep Agents ｜ Human-in-the-loop

```text
genai:gemini-4-hydrogen", tools=[remove_file, fetch_file, notify_email], interrupt_on={ "remove_file": True,  # Default: approve, edit, reject, respond "fetch_file": False,  # No interrupts needed "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing }, checkpointer=checkpointer,  # Required! ) ```
```

片段[2] `oss__python__deepagents__customization#155` ｜ Customize Deep Agents ｜ Human-in-the-loop

```text
del="openai:gpt-6.1-sol", tools=[remove_file, fetch_file, notify_email], interrupt_on={ "remove_file": True,  # Default: approve, edit, reject, respond "fetch_file": False,  # No interrupts needed "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing }, checkpointer=checkpointer,  # Required! ) ```
```

片段[3] `oss__javascript__deepagents__acp#021` ｜ Agent Client Protocol (ACP) ｜ Customization > Human-in-the-loop

```text
```

import { DeepAgentsServer } from "deepagents-acp";



const server = new DeepAgentsServer({

  agents: {

    name: "careful-agent",

    interruptOn: {

      execute: { allowedDecisions: ["approve", "edit", "reject"] },

      write_file: true,

    },

  },

});

```
```

片段[4] `oss__python__deepagents__customization#157` ｜ Customize Deep Agents ｜ Human-in-the-loop

```text
thropic:claude-sonnet-5", tools=[remove_file, fetch_file, notify_email], interrupt_on={ "remove_file": True,  # Default: approve, edit, reject, respond "fetch_file": False,  # No interrupts needed "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing }, checkpointer=checkpointer,  # Required! ) ```
```

片段[5] `oss__python__deepagents__customization#165` ｜ Customize Deep Agents ｜ Human-in-the-loop

```text
ama:north-mini-code-1.0", tools=[remove_file, fetch_file, notify_email], interrupt_on={ "remove_file": True,  # Default: approve, edit, reject, respond "fetch_file": False,  # No interrupts needed "notify_email": {"allowed_decisions": ["approve", "reject"]},  # No editing }, checkpointer=checkpointer,  # Required! ) ```
```

---

## v2-I-005（single-hop）

**问题**：provider 整体宕机、agent 陷入失控循环、以及意料之外的异常，官方分别建议怎么处理？

**gold**：provider outage 用 ModelFallbackMiddleware 回退到备用模型；失控循环用 ModelCallLimitMiddleware 和 ToolCallLimitMiddleware 限制每次运行的模型与工具调用数；意外错误不要吞掉，让它向上抛出。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

- **Provider 整体宕机（Provider outage）**：属于系统自动处理的错误，策略是**回退到备用模型**，使用 `modelFallbackMiddleware` [2][9]。
- **Agent 陷入失控循环（Excessive calls / runaway loops）**：属于系统自动处理的错误，策略是**限制每次运行的模型调用和工具调用次数**，使用 `ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` [2]。
- **意料之外的异常（Unexpected errors）**：由开发者处理，策略是**让异常向上冒泡（bubble up）**，不使用中间件，直接让异常传播 [2]。

**最小可用示例**

文档片段中只给出了重试类中间件（`modelRetryMiddleware` / `ModelRetryMiddleware`、`toolRetryMiddleware` / `ToolRetryMiddleware`）的示例代码 [8][10]，**没有给出** `modelFallbackMiddleware`、`ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` 的示例代码，因此这里无法提供这三者的可用示例。

可参考的重试中间件示例（Python，来自片段 [10]）：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware, ToolRetryMiddleware

agent = create_agent(
    model="google_genai:gemini-4-hydrogen",
    tools=[search_tool, fetch_url_tool],
    middleware=[
        ModelRetryMiddleware(max_retries=3, backoff_factor=2.0, initial_delay=1.0),
        ToolRetryMiddleware(
            max_retries=2,
            tools=["search", "fetch_url"],
            retry_on=(TimeoutError, ConnectionError),
        ),
    ],
)
```

**需要指出的差异 / 缺口**

- 片段 [2]（Python）与 [1]（JavaScript）在“用户可修复错误”一行上内容不同：[2] 有 `interrupt()` + Human-in-the-loop 一行，[1] 该行缺失；但两者对“Provider outage / Excessive calls / Unexpected errors”的处理建议一致。
- 关于 `modelFallbackMiddleware`、`ModelCallLimitMiddleware`、`ToolCallLimitMiddleware` 的具体参数与用法，给出的文档里没有找到能回答的内容，缺少对应的 API 说明和示例。

**top5 片段**：

片段[1] `oss__javascript__deepagents__fault-tolerance#002` ｜ Fault tolerance ｜ Error handling strategies

```text
man-in-the-loop | | Provider outage | System (automatic) | Fall back to an alternative model | modelFallbackMiddleware | | Excessive calls (runaway loops) | System (automatic) | Cap model and tool calls per run | ModelCallLimitMiddleware , ToolCallLimitMiddleware | | Unexpected errors | Developer | Let them bubble up | No middleware; let the exception propagate |
```

片段[2] `oss__python__deepagents__fault-tolerance#002` ｜ Fault tolerance ｜ Error handling strategies

```text
| User-fixable errors (missing information, unclear instructions) | Human | Pause with interrupt() | Human-in-the-loop | | Provider outage | System (automatic) | Fall back to an alternative model | ModelFallbackMiddleware | | Excessive calls (runaway loops) | System (automatic) | Cap model and tool calls per run | ModelCallLimitMiddleware , ToolCallLimitMiddleware | | Unexpected errors | Developer | Let them bubble up | No middleware; let the exception propagate |
```

片段[3] `oss__javascript__langchain__middleware__built-in#013` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model retry

```text
- 'continue' (default) - Return an AIMessage with error details, allowing the agent to potentially handle the failure gracefully
```

片段[4] `oss__python__langchain__middleware__built-in#013` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model retry

```text
- 'continue' (default) - Return an AIMessage with error details, allowing the agent to potentially handle the failure gracefully
```

片段[5] `oss__javascript__deepagents__fault-tolerance#001` ｜ Fault tolerance ｜ Error handling strategies

```text
| Error type | Who fixes it | Strategy | Middleware or feature | | --- | --- | --- | --- | | Transient errors (network issues, rate limits) | System (automatic) | Retry with exponential backoff | modelRetryMiddleware , toolRetryMiddleware | | Model refusals | System or developer | Fall back to another model, then catch the error | modelFallbackMiddleware , modelRefusalMiddleware | | User-fixable errors (missing information, unclear instructions) | Human | Pause with interrupt() | Human-in-the-loop | | Provider outage | System (automatic) | Fall back to an alternative model | modelFallbackMiddleware |
```

---

## v2-I-006（single-hop）

**问题**：给模型加本地限流时，InMemoryRateLimiter 的三个参数分别控制什么？文档示例给的值是多少？

**gold**：requests_per_second=0.1 表示每 10 秒放行一次请求；check_every_n_seconds=0.1 表示每 100ms 检查一次是否允许发请求；max_bucket_size=10 控制最大突发量。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** `InMemoryRateLimiter` 的三个参数含义与示例值如下（Python 版）[1][2]：

- `requests_per_second`：每秒允许的请求数，示例值 `0.1`，即每 10 秒 1 个请求 [1][2]。
- `check_every_n_seconds`：每隔多久检查一次当前是否允许发起请求，示例值 `0.1`，即每 100ms 检查一次 [1][2]。
- `max_bucket_size`：控制最大突发（burst）大小，示例值 `10` [1][2]。

**最小可用示例：**

```python
from langchain.rate_limiters import InMemoryRateLimiter
from langchain.chat_models import init_chat_model

rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.1,       # 1 request every 10s
    check_every_n_seconds=0.1,     # Check every 100ms whether allowed to make a request
    max_bucket_size=10,            # Controls the maximum burst size
)

model = init_chat_model(
    model="google_genai:gemini-4-hydrogen",
    rate_limiter=rate_limiter,
)
```

**补充说明（与用户说法可能不一致之处）：** 片段 [1] 的示例中 `init_chat_model` 同时传了 `model_provider="openai"`，而片段 [2] 的示例未传 `model_provider`，而是把 provider 写在 `model` 字符串里（`"google_genai:gemini-4-hydrogen"`）[1][2]。两种写法在文档中均出现，请以你实际使用的 provider 形式为准。

**top5 片段**：

片段[1] `oss__python__langchain__models#077` ｜ Models ｜ Advanced topics > Rate limiting

```text
```

from langchain.rate_limiters import InMemoryRateLimiter



rate_limiter = InMemoryRateLimiter(

    requests_per_second=0.1,  # 1 request every 10s

    check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request

    max_bucket_size=10,  # Controls the maximum burst size.

)



model = init_chat_model(

    model="gpt-6.1-sol",

    model_provider="openai",

    rate_limiter=rate_limiter  

)

```
```

片段[2] `oss__python__deepagents__fault-tolerance#009` ｜ Fault tolerance ｜ Rate limiting > Provider rate limiting

```text
```

from langchain.rate_limiters import InMemoryRateLimiter

from langchain.chat_models import init_chat_model



rate_limiter = InMemoryRateLimiter(

    requests_per_second=0.1,  # 1 request every 10s

    check_every_n_seconds=0.1,  # Check every 100ms whether allowed to make a request

    max_bucket_size=10,  # Controls the maximum burst size

)



model = init_chat_model(

    model="google_genai:gemini-4-hydrogen",

    rate_limiter=rate_limiter,

)



agent = create_deep_agent(model=model, tools=[search_tool])

```
```

片段[3] `oss__python__langchain__middleware__built-in#034` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model call limit

```text
```

from langchain.agents import create_agent

from langchain.agents.middleware import ModelCallLimitMiddleware

from langgraph.checkpoint.memory import InMemorySaver



agent = create_agent(

    model="gpt-6.1-sol",

    checkpointer=InMemorySaver(),  # Required for thread limiting

    tools=[],

    middleware=[

        ModelCallLimitMiddleware(

            thread_limit=10,

            run_limit=5,

            exit_behavior="end",

        ),

    ],

)

```
```

片段[4] `oss__python__langgraph__interrupts#015` ｜ Interrupts ｜ Define an interrupt response schema

```text
pointer=InMemorySaver()) ) config = {"configurable": {"thread_id": "1"}} result = graph.invoke({"answer": None}, config) pending = result["__interrupt__"][0] assert pending.response_schema == Decision.model_json_schema() result = graph.invoke(Command(resume={"approved": True}), config) assert result["answer"] == Decision(approved=True) ```
```

片段[5] `oss__javascript__langchain__middleware__built-in#035` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Model call limit

```text
```

import { createAgent, modelCallLimitMiddleware } from "langchain";

import { MemorySaver } from "@langchain/langgraph";



const agent = createAgent({

  model: "gpt-6.1-sol",

  checkpointer: new MemorySaver(), // Required for thread limiting

  tools: [],

  middleware: [

    modelCallLimitMiddleware({

      threadLimit: 10,

      runLimit: 5,

      exitBehavior: "end",

    }),

  ],

});

```
```

---

## v2-I-007（single-hop）

**问题**：retrieve, offload, and delegate 这个 RAG 模式具体怎么跑？为什么这样能省 orchestrator 的上下文？

**gold**：agent 检索出匹配的 chunk 后写进文件系统 backend，而不是把全文留在 orchestrator 上下文里；再由子 agent 并行读、搜索并摘要各自负责的文件，大文档还能分页读或用 code interpreter 生成表格、时间线。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

这个模式的核心流程是：用户提问 → agent 检索出匹配的 chunk → 把 chunk **写入 filesystem backend**，而不是把全文留在 orchestrator 的上下文里 → 由 subagents 并行读取、搜索、总结各个文件 [1][2]。对于大文档，agent 还可以用内置搜索工具对文件分页，或运行 code interpreter 从源数据生成表格、时间线、可视化 [1][2]。

之所以能省 orchestrator 上下文，是因为片段明确说它「writes them to the filesystem backend rather than keeping full text in the orchestrator context」——即检索到的全文被卸载（offload）到文件系统，orchestrator 上下文里不再保留全文，只由 subagents 去读文件并汇总 [1][2]。这与 Deep Agents 的「Manage growing context: Summarize history and offload large results across long runs」思路一致 [8]。

**最小可用示例**

给出的片段里没有该模式可直接运行的完整代码。片段 [9][11] 只是「Why retrieval matters」里的 baseline agent 示例（`createDeepAgent` / `create_deep_agent`，tools 为空），并不是 retrieve-offload-delegate 的实现，不能当作该模式的示例。片段 [7] 是另一个页面（custom-workflow）的 RAG pipeline 图结构示例，也不是本模式。

因此按规则，**给出的文档里没有找到能回答「该模式具体代码怎么写」的内容**，缺少的是：把检索 chunk 写入 filesystem backend 的具体 API、subagent 并行读取/总结的配置方式，以及分页搜索与 code interpreter 的调用示例。

**与用户说法的一致性**

用户说的「retrieve, offload, and delegate」与片段中的模式名一致 [1][2]，无 API 名称或参数冲突需要指出。

**top5 片段**：

片段[1] `oss__javascript__deepagents__rag#004` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ RAG patterns

```text
- Retrieve, offload, and delegate : The user asks a question. The agent retrieves matching chunks and writes them to the filesystem backend rather than keeping full text in the orchestrator context. Subagents read, search, and summarize individual files in parallel. For large documents, the agent can paginate through files with built-in search tools or run a code interpreter to produce tables, timelines, or visuals from source data.
```

片段[2] `oss__python__deepagents__rag#004` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ RAG patterns

```text
- Retrieve, offload, and delegate : The user asks a question. The agent retrieves matching chunks and writes them to the filesystem backend rather than keeping full text in the orchestrator context. Subagents read, search, and summarize individual files in parallel. For large documents, the agent can paginate through files with built-in search tools or run a code interpreter to produce tables, timelines, or visuals from source data.
```

片段[3] `oss__javascript__deepagents__rag#000` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ ROOT

```text
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
```

片段[4] `oss__python__deepagents__rag#000` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ ROOT

```text
Retrieval Augmented Generation (RAG) with Deep Agents RAG patterns for Deep Agents, including skills-guided retrieval, rubric grading, and a tutorial that indexes LangChain docs, offloads chunks to the filesystem, and delegates analysis to subagents
```

片段[5] `oss__javascript__deepagents__retrieval#001` ｜ Retrieval ｜ RAG architectures

```text
| Architecture | Description | Control | Flexibility | Latency | Example Use Case |

| --- | --- | --- | --- | --- | --- |

| 2-Step RAG | Retrieval always happens before generation. Simple and predictable | ✅ High | ❌ Low | ⚡ Fast | FAQs, documentation bots |

| Agentic RAG | An LLM-powered agent decides when and how to retrieve during reasoning | ❌ Low | ✅ High | ⏳ Variable | Research assistants with access to multiple tools |

| Hybrid | Combines characteristics of both approaches with validation steps | ⚖️ Medium | ⚖️ Medium | ⏳ Variable | Domain-specific Q&A with quality validation |
```

---

## v2-I-008（single-hop）

**问题**：给 agent 的记忆划分 namespace 时，user / assistant / global 三种 scope 分别放什么？官方推荐哪个做默认？

**gold**：user scope 用 (user_id) 存每个用户的偏好，官方推荐作为默认；assistant scope 用 (assistant_id) 放单个助手的共享指令；global scope 用 (org_id) 放对所有用户和助手只读的策略。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- **User scope**：按 `user_id` 划分，用于存放**每个用户各自的偏好和上下文**（例如“我希望回答简洁一些”）。官方标注为 **recommended default（推荐默认）** [2][3]。
- **Assistant scope**：按 `assistant_id` 划分，用于存放**某个 assistant 共享的指令**（例如“帖子最多 280 字符”）[2][3]。
- **Global scope**：按 `org_id` 划分，用于存放**对所有用户和 assistant 都适用的只读策略**（例如“绝不披露内部定价”）[2][3]。

**官方推荐的默认 scope：User（user_id）** [2][3]。

**最小可用示例（JavaScript，来自片段 [1]）：**

```javascript
import { StoreBackend } from "deepagents";

// User scope（推荐默认）：从已认证的 Agent Server 用户派生
const perUserBackend = new StoreBackend({
  namespace: ({ config }) => [String(config?.configurable?.langgraph_auth_user_id)],
});

// Assistant scope：使用解析出的 assistant id
const perAssistantBackend = new StoreBackend({
  namespace: ({ assistantId }) => [assistantId ?? "default"],
});

// Global scope：构造时已知范围，用静态 namespace
const orgId = "acme";
const userId = "user-1";
const staticBackend = new StoreBackend({
  namespace: ["memories", orgId, userId, "filesystem"],
});
```

**补充说明（以片段为准）：**

- 片段 [1] 中 `StoreBackend` 的 `namespace` 既支持**函数**（接收 `{ config }` 或 `{ assistantId }`），也支持**静态数组**；函数形式里 user 的取值路径是 `config?.configurable?.langgraph_auth_user_id` [1]。
- 片段 [9] 展示了另一种写法：`namespace: (rt) => [rt.serverInfo.assistantId, rt.serverInfo.user.identity]`，即同时把 assistant 和 user 拼进 namespace [9]。这与 [1] 的 `config.configurable.langgraph_auth_user_id` 写法**不一致**，属于不同 API 形态，使用时请按你所用的版本对齐。
- 片段 [2][3] 的表格里 namespace 写作 `(user_id)`、`(assistant_id)`、`(org_id)`，是概念性表示，不是可直接复制的代码 [2][3]。

**top5 片段**：

片段[1] `oss__javascript__deepagents__backends#049` ｜ Backends ｜ Built-in backends > StoreBackend (LangGraph store) > Namespace factories

```text
```

import { StoreBackend } from "deepagents";



// Per-user: derive from the authenticated Agent Server user

const perUserBackend = new StoreBackend({

  namespace: ({ config }) => [String(config?.configurable?.langgraph_auth_user_id)],

});



// Per-assistant: use the resolved assistant id

const perAssistantBackend = new StoreBackend({

  namespace: ({ assistantId }) => [assistantId ?? "default"],

});



// Static namespace when the scope is known at construction time

const orgId = "acme";

const userId = "user-1";

const staticBackend = new StoreBackend({

  namespace: ["memories", orgId, userId, "filesystem"],

});

```
```

片段[2] `oss__javascript__deepagents__going-to-production#027` ｜ Going to production ｜ Memory > Scoping

```text
| Scope | Namespace | Use case | Example |

| --- | --- | --- | --- |

| User (recommended default) | (user_id) | Per-user preferences and context | ”I prefer concise responses” |

| Assistant | (assistant_id) | Shared instructions for one assistant | ”Cap posts at 280 characters” |

| Global | (org_id) | Read-only policies for all users and assistants | ”Never disclose internal pricing” |
```

片段[3] `oss__python__deepagents__going-to-production#026` ｜ Going to production ｜ Memory > Scoping

```text
| Scope | Namespace | Use case | Example |

| --- | --- | --- | --- |

| User (recommended default) | (user_id) | Per-user preferences and context | ”I prefer concise responses” |

| Assistant | (assistant_id) | Shared instructions for one assistant | ”Cap posts at 280 characters” |

| Global | (org_id) | Read-only policies for all users and assistants | ”Never disclose internal pricing” |
```

片段[4] `oss__python__deepagents__memory#007` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
da rt: ("my-agent",) ), "/skills/": StoreBackend( namespace=lambda rt: ("my-agent",) ), }, ), store=store, ) # Thread 1: the agent learns a new preference and saves it to memory config1 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "I prefer detailed explanations. Remember that."}]}, config=config1, ) # Thread 2: the agent reads memory and applies the preference config2 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "Explain how transformers work."}]}, config=config2, ) ```
```

片段[5] `oss__python__deepagents__memory#004` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
``` from deepagents import create_deep_agent from deepagents.backends import CompositeBackend, StateBackend, StoreBackend agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", memory=["/memories/AGENTS.md"], skills=["/skills/"], backend=CompositeBackend( default=StateBackend(), routes={ "/memories/": StoreBackend( namespace=lambda rt: ( rt.server_info.assistant_id, ), ), "/skills/": StoreBackend( namespace=lambda rt: ( rt.server_info.assistant_id, ), ), }, ), ) ```
```

---

## v2-I-009（single-hop）

**问题**：对话变长触发上下文压缩后，较早轮次里的图片、音频、视频块会怎样？keep 阈值内的消息受影响吗？

**gold**：summarization 只把较早消息压成纯文本摘要，范围内的 image、audio、video、file 块不会被带过去，模型只能看到 summarizer 写下的文字；keep 阈值内的最近消息保持不变。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. 对话变长触发摘要式压缩（summarization）后，较早轮次里的图片、音频、视频、文件块**不会被保留到摘要中**——摘要只写入摘要器生成的纯文本，模型只能看到摘要器对这些媒体内容的文字描述 [1][2]。
2. **keep 阈值以内的近期消息不受影响**，保持原样 [1][2]。
3. 补充一点：offloading（卸载）只按文本 token 计量，非文本块（含图片）在替换消息中会被保留而非压缩；仅含图片的消息不会仅因图片大小被卸载 [8][10]。这与摘要压缩的行为不同，注意区分两种机制。

**最小示例（Python，摘自片段）：**

```python
# Before — model receives image blocks in older turns
[
    HumanMessage(
        content=[
            {"type": "text", "text": "What trends do you see in this chart?"},
            {"type": "image", "base64": IMG, "mime_type": "image/png"},
        ]
    ),
    ToolMessage(
        content=[
            {"type": "text", "text": "Updated chart:"},
            {"type": "image", "base64": IMG, "mime_type": "image/png"},
        ],
        tool_call_id="call_chart_1",
    ),
    AIMessage(content="Revenue rose in Q3 based on the chart trend."),
    HumanMessage(content="Reply with one sentence summarizing our analysis."),
]

# After — those turns collapse to text; image blocks are gone
{
    "content": (
        "User asked about trends in a chart screenshot. "
        "Tool returned an updated chart. Agent identified Q3 revenue growth."
    )
}
```

原始对话仍会以文本形式写入文件系统 [7]。

**另外**，片段还建议：在长对话中优先使用引用（references）而非 base64 编码的图片块 [6]。

**关于 API 名称的说明：** 片段中摘要中间件的创建函数在 Python 侧为 `create_summarization_middleware` [4]，JavaScript 侧为 `createSummarizationMiddleware` [3]，与「SummarizationMiddleware」这一组件名对应，无冲突。

**top5 片段**：

片段[1] `oss__python__deepagents__multimodal#005` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: # Before — model receives image blocks in older turns [ HumanMessage ( content = [ { "type" : "text" , "text" : "What trends do you see in this chart?" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ] ), ToolMessage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" :
```

片段[2] `oss__javascript__deepagents__multimodal#005` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
- Summarization compacts older messages into a text-only summary. Image, audio, video, and file blocks in that range are not carried forward—the model only sees what the summarizer writes about them. Recent messages below the keep threshold stay unchanged. When summarization runs, media blocks in older turns drop out of the active context: // Before — model receives image blocks in older turns void { role : "user" , content : [ { type : "text" , text : "What trends do you see in this chart?" }, { type : "image" , url : "https://example.com/chart.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url :
```

片段[3] `oss__python__deepagents__multimodal#006` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
ssage ( content = [ { "type" : "text" , "text" : "Updated chart:" }, { "type" : "image" , "base64" : IMG , "mime_type" : "image/png" }, ], tool_call_id = "call_chart_1" , ), AIMessage ( content = "Revenue rose in Q3 based on the chart trend." ), HumanMessage ( content = "Reply with one sentence summarizing our analysis." ), ] # After — those turns collapse to text; image blocks are gone { "content" : ( "User asked about trends in a chart screenshot. " "Tool returned an updated chart. Agent identified Q3 revenue growth." )} The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
```

片段[4] `oss__javascript__deepagents__multimodal#006` ｜ Multimodal inputs and outputs ｜ Context compression and multimodal content

```text
.png" }, ] , }; void { role : "tool" , content : [ { type : "text" , text : "Updated chart:" }, { type : "image" , url : "https://example.com/chart-v2.png" }, ] , }; // After — those turns collapse to text; image blocks are gone void { content : "User asked about trends in a chart screenshot. " + "Tool returned an updated chart. Agent identified Q3 revenue growth." , }; The original conversation is still written to the filesystem as text. See Summarization for triggers, keep thresholds, and the full flow.
```

片段[5] `oss__javascript__deepagents__customization#060` ｜ Customize Deep Agents ｜ Middleware > Deep Agents stack > Full stack

```text
3. SummarizationMiddleware : Condenses message history to stay within context limits when conversations grow long (via createSummarizationMiddleware ).
```

---

## v2-I-010（single-hop）

**问题**：在 supervisor 里怎么查出某个父线程启动的所有 async 子 agent 线程？

**gold**：用 LangGraph SDK 客户端按 metadata 过滤：调用 client.threads.search，metadata 里传 parent_thread_id；父线程 id 从 config 的 metadata 里取。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：通过 LangGraph SDK 的 `client.threads.search`，用 `metadata.parent_thread_id` 过滤即可查出某个父线程启动的所有 async 子 agent 线程。父线程 ID 在子 agent 运行时可从 `config.metadata.parent_thread_id` 取得（该值由 supervisor 用 `start_async_task` 启动时设置）[1][2]。

Python 最小示例（来自 [1]）：

```python
from langchain_core.runnables import RunnableConfig
from langgraph_sdk import get_client
from deepagents import create_deep_agent

async def find_subagent_threads(parent_thread_id: str) -> list[dict]:
    client = get_client()
    return await client.threads.search(metadata={"parent_thread_id": parent_thread_id})

def researcher(config: RunnableConfig):
    # Set when a supervisor launched this run with `start_async_task`
    parent_thread_id = (config.get("metadata") or {}).get("parent_thread_id")
    return create_deep_agent(
        model="openai:gpt-5.5",
        system_prompt="You research topics thoroughly.",
    )
```

JavaScript 最小示例（来自 [2]）：

```javascript
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
    model: "fireworks:accounts/fireworks/models/glm-5p2",
    systemPrompt: "You research topics thoroughly.",
  });
}
```

补充说明：
- 片段中 Python 与 JS 的 API 名称不同：Python 用 `get_client()` 和 `await client.threads.search(...)`，JS 用 `new Client()` 和 `client.threads.search(...)`，请按语言对应使用 [1][2]。
- 若子 agent 部署在其他 deployment 上，片段 [7] 提示 `get_client()` 可传 `url=...`，但该片段讲的是处理等待输入的 subagent，并非直接针对本问题的检索场景，仅供参考 [7]。
- 片段中多个 JS 示例仅 `model` 取值不同（如 `google:gemini-4-hydrogen`、`anthropic:claude-sonnet-5` 等），检索逻辑一致 [2][3][4][5][8]。

**top5 片段**：

片段[1] `oss__python__deepagents__async-subagents#016` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
```

from langchain_core.runnables import RunnableConfig

from langgraph_sdk import get_client



from deepagents import create_deep_agent



async def find_subagent_threads(parent_thread_id: str) -> list[dict]:

    client = get_client()

    return await client.threads.search(metadata={"parent_thread_id": parent_thread_id})



def researcher(config: RunnableConfig):

    # Set when a supervisor launched this run with `start_async_task`

    parent_thread_id = (config.get("metadata") or {}).get("parent_thread_id")

    return create_deep_agent(

        model="openai:gpt-5.5",

        system_prompt="You research topics thoroughly.",

    )

```
```

片段[2] `oss__javascript__deepagents__async-subagents#026` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

```text
``` import { Client } from "@langchain/langgraph-sdk"; import type { LangGraphRunnableConfig } from "@langchain/langgraph"; import { createDeepAgent } from "deepagents"; async function findSubagentThreads(parentThreadId: string) { const client = new Client(); return client.threads.search({ metadata: { parent_thread_id: parentThreadId } }); } function researcher(config: LangGraphRunnableConfig) { // Set when a supervisor launched this run with `start_async_task` const parentThreadId = config.metadata?.parent_thread_id; return createDeepAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", systemPrompt: "You research topics thoroughly.", }); } ```
```

片段[3] `oss__javascript__deepagents__async-subagents#025` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

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

片段[4] `oss__javascript__deepagents__async-subagents#022` ｜ Async subagents ｜ Understand state management > Find a supervisor’s subagent threads

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

## v2-I-011（single-hop）

**问题**：官方建议怎么限制子 agent 回传的内容量，避免把主 agent 的上下文撑爆？

**gold**：在子 agent 的 system_prompt 里明确要求只返回 essential summary，控制在 under 500 words，不要包含原始搜索结果或详细的 tool 输出。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段只涉及：
- 如何用 `agent.stream(..., stream_mode="updates", subgraphs=True, version="v2")` 区分主 agent（`chunk["ns"]` 为空）与子 agent（`chunk["ns"]` 非空）的更新，以及如何打印子 agent 返回的 tool 消息 [1][9]；
- 一句说明「主 agent 保留对话上下文，但子 agent 每次都是全新开始」[7][8]。

片段中没有任何关于「限制子 agent 回传内容量」「截断/摘要子 agent 输出」「避免主 agent 上下文膨胀」的官方建议或参数说明。唯一与「量」相关的只是示例里打印时用了 `str(msg.content)[:200]` 做展示截断 [1]，但那是打印层面的截断，并非官方对回传内容量的限制建议，不能据此推断。

缺少的内容：关于子 agent 输出如何进入主 agent 上下文、是否有 `max_tokens`/摘要/裁剪等配置项的官方说明。

**top5 片段**：

片段[1] `oss__python__deepagents__streaming#020` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[2] `oss__python__deepagents__streaming#023` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[3] `oss__python__deepagents__streaming#017` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[4] `oss__python__deepagents__streaming#011` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

片段[5] `oss__python__deepagents__streaming#029` ｜ Streaming ｜ Subagent progress

```text
ide a concise summary in 2-3 sentences." ), }, ], ) for chunk in agent.stream( {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]}, stream_mode="updates", subgraphs=True, version="v2", ): if chunk["type"] == "updates": # Main agent updates (empty namespace) if not chunk["ns"]: for node_name, data in chunk["data"].items(): if node_name == "tools": # Subagent results returned to main agent for msg in data.get("messages", []): if msg.type == "tool": print(f"\nSubagent complete: {msg.name}") print(f"  Result: {str(msg.content)[:200]}...") else: print(f"[main agent] step: {node_name}") # Subagent updates (non-empty namespace) else:
```

---

## v2-I-012（single-hop）

**问题**：FilesystemPermission 规则里 operations 的 read 和 write 分别覆盖哪些内置工具？paths 支持什么写法？mode 默认值是什么？

**gold**：read 覆盖 ls、read_file、glob、grep；write 覆盖 write_file、edit_file、delete。paths 是 glob 模式，支持 ** 递归匹配和 {a,b} 交替；mode 取 allow / deny / interrupt，默认 allow。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- `operations` 中 `"read"` 覆盖 `ls`、`read_file`、`glob`、`grep`；`"write"` 覆盖 `write_file`、`edit_file`、`delete`（Python 版）[4]。注意 JavaScript 版的 `"write"` 只列了 `write_file`、`edit_file`，没有 `delete` [3]，两版存在差异。
- `paths` 是 glob 模式字符串数组，支持 `**` 递归匹配和 `{a,b}` 交替写法，例如 `["/workspace/**"]` [3][4]。
- `mode` 默认值为 `"allow"` [3][4]。Python 版 `mode` 可取 `"allow" | "deny" | "interrupt"`（`interrupt` 用于暂停等待人工审批）[4]；JavaScript 版只列了 `"allow" | "deny"` [3]。

**最小可用示例（Python）：**

```python
FilesystemPermission(
    operations=["read", "write"],
    paths=["/workspace/**"],
    mode="allow",
)
```

**差异提示：** 你问的 `operations` 覆盖范围在 Python 与 JavaScript 文档中不完全一致——Python 的 `"write"` 包含 `delete` [4]，JavaScript 的 `"write"` 未包含 [3]；`mode` 的取值集合也以各自片段为准 [3][4]。

**top5 片段**：

片段[1] `oss__python__deepagents__permissions#005` ｜ Permissions ｜ Examples > Protect specific files

```text
```

agent = create_deep_agent(

    model=model,

    backend=backend,

    permissions=[

        FilesystemPermission(

            operations=["read", "write"],

            paths=["/workspace/.env", "/workspace/examples/**"],

            mode="deny",

        ),

        FilesystemPermission(

            operations=["read", "write"],

            paths=["/workspace/**"],

            mode="allow",

        ),

        FilesystemPermission(

            operations=["read", "write"],

            paths=["/**"],

            mode="deny",

        ),

    ],

)

```
```

片段[2] `oss__python__deepagents__permissions#004` ｜ Permissions ｜ Examples > Isolate to a workspace directory

```text
```

agent = create_deep_agent(

    model=model,

    backend=backend,

    permissions=[

        FilesystemPermission(

            operations=["read", "write"],

            paths=["/workspace/**"],

            mode="allow",

        ),

        FilesystemPermission(

            operations=["read", "write"],

            paths=["/**"],

            mode="deny",

        ),

    ],

)

```
```

片段[3] `oss__python__deepagents__permissions#010` ｜ Permissions ｜ Subagent permissions

```text
``` agent = create_deep_agent( model=model, backend=backend, permissions=[ FilesystemPermission( operations=["read", "write"], paths=["/workspace/**"], mode="allow", ), FilesystemPermission( operations=["read", "write"], paths=["/**"], mode="deny", ), ], subagents=[ { "name": "auditor", "description": "Read-only code reviewer", "system_prompt": "Review the code for issues.", "permissions": [ FilesystemPermission( operations=["write"], paths=["/**"], mode="deny", ), FilesystemPermission( operations=["read"], paths=["/workspace/**"], mode="allow", ), FilesystemPermission( operations=["read"], paths=["/**"], mode="deny", ), ], } ], ) ```
```

片段[4] `oss__python__deepagents__permissions#009` ｜ Permissions ｜ Examples > Rule ordering

```text
mission( operations=["read", "write"], paths=["/workspace/.env"], mode="deny",  # never reached ), FilesystemPermission( operations=["read", "write"], paths=["/**"], mode="deny", ), ] ```
```

片段[5] `oss__javascript__deepagents__permissions#002` ｜ Permissions ｜ Rule structure

```text
| Field | Type | Description |

| --- | --- | --- |

| operations | ("read" \| "write")[] | Operations this rule applies to. "read" covers ls , read_file , glob , grep . "write" covers write_file , edit_file . |

| paths | string[] | Glob patterns for matching file paths (e.g., ["/workspace/**"] ). Supports ** for recursive matching and {a,b} for alternation. |

| mode | "allow" \| "deny" | Whether to allow or deny matching operations. Defaults to "allow" . |
```

---

## v2-I-013（single-hop）

**问题**：deepagents v0.7.0 对文件系统工具做了哪些调整？read_file 和 grep 的行为有什么变化？

**gold**：新增 delete 工具（可递归删目录）；write_file 改成覆盖已有文件而不再报错；read_file 改为分页并报告 total/remaining 行数和 next offset；grep/glob 在大目录树上返回带 truncated 标志的部分结果；grep 加了 1,000 条匹配上限；FilesystemMiddleware 支持工具白名单。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

deepagents v0.7.0 对文件系统工具做了以下调整 [2]：

1. **新增 `delete` 工具**：可删除文件，或递归删除目录 [2]。
2. **`write_file` 行为变更**：现在会覆盖已存在的文件，而不是报错 [2]。
3. **`FilesystemMiddleware` 支持工具白名单**：可只暴露选定的内置工具 [2]。
4. **针对开放模型优化了读取和搜索** [2]：
   - **`read_file`**：改为分页读取，会报告总行数、剩余行数以及下一个 offset [2]。
   - **`grep` / `glob`**：在大目录树上返回带 `truncated` 标志的部分结果，而不是卡住 [2]。
   - **`grep`**：新增 1,000 条匹配上限，支持流式输出和可选的上下文行 [2]。

## 最小可用示例

片段 [2] 只描述了行为变化，没有给出 v0.7.0 的具体调用代码。片段 [3] 展示了 `FilesystemMiddleware` 使用 `tools` 白名单的写法（该片段来自 Python overview 页面，未标注版本）：

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

## 需要指出的差异

- 你问的是 **v0.7.0**，但片段 [1] 和 [8] 描述的是 **JavaScript 版 deepagents v1.9.0-alpha.0** 的 Backend protocol v2（结构化 `Result` 类型、`read()` 返回 `ReadResult`、`readRaw()` 返回 `Uint8Array`、方法名 `lsInfo -> ls` 等）。这些属于另一个版本/语言线的变更，不能当作 v0.7.0 的内容 [1][8]。
- 片段 [2] 未说明 `read_file` 分页参数的具体名称，也未给出 `grep` 上下文行参数的名称，因此无法从给出的文档确认这些 API 细节。

**top5 片段**：

片段[1] `oss__javascript__releases__changelog#011` ｜ Changelog ｜ deepagents v1.9.0-alpha.0

```text
- Backend protocol v2 : We’ve introduced a new v2 backend protocol ( BackendProtocolV2 ) with backward-compatible changes to the Deep Agents backend interface. Key changes: Structured result types : All methods now return structured Result objects (e.g., ReadResult , LsResult , GrepResult , GlobResult ) with consistent error handling via an error field, instead of returning raw values or throwing exceptions. Multi-modal file support : read() returns a ReadResult with a .content field instead of a plain string. For binary files (images, PDFs, audio, video), the full raw Uint8Array content is returned via readRaw() , enabling agents to work with multi-modal files natively.
```

片段[2] `oss__python__releases__changelog#019` ｜ Changelog ｜ deepagents v0.7.0 > Features

```text
- Filesystem tools : New delete tool removes a file or recursively removes a directory ( #3659 , #3851 ); write_file now overwrites an existing file instead of erroring ( #4109 ); FilesystemMiddleware accepts a tool allowlist to expose only selected built-in tools ( #4325 , #4698 ); and reads and searches are tuned for open models — paginated read_file reports total and remaining lines plus the next offset ( #4540 ), grep / glob return partial results with a truncated flag instead of hanging on large trees ( #4063 ), and grep gains a 1,000-match cap with streamed output and optional context lines ( #4570 , #4706 ).
```

片段[3] `oss__python__deepagents__overview#019` ｜ Deep Agents overview ｜ Execution environment > Virtual filesystem access

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

片段[4] `oss__python__releases__changelog#037` ｜ Changelog ｜ deepagents v0.5.0

```text
- Backend changes : We’ve made backward-compatible changes to the Deep Agents backend protocol : Updated the file format stored in State and Store backends to support binary files. Improved error propagation from backends to tools. You can now instantiate StateBackend() and StoreBackend() directly. Specifying with a factory (e.g., backend=(lambda rt: StateBackend(rt)) ) is deprecated.
```

片段[5] `oss__python__langchain__middleware__built-in#061` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Filesystem middleware

```text
``` from langchain.agents import create_agent from deepagents.middleware.filesystem import FilesystemMiddleware # FilesystemMiddleware is included by default in create_deep_agent # You can customize it if building a custom agent agent = create_agent( model="claude-sonnet-4-6", middleware=[ FilesystemMiddleware( backend=None,  # Optional: custom backend (defaults to StateBackend) system_prompt="Write to the filesystem when...",  # Optional custom addition to the system prompt custom_tool_descriptions={ "ls": "Use the ls tool when...", "read_file": "Use the read_file tool to..." },  # Optional: Custom descriptions for filesystem tools tools=["read_file", "ls", "glob", "grep"],  # Optional:
```

---

## v2-I-014（single-hop）

**问题**：文档里写交叉引用时，@[X]、@[`X`]、@[text][X] 和反斜杠转义分别渲染成什么？

**gold**：@[ChatAnthropic] 用 ChatAnthropic 作显示文本；@[`ChatAnthropic`] 用代码格式的 ChatAnthropic 作文本；@[text][ChatAnthropic] 用 text 显示、ChatAnthropic 作为 link map 的 key；前面加反斜杠则转义为字面量、不生成链接。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：文档里交叉引用的四种写法渲染结果如下（JavaScript 与 Python 文档的说明一致）：

- `@[ChatAnthropic]`：渲染为链接，显示文本是 “ChatAnthropic” [1][2]
- `@[`ChatAnthropic`]`：渲染为链接，显示文本是代码格式的 `ChatAnthropic` [1][2]
- `@[text][ChatAnthropic]`：渲染为链接，显示文本是 “text”，而 ChatAnthropic 是链接映射（link map）里的 key [1][2]
- `\@[ChatAnthropic]`：转义写法，渲染为字面量 `@[ChatAnthropic]`，不生成链接 [1][2]

补充说明：key 是 `@[key]` 或 `@[text][key]` 中使用的链接名，value 是相对于 reference host 的路径 [7][9]。

最小可用示例（原语言保留）：

```
See @[`ChatAnthropic`] for all configuration options.

The @[`bind_tools`][ChatAnthropic.bind_tools] method accepts...
```
[8][10]

**top5 片段**：

片段[1] `oss__javascript__contributing__documentation#015` ｜ Contributing to documentation ｜ Quality standards > Cross-referencing

```text
| Syntax | Result |

| --- | --- |

| @[ChatAnthropic] | Link with “ChatAnthropic” as the displayed text |

| @[`ChatAnthropic`] | Link with `ChatAnthropic` (code formatted) as text |

| @[text][ChatAnthropic] | Link with “text” as text and ChatAnthropic as the key in the link map |

| \@[ChatAnthropic] | Escaped: renders as literal @[ChatAnthropic] (no link – what’s being used on this page!) |
```

片段[2] `oss__python__contributing__documentation#015` ｜ Contributing to documentation ｜ Quality standards > Cross-referencing

```text
| Syntax | Result |

| --- | --- |

| @[ChatAnthropic] | Link with “ChatAnthropic” as the displayed text |

| @[`ChatAnthropic`] | Link with `ChatAnthropic` (code formatted) as text |

| @[text][ChatAnthropic] | Link with “text” as text and ChatAnthropic as the key in the link map |

| \@[ChatAnthropic] | Escaped: renders as literal @[ChatAnthropic] (no link – what’s being used on this page!) |
```

片段[3] `oss__javascript__deepagents__backends#083` ｜ Backends ｜ Multimodal and binary files > Supported MIME types

```text
| video/mp4 , video/webm , video/mpeg , video/quicktime , video/x-msvideo , video/x-flv , video/x-ms-wmv , video/3gpp | | Documents | .pdf , .ppt , .pptx | application/pdf , application/vnd.ms-powerpoint , application/vnd.openxmlformats-officedocument.presentationml.presentation | | Text | .txt , .html , .json , .js , .ts , .py , etc. | text/plain , text/html , application/json , etc. |
```

片段[4] `oss__javascript__contributing__documentation#016` ｜ Contributing to documentation ｜ Quality standards > Cross-referencing

```text
3. The key is the link name used in @[key] or @[text][key] , the value is the path relative to the reference host
```

片段[5] `oss__python__contributing__documentation#016` ｜ Contributing to documentation ｜ Quality standards > Cross-referencing

```text
3. The key is the link name used in @[key] or @[text][key] , the value is the path relative to the reference host
```

---

## v2-I-015（multi-hop）

**问题**：memory= 只是把 agent 指向几个文件路径，那到底谁决定这些文件存在哪、能不能持久？要让 /memories/ 落进 LangGraph store，backend 和 store 分别该怎么给？

**gold**：memory= 只给出记忆文件路径，真正决定存储位置与访问权的是 backend；要持久化需要 CompositeBackend，default 用 StateBackend，routes 里把 /memories/ 映射到 StoreBackend（namespace 取 rt.server_info.user.identity），且 store=InMemoryStore() 必须传给 create_deep_agent 而不是传给 backend。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论**

1. `memory=` 只是把 agent 指向记忆文件路径；文件实际存在哪、谁能访问，由 **backend** 控制 [1]。
2. 要让 `/memories/` 落进 LangGraph store，需要用 `CompositeBackend` 把 `/memories/` 路由到 `StoreBackend`，并把 `store` 传给 `create_deep_agent`（不是传给 backend）[4][5]。
3. 注意片段里的参数写法：`store` 是 `create_deep_agent(...)` 的参数，`backend` 是另一个参数；片段 [5] 的注释明确写了 “Store passed to create_deep_agent, not backend” [5]。

**最小可用示例**（来自片段 [4][5]）

```python
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    store=store,
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),
        },
    ),
    system_prompt="""When users tell you their preferences, save them to
    /memories/user_preferences.txt so you remember them in future conversations.""",
)
```

**补充说明**

- 片段 [2] 提到 LangGraph 的持久化层：checkpointer 提供短期记忆，store 提供长期记忆 [2]；但片段没有进一步说明 `StoreBackend` 内部如何读写 store，这部分给出的文档里没有找到。
- 片段 [1] 还提到可以用 `skills=` 传程序性记忆，以及 backend 控制文件存储位置和访问权限 [1]，但没有展开 backend 的具体配置细节。

**top5 片段**：

片段[1] `oss__python__deepagents__memory#001` ｜ Memory ｜ How memory works

```text
1. Point the agent at memory files. Pass file paths to memory= when creating the agent. You can also pass skills via skills= for procedural memory (reusable instructions that tell the agent how to perform a task). A backend controls where files are stored and who can access them.
```

片段[2] `oss__python__langgraph__persistence#000` ｜ Persistence ｜ ROOT

```text
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
```

片段[3] `oss__javascript__langgraph__persistence#000` ｜ Persistence ｜ ROOT

```text
Persistence LangGraph’s persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
```

片段[4] `oss__python__deepagents__context-engineering#069` ｜ Context engineering in Deep Agents ｜ Long-term memory

```text
```

from deepagents import create_deep_agent

from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

from langgraph.store.memory import InMemoryStore



store = InMemoryStore()



agent = create_deep_agent(

    model="fireworks:accounts/fireworks/models/glm-5p2",

    store=store,

    backend=CompositeBackend(

        default=StateBackend(),

        routes={

            "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),

        },

    ),

    system_prompt="""When users tell you their preferences, save them to

    /memories/user_preferences.txt so you remember them in future conversations.""",

)

```
```

片段[5] `oss__python__deepagents__customization#143` ｜ Customize Deep Agents ｜ Backends

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

---

## v2-I-016（multi-hop）

**问题**：为什么一个 agent 挂十几个 skill 不会明显撑大上下文，而一份同样大小的记忆文件却会？

**gold**：skills 走三级渐进披露：启动时只为每个 skill 加载 frontmatter 里的 name 和 description，被调用时才载入完整 SKILL.md 正文，scripts/references/assets 只在指令引用时按需读；而 memory 可以在启动时整份读进 system prompt（也可以按需读），一旦选择启动加载，记忆的体积就直接进上下文。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

给出的文档里**没有直接对比**「十几个 skill」与「同样大小的记忆文件」在上下文占用上的差异，因此无法完整回答这个对比问题。缺的是：关于记忆文件加载方式（是否全量注入 system prompt）与 skill 按需加载之间上下文开销的量化对比说明。

不过，片段中确实说明了 skill 为什么能保持上下文精简，可以解释问题中 skill 那一半：

- skill 采用**按需加载（on-demand loading）**：启动时 agent 只读取 skill 的**描述**，只有当某个 skill 匹配当前任务时，才读取完整的 skill 文件。这样在能力被真正需要之前，上下文一直保持精简 [1][2]。
- 另外，过大的 skill 本身也有约束：超过 10 MB 的 `SKILL.md` 在发现阶段会被 Deep Agents 跳过 [3][4]；而大于 10K tokens（约 7.5K 词，或超过上下文窗口的 5–10%）的 skill 建议使用渐进式披露（分页、基于搜索的加载、分层探索）以避免占用过多上下文 [5][6]。

也就是说，skill 之所以「挂十几个也不明显撑大上下文」，是因为启动阶段只加载描述、完整内容延迟到匹配时才读 [1][2]，且超大 skill 有跳过与渐进披露机制 [3][4][5][6]。

至于「同样大小的记忆文件却会撑大上下文」这一半，片段中只提到 agent 可以**在启动时把记忆文件加载进 system prompt**，或**在对话中按需读取** [1][2]，以及通过 `memory=` 传入文件路径、通过 `skills=` 传入技能 [10][12]。但**没有说明记忆文件默认采用哪种加载方式、是否会全量注入**，也没有与 skill 的加载开销做对比。因此不能据此断言记忆文件一定会撑大上下文。

## 最小可用示例

片段未给出可直接运行的代码示例（仅提到 `memory=` 与 `skills=` 两个参数 [10][12]），故不提供代码，避免臆造 API 用法。

## 与提问说法的差异提示

提问把「skill 不撑上下文」与「记忆文件撑上下文」当作既定事实对比，但文档只支持前者（按需加载 [1][2]），后者在给出的片段中**没有依据**。若需确认记忆文件的加载策略，需要查阅 memory 页面中关于加载时机与 system prompt 注入的完整说明。

**top5 片段**：

片段[1] `oss__python__deepagents__memory#002` ｜ Memory ｜ How memory works

```text
2. Agent reads memory. The agent can load memory files into the system prompt at startup, or read them on demand during the conversation. For example, skills use on-demand loading: the agent reads only skill descriptions at startup, then reads the full skill file only when it matches a task. This keeps context lean until a capability is needed.
```

片段[2] `oss__javascript__deepagents__memory#002` ｜ Memory ｜ How memory works

```text
2. Agent reads memory. The agent can load memory files into the system prompt at startup, or read them on demand during the conversation. For example, skills use on-demand loading: the agent reads only skill descriptions at startup, then reads the full skill file only when it matches a task. This keeps context lean until a capability is needed.
```

片段[3] `oss__javascript__deepagents__skills#126` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
3. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
```

片段[4] `oss__python__deepagents__skills#126` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
4. Check file size. Deep Agents skips SKILL.md files over 10 MB during discovery.
```

片段[5] `oss__javascript__langchain__multi-agent__skills-sql-assistant#061` ｜ Build a SQL assistant with on-demand skills ｜ Implementation variations

```text
- Large skills (> 10K tokens / ~7.5K words, or > 5-10% of context window): Should use progressive disclosure techniques like pagination, search-based loading, or hierarchical exploration to avoid consuming excessive context
```

---

## v2-I-017（multi-hop）

**问题**：想让后台运行的 async 子 agent 拿到父对话的上下文，又不阻塞父 agent、还能中途追加指令，启动模式和工具该怎么组合？

**gold**：启动模式设为 fork，它会先发父对话快照再发任务描述（isolated 默认只发任务描述）；用 start_async_task 启动会立即返回 Task ID、不阻塞父流程，之后用 update_async_task 追加指令、check_async_task 查状态、cancel_async_task 取消任务。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：用 `"fork"` 启动模式 + `start_async_task` 启动 + `update_async_task` 追加指令。`"fork"` 会把父对话快照随任务描述一起发给子 agent，从而让后台子 agent 拿到父上下文 [4][5]；`start_async_task` 立即返回任务 ID、不阻塞父 agent [11]；`update_async_task` 用于向任务发送新指令 [11]。注意：async 子 agent 需要 LangSmith Deployment 支持 [6][7]。

最小可用示例（示意，片段未给出完整调用签名）：

```python
# 1) 以 fork 模式启动后台任务，立即拿到 task_id，不阻塞父 agent
task_id = start_async_task(
    mode="fork",              # 发送父对话快照 + 任务描述 [4][5]
    task="...",               # 任务描述
)

# 2) 父 agent 继续交互；需要时查看状态
status = check_async_task(task_id)

# 3) 中途追加指令
update_async_task(task_id, instructions="...")
```

补充说明与差异提示：

- 启动模式默认是 `"isolated"`，只发送任务描述、子 agent 看不到父对话历史 [4][5]；要拿父上下文必须显式设为 `"fork"` [4][5]。
- `"fork"` 发送的是“启动时刻的父对话快照”，之后父对话的新增内容不会自动同步 [4][5]。
- 同步（非 async）子 agent 的字典配置里也有 `mode` 字段（`"isolated"` / `"fork"`，默认 `"isolated"`），其中 `"fork"` 会保留父 system prompt 不变，并在继承的对话之后随任务消息传递指令 [1]；这与 async 场景的 `"fork"` 描述（发送父对话快照）表述角度不同，但都指向“继承父上下文” [1][4]。
- 工具名以片段为准：启动是 `start_async_task`（不是 `launch` 之类），返回的是 thread ID 作为 task ID [2][3][11]；追加指令是 `update_async_task` [11]。

**top5 片段**：

片段[1] `oss__python__deepagents__subagents#003` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
nts must define their own. Include tool usage guidance and output format requirements. Does not inherit from main agent. For mode: "fork" , the fork keeps the parent’s system prompt unchanged and delivers these instructions with the task message after the inherited conversation, preserving the parent’s cached prompt prefix. See Forked subagents . | | mode | "isolated" \| "fork" | Optional. Context mode. Defaults to "isolated" , where the subagent only sees the delegated task. Set to "fork" to inherit the parent’s conversation and system prompt instead. See Forked subagents . | | tools | list[Callable] | Optional. Tools the subagent can use. Keep this minimal and include only what’s needed.
```

片段[2] `oss__python__deepagents__async-subagents#009` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
- Launch creates a new thread on the server and starts a run with input determined by the launch mode . Isolated mode sends only the task description. Fork mode also sends the parent’s effective conversation history. start_async_task returns the thread ID as the task ID.
```

片段[3] `oss__javascript__deepagents__async-subagents#015` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
- Launch creates a new thread on the server and starts a run with input determined by the launch mode . Isolated mode sends only the task description. Fork mode also sends the parent’s effective conversation history. start_async_task returns the thread ID as the task ID.
```

片段[4] `oss__python__deepagents__async-subagents#018` ｜ Async subagents ｜ Choose a launch mode

```text
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
```

片段[5] `oss__javascript__deepagents__async-subagents#030` ｜ Async subagents ｜ Choose a launch mode

```text
| Mode | Behavior |

| --- | --- |

| "isolated" (default) | Sends only the delegated task description. The subagent starts fresh with no knowledge of the parent’s conversation history. |

| "fork" | Sends a snapshot of the parent’s conversation at launch, followed by the task description. The subagent can use that context while working in the background. |
```

---

## v2-I-018（multi-hop）

**问题**：从 langchain-mcp-adapters 迁到 langchain.mcp 后，客户端类、列工具的调用方式、工具名前缀和错误处理分别变成什么？

**gold**：MultiServerMCPClient 换成 langchain.mcp 的 MCPAdapter；原来的 load_mcp_tools 改成 MCPAdapter 实例上的 list_tools；多 server 的 MCPConfig 或 ClientGroup 会自动加 server 与 tool 组成的下划线前缀；handle_tool_errors 标志被移除，行为固定为 isError=True 时返回 status 为 error 的 ToolMessage，传输失败则直接抛出。

**judge 分**：0.5　**拒答标记**：None

**回答**：

# 迁移到 langchain.mcp 后的变化

## 结论

**1. 客户端类**
`MultiServerMCPClient` 被替换为 `MCPAdapter` [3]。

**2. 列工具的调用方式**
`load_mcp_tools` 不再单独存在，改为使用 `MCPAdapter(...).list_tools()` [3]。

**3. 工具名前缀**
默认会给工具名加上服务器名前缀，格式为 `{server}_{tool}`（例如 `weather_get_forecast`），即使只有一个服务器也是如此；除非设置 `prefixToolNameWithServerName`。1.x 中该选项默认是 `false`，2.0 改为默认开启。若要保留 1.x 的名字，需设置 `prefixToolNameWithServerName: false`。`loadMcpTools` 仍默认 `false`。此外，`interruptOn` 审批规则也要改成带前缀的名字（例如 `delete_repo` 不再匹配 `github_delete_repo`）[7]。

**4. 错误处理**
给出的文档片段里**没有找到**关于错误处理（error handling）如何变化的内容，无法回答这一部分。

## 最小可用示例

```python
from langchain.mcp import MCPAdapter

async with MCPAdapter(target) as adapter:
    tools = await adapter.list_tools()
```

（示例结构参考 [9] 中的 `MCPAdapter(target)` + `adapter.list_tools()` 用法 [9]；导入路径参考 [3]。）

## 补充说明（与用户说法可能不一致之处）

- 用户问的是「客户端类」，但片段中 `MCPAdapter` 的用法是作为上下文管理器 `async with MCPAdapter(target) as adapter` [9]，并非直接对应 1.x 的 `MultiServerMCPClient` 构造方式；1.x 的 `MultiServerMCPClient({...})` 写法见 [10]，迁移后需按 `MCPAdapter` 的接口调整。
- 工具名相关参数在片段中写作 `prefixToolNameWithServerName` [7]，请以该名称为准。

**top5 片段**：

片段[1] `oss__javascript__migrate__langchain-mcp-adapters#000` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ ROOT

```text
Migrate to @langchain/mcp-adapters 2.0 Upgrade from @langchain/mcp-adapters 1.x to 2.0, covering renamed APIs, stricter configuration, authentication, elicitation, and tool result changes.
```

片段[2] `oss__python__migrate__langchain-mcp-adapters#014` ｜ Migrate from langchain-mcp-adapters ｜ Tool results

```text
| langchain-mcp-adapters | langchain.mcp |

| --- | --- |

| MCPToolArtifact (structured content) | Kept. Exported from langchain.mcp . See structured content . |

| Multimodal content blocks | Kept. See multimodal content . |

| Tool metadata | Extended. Grouped under an mcp namespace on the tool’s metadata, with annotations and server identity. See tool metadata . |

| convert_mcp_tool_to_langchain_tool | Renamed to as_langchain_tool , and now a coroutine: await as_langchain_tool(tool, client) . |

| to_fastmcp (LangChain tool → FastMCP tool) | No langchain.mcp equivalent yet. If you convert LangChain tools into MCP tools, open an issue — we would like to hear about the use case. |
```

片段[3] `oss__python__migrate__langchain-mcp-adapters#001` ｜ Migrate from langchain-mcp-adapters ｜ Import paths

```text
| langchain-mcp-adapters | langchain.mcp |

| --- | --- |

| from langchain_mcp_adapters.client import MultiServerMCPClient | from langchain.mcp import MCPAdapter |

| from langchain_mcp_adapters.tools import load_mcp_tools | from langchain.mcp import MCPAdapter (use MCPAdapter(...).list_tools() ) |

| from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool | from langchain.mcp import as_langchain_tool (renamed) |

| from langchain_mcp_adapters.tools import MCPToolArtifact | from langchain.mcp import MCPToolArtifact |
```

片段[4] `oss__python__migrate__langchain-mcp-adapters#000` ｜ Migrate from langchain-mcp-adapters ｜ ROOT

```text
Migrate from langchain-mcp-adapters Migrate from the standalone langchain-mcp-adapters package to the built-in langchain.mcp namespace.
```

片段[5] `oss__python__migrate__langchain-mcp-adapters#007` ｜ Migrate from langchain-mcp-adapters ｜ Connection configuration

```text
| langchain-mcp-adapters | langchain.mcp | | --- | --- | | StdioConnection | A Path target, or an MCPConfig entry with command / args . | | StreamableHttpConnection | An http / https URL target, or an MCPConfig entry with url . | | SSEConnection | Client(SSETransport(url)) , passed to MCPAdapter . Supported, but the transport is deprecated. See Deprecated transports . | | WebsocketConnection | No FastMCP transport. Migrate the server to Streamable HTTP. See Deprecated transports . | | httpx_client_factory | Set on a fastmcp transport. See shared connection pool . | | auth (per connection) | Set auth on a fastmcp.Client . See Authentication . |
```

---

## v2-I-019（multi-hop）

**问题**：错误处理表里用户可修的那类错误怎么暂停？人恢复时能给出哪些决策、各自语义是什么？

**gold**：用户可修错误（缺信息、指令不清）用 interrupt() 暂停等人工；恢复时可给的决策有 approve（按原参数执行）、edit（改参数再执行）、reject（跳过并把拒绝反馈给 agent）、respond（把人的话当合成工具结果、跳过执行）。

**judge 分**：0.5　**拒答标记**：None

**回答**：

## 结论

**1. 用户可修错误的暂停方式**

用户可修的错误（如缺少信息、指令不清）由人类修复，策略是「用 `interrupt()` 暂停」，对应 Human-in-the-loop 机制 [1][3][5][8]。

**2. 人恢复时能给出的决策**

给出的文档里**只明确出现了 `approve` 这一种决策类型**，示例中通过 `Command(resume={"decisions": [{"type": "approve"}]})` 恢复执行 [7]。代码注释里提到「approve, edit, or reject」三种决策 [7]，但**片段没有给出 `edit` 和 `reject` 的具体字段结构或各自语义说明**，因此无法根据现有片段回答它们的准确语义。

## 最小可用示例（来自片段 [7]）

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "fs-thread-1"}}

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Save the API key to /secrets/key.txt"}]},
    config=config,
)

if result.get("__interrupt__"):
    action = result["__interrupt__"][0].value["action_requests"][0]
    print(f"Approve {action['name']} on {action['args']}?")

    # Resume with the human decision (approve, edit, or reject).
    result = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,  # Same thread ID
    )
```

## 缺失说明

- 片段只展示了 `{"type": "approve"}` 的写法 [7]。
- `edit`、`reject` 的**具体参数结构（例如编辑时如何传新值、拒绝时如何附带理由）以及三者的精确语义差异**，给出的文档里没有找到能回答这个问题的内容。
- 另外注意：片段 [7] 的示例场景是「Filesystem permission interrupts（文件系统权限中断）」，属于权限审批场景；它是否与「用户可修错误」的中断完全同一套决策语义，片段未作说明，请以实际 API 文档为准。

**top5 片段**：

片段[1] `oss__python__deepagents__fault-tolerance#001` ｜ Fault tolerance ｜ Error handling strategies

```text
| Error type | Who fixes it | Strategy | Middleware or feature | | --- | --- | --- | --- | | Transient errors (network issues, rate limits) | System (automatic) | Retry with exponential backoff | ModelRetryMiddleware , ToolRetryMiddleware | | LLM-recoverable errors (tool failures, parsing issues) | LLM | Convert to error ToolMessage and let the model adjust | ToolErrorMiddleware | | Model refusals | System or developer | Fall back to another model, then catch the error | ModelFallbackMiddleware , ModelRefusalMiddleware | | User-fixable errors (missing information, unclear instructions) | Human | Pause with interrupt() | Human-in-the-loop |
```

片段[2] `oss__javascript__langgraph__thinking-in-graph-api#008` ｜ Thinking in the Graph API ｜ Step 4: Build your nodes > Handle errors appropriately

```text
| Error type | Who fixes it | Strategy | When to use | | --- | --- | --- | --- | | Transient errors (network issues, rate limits) | System (automatic) | Retry policy on the node | Temporary failures that usually resolve on retry | | LLM-recoverable errors (tool failures, parsing issues) | LLM | Store the error in state and route back | The model can adjust with more context | | User-fixable errors (missing information, unclear instructions) | Human | Pause with interrupt() | Need user input to proceed | | Recoverable failure after retries | Developer | error_handler (Python) / errorHandler (TypeScript) | Run a compensation branch after retry exhaustion |
```

片段[3] `oss__python__langgraph__thinking-in-graph-api#008` ｜ Thinking in the Graph API ｜ Step 4: Build your nodes > Handle errors appropriately

```text
| Error type | Who fixes it | Strategy | When to use | | --- | --- | --- | --- | | Transient errors (network issues, rate limits) | System (automatic) | Retry policy on the node | Temporary failures that usually resolve on retry | | LLM-recoverable errors (tool failures, parsing issues) | LLM | Store the error in state and route back | The model can adjust with more context | | User-fixable errors (missing information, unclear instructions) | Human | Pause with interrupt() | Need user input to proceed | | Recoverable failure after retries | Developer | error_handler (Python) / errorHandler (TypeScript) | Run a compensation branch after retry exhaustion |
```

片段[4] `oss__javascript__langgraph__fault-tolerance#032` ｜ Fault tolerance ｜ Recovery strategies

```text
| Strategy | Who fixes it | Mechanism |

| --- | --- | --- |

| Transient errors | System | Retry policy on the node |

| Recoverable failure after retries | Developer | error_handler / errorHandler (Saga / compensation) |

| LLM-recoverable errors | LLM | Store the error in state and route back with Command |

| User-fixable errors | Human | Pause with interrupt() |

| Unexpected errors | Developer | Let the exception bubble up and fail the run |
```

片段[5] `oss__python__langgraph__fault-tolerance#028` ｜ Fault tolerance ｜ Recovery strategies

```text
| Strategy | Who fixes it | Mechanism |

| --- | --- | --- |

| Transient errors | System | Retry policy on the node |

| Recoverable failure after retries | Developer | error_handler / errorHandler (Saga / compensation) |

| LLM-recoverable errors | LLM | Store the error in state and route back with Command |

| User-fixable errors | Human | Pause with interrupt() |

| Unexpected errors | Developer | Let the exception bubble up and fail the run |
```

---

## v2-I-020（multi-hop）

**问题**：多租户场景下，既要按用户隔离记忆、又要代用户调 GitHub，这两个地方该用哪个身份字段？

**gold**：记忆按用户隔离时官方推荐 user scope，namespace 用 (user_id)；代用户调用外部服务时用 langchain_auth 的 Client.authenticate，传 provider 为 github 和相应 scopes，并把 user_id 设为 runtime.server_info.user.identity，两处指向同一个人的身份。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：两个场景用的身份字段是同一个——`runtime.server_info.user.identity`（Python）/ `runtime.serverInfo.user.identity`（JavaScript）。

- 按用户隔离记忆：用 `StoreBackend` 的 namespace 工厂，按用户身份划分命名空间，即 `lambda rt: (rt.server_info.user.identity,)`，这样每个用户获得独立隔离的存储 [4]。
- 代用户调 GitHub：在工具里调用 `auth_client.authenticate(...)`，把 `user_id` 设为 `runtime.server_info.user.identity`，再用返回的 `auth_result.token` 代表该用户调用 GitHub API [1]；JavaScript 版本对应 `userId: runtime.serverInfo.user.identity` [2]。

最小可用示例（Python）：

```python
from deepagents.backends import StoreBackend
from langchain_auth import Client
from langchain.tools import tool, ToolRuntime

# 按用户隔离存储
backend = StoreBackend(
    namespace=lambda rt: (rt.server_info.user.identity,),
)

auth_client = Client()

@tool
async def github_action(runtime: ToolRuntime):
    """Perform an action on behalf of the user via GitHub."""
    auth_result = await auth_client.authenticate(
        provider="github",
        scopes=["repo", "read:org"],
        user_id=runtime.server_info.user.identity,
    )
    # Use auth_result.token for GitHub API calls on the user's behalf
```

补充说明（以片段为准的差异点）：
- 片段中 Python 的认证客户端来自 `langchain_auth` 的 `Client` [1]，JavaScript 的来自 `@langchain/auth` 的 `Client` [2]，两者包名不同，不要混用。
- 片段里没有出现 `user_id` 之外的“租户 ID / workspace ID”字段用于这两处；`server_info` 下片段明确展示的字段是 `user.identity`、`assistant_id`，以及 `execution_info` 下的 thread/run/checkpoint 信息 [4][16]。若你想按“组织/工作区”而非“用户”隔离，给出的文档里没有找到对应的身份字段说明。

**top5 片段**：

片段[1] `oss__python__deepagents__going-to-production#019` ｜ Going to production ｜ View example trace > Multi-tenancy > End-user credentials

```text
```

from langchain_auth import Client

from langchain.tools import tool, ToolRuntime



auth_client = Client()



# Inside your agent's tool:

@tool

async def github_action(runtime: ToolRuntime):

    """Perform an action on behalf of the user via GitHub."""

    auth_result = await auth_client.authenticate(

        provider="github",

        scopes=["repo", "read:org"],

        user_id=runtime.server_info.user.identity,

    )

    # Use auth_result.token for GitHub API calls on the user's behalf

```
```

片段[2] `oss__javascript__deepagents__going-to-production#020` ｜ Going to production ｜ View example trace > Multi-tenancy > End-user credentials

```text
```

import { Client } from "@langchain/auth";



const authClient = new Client();



// Inside your agent's tool:

// Access the authenticated user via runtime.serverInfo

const authResult = await authClient.authenticate({

  provider: "github",

  scopes: ["repo", "read:org"],

  userId: runtime.serverInfo.user.identity,

});

// Use authResult.token for GitHub API calls on the user's behalf

```
```

片段[3] `oss__javascript__langchain__middleware__custom#027` ｜ Custom middleware ｜ Custom context

```text
- Tenant/workspace context : Include organization-specific data for multi-tenant applications
```

片段[4] `oss__python__deepagents__backends#057` ｜ Backends ｜ Built-in backends > StoreBackend (LangGraph store) > Namespace factories

```text
```

from deepagents.backends import StoreBackend



# Per-user: each user gets their own isolated storage

backend = StoreBackend(

    namespace=lambda rt: (rt.server_info.user.identity,),

)



# Per-assistant: all users of the same assistant share storage

backend = StoreBackend(

    namespace=lambda rt: (

        rt.server_info.assistant_id,

    ),

)



# Per-thread: storage scoped to a single conversation

backend = StoreBackend(

    namespace=lambda rt: (

        rt.execution_info.thread_id,

    ),

)

```
```

片段[5] `oss__openwiki__providers#008` ｜ Model providers ｜ GitHub Copilot

```text
1. Select GitHub Copilot during openwiki --init . If you have an active GitHub CLI session, OpenWiki can reuse it. Otherwise, run gh auth login from the credential prompt.
```

---

## v2-I-021（paraphrase）

**问题**：把 agent 的长期笔记在对话过程中随手更新，和等对话结束之后再由另一个 agent 统一整理，两种做法各有什么代价？

**gold**：对话中更新：笔记立刻可用、对用户透明，但会增加延迟、要求 agent 一边干活一边整理；对话之间更新：没有用户可见延迟、还能跨多次对话综合，但笔记要到下一次对话才生效，而且需要第二个 agent。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 文档把这两种做法分别称为 **Hot path（对话过程中更新）** 和 **Background（对话之间后台整理）**，代价如下：

- **Hot path（对话中随手更新）**
  - 优点：记忆立即可用，对用户透明 [1][2]。
  - 代价：会增加延迟（adds latency），并且 agent 必须同时兼顾多任务（agent must multitask）[1][2]。
  - 补充：这是默认方式，agent 通常在回复用户前决定要记住哪些事实 [6][8]。

- **Background（对话结束后由另一个 agent 统一整理）**
  - 优点：没有用户可感知的延迟，且可以跨多次对话综合归纳 [1][2]。
  - 代价：记忆要到下一次对话才可用（Memories not available until next conversation），并且需要第二个 agent（requires a second agent）[1][2]。
  - 补充：更新会持久化并在下一次对话中可用 [6]。

**最小可用示例（Python，后台整理 agent 的检索工具片段）：**

```python
from datetime import datetime, timedelta, timezone
from deepagents import create_deep_agent
from langchain.tools import tool, ToolRuntime
from langgraph_sdk import get_client

sdk_client = get_client(url="<DEPLOYMENT_URL>")

@tool
async def search_recent_conversations(query: str, runtime: ToolRuntime) -> str:
    """Search this user's conversations updated in the last 6 hours."""
    user_id = runtime.server_info.user.identity
    since = datetime.now(timezone.utc) - timedelta(hours=6)
    threads = await sdk_client.threads.search(
        metadata={"user_id": user_id},
        sort_by="updated_at",
        sort_order="desc",
        limit=20,
    )
    conversations = []
    for thread in threads:
        ...
```

[9]

**术语差异提示：** 你问的是「长期笔记」，文档中的对应概念是 memory files，由内置 `edit_file` 工具更新；并且并非所有记忆都可写——开发者定义的 skills 和组织策略通常是只读的 [6]。

**top5 片段**：

片段[1] `oss__python__deepagents__memory#018` ｜ Memory ｜ Advanced usage > Background consolidation

```text
| Approach | Pros | Cons |

| --- | --- | --- |

| Hot path (during conversation) | Memories available immediately, transparent to user | Adds latency, agent must multitask |

| Background (between conversations) | No user-facing latency, can synthesize across multiple conversations | Memories not available until next conversation, requires a second agent |
```

片段[2] `oss__javascript__deepagents__memory#018` ｜ Memory ｜ Advanced usage > Background consolidation

```text
| Approach | Pros | Cons |

| --- | --- | --- |

| Hot path (during conversation) | Memories available immediately, transparent to user | Adds latency, agent must multitask |

| Background (between conversations) | No user-facing latency, can synthesize across multiple conversations | Memories not available until next conversation, requires a second agent |
```

片段[3] `oss__javascript__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[4] `oss__python__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[5] `oss__javascript__deepagents__memory#003` ｜ Memory ｜ How memory works

```text
3. Agent updates memory (optional). When the agent learns new information, it can use its built-in edit_file tool to update memory files. Updates can happen during the conversation (the default) or in the background between conversations via background consolidation . Changes are persisted and available in the next conversation. Not all memory is writable: developer-defined skills and organization policies are typically read-only. See read-only vs writable memory for details.
```

---

## v2-I-022（paraphrase）

**问题**：哪个内置文件工具能一次删掉整个目录及其内容？它有什么版本要求？

**gold**：delete 工具，既能删单个文件，也能递归删除目录及其内容；该工具要求 deepagents>=0.7。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 内置的 `delete` 工具可以删除文件，或递归删除一个目录及其内容 [2]。该工具要求 `deepagents>=0.7` [2]。

**补充说明：**
- 在 v0.7.0 的变更日志中，`delete` 被描述为「New delete tool removes a file or recursively removes a directory」[1]。
- 在自定义后端场景下，`delete` 属于可选能力：如果后端不支持删除，该工具会在请求时自动对模型隐藏 [4]。

**最小可用示例（来自文档片段的自定义工具写法，非内置 delete 的直接调用示例）：**

```python
from langchain.tools import tool
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

@tool
def remove_file(path: str) -> str:
    """Delete a file from the filesystem."""
    return f"Deleted {path}"

# Checkpointer is REQUIRED for human-in-the-loop
checkpointer = MemorySaver()
agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    tools=[remove_file],
    interrupt_on={
        "remove_file": True,  # Default:
    },
)
```

注：上面示例是文档中 human-in-the-loop 的自定义 `remove_file` 工具写法 [6][7][8]，并非内置 `delete` 工具的调用示例；片段中未给出内置 `delete` 的直接调用代码。

**top5 片段**：

片段[1] `oss__python__releases__changelog#019` ｜ Changelog ｜ deepagents v0.7.0 > Features

```text
- Filesystem tools : New delete tool removes a file or recursively removes a directory ( #3659 , #3851 ); write_file now overwrites an existing file instead of erroring ( #4109 ); FilesystemMiddleware accepts a tool allowlist to expose only selected built-in tools ( #4325 , #4698 ); and reads and searches are tuned for open models — paginated read_file reports total and remaining lines plus the next offset ( #4540 ), grep / glob return partial results with a truncated flag instead of hanging on large trees ( #4063 ), and grep gains a 1,000-match cap with streamed output and optional context lines ( #4570 , #4706 ).
```

片段[2] `oss__python__deepagents__tools#022` ｜ Tools ｜ Built-in harness tools

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

片段[3] `oss__python__deepagents__sandboxes#000` ｜ Sandboxes ｜ ROOT

```text
- All standard filesystem tools ( ls , read_file , write_file , edit_file , delete , glob , grep )
```

片段[4] `oss__python__deepagents__backends#089` ｜ Backends ｜ Custom backends > Implement the backend protocol

```text
| None, glob: str | | delete | (file_path: str) -> DeleteResult | Optional. Remove a file or, recursively, a directory. If the backend does not support deletion, the tool is automatically hidden from the model at request time. |
```

片段[5] `oss__python__deepagents__human-in-the-loop#011` ｜ Human-in-the-loop ｜ Basic configuration

```text
``` from langchain.tools import tool from deepagents import create_deep_agent from langgraph.checkpoint.memory import MemorySaver @tool def remove_file(path: str) -> str: """Delete a file from the filesystem.""" return f"Deleted {path}" @tool def fetch_file(path: str) -> str: """Read a file from the filesystem.""" return f"Contents of {path}" @tool def notify_email(to: str, subject: str, body: str) -> str: """Send an email.""" return f"Sent email to {to}" # Checkpointer is REQUIRED for human-in-the-loop checkpointer = MemorySaver() agent = create_deep_agent( model="fireworks:accounts/fireworks/models/glm-5p2", tools=[remove_file, fetch_file, notify_email], interrupt_on={ "remove_file":
```

---

## v2-I-023（paraphrase）

**问题**：一个数据分析 bot 希望每次对话都从干净环境开始，而编码助手要跨对话保留已克隆的仓库——执行环境的生命周期该怎么选？

**gold**：前者用 thread-scoped：沙箱 id 存在 thread metadata 里，每次对话新建、按 TTL 清理；后者用 assistant-scoped：id 存在 assistant config 里，所有对话共享同一个沙箱。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 按 sandbox 的 scope 来选——数据分析 bot 用 **Thread-scoped**（每个对话新建、TTL 到期清理），编码助手用 **Assistant-scoped**（所有对话共享同一个 sandbox）[1][2]。

具体对应关系（片段表格原文）：

| Scope | Sandbox ID 存放位置 | 生命周期 | 示例场景 |
| --- | --- | --- | --- |
| Thread-scoped | Thread metadata | 每个对话新建，TTL 到期清理 | 每次对话都从干净状态开始的数据分析 bot [1][2] |
| Assistant-scoped | Assistant config | 所有对话共享 | 跨对话保留已克隆仓库的编码助手 [1][2] |

也就是说，你描述的两个场景正好就是文档表格里给出的两个示例用例，直接按上表选即可 [1][2]。

**最小可用示例（Python，Thread-scoped 思路）：** 用 `thread_id` 拼出 sandbox 名称，已存在则复用、不存在则创建，并设置 `idle_ttl_seconds` 作为空闲清理的 TTL [10]：

```python
from deepagents import create_deep_agent
from deepagents.backends.langsmith import LangSmithSandbox
from langchain_core.runnables import RunnableConfig
from langsmith.sandbox import SandboxClient

client = SandboxClient()

async def agent(config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    sandbox_name = f"thread-{thread_id}"
    existing = [
        sb for sb in client.list_sandboxes()
        if getattr(sb, "name", None) == sandbox_name
    ]
    if existing:
        ls_sandbox = existing[0]
    else:
        ls_sandbox = client.create_sandbox(
            name=sandbox_name,
            idle_ttl_seconds=3600,  # TTL: clean up when idle
        )
    return create_deep_agent(
        model="google_genai:gemini-4-hydrogen",
        # ...
    )
```

**需要指出的差异/限制：**
- 片段只给出了 Thread-scoped 的代码示例（按 `thread_id` 命名 sandbox）[10]，**没有给出 Assistant-scoped 的具体实现代码**；若要跨对话共享，需按表格把 sandbox ID 存到 Assistant config 中 [1][2]，但片段未展示该写法。
- 片段 [10] 的示例本身是 Thread-scoped 的写法，不能直接用于“跨对话保留仓库”的编码助手场景。
- 另外，片段 [9] 提到 `CompositeBackend` 可混合使用：默认 thread-scoped 临时空间 + 对 `/memories/` 等特定路径做跨线程路由 [9]，但这属于文件系统后端选项，不是 sandbox 生命周期选择本身。

**top5 片段**：

片段[1] `oss__javascript__deepagents__going-to-production#037` ｜ Going to production ｜ Execution environment > Sandboxes > Lifecycle

```text
| Scope | Sandbox ID stored on | Lifecycle | Example use case |

| --- | --- | --- | --- |

| Thread-scoped | Thread metadata | Fresh per conversation, cleaned up on TTL | A data analysis bot where each conversation starts clean |

| Assistant-scoped | Assistant config | Shared across all conversations | A coding assistant that maintains a cloned repo across conversations |
```

片段[2] `oss__python__deepagents__going-to-production#037` ｜ Going to production ｜ Execution environment > Sandboxes > Lifecycle

```text
| Scope | Sandbox ID stored on | Lifecycle | Example use case |

| --- | --- | --- | --- |

| Thread-scoped | Thread metadata | Fresh per conversation, cleaned up on TTL | A data analysis bot where each conversation starts clean |

| Assistant-scoped | Assistant config | Shared across all conversations | A coding assistant that maintains a cloned repo across conversations |
```

片段[3] `oss__javascript__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[4] `oss__python__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[5] `oss__javascript__langchain__context-engineering#050` ｜ Context engineering in agents ｜ Best practices

```text
6. Understand transient vs persistent : Model context changes are transient (per-call), while life-cycle context changes persist to state
```

---

## v2-I-024（paraphrase）

**问题**：deepagents v0.7.0 精简默认提示词之后，工具说明和一次默认对话输入的用量分别下降了多少？

**gold**：工具描述总量降 43%（4,005 → 2,302）；叠加默认 base prompt 为空和 todos 改为 opt-in，默认 agent 单轮输入降 65%（5,395 → 1,895）。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：deepagents v0.7.0 精简默认提示词后，工具说明（tool description）token 总量下降 43%（4,005 → 2,302）；默认 agent 单轮对话的输入 token 下降 65%（5,395 → 1,895）[1]。工具行为不变 [1]。

最小示例（片段中无代码，仅示意数据）：

```text
tool description tokens: 4,005 → 2,302  (-43%)
default-agent turn input tokens: 5,395 → 1,895  (-65%)
```

补充说明：片段 [1] 提到该降幅是「空基础提示词 + 可选 todos」共同作用的结果，其中 todos 默认不再启用（需通过 `middleware=[TodoListMiddleware()]` 恢复）[4]。

**top5 片段**：

片段[1] `oss__python__releases__changelog#017` ｜ Changelog ｜ deepagents v0.7.0 > Optimizations

```text
- Lean prompts by default : The authored base prompt starts empty and tool-usage prose that duplicated tool schemas has been trimmed. Isolated to the default agent’s tool schemas, total description tokens drop 43% (4,005 → 2,302); combined with the empty base prompt and opt-in todos, a default-agent turn’s input tokens drop 65% (5,395 → 1,895). Tool behavior is unchanged. ( #4859 , #4979 , #5009 )
```

片段[2] `oss__python__deepagents__context-engineering#048` ｜ Context engineering in Deep Agents ｜ Summarization > Offloading

```text
1. Tool call inputs exceed 20,000 tokens : File write and edit operations leave behind tool calls containing the complete file content in the agent’s conversation history. Since this content is already persisted to the filesystem, it’s often redundant. As the session context crosses 85% of the model’s available window, deep agents truncate older tool calls, replacing them with a pointer to the file on disk and reducing the size of the active context.
```

片段[3] `oss__javascript__deepagents__context-engineering#044` ｜ Context engineering in Deep Agents ｜ Summarization > Offloading

```text
1. Tool call inputs exceed 20,000 tokens : File write and edit operations leave behind tool calls containing the complete file content in the agent’s conversation history. Since this content is already persisted to the filesystem, it’s often redundant. As the session context crosses 85% of the model’s available window, deep agents truncate older tool calls, replacing them with a pointer to the file on disk and reducing the size of the active context.
```

片段[4] `oss__python__releases__changelog#022` ｜ Changelog ｜ deepagents v0.7.0 > Breaking changes

```text
- Planning todos are opt-in : create_deep_agent no longer includes TodoListMiddleware by default, so the write_todos tool, todos state channel, and todo-planning prompt are absent unless restored with middleware=[TodoListMiddleware()] . (The OpenAI Codex harness profile still opts in automatically.) ( #4929 )
```

片段[5] `oss__python__deepagents__customization#212` ｜ Customize Deep Agents ｜ Memory

```text
``` from deepagents import create_deep_agent from deepagents.backends import FilesystemBackend from langgraph.checkpoint.memory import MemorySaver # Checkpointer is REQUIRED for human-in-the-loop checkpointer = MemorySaver() agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", backend=FilesystemBackend(root_dir="/Users/user/{project}"), memory=[ "./AGENTS.md" ], interrupt_on={ "write_file": True,  # Default: approve, edit, reject "read_file": False,  # No interrupts needed "edit_file": True,   # Default: approve, edit, reject }, checkpointer=checkpointer,  # Required! ) result = agent.invoke( { "messages": [ { "role": "user", "content":
```

---

## v2-I-025（no-answer）

**问题**：create_deep_agent 的 memory_backend 参数支持哪些后端，可以传 redis 吗？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺失的信息：
- 所有片段中都没有出现 `memory_backend` 这个参数名。片段里出现的相关参数是 `backend`（如 [1][2][3][4][5]）和 `memory`（如 [4]），没有 `memory_backend`。
- 片段中出现的后端类型只有 `StoreBackend` [1][2][4][5]、`ContextHubBackend` [3]、`StateBackend` [4][5]、`CompositeBackend` [4][5]，没有任何关于 Redis 后端的说明，也没有列出后端支持的完整清单。

因此无法确认 `memory_backend` 是否存在、支持哪些后端，以及能否传 Redis。建议查阅 deepagents 的 Backends 文档页（https://docs.langchain.com/oss/python/deepagents/customization）以获取完整后端列表。

**top5 片段**：

片段[1] `oss__python__deepagents__customization#129` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="fireworks:accounts/fireworks/models/glm-5p2",

    backend=StoreBackend(

        namespace=lambda rt: (rt.server_info.user.identity,),

    ),

    store=InMemoryStore(),  # Good for local dev; omit for LangSmith Agent Server

)

```
```

片段[2] `oss__python__deepagents__customization#126` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    backend=StoreBackend(

        namespace=lambda rt: (rt.server_info.user.identity,),

    ),

    store=InMemoryStore(),  # Good for local dev; omit for LangSmith Agent Server

)

```
```

片段[3] `oss__python__deepagents__customization#133` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import ContextHubBackend



agent = create_deep_agent(

    model="openai:gpt-6.1-sol",

    backend=ContextHubBackend("my-agent"),

)

```
```

片段[4] `oss__python__deepagents__customization#125` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import StoreBackend

from langgraph.store.memory import InMemoryStore



agent = create_deep_agent(

    model="google_genai:gemini-4-hydrogen",

    backend=StoreBackend(

        namespace=lambda rt: (rt.server_info.user.identity,),

    ),

    store=InMemoryStore(),  # Good for local dev; omit for LangSmith Agent Server

)

```
```

片段[5] `oss__python__deepagents__customization#134` ｜ Customize Deep Agents ｜ Backends

```text
```

from deepagents import create_deep_agent

from deepagents.backends import ContextHubBackend



agent = create_deep_agent(

    model="anthropic:claude-sonnet-5",

    backend=ContextHubBackend("my-agent"),

)

```
```

---

## v2-I-026（no-answer）

**问题**：deepagents 有没有 subagent_max_depth 这类配置，用来限制子 agent 的嵌套层数？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

片段中只展示了 `createDeepAgent` 的以下配置项：`model`、`tools`、`backend`、`systemPrompt`、`subagents` [1][2][5][6][7][9]，以及子 agent 对象里的 `name`、`description`、`systemPrompt` [1][2][5][6][7][9]。没有任何片段提到 `subagent_max_depth` 或类似的嵌套层数限制参数。

缺失的信息是：`createDeepAgent` 的完整配置项列表（或 subagent 相关配置的 API 参考），以确认是否存在限制子 agent 嵌套深度的选项。

**top5 片段**：

片段[1] `oss__javascript__deepagents__rag#049` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
``` import { createDeepAgent } from "deepagents"; const maxConcurrentAnalysts = 3; const instructions = RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=".repeat(80) + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.replace( "{max_concurrent_analysts}", String(maxConcurrentAnalysts), ); const chunkAnalystSubagent = { name: "chunk-analyst", description: "Analyze one retrieved documentation chunk file. Pass the user question and a single file path under /retrieved/.", systemPrompt: CHUNK_ANALYST_INSTRUCTIONS, }; const agent = createDeepAgent({ model: "google:gemini-4-hydrogen", tools: [searchDocumentation], backend, systemPrompt: instructions, subagents: [chunkAnalystSubagent], }); ```
```

片段[2] `oss__javascript__deepagents__rag#052` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
``` import { createDeepAgent } from "deepagents"; const maxConcurrentAnalysts = 3; const instructions = RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=".repeat(80) + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.replace( "{max_concurrent_analysts}", String(maxConcurrentAnalysts), ); const chunkAnalystSubagent = { name: "chunk-analyst", description: "Analyze one retrieved documentation chunk file. Pass the user question and a single file path under /retrieved/.", systemPrompt: CHUNK_ANALYST_INSTRUCTIONS, }; const agent = createDeepAgent({ model: "openrouter:z-ai/glm-5.2", tools: [searchDocumentation], backend, systemPrompt: instructions, subagents: [chunkAnalystSubagent], }); ```
```

片段[3] `oss__javascript__deepagents__rag#053` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
``` import { createDeepAgent } from "deepagents"; const maxConcurrentAnalysts = 3; const instructions = RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=".repeat(80) + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.replace( "{max_concurrent_analysts}", String(maxConcurrentAnalysts), ); const chunkAnalystSubagent = { name: "chunk-analyst", description: "Analyze one retrieved documentation chunk file. Pass the user question and a single file path under /retrieved/.", systemPrompt: CHUNK_ANALYST_INSTRUCTIONS, }; const agent = createDeepAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", tools: [searchDocumentation], backend, systemPrompt: instructions, subagents: [chunkAnalystSubagent], }); ```
```

片段[4] `oss__javascript__deepagents__rag#051` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
``` import { createDeepAgent } from "deepagents"; const maxConcurrentAnalysts = 3; const instructions = RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=".repeat(80) + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.replace( "{max_concurrent_analysts}", String(maxConcurrentAnalysts), ); const chunkAnalystSubagent = { name: "chunk-analyst", description: "Analyze one retrieved documentation chunk file. Pass the user question and a single file path under /retrieved/.", systemPrompt: CHUNK_ANALYST_INSTRUCTIONS, }; const agent = createDeepAgent({ model: "anthropic:claude-sonnet-5", tools: [searchDocumentation], backend, systemPrompt: instructions, subagents: [chunkAnalystSubagent], }); ```
```

片段[5] `oss__javascript__langgraph__event-streaming#025` ｜ Event streaming ｜ Related

```text
- Deep Agents streaming covers subagents, nested messages, and subagent tool calls.
```

---

## v2-I-027（no-answer）

**问题**：DSPy 的 BootstrapFewShot 优化器该怎么和 LangChain 的 create_agent 配合使用？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

现有片段只覆盖了 `create_agent` / `createAgent` 的基本用法（模型字符串、`tools`、`checkpointer`、`MCPAdapter`、`create_deep_agent` 等）[1][2][3][4][5][6][7][8]，以及前端 `useStream` 的用法 [13][14]，完全没有提到 DSPy、`BootstrapFewShot` 优化器，也没有任何关于把外部优化器与 `create_agent` 组合的说明。

缺少的内容包括：
- DSPy 与 LangChain 的集成方式（是否存在官方适配层）；
- `BootstrapFewShot` 的输入输出契约，以及如何把 `create_agent` 包装成 DSPy 可优化的模块；
- 优化后的 few-shot 示例如何注入到 agent 的 prompt 中。

因此无法根据这些片段给出结论或示例，也不做推测。

**top5 片段**：

片段[1] `oss__python__langchain__agents#005` ｜ Agents ｜ ROOT

```text
```

from langchain.agents import create_agent



agent = create_agent(model="fireworks:accounts/fireworks/models/glm-5p2", tools=tools)

```
```

片段[2] `oss__python__langchain__agents#012` ｜ Agents ｜ Core components > Model

```text
```

from langchain.agents import create_agent



agent = create_agent(model="fireworks:accounts/fireworks/models/glm-5p2", tools=tools)

```
```

片段[3] `oss__python__langchain__frontend__overview#002` ｜ Overview ｜ Why use the LangChain frontend SDKs?

```text
```

from langchain.agents import create_agent

from langgraph.checkpoint.memory import MemorySaver



agent = create_agent(

    model="openai:gpt-6.1-sol",

    tools=[get_weather, search_web],

    checkpointer=MemorySaver(),

)

```
```

片段[4] `oss__javascript__langchain__agents#012` ｜ Agents ｜ Core components > Model

```text
```

import { createAgent } from "langchain";



var agent = createAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", tools });

```
```

片段[5] `oss__javascript__langchain__agents#005` ｜ Agents ｜ ROOT

```text
```

import { createAgent } from "langchain";



var agent = createAgent({ model: "fireworks:accounts/fireworks/models/glm-5p2", tools });

```
```

---

## v2-I-028（no-answer）

**问题**：Haystack 的 Pipeline.run 里 max_loops 参数设多少合适？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

缺少的信息：这些片段全部来自 LangChain / LangGraph 文档，没有任何片段提到 Haystack，也没有提到 `Pipeline.run` 或 `max_loops` 参数。片段 [5] 只提到 LangGraph 图可以用「recursion limit」限制循环次数，但那是 LangGraph 的概念，不是 Haystack 的 `max_loops`，不能据此推断 Haystack 的参数取值。

**top5 片段**：

片段[1] `oss__python__langgraph__frontend__graph-execution#008` ｜ Graph execution ｜ Building the pipeline progress bar

```text
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
```

片段[2] `oss__javascript__langgraph__frontend__graph-execution#008` ｜ Graph execution ｜ Building the pipeline progress bar

```text
``` function PipelineProgress({ nodes, isLoading, }: { nodes: SubgraphDiscoverySnapshot[]; isLoading: boolean; }) { const firstIncompleteIdx = nodes.findIndex((node) => node.status !== "complete"); return ( <div className="flex items-center gap-1"> {nodes.map((node, i) => { const isRunning = isLoading && node.status !== "complete" && firstIncompleteIdx === i; const colors = { pending: "bg-gray-200 text-gray-500", running: "bg-blue-400 text-white animate-pulse", complete: "bg-green-500 text-white", error: "bg-red-500 text-white", }; const status = isRunning ? "running" : node.status; return ( <div key={node.id} className="flex items-center"> <div
```

片段[3] `oss__python__langchain__models#031` ｜ Models ｜ Invocation > Batch

```text
```

model.batch(

    list_of_inputs,

    config={

        'max_concurrency': 5,  # Limit to 5 parallel calls

    }

)

```
```

片段[4] `oss__python__langchain__models#052` ｜ Models ｜ Advanced topics > Model profiles

```text
```

model.profile

# {

#   "max_input_tokens": 400000,

#   "image_inputs": True,

#   "reasoning_output": True,

#   "tool_calling": True,

#   ...

# }

```
```

片段[5] `oss__javascript__langgraph__use-graph-api#004` ｜ Build checklist for the Graph API ｜ Build your graph

```text
- Loop : Cycle until a termination condition, or cap runs with a recursion limit .
```

---
