**English** | [한국어](README.ko.md)

# Can you trust an AI answer?

**A self-guided Microsoft Foundry Evaluation workshop**

**Jump to:** [Choose a path](#choose-path) · [Setup](#setup-map) · [Resume](docs/en/setup.md#resume)

Check whether the fictional **Gaon Lab travel-expense assistant** follows policy. This is **evaluation**. Copy the commands, run them, and read the results. **No Python coding is required.**

**The learning loop:** define criteria → check answers → improve instructions → test fresh questions → make an evidence-based decision.

**New to evaluation or without Azure? Start with [free DEMO](docs/en/offline.md#lab-0).** Choose [Introductory LIVE](docs/en/intro-lab.md#lab-0) to evaluate a real model, or [Complete RAG](docs/en/complete-lab.md#architecture) to include retrieval.

**Language:** the guides are in English, but policy inputs, questions, prompts, and CLI output remain **Korean** so both guides run the same experiment. Use the [English policy translation](docs/en/policies.md) for reading, not as a replacement input.

<details>
<summary>Workshop inspiration and recorded results</summary>

Inspired by [Satya Nadella's post on building a frontier ecosystem](https://snscratchpad.com/posts/frontier-ecosystem/). Evaluate and improve AI against your own business criteria, not just external rankings.

[Recorded results](docs/en/reference.md#live-verification) are examples, not target scores. Judge your own results; do not rerun to match someone else's scores.

</details>

<a id="choose-path"></a>
## Choose one learning path

**Choose one row.** You do not need to complete another path first.

| Path | Choose it to… | Environment and cost |
|---|---|---|
| **[DEMO — start here if new](docs/en/offline.md)** | Learn the evaluation workflow without Azure | Python only. **Free, authored examples**, not a performance measurement |
| [Introductory LIVE](docs/en/intro-lab.md) | Learn evaluation and prompt improvement without retrieval | Foundry project and one model deployment. **Paid** |
| [Complete RAG](docs/en/complete-lab.md) | Connect retrieval, dialogue improvement, and fresh-question validation | Required model version, three deployments, Basic-or-higher Search. **Paid** |
| [Optional RAG — retrieval comparison](docs/en/optional-rag.md) | Compare direct Search with Knowledge Base retrieval | Shared setup and Basic-or-higher Search. **Paid** |

**LIVE makes real Azure calls; RAG answers using retrieved evidence.** Paid paths require an active subscription and access. Your guide covers resource creation and permissions. [Reuse existing resources](docs/en/setup.md#existing-environment) only with the owner's permission.

> [!IMPORTANT]
> **Execution completion ≠ passing answers.** Low scores or `BLOCK` (unmet quality criteria) are learning outcomes. If LIVE is blocked, [switch to DEMO](docs/en/setup.md#switch-to-demo) without mixing the results.

<a id="prepare"></a>
<a id="setup-map"></a>
## Shared setup shortcuts

**[Shared setup 1–7](docs/en/setup.md#prepare)** serves the LIVE paths. Return to your chosen guide afterward. DEMO uses only [its own setup](docs/en/offline.md#prepare).

| Find a step | Guide |
|---|---|
| <a id="setup-tools"></a>1. Code and tools | [Folder, terminal, and virtual environment](docs/en/setup.md#setup-tools) |
| <a id="setup-sign-in"></a>2. Sign-in | [Account, subscription, and tenant](docs/en/setup.md#setup-sign-in) |
| <a id="setup-project"></a>3. Project | [Dedicated group and Foundry project](docs/en/setup.md#setup-project) |
| <a id="setup-permissions"></a>4. Permissions | [Your user and the project identity](docs/en/setup.md#setup-permissions) |
| <a id="setup-model"></a>5. Model | [Model name, version, and deployment name](docs/en/setup.md#setup-model) |
| <a id="setup-config"></a>6. Configuration | [Actual endpoint in `config.json`](docs/en/setup.md#setup-config) |
| <a id="setup-smoke"></a>7. Connectivity | [Generate and evaluate N01](docs/en/setup.md#setup-smoke) |

Do not recreate an existing environment. [New-environment CLI setup](docs/en/setup.md#cli-provision) is an **alternative to portal steps 3–5**, not an extra task.

<a id="lab-map"></a>
## Introductory LIVE shortcuts

Use the [introductory progress map](docs/en/intro-lab.md#lab-map) **only if you chose that path**.

<a id="reading-guide"></a>
[How to read the guide](docs/en/intro-lab.md#reading-guide): follow **action → command → checkpoint → next step**.

| Find a step | Guide |
|---|---|
| <a id="lab-0"></a>0. Spot the mistake | [Judge policy and answers before installation](docs/en/intro-lab.md#lab-0) |
| <a id="lab-1"></a>1. Set criteria | [Fix expected behavior and thresholds](docs/en/intro-lab.md#lab-1) |
| <a id="lab-2"></a>2. Baseline answers | [Generate eight dev answers with V1](docs/en/intro-lab.md#lab-2) |
| <a id="lab-3"></a>3. Foundry evaluation | [Compare code, a judge, and your judgment](docs/en/intro-lab.md#lab-3) |
| <a id="lab-4"></a>4. Improve and compare | [Change only instructions; check regressions](docs/en/intro-lab.md#lab-4) |
| <a id="lab-5"></a>5. Fresh questions | [Four holdout cases and a decision](docs/en/intro-lab.md#lab-5) |
| <a id="lab-6"></a>6. Apply it yourself | [One extra question and four final sentences](docs/en/intro-lab.md#lab-6) |
| <a id="finish"></a>Finish | [Completion checklist](docs/en/intro-lab.md#finish) |
| <a id="working-files"></a>Working files | [Which three files to edit, and when](docs/en/intro-lab.md#working-files) |
| <a id="validate-extra"></a>Validate your question | [Check JSONL before paid calls](docs/en/intro-lab.md#validate-extra) |

<a id="help"></a>
## Look up help when needed

| Need | Guide |
|---|---|
| <a id="command-status"></a>Understand command output | [Complete, waiting, errors, and BLOCK](docs/en/setup.md#command-status) |
| Continue interrupted work | [Resumption and result-file checkpoints](docs/en/setup.md#resume) |
| Installation, access, model, or score problems | [Troubleshooting](docs/en/reference.md#troubleshooting) |
| <a id="retain-resources"></a>Default finish | [Retain results/resources and check costs](docs/en/cleanup.md#retain-resources) |
| <a id="delete-resources"></a>A separate later deletion decision | [Owner approval, scope, and deletion](docs/en/cleanup.md#delete-resources) |
| Terms, evaluation criteria, and official sources | [Detailed reference](docs/en/reference.md) |
| Lead a group | [Facilitator guide](docs/en/facilitator.md) |
| Watch an example result | [English/Korean summaries and subtitles](docs/media/README.md) |

**Retain resources by default.** Closing a terminal does not remove resources or stop their costs. Do not enter real personal data, confidential information, or passwords.
