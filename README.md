# GitHub Portfolio Platform

Senior-engineering portfolio for cloud, SRE, distributed systems, GitOps, and backend work. The public story is **one shared platform**, not sixteen isolated cloud accounts.

**Default cluster:** [kind](https://kind.sigs.k8s.io/). **Interview cloud:** AWS (Terraform, OIDC, ephemeral apply/destroy). **GitOps:** Argo CD.

| Always on | Ephemeral | Never |
| --- | --- | --- |
| Public GitHub, Actions, Pages, GHCR, this laptop's kind cluster | AWS sandbox for demos and module tests | Idle EKS, idle RDS, idle NAT, sixteen separate accounts |

## How to read this org

1. This meta repo — narrative and [ARCHITECTURE.md](ARCHITECTURE.md)
2. [cloud-platform-blueprint](https://github.com/EtienneFokou-E18560/cloud-platform-blueprint) — provision and bootstrap
3. [kubernetes-gitops](https://github.com/EtienneFokou-E18560/kubernetes-gitops) — desired state
4. A workload such as [career-workspace](https://github.com/EtienneFokou-E18560/career-workspace) or [distributed-job-processor](https://github.com/EtienneFokou-E18560/distributed-job-processor)

Full index and deferred repos: [TRACKER.md](TRACKER.md). Org transfer: [ORG_SETUP.md](ORG_SETUP.md).

## Local layout

```text
portfolio/                 this meta repo
  ARCHITECTURE.md
  portfolio.code-workspace
  repos/                   each directory is its own git repository
    cloud-platform-blueprint/
    ...
```

Open `portfolio.code-workspace` in Cursor so later chats attach one or two repos instead of all of them.

## Verify

```bash
make check
```

Platform bring-up (requires Docker, kind, helm, kubectl):

```bash
cd repos/cloud-platform-blueprint && make kind-up
```

## Conventions

MIT license, Conventional Commits, CODEOWNERS, no secrets in Git, AWS via OIDC only. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
