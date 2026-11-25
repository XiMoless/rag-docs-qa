# 审计材料 7/8（30 条，明细文件第 181–210 行）

## v2-G-025（paraphrase）

**问题**：一个技能目录里那份说明文件，头部元信息哪些是必须写的？名字有什么格式限制？

**gold**：必填的是 name 与 description。name 只能用小写字母数字加连字符，长度 1-64，并且必须与所在父目录同名。description 要写清这个技能做什么、什么时候用，上限 1,024 个字符。其余如 license、compatibility、metadata、allowed-tools 都是可选项。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 说明文件（`SKILL.md`）的 frontmatter 中，**必填字段只有两个：`name` 和 `description`** [5][6]。其中 `name` 的格式限制为：小写字母数字加连字符，长度 1–64 个字符，且必须与父目录名一致 [5][6]。

**必填字段说明：**

| 字段 | 是否必填 | 限制 |
| --- | --- | --- |
| `name` | 是 | 小写字母数字加连字符，1–64 字符，必须匹配父目录名 [5][6] |
| `description` | 是 | 描述技能做什么、何时使用，最多 1,024 字符 [5][6] |

**可选字段：** `license`、`compatibility`（最多 500 字符）、`metadata`、`allowed-tools`（空格分隔的预批准工具列表，实验性）[5][6]。

**补充：** 排查技能启动时缺失的问题时，文档也强调要校验 frontmatter，`name` 必须与父目录名匹配并符合 Agent Skills 规范，可用 `skills-ref` 校验工具检查格式 [1][2]。

**最小可用示例**（仅含必填字段）：

```yaml
---
name: langgraph-docs
description: Use this skill for requests related to LangGraph in order to fetch relevant documentation to provide accurate, up-to-date guidance.
---
```

（完整示例还包含 `license`、`compatibility`、`metadata`、`allowed-tools` 等可选字段 [15]。）

**top5 片段**：

片段[1] `oss__python__deepagents__skills#125` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
3. Validate SKILL.md frontmatter . The name must match the parent directory name and follow the Agent Skills specification . Use the skills-ref validation tool to check formatting.
```

片段[2] `oss__javascript__deepagents__skills#125` ｜ Skills ｜ Troubleshooting > Skills missing at startup

```text
2. Validate SKILL.md frontmatter . The name must match the parent directory name and follow the Agent Skills specification . Use the skills-ref validation tool to check formatting.
```

片段[3] `oss__python__deepagents__skills#006` ｜ Skills ｜ How skills work

```text
| Level | What loads | When |

| --- | --- | --- |

| 1. Metadata | name and description from SKILL.md frontmatter | Agent startup, for every configured skill |

| 2. Instructions | Full SKILL.md body | When the skill is invoked |

| 3. Resources | Supporting files under scripts/ , references/ , and assets/ | As needed after invocation, when the instructions reference them |
```

片段[4] `oss__javascript__deepagents__skills#006` ｜ Skills ｜ How skills work

```text
| Level | What loads | When |

| --- | --- | --- |

| 1. Metadata | name and description from SKILL.md frontmatter | Agent startup, for every configured skill |

| 2. Instructions | Full SKILL.md body | When the skill is invoked |

| 3. Resources | Supporting files under scripts/ , references/ , and assets/ | As needed after invocation, when the instructions reference them |
```

片段[5] `oss__python__deepagents__skills#136` ｜ Skills ｜ Reference > Frontmatter fields

```text
| Field | Required | Description |

| --- | --- | --- |

| name | Yes | Lowercase alphanumeric with hyphens, 1-64 characters. Must match the parent directory name. |

| description | Yes | What the skill does and when to use it. Max 1,024 characters. |

| license | No | License name or reference to a bundled license file. |

| compatibility | No | Environment requirements (system packages, network access). Max 500 characters. |

| metadata | No | Arbitrary key-value pairs for additional properties. |

| allowed-tools | No | Space-separated list of pre-approved tools the skill can use. Experimental. |
```

---

## v2-G-026（paraphrase）

**问题**：我让一个助手接着当前这轮对话继续排查，而不是只丢给它一句任务描述；这样接手之后它还能再把活分包给别的助手吗？

**gold**：这种继承上下文的做法对应 Forked 模式：它拿到父级有效的 conversation history 与继承来的 state，外加任务描述，还可以追加 systemPrompt，但追加会降低 cache reuse。代价是不能再用 task 工具，必须自己把活干完；isolated 默认模式才允许用 task 再分包。另外技能与父级 base prompt 也随继承而来。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不能。** 如果让子代理以「继承父级对话」的方式接手（fork 模式），它就无法再调用 `task` 工具把活分包给其他子代理，必须自己把活干完 [3]。

具体差异如下：

- **默认 isolated 模式**：子代理只看到你传入的任务描述，但可以使用 `task` 工具调用其他子代理 [3]。
- **fork 模式**：子代理会继承父级的有效对话历史和继承状态，以及任务描述；但它**不能使用 `task`**，必须自己完成工作 [3]。fork 模式适合「继续父级已经开始的调查」这类场景 [3]。
- 另外，fork 模式下子代理会继承技能和父级的基础 prompt；可选的 `system_prompt` 会随任务消息一起传递，以保留缓存复用 [3]。字典式自定义子代理的 `mode` 参数取值为 `"isolated" | "fork"`，默认是 `"isolated"` [4]。

所以你的需求（接着当前对话继续排查）对应 fork 模式，代价就是失去再分包的能力；若需要继续分包，应改用 isolated 模式并显式传入足够的上下文。

最小可用示例（Python，字典式子代理配置）：

```python
subagents = [{
    "name": "investigator",
    "description": "Continues the parent's investigation",
    "system_prompt": "Continue the investigation from the inherited conversation.",
    "mode": "fork",  # 继承父级对话与系统提示；此模式下不能用 task 再分包
}]
```

补充说明：片段 [1][2] 只提到「主代理维护对话上下文，但子代理每次都是全新开始」，这与 fork 模式的描述存在表述差异——按规则以片段为准，fork 模式确实会继承父级对话历史 [3]，而 [1][2] 描述的是默认/非 fork 情形。

**top5 片段**：

片段[1] `oss__javascript__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[2] `oss__python__langchain__multi-agent#011` ｜ Multi-agent ｜ Performance comparison > Repeat request

```text
- The main agent maintains conversation context, but subagents start fresh each time
```

片段[3] `oss__python__deepagents__subagents#030` ｜ Subagents ｜ View example trace > When to use forking

```text
| Dimension | Isolated (default) | Forked |

| --- | --- | --- |

| Context | Only the task description you pass in | The parent’s effective conversation history and inherited state, plus the task description |

| System prompt and skills | You set them on the subagent | Inherits skills and the parent’s base prompt. An optional system_prompt is delivered with the task message to preserve cache reuse. |

| Calling other subagents | Can use the task tool | Cannot use task ; must finish the work itself |

| Best for | Focused work that needs little prior context | Continuing an investigation the parent has already started |
```

片段[4] `oss__python__deepagents__subagents#003` ｜ Subagents ｜ Custom subagents > SubAgent (Dictionary-based)

```text
nts must define their own. Include tool usage guidance and output format requirements. Does not inherit from main agent. For mode: "fork" , the fork keeps the parent’s system prompt unchanged and delivers these instructions with the task message after the inherited conversation, preserving the parent’s cached prompt prefix. See Forked subagents . | | mode | "isolated" \| "fork" | Optional. Context mode. Defaults to "isolated" , where the subagent only sees the delegated task. Set to "fork" to inherit the parent’s conversation and system prompt instead. See Forked subagents . | | tools | list[Callable] | Optional. Tools the subagent can use. Keep this minimal and include only what’s needed.
```

片段[5] `oss__python__deepagents__async-subagents#011` ｜ Async subagents ｜ Use the async subagent tools > Understand the lifecycle

```text
- Update creates a new run on the same thread. By default it interrupts the previous run, and the subagent restarts with the full conversation history plus the new instructions. The task ID stays the same.
```

---

## v2-G-027（no-answer）

**问题**：Haystack 那种用 YAML 声明组件和连线的 pipeline，在本库里对应的写法是什么？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

缺少的信息：文档片段中没有关于「用 YAML 声明组件和连线（component + connection）的 pipeline」这一概念的说明。片段 [1][2][9][10][11][12] 讲的是 deepagents 的 **HarnessProfile**（从 YAML 加载 profile 配置，如 `base_system_prompt`、`excluded_tools`、`excluded_middleware` 等），这是代理运行配置，不是组件编排/连线式的 pipeline 声明；片段 [4][5] 是前端 `useStream` 消费图流的用法；片段 [6] 是语音 agent 的代码式流串联；片段 [3][13][14] 是 OpenWiki 的 CI 工作流配置。这些都不涉及「YAML 声明组件与连线」的等价写法。

另外提示一处可能的名称差异：你提到的「Haystack」在本库文档片段中未出现，片段里也没有任何把该库的 pipeline 与 Haystack 做类比的表述，因此无法据此给出对应写法。

**top5 片段**：

片段[1] `oss__python__deepagents__profiles#014` ｜ Profiles ｜ Load profiles from config files

```text
```

import yaml

from deepagents import HarnessProfileConfig, register_harness_profile



with open("openai.yaml") as f:

    register_harness_profile(

        "openai",

        HarnessProfileConfig.from_dict(yaml.safe_load(f)),

    )

```
```

片段[2] `oss__javascript__deepagents__profiles#010` ｜ Profiles ｜ Load profiles from config files

```text
```

import { readFileSync } from "fs";

import YAML from "yaml";

import { parseHarnessProfileConfig, registerHarnessProfile } from "deepagents";



const raw = YAML.parse(readFileSync("profile.yaml", "utf-8"));

registerHarnessProfile("openai", parseHarnessProfileConfig(raw));

```
```

片段[3] `oss__openwiki__automate-updates#001` ｜ Automate updates ｜ Add a workflow

```text
| Provider | Example | Destination |

| --- | --- | --- |

| GitHub Actions | openwiki-update.yml | .github/workflows/openwiki-update.yml |

| GitLab CI | openwiki-update.gitlab-ci.yml | .gitlab-ci.yml , or include it from an existing pipeline |

| Bitbucket Pipelines | openwiki-update.bitbucket-pipelines.yml | bitbucket-pipelines.yml , then schedule the openwiki-update custom pipeline |
```

片段[4] `oss__javascript__langgraph__frontend__overview#001` ｜ Overview ｜ Architecture

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

片段[5] `oss__python__langgraph__frontend__overview#001` ｜ Overview ｜ Architecture

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

---

## v2-G-028（no-answer）

**问题**：AutoGen 里多个 agent 轮流发言的 GroupChat 编排，本库是怎么配置的？

**gold**：本题无答案

**judge 分**：None　**拒答标记**：1.0

**回答**：

给出的文档里没有找到能回答这个问题的内容。

缺少的信息：这些片段里没有任何关于 AutoGen、GroupChat、多个 agent 轮流发言（round-robin / speaker selection）编排方式的配置说明。片段只涉及 deepagents 的 `create_deep_agent`（含 `subagents` 参数）[1][8]、LangChain `create_agent` 的调用与 `thread_id` 会话续接 [4][5][6]、子 agent 作为工具包装 [10]，以及“主 agent 可在单轮内并行调用多个子 agent”这一特性 [2][3]，并未描述轮流发言式的群聊编排。

另外需指出一处名称差异：片段中出现的 API 是 `create_deep_agent` [1][5][6] 和 `create_agent` [4][10]，没有出现 AutoGen 的 `GroupChat` 或 `GroupChatManager` 相关配置。

**top5 片段**：

片段[1] `oss__python__deepagents__rag#063` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
``` from deepagents import create_deep_agent from langchain.chat_models import init_chat_model max_concurrent_analysts = 3 INSTRUCTIONS = ( RAG_WORKFLOW_INSTRUCTIONS + "\n\n" + "=" * 80 + "\n\n" + SUBAGENT_DELEGATION_INSTRUCTIONS.format( max_concurrent_analysts=max_concurrent_analysts, ) ) chunk_analyst_subagent = { "name": "chunk-analyst", "description": ( "Analyze one retrieved documentation chunk file. " "Pass the user question and a single file path under /retrieved/." ), "system_prompt": CHUNK_ANALYST_INSTRUCTIONS, } model = init_chat_model(model="google_genai:gemini-4-hydrogen") agent = create_deep_agent( model=model, tools=[search_documentation], backend=backend,
```

片段[2] `oss__javascript__langchain__multi-agent__subagents#001` ｜ Subagents ｜ Key characteristics

```text
- Parallel execution: The main agent can invoke multiple subagents in a single turn
```

片段[3] `oss__python__langchain__multi-agent__subagents#001` ｜ Subagents ｜ Key characteristics

```text
- Parallel execution: The main agent can invoke multiple subagents in a single turn
```

片段[4] `oss__python__langchain__agents#044` ｜ Agents ｜ Invocation

```text
```

from langchain.agents import create_agent

from langchain_core.utils.uuid import uuid7

from langgraph.checkpoint.memory import InMemorySaver



agent = create_agent(

    model="google_genai:gemini-4-hydrogen",

    tools=[],

    checkpointer=InMemorySaver(),

)



config = {"configurable": {"thread_id": str(uuid7())}}



result = agent.invoke(

    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]},

    config=config,

)



# A follow-up turn on the same conversation: reuse the same thread_id to keep history

result = agent.invoke(

    {"messages": [{"role": "user", "content": "What about tomorrow?"}]},

    config=config,

)

```
```

片段[5] `oss__python__deepagents__going-to-production#010` ｜ Going to production ｜ Production considerations > Invoking the agent

```text
``` from dataclasses import dataclass from deepagents import create_deep_agent from langchain_core.utils.uuid import uuid7 @dataclass class Context: user_id: str agent = create_deep_agent( model="google_genai:gemini-4-hydrogen", context_schema=Context, ) # Start a conversation config = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "Plan a 3-day trip to Tokyo"}]}, config=config, context=Context(user_id="user-123"), ) # Follow-up on the same conversation: reuse the same thread_id agent.invoke( {"messages": [{"role": "user", "content": "Make it 5 days instead"}]}, config=config, context=Context(user_id="user-123"), ) ```
```

---

## v2-H-001（single-hop）

**问题**：把 Claude 4/5 模型接进 openwiki，单次输出的 token 上限默认给到多少？为什么不用旧元数据里那个更小的值？

**gold**：Anthropic 的现代 Claude 4 和 5 模型默认上限是 16384 tokens；原因是旧的 LangChain 元数据会把较新的 Claude 别名卡在 4096。所以这里刻意不沿用旧值，避免新模型一接进来就被截断。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 openwiki 的 provider 配置里，Anthropic 的现代 Claude 4 和 5 模型默认输出上限是 **16384 tokens**；之所以不用旧元数据里更小的值，是因为旧 LangChain 元数据会把较新的 Claude 别名上限压到 4096 [1]。

最小可用示例（片段中未给出 openwiki 的具体配置代码，仅给出默认值说明）：

```text
Anthropic (Claude 4 / 5): default max output tokens = 16384
原因：older LangChain metadata otherwise caps newer Claude aliases at 4096
```

补充说明：片段 [9] 提到 `maxTokens` 适用于 anthropic 等 provider，但未给出 openwiki 中覆盖该默认值的具体写法；如需覆盖方式，给出的文档里没有找到相应内容。

**top5 片段**：

片段[1] `oss__openwiki__providers#004` ｜ Model providers ｜ Output token limits

```text
- Anthropic : modern Claude 4 and 5 models default to 16384 tokens because older LangChain metadata otherwise caps newer Claude aliases at 4096
```

片段[2] `oss__openwiki__providers#005` ｜ Model providers ｜ Output token limits

```text
- Bedrock : defaults to 16000 tokens. Override with OPENWIKI_BEDROCK_MAX_TOKENS when a model supports a lower ceiling
```

片段[3] `oss__python__langchain__models#082` ｜ Models ｜ Advanced topics > Token usage

```text
```

{

    'gpt-5.4-mini': {

        'input_tokens': 8,

        'output_tokens': 10,

        'total_tokens': 18,

        'input_token_details': {'audio': 0, 'cache_read': 0},

        'output_token_details': {'audio': 0, 'reasoning': 0}

    },

    'claude-haiku-4-5-20251001': {

        'input_tokens': 8,

        'output_tokens': 21,

        'total_tokens': 29,

        'input_token_details': {'cache_read': 0, 'cache_creation': 0}

    }

}

```
```

片段[4] `oss__python__langchain__models#084` ｜ Models ｜ Advanced topics > Token usage

```text
```

{

    'gpt-5.4-mini': {

        'input_tokens': 8,

        'output_tokens': 10,

        'total_tokens': 18,

        'input_token_details': {'audio': 0, 'cache_read': 0},

        'output_token_details': {'audio': 0, 'reasoning': 0}

    },

    'claude-haiku-4-5-20251001': {

        'input_tokens': 8,

        'output_tokens': 21,

        'total_tokens': 29,

        'input_token_details': {'cache_read': 0, 'cache_creation': 0}

    }

}

```
```

片段[5] `oss__python__langchain__models#019` ｜ Models ｜ Parameters

```text
```

model = init_chat_model(

    "claude-sonnet-4-6",

    # Kwargs passed to the model:

    temperature=0.7,

    timeout=30,

    max_tokens=1000,

    max_retries=6,  # Default; increase for unreliable networks

)

```
```

---

## v2-H-002（single-hop）

**问题**：走 Bedrock 的时候输出上限默认是多少？遇到某个模型本身的上限更低，怎么把它压下来？

**gold**：Bedrock 默认 16000 tokens；如果模型支持的上限更低，用 OPENWIKI_BEDROCK_MAX_TOKENS 覆盖这个默认值。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

- 走 Bedrock 时，输出 token 上限默认是 **16000 tokens** [1]。
- 如果某个模型本身支持的上限更低，可以用环境变量 **`OPENWIKI_BEDROCK_MAX_TOKENS`** 来覆盖（压低）这个默认值 [1]。

**最小可用示例：**

```bash
export OPENWIKI_BEDROCK_MAX_TOKENS=4096
```

**补充说明（与用户说法可能不一致之处）：**

- 片段里提到的覆盖方式是环境变量 `OPENWIKI_BEDROCK_MAX_TOKENS`，而不是在模型初始化参数里传 `maxTokens` [1]。虽然 [2] 的示例里出现了 `maxTokens: 25000` 这样的初始化参数，但那是 JavaScript `initChatModel` 的用法示例，片段并未说明它能用于覆盖 Bedrock 的默认输出上限，因此不能据此推断。
- 另外，[6] 提到 `maxTokens` 适用于包括 `bedrock` 在内的多个 provider，但同样没有说明它与 Bedrock 默认 16000 的关系，无法据此确认覆盖机制。

**top5 片段**：

片段[1] `oss__openwiki__providers#005` ｜ Model providers ｜ Output token limits

```text
- Bedrock : defaults to 16000 tokens. Override with OPENWIKI_BEDROCK_MAX_TOKENS when a model supports a lower ceiling
```

片段[2] `oss__javascript__langchain__quickstart#030` ｜ Quickstart ｜ Build a real-world agent

```text
```

import { initChatModel } from "langchain";



const model = await initChatModel("bedrock:gpt-6.1-sol", {

  temperature: 0.5,

  timeout: 300,

  maxTokens: 25000,

});

```
```

片段[3] `oss__python__langchain__test__integration-testing#007` ｜ Integration testing ｜ Reduce cost and latency

```text
- Cap output tokens : Limit response length on the chat model to avoid long, expensive completions.
```

片段[4] `oss__javascript__langchain__test__integration-testing#017` ｜ Integration testing ｜ Reduce cost and latency

```text
- Cap output tokens : Limit response length on the chat model to avoid long, expensive completions.
```

片段[5] `oss__python__deepagents__customization#091` ｜ Customize Deep Agents ｜ Middleware > Override a default middleware instance > Examples

```text
```

from deepagents import create_deep_agent

from langchain_anthropic.middleware import AnthropicPromptCachingMiddleware



agent = create_deep_agent(

    model="anthropic:claude-sonnet-4-6",

    middleware=[

        AnthropicPromptCachingMiddleware(ttl="1h"),  # replaces the default 5m TTL

    ],

)

```
```

---

## v2-H-003（single-hop）

**问题**：OpenAI 兼容通道走 Entra 那条认证链时，没单独配联合凭据的话，凭据还能从哪些地方来？

**gold**：这种情况下用 DefaultAzureCredential，它接受 az login、托管的 managed identity，或者环境凭据。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答这个问题的内容。

片段能确认的部分：

- 在 OpenAI 兼容通道启用 Entra 认证时，把 `OPENAI_COMPATIBLE_AUTH` 设为 `entra-id`，此时不需要 `OPENAI_COMPATIBLE_API_KEY` [1]。
- 默认 scope 是 `https://cognitiveservices.azure.com/.default`，自定义网关可能需要改 `OPENAI_COMPATIBLE_ENTRA_SCOPE` [3]。
- 片段 [11] 只提到「工作负载身份联合」这一种方式：设置 `AZURE_CLIENT_ID`、`AZURE_TENANT_ID`、`AZURE_FEDERATED_TOKEN_FILE`，当设置了 `AZURE_FEDERATED_TOKEN_FILE` 时使用 `WorkloadIdentityCredential` [11]。

缺什么：片段没有说明在**不使用联合凭据**（即不设 `AZURE_FEDERATED_TOKEN_FILE`）时，Entra 凭据还会从哪些来源获取（例如环境变量客户端密钥、托管标识、Azure CLI 登录、默认凭据链等）。[11] 只覆盖了联合凭据这一条路径，[1][3][8][9] 只涉及开关、scope 和 base URL，均未列出其他凭据来源，因此无法据此回答。

**top5 片段**：

片段[1] `oss__openwiki__providers#010` ｜ Model providers ｜ Microsoft Entra auth

```text
- OPENAI_COMPATIBLE_AUTH : Set to entra-id to enable Entra auth. The default is api-key . In Entra mode, OPENAI_COMPATIBLE_API_KEY is not required.
```

片段[2] `oss__openwiki__providers#009` ｜ Model providers ｜ Microsoft Entra auth

```text
```

OPENWIKI_PROVIDER=openai-compatible

OPENAI_COMPATIBLE_AUTH=entra-id

OPENAI_COMPATIBLE_BASE_URL=https://gateway.example.com/openai/v1

OPENAI_COMPATIBLE_ENTRA_SCOPE=api://gateway-application-id/.default

OPENWIKI_MODEL_ID=your-gateway-model

```
```

片段[3] `oss__openwiki__providers#000` ｜ Model providers ｜ ROOT

```text
| Provider | Credential | Notes | | --- | --- | --- | | openai | OPENAI_API_KEY | Optional OPENAI_BASE_URL for OpenAI-compatible gateways that expose the Responses API | | openai-chatgpt | ChatGPT OAuth tokens | Sign in with ChatGPT; usage draws on Plus/Pro/Team Codex allowance | | copilot | GitHub CLI session or COPILOT_API_KEY | Optional COPILOT_BASE_URL . CI needs an OAuth token, not a classic PAT | | openrouter | OPENROUTER_API_KEY | Optional OPENWIKI_OPENROUTER_PROVIDER_ONLY allowlist | | anthropic | ANTHROPIC_API_KEY | Optional ANTHROPIC_BASE_URL | | bob | BOB_API_KEY | Optional BOB_BASE_URL . Fixed model ID premium ; no model picker | | gemini | GEMINI_API_KEY | Google AI Studio |
```

片段[4] `oss__openwiki__providers#012` ｜ Model providers ｜ Microsoft Entra auth

```text
- OPENAI_COMPATIBLE_ENTRA_SCOPE : Optional. Defaults to https://cognitiveservices.azure.com/.default , the Azure OpenAI scope. Custom gateways may require a different scope.
```

片段[5] `oss__python__integrations__providers__microsoft#000` ｜ Microsoft integrations ｜ Explore integrations > Chat models

```text
- Microsoft Foundry (recommended) : To call models in Microsoft Foundry, use AzureAIOpenAIApiChatModel from langchain-azure-ai . It handles project endpoint resolution and Microsoft Entra ID authentication through Azure credentials.
```

---

## v2-H-004（single-hop）

**问题**：失败时只看到一句被包了一层的报错，哪个开关能把更完整的原因打出来，会细到什么程度？

**gold**：用 --debug：它会打印更完整的失败细节，包括包在包装错误背后的最内层原因，比如只显示 “Connection error.” 的那种情况。

**judge 分**：0.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能回答这个问题的内容。

具体缺什么：
- 没有任何片段提到「把更完整的原因打出来」的开关（例如某种 verbose / debug / 错误详情开关）。
- 片段 [1] 只说明认证失败时错误会被包装（`MCPClientError`、`ToolException`），并提示可以沿 cause chain 查找 `UnauthorizedError` 或 HTTP 401，但没有给出「打开某个开关以输出完整原因」的配置项。
- 片段 [8] 提到其他失败仍会从工具抛出，在 `createAgent` 中默认工具错误处理会转成 `status: "error"` 的 `ToolMessage`，并说「Read the exception's message for details; cause is not always set」，同样没有提到开关，也没有说明能细到什么程度。
- 片段 [3]、[5]、[6]、[13] 讲的是错误信息的「脱敏/受控展示」、重试与失败策略，方向与「打印更完整原因」相反，也没有对应开关。

因此无法根据现有片段回答「哪个开关」以及「会细到什么程度」。

**top5 片段**：

片段[1] `oss__javascript__migrate__langchain-mcp-adapters#032` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ Authentication

```text
- Errors : Walk an authentication failure’s cause chain for UnauthorizedError , which the adapter now exports, or an HTTP 401 error. Discovery wraps it in MCPClientError , twice when legacy mode falls back to SSE; tool calls wrap it in ToolException .
```

片段[2] `oss__javascript__langchain__structured-output#036` ｜ Structured output ｜ Handle parsing errors in chains

```text
- Fix malformed output with a model : Wrap the output parser in an OutputFixingParser from @langchain/classic . On a parsing failure, the wrapper sends the malformed output, the parser’s format instructions, and the error message to a model and parses the corrected response.
```

片段[3] `oss__python__langchain__middleware__built-in#004` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool error

```text
- Surfacing controlled, sanitized error messages instead of raw exception details.
```

片段[4] `oss__javascript__langgraph__fault-tolerance#034` ｜ Fault tolerance ｜ Recovery strategies > LLM-recoverable errors

```text
catch (error) { // Let the LLM see what went wrong and try again return new Command({ update: { toolResult: `Tool error: ${error}` }, goto: "agent", }); } }; ```
```

片段[5] `oss__javascript__langchain__middleware__built-in#009` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool retry

```text
ays wait 2 seconds }); // Raise exception on failure const strictRetry = toolRetryMiddleware({ maxRetries: 2, onFailure: "error", // Re-raise exception instead of returning message }); ```
```

---

## v2-H-005（single-hop）

**问题**：个人模式里接 Slack 和 Gmail，为什么得先把应用凭据自己填进本地配置文件？

**gold**：这两个源都要求 Slack 和 Gmail 的 app client credentials 已经提前放进 ~/.openwiki/.env；缺了这一步，后面的授权流程没法开始。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接回答「为什么」的内容——片段只说明了「需要这样做」这一事实，没有解释原因。

能确认的相关事实：

- Slack 和 Gmail 要求应用客户端凭据必须已经设置在 `~/.openwiki/.env` 中 [1]。
- 内置源列表中，`slack` 需要 Slack app client credentials + OAuth，且 OAuth 需要 HTTPS 回调设置 [2]；`google`（Gmail）走 Gmail OAuth，在 `openwiki auth gmail` 之后通过 Gmail API 拉取最近邮件 [10]。
- `~/.openwiki/.env` 的用途是存放 provider 配置、API key 以及 connector 的 OAuth token [3]。

缺失的内容：文档片段没有说明「为什么必须由用户预先自行填写凭据」这一设计动机（例如是否因为 OpenWiki 不托管 OAuth 应用、是否出于安全/本地优先考虑等）。要回答「为什么」，需要补充说明凭据来源与 OAuth 应用归属的文档段落。

最小可用示例（仅体现片段中的操作顺序，不代表原因）：

```bash
# 先在 ~/.openwiki/.env 中配置 Slack / Gmail 的 app client credentials
openwiki auth gmail
openwiki auth slack
```

注意一处表述差异：你问的是「Slack 和 Gmail」，片段 [1] 的原文确实是 “Slack and Gmail require app client credentials to already be set in ~/.openwiki/.env”，与此一致；但片段 [2]/[10] 的表格中对应条目名是 `slack` 和 `google`（Gmail 属于 `google` 源），并非直接叫 “Gmail”。

**top5 片段**：

片段[1] `oss__openwiki__personal-mode#006` ｜ Personal mode ｜ Connect your sources > Connect a source

```text
- Slack and Gmail require app client credentials to already be set in ~/.openwiki/.env
```

片段[2] `oss__openwiki__personal-mode#004` ｜ Personal mode ｜ Connect your sources > Built-in sources

```text
ecent mail via the Gmail API after openwiki auth gmail | | web-search | TAVILY_API_KEY | Uses Tavily through LangChain | | hackernews | None | Public Hacker News feed and search APIs | | slack | Slack app client credentials + OAuth | Requires HTTPS callback setup for OAuth; see Slack OAuth |
```

片段[3] `oss__openwiki__customize#004` ｜ Customize OpenWiki ｜ Local configuration directory

```text
| Path | Mode | Purpose |

| --- | --- | --- |

| ~/.openwiki/.env | Both | Provider config, API keys, and connector OAuth tokens |

| ~/.openwiki/openwiki.sqlite | Both | Conversation checkpoint database |

| ~/.openwiki/install-id | Both | Random install ID for anonymous telemetry |

| ~/.openwiki/wiki/ | Personal | Personal mode wiki output |

| ~/.openwiki/INSTRUCTIONS.md | Personal | Personal wiki brief |

| ~/.openwiki/onboarding.json | Personal | Personal onboarding preferences and connector schedules |

| ~/.openwiki/connectors/ | Mostly personal | Connector raw data and config. Personal sources use this path; code-mode LangSmith ingestion can also cache raw data here |
```

片段[4] `oss__python__deepagents__data-analysis#011` ｜ Build a data analysis agent ｜ Implement custom tools

```text
``` import os from langchain.tools import tool from slack_sdk import WebClient slack_token = os.environ["SLACK_USER_TOKEN"] slack_client = WebClient(token=slack_token) channel = "C0123456ABC"  # specify your own channel here @tool(parse_docstring=True) def slack_send_message(text: str, file_path: str | None = None) -> str: """Send message, optionally including attachments such as images. Args: text: (str) text content of the message file_path: (str) file path of attachment in the filesystem. """ if not file_path: slack_client.chat_postMessage(channel=channel, text=text) else: fp = backend.download_files([file_path]) slack_client.files_upload_v2( channel=channel, content=fp[0].content,
```

片段[5] `oss__openwiki__personal-mode#003` ｜ Personal mode ｜ Connect your sources > Built-in sources

```text
| Source | Credentials | Behavior | | --- | --- | --- | | custom-mcp | None required by default | Connects to any configured HTTP or stdio MCP server and permits only explicitly safe, read-only tools | | git-repo | Local paths | Reads configured local repository paths and writes compact manifests | | x | OAuth user-context credentials | Home timeline, user posts, mentions, bookmarks, and list posts via the X API | | notion | Notion OAuth (hosted MCP) | Authenticate through Notion OAuth instead of pasting a Notion token | | google | Gmail OAuth | Fetches recent mail via the Gmail API after openwiki auth gmail | | web-search | TAVILY_API_KEY | Uses Tavily through LangChain |
```

---

## v2-H-006（single-hop）

**问题**：页面上的 verified 戳，是生成一跑完就写上去的吗？要满足哪些条件？

**gold**：不是。只有当页面提交成功、Claims 集合非空且完整、通过最后的证据复核，并且把 Claims sidecar 持久化之后，才会写入 verified: {by: openwiki/<version>, at: ...}。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不是生成一跑完就写。** 只有在一次页面提交成功、并且满足若干校验条件之后，`verified` 戳才会被写入。

需要满足的条件（以片段为准）：

1. 页面提交（page submission）成功，并且这次提交**对账（reconcile）出一个非空且完整的 Claims 集合** [1]。
2. 通过**最终的证据复核（final evidence recheck）** [1]。
3. **持久化 Claims sidecar** [1]。

只有以上都完成后，Repository 页面才会收到 `verified: {by: openwiki/<version>, at: ...}` 形式的戳 [1]。

补充说明（同页信息）：

- `verified` 属于可选的 v0.2 provenance / trust / lifecycle 家族（`sources`、`verified`、`status`、`stale_after`），**存在时才会被校验**，并非必填字段 [8]。
- 页面会把有依据的 Claims 证据投影到 `sources` 中，OpenWiki 对确定性标识的条目做对账，同时保留独立编写的 sources [10]。

最小示例（示意该字段形态，非可执行代码）：

```yaml
verified:
  by: openwiki/<version>
  at: <timestamp>
```

注意：片段中没有给出 `at` 的具体时间格式，也没有说明 `openwiki/<version>` 的取值规则，这些内容在给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__openwiki__code-mode#012` ｜ Code mode ｜ Open Knowledge Format

```text
- Repository pages receive verified: {by: openwiki/<version>, at: ...} only after a successful page submission reconciles a non-empty complete Claims set, passes the final evidence recheck, and persists the Claims sidecar
```

片段[2] `oss__python__deepagents__rubric#029` ｜ Grading rubrics ｜ Observe iteration progress

```text
| Field | Type | Description | | --- | --- | --- | | grading_run_id | str | Identifier shared by every evaluation in one rubric attempt. A new run starts when the caller supplies a different rubric , or when the same rubric is invoked again after a terminal verdict. | | iteration | int | Zero-based index of the current grader pass within that run. | | result | str | The grader verdict for this pass: satisfied , needs_revision , failed , or grader_error . | | explanation | str | Free-form summary from the grader. On infrastructure failures, this includes the exception type and message. | | criteria | list | Per-criterion verdicts. Each entry is either {name, passed: true} or {name, passed:
```

片段[3] `oss__python__deepagents__rubric#014` ｜ Grading rubrics ｜ Pass rubric on invocation > Rubric verdicts

```text
| Status | Meaning | Loops back? |

| --- | --- | --- |

| satisfied | Every criterion in the rubric passes. | No |

| needs_revision | At least one criterion fails; grader feedback is injected and the agent runs again. | Yes |

| max_iterations_reached | Grader still wants revisions, but max_iterations has been hit. | No |

| failed | The grader judged the rubric malformed or impossible to evaluate against the transcript. | No |

| grader_error | The LLM-as-a-judge grader sub-agent itself raised an exception (provider timeout, missing credentials, malformed structured response, etc.). | No |
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

## v2-H-007（single-hop）

**问题**：用 e5 这类要求非对称提示的模型，文档侧和查询侧的前缀分别怎么配？

**gold**：用 HuggingFaceEmbeddings 时，文档侧放 encode_kwargs={"prompt": "passage: "}，查询侧放 query_encode_kwargs={"prompt": "query: "}，两侧不能共用同一个前缀。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：文档片段里给出的做法是——文档侧用 `encode_kwargs={"prompt": "passage: "}`，查询侧用 `query_encode_kwargs={"prompt": "query: "}`，两者都通过 `HuggingFaceEmbeddings` 传入 [2]。也就是说，文档侧前缀是 `passage: `，查询侧前缀是 `query: `，分别对应两个不同的参数名，不能混用 [2]。

最小可用示例（片段原文）：

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/e5-large-v2",
    encode_kwargs={"prompt": "passage: "},
    query_encode_kwargs={"prompt": "query: "},
)
```

补充说明：
- 片段 [1] 也提到多语言 e5 模型（`intfloat/multilingual-e5-large`）需要「configured query and document prompts」，但没有给出具体参数写法 [1]；具体参数写法只在 [2] 中出现。
- 片段 [12] 只列出 `intfloat/multilingual-e5-*` 属于多语言可选模型，未涉及前缀配置 [12]。

如果你问的是「前缀字符串本身」，片段只提供了 `passage: ` 和 `query: ` 这一组写法 [2]；其他 e5 变体是否用相同前缀，给出的文档里没有找到能回答这个问题的内容（缺少各模型对 prompt 前缀的具体要求说明）。

**top5 片段**：

片段[1] `oss__python__integrations__embeddings#015` ｜ Embedding model integrations ｜ Top integrations > Starting points

```text
- Multilingual, open: HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large") with query and document prompts configured
```

片段[2] `oss__python__integrations__embeddings#011` ｜ Embedding model integrations ｜ Top integrations > Factors to weigh > Query and document prompts

```text
```

from langchain_huggingface import HuggingFaceEmbeddings



embeddings = HuggingFaceEmbeddings(

    model_name="intfloat/e5-large-v2",

    encode_kwargs={"prompt": "passage: "},

    query_encode_kwargs={"prompt": "query: "},

)

```
```

片段[3] `oss__python__langchain__retrieval-optimization#009` ｜ Improve retrieval quality ｜ Combine semantic and keyword search

```text
retrieve(query: str): """Retrieve information related to a query.""" dense = vector_store.similarity_search(query, k=10) sparse = keyword_retriever.invoke(query) docs = reciprocal_rank_fusion([dense, sparse])[:4] serialized = "\n\n".join( f"Source: {doc.metadata}\nContent: {doc.page_content}" for doc in docs ) return serialized, docs ```
```

片段[4] `oss__python__langgraph__sql-agent#029` ｜ Build a custom SQL agent ｜ 4. Define application steps

```text
em_prompt, } # We do not force a tool call here, to allow the model to # respond naturally when it obtains the solution. llm_with_tools = model.bind_tools([run_query_tool]) response = llm_with_tools.invoke([system_message] + state["messages"]) return {"messages": [response]} check_query_system_prompt = """ You are a SQL expert with a strong attention to detail. Double check the {dialect} query for common mistakes, including: - Using NOT IN with NULL values - Using UNION when UNION ALL should have been used - Using BETWEEN for exclusive ranges - Data type mismatch in predicates - Properly quoting identifiers - Using the correct number of arguments for functions
```

片段[5] `oss__javascript__langgraph__frontend__overview#000` ｜ Overview ｜ Architecture

```text
``` import { Annotation, MessagesAnnotation, StateGraph, START, END } from "@langchain/langgraph"; const State = Annotation.Root({ ...MessagesAnnotation.spec, classification: Annotation<string>(), research: Annotation<string>(), analysis: Annotation<string>(), synthesis: Annotation<string>(), }); const graph = new StateGraph(State) .addNode("classify", classifyNode) .addNode("do_research", researchNode) .addNode("analyze", analyzeNode) .addNode("synthesize", synthesizeNode) .addEdge(START, "classify") .addEdge("classify", "do_research") .addEdge("do_research", "analyze") .addEdge("analyze", "synthesize") .addEdge("synthesize", END) .compile(); ```
```

---

## v2-H-008（single-hop）

**问题**：数据集大到一次装不进内存，DoclingLoader 该怎么读？它的行为和 load() 差在哪？

**gold**：用 lazy_load() 逐个产出文档，适合大数据集；load() 则一次性把所有文档都读出来返回。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：** 文档片段只给出了 `DoclingLoader` 的 `lazy_load()` 用法，说明它用于「大数据集」时逐条惰性加载；但没有说明 `lazy_load()` 与 `load()` 在内存占用、返回类型、执行时机上的具体差异，也没有给出「一次装不进内存」时的额外配置或分片策略。

**片段能确认的内容：**

- `DoclingLoader` 支持 `load()` 一次性加载全部文档，也支持 `lazy_load()` 惰性加载，后者在注释中被标注为「For large datasets」[1]。
- `lazy_load()` 的用法是迭代器形式，逐条 `print(document)` [1]。

**最小可用示例（来自片段 [1]）：**

```python
from langchain_docling.loader import DoclingLoader

FILE_PATH = "https://arxiv.org/pdf/2408.09869"

loader = DoclingLoader(file_path=FILE_PATH)

# Load all documents
documents = loader.load()

# For large datasets, lazily load documents
for document in loader.lazy_load():
    print(document)
```

**片段不足以回答的部分：**

- `lazy_load()` 与 `load()` 在内存行为上的具体差别（例如是否流式解析、是否仍会整体缓存）——片段没有说明。
- 数据集大到装不进内存时，除改用 `lazy_load()` 外是否还有分页、分批、分片参数——片段没有说明。
- 片段 [3] 提到的 `loadAndSplit()` 属于 JavaScript 文档加载器接口，且只说明「一次性加载并切分」，与 Python 的 `DoclingLoader` 不是同一接口，不能据此推断 Python 侧行为。

**名称/接口差异提示：** 片段 [3] 的 `loadAndSplit()` 出现在 JavaScript 文档加载器接口中 [3]，而 `DoclingLoader` 的示例出现在 Python 文档加载器接口中 [1]，两者不要混用。

**top5 片段**：

片段[1] `oss__python__integrations__document_loaders#001` ｜ Document loader integrations ｜ Interface

```text
```

from langchain_docling.loader import DoclingLoader



FILE_PATH = "https://arxiv.org/pdf/2408.09869"



loader = DoclingLoader(file_path=FILE_PATH)



# Load all documents

documents = loader.load()



# For large datasets, lazily load documents

for document in loader.lazy_load():

    print(document)

```
```

片段[2] `oss__javascript__langchain__messages#038` ｜ Messages ｜ Serialization

```text
load() deserializes data by instantiating classes and invoking constructors. Never call load() on untrusted or user-supplied input.
```

片段[3] `oss__javascript__integrations__document_loaders#001` ｜ Document loader integrations ｜ Interface

```text
- loadAndSplit() : Loads all documents at once and splits them into smaller documents.
```

片段[4] `oss__python__integrations__document_loaders#012` ｜ Document loader integrations ｜ All document loaders

```text
DoclingLoader |  | | Azure blob storage loader |  | | FlatmarkLoader |  | | FirecrawlLoader |  | | OpenDocKitLoader |  | | OpenDataLoader PDF |  | | AnakinLoader |  | | Docugami |  | | HwpHwpxLoader |  | | PDFParser |  | | SingleStoreLoader |  | | YoutubeLoaderDL |  | | SuperPDFLoader |  | | MeshArcLoader |  | | HyperbrowserLoader |  | | FastOCRLoader |  | | ReplyLayerLoader |  | | HydrafetchLoader |  | | SecureLangChainLoader |  | | SpidraLoader |  | | PdfInspectorLoader |  | | WebCrawlerAPILoader |  | | CrwLoader |  | | Google bigtable |  | | Outline |  | | MinerULoader |  | | DiffbotCrawlLoader |  | | DiffbotExtractLoader |  | | DomPrunerLoader |  | | PolarisAIDataInsightLoader |  |
```

片段[5] `oss__javascript__integrations__document_loaders#002` ｜ Document loader integrations ｜ Interface

```text
```

import { OracleDocLoader } from "@oracle/langchain-oracledb";



const loader = new OracleDocLoader(,

  ...  // <-- Integration specific parameters here

);

const data = await loader.load();

```
```

---

## v2-H-009（single-hop）

**问题**：切分长文档时，希望尽量别把完整段落拆散，应该优先选哪种 splitter？

**gold**：选 RecursiveCharacterTextSplitter，它会尝试保留更大的文本单元（例如段落）不被打断。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：应优先选 `RecursiveCharacterTextSplitter`。文档说明它会尽量保持较大单元（例如段落）完整 [1][2]；如果某个单元超过 chunk size，才会退到下一层级（例如句子）继续切 [9][11]。

最小可用示例（片段里只出现了 JavaScript 侧的构造参数，Python 侧未给出示例）：

```javascript
const textSplitter = new RecursiveCharacterTextSplitter({
  chunkSize: 1000,
  chunkOverlap: 200,
});
const allSplits = await textSplitter.splitDocuments(docs);
```

说明：片段 [3]–[8] 的代码开头被截断为 `aracterTextSplitter(...)`，从上下文看应为 `RecursiveCharacterTextSplitter`，但片段本身没有完整类名，这里按 [1][2] 的类名给出。

**top5 片段**：

片段[1] `oss__javascript__integrations__splitters#004` ｜ Text splitter integrations ｜ Text structure-based

```text
- The RecursiveCharacterTextSplitter attempts to keep larger units (e.g., paragraphs) intact.
```

片段[2] `oss__python__integrations__splitters#000` ｜ Text splitter integrations ｜ Text structure-based

```text
- The RecursiveCharacterTextSplitter attempts to keep larger units (e.g., paragraphs) intact.
```

片段[3] `oss__javascript__deepagents__rag#072` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Full code

```text
aracterTextSplitter({ chunkSize: 1000, chunkOverlap: 200, }); const allSplits = await textSplitter.splitDocuments(docs); console.log(`Split documentation into ${allSplits.length} chunks.`); const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" }); const vectorStore = new MemoryVectorStore(embeddings); await vectorStore.addDocuments(allSplits); console.log(`Indexed ${allSplits.length} chunks.`); const backend = new StateBackend(); const searchDocumentation = tool( async ({ query }) => { const retrievedDocs = await vectorStore.similaritySearch(query, 4); const batchId = uuid7().slice(0, 8); const uploads: Array<[string, Uint8Array]> = []; const savedPaths: string[] = [];
```

片段[4] `oss__javascript__deepagents__rag#061` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Full code

```text
aracterTextSplitter({ chunkSize: 1000, chunkOverlap: 200, }); const allSplits = await textSplitter.splitDocuments(docs); console.log(`Split documentation into ${allSplits.length} chunks.`); const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" }); const vectorStore = new MemoryVectorStore(embeddings); await vectorStore.addDocuments(allSplits); console.log(`Indexed ${allSplits.length} chunks.`); const backend = new StateBackend(); const searchDocumentation = tool( async ({ query }) => { const retrievedDocs = await vectorStore.similaritySearch(query, 4); const batchId = uuid7().slice(0, 8); const uploads: Array<[string, Uint8Array]> = []; const savedPaths: string[] = [];
```

片段[5] `oss__javascript__deepagents__rag#094` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Full code

```text
aracterTextSplitter({ chunkSize: 1000, chunkOverlap: 200, }); const allSplits = await textSplitter.splitDocuments(docs); console.log(`Split documentation into ${allSplits.length} chunks.`); const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" }); const vectorStore = new MemoryVectorStore(embeddings); await vectorStore.addDocuments(allSplits); console.log(`Indexed ${allSplits.length} chunks.`); const backend = new StateBackend(); const searchDocumentation = tool( async ({ query }) => { const retrievedDocs = await vectorStore.similaritySearch(query, 4); const batchId = uuid7().slice(0, 8); const uploads: Array<[string, Uint8Array]> = []; const savedPaths: string[] = [];
```

---

## v2-H-010（single-hop）

**问题**：部署环境完全不能出网、检索只能用自建；候选 retriever 里哪个明确只支持自建，哪些两边都行？

**gold**：NVIDIARAGRetriever 只有 self-host 这一列；ElasticsearchRetriever 和 MengramRetriever 是自建与云都支持的。其余如 AmazonKnowledgeBasesRetriever、AzureAISearchRetriever、VertexAISearchRetriever 只有云。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能完整回答这个问题的内容。

**能确认的部分：**

- 明确标注「只支持自建」（Self-host ✅、Cloud offering ❌）的只有 **NVIDIARAGRetriever**，包为 `langchain-nvidia-ai-endpoints` [2][6]。
- 明确标注「两边都行」（Self-host ✅、Cloud offering ✅）的有：
  - **ElasticsearchRetriever**（`langchain-elasticsearch`）[2]
  - **MengramRetriever**（`langchain-mengram`）[2]
  - **RecallRetriever**（`@recall-memory/langchain`）[7]
- 另外 **LoomKnowledgeRetriever** 和 **LoomMemoryRetriever** 在 JS 表中 Self-host 为 ✅，但 Cloud offering 列为空，无法据此判定是否支持云 [1]。

**缺什么：**

1. 片段中的表格大量单元格为空（如 [1] 里多数 retriever 的 Self-host / Cloud 列都是空白），空值不能等同于「不支持」，因此无法判断这些条目是否满足「完全离线自建」。
2. 没有任何片段说明这些 retriever 是否需要访问外部网络（例如 ExaRetriever、PerplexitySearchRetriever 属于互联网搜索类 [8]，但片段未直接给出「不能出网」的结论）。
3. 没有片段说明自建部署的具体方式或离线运行要求。

因此，除上述明确标注的条目外，其余候选无法根据给出的文档判断。

**top5 片段**：

片段[1] `oss__javascript__integrations__retrievers#000` ｜ Retriever integrations ｜ All retrievers

```text
| Retriever | Self-host | Cloud offering | Package | Downloads | | --- | --- | --- | --- | --- | | AWSKendraRetriever |  |  | @langchain/aws |  | | Knowledge bases for Amazon Bedrock |  |  | @langchain/aws |  | | ExaRetriever |  |  | @langchain/exa |  | | PerplexitySearchRetriever |  |  | @langchain/perplexity |  | | LoomKnowledgeRetriever | ✅ |  | @clickhouse/loom |  | | LoomMemoryRetriever | ✅ |  | @clickhouse/loom |  | | SourceyRetriever |  |  | langchain-sourcey |  | | ClawDBRetriever (Axonio) |  |  | axonio-langchain |  | | AlchemystRetriever |  |  | @alchemystai/langchain-js |  | | FoxNoseRetriever | ❌ | ✅ | @foxnose/langchain |  |
```

片段[2] `oss__python__integrations__retrievers#000` ｜ Retriever integrations ｜ Bring-your-own documents

```text
| Retriever | Self-host | Cloud offering | Package |

| --- | --- | --- | --- |

| AmazonKnowledgeBasesRetriever | ❌ | ✅ | langchain-aws |

| AzureAISearchRetriever | ❌ | ✅ | langchain-azure-ai |

| ElasticsearchRetriever | ✅ | ✅ | langchain-elasticsearch |

| MongoDBAtlasHybridSearchRetriever | ❌ | ✅ | langchain-mongodb |

| MemstateRetriever | ❌ | ✅ | langchain-memstate |

| MengramRetriever | ✅ | ✅ | langchain-mengram |

| NVIDIARAGRetriever | ✅ | ❌ | langchain-nvidia-ai-endpoints |

| VertexAISearchRetriever | ❌ | ✅ | langchain-google-community |
```

片段[3] `oss__javascript__langchain__mcp__connections#008` ｜ Connections ｜ View example trace

```text
- "auto" (the default): Try the current protocol and fall back for a legacy-only server.
```

片段[4] `oss__python__deepagents__comparison#008` ｜ Comparison with Claude Agent SDK ｜ Summary

```text
- Choose Deep Agents if you want model and infrastructure flexibility, built-in multi-tenant deployment, and the option to run managed or self-hosted with the same agent code.
```

片段[5] `oss__javascript__deepagents__comparison#008` ｜ Comparison with Claude Agent SDK ｜ Summary

```text
- Choose Deep Agents if you want model and infrastructure flexibility, built-in multi-tenant deployment, and the option to run managed or self-hosted with the same agent code.
```

---

## v2-H-011（single-hop）

**问题**：PIIMiddleware 的 strategy 用 redact 和用 block 分别是什么效果？想对邮箱和电话用不同策略该怎么配？

**gold**：redact 把命中的内容抹掉，示例里邮箱还配了 apply_to_input=True；block 直接把这次输入拦下不让过。要分别处理就同时挂两个 PIIMiddleware，电话那个用自定义 detector 正则加 block。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论**

- `strategy="redact"`：把检测到的 PII 内容做脱敏/打码处理（片段中示例用于邮箱），处理后继续流程 [1][7]。
- `strategy="block"`：检测到 PII 时直接抛出错误阻断（片段注释为 "raise error if detected"），例如对 API key 使用 [1]。
- 想对邮箱和电话用不同策略：为每种 PII 各配一个 `PIIMiddleware`，分别指定 `strategy`。片段中就有邮箱用 `redact`、电话用 `block` 的写法 [3]。

**最小可用示例（Python）**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware

agent = create_agent(
    model="claude-sonnet-4-6",
    tools=[read_email, send_email],
    middleware=[
        PIIMiddleware("email", strategy="redact", apply_to_input=True),
        PIIMiddleware(
            "phone_number",
            detector=(
                r"(?:\+?\d{1,3}[\s.-]?)?"
                r"(?:\(?\d{2,4}\)?[\s.-]?)?"
                r"\d{3,4}[\s.-]?\d{4}"
            ),
            strategy="block",
        ),
    ],
)
```

**说明与差异提示**

- 片段里 `PIIMiddleware` 的第一个位置参数是 PII 类型（如 `"email"`、`"credit_card"`、`"api_key"`、`"phone_number"`），策略通过 `strategy` 传入 [1][3][7]。
- 片段中 `block` 的语义仅以注释形式出现（"raise error if detected"）[1]，未给出更细的异常类型或错误信息，这部分文档片段没有覆盖。
- JavaScript 版本对应的是 `piiMiddleware(...)`（小写开头），参数为对象形式（如 `{ strategy: "redact", applyToInput: true }`）[2][5][8]，与 Python 的 `PIIMiddleware(...)` 写法不同，注意不要混用。

**top5 片段**：

片段[1] `oss__python__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[customer_service_tool, email_tool], middleware=[ # Redact emails in user input before sending to model PIIMiddleware( "email", strategy="redact", apply_to_input=True, ), # Mask credit cards in user input PIIMiddleware( "credit_card", strategy="mask", apply_to_input=True, ), # Block API keys - raise error if detected PIIMiddleware( "api_key", detector=r"sk-[a-zA-Z0-9]{32}", strategy="block", apply_to_input=True, ), ], ) # When user provides PII, it will be handled according to the strategy result = agent.invoke({ "messages": [{"role":
```

片段[2] `oss__javascript__langchain__guardrails#001` ｜ Guardrails ｜ Built-in guardrails > PII detection

```text
``` import { createAgent, piiMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [customerServiceTool, emailTool], middleware: [ // Redact emails in user input before sending to model piiMiddleware("email", { strategy: "redact", applyToInput: true, }), // Mask credit cards in user input piiMiddleware("credit_card", { strategy: "mask", applyToInput: true, }), // Block API keys - raise error if detected piiMiddleware("api_key", { detector: /sk-[a-zA-Z0-9]{32}/, strategy: "block", applyToInput: true, }), ], }); // When user provides PII, it will be handled according to the strategy const result = await agent.invoke({ messages: [{ role: "user", content:
```

片段[3] `oss__python__releases__langchain-v1#001` ｜ What's new in LangChain v1 ｜ create_agent > Middleware > Prebuilt middleware

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import ( PIIMiddleware, SummarizationMiddleware, HumanInTheLoopMiddleware ) agent = create_agent( model="claude-sonnet-4-6", tools=[read_email, send_email], middleware=[ PIIMiddleware("email", strategy="redact", apply_to_input=True), PIIMiddleware( "phone_number", detector=( r"(?:\+?\d{1,3}[\s.-]?)?" r"(?:\(?\d{2,4}\)?[\s.-]?)?" r"\d{3,4}[\s.-]?\d{4}" ), strategy="block" ), SummarizationMiddleware( model="claude-sonnet-4-6", trigger={"tokens": 500} ), HumanInTheLoopMiddleware( interrupt_on={ "send_email": { "allowed_decisions": ["approve", "edit", "reject"] } } ), ] ) ```
```

片段[4] `oss__python__langchain__guardrails#017` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import PIIMiddleware, HumanInTheLoopMiddleware agent = create_agent( model="gpt-6.1-sol", tools=[search_tool, send_email_tool], middleware=[ # Layer 1: Deterministic input filter (before agent) ContentFilterMiddleware(banned_keywords=["hack", "exploit"]), # Layer 2: PII protection (before and after model) PIIMiddleware("email", strategy="redact", apply_to_input=True), PIIMiddleware("email", strategy="redact", apply_to_output=True), # Layer 3: Human approval for sensitive tools HumanInTheLoopMiddleware(interrupt_on={"send_email": True}), # Layer 4: Model-based safety check (after agent) SafetyGuardrailMiddleware(),
```

片段[5] `oss__javascript__langchain__guardrails#011` ｜ Guardrails ｜ Custom guardrails > Combine multiple guardrails

```text
``` import { createAgent, piiMiddleware, humanInTheLoopMiddleware } from "langchain"; const agent = createAgent({ model: "gpt-6.1-sol", tools: [searchTool, sendEmailTool], middleware: [ // Layer 1: Deterministic input filter (before agent) contentFilterMiddleware(["hack", "exploit"]), // Layer 2: PII protection (before and after model) piiMiddleware("email", { strategy: "redact", applyToInput: true, }), piiMiddleware("email", { strategy: "redact", applyToOutput: true, }), // Layer 3: Human approval for sensitive tools humanInTheLoopMiddleware({ interruptOn: { send_email: { allowAccept: true, allowEdit: true, allowRespond: true }, } }), // Layer 4: Model-based safety check (after agent)
```

---

## v2-H-012（single-hop）

**问题**：改完一个跟集成有关的 bug，本地该跑哪些检查命令？

**gold**：先跑 make format、make lint、make test；涉及集成的 bugfix 还要再跑 make integration_tests，这一步可能需要先配好 API testing credentials。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：集成相关 bugfix 的检查命令因语言仓库而异。Python 仓库在常规 `make format` / `make lint` / `make test` 之外，还要跑 `make integration_tests`（可能需要配置 API 测试凭据）[1]；JavaScript 仓库在 `pnpm lint` / `pnpm test` 之外，还要跑 `pnpm test:int` [2]。

最小可用示例：

Python 仓库：
```bash
make format
make lint
make test

# For bugfixes involving integrations, also run:
make integration_tests
# (You may need to set up API testing credentials)
```
[1]

JavaScript 仓库：
```bash
pnpm lint
pnpm test

# For bugfixes involving integrations, also run:
pnpm test:int
```
[2]

补充说明（以片段为准的差异点）：
- 片段 [2] 里集成测试脚本名是 `pnpm test:int`；而片段 [5] 的 `package.json` 示例中脚本名是 `test:integration`（`vitest --mode int`）。两处命名不一致，请以你所在仓库实际的 `package.json` 脚本为准，不要直接照搬。
- 片段 [2] 还给出了按包运行的方式，例如 `pnpm --filter @langchain/core test` 和 `pnpm --filter @langchain/core lint` [2]。
- 若改动同时涉及文档，文档质量检查命令为 `make broken-links-with-anchors`、`make format`、`make lint`、`make lint_md_fix`、`make test` [3][4]。

**top5 片段**：

片段[1] `oss__python__contributing__code#003` ｜ Contributing to code ｜ Deep Agents > Quick fix: submit a bugfix

```text
```

make format

make lint

make test



# For bugfixes involving integrations, also run:

make integration_tests

# (You may need to set up API testing credentials)

```
```

片段[2] `oss__javascript__contributing__code#004` ｜ Contributing to code ｜ Deep Agents > Quick fix: submit a bugfix

```text
```

pnpm lint

pnpm test



# For bugfixes involving integrations, also run:

pnpm test:int



# Or run tests in a specific workspace package

cd libs/langchain-core

pnpm test

pnpm lint



# Or run tests for a specific package from the root of the repo

pnpm --filter @langchain/core test

pnpm --filter @langchain/core lint

```
```

片段[3] `oss__python__contributing__documentation#003` ｜ Contributing to documentation ｜ Edit documentation > Run quality checks

```text
```

# Check broken links and anchors

make broken-links-with-anchors



# Format code automatically

make format



# Check for linting issues

make lint



# Fix markdown issues

make lint_md_fix



# Run tests to ensure your changes don't break existing functionality

make test

```
```

片段[4] `oss__javascript__contributing__documentation#003` ｜ Contributing to documentation ｜ Edit documentation > Run quality checks

```text
```

# Check broken links and anchors

make broken-links-with-anchors



# Format code automatically

make format



# Check for linting issues

make lint



# Fix markdown issues

make lint_md_fix



# Run tests to ensure your changes don't break existing functionality

make test

```
```

片段[5] `oss__javascript__langchain__test__integration-testing#002` ｜ Integration testing ｜ Separate unit and integration tests

```text
```

{

  "scripts": {

    "test": "vitest",

    "test:integration": "vitest --mode int"

  }

}

```
```

---

## v2-H-013（single-hop）

**问题**：在函数 docstring 里用 ???+ 折叠块会有什么问题？

**gold**：不要把 ???+、accordion 或 tabs 这类 MkDocs 专有语法写进 docstring——它们在 IDE 里不会渲染，读者只能看到原始标记。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 docstring 里使用 `???+` 这类 MkDocs 专有语法会有问题——它们在 IDE 中不会渲染 [1]。文档建议避免在 docstring 中使用 `???+`、accordions（折叠面板）或 tabs（标签页）[1]。

最小可用示例（按片段建议，docstring 中不使用 MkDocs 专有语法）：

```python
def my_function(x: int) -> int:
    """Return x doubled.

    Args:
        x: Input value.
    """
    return x * 2
```

补充说明：给出的文档里没有找到关于 `???+` 具体渲染失败原因或替代写法的更多内容；片段 [1] 只说明「避免使用，因为 IDE 不渲染」。

**top5 片段**：

片段[1] `oss__python__contributing__code#030` ｜ Contributing to code ｜ Development workflow > Code quality standards

```text
- MkDocs-specific syntax : Avoid ???+ , accordions, or tabs in docstrings. They don’t render in IDEs.
```

片段[2] `oss__javascript__langchain__frontend__tool-calling#009` ｜ Tool calling ｜ Building specialized tool cards > Loading and error states

```text
```

function LoadingCard({ name }: { name: string }) {

  return (

    <div className="flex items-center gap-2 rounded-lg border p-4 animate-pulse">

      <Spinner />

      <span>Running {name}...</span>

    </div>

  );

}



function ErrorCard({ name, error }: { name: string; error?: unknown }) {

  return (

    <div className="rounded-lg border border-red-300 bg-red-50 p-4">

      <h3 className="font-semibold text-red-700">Error in {name}</h3>

      <p className="text-sm text-red-600">

        {String(error ?? "Tool execution failed")}

      </p>

    </div>

  );

}

```
```

片段[3] `oss__python__langchain__frontend__tool-calling#009` ｜ Tool calling ｜ Building specialized tool cards > Loading and error states

```text
```

function LoadingCard({ name }: { name: string }) {

  return (

    <div className="flex items-center gap-2 rounded-lg border p-4 animate-pulse">

      <Spinner />

      <span>Running {name}...</span>

    </div>

  );

}



function ErrorCard({ name, error }: { name: string; error?: unknown }) {

  return (

    <div className="rounded-lg border border-red-300 bg-red-50 p-4">

      <h3 className="font-semibold text-red-700">Error in {name}</h3>

      <p className="text-sm text-red-600">

        {String(error ?? "Tool execution failed")}

      </p>

    </div>

  );

}

```
```

片段[4] `oss__javascript__langgraph__agentic-rag#010` ｜ Build a custom RAG agent with LangGraph ｜ Preprocess documents

```text
```

const docsList = docs.flat();

const textSplitter = new RecursiveCharacterTextSplitter({

  chunkSize: 500,

  chunkOverlap: 50,

});

const docSplits = await textSplitter.splitDocuments(docsList);

```
```

片段[5] `oss__javascript__deepagents__rag#117` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Full code

```text
aracterTextSplitter({ chunkSize: 1000, chunkOverlap: 200, }); const allSplits = await textSplitter.splitDocuments(docs); console.log(`Split documentation into ${allSplits.length} chunks.`); const embeddings = new OpenAIEmbeddings({ model: "text-embedding-3-small" }); const vectorStore = new MemoryVectorStore(embeddings); await vectorStore.addDocuments(allSplits); console.log(`Indexed ${allSplits.length} chunks.`); const backend = new StateBackend(); const searchDocumentation = tool( async ({ query }) => { const retrievedDocs = await vectorStore.similaritySearch(query, 4); const batchId = uuid7().slice(0, 8); const uploads: Array<[string, Uint8Array]> = []; const savedPaths: string[] = [];
```

---

## v2-H-014（single-hop）

**问题**：想按对话长度在便宜模型和强模型之间切换，v1 里应该在哪一层做？切换怎么落到本次请求上？

**gold**：写一个自定义 AgentMiddleware，在 wrap_model_call 里比较 len(request.state.messages) 与阈值来选模型，最后用 handler(request.override(model=model)) 把选择应用到这次调用。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 v1 里，按对话长度切换模型应该放在 **middleware 的 `wrap_model_call` 层**做，而不是在 `create_agent` 的 `model=` 参数里传一个选择函数。切换通过 `request.override(model=...)` 落到本次请求上，然后调用 `handler(request)` [2][7]。

具体要点：

1. **位置**：用 `@wrap_model_call` 装饰一个函数，在函数里读 `request.messages`（它是 `request.state["messages"]` 的快捷方式），按长度选模型 [1][7]。
2. **落到本次请求**：用 `request.override(model=model)` 生成新的 request，再 `return handler(request)`。这样只影响当前这次模型调用，不改 agent 的默认模型 [2][7]。
3. **默认模型**：`create_agent(model=..., middleware=[...])` 里的 `model` 是基础/默认模型 [2][7]。
4. **注意 API 差异**：片段 [6] 展示的是旧写法——把 `select_model` 函数直接传给 `create_react_agent(model=select_model)`。这是迁移页里的旧 API，不是 v1 的 `create_agent` 写法；v1 应按 [2][7] 用 middleware 实现 [6][2]。

最小可用示例（Python，v1）：

```python
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse
from typing import Callable

# 模型在 middleware 外初始化一次
large_model = init_chat_model("claude-sonnet-4-6")
standard_model = init_chat_model("gpt-6.1-sol")
efficient_model = init_chat_model("gpt-5.4-mini")

@wrap_model_call
def state_based_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    """按对话长度选择模型。"""
    message_count = len(request.messages)  # 等价于 request.state["messages"]

    if message_count > 20:
        model = large_model
    elif message_count > 10:
        model = standard_model
    else:
        model = efficient_model

    request = request.override(model=model)  # 只覆盖本次请求
    return handler(request)

agent = create_agent(
    model="gpt-5.4-mini",  # 默认模型
    tools=[...],
    middleware=[state_based_model],
)
```

补充：如果切换依据是运行时上下文（如成本档位、环境）而不是消息条数，同样在 `wrap_model_call` 里读 `request.runtime.context`，再用 `request.override(model=model)` 落到本次请求 [3]。

**top5 片段**：

片段[1] `oss__python__langchain__context-engineering#026` ｜ Context engineering in agents ｜ Response Format > Model

```text
``` from langchain.agents import create_agent from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse from langchain.chat_models import init_chat_model from typing import Callable # Initialize models once outside the middleware large_model = init_chat_model("claude-sonnet-4-6") standard_model = init_chat_model("gpt-6.1-sol") efficient_model = init_chat_model("gpt-5.4-mini") @wrap_model_call def state_based_model( request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse] ) -> ModelResponse: """Select model based on State conversation length.""" # request.messages is a shortcut for request.state["messages"] message_count = len(request.messages)
```

片段[2] `oss__python__langchain__models#093` ｜ Models ｜ Advanced topics > Dynamic model selection

```text
``` from langchain_openai import ChatOpenAI from langchain.agents import create_agent from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse basic_model = ChatOpenAI(model="gpt-5.4-mini") advanced_model = ChatOpenAI(model="gpt-6.1-sol") @wrap_model_call def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse: """Choose model based on conversation complexity.""" message_count = len(request.state["messages"]) if message_count > 10: # Use an advanced model for longer conversations model = advanced_model else: model = basic_model return handler(request.override(model=model)) agent = create_agent( model=basic_model,  # Default model tools=[],
```

片段[3] `oss__python__langchain__context-engineering#031` ｜ Context engineering in agents ｜ Response Format > Model

```text
quest, handler: Callable[[ModelRequest], ModelResponse] ) -> ModelResponse: """Select model based on Runtime Context.""" # Read from Runtime Context: cost tier and environment cost_tier = request.runtime.context.cost_tier environment = request.runtime.context.environment if environment == "production" and cost_tier == "premium": # Production premium users get best model model = premium_model elif cost_tier == "budget": # Budget tier gets efficient model model = budget_model else: # Standard tier model = standard_model request = request.override(model=model) return handler(request) agent = create_agent( model="gpt-6.1-sol", tools=[...], middleware=[context_based_model], context_schema=Context
```

片段[4] `oss__python__langchain__context-engineering#027` ｜ Context engineering in agents ｜ Response Format > Model

```text
ersation length.""" # request.messages is a shortcut for request.state["messages"] message_count = len(request.messages) if message_count > 20: # Long conversation - use model with larger context window model = large_model elif message_count > 10: # Medium conversation model = standard_model else: # Short conversation - use efficient model model = efficient_model request = request.override(model=model) return handler(request) agent = create_agent( model="gpt-5.4-mini", tools=[...], middleware=[state_based_model] ) ```
```

片段[5] `oss__javascript__langchain__models#072` ｜ Models ｜ Advanced topics > Dynamic model selection

```text
``` import { ChatOpenAI } from "@langchain/openai"; import { createAgent, createMiddleware } from "langchain"; const basicModel = new ChatOpenAI({ model: "gpt-5.4-mini" }); const advancedModel = new ChatOpenAI({ model: "gpt-6.1-sol" }); const dynamicModelSelection = createMiddleware({ name: "DynamicModelSelection", wrapModelCall: (request, handler) => { // Choose model based on conversation complexity const messageCount = request.messages.length; return handler({ ...request, model: messageCount > 10 ? advancedModel : basicModel, }); }, }); const agent = createAgent({ model: "gpt-5.4-mini", // Base model (used when messageCount ≤ 10) tools: [], middleware: [dynamicModelSelection], }); ```
```

---

## v2-H-015（multi-hop）

**问题**：同一台机器上同时用 Codex 和 Claude Code，两个 agent 说明文件 openwiki 都会帮你建出来吗？

**gold**：不一样。AGENTS.md 缺失时会被创建，之后只重写 <!-- OPENWIKI:START --> 到 <!-- OPENWIKI:END --> 这一段；CLAUDE.md 只在文件已经存在时才刷新，缺失时不会创建，它的托管块通过 import @AGENTS.md 复用同一套说明。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不会都自动创建。** OpenWiki 会创建 `AGENTS.md`（缺失时创建）[9][11]，但 **不会创建 `CLAUDE.md`**——只有当 `CLAUDE.md` 已经存在时才会刷新它 [1][2]。

具体行为：
- `AGENTS.md`：缺失时创建，之后只重写 `<!-- OPENWIKI:START --> … <!-- OPENWIKI:END -->` 块，其余内容保留 [9][11]。
- `CLAUDE.md`：仅在文件已存在时更新；其中的 managed block 通过 `@AGENTS.md` 导入，让 Claude Code 读到同一份指令；文件不存在时 OpenWiki 不创建它 [1][2]。另外，如果文件内容只有 `@AGENTS.md`，则保持不变 [2]。

所以同一台机器上同时用 Codex 和 Claude Code 时，你需要自己先建一个 `CLAUDE.md`（例如内容为 `@AGENTS.md`），OpenWiki 才会去维护它。

最小可用示例（先手动创建 `CLAUDE.md`，再安装集成）：

```bash
# 1. 手动创建 CLAUDE.md，让 Claude Code 复用 AGENTS.md 的指令
printf '@AGENTS.md\n' > CLAUDE.md

# 2. 安装两个 coding-agent 集成
openwiki integrations install codex
openwiki integrations install claude
```

补充说明（以片段为准的差异点）：
- 集成安装命令中，Claude Code 对应的标识是 `claude`，不是 `claude-code` [6][13]。
- 关于支持的 agent 列表，片段 [3] 与 [4] 不完全一致：[3] 含 `Pi`，[4] 含 `GitHub Copilot` 且不含 `Pi`；而 CLI 的 `install` 子命令参数列表为 `codex|claude|opencode|cursor|bob|kiro|omp|antigravity` [6]，`copilot` 出现在 [7][13] 的示例中但不在 [6] 的参数枚举里。

**top5 片段**：

片段[1] `oss__openwiki__code-mode#008` ｜ Code mode ｜ What code mode produces

```text
- CLAUDE.md : Refreshed only when the file already exists. The managed block imports @AGENTS.md so Claude Code still loads the same instructions. OpenWiki does not create CLAUDE.md when it is absent
```

片段[2] `oss__openwiki__customize#003` ｜ Customize OpenWiki ｜ Agent instruction files

```text
- CLAUDE.md : Updated only when the file already exists. The managed block imports @AGENTS.md so Claude Code reads the same instructions. OpenWiki does not create CLAUDE.md when it is absent, and it leaves a file that is only @AGENTS.md unchanged
```

片段[3] `oss__openwiki__quickstart#002` ｜ Quickstart ｜ Next steps

```text
- Coding-agent integrations : run OpenWiki inside Codex, Claude Code, OpenCode, Cursor, IBM Bob, Kiro, Oh My Pi, Antigravity, or Pi
```

片段[4] `oss__openwiki__integrations#000` ｜ Coding-agent integrations ｜ ROOT

```text
Coding-agent integrations Run OpenWiki inside Codex, Claude Code, GitHub Copilot, OpenCode, Cursor, IBM Bob, Kiro, Oh My Pi, or Antigravity using the host model and tools
```

片段[5] `oss__openwiki__integrations#001` ｜ Coding-agent integrations ｜ Install an integration

```text
```

openwiki integrations install codex

openwiki integrations install claude

openwiki integrations install copilot

openwiki integrations install opencode

openwiki integrations install cursor

openwiki integrations install bob

openwiki integrations install kiro

openwiki integrations install omp

openwiki integrations install antigravity

```
```

---

## v2-H-016（multi-hop）

**问题**：接 Slack 源时，为什么授权回调不能只挂在本机 http 地址上？openwiki 给了什么现成办法？

**gold**：Slack 的 OAuth 需要 HTTPS callback setup；先起一条 HTTPS 隧道再授权，命令行是 openwiki ngrok start，它会保存 OPENWIKI_HTTPS_OAUTH_REDIRECT_URI 供回调使用。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接回答「为什么授权回调不能只挂在本机 http 地址上」这一原因的内容——片段里没有解释原因（例如 OAuth 回调必须使用 HTTPS 之类的说明）。

不过，片段中确实给出了与 Slack OAuth 回调相关的现成办法：

- 文档提到 Slack 源「Requires HTTPS callback setup for OAuth」[7]，即 Slack 的 OAuth 需要 HTTPS 回调设置。
- 提供的现成办法是用 `openwiki ngrok start` 启动 HTTPS 隧道，用于 Slack OAuth，并会保存 `OPENWIKI_HTTPS_OAUTH_REDIRECT_URI` [1]。
- 也可以指定固定域名：`openwiki ngrok start https://your-domain.ngrok.app` [5]。

最小可用示例：

```bash
# 启动 HTTPS 隧道（用于 Slack OAuth）
openwiki ngrok start

# 或使用固定域名
openwiki ngrok start https://your-domain.ngrok.app
```

补充：Slack 还需要先在 `~/.openwiki/.env` 中配置好 app client credentials [3][7]。

如果你要问的是「为什么必须 HTTPS / 为什么本机 http 不行」的具体原因，给出的文档里没有找到，缺少对 OAuth 回调限制的说明。

**top5 片段**：

片段[1] `oss__openwiki__cli-reference#007` ｜ Command reference ｜ Auth and connectors

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

片段[2] `oss__openwiki__customize#004` ｜ Customize OpenWiki ｜ Local configuration directory

```text
| Path | Mode | Purpose |

| --- | --- | --- |

| ~/.openwiki/.env | Both | Provider config, API keys, and connector OAuth tokens |

| ~/.openwiki/openwiki.sqlite | Both | Conversation checkpoint database |

| ~/.openwiki/install-id | Both | Random install ID for anonymous telemetry |

| ~/.openwiki/wiki/ | Personal | Personal mode wiki output |

| ~/.openwiki/INSTRUCTIONS.md | Personal | Personal wiki brief |

| ~/.openwiki/onboarding.json | Personal | Personal onboarding preferences and connector schedules |

| ~/.openwiki/connectors/ | Mostly personal | Connector raw data and config. Personal sources use this path; code-mode LangSmith ingestion can also cache raw data here |
```

片段[3] `oss__openwiki__personal-mode#006` ｜ Personal mode ｜ Connect your sources > Connect a source

```text
- Slack and Gmail require app client credentials to already be set in ~/.openwiki/.env
```

片段[4] `oss__openwiki__personal-mode#005` ｜ Personal mode ｜ Connect your sources > Connect a source

```text
```

openwiki auth notion

openwiki auth gmail

openwiki auth x

openwiki auth slack

```
```

片段[5] `oss__javascript__langchain__multi-agent__router-knowledge-base#048` ｜ Build a multi-source knowledge base with routing ｜ 8. Complete working example

```text
implementation details, issues, pull requests - notion: Internal documentation, processes, policies, team wikis - slack: Team discussions, informal knowledge sharing, recent conversations Return ONLY the sources that are relevant to the query. Each source should have a targeted sub-question optimized for that specific knowledge domain. Example for "How do I authenticate API requests?": - github: "What authentication code exists? Search for auth middleware, JWT handling" - notion: "What authentication documentation exists? Look for API auth guides" (slack omitted because it's not relevant for this technical question)`, }, { role: "user", content: state.query }, ]); return { classifications:
```

---

## v2-H-017（multi-hop）

**问题**：浏览器授权拿到的 token 存在哪？之后想换环境，怎么按已保存的变量重建 connector 配置？

**gold**：OAuth 授权会把 token 存到 ~/.openwiki/.env，这个文件同时还放 provider 配置和 API key；要从已保存的变量重建 connector 配置，用 openwiki auth configure <provider>，必要时加 --force 覆盖已有配置。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. 浏览器 OAuth 拿到的 token 会保存到 `~/.openwiki/.env`，该文件同时存放 provider 配置、API key 和 connector 的 OAuth token [1][2]。
2. 想按已保存的 auth 环境变量重建 connector 配置，用 `openwiki auth configure <provider> [--force]` [1]。

**最小可用示例：**

```bash
# 浏览器 OAuth，token 保存到 ~/.openwiki/.env
openwiki auth gmail

# 之后按已保存的 auth 环境变量重建 connector 配置
openwiki auth configure <provider> [--force]
```

**补充说明：**

- `~/.openwiki/.env` 的用途在文档中标注为「Provider config, API keys, and connector OAuth tokens」，模式为 Both [2]。
- `--force` 是可选参数，用于强制重建 [1]。

**差异提示：** 你问的是「换环境」，但给出的文档片段里没有提到跨环境迁移、复制 `.env` 或同步 token 的具体做法，只说明了 token 的存放位置和重建配置的命令。如果需要迁移步骤，给出的文档里没有找到能回答这部分的内容。

**top5 片段**：

片段[1] `oss__openwiki__cli-reference#007` ｜ Command reference ｜ Auth and connectors

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

片段[2] `oss__openwiki__customize#004` ｜ Customize OpenWiki ｜ Local configuration directory

```text
| Path | Mode | Purpose |

| --- | --- | --- |

| ~/.openwiki/.env | Both | Provider config, API keys, and connector OAuth tokens |

| ~/.openwiki/openwiki.sqlite | Both | Conversation checkpoint database |

| ~/.openwiki/install-id | Both | Random install ID for anonymous telemetry |

| ~/.openwiki/wiki/ | Personal | Personal mode wiki output |

| ~/.openwiki/INSTRUCTIONS.md | Personal | Personal wiki brief |

| ~/.openwiki/onboarding.json | Personal | Personal onboarding preferences and connector schedules |

| ~/.openwiki/connectors/ | Mostly personal | Connector raw data and config. Personal sources use this path; code-mode LangSmith ingestion can also cache raw data here |
```

片段[3] `oss__javascript__langchain__mcp__auth#011` ｜ Authentication ｜ OAuth authentication > Complete the redirect

```text
```

const result = await crm.completeLogin(new URL(req.url, "http://localhost"), userId, sessionId);

// The helper exchanges the code and retries discovery using saved tokens.

// Pass result.tools to your agent, or redirect if another login is required.

```
```

片段[4] `oss__javascript__langchain__mcp__auth#001` ｜ Authentication ｜ Bearer token

```text
``` import { MCPAdapter, UnauthorizedError } from "@langchain/mcp-adapters"; const adapter = new MCPAdapter({ servers: { // A fixed API key, sent as a header. search: { url: "https://search.example.com/mcp", headers: { Authorization: `Bearer ${process.env.SEARCH_API_KEY}` }, }, // A token your app issues and rotates. crm: { url: "https://crm.example.com/mcp", authProvider: { token: async () => tokenStore.current(), onUnauthorized: async () => { // Throw when no newer token exists: over SSE, the SDK calls this // again every time a reconnect is rejected. if (!(await tokenStore.refresh())) { throw new UnauthorizedError("No newer token for the CRM server"); } }, }, }, }, }); ```
```

片段[5] `oss__python__langchain__mcp__auth#001` ｜ Authentication ｜ Bearer token

```text
```

from fastmcp.client import Client

from langchain.mcp import MCPAdapter



async def load_tools_with_bearer(url: str, token: str) -> list:

    # `auth` accepts a bearer-token string, the literal "oauth" (full OAuth 2.1

    # with dynamic client registration), or any `httpx.Auth`.

    async with MCPAdapter(Client(url, auth=token)) as adapter:

        return await adapter.list_tools()

```
```

---

## v2-H-018（multi-hop）

**问题**：老代码把 user_id、session_id 塞在 config["configurable"] 里传给 agent，迁到 v1 后这套值该从哪传进去？

**gold**：v1 用 context 参数取代了 config["configurable"]：先用 dataclass 定义 Context，create_agent 时传 context_schema=Context，调用时写成 agent.invoke({...}, context=Context(user_id="123", session_id="abc"))。

**judge 分**：1.0　**拒答标记**：None

**回答**：

## 结论

迁到 v1 后，**不应该再通过 `config["configurable"]` 传 `user_id` / `session_id` 这类运行时上下文**，而应改用 `create_agent` 的 `context_schema` 声明一个上下文类型，并在 `invoke` 时通过 `context=` 参数传入 [7]。

- 旧写法（`create_react_agent` + `config={"configurable": {...}}`）是迁移前的做法 [1]。
- v1 的 `create_agent` 用 `context_schema=Context` 声明上下文结构，调用时用 `context=Context(user_id="123", session_id="abc")` 传入 [7]。
- 注意 API 名称差异：片段里 v1 用的是 `from langchain.agents import create_agent` [7]，而旧片段用的是 `from langgraph.prebuilt import create_react_agent` [1]，两者不是同一个入口。

另外要区分用途：如果这些值只是想作为**追踪元数据**（trace metadata），片段里展示的是放在 `config` 的 `metadata` 字段里 [2][3]，而不是 `configurable`。这与“运行时上下文”是两回事，别混用。

## 最小可用示例（v1 运行时上下文）

```python
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

来源：[7]

## 补充说明

- 若你的目的其实是“给 trace 打标签/元数据”，片段给出的写法是把 `user_id`、`session_id` 放进 `config` 的 `metadata`（配合 `tags`）[2][3]，或用 `ls.tracing_context(...)` 包裹调用 [8][10]。这与上面的 `context=` 是不同机制。
- 片段 [4] 里出现的 `configurable.thread_id` 是用于**线程/记忆隔离**的，不是用来传 `user_id`/`session_id` 的，别拿它替代上下文传递 [4]。

**top5 片段**：

片段[1] `oss__python__migrate__langchain-v1#040` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Runtime context

```text
```

from langgraph.prebuilt import create_react_agent



agent = create_react_agent(model, tools)



# Pass context via configurable

result = agent.invoke(

    {"messages": [{"role": "user", "content": "Hello"}]},

    config={

        "configurable": {

            "user_id": "123",

            "session_id": "abc"

        }

    }

)

```
```

片段[2] `oss__python__migrate__langchain-v1#039` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Runtime context

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

片段[3] `oss__python__langchain__observability#003` ｜ LangSmith Observability ｜ Add metadata to traces

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

片段[4] `oss__python__langgraph__observability#002` ｜ LangSmith Observability ｜ Add metadata to traces

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

片段[5] `oss__python__deepagents__memory#007` ｜ Memory ｜ Scoped memory > Agent-scoped memory

```text
da rt: ("my-agent",) ), "/skills/": StoreBackend( namespace=lambda rt: ("my-agent",) ), }, ), store=store, ) # Thread 1: the agent learns a new preference and saves it to memory config1 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "I prefer detailed explanations. Remember that."}]}, config=config1, ) # Thread 2: the agent reads memory and applies the preference config2 = {"configurable": {"thread_id": str(uuid7())}} agent.invoke( {"messages": [{"role": "user", "content": "Explain how transformers work."}]}, config=config2, ) ```
```

---

## v2-H-019（multi-hop）

**问题**：多级 agent 要能在工具中断后恢复，checkpointer 该挂在哪一层？外层调用还必须带什么？

**gold**：只给最外层的图编译时挂 checkpointer，子 agent 不要传 checkpointer，让它们按每次调用继承父级的检查点；外层 invoke() 或 stream_events() 的 configurable 里必须带 thread_id，图才有地方落检查点并恢复。

**judge 分**：0.5　**拒答标记**：None

**回答**：

**结论：**

1. **checkpointer 只挂在顶层（top-level）agent 上**，不需要给每个子 agent 都挂。文档明确说「We add a checkpointer only to the top-level agent. This is required to pause and resume execution.」[1][2]
2. **外层调用必须带 `thread_id`（线程配置）**，否则无法按线程暂停/恢复。片段 [3] 的注释也提示：per-thread 子 agent 若被并行调用会造成 checkpoint 冲突，因此要用 `ToolCallLimitMiddleware` 限制并行调用 [3][11]。

**最小可用示例（Python，基于片段 [3][11] 的结构）：**

```python
from langgraph.checkpoint.memory import MemorySaver
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware

agent = create_agent(
    model="gpt-5.4-mini",
    tools=[ask_fruit_expert],
    system_prompt="You have a fruit expert. ALWAYS delegate fruit questions to ask_fruit_expert.",
    middleware=[
        # 防止并行调用 per-thread 子 agent 导致 checkpoint 冲突
        ToolCallLimitMiddleware(tool_name="ask_fruit_expert", run_limit=1),
    ],
    checkpointer=MemorySaver(),  # 只挂在顶层
)

# 外层调用必须带 thread_id
config = {"configurable": {"thread_id": "thread-1"}}
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]}, config)
```

**需要指出的差异/注意点：**

- 片段里 checkpointer 的类名在不同页面不一致：LangGraph 页面用 `MemorySaver` [3][11]，Python deepagents 页面用 `MemorySaver`（从 `langgraph.checkpoint.memory` 导入）[5]，而 Python 多 agent 页面示例里出现的是 `InMemorySaver` [9]。以你所用页面的导入为准。
- 片段 [3][11] 只给出了 `checkpointer=MemorySaver()` 和 `ToolCallLimitMiddleware` 的用法，**没有直接展示 `thread_id` 的传参代码**；「外层调用必须带 thread_id」是从「per-thread」语义与「pause and resume execution」推断的必要条件，片段中未给出完整调用示例。若你需要精确的调用签名，给出的文档里没有找到对应内容。

**top5 片段**：

片段[1] `oss__javascript__langchain__multi-agent__subagents-personal-assistant#049` ｜ Build a personal assistant with subagents ｜ 6. Add human-in-the-loop review

```text
- We add a checkpointer only to the top-level agent . This is required to pause and resume execution.
```

片段[2] `oss__python__langchain__multi-agent__subagents-personal-assistant#049` ｜ Build a personal assistant with subagents ｜ 6. Add human-in-the-loop review

```text
- We add a checkpointer only to the top-level agent . This is required to pause and resume execution.
```

片段[3] `oss__python__langgraph__use-subgraphs#029` ｜ Subgraphs ｜ View example trace > Per-thread

```text
.", checkpointer=True, ) # Wrap subagent as a tool for the outer agent @tool def ask_fruit_expert(question: str) -> str: """Ask the fruit expert. Use for ALL fruit questions.""" response = fruit_agent.invoke( {"messages": [{"role": "user", "content": question}]}, ) return response["messages"][-1].content # Outer agent with checkpointer # Use ToolCallLimitMiddleware to prevent parallel calls to per-thread subagents, # which would cause checkpoint conflicts. agent = create_agent( model="gpt-5.4-mini", tools=[ask_fruit_expert], system_prompt="You have a fruit expert. ALWAYS delegate fruit questions to ask_fruit_expert.", middleware=[
```

片段[4] `oss__javascript__deepagents__customization#186` ｜ Customize Deep Agents ｜ View example trace

```text
```

import { createDeepAgent, FilesystemBackend } from "deepagents";

import { MemorySaver } from "@langchain/langgraph";



// Checkpointer is REQUIRED for human-in-the-loop

const checkpointer = new MemorySaver();



const agent = await createDeepAgent({

  model: "openai:gpt-6.1-sol",

  backend: new FilesystemBackend({ rootDir: "/Users/user/{project}" }),

  memory: ["./AGENTS.md", "./.deepagents/AGENTS.md"],

  interruptOn: {

    read_file: true,

    write_file: true,

    delete_file: true,

  },

  checkpointer, // Required!

});

```
```

片段[5] `oss__python__deepagents__customization#220` ｜ Customize Deep Agents ｜ Memory

```text
``` from deepagents import create_deep_agent from deepagents.backends import FilesystemBackend from langgraph.checkpoint.memory import MemorySaver # Checkpointer is REQUIRED for human-in-the-loop checkpointer = MemorySaver() agent = create_deep_agent( model="fireworks:accounts/fireworks/models/glm-5p2", backend=FilesystemBackend(root_dir="/Users/user/{project}"), memory=[ "./AGENTS.md" ], interrupt_on={ "write_file": True,  # Default: approve, edit, reject "read_file": False,  # No interrupts needed "edit_file": True,   # Default: approve, edit, reject }, checkpointer=checkpointer,  # Required! ) result = agent.invoke( { "messages": [ { "role": "user", "content":
```

---

## v2-H-020（multi-hop）

**问题**：把单个 MCP 工具转成 LangChain 工具，v1 里 import 路径和调用写法都变了，具体怎么改？

**gold**：换成从 langchain.mcp import as_langchain_tool（原来的 convert_mcp_tool_to_langchain_tool 改名而来）；而且它现在是 coroutine，要写成 await as_langchain_tool(tool, client)。

**judge 分**：1.0　**拒答标记**：None

**回答**：

结论：在 Python 侧，`convert_mcp_tool_to_langchain_tool` 已改名为 `as_langchain_tool`，并且从同步函数变成了协程，需要 `await` 调用；import 路径也从 `langchain_mcp_adapters.tools` 变为 `langchain.mcp` [4][5]。

具体改动：
- 旧：`from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool` [4]
- 新：`from langchain.mcp import as_langchain_tool`（已重命名）[4]
- 调用写法：现在是协程，需写成 `await as_langchain_tool(tool, client)` [5]

最小可用示例（Python）：

```python
from langchain.mcp import as_langchain_tool

# tool 为 MCP 工具，client 为对应的 MCP 客户端
lc_tool = await as_langchain_tool(tool, client)
```

补充说明：
- 片段中只给出了 Python 侧的这组改名与调用变化 [4][5]；关于 JavaScript 侧单个工具转换的对应 API，给出的文档里没有找到能回答这个问题的内容，缺少 JS 侧 `convert_mcp_tool_to_langchain_tool` 等价物的迁移说明。
- 另外注意：`to_fastmcp`（LangChain 工具 → FastMCP 工具）目前在 `langchain.mcp` 中还没有等价物 [5]。

**top5 片段**：

片段[1] `oss__javascript__migrate__langchain-mcp-adapters#000` ｜ Migrate to @langchain/mcp-adapters 2.0 ｜ ROOT

```text
Migrate to @langchain/mcp-adapters 2.0 Upgrade from @langchain/mcp-adapters 1.x to 2.0, covering renamed APIs, stricter configuration, authentication, elicitation, and tool result changes.
```

片段[2] `oss__javascript__langchain__mcp__tools#000` ｜ Tools ｜ ROOT

```text
Tools Load MCP tools into LangChain agents, control their execution, and handle server results and requests.
```

片段[3] `oss__python__langchain__mcp__tools#000` ｜ Tools ｜ ROOT

```text
Tools Load MCP tools into LangChain agents, control their execution, and handle server results and requests.
```

片段[4] `oss__python__migrate__langchain-mcp-adapters#001` ｜ Migrate from langchain-mcp-adapters ｜ Import paths

```text
| langchain-mcp-adapters | langchain.mcp |

| --- | --- |

| from langchain_mcp_adapters.client import MultiServerMCPClient | from langchain.mcp import MCPAdapter |

| from langchain_mcp_adapters.tools import load_mcp_tools | from langchain.mcp import MCPAdapter (use MCPAdapter(...).list_tools() ) |

| from langchain_mcp_adapters.tools import convert_mcp_tool_to_langchain_tool | from langchain.mcp import as_langchain_tool (renamed) |

| from langchain_mcp_adapters.tools import MCPToolArtifact | from langchain.mcp import MCPToolArtifact |
```

片段[5] `oss__python__migrate__langchain-mcp-adapters#014` ｜ Migrate from langchain-mcp-adapters ｜ Tool results

```text
| langchain-mcp-adapters | langchain.mcp |

| --- | --- |

| MCPToolArtifact (structured content) | Kept. Exported from langchain.mcp . See structured content . |

| Multimodal content blocks | Kept. See multimodal content . |

| Tool metadata | Extended. Grouped under an mcp namespace on the tool’s metadata, with annotations and server identity. See tool metadata . |

| convert_mcp_tool_to_langchain_tool | Renamed to as_langchain_tool , and now a coroutine: await as_langchain_tool(tool, client) . |

| to_fastmcp (LangChain tool → FastMCP tool) | No langchain.mcp equivalent yet. If you convert LangChain tools into MCP tools, open an issue — we would like to hear about the use case. |
```

---

## v2-H-021（multi-hop）

**问题**：给包加一个可选依赖，怎么保证没装它的用户不受影响？需要这个依赖的单测又该怎么标？

**gold**：没装依赖的用户必须仍然能够 import 你的代码，而且不能有任何副作用（不要有 warning、error 或 exception）；需要该依赖的单测用 @pytest.mark.requires("package_name") 标记。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：**

1. 没装该依赖的用户必须能正常 import 你的代码，且不产生任何副作用（无警告、无错误、无异常）[2]。
2. 需要该依赖的单元测试，用 `@pytest.mark.requires("package_name")` 装饰器标注 [1]。

**最小可用示例：**

```python
# 代码中延迟/可选导入，保证未安装依赖时 import 无副作用
try:
    import optional_pkg
except ImportError:
    optional_pkg = None
```

```python
import pytest

@pytest.mark.requires("optional_pkg")
def test_something_using_optional_pkg():
    ...
```

**补充说明：** 片段 [8][9][10] 还提到，若要把依赖变成硬依赖（而非可选），需先开 issue 说明原因、添加至少能尝试 import 新代码的单测、并把依赖加到相应的测试依赖文件（如 `extended_testing_deps.txt`）——但这属于「硬依赖」流程，与你的「可选依赖」问题不同，仅供参考。

**top5 片段**：

片段[1] `oss__python__contributing__code#034` ｜ Contributing to code ｜ Development workflow > Dependencies

```text
3. Use the @pytest.mark.requires("package_name") decorator for any unit tests that require the dependency.
```

片段[2] `oss__python__contributing__code#031` ｜ Contributing to code ｜ Development workflow > Dependencies

```text
- Users without the dependency installed must be able to import your code without any side effects (no warnings, no errors, no exceptions)
```

片段[3] `oss__python__contributing__code#032` ｜ Contributing to code ｜ Development workflow > Dependencies

```text
1. Add the dependency to the appropriate testing dependencies file (e.g., extended_testing_deps.txt )
```

片段[4] `oss__python__langgraph__application-structure#006` ｜ Application structure ｜ Dependencies

```text
1. A file in the directory that specifies the dependencies (e.g. requirements.txt , pyproject.toml , or package.json ).
```

片段[5] `oss__javascript__contributing__code#008` ｜ Contributing to code ｜ Development environment

```text
```

pnpm install

pnpm --filter {package-name} test  # Verify tests pass before starting development

```
```

---

## v2-H-022（paraphrase）

**问题**：我把两个项目各自生成了一份文档，一搜东西它就反问我到底指哪一份，这是为什么？

**gold**：因为那个页面同时属于多个 workspace，而当时没有 active selection，搜索会返回 workspace_required，让 agent 反问你要用哪个 workspace。

**judge 分**：1.0　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接解释「为什么它会反问你指哪一份」的完整原因，只找到一条相关线索：

- 当查询命中多个 workspace 且没有激活的选择时，搜索会返回 `workspace_required`，然后 agent 会询问使用哪个 workspace [2]。

也就是说，片段 [2] 描述的现象和你遇到的情况一致：多份文档/多个 workspace 同时存在、又没有指定当前 workspace 时，搜索无法确定范围，于是让 agent 反问用户。但片段里没有说明如何设置或切换默认 workspace 来避免这个反问（片段 [11] 只列出了 `openwiki workspace use/current/clear` 命令，未给出完整用法说明），因此无法给出可靠的最小示例。

如果你希望我基于片段给出可操作步骤，需要补充：workspace 选择/默认值配置相关的文档片段。

**top5 片段**：

片段[1] `oss__javascript__deepagents__rag#043` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ Build the agent

```text
a.source ?? "unknown"}\n\n${doc.pageContent}`; uploads.push([path, encoder.encode(content)]); savedPaths.push(path); }); backend.uploadFiles(uploads); return `Saved ${savedPaths.length} documentation chunks:\n${savedPaths.join("\n")}`; }, { name: "search_documentation", description: "Search LangChain documentation and save matching chunks to the agent filesystem.", schema: z.object({ query: z.string().describe("Natural language search query."), }), }, ); ```
```

片段[2] `oss__openwiki__search-and-link#005` ｜ Search and link wikis ｜ Create wiki workspaces > Search scope

```text
4. If it belongs to multiple workspaces without an active selection, search returns workspace_required and the agent asks which workspace to use.
```

片段[3] `oss__javascript__langchain__knowledge-base#025` ｜ Build a semantic search engine with LangChain ｜ Use retrievers

```text
```

[

    [Document {

        metadata: {'page': 4, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 3125},

        pageContent: 'direct to consumer operations sell products...',

    }],

    [Document {

        metadata: {'page': 3, 'source': '../example_data/nke-10k-2023.pdf', 'start_index': 0},

        pageContent: 'Table of Contents...',

    }],

]

```
```

片段[4] `oss__javascript__langgraph__use-subgraphs#035` ｜ Subgraphs ｜ Subgraph persistence > Stateful > Per-thread

```text
ld cause checkpoint conflicts. const agent = createAgent({ model: "gpt-5.4-mini", tools: [askFruitExpert], systemPrompt: "You have a fruit expert. ALWAYS delegate fruit questions to ask_fruit_expert.", middleware: [ toolCallLimitMiddleware({ toolName: "ask_fruit_expert", runLimit: 1 }), ], checkpointer: new MemorySaver(), }); ```
```

片段[5] `oss__python__deepagents__rag#004` ｜ Retrieval Augmented Generation (RAG) with Deep Agents ｜ RAG patterns

```text
- Retrieve, offload, and delegate : The user asks a question. The agent retrieves matching chunks and writes them to the filesystem backend rather than keeping full text in the orchestrator context. Subagents read, search, and summarize individual files in parallel. For large documents, the agent can paginate through files with built-in search tools or run a code interpreter to produce tables, timelines, or visuals from source data.
```

---

## v2-H-023（paraphrase）

**问题**：我把工具直接绑在模型对象上再交进去，升级后这套写法为什么不管用了？应该怎么改？

**gold**：把工具绑在模型对象上再传进去的写法不再支持：ChatOpenAI().bind_tools([some_tool]) 配合 create_agent(model_with_tools, tools=[]) 要去掉，改成 create_agent("gpt-5.4-mini", tools=[some_tool])，工具直接交给 create_agent。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：** 在 v1 里，`create_agent` 不再接受「已经用 `bind_tools` 绑好工具的模型对象」作为 `model` 参数。正确做法是把**原始模型（或模型名）**和**工具列表**分别传给 `create_agent`，由它自己完成绑定 [2][5]。

**原因与差异说明：**
- 文档明确把「先 `bind_tools` 再传入 `create_agent`」标为 *No longer supported* [2][5]。
- 另外注意 `bind_tools` 的返回类型在 v1 有变化：片段 [1] 写的是 `Runnable[LanguageModelInput, BaseMessage]`，而相邻补全片段 [10] 写的是 `Runnable[LanguageModelInput, AIMessage]`。两处片段本身不一致，这里只如实指出差异，不替文档下结论。

**最小可用示例（Python）：**

```python
# 不再支持的写法
# model_with_tools = ChatOpenAI().bind_tools([some_tool])
# agent = create_agent(model_with_tools, tools=[])

# 改为
from langchain.agents import create_agent

agent = create_agent("gpt-5.4-mini", tools=[some_tool])
```

[2]

**最小可用示例（JavaScript）：**

```javascript
// 不再支持的写法
// const modelWithTools = new ChatOpenAI({ model: "gpt-5.4-mini" }).bindTools([someTool]);
// const agent = createAgent({ model: modelWithTools, tools: [] });

// 改为
const agent = createAgent({ model: "gpt-5.4-mini", tools: [someTool] });
```

[5]

**补充：** 如果你只是想「直接调用模型并手动处理工具调用」（不走 `create_agent`），`model.bind_tools(tools)` 这种用法在模型文档里仍然存在，配合 `invoke` 和 `tool_calls` 使用 [3][14]。也就是说，受限的是「把预绑定模型交给 `create_agent`」这一路径，而不是 `bind_tools` 本身。

**top5 片段**：

片段[1] `oss__python__migrate__langchain-v1#049` ｜ LangChain v1 migration guide ｜ Breaking changes > Updated return type for chat models

```text
```

def bind_tools(

        ...

    ) -> Runnable[LanguageModelInput, BaseMessage]:

```
```

片段[2] `oss__python__migrate__langchain-v1#029` ｜ LangChain v1 migration guide ｜ Migrate to create_agent > Model > Pre-bound models

```text
```

# No longer supported

model_with_tools = ChatOpenAI().bind_tools([some_tool])

agent = create_agent(model_with_tools, tools=[])



# Use instead

agent = create_agent("gpt-5.4-mini", tools=[some_tool])

```
```

片段[3] `oss__python__langchain__models#034` ｜ Models ｜ Tool calling

```text
``` # Bind (potentially multiple) tools to the model tools = [get_weather] tools_by_name = {tool.name: tool for tool in tools} model_with_tools = model.bind_tools(tools) # Step 1: Model generates tool calls messages = [{"role": "user", "content": "What's the weather in Boston?"}] ai_msg = model_with_tools.invoke(messages) messages.append(ai_msg) # Step 2: Execute tools and collect results for tool_call in ai_msg.tool_calls: # Execute the tool with the generated arguments tool = tools_by_name[tool_call["name"]] tool_result = tool.invoke(tool_call) messages.append(tool_result) # Step 3: Pass results back to model for final response final_response = model_with_tools.invoke(messages)
```

片段[4] `oss__javascript__langchain__models#033` ｜ Models ｜ Tool calling

```text
```

const modelWithTools = model.bindTools([tool_1], { toolChoice: "tool_1" })

```
```

片段[5] `oss__javascript__migrate__langchain-v1#020` ｜ LangChain v1 migration guide ｜ createAgent > Model > Pre-bound models

```text
```

// No longer supported

// const modelWithTools = new ChatOpenAI({ model: "gpt-5.4-mini" }).bindTools([someTool]);

// const agent = createAgent({ model: modelWithTools, tools: [] });



// Use instead

const agent = createAgent({ model: "gpt-5.4-mini", tools: [someTool] });

```
```

---

## v2-H-024（paraphrase）

**问题**：它说会收集匿名使用数据，那我程序报错的具体内容会被一起传上去吗？

**gold**：不会。每次记录只包含命令（init 或 update）、结果（success、failure、no-op）以及失败时的粗粒度错误类别，从不记录错误原文；交互式 chat、auth 和 ingest 也不记录。

**judge 分**：1.0　**拒答标记**：None

**回答**：

**结论：不会。** 根据文档，失败时只记录一个粗粒度的错误类别（coarse error category），明确注明「never the error message」，即不会上传具体错误信息 [2]。

另外，遥测记录的是每次运行的命令（init / update）和结果（success / failure / no-op），交互式聊天、auth 和 ingest 都不记录 [2]。初始化时也只记录 brain 模式、模型提供商和已配置的连接器名称，不记录其内容 [10]。

**最小示例（说明边界，非可运行代码）：**

```text
记录内容示例：
- command: update
- outcome: failure
- error_category: <粗粒度类别>   # 不含 error message
```

**需要说明的差异/缺口：**
- 你问的是「程序报错的具体内容」，文档只覆盖了 openwiki 的遥测范围 [2][10]，没有说明其他组件（如 LangChain 中间件、agent 运行）是否也有遥测，因此无法据此推断全局行为。
- 片段 [2] 未列出「粗粒度错误类别」具体包含哪些取值，若你需要精确字段清单，给出的文档里没有找到。

**top5 片段**：

片段[1] `oss__python__langchain__middleware__built-in#004` ｜ Prebuilt middleware ｜ Provider-agnostic middleware > Tool error

```text
- Surfacing controlled, sanitized error messages instead of raw exception details.
```

片段[2] `oss__openwiki__customize#005` ｜ Customize OpenWiki ｜ Telemetry

```text
- Every recorded run: the command ( init / update ) and outcome ( success / failure / no-op ), plus a coarse error category on failure (never the error message). Interactive chat, auth , and ingest are not recorded
```

片段[3] `oss__python__langchain__structured-output#047` ｜ Structured output ｜ Tool calling strategy > Error handling > Error handling strategies

```text
Strategy( schema=Union[ContactInfo, EventDetails], handle_errors=custom_error_handler )  # Default: handle_errors=True ) result = agent.invoke({ "messages": [{"role": "user", "content": "Extract info: John Doe (john@email.com) is organizing Tech Conference on March 15th"}] }) for msg in result['messages']: # If message is actually a ToolMessage object (not a dict), check its class name if type(msg).__name__ == "ToolMessage": print(msg.content) # If message is a dictionary or you want a fallback elif isinstance(msg, dict) and msg.get('tool_call_id'): print(msg['content']) ```
```

片段[4] `oss__openwiki__customize#004` ｜ Customize OpenWiki ｜ Local configuration directory

```text
| Path | Mode | Purpose |

| --- | --- | --- |

| ~/.openwiki/.env | Both | Provider config, API keys, and connector OAuth tokens |

| ~/.openwiki/openwiki.sqlite | Both | Conversation checkpoint database |

| ~/.openwiki/install-id | Both | Random install ID for anonymous telemetry |

| ~/.openwiki/wiki/ | Personal | Personal mode wiki output |

| ~/.openwiki/INSTRUCTIONS.md | Personal | Personal wiki brief |

| ~/.openwiki/onboarding.json | Personal | Personal onboarding preferences and connector schedules |

| ~/.openwiki/connectors/ | Mostly personal | Connector raw data and config. Personal sources use this path; code-mode LangSmith ingestion can also cache raw data here |
```

片段[5] `oss__javascript__integrations__middleware#001` ｜ Middleware integrations ｜ Official integrations

```text
l calls with BRYDGE and checks the destination system’s own records to report whether each action happened as permitted. | contactkontey-dotcom/langchain-brydge |  | | Sanity Context | Agent middleware for Sanity Context: cited facts from Knowledge Bases built from your content, or a live Sanity dataset. | sanity-io/context |  | | RecallChatMessageHistory | Chat message history stored in a Recall session, so Recall also learns about the user from it. | recallmem/recall |  | | RuthlessSchemaGuard | Agent middleware that validates tool and HTTP responses against Pydantic or JSON Schema and raises on violations. | moltbot-den/openentity |  |
```

---

## v2-H-025（paraphrase）

**问题**：缓存那套里有个参数，管的是「攒多少文档才往存储里写一次」，它的默认行为是什么？

**gold**：那是 batch_size，可选，默认 None，意思是每批嵌入多少文档之后才更新一次存储。

**judge 分**：0.5　**拒答标记**：None

**回答**：

给出的文档里没有找到能直接回答「攒多少文档才往存储里写一次」这个参数默认行为的完整内容。

现有片段中只有一处相关描述：

- `batch_size`：可选，默认值为 `None`，含义是「在两次存储更新之间要嵌入的文档数量」[1]。

也就是说，片段只说明了 `batch_size` 的默认值是 `None` [1]，但**没有说明当它为 `None` 时实际的攒批/写入行为是什么**（例如是否等于不攒批、逐条写入，或由底层实现决定）。因此无法根据给出的文档确认其默认行为。

另外提醒一处可能的名称差异：你问的是「缓存那套里」的参数，而片段 [1] 中该参数名为 `batch_size`，并非 `namespace`（`namespace` 是文档缓存的命名空间参数，默认 `""`，用于避免冲突 [2][9]）。如果你指的是别的参数名，请以片段中的 `batch_size` 为准 [1]。

**top5 片段**：

片段[1] `oss__python__integrations__embeddings#016` ｜ Embedding model integrations ｜ Caching

```text
- batch_size : (optional, defaults to None ) The number of documents to embed between store updates.
```

片段[2] `oss__javascript__integrations__embeddings#014` ｜ Embedding model integrations ｜ Caching

```text
- options.namespace : (optional, defaults to "" ) The namespace to use for the document cache. Helps avoid collisions (e.g., set it to the embedding model name).
```

片段[3] `oss__python__deepagents__interpreters#060` ｜ Interpreters ｜ Configuration

```text
True uses the backend from create_deep_agent . See Files ( fs ) . | | mode | "thread" | Control interpreter persistence: "thread" (across turns), "turn" (within one turn), or "call" (fresh REPL per eval ). See Persistence . | | max_snapshot_bytes | None | Drop snapshots larger than this byte limit. Defaults to memory_limit . See Persistence . |
```

片段[4] `oss__javascript__deepagents__human-in-the-loop#001` ｜ Human-in-the-loop ｜ Basic configuration

```text
- True : Enable interrupts with default behavior (approve, edit, and reject allowed)
```

片段[5] `oss__javascript__langgraph__frontend__custom-stream-channels#019` ｜ Custom stream channels ｜ Buffer raw events with useChannel

```text
| Option | Default | Effect |

| --- | --- | --- |

| bufferSize | "default" | Maximum number of buffered events. Older events drop once the cap is reached. |

| replay | true | Replay events already seen on the channel when the selector mounts, instead of only live events. |
```

---

## v2-H-026（paraphrase）

**问题**：我不查自己的资料库，只想让它直接上网搜，库里有没有现成的东西？

**gold**：有。这一组是走公网搜索的：ApifySearchRetriever 通过 Apify RAG Web Browser 做 Internet search，另外还有 DiffbotWebSearchRetriever、ParallelSearchRetriever、PerplexitySearchRetriever、YouRetriever；它们查的是互联网，不是你自己的资料。

**judge 分**：0.0　**拒答标记**：None

**回答**：

结论：有现成的做法，但需要区分「内置联网搜索」和「第三方搜索工具」两类，且不同语言/提供方的写法不一致。

**1. 用模型厂商内置的 web search（无需额外安装或 API key）**

- JavaScript 版 Deep Agents 里，Anthropic 内置搜索写成 `{ type: "web_search_20250305", name: "web_search" }` [1]。
- Python 版 Deep Agents 里，Anthropic 内置搜索写成 `{"type": "web_search_20260209", "name": "web_search"}` [3]。注意两处版本号不同（`20250305` vs `20260209`），以各自片段为准。
- JavaScript 版里 OpenAI 内置搜索写成 `{ type: "web_search_preview" }` [8]；Python 版里 OpenAI 内置搜索写成 `{"type": "web_search"}` [11]。注意 JS 与 Python 的写法不同，不要混用。

**2. 用 Tavily 作为搜索工具（需要 `TAVILY_API_KEY`）**

- JavaScript 版用 `@langchain/tavily` 的 `TavilySearch` 包成 `tool(...)`，工具名 `internet_search` [7]。
- Python 版直接用 `TavilyClient` 写一个 `internet_search` 函数 [10]。
- Python 的 content-builder 示例里也有一个 `web_search` 工具，内部用 `TavilyClient`，参数含 `query`、`max_results`、`topic`（`"general"`/`"news"`）[6]。

**最小可用示例（JavaScript，Anthropic 内置搜索）**

```javascript
import { createDeepAgent } from "deepagents";

// Anthropic's built-in web search — no extra install or API key needed
const internetSearch = { type: "web_search_20250305", name: "web_search" };
```

**最小可用示例（Python，Anthropic 内置搜索）**

```python
from deepagents import create_deep_agent

# Anthropic's built-in web search — no extra install or API key needed
internet_search = {"type": "web_search_20260209", "name": "web_search"}
```

**需要指出的差异/缺口**

- 你问的是「不查自己的资料库、直接上网搜」。片段里确实有内置 web search 和 Tavily 搜索工具，但没有片段说明如何「禁用/绕过本地资料库检索」这一配置项，因此这一点给出的文档里没有找到能回答的内容。
- 片段 [2] 只提到 OpenAI web search 有「Non-reasoning web search」用于快速查询 [2]，片段 [9] 提到「Agentic search with reasoning models」由模型主动管理搜索过程 [9]，但没有给出具体调用参数。
- 片段 [4] 是 Anthropic 的 citations/search results 示例，属于 RAG 工具返回搜索结果并带引用的用法 [4]，不是「直接上网搜」的配置，别把它当成联网搜索开关。
- 片段 [5] 是检索优化里的 `retrieve` 工具（查向量库）[5]，属于「查自己的资料库」，与你的需求相反，不要用这个。

**top5 片段**：

片段[1] `oss__javascript__deepagents__quickstart#009` ｜ Quickstart ｜ Step 3: Create a search tool

```text
```

import { createDeepAgent } from "deepagents";



// Anthropic's built-in web search — no extra install or API key needed

const internetSearch = { type: "web_search_20250305", name: "web_search" };

```
```

片段[2] `oss__javascript__integrations__tools__openai#000` ｜ OpenAI integration ｜ Web search tool

```text
1. Non-reasoning web search : Quick lookups where the model passes queries directly to the search tool
```

片段[3] `oss__javascript__deepagents__quickstart#008` ｜ Quickstart ｜ Step 3: Create a search tool

```text
```

import { createDeepAgent } from "deepagents";



// OpenAI's built-in web search — no extra install or API key needed

const internetSearch = { type: "web_search_preview" };

```
```

片段[4] `oss__python__deepagents__quickstart#009` ｜ Quickstart ｜ Step 3: Create a search tool

```text
```

from deepagents import create_deep_agent



# Anthropic's built-in web search — no extra install or API key needed

internet_search = {"type": "web_search_20260209", "name": "web_search"}

```
```

片段[5] `oss__python__deepagents__quickstart#008` ｜ Quickstart ｜ Step 3: Create a search tool

```text
```

from deepagents import create_deep_agent



# OpenAI's built-in web search — no extra install or API key needed

internet_search = {"type": "web_search"}

```
```

---
