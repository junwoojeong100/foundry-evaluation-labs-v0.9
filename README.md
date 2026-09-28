**English** | [한국어](README.ko.md)

# Can you trust an AI answer?

## Microsoft Foundry Evaluation: an end-to-end, self-guided workshop

**Recommended complete path:** [Failure → V2 improvement → fresh-question acceptance](docs/en/complete-lab.md). It uses one shared Basic Search service, real vector/hybrid retrieval and LLM query planning. Every final V2 holdout case passes **Groundedness, Relevance, policy task success, business, and retrieval checks**. The introductory material below remains a separate learning path.

Find out whether the fictional **Gaon Lab travel-expense assistant** follows policy. Evaluation means **checking AI answers against criteria chosen in advance**. The code is provided; you do not need to write Python.

**Follow this page from top to bottom: identify a wrong answer, prepare your environment, generate answers, evaluate them, change the instructions, compare, and record your decision.** The first activity needs no installation. Open or edit files only when a step asks you to; you do not need to read all the reference material first.

> **Completing the workshop is not the same as passing the quality gate.** Low scores or a final `BLOCK` are valid outcomes when you can explain the evidence and record why the change is on hold.

**LIVE configuration:** **`gpt-6-luna`**, **Sweden Central (`swedencentral`)**, deployment name **`eval-model`**. Use the same deployment for generation and judging. **Retain all Azure resources after the workshop.** At the end, [verify retention and costs](#retain-resources). Delete resources only after a separate decision to do so.

**Language scope:** this guide, its worksheet, and the supporting English documents are in English. The controlled policy, questions, prompts, and CLI output remain **Korean** so both language guides run the same experiment. This page translates the concepts and explains the exact Korean completion messages. Use the [English policy translation](docs/en/policies.md) for reading; do not substitute it into a partially completed experiment.

[Recorded summaries and subtitles](docs/media/README.md) show actual portal and CLI interactions. They are an overview, not a substitute for the completion checkpoints. The [recorded LIVE findings](docs/en/reference.md#live-verification) are a single-run example, not scores you should try to reproduce.

**Optional RAG extension:** [Azure AI Search + Foundry IQ and evaluation](docs/en/optional-rag.md) adds a real search index and knowledge base, evaluates retrieval separately from answers, and uses only retrieved context. It is separate from the core fixed-policy workshop below.

### Choose your path

| Your situation | Start here |
|---|---|
| You want real model calls and Foundry evaluation | **LIVE: start at [0. Spot the mistake](#lab-0)**. Setup later requires an active Azure subscription and permission to create resources and assign roles. Calls incur charges. |
| You do not have Azure access, permissions, or an available model | Follow only the [DEMO guide](docs/en/offline.md). It uses Python but does not measure a real model. |
| You already have an authorized project and deployment | Complete [activity 0](#lab-0), then follow [existing-environment setup](docs/en/setup.md#existing-environment). |

**The rest of this page is one LIVE path.** Do not simply change `live` to `demo` in its commands. If Azure prevents progress, [switch to DEMO explicitly](docs/en/setup.md#switch-to-demo), preserving the LIVE records.

**Activities 0–6 use the same numbers in LIVE, DEMO, and the worksheet.** The worksheet groups related notes under 0–1 and 2–3. Setup is separate from those activity numbers.

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

**Checkpoint:** explain in one sentence which answer follows policy. You do not need a worksheet file yet. Save your A/B choice and reason immediately after creating the worksheet during setup.

---

<a id="prepare"></a>
## Setup. Connect your computer to Azure

If you already have an authorized environment, use [existing-environment setup](docs/en/setup.md#existing-environment) instead of creating another one, then continue to [activity 1](#lab-1).

**Starting requirements for the new-environment path:** a Microsoft Entra ID account, an active Azure subscription, and an **active Owner role** on that subscription, including an applicable inherited role. This is for creating resources and assigning roles; it is not the minimum permission for using an existing environment. No API keys are used.

You need **one project and one model deployment**. You do not need a search service, agent server, Docker, Git, azd, or Jupyter. Do not enter real personal data, confidential information, or passwords.

The complete LIVE path generates **22 responses and evaluates 44 metric items**: one setup case, eight baseline cases, eight candidate cases, four holdout cases, and one extra case, each judged using two metrics. This is not the number of billable API requests including evaluator internals and retries. Charges depend on the model and token usage. Budget alerts and TPM allocations do not automatically stop spending.

<a id="setup-tools"></a>
### Setup 1. Get the code and install tools

**Where: browser, then VS Code**

1. On the [repository page](https://github.com/junwoojeong100/foundry-evaluation-v1), choose **Code → Download ZIP** and extract it. Skip this if you already have the files. If the repository is private, request an authorized ZIP or repository access. Azure permission and GitHub permission are separate.
2. Install the tools below, then open a new terminal.
3. In VS Code, choose **File → Open Folder** and open the folder that directly contains **`lab.py` and `requirements.txt`**, not an outer ZIP extraction directory.
4. Choose **Terminal → New Terminal**. Enter subsequent commands there.

Use the browser to read the guide and operate Azure, and VS Code to edit local files and run commands. Reading a GitHub file does not change your local copy. Do not use a Python file's Run button or enter shell commands at the Python `>>>` prompt. If you see `>>>`, type `exit()` first.

| Tool | Installation | Check |
|---|---|---|
| Python 3.10+ | [Python downloads](https://www.python.org/downloads/); enable PATH setup on Windows | macOS/Linux: `python3 --version`; Windows: `py -3 --version` |
| Azure CLI | [Installation instructions](https://learn.microsoft.com/cli/azure/install-azure-cli) | `az version` |
| Editor | [VS Code](https://code.visualstudio.com/) | Open the workshop folder and a terminal |

**Opening a file:** press **Ctrl+P / macOS Cmd+P**, enter a path such as `WORKSHEET.en.md`, and press Enter. If it is not found, use Explorer. For Markdown tables, run **Markdown: Open Preview to the Side** from the Command Palette. **Edit the source tab, not the preview**, and choose **File → Save**.

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

If organizational policy blocks `Activate.ps1`, do not relax the policy. Replace every subsequent `python`, including the installation command, with **`.\.venv\Scripts\python.exe`**.

Install the packages:

```bash
python -m pip install -r requirements.txt
```

When installation finishes without errors, check the local files:

```bash
python lab.py doctor
```

**Checkpoint:** `LOCAL OK: Python ... , dev 8개, holdout 4개` means the local files contain eight dev and four holdout cases. It does **not** confirm Azure connectivity. Reactivate the virtual environment when opening a new terminal; do not reinstall everything.

Create a `results` folder in VS Code Explorer if it does not already exist. Open [WORKSHEET.en.md](WORKSHEET.en.md), choose **File → Save As**, select `results`, and save as **`my-worksheet.md`**. Continue an existing worksheet instead of overwriting it. “Record in the worksheet” means editing this copy.

<a id="working-files"></a>
**Create these working copies only when their steps ask for them.**

| When | Source | Save as |
|---|---|---|
| Now | `WORKSHEET.en.md` | `results/my-worksheet.md` |
| Setup 6 | `config.example.json` | `config.json`, beside `lab.py` |
| Activity 4 | `prompts/v2.txt` | `prompts/my-v2.txt` |
| Activity 6 | `data/my-case.example.jsonl` | `data/my-case.jsonl` |

The commands automatically create output subdirectories and reports such as `results/baseline`. Do not prefill them. Apart from the worksheet, treat result JSON and reports as read-only evidence. Keep original policies, questions, and prompts unchanged, and save working copies as **UTF-8**. If an example working copy already exists in your download, inspect it and record whether you reused or edited it.

**Record now:** your A/B decision and policy reason in worksheet 0–1, plus the date and LIVE path in Setup. Leave the D02 entry for activity 1.

<a id="setup-sign-in"></a>
### Setup 2. Sign in to the intended subscription

**Where: [Azure portal](https://portal.azure.com)**

1. Sign in with your Entra ID account and open the intended subscription under **Subscriptions**.
2. Record its **subscription ID and directory/tenant ID** from **Overview**.
3. Under **Access control (IAM) → View my access**, confirm an active **Owner** role. If you only have an eligible PIM role, activate it using your organization's process.
4. Under the subscription's **Resource providers**, check `Microsoft.CognitiveServices`. If needed, select **Register** and wait for `Registered`.

**Where: VS Code terminal.** Replace `YOUR-...` with the actual recorded values, keeping the quotation marks.

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

**Checkpoint:** `account` is the intended user, subscription and tenant IDs match the portal, and `state` is `Enabled`. Record the account too. **Do not rely on the subscription's display name alone.** With several signed-in identities, the default subscription may belong to another account. If the subscription is missing, check the tenant.

**The browser and CLI have separate sign-in sessions.** If Foundry or a report link shows **Pick an account**, select the same account confirmed above. New Foundry may request another selection. CLI authentication does not authenticate a different or headless browser.

<a id="setup-project"></a>
### Setup 3. Create a dedicated group and Foundry project

| Resource | Purpose | Example name |
|---|---|---|
| Resource group | Contains this workshop's resources | A unique name such as `rg-feval-a7k3m9` |
| Foundry resource | Parent account for deployments and access | A unique name such as `feval-a7k3m9` |
| Foundry project | Stores evaluation work and results | `eval-workshop` |
| Model deployment | Name the code calls; created in setup 5 | `eval-model` |

Replace `a7k3m9` with your own unique lowercase letters and digits. Record the names **actually created**, not just intended names.

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

**Checkpoint:** **Manage → Project details / Resource details** identifies the project and parent resource, and their provisioning state is `Succeeded`. Record the names and location.

**Check the location of the group, parent resource, and project separately.** Creating a group in `swedencentral` does not put every child there automatically. Availability and quota are not guaranteed. Use the [model-availability guidance](docs/en/reference.md#model-availability) if blocked; do not silently change region or disable existing network restrictions.

For commands instead of portal creation, use the [Azure CLI alternative](docs/en/setup.md#cli-provision). It **replaces setup 3–5**; do not provision both ways.

<a id="setup-permissions"></a>
### Setup 4. Verify generation and evaluation permissions

**Owner alone does not necessarily grant model and evaluation data access.** Your terminal uses **your user identity**; cloud evaluation uses the **project's managed identity**.

1. In Foundry, open the project's Azure resource from **Manage → Project details**. Its resource ID ends in **`/accounts/ACCOUNT/projects/PROJECT`**. Match the actual names to your worksheet.
2. Under that project's **Identity → System assigned**, record its **Object (principal) ID**. Do not copy the parent account's identity. If the menu or ID is missing, use the [managed-identity help](docs/en/reference.md#managed-identity-access).

The following is an **illustration, not an actual portal screenshot**. Names and IDs are fictional; use values from your own environment.

![Match the project's principal ID with the managed-identity member on the parent Foundry resource, and verify Foundry User for the user and project](docs/images/foundry-permissions.en.svg)

Open **Azure portal → parent Foundry resource → Access control (IAM)**. The scope ends in **`/accounts/ACCOUNT`**, with no `/projects/...` suffix.

| Role | Member | Scope |
|---|---|---|
| **Foundry User** | Your user account | Parent **Foundry resource** |
| **Foundry User** | The **project managed identity recorded in your worksheet** | Same **Foundry resource** |

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

**Do not choose Provisioned/PTU or GPU deployment.** Global Standard is consumption-based, but a resource in `swedencentral` does **not** guarantee all inference stays in that region. If the model or quota is unavailable, follow [availability guidance](docs/en/reference.md#model-availability). Do not silently switch models/regions or reduce someone else's quota.

**Checkpoint:** **Build → Models** shows `eval-model` as `Succeeded`, backed by **`gpt-6-luna`**. Record the model, version, and deployment type. **The model name and deployment name are different.**

One deployment serves both generation and judging, but these are separate calls. Catalog visibility or successful deployment does not prove Chat Completions, Structured Outputs, and cloud judging all work. Verify them with [the one-case smoke check](#setup-smoke). A judge can still be wrong.

<a id="setup-config"></a>
### Setup 6. Put the project endpoint in your configuration

1. Copy **Project endpoint** from the project's **Overview** or **Manage → Project details**. Do not guess it from the name or copy an API key.
2. In VS Code, open [config.example.json](config.example.json) and **Save As `config.json`**, beside `lab.py`.
3. Replace the example `project_endpoint` and save.

```json
{
  "project_endpoint": "https://YOUR-ACCOUNT.services.ai.azure.com/api/projects/YOUR-PROJECT",
  "model_deployment": "eval-model",
  "judge_deployment": "eval-model"
}
```

In the default path, **change only the endpoint**. Keep both deployment fields as `eval-model`; do not replace them with `gpt-6-luna` merely because that is the model name. The endpoint must contain **`.services.ai.azure.com/api/projects/PROJECT`**. A portal browser URL, bare account endpoint, or `.openai.azure.com` model endpoint is not a project endpoint. If you deliberately used another deployment name, put that actual name in both fields. Check that the filename is not `config.json.txt`. No `.env` is needed.

```bash
python lab.py doctor --live
```

**Checkpoint:** both fields show **`LIVE 조회 OK`** (“LIVE lookup OK”), `eval-model`, and `gpt-6-luna`. Seeing the same deployment twice is expected. This checks lookup, not generation or evaluation.

<a id="command-status"></a>
### Read command status before continuing

| Output | Meaning | Action |
|---|---|---|
| `평가 완료: …개 답변 × 2개 지표 (점수·이유 저장)` | All scores/reasons are validated and saved: “evaluation complete” | Check the case count, then continue. This does **not** mean the answers passed. |
| `D04 FAIL` or a low score | A collected answer failed a criterion | Record why and continue; do not resample for a better score. |
| `Judge: 아직 미평가` | “Judge: not evaluated yet” | Run this step's `judge`. |
| Only `Foundry 상태: completed` | The remote job ended; local collection may remain | Wait for **`평가 완료`**. Resolve any later `ERROR:`. |
| `아직 처리 중입니다` / exit `3` | “Still processing” | Repeat the **entire same `judge` command**, including `--like`. |
| `ERROR:` / exit `1` | An input, environment, or execution error | Stop and [troubleshoot](docs/en/reference.md#troubleshooting). |
| `BLOCK` / exit `2` | The quality gate holds the change | Record `gate.md` reasons and continue to activity 6, after addressing missing evidence. |

By default, `judge` waits **up to five minutes** before returning. Repeat it **only if still processing**. It retrieves the saved remote job instead of submitting another one. Do not run it concurrently in another terminal.

The completion message appears only after score/reason validation and `judge.json`/`report.md` are saved. Read the count, the report path after `보고서:`, and the per-case evidence under `사례별 근거`. Missing scores are not merely low scores. Before stopping, record your checkpoint and **complete next command**.

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

Repeat only if still processing. Wait for **`평가 완료: 1개 답변 × 2개 지표`**: one answer, two metrics. Then inspect it:

```bash
python lab.py inspect results/setup-smoke N01
```

**Checkpoint:** business checks contain `"schema": true`, and both `groundedness` and `relevance` have scores from **1 to 5 with reasons**. Open the **Foundry report URL** and match the same question, answer, and scores. Without a URL, use **Build → Evaluations** and the `eval_id`/`run_id` in `results/setup-smoke/foundry-job.json`.

A low score does not invalidate connectivity. Authentication failures, truncated output, and missing scores must be fixed first. N01 is a setup case, not part of dev or holdout.

**A judge can give 5 while `citations` fails.** An answer may correctly reject the draft but also include `FAQ-DRAFT` in its citations array. That fails the exact citation-set contract. With valid JSON and complete scores/reasons, the smoke check still verifies connectivity; record the disagreement as an evaluation finding.

**Setup complete. Continue to activity 1.**

---

<a id="lab-1"></a>
## 1. Set criteria before seeing the answers

Read the [eight dev questions](data/dev.jsonl). **Dev** is the set used during improvement. Do not open `data/holdout.jsonl` yet; those four questions are for the final check.

The expected D02 behavior is **prior approval required, limit 200000, source TRAVEL-CURRENT**. Record what the assistant must never advise: claiming immediate reimbursement or inventing existing approval.

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

`decision` is one of `allowed`, `needs_approval`, `not_allowed`, `unknown`, or `needs_info`. `limit_krw` is an integer limit in KRW or `null`; `citations` contains supporting document IDs; `answer` is the employee-facing explanation.

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

**Checkpoint:** worksheet 0–1 records D02 expectations and risk. Keep these criteria fixed.

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

---

<a id="lab-3"></a>
## 3. Compare Foundry scores with your own judgment

**First, review D04 before judging:**

```bash
python lab.py inspect results/baseline D04
```

`Judge: 아직 미평가` is expected. Record **your pass/fail and policy-based reason first** in worksheet 2–3.

**Then evaluate the eight saved answers:**

```bash
python lab.py judge results/baseline
```

Wait for **`평가 완료: 8개 답변 × 2개 지표`**. If still processing, repeat that exact command. `judge.json` is saved and `report.md` gains scores and reasons. Groundedness sees question, policy, and answer; Relevance sees question and answer. Neither gets `ground_truth`.

**Inspect the same D04 again:**

```bash
python lab.py inspect results/baseline D04
```

Open the printed **Foundry report URL**, or locate the run using `foundry-job.json`. In the Completed run, find **D04**, or search for its original question:

> 2026년 9월 도쿄 출장의 호텔비 한도가 얼마인가요?

This asks for the Tokyo hotel limit in September 2026. Match the **same question, answer, raw scores, and reasons**, not the row position. Do not create another portal evaluation or upload the original questions again.

Record both scores and why you agree or disagree. The portal may call 3 a Pass, but this workshop requires 4.

**Checkpoint:** worksheet 2–3 contains your original judgment, two judge scores, and agreement/disagreement reasons. Keep the original judgment rather than rewriting it to match the judge.

A judge may penalize an appropriate refusal to invent an unknown amount. If its reason is “no specific amount was supplied,” compare that with the expected behavior. Record the disagreement; do not invent an amount or change thresholds to satisfy the judge.

---

<a id="lab-4"></a>
## 4. Change only the prompt, then compare

**Write a hypothesis first:** “To reduce ___, I will change ___.” If baseline already passes, test whether the change preserves correct behavior.

1. Open [V1](prompts/v1.txt) and the [V2 example](prompts/v2.txt).
2. With V2 open, choose **Save As `prompts/my-v2.txt`**. Do not change the originals.
3. Edit one or two sentences to match your hypothesis. Reusing V2 unchanged is allowed, but **still use the filename `prompts/my-v2.txt`** and record that choice. The Korean V2 requires official policy, the actual travel date, no invented limits/approval, and consistent JSON and explanation.

Keep **model, policy, questions/expectations, judge, and thresholds unchanged**.

**Generate the same eight dev answers:**

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

In **Build → Evaluations**, open the baseline's **`straightforward-…` group name**, not just its Last run link. Under **Evaluation runs**, select only **`v1-dev-…` and `my-v2-dev-…`**, then **Compare runs**. Set **Baseline** explicitly to `v1-dev-…`; the first-selected candidate might otherwise become the reference. Do not mix holdout or extra cases into before/after comparison.

The portal summarizes averages/statistics, not the local business checks or score-4 regressions. **Too few samples / Inconclusive** means there is insufficient evidence for a statistically established improvement. If comparison is unavailable, inspect the same question in each run.

**Review the actual D06 answer:**

```bash
python lab.py review results/candidate D06
```

The command waits for input. Enter lowercase `pass` or `fail`, then a **policy-based reason of at least five characters**. Read the `answer` text, not just its structured fields or judge score. A good answer refuses to invent approval and explains the applicable limit and prior-approval requirement.

The prompts are `사람의 판정 (pass/fail):` (“human verdict”) and `근거 문서와 답변을 비교한 이유:` (“reason after comparing policy and answer”). You may write your reason in English. Do not copy another review without checking your actual answer. Dangerous text warrants `fail` even with high scores.

For AI-operated walkthroughs, use [assistant-attributed reviews](docs/en/reference.md#assisted-review). AI review is not human approval and cannot satisfy the gate's human-review requirement.

**Checkpoint:** see `검토 저장: results/candidate/reviews.json`. Record the changed instruction and improved/worsened cases, or “no change,” in worksheet 4.

---

<a id="lab-5"></a>
## 5. Test unseen questions and decide

**Freeze the candidate and generate four holdout answers:**

```bash
python lab.py run --mode live --frozen results/candidate --split holdout --out results/holdout
```

`--frozen` uses the prompt, policy, and model configuration stored in candidate. Do not edit `my-v2.txt` now. After **`4/4  H04 저장`**, you may open `data/holdout.jsonl`.

```bash
python lab.py judge results/holdout --like results/baseline
```

Wait for **`평가 완료: 4개 답변 × 2개 지표`** and `Judge 결과: results/holdout/judge.json`. Repeat only if still processing, keeping `--like`.

```bash
python lab.py review results/holdout H04
```

Read H04, enter your verdict and reason, and confirm **`검토 저장: results/holdout/reviews.json`**. A note in the worksheet alone is not a saved review.

**Apply the original criteria:**

```bash
python lab.py gate results/baseline results/candidate results/holdout
```

The gate writes `results/candidate/gate.md`.

| Result | Action |
|---|---|
| **BLOCK** | Record its reasons and hold the change. **Continue to activity 6.** Exit code 2 is intentional quality blocking. |
| **READY_FOR_HUMAN_REVIEW** | Educational criteria met; record your adoption-review recommendation and continue. **Not production approval.** |

**Checkpoint:** both `gate.md` and worksheet 5 contain the result, decision, and case-based evidence. Address missing scores or omitted human review; do not turn a genuine `fail` into `pass` to remove a block. In an automated rehearsal, explicitly leave real human review incomplete.

Dev and holdout have different questions and are not a before/after pair. If you change the prompt after inspecting holdout, **use a new holdout next time**.

---

<a id="lab-6"></a>
## 6. Evaluate one question of your own

Open [the extra-case example](data/my-case.example.jsonl) and **Save As `data/my-case.jsonl`**. Keep the original unchanged.

Replace the copy with this **entire single line**. It creates **N02**, not setup case N01. Keep the Korean question and expectation for the shared experiment.

```jsonl
{"id":"N02","category":"과거 출장의 한도 초과","critical":true,"query":"2026년 6월 15일 국내 출장 숙박비가 1박 170000원입니다. 9월에 정산하면 사전 승인 없이 처리해도 되나요?","expected_decision":"needs_approval","expected_limit_krw":160000,"expected_citations":["TRAVEL-PREVIOUS"],"ground_truth":"정산일이 아니라 출장일의 과거 한도 160000원을 적용한다. 170000원은 한도 초과이므로 재무팀 사전 승인이 필요하며 바로 정산할 수 있다고 안내하면 안 된다."}
```

Meaning: a June 15 trip costs KRW 170000 per night and is claimed in September. The travel-date limit is KRW 160000; exceeding it requires prior Finance approval.

**Change just two amounts first:**

| Field | Change |
|---|---|
| Hotel expense in `query` | `170000` → `180000` |
| Expense described in `ground_truth` | `170000` → `180000` |

Keep the **160000 limit**, `needs_approval`, and `TRAVEL-PREVIOUS`. The expense is not the policy limit. Record whether you edited the example, wrote your own question, or used the example unchanged.

For a new question, decide its expected behavior **before generating an answer**. Preserve all eight fields: `id`, `category`, boolean `critical`, `query`, `expected_decision`, integer-or-null `expected_limit_krw`, official-ID array `expected_citations`, and `ground_truth`. Keep ID `N02` for the commands below. Do not put another business domain into the travel-policy checker.

Use exactly one JSON object on one line, without blank lines. Editor word wrapping is fine; literal newlines inside the object are not. Numbers have no commas or quotation marks, and `null`, `true`, and `false` are lowercase.

**Validate locally before paid calls:**

```bash
python lab.py validate-data data/my-case.jsonl
```

**Checkpoint:** `DATA OK: 1 case(s)`. Fix any reported field/line error and rerun validation. More than one case means another line such as N01 was left in the file. This checks structure, not whether your expected answer is correct.

**Generate using the unchanged candidate prompt:**

```bash
python lab.py run --mode live --prompt prompts/my-v2.txt --data data/my-case.jsonl --out results/my-case
```

After **`1/1  N02 저장`**, evaluate:

```bash
python lab.py judge results/my-case --like results/baseline
```

Wait for **`평가 완료: 1개 답변 × 2개 지표`** and `Judge 결과: results/my-case/judge.json`. Repeat the same command only if still processing.

```bash
python lab.py inspect results/my-case N02
```

This is an `extra` case. It does not change dev, holdout, or the gate.

**Checkpoint:** record its intended failure mode and actual result, then complete your four-sentence report:

> In case ___, I found ___. / I found no error in these questions.<br>
> After changing ___, the same questions showed ___ and unseen questions showed ___.<br>
> Based on ___, I recommend adoption review / holding the change.<br>
> In my own work, I would first add cases testing ___.

For another domain, design a separate **question / expected behavior / forbidden behavior / evaluation method**. Do not run it through this domain-specific checker.

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
- [ ] `results/my-worksheet.md` contains D04's original judgment, observations, and four final sentences.

**Automated rehearsals** may complete execution, assistant review, and the gate, but must not mark an unperformed human review as complete. Report that remaining condition honestly.

<a id="retain-resources"></a>
### Default: retain every created Azure resource

**Do not delete resources in this workshop.** Keep the group, Foundry resource, project, model deployment, evaluation records, and required role assignments. Do not run group/deployment deletion commands or `azd down`.

1. Keep `results/` locally and record the state of remote jobs. Closing a terminal does not cancel or finish them.
2. In the intended subscription, verify the dedicated group, parent resource, and project remain in `swedencentral`. Check `eval-model` under **Build → Models**.
3. Check **Cost Management → Cost analysis**, scoped to the group. Reporting may lag; no visible cost does not prove free use. Retention is not a billing stop, and alerts do not automatically block spending.
4. Record **not deleted, retention reason, next check date or condition, and cost status**. If no deletion date is planned, write **“retain until a separate request.”**

**Checkpoint:** actually created resources and records remain, and the retention/cost decision is recorded. Do not mark uncreated resources or unrun evaluations as completed. Skip the optional deletion path below.

<a id="delete-resources"></a>
### Optional: only after a separate deletion decision

Do not follow this section while a retention request is in effect.

1. Keep local results and export any needed portal records. Confirm or cancel only your own pending jobs.
2. Open the exact recorded **subscription → dedicated resource group** and inspect its contents. Do not delete a shared group or an uncertain scope.
3. Only when the owner has decided it is no longer needed, choose **Overview → Delete resource group**, read the list, and enter the exact group name yourself.
4. Wait for actual deletion completion, not merely “request submitted.” This read-only query can confirm:

```bash
az group exists --name "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID"
```

Successful cleanup means **`false` for the correct group/subscription** and portal confirmation. Authentication errors or 403 are not proof of deletion. Do not remove organizational locks or policies without authorization. Deletion does not cancel costs already incurred.

Record deletion status/time and reported or still-pending costs. Use the [retention and cleanup reference](docs/en/cleanup.md) if needed.

**The checklist plus retention or deletion records complete the workshop. Deletion is not required.** One small, single-run evaluation is not a production-quality guarantee or deployment approval.

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
| Watch edited portal/CLI recordings | [Videos and subtitles](docs/media/README.md) |

See [contracts, limitations, and official sources](docs/en/reference.md) for details, not prerequisites to reading this guide.
