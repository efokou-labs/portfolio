# efokou-labs

I build **shared platforms** that teams can run, observe, and tear down: Kubernetes, GitOps, and AWS with separately reviewable repositories—not sixteen disconnected cloud accounts.

## What I build

- A local-first kind cluster as the default runtime
- Terraform on AWS for interview-cloud demos (apply, walk through, destroy)
- Argo CD as the promotion path from Git to the cluster
- Workloads that prove full-stack SaaS, async jobs, SRE operations, and gated AI services

## Problems I solve

- **Leftover infrastructure** — no idle EKS, RDS, or NAT; sandbox AWS is ephemeral
- **Config drift** — desired state lives in Git; GitOps reconciles the cluster
- **Operations without folklore** — injected failure modes, alerts, and runbooks
- **Jobs that fail honestly** — retries, idempotency, dead-letter queues, traces
- **AI that cannot skip the gate** — evaluation thresholds and cost controls before a model call

## Technical capabilities

Kubernetes, GitOps (Argo CD), Terraform, AWS (OIDC), GitHub Actions, Python / FastAPI, observability (metrics, logs, traces), SRE runbooks, and system design.

## Evidence

| Repository | What it proves |
| --- | --- |
| [cloud-platform-blueprint](https://github.com/efokou-labs/cloud-platform-blueprint) | Platform bootstrap (kind + Terraform) |
| [terraform-modules](https://github.com/efokou-labs/terraform-modules) | Reusable AWS modules with create-and-destroy tests |
| [kubernetes-gitops](https://github.com/efokou-labs/kubernetes-gitops) | Argo CD desired state |
| [kubernetes-operations-toolkit](https://github.com/efokou-labs/kubernetes-operations-toolkit) | SRE failure modes and runbooks |
| [career-workspace](https://github.com/efokou-labs/career-workspace) | Full-stack SaaS on the shared platform |
| [distributed-job-processor](https://github.com/efokou-labs/distributed-job-processor) | Async jobs, retries, tracing |
| [agentic-ai-platform](https://github.com/efokou-labs/agentic-ai-platform) | AI service with eval gates and cost controls |
| [system-design-notes](https://github.com/efokou-labs/system-design-notes) | Architecture write-ups |
| [observability-lab](https://github.com/efokou-labs/observability-lab) | Metrics, logs, traces |
| [aws-cdk-examples](https://github.com/efokou-labs/aws-cdk-examples) | CDK patterns with teardown |

Meta repo and tracker: [portfolio](https://github.com/efokou-labs/portfolio).

Bring-up (Docker, kind, Helm, kubectl): clone the meta repo, then `cd repos/cloud-platform-blueprint && make kind-up`.

## Experience

This org is the work sample. Each repository is meant to survive a clone, a `make verify`, and a walkthrough of trade-offs: kind vs AWS, GitOps vs `kubectl apply`, destroy vs always-on.

## Contact

- GitHub: [EtienneFokou-E18560](https://github.com/EtienneFokou-E18560)
- Email: [fokou.etienne@gmail.com](mailto:fokou.etienne@gmail.com)
