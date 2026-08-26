# efokou-labs

Production-style engineering platform for interviews: **one cluster story**, separately reviewable repositories.

**Default runtime:** kind. **Cloud:** AWS (Terraform, OIDC, destroy after demos). **Delivery:** GitHub Actions → GHCR → Argo CD.

## How to run locally

```bash
git clone https://github.com/EtienneFokou-E18560/portfolio.git
cd portfolio
make check
cd repos/cloud-platform-blueprint && make kind-up
```

## Cost policy

- Always-on: public GitHub, Actions, Pages, GHCR, kind on a laptop.
- Ephemeral: AWS sandbox. Put a **$10 budget alarm** in the account before the first apply.
- Never: idle EKS, idle RDS, idle NAT gateways, or sixteen separate cloud environments.

## Repository map

| Repository | Signal |
| --- | --- |
| [cloud-platform-blueprint](https://github.com/EtienneFokou-E18560/cloud-platform-blueprint) | Cloud platform / IaC |
| [terraform-modules](https://github.com/EtienneFokou-E18560/terraform-modules) | Reusable IaC |
| [kubernetes-gitops](https://github.com/EtienneFokou-E18560/kubernetes-gitops) | Continuous delivery |
| [kubernetes-operations-toolkit](https://github.com/EtienneFokou-E18560/kubernetes-operations-toolkit) | SRE / operations |
| [career-workspace](https://github.com/EtienneFokou-E18560/career-workspace) | Full-stack SaaS |
| [distributed-job-processor](https://github.com/EtienneFokou-E18560/distributed-job-processor) | Distributed systems |
| [agentic-ai-platform](https://github.com/EtienneFokou-E18560/agentic-ai-platform) | AI service / evaluation |
| [system-design-notes](https://github.com/EtienneFokou-E18560/system-design-notes) | Architecture knowledge |
| [observability-lab](https://github.com/EtienneFokou-E18560/observability-lab) | Metrics, logs, traces |
| [aws-cdk-examples](https://github.com/EtienneFokou-E18560/aws-cdk-examples) | AWS infrastructure patterns |

Deferred on purpose (do not pin): microservices-demo, homelab-infrastructure, linux-automation-scripts, python-algorithms, leetcode-solutions, awesome-sre. See the [portfolio tracker](https://github.com/EtienneFokou-E18560/portfolio/blob/main/TRACKER.md).
