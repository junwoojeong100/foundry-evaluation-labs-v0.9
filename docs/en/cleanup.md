**English** | [한국어](../cleanup.md)

# Retain results and Azure resources

[Main finish checklist](../../README.md#finish) · [Setup](setup.md)

**The default is to retain every created resource.** Do not run deletion while a retention request is active. Closing your terminal or deleting local results does not remove Azure resources.

## 1. Keep the results locally

Keep the **entire result folder for the path you actually ran**. Reports/scores alone omit input/response snapshots, remote IDs in `foundry-job.json`, raw evaluation results, and reviews needed for resumption and comparison. Export additional portal records if needed.

| Executed path | Local evidence to retain |
|---|---|
| Introductory LIVE/DEMO | Your smoke, baseline, candidate, holdout, and extra-case results; distinguish LIVE from `demo-*` folders |
| Minimal RAG | `results/rag-setup.json`, query outputs, and experiment files such as `results/rag-search/` and `results/rag-iq/` |
| Complete RAG | Entire `results/advanced/`: retrieval, calibration, stage generation/evaluation, freeze, fresh-question registration, and acceptance. See [stage artifacts](complete-lab.md#resume) |

Poll pending jobs using the **entire original command, retaining options such as `--like`**. Complete-path calibration uses the original `calibrate` command. Cancel only your own job when separately needed and supported by its run screen, then verify its state. **Closing the terminal does not cancel remote work.**

**Checkpoint:** needed local evidence and actual remote job states are saved. If a job is still pending, record the next check rather than marking it complete. Apply your organization's data-retention policy if extending the workshop to real information.

<a id="retain-resources"></a>
## 2. Default: retain and check costs

**Stop after this section; skip optional steps 3–5.**

1. Match the recorded account, subscription, and dedicated group. Confirm the actually created Foundry resource/project remain in `swedencentral`.
2. In **Build → Models**, confirm the created deployment remains. Keep remote evaluation IDs and states. Group existence alone does not prove every child still exists.
3. Leave the group, account, project, deployment, evaluations, and required role assignments in place. **If you ran RAG, also verify the Search service, indexes, knowledge sources/bases, and the complete path's embedding/planning deployments.** Do not run group/model deletion or `azd down`.
4. Scope **Cost Management → Cost analysis** to the group. If reusing Search/models in another group, confirm that cost scope with the owner too. Costs may not yet be reported. Retention is **not a billing stop**, and alerts do not automatically stop spending.

**RAG costs:** [Basic Search incurs provisioned-capacity charges while retained](https://learn.microsoft.com/azure/search/search-sku-tier). Free semantic/knowledge-retrieval allowances do not make the Basic service free. Embedding, LLM planning, generation, and judging usage are separate; local generation token totals do not represent the whole bill. Check only resources you actually used; this is not a request to create more.

Confirm **not deleted**, why, the next check date or condition, and reported or pending costs. With no planned deletion date, **retain until a separate request**. Do not mark uncreated resources or unrun evaluations complete.

**Checkpoint:** actual resources and local evidence remain, and you can explain retention conditions and cost status. Deletion is not required to complete the workshop.

## 3. Optional: verify the deletion scope

Continue only after a separate owner decision to delete.

Open the exact recorded **subscription → resource group**. Before continuing, confirm all three:

- Its name and subscription ID match the dedicated group created during setup.
- Its account, project, deployment, and any Search service are approved for deletion as part of this workshop.
- No shared resources, other exercises, or production dependencies are included.

If any point is uncertain, do not delete. In shared environments, operate only on items explicitly approved by the owner.

A personal suffix on shared Search objects does not authorize deleting the service. Do not mark connected resources in another group as deleted merely because this group was removed.

## 4. Delete only the authorized dedicated group

1. Choose **Overview → Delete resource group**.
2. Review every affected resource. Deleting the parent affects projects and models.
3. Enter the exact recorded group name and approve the deletion yourself.
4. Wait for **completed deletion**, not merely a submitted request.

Treat group deletion as irreversible. Individual services' soft-delete capabilities do not guarantee full restoration. If a lock or policy blocks deletion, record it as incomplete and consult its owner rather than removing controls.

## 5. Confirm deletion and incurred costs

Refresh the portal and query the exact group/subscription:

```bash
az group exists --name "YOUR-LAB-RESOURCE-GROUP" --subscription "YOUR-SUBSCRIPTION-ID"
```

**Checkpoint:** the result is `false` and the portal confirms deletion. A 403, sign-in failure, or a missing item in a filtered view is not proof.

Check costs incurred before deletion. Reporting may lag; an immediate zero does not prove free use. Deleting resources does not cancel incurred charges.

Do not delete the subscription, unregister `Microsoft.CognitiveServices`, or purge a soft-deleted name to reuse it quickly. Use a new unique name if necessary.

Record the actual deletion scope, completion/time, and costs or reporting delay. If retaining instead, use the [retention record](#retain-resources).
