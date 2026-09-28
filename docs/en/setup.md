**English** | [한국어](../setup.md)

# Setup shortcuts and safe resumption

[Main workshop](../../README.md) · [Troubleshooting](reference.md#troubleshooting)

Start a new workshop with [activity 0](../../README.md#lab-0), before installing anything. The main page contains the complete setup, execution, and retention sequence. Use this page only to find a checkpoint, use existing resources, or resume work.

The LIVE target is **`gpt-6-luna`**, **`swedencentral`**, deployment **`eval-model`**, used for generation and judging. **Retain resources** after the workshop. Do not silently substitute another model or region.

<a id="tools"></a>
## Setup 1. Tools and files

[Install tools and prepare the virtual environment](../../README.md#setup-tools). The local checkpoint is `LOCAL OK` with `dev 8개, holdout 4개`: eight dev and four holdout cases.

<a id="sign-in"></a>
## Setup 2. Account and subscription

[Sign in](../../README.md#setup-sign-in), matching the portal and CLI account, tenant, and subscription. Check the `account` field too, not just a subscription display name. Replace `YOUR-...` placeholders with the recorded values.

<a id="create-project"></a>
## Setup 3. Dedicated resources

[Create the group and project](../../README.md#setup-project). Check `swedencentral` separately on the group, Foundry resource, and project. Do not mistake shared resources for a new dedicated environment.

<a id="permissions"></a>
## Setup 4. Data-plane permissions

[Verify the two identities](../../README.md#setup-permissions): your user and the project's managed identity. Both need Foundry User on the parent Foundry resource. Use [identity-selection help](reference.md#managed-identity-access) when necessary.

<a id="deploy-model"></a>
## Setup 5. One deployment

[Deploy `gpt-6-luna` as `eval-model`](../../README.md#setup-model). Model and deployment names are different. If unavailable, use [model and quota guidance](reference.md#model-availability).

<a id="configure"></a>
## Setup 6. Configuration

[Configure the project endpoint](../../README.md#setup-config). Keep both deployment fields as `eval-model`. Both lookups should show `LIVE 조회 OK` and `gpt-6-luna`.

<a id="smoke"></a>
## Setup 7. One-case smoke check

[Generate and evaluate N01](../../README.md#setup-smoke). Valid JSON, both scores, and reasons confirm the path works. Distinguish [waiting, quality failures, and execution errors](../../README.md#command-status).

---

<a id="cli-provision"></a>
## Optional: create a new environment with Azure CLI

After completing main-guide setup 1–2, this path **replaces portal setup 3–5**. It requires Azure CLI **2.80.0+** and resource-creation/role-assignment permissions. It follows the [official project-creation instructions](https://learn.microsoft.com/azure/foundry/how-to/create-projects). No azd, search service, or agent server is added. Do not run it if your project and model already exist.

Use unique group and account names, project `eval-workshop`, and deployment `eval-model`. Replace placeholders with the subscription ID verified in setup 2 and your actual chosen values. These one-line commands work in macOS/Linux and PowerShell.

### 1. Create a new group and parent Foundry resource

```bash
az group exists --name "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID"
```

Proceed with that name **only if the result is `false`**. If `true`, choose another unique name rather than reusing or deleting the existing group.

```bash
az group create --name "YOUR-LAB-RESOURCE-GROUP" --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --tags purpose=foundry-evaluation-workshop retain=true
```

```bash
az cognitiveservices account create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --kind AIServices --sku S0 --location swedencentral --custom-domain "YOUR-FOUNDRY-ACCOUNT" --assign-identity --allow-project-management true --subscription "YOUR-SUBSCRIPTION-ID" --yes
```

**Do not omit `--assign-identity` or `--allow-project-management true`.** Project management needs the parent's identity and must be enabled at account creation. The custom domain must be globally unique. `retain=true` records intent; it is not a deletion lock or a billing stop.

### 2. Create the project and retrieve real IDs and endpoint

```bash
az cognitiveservices account project create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --project-name eval-workshop --location swedencentral --assign-identity --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az cognitiveservices account show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,state:properties.provisioningState}" --output json
```

```bash
az cognitiveservices account project show --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --project-name eval-workshop --subscription "YOUR-SUBSCRIPTION-ID" --query "{id:id,location:location,state:properties.provisioningState,principalId:identity.principalId,endpoints:properties.endpoints}" --output json
```

Both resources should be `swedencentral` / `Succeeded`. The parent's `id` is **`YOUR-FOUNDRY-RESOURCE-ID`**. The project's `principalId` is **`YOUR-PROJECT-PRINCIPAL-ID`**. Use the **AI Foundry API** entry in `endpoints` for `config.json`. Do not construct an endpoint from a guessed name.

### 3. Grant the two necessary data roles

```bash
az ad signed-in-user show --query "{account:userPrincipalName,objectId:id}" --output json
```

Verify the account again; its `objectId` is **`YOUR-USER-OBJECT-ID`**. Check existing assignments in the parent's IAM first, then assign **only missing roles**. CLI creation does not guarantee the portal's automatic assignments.

```bash
az role assignment create --assignee-object-id "YOUR-USER-OBJECT-ID" --assignee-principal-type User --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

```bash
az role assignment create --assignee-object-id "YOUR-PROJECT-PRINCIPAL-ID" --assignee-principal-type ServicePrincipal --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "YOUR-FOUNDRY-RESOURCE-ID" --subscription "YOUR-SUBSCRIPTION-ID"
```

The GUID is **Foundry User**. Both scopes end at `/accounts/ACCOUNT`, not the subscription or another project. Your account is a `User`; the managed identity is a `ServicePrincipal`.

### 4. Check model/SKU quota, then deploy once

```bash
az cognitiveservices model list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?model.name=='gpt-6-luna'].model" --output json
```

```bash
az cognitiveservices usage list --location swedencentral --subscription "YOUR-SUBSCRIPTION-ID" --query "[?name.value=='OpenAI.GlobalStandard.gpt-6-luna'].{name:name.value,current:currentValue,limit:limit}" --output json
```

Use the example below only when the model/version supports `GlobalStandard` and **`limit - current ≥ 60`**. For this model/SKU, one CLI capacity unit is 1000 TPM. Do not infer other models' units or usage names from this example. Quota availability does not guarantee physical deployment capacity.

```bash
az cognitiveservices account deployment create --name "YOUR-FOUNDRY-ACCOUNT" --resource-group "YOUR-LAB-RESOURCE-GROUP" --deployment-name eval-model --model-name gpt-6-luna --model-version "YOUR-MODEL-VERSION" --model-format OpenAI --sku-name GlobalStandard --sku-capacity 60 --subscription "YOUR-SUBSCRIPTION-ID"
```

Use an **actually listed version**. The September 27 rehearsal used `2026-09-22`; that is not a guarantee of future availability. Return to [setup 6](../../README.md#setup-config), then complete lookup and the smoke check. No API key needs to be retrieved. **Do not finish by deleting resources.**

Complete RAG requires the [specified answer version](complete-lab.md#setup) for recorded V1 comparison. Do not confuse this with the introductory path, which can use another offered version.

<a id="existing-environment"></a>
## If you already have an authorized environment

Do not create resources or rename/reconfigure an existing model. Introductory participants complete [activity 0](../../README.md#lab-0) first if needed.

You need an existing **Foundry project, not a classic hub-based project**, and an accessible compatible deployment. A project endpoint has the form `https://ACCOUNT.services.ai.azure.com/api/projects/PROJECT`. A classic hub connection string or model-only endpoint is not interchangeable.

**Complete-RAG participants return to [complete-path Search setup](complete-lab.md#search-setup) instead of step 5 below.** Verify the required deployment name/model version on existing resources first; do not silently change a shared deployment to match.

1. Obtain the actual tenant/subscription, resource names, region, project endpoint, deployment name, access permissions, and usage/cost/retention scope from the owner. Do not request API keys or shared passwords.
2. Complete [local setup](../../README.md#setup-tools) and [sign-in checks](../../README.md#setup-sign-in). Resource creation is not required, so Owner activation/provider registration is not a prerequisite for this path.
3. Verify [the two data identities](../../README.md#setup-permissions); ask an authorized owner to grant anything missing.
4. Verify Chat Completions, Structured Outputs, and judging through [configuration](../../README.md#setup-config) and the [smoke case](../../README.md#setup-smoke).
5. Continue to [activity 1](../../README.md#lab-1). Retain shared resources and operate only within the owner's agreed scope.

`eval-workshop` and `eval-model` are names for the new-resource path, not instructions to rename shared resources. If using one shared deployment for both purposes, put its actual name in both configuration fields.

<a id="switch-to-demo"></a>
## Switching from blocked LIVE work to DEMO

1. Stop new LIVE calls. Record the checkpoint, error, and already-created resources; preserve configuration, questions, and results.
2. Follow [DEMO setup](offline.md#prepare), reusing installed Python/editor/environment and preserving the LIVE records.
3. Use `results/demo-*` directories and the DEMO commands. Do not mix modes or compare authored scores with LIVE scores.
4. [Verify retention and costs](cleanup.md#retain-resources) for any Azure resources. Switching modes does not delete resources or cancel already-submitted evaluations.

<a id="cost"></a>
## Costs

See [the main path's call scale](../../README.md#prepare), [model pricing](https://azure.microsoft.com/pricing/details/azure-openai/), and your deployment type. Generation token totals exclude judge usage.

Scope **Cost Management → Cost analysis** to your dedicated group. Reporting may lag. Alerts do not stop spending, and resource retention is not a billing pause. Review [retention/cleanup](cleanup.md) even if stopping early.

<a id="resume"></a>
## Resume later

The tables below are for **introductory LIVE/DEMO with `lab.py`**. `advanced_lab.py` has different files and fixed output paths; use [complete-RAG status and resumption](complete-lab.md#resume).

1. Reopen the folder containing `lab.py` in VS Code and open a terminal.
2. Reactivate `.venv`, or keep using its Python executable if activation is prohibited. Do not reinstall packages every time.
3. Find your last completed stage and next command in the [result-file resume table](#resume-checkpoints). If LIVE authentication expired, [sign in again](../../README.md#setup-sign-in). DEMO needs no sign-in.

| Saved state | Resume action |
|---|---|
| `run` saved only some answers | Repeat the same command, inputs, and `--out`. Saved rows are not regenerated. |
| `judge` still processing | Repeat the entire command, including `--like`, to retrieve the existing job. |
| Command already completed | Continue to the next step; repeating it reads cached evidence, not a new experiment. |
| Prompt, data, or configuration changed | Design a new experiment with new output names; do not overwrite earlier evidence. |

Do not delete `run.json` or `judge.json` to force another attempt. A call interrupted between response and persistence might be charged again. See [recovery details](reference.md#resume) if remote IDs were not saved.

<a id="resume-checkpoints"></a>
### If you forgot the last checkpoint

Inspect only your own results. For DEMO, substitute `demo-baseline`, `demo-candidate`, and `demo-holdout`.

| Existing evidence / missing step | Continue |
|---|---|
| Baseline `run.json` complete; no judge | [Activity 3](../../README.md#lab-3): your D04 judgment, then judge |
| Baseline judge complete; no candidate | [Activity 4](../../README.md#lab-4): hypothesis and prompt copy |
| Candidate answers complete; no judge/comparison | [Activity 4](../../README.md#lab-4): missing judge/comparison |
| Comparison exists; no D06 review | [Activity 4 review](../../README.md#lab-4) |
| Candidate done; holdout/judge/H04/gate incomplete | First missing step in [activity 5](../../README.md#lab-5) |
| Gate and decision recorded | [Activity 6](../../README.md#lab-6) |

For DEMO, use the same numbered activities in [its guide](offline.md). Files are only clues: resume a `collecting` run or in-progress judge before proceeding. Preserve `--like`, all input evidence, and your original judgment.
