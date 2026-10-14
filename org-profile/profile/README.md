# efokou-labs

Etienne Fokou. Cloud, SRE, GitOps, backend.

Repos share one platform. Default cluster is kind. AWS is for demos, then destroyed. GitOps is Argo CD.

## What I build

- kind cluster: ingress, metrics, Argo CD
- Terraform: VPC, EKS, ECR, RDS, Secrets Manager, budget alarm
- GitOps overlays for the workloads in this org
- Askel (job search), job queue + workers, SRE failure drills, AI service with eval gates

## Problems I solve

- EKS, RDS, or NAT left running after a demo
- Cluster config that does not match Git
- Incidents with no runbook
- Duplicate jobs and silent worker failures
- LLM calls with no eval gate or token cap

## Technical capabilities

Kubernetes, Argo CD, Terraform, AWS (OIDC), GitHub Actions, Python, FastAPI, Prometheus / Grafana / Loki, system design.

## Evidence

| Repo | Contents |
| --- | --- |
| [cloud-platform-blueprint](https://github.com/efokou-labs/cloud-platform-blueprint) | kind bootstrap and Terraform env roots |
| [terraform-modules](https://github.com/efokou-labs/terraform-modules) | AWS modules; `terraform test`; destroy in CI |
| [kubernetes-gitops](https://github.com/efokou-labs/kubernetes-gitops) | Argo CD desired state |
| [kubernetes-operations-toolkit](https://github.com/efokou-labs/kubernetes-operations-toolkit) | Failure modes and runbooks |
| [Askel](https://www.getaskel.com/) | Job-search product (live) |
| [distributed-job-processor](https://github.com/efokou-labs/distributed-job-processor) | API, queue, retries, DLQ, traces |
| [agentic-ai-platform](https://github.com/efokou-labs/agentic-ai-platform) | FastAPI agent, eval gates, cost controls |
| [system-design-notes](https://github.com/efokou-labs/system-design-notes) | MkDocs notes |
| [observability-lab](https://github.com/efokou-labs/observability-lab) | Metrics, logs, traces |
| [aws-cdk-examples](https://github.com/efokou-labs/aws-cdk-examples) | CDK patterns and teardown workflow |

Index: [portfolio](https://github.com/efokou-labs/portfolio).

```bash
git clone https://github.com/efokou-labs/portfolio.git
cd portfolio/repos/cloud-platform-blueprint && make kind-up
```

Needs Docker, kind, Helm, kubectl.

## Experience

This GitHub org is the sample. Clone a repo and run `make verify`.

## Contact

- GitHub: [EtienneFokou-E18560](https://github.com/EtienneFokou-E18560)
- Email: [fokou.etienne@gmail.com](mailto:fokou.etienne@gmail.com)
