# Portfolio tracker

Status of the GitHub portfolio platform. Repositories live under `repos/` locally and on GitHub under org [efokou-labs](https://github.com/efokou-labs).

## Active (this implementation)

| Repo | Phase | Role | Local path |
| --- | --- | --- | --- |
| portfolio (meta) | 0 | Narrative, architecture, tracker | `.` |
| cloud-platform-blueprint | 1 | Flagship IaC + kind bootstrap | `repos/cloud-platform-blueprint` |
| terraform-modules | 1 | Versioned AWS modules | `repos/terraform-modules` |
| kubernetes-gitops | 1 | Argo CD desired state | `repos/kubernetes-gitops` |
| kubernetes-operations-toolkit | 1 | SRE failure modes + runbooks | `repos/kubernetes-operations-toolkit` |
| distributed-job-processor | 1 | Async jobs, retries, tracing | `repos/distributed-job-processor` |
| Askel | 1 | Job-search product + kind GitOps workload | [getaskel.com](https://www.getaskel.com/), `repos/askel` |
| agentic-ai-platform | 2 | AI service + eval gates | `repos/agentic-ai-platform` |
| system-design-notes | 2 | Architecture knowledge base | `repos/system-design-notes` |
| observability-lab | 3 | Metrics, logs, traces | `repos/observability-lab` |
| aws-cdk-examples | 3 | CDK patterns + teardown | `repos/aws-cdk-examples` |

## Deferred until P0 is demoable

Do **not** start these while kind bootstrap, GitOps, and at least one workload are unfinished. They are listed so the org story stays complete, not so they compete with P0 polish.

| Repo | Why it waits | When to start |
| --- | --- | --- |
| microservices-demo | High build depth; duplicates job-processor + GitOps patterns | After Askel and job-processor are the public workloads |
| homelab-infrastructure | Needs a real extra cluster and secret hygiene | After kubernetes-gitops is the promotion path |
| linux-automation-scripts | Low hiring signal vs platform work | After P0 READMEs are interview-ready |
| python-algorithms | Fundamentals archive, not a flagship | After P0; do not pin on the GitHub profile |
| leetcode-solutions | Interview practice archive | After P0; do not pin on the GitHub profile |
| awesome-sre | Lightweight docs; overlaps system-design-notes | After system-design-notes is published |

## Verify (meta)

```bash
make check
```
