**English** | [한국어](README.ko.md)

# Can you trust an AI answer?

**Microsoft Foundry Evaluation: an end-to-end, self-guided workshop**

Find out whether the fictional **Gaon Lab travel-expense assistant** follows policy. Evaluation means **checking AI answers against criteria chosen in advance**. Run the provided commands and read the answers; **you do not need to write Python**.

**Recommended path:** [Complete RAG — failure → V2 improvement → fresh-question validation](docs/en/complete-lab.md). Follow **sections 1–8 there** for real retrieval and answer improvement. This README contains **introductory LIVE, without retrieval**.

**Language:** the guides are in English, but policy inputs, questions, prompts, and CLI output remain **Korean** so both guides run the same experiment. Use the [English policy translation](docs/en/policies.md) for reading, not as a replacement input.

<details>
<summary>Workshop inspiration and the scope of published evidence</summary>

Inspired by [Satya Nadella's post on building a frontier ecosystem](https://snscratchpad.com/posts/frontier-ecosystem/), this workshop practices **business-specific evaluations and human-guided learning loops**: judge AI against your own criteria, improve it, and evaluate again—not just compare external benchmarks.

Keep [evidence scopes separate](docs/en/reference.md#live-verification): the published complete-path result does not revalidate introductory LIVE. Do not rerun to reproduce another execution's scores.

</details>

<a id="choose-path"></a>
## Choose one path

You do not need to finish every guide. **Choose the row that matches your goal and available environment.**

| Path | What you learn | Requirements |
|---|---|---|
| **[Complete RAG — recommended](docs/en/complete-lab.md)** | Real retrieval → dialogue improvement → fresh-question validation | Fixed model version, Basic Search, extra models, and permissions. **Paid** |
| **[Introductory LIVE — this page](#lab-0)** | Evaluation and prompt improvement without retrieval | Active Azure subscription, resource-creation and role-assignment permissions. **Paid** |
| **[DEMO](docs/en/offline.md)** | Evaluation workflow using authored examples | Python only. **No Azure or paid calls**; not a model-performance measurement |
| **[Optional RAG](docs/en/optional-rag.md)** | Direct Search versus Knowledge Base retrieval | Shared setup and Basic-or-higher Search. **Paid** |

If Azure or terminals are new to you, DEMO can help you learn the workflow first. **Neither RAG path requires completing the introduction.** Follow only the shared setup linked from your chosen guide.

**Already have an authorized environment?** Use [existing-environment setup](docs/en/setup.md#existing-environment) within your chosen LIVE path. Do not switch paths or create duplicate resources just because you already have them.

> [!IMPORTANT]
> The commands below are **introductory LIVE only**. Do not simply replace `live` with `demo`. If Azure prevents progress, [switch to DEMO explicitly](docs/en/setup.md#switch-to-demo), preserving the existing records.

<a id="lab-map"></a>
## Introductory LIVE progress map

**Start at [0. Spot the mistake](#lab-0); installation comes next.** Do not read every reference or edit files in advance.

Activities 0–6 share numbers across LIVE and DEMO; setup is separate. Follow each **Checkpoint → next step**. Generated reports replace any separate record form. Personal notes are optional; save human verdicts with `review`.

| Step | Your action | Evidence to keep |
|---|---|---|
| [0. Spot the mistake](#lab-0) | Explain why a plausible answer is unsafe | A policy-based judgment |
| [Setup](#prepare) | Prepare tools and Azure; try one answer | Configuration and one generated, evaluated answer |
| [1. Set criteria](#lab-1) | Define a good answer before seeing results | Fixed thresholds |
| [2. Baseline](#lab-2) | Answer eight questions using V1 | `results/baseline/report.md` |
| [3. Foundry evaluation](#lab-3) | Compare code, an AI judge, and your judgment | Reasons for the same D04 answer |
| [4. Improve and compare](#lab-4) | Change only the instructions; repeat the same questions | `results/candidate/comparison.md` |
| [5. Unseen questions and a decision](#lab-5) | Check four held-out questions | `results/candidate/gate.md` |
| [6. Apply it yourself](#lab-6) | Add one question and summarize | An extra case and four final sentences |
| [Finish](#finish) | Keep the evidence and verify retained resources | Completion and retention records |

> **Workshop completion ≠ passing AI answers.** Low scores or a final `BLOCK` are valid outcomes when you can explain the evidence and record why the change is on hold.

### Three working rules

1. **No time limit: execute one command at a time.** Copy only commands inside code blocks, press Enter, and wait for the prompt to return. Read the **Checkpoint** before continuing. A `text` block shows expected output, not a command.
2. **Run commands from the folder containing `lab.py`.** Unless stated otherwise, commands work in macOS/Linux terminals and Windows PowerShell.
3. **Keep the documented filenames and output directories.** Paths such as `results/baseline` are relative to the workshop folder. Windows may show `\` rather than `/`. Open `.md` reports in VS Code. If results already exist, [resume them](docs/en/setup.md#resume) instead of deleting them.

---

<a id="lab-0"></a>
## 0. Spot a plausible wrong answer

**Start without installing anything or signing in to Azure.** An employee asks:

> My domestic business-trip hotel costs KRW 220000 per night in September 2026. I have no prior approval. Can I claim it immediately?

| Answer A | Answer B |
|---|---|
| Yes. The limit is KRW 240000, so submit the claim. | The official KRW 200000 limit is exceeded; prior Finance approval is required. |

**Do this:** choose an answer and explain why. Then read the [English policy translation](docs/en/policies.md), or the [Korean source used by the model](data/policies.md), and check your judgment.

<details>
<summary>Read the explanation after deciding</summary>

B is appropriate. KRW 240000 appears in an **unapproved draft**. A sounds helpful but gives the wrong reimbursement advice. Fluency alone would miss this error.

</details>

**Checkpoint:** explain in one sentence which answer follows policy.

**Next:** [Setup](#prepare) · [Progress map](#lab-map)

---

<a id="prepare"></a>
## Setup. Connect your computer to Azure

> [!IMPORTANT]
> **RAG participants perform setup 1–7 only.** Then return to [complete-path Search setup](docs/en/complete-lab.md#search-setup) or [Optional RAG prerequisites](docs/en/optional-rag.md#prerequisites). The one-model/22-response scale below applies **only to the introduction**.

If you already have an authorized environment, use [existing-environment setup](docs/en/setup.md#existing-environment) instead of creating another one. Introductory participants then continue to [activity 1](#lab-1); RAG participants return to their chosen guide above.

| Setup item | Introductory LIVE value |
|---|---|
| Model / deployment name | **`gpt-6-luna` / `eval-model`** — same deployment for answers and judging |
| Region | **Sweden Central (`swedencentral`)** |
| Resources | **One project + one model deployment** |
| Identity and subscription | Microsoft Entra ID account + active Azure subscription. No API keys |
| New-environment starting role | **Active Owner** on the subscription, including an applicable inherited role |
| After the workshop | **Retain all resources** and [check costs](#retain-resources). Deletion requires a separate decision |

Owner lets one person create resources and assign roles in this path. It is not required for all Azure provisioning or existing-environment use. See the [permission contract](docs/en/reference.md#permissions-contract) for other authorized role combinations.

No search service, agent server, Docker, Git, azd, or Jupyter is needed. **Do not enter real personal data, confidential information, or passwords.**

**Cost:** charges depend on the model and token usage. Budget alerts and TPM allocations do not automatically stop spending.

<details>
<summary>Introductory LIVE response and evaluation counts</summary>

The path generates **22 responses and evaluates 44 metric items**: one setup case, eight baseline, eight candidate, four holdout, and one extra, each judged using two metrics. These are not billable API-request counts including evaluator internals and retries.

</details>

<a id="setup-map"></a>
### Setup progress map

| Step | Where | Completion signal |
|---|---|---|
| [1. Code and tools](#setup-tools) | Browser → VS Code | `LOCAL OK` |
| [2. Sign-in](#setup-sign-in) | Azure portal + terminal | Matching account, subscription, tenant |
| [3. Project](#setup-project) | Azure portal + Foundry | Provisioning `Succeeded` |
| [4. Permissions](#setup-permissions) | Azure portal IAM | Foundry User for user and project identity |
| [5. Model](#setup-model) | Foundry | `eval-model` deployed successfully |
| [6. Configuration](#setup-config) | Foundry → VS Code | `LIVE 조회 OK` for both fields |
| [7. Connectivity](#setup-smoke) | Terminal + Foundry | N01 answer and two scores with reasons |

<a id="setup-tools"></a>
### Setup 1. Get the code and install tools

**Where: browser, then VS Code**

1. On the [repository page](https://github.com/junwoojeong100/foundry-evaluation-labs-v1), choose **Code → Download ZIP** and extract it. Skip this if you already have the files. If the repository is private, request an authorized ZIP or repository access. Azure permission and GitHub permission are separate.
2. Install the tools below, then open a new terminal.
3. In VS Code, choose **File → Open Folder** and open the folder that directly contains **`lab.py` and `requirements.txt`**, not an outer ZIP extraction directory.
4. Choose **Terminal → New Terminal**. Enter subsequent commands there.

**Use VS Code's terminal on your own computer**, not **Azure Cloud Shell** in the portal or a notebook cell. Use **PowerShell on Windows**, or **zsh/bash on macOS/Linux**. If Windows opens another shell, choose the arrow beside the terminal's `+` → **Select Default Profile → PowerShell**, then open a new terminal.

Use the browser to read the guide and operate Azure, and VS Code to edit local files and run commands. Reading a GitHub file does not change your local copy. Do not use a Python file's Run button or enter shell commands at the Python `>>>` prompt. If you see `>>>`, type `exit()` first.

| Tool | Installation | Check |
|---|---|---|
| Python 3.10+ | [Python downloads](https://www.python.org/downloads/); enable PATH setup on Windows | macOS/Linux: `python3 --version`; Windows: `py -3 --version` |
| Azure CLI | [Installation instructions](https://learn.microsoft.com/cli/azure/install-azure-cli) | `az version` |
| Editor | [VS Code](https://code.visualstudio.com/) | Open the workshop folder and a terminal |

<details>
<summary>Open, preview, and save files in VS Code</summary>

1. Press **Ctrl+P / macOS Cmd+P**, enter a path such as `docs/en/policies.md`, and press Enter. If not found, use Explorer.
2. Read `.md` files with **View → Command Palette → Markdown: Open Preview to the Side**.
3. Edit the **source tab, not the preview**, then choose **File → Save**.

</details>

Run **only the block for your operating system**. `.venv` holds the workshop's Python dependencies.

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows / PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

<details>
<summary>If Windows blocks Activate.ps1</summary>

Do not relax organizational policy. Replace every subsequent `python`, including the installation command, with **`.\.venv\Scripts\python.exe`**. For example, `python lab.py doctor` becomes `.\.venv\Scripts\python.exe lab.py doctor`. Leave commands starting with `az` unchanged.

</details>

Install the packages:

```bash
python -m pip install -r requirements.txt
```

When installation finishes without errors, check the local files:

```bash
python lab.py doctor
```

**Checkpoint:** `LOCAL OK: Python ... , dev 8개, holdout 4개` means the local files contain eight dev and four holdout cases. It does **not** confirm Azure connectivity. In a new terminal, return to this folder and run only `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (PowerShell). If activation is blocked, keep using the virtual environment's Python directly. Do not recreate the environment or reinstall packages.

**Only if moving or renaming the folder broke the virtual environment**, follow [environment recovery](docs/en/reference.md#moved-folder). Keep your existing results, configuration, and edited files.

<a id="working-files"></a>
**Edit only these three local working files, when their steps ask for them.**

This table belongs to the introduction. **Complete and Optional RAG participants create only `config.json` in setup 6**; their chosen RAG guide introduces later files.

| When | Local working file | Starting material |
|---|---|---|
| Setup 6 | `config.json`, beside `lab.py` | Copy `config.example.json` |
| Activity 4 | `prompts/my-v2.txt` | Included example working copy; compare it with `prompts/v2.txt` |
| Activity 6 | `data/my-case.jsonl` | Included N02 working copy; `data/my-case.example.jsonl` is the N01 setup case |

**The repository already includes `prompts/my-v2.txt` and `data/my-case.jsonl`.** Their presence does not mean you edited or ran them. Inspect them at the relevant step; do not overwrite your previous work.

The commands automatically create output directories and reports such as `results/baseline`. Do not prefill or manually edit generated JSON and reports; read them as evidence. Keep original policies, questions, and prompts unchanged, and save working files as **UTF-8**.

<a id="setup-sign-in"></a>
### Setup 2. Sign in to the intended subscription

**Where: [Azure portal](https://portal.azure.com)**

1. Sign in with your Entra ID account and open the intended subscription under **Subscriptions**.
2. Check its **subscription ID and directory/tenant ID** in **Overview**. Use these values in the sign-in commands below.
3. Under **Access control (IAM) → View my access**, confirm an active **Owner** role. If you only have an eligible PIM role, activate it using your organization's process.
4. Under the subscription's **Resource providers**, check `Microsoft.CognitiveServices`. If needed, select **Register** and wait for `Registered`.

**Where: VS Code terminal.** Replace `YOUR-...` with the actual verified values, keeping the quotation marks.

```bash
az login --tenant "YOUR-TENANT-ID"
```

Complete browser authentication and MFA yourself, then run each command:

```bash
az account set --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az account show --query "{account:user.name,subscription:name,subscriptionId:id,tenantId:tenantId,state:state}" --output json
```

**Checkpoint:** `account` is the intended user, subscription and tenant IDs match the portal, and `state` is `Enabled`. **Do not rely on the subscription's display name alone.** With several signed-in identities, the default subscription may belong to another account. If the subscription is missing, check the tenant.

**The browser and CLI have separate sign-in sessions.** If Foundry or a report link shows **Pick an account**, select the same account confirmed above. New Foundry may request another selection. CLI authentication does not authenticate a different or headless browser.

<a id="setup-project"></a>
### Setup 3. Create a dedicated group and Foundry project

| Resource | Purpose | Example name |
|---|---|---|
| Resource group | Contains this workshop's resources | A unique name such as `rg-feval-a7k3m9` |
| Foundry resource | Parent account for deployments and access | A unique name such as `feval-a7k3m9` |
| Foundry project | Stores evaluation work and results | `eval-workshop` |
| Model deployment | Name the code calls; created in setup 5 | `eval-model` |

Replace `a7k3m9` with your own unique lowercase letters and digits. Use the names **actually created** in later steps, not just intended names.

**In Azure portal:**

1. Choose **Resource groups → Create**, using the subscription from setup 2.
2. Enter a new dedicated group name and select **Sweden Central (`swedencentral`)**.
3. Choose **Review + create → Create** and wait for completion.

**In [Microsoft Foundry](https://ai.azure.com):**

1. Sign in with the same account. Enable **New Foundry** if a switch appears.
2. Choose **Create project**, or the project selector → **Create new project**.
3. Enter **`eval-workshop`** and open **Advanced options**.
4. Select the **same subscription, new dedicated group, and Sweden Central**. Use a **new Foundry resource**, not a shared one. Enter the unique resource name if the form allows it.
5. Choose **Create** and wait for the project to open.

**Stop if the interface asks you to create a Hub first.** This workshop uses a new Foundry project under a Foundry resource, not a classic hub-based project. Their setup and SDK contracts differ.

**Checkpoint:** **Manage → Project details / Resource details** identifies the project and parent resource, and their provisioning state is `Succeeded`. Match the names and location.

**Check the location of the group, parent resource, and project separately.** Creating a group in `swedencentral` does not put every child there automatically. Availability and quota are not guaranteed. Use the [model-availability guidance](docs/en/reference.md#model-availability) if blocked; do not silently change region or disable existing network restrictions.

For commands instead of portal creation, use the [Azure CLI alternative](docs/en/setup.md#cli-provision). It **replaces setup 3–5**; do not provision both ways.

<a id="setup-permissions"></a>
### Setup 4. Verify generation and evaluation permissions

**Owner alone does not necessarily grant model and evaluation data access.** Your terminal uses **your user identity**; cloud evaluation uses the **project's managed identity**.

The parent-resource assignments below are this dedicated workshop's common starting configuration, not the only minimum scope for every evaluation or existing project. Access is inherited by child projects too. For shared or existing environments, confirm the required scope with the owner using the [permission contract](docs/en/reference.md#permissions-contract).

1. In Foundry, open the project's Azure resource from **Manage → Project details**. Its resource ID ends in **`/accounts/ACCOUNT/projects/PROJECT`**. Match the names to the resources verified in setup 3.
2. Under that project's **Identity → System assigned**, check its **Object (principal) ID** against the IAM member below. Do not copy the parent account's identity. If the menu or ID is missing, use the [managed-identity help](docs/en/reference.md#managed-identity-access).

The following is an **illustration, not an actual portal screenshot**. Names and IDs are fictional; use values from your own environment.

![Match the project's principal ID with the managed-identity member on the parent Foundry resource, and verify Foundry User for the user and project](docs/images/foundry-permissions.en.svg)

Open **Azure portal → parent Foundry resource → Access control (IAM)**. The scope ends in **`/accounts/ACCOUNT`**, with no `/projects/...` suffix.

| Role | Member | Scope |
|---|---|---|
| **Foundry User** | Your user account | Parent **Foundry resource** |
| **Foundry User** | The **project managed identity verified above** | Same **Foundry resource** |

Check **Role assignments** first. The role might appear under its previous name, **Azure AI User**. Do not duplicate an existing assignment.

For a missing user assignment, select **Add → Add role assignment → Foundry User → User, group, or service principal**, choose yourself, and **Review + assign**. For the project, use **Members → Managed identity** and verify that the selected object's ID exactly matches the project's recorded principal ID before assigning.

**Checkpoint:** both identities have Foundry User at the **parent resource scope**. Do not grant subscription-wide access or select another identity with a similar name. If propagation takes time, wait rather than creating duplicate assignments.

<a id="setup-model"></a>
### Setup 5. Deploy one model

**Where: Foundry → Discover → Models**

1. Search for **`gpt-6-luna`** and inspect its actual name and available version. Do not substitute a similarly named model.
2. Select **Deploy → Custom settings**, targeting your new project/resource.
3. Review these settings, then choose **Deploy**.

| Setting | Value |
|---|---|
| Deployment name | **`eval-model`** |
| Model / version | **`gpt-6-luna`** / a version offered in this region; record it |
| Resource location | **Sweden Central (`swedencentral`)** |
| Deployment type | **Global Standard**, if supported, permitted, and quota is available |
| Tokens per minute | Start with **30K–60K TPM** if available within the model/SKU quota |

**Complete-RAG participants require version `2026-09-22`.** Check the recorded V1 comparison's [fixed-version condition](docs/en/complete-lab.md#setup). If unavailable, choose another learning path before creating Search or additional models. Choosing another offered version above applies only to the separate introduction.

**Do not choose Provisioned/PTU or GPU deployment.** Global Standard is consumption-based, but a resource in `swedencentral` does **not** guarantee all inference stays in that region. If the model or quota is unavailable, follow [availability guidance](docs/en/reference.md#model-availability). Do not silently switch models/regions or reduce someone else's quota.

**Checkpoint:** **Build → Models** shows `eval-model` as `Succeeded`, backed by **`gpt-6-luna`**. Record the model, version, and deployment type. **The model name and deployment name are different.**

One deployment serves both generation and judging, but these are separate calls. Catalog visibility or successful deployment does not prove Chat Completions, Structured Outputs, and cloud judging all work. Verify them with [the one-case smoke check](#setup-smoke). A judge can still be wrong.

<a id="setup-config"></a>
### Setup 6. Put the project endpoint in your configuration

1. Copy **Project endpoint** from the project's **Overview** or **Manage → Project details**. Do not guess it from the name or copy an API key.
2. In VS Code, open [config.example.json](config.example.json) and **Save As `config.json`**, beside `lab.py`.
3. Replace the example `project_endpoint` and save.

**Editing JSON:** keep the field names on the left; change only the values specified on the right. Preserve straight double quotes `"`, commas, and braces, with no comma after the last field. If copying the example, copy only from `{` through `}` into the file—not explanatory text or code-block fences.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "eval-model",
  "judge_deployment": "eval-model"
}
```

**Change only the endpoint in the default path.** Check these values before saving:

| Value | Correct input | Do not use |
|---|---|---|
| `project_endpoint` | Address containing `.services.ai.azure.com/api/projects/PROJECT` | Portal browser URL, bare account endpoint, or `.openai.azure.com` address |
| Both deployment fields | **`eval-model`**, or your actual deployment name if different | Model name `gpt-6-luna` |
| Filename and location | **`config.json` beside `lab.py`** | `config.json.txt` |

No `.env` is needed.

```bash
python lab.py doctor --live
```

**Checkpoint:** both fields show **`LIVE 조회 OK`** (“LIVE lookup OK”), `eval-model`, and `gpt-6-luna`. Seeing the same deployment twice is expected. This checks lookup, not generation or evaluation.

<a id="command-status"></a>
### Read command status before continuing

Read **completion message → case count → report**. A low score is an observation; resolve `ERROR:` before continuing. These rules apply to every `run`, `judge`, and `gate`.

<details>
<summary>Next action by output: complete, waiting, errors, BLOCK, and resumption</summary>

| Output | Meaning | Action |
|---|---|---|
| `평가 완료: …개 답변 × 2개 지표 (점수·이유 저장)` | All scores/reasons are validated and saved: “evaluation complete” | Check the case count, then continue. This does **not** mean the answers passed. |
| `기존의 완료된 결과를 읽었습니다` | Completed answers for the same inputs were reused; new collection messages such as `8/8 … 저장` do not appear | Check the summary count and `report.md`, then continue at the next unfinished step. Do not delete files to regenerate answers. |
| `D04 FAIL` or a low score | A collected answer failed a criterion | Record why and continue; do not resample for a better score. |
| `Judge: 아직 미평가` | “Judge: not evaluated yet” | Run this step's `judge`. |
| Only `Foundry 상태: completed` | The remote job ended; local collection may remain | Wait for **`평가 완료`**. Resolve any later `ERROR:`. |
| `아직 처리 중입니다` / exit `3` | “Still processing” | Repeat the **entire same `judge` command**, including `--like`. |
| `중단했습니다` / exit `130` | Interrupted from the terminal | Preserve the files and use the [resume checkpoints](docs/en/setup.md#resume-checkpoints). |
| `ERROR:` / exit `1` | An input, environment, or execution error | Stop and [troubleshoot](docs/en/reference.md#troubleshooting). |
| `BLOCK` / exit `2` | The quality gate holds the change | Record `gate.md` reasons and continue to activity 6, after addressing missing evidence. |
| `usage:` / `error:` with exit `2` | Missing required arguments or invalid options | Correct and rerun the command; this is not `BLOCK`. |

The default `judge` **status-polling budget is 300 seconds**. Authentication, submission, HTTP responses, and result collection can make total command time longer. If it exits with “still processing,” repeat the same command: it retrieves the saved remote job instead of submitting another one. Do not run it concurrently in another terminal.

**After an error or interruption, fix the cause and check the [result-file resume table](docs/en/setup.md#resume-checkpoints).** Resume an incomplete `run` with the same inputs and `--out`; it skips saved answers, though an answer not saved before interruption may incur another call. If the remote job is still processing or completed and its IDs are saved, `judge` can resume polling/collection after a connection or local-save error. If submission stopped before its ID was saved, or the service reports `failed`/`canceled`, follow [remote-ID recovery](docs/en/reference.md#resume), not a blind resubmission.

The completion message appears only after score/reason validation and `judge.json`/`report.md` are saved. Read the count, the report path after `보고서:`, and the per-case evidence under `사례별 근거`. Missing scores are not merely low scores. After completion, continue; repeating a completed `run` or `judge` reads saved results rather than generating better ones.

</details>

<a id="setup-smoke"></a>
### Setup 7. Verify one generated and evaluated answer

**Paid generation/evaluation calls begin here.**

```bash
python lab.py run --mode live --prompt v1 --data data/my-case.example.jsonl --out results/setup-smoke
```

After **`1/1  N01 저장`** (“N01 saved”), evaluate the saved answer:

```bash
python lab.py judge results/setup-smoke
```

If still processing, repeat the same command. For an error or interruption, use the [status and resume guidance](#command-status). Wait for **`평가 완료: 1개 답변 × 2개 지표`**: one answer, two metrics. Then inspect it:

```bash
python lab.py inspect results/setup-smoke N01
```

**Checkpoint:** business checks contain `"schema": true`, and both `groundedness` and `relevance` have scores from **1 to 5 with reasons**. Open the **Foundry report URL** and match the same question, answer, and scores. Without a URL, use **Build → Evaluations** and the `eval_id`/`run_id` in `results/setup-smoke/foundry-job.json`.

A low score does not invalidate connectivity. Authentication failures, truncated output, and missing scores must be fixed first. N01 is a setup case, not part of dev or holdout.

**A judge can give 5 while `citations` fails.** An answer may correctly reject the draft but also include `FAQ-DRAFT` in its citations array. That fails the exact citation-set contract. With valid JSON and complete scores/reasons, the smoke check still verifies connectivity; record the disagreement as an evaluation finding.

**Setup complete. Introductory participants continue to activity 1 below.** RAG participants who borrowed setup return to **only their chosen path**:

| Chosen path | Continue here |
|---|---|
| Complete RAG | [Check setup values and prepare Search](docs/en/complete-lab.md#search-setup) |
| Optional RAG | [Optional RAG prerequisites](docs/en/optional-rag.md#prerequisites) |

**Next for introductory LIVE:** [1. Set criteria](#lab-1) · [Progress map](#lab-map)

---

<a id="lab-1"></a>
## 1. Set criteria before seeing the answers

Read the [eight dev questions](data/dev.jsonl). **Dev** is the set used during improvement. Do not open `data/holdout.jsonl` yet; those four questions are for the final check.

The expected D02 behavior is **prior approval required, limit 200000, source TRAVEL-CURRENT**. Identify what the assistant must never advise: claiming immediate reimbursement or inventing existing approval.

For English readers, the dev cases cover: D01 current policy, D02 missing prior approval, D03 an earlier travel date but later claim date, D04 an unknown overseas limit, D05 a prohibited business-class flight, D06 a request to ignore policy and invent approval, D07 an exact-limit boundary, and D08 a missing travel date.

Every question receives the same policy. **The model receives the question and policy, not the expected answers.** JSONL means one JSON object per line. `id` identifies a case, `query` is its question, `expected_*` supplies code-check expectations, and `ground_truth` is the human-readable explanation.

The answer has four fields. This is an **English explanation of the expected D02 answer, not actual model output**:

```json
{
  "decision": "needs_approval",
  "limit_krw": 200000,
  "citations": ["TRAVEL-CURRENT"],
  "answer": "KRW 220000 exceeds the KRW 200000 limit, so prior Finance approval is required."
}
```

| Answer field | Meaning |
|---|---|
| `decision` | Policy decision |
| `limit_krw` | Applicable lodging limit in KRW, or `null` |
| `citations` | Supporting document IDs |
| `answer` | Employee-facing explanation |

Decisions are `allowed`, `needs_approval`, `not_allowed`, `unknown`, or `needs_info`.

`limit_krw` is not the claimed expense. `null` means the limit cannot be determined or lodging limits do not apply—not zero. `unknown` and `needs_info` can be correct depending on the case; decision values do not execute reimbursement or grant approval.

### Use three complementary checks

| Method | What it checks | Limitation |
|---|---|---|
| **Code** | Format, decision, amount, and citations match expectations | Cannot understand the explanation's meaning |
| **Foundry LLM judge** | **Groundedness:** supported by policy? **Relevance:** responds appropriately? | The judge itself can be wrong |
| **Human review** | Policy consistency and real business risk | Cannot review every answer |

### Fixed thresholds

| Criterion | Requirement |
|---|---|
| Business checks | All four checks pass for each passing answer |
| Judge | Groundedness and Relevance **each ≥ 4/5** |
| Pass rates | Candidate dev and holdout each have business and **each judge metric ≥ 80%** |
| Critical cases | No business or judge failures on **P0**, marked `critical: true` |
| Regression | No previously passing individual check or judge metric becomes a failure |
| Completeness and review | No missing scores; at least one actual human review in candidate and holdout, with no rejected case |

For eight cases, 80% requires **at least seven**; for four, it requires **all four**. A score of 4 is not “80% accuracy.” Do not lower thresholds after seeing results.

**Checkpoint:** explain D02's expected behavior and risk. Keep these criteria fixed.

**Next:** [2. Baseline answers](#lab-2) · [Progress map](#lab-map)

---

<a id="lab-2"></a>
## 2. Generate eight baseline answers

Use the basic V1 instructions. `v1` refers to `prompts/v1.txt`; omitting `--split` selects the eight dev cases.

```bash
python lab.py run --mode live --prompt v1 --out results/baseline
```

`baseline` is the before-change result. This command generates answers and runs free code checks, but not the LLM judge.

**Checkpoint:** see **`8/8  D08 저장`**, the business pass rate, and `results/baseline/report.md`.

| Report column | Meaning |
|---|---|
| `규칙` | `PASS` means all four business checks passed |
| `실패한 검사` | Failed `schema`, `decision`, `limit`, or `citations` check |
| Groundedness / Relevance | `미평가` (“not evaluated”) is expected for now |

A FAIL is an observed result, not failure to complete the workshop. All-pass results are also valid. Do not regenerate until the scores look better.

**Next:** [3. Foundry evaluation](#lab-3) · [Progress map](#lab-map)

---

<a id="lab-3"></a>
## 3. Compare Foundry scores with your own judgment

### 3-1. Decide before seeing judge scores

Read D04's question, answer, and policy.

```bash
python lab.py inspect results/baseline D04
```

`Judge: 아직 미평가` is expected. Decide **your pass/fail and policy-based reason first**.

### 3-2. Evaluate the eight saved answers

```bash
python lab.py judge results/baseline
```

Wait for **`평가 완료: 8개 답변 × 2개 지표`**. If still processing, repeat that exact command. `judge.json` is saved and `report.md` gains scores and reasons. Groundedness sees question, policy, and answer; Relevance sees question and answer. Neither gets `ground_truth`.

### 3-3. Compare scores and reasons for the same D04

```bash
python lab.py inspect results/baseline D04
```

Open the printed **Foundry report URL**, or locate the run using `foundry-job.json`. In the Completed run, find **D04**, or search for its original question:

> 2026년 9월 도쿄 출장의 호텔비 한도가 얼마인가요?

This asks for the Tokyo hotel limit in September 2026. Match the **same question, answer, raw scores, and reasons**, not the row position. Do not create another portal evaluation or upload the original questions again.

Read both scores and explain why you agree or disagree. The portal may call 3 a Pass, but this workshop requires 4.

**Checkpoint:** explain your original judgment, the two judge scores, and agreement/disagreement reasons. Keep the original judgment rather than changing it to match the judge.

A judge may penalize an appropriate refusal to invent an unknown amount. If its reason is “no specific amount was supplied,” compare that with the expected behavior. Record the disagreement; do not invent an amount or change thresholds to satisfy the judge.

**Next:** [4. Improve and compare](#lab-4) · [Progress map](#lab-map)

---

<a id="lab-4"></a>
## 4. Change only the prompt, then compare

### 4-1. Choose a hypothesis and edit the working copy

“To reduce ___, I will change ___.” If baseline already passes, test whether the change preserves correct behavior.

1. Open [V1](prompts/v1.txt) and the [V2 example](prompts/v2.txt).
2. Open **`prompts/my-v2.txt`**. The included example adds a missing-date guard to V2: do not list date-specific limits before the travel date is known, and cite only `SCOPE` then. Include this difference in your hypothesis. **Only if the working file is missing**, open V2 and **Save As `prompts/my-v2.txt`**. Keep the originals and any previous personal edits intact.
3. Edit one or two sentences in the working file to match your hypothesis and save. Using the included working example, or copying V2 unchanged, is also allowed; record which you used. **Always use the filename `prompts/my-v2.txt`**. V2 requires official policy, the actual travel date, no invented limits/approval, and consistent JSON and explanation.

Keep **model, policy, questions/expectations, judge, and thresholds unchanged**. Once candidate generation starts, keep this working prompt unchanged through activity 6. If candidate results already exist, [resume](docs/en/setup.md#resume) rather than replacing the prompt and rerunning into the same folder.

### 4-2. Generate, evaluate, and compare the same eight dev answers

Check each command's completion before running the next.

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --out results/candidate
```

After `8/8  D08 저장`, use the baseline judge contract:

```bash
python lab.py judge results/candidate --like results/baseline
```

Wait for **`평가 완료: 8개 답변 × 2개 지표`** and `Judge 결과: results/candidate/judge.json`. If still processing, repeat the command **including `--like`**. It preserves the judge model, evaluator versions, and evaluation group.

```bash
python lab.py compare results/baseline results/candidate
```

In `results/candidate/comparison.md`, inspect the business pass rate, newly passing cases, business regressions, and judge regressions. A regression is a previously passing check becoming a failure. **A better average does not cancel an important new failure.** Match case IDs in both reports to read actual answers and reasons.

**Compare in the portal:**

1. Under **Build → Evaluations**, open the baseline's **`straightforward-…` group name**, not just its Last run link.
2. Under **Evaluation runs**, select only **`v1-dev-…` and `my-v2-dev-…`**, then **Compare runs**.
3. Set **Baseline** explicitly to **`v1-dev-…`**; the first-selected candidate might otherwise become the reference.

Do not mix holdout, setup, or extra cases into before/after comparison.

The portal summarizes averages/statistics, not the local business checks or score-4 regressions. **Too few samples / Inconclusive** means there is insufficient evidence for a statistically established improvement. If comparison is unavailable, inspect the same question in each run.

`comparison.md`, human verdicts in `reviews.json`, and `gate.md` are **local workshop records**, not additional Foundry evaluations. A portal Pass does not replace them.

### 4-3. Read D06 and save your verdict

```bash
python lab.py review results/candidate D06
```

The command waits for input. Enter lowercase `pass` or `fail`, then a **policy-based reason of at least five characters**. Read the `answer` text, not just its structured fields or judge score. A good answer refuses to invent approval and explains the applicable limit and prior-approval requirement.

The prompts are `사람의 판정 (pass/fail):` (“human verdict”) and `근거 문서와 답변을 비교한 이유:` (“reason after comparing policy and answer”). You may write your reason in English. Do not copy another review without checking your actual answer. Dangerous text warrants `fail` even with high scores.

For AI-operated walkthroughs, use [assistant-attributed reviews](docs/en/reference.md#assisted-review). AI review is not human approval and cannot satisfy the gate's human-review requirement.

**Checkpoint:** see `검토 저장: results/candidate/reviews.json`. Use `comparison.md` and both runs' `report.md` to explain the changed instruction and improved/worsened cases, or “no change.”

**Next:** [5. Unseen questions and a decision](#lab-5) · [Progress map](#lab-map)

---

<a id="lab-5"></a>
## 5. Test unseen questions and decide

### 5-1. Freeze the candidate and generate/evaluate four holdout answers

```bash
python lab.py run --mode live --frozen results/candidate --split holdout --out results/holdout
```

`--frozen` uses the prompt, policy, and model configuration stored in candidate. Do not edit `my-v2.txt` now. After **`4/4  H04 저장`**, you may open `data/holdout.jsonl`.

```bash
python lab.py judge results/holdout --like results/baseline
```

Wait for **`평가 완료: 4개 답변 × 2개 지표`** and `Judge 결과: results/holdout/judge.json`. If still processing, repeat the same command, keeping `--like`.

### 5-2. Save the human verdict for H04

```bash
python lab.py review results/holdout H04
```

Read H04, enter your verdict and reason, and confirm **`검토 저장: results/holdout/reviews.json`**. Save human verdicts through this command so the gate can use them.

### 5-3. Apply the original criteria

```bash
python lab.py gate results/baseline results/candidate results/holdout
```

The gate writes `results/candidate/gate.md`.

| Result | Action |
|---|---|
| **BLOCK** | Record its reasons and hold the change. **Continue to activity 6.** Exit code 2 is intentional quality blocking. |
| **READY_FOR_HUMAN_REVIEW** | Educational criteria met; record your adoption-review recommendation and continue. **Not production approval.** |

**Checkpoint:** use `gate.md` to explain the result, your decision, and case-based evidence. If scores or human review are missing, finish those steps and **rerun the same `gate` command** to update the decision; saving a review alone does not refresh `gate.md`. Do not turn a genuine `fail` into `pass` to remove a block. In an automated rehearsal, explicitly leave real human review incomplete.

Dev and holdout have different questions and are not a before/after pair. If you change the prompt after inspecting holdout, **use a new holdout next time**.

**Next:** [6. Your own question](#lab-6) · [Progress map](#lab-map)

---

<a id="lab-6"></a>
## 6. Evaluate one question of your own

### 6-1. Inspect the working copy and choose how to use it

Open `data/my-case.jsonl` first. The repository includes an N02 example with an expense of **180000**.

| Situation | Action |
|---|---|
| Use the provided example unchanged | Go to [6-3. Validation](#validate-extra); record “provided example unchanged” |
| Your previous LIVE/DEMO question is present | Preserve it and go to [6-3. Validation](#validate-extra); record reuse |
| `results/my-case` already exists too | Use [resume checkpoints](docs/en/setup.md#resume-checkpoints); do not replace the question |
| Practice editing | Prepare the working copy below, then change two values in 6-2 |

**Only when editing:** if the file is missing, open [the extra-case example](data/my-case.example.jsonl) and **Save As `data/my-case.jsonl`**, preserving the original. Replace the working copy with this **entire single line**, then continue to 6-2. It creates **N02**, not setup case N01. Keep the Korean question and expectation.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

Meaning: a June 15 trip costs KRW 170000 per night and is claimed in September. The travel-date limit is KRW 160000; exceeding it requires prior Finance approval.

### 6-2. Change only two amounts

| Field | Change |
|---|---|
| Hotel expense in `query` | `170000` → `180000` |
| Expense described in `ground_truth` | `170000` → `180000` |

Keep the **160000 limit**, `needs_approval`, and `TRAVEL-PREVIOUS`. The expense is not the policy limit. In your final summary, distinguish editing the example, writing your own question, using the example unchanged, or reusing your previous question.

For a new question, decide its expected behavior **before generating an answer**. Preserve all eight fields: `id`, `category`, boolean `critical`, `query`, `expected_decision`, integer-or-null `expected_limit_krw`, official-ID array `expected_citations`, and `ground_truth`. Keep ID `N02` for the commands below. Do not put another business domain into the travel-policy checker.

Use exactly one JSON object on one line, without blank lines. Editor word wrapping is fine; literal newlines inside the object are not. Numbers have no commas or quotation marks, and `null`, `true`, and `false` are lowercase.

<a id="validate-extra"></a>
### 6-3. Validate locally before paid calls

```bash
python lab.py validate-data data/my-case.jsonl
```

**Checkpoint:** `DATA OK: 1 case(s)`. Fix any reported field/line error and rerun validation. More than one case means another line such as N01 was left in the file. This checks structure, not whether your expected answer is correct.

### 6-4. Generate, evaluate, and inspect the extra case

Use the unchanged candidate prompt from activity 4.

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --data data/my-case.jsonl --out results/my-case
```

After **`1/1  N02 저장`**, evaluate:

```bash
python lab.py judge results/my-case --like results/baseline
```

Wait for **`평가 완료: 1개 답변 × 2개 지표`** and `Judge 결과: results/my-case/judge.json`. If still processing, repeat the same command, including `--like`.

```bash
python lab.py inspect results/my-case N02
```

This is an `extra` case. It does not change dev, holdout, or the gate.

**Checkpoint:** check its intended failure mode and actual result, then explain your findings in four sentences:

> In case ___, I found ___. / I found no error in these questions.<br>
> After changing ___, the same questions showed ___ and unseen questions showed ___.<br>
> Based on ___, I recommend adoption review / holding the change.<br>
> In my own work, I would first add cases testing ___.

For another domain, design a separate **question / expected behavior / forbidden behavior / evaluation method**. Do not run it through this domain-specific checker.

**Next:** [Finish checklist](#finish) · [Progress map](#lab-map)

---

<a id="finish"></a>
## Finish. Keep results and resources

### Completion checklist

Completion is about **execution and evidence-based judgment**, not obtaining high scores.

- [ ] Baseline, candidate, and holdout each have `report.md` and `judge.json`, containing scores and reasons for 8, 8, and 4 answers.
- [ ] Candidate `comparison.md` identifies improvements and regressions, or explicitly no change.
- [ ] Candidate D06 and holdout H04 have actual human verdicts/reasons in their `reviews.json` files.
- [ ] You can explain `results/candidate/gate.md` and your decision, including a valid `BLOCK`.
- [ ] `results/my-case/report.md` and `judge.json` contain the N02 answer and two scores; its creation method is recorded.
- [ ] D04's original judgment is compared with the judge scores, and you can explain the observations and final decision in the four sentences above.

**Automated rehearsals** may complete execution, assistant review, and the gate, but must not mark an unperformed human review as complete. Report that remaining condition honestly.

<a id="retain-resources"></a>
### Default: retain every created Azure resource

**Do not delete resources in this workshop.** Keep the group, Foundry resource, project, model deployment, evaluation records, and required role assignments. Do not run group/deployment deletion commands or `azd down`.

1. Keep `results/` locally and record the state of remote jobs. Closing a terminal does not cancel or finish them.
2. In the intended subscription, verify the dedicated group, parent resource, and project remain in `swedencentral`. Check `eval-model` under **Build → Models**.
3. Check **Cost Management → Cost analysis**, scoped to the group. Reporting may lag; no visible cost does not prove free use. Retention is not a billing stop, and alerts do not automatically block spending.
4. Confirm **not deleted, retention reason, next check date or condition, and cost status**. With no planned deletion date, **retain until a separate request**.

**Checkpoint:** actually created resources and records remain, and you can explain the retention conditions and cost status. Do not mark uncreated resources or unrun evaluations as completed. Skip the optional deletion path below.

<a id="delete-resources"></a>
### Optional: only after a separate deletion decision

Do not follow this section while a retention request is in effect.

<details>
<summary>Only after a separate deletion decision: scope, deletion, and confirmation</summary>

1. Keep local results and export any needed portal records. Confirm or cancel only your own pending jobs.
2. Open the exact recorded **subscription → dedicated resource group** and inspect its contents. Do not delete a shared group or an uncertain scope.
3. Only when the owner has decided it is no longer needed, choose **Overview → Delete resource group**, read the list, and enter the exact group name yourself.
4. Wait for actual deletion completion, not merely “request submitted.” This read-only query can confirm:

```bash
az group exists --name "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID"
```

Successful cleanup means **`false` for the correct group/subscription** and portal confirmation. Authentication errors or 403 are not proof of deletion. Do not remove organizational locks or policies without authorization. Deletion does not cancel costs already incurred.

Record deletion status/time and reported or still-pending costs. Use the [retention and cleanup reference](docs/en/cleanup.md) if needed.

</details>

**The checklist plus confirmed retention or deletion status completes the workshop. Deletion is not required.** One small, single-run evaluation is not a production-quality guarantee or deployment approval.

[Back to the progress map](#lab-map) · [Choose another path](#choose-path)

---

## Read only when needed

| Need | Reference |
|---|---|
| Find a setup step or use CLI provisioning | [Setup](docs/en/setup.md) |
| Resolve errors or missing scores | [Troubleshooting](docs/en/reference.md#troubleshooting) |
| Continue interrupted work | [Resume safely](docs/en/setup.md#resume) |
| Explore a higher-average regression trap | [Optional DEMO exercise](docs/en/offline.md#regression-trap) |
| Check your understanding | [Five questions](docs/en/reference.md#self-check) |
| Lead a group | [Facilitator guide](docs/en/facilitator.md) |
| Watch edited portal/CLI recordings | [Videos and subtitles](docs/media/README.md), from a separate complete-path run, not evidence that you completed this lab |

See [contracts, limitations, and official sources](docs/en/reference.md) for details, not prerequisites to reading this guide.
