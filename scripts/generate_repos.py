#!/usr/bin/env python3
"""Generate remaining portfolio repositories. Run from workspace root."""
from __future__ import annotations

from pathlib import Path

ROOT = Path("/Users/efokou/Documents/MyDevelopment/portfolio")
REPOS = ROOT / "repos"
LICENSE = (ROOT / "LICENSE").read_text()
SECURITY = (ROOT / "SECURITY.md").read_text()
CODEOWNERS = "* @EtienneFokou-E18560\n"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content if content.endswith("\n") else content + "\n")


def common(repo: Path) -> None:
    write(repo / "LICENSE", LICENSE)
    write(repo / "SECURITY.md", SECURITY)
    write(repo / "CODEOWNERS", CODEOWNERS)


def gitignore_python() -> str:
    return """__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
.env
.env.*
!.env.example
.DS_Store
dist/
*.egg-info/
"""


def gitignore_node() -> str:
    return """node_modules/
.next/
dist/
coverage/
.env
.env.*
!.env.example
.DS_Store
cdk.out/
*.js.map
"""


# ---------------------------------------------------------------------------
# terraform-modules
# ---------------------------------------------------------------------------
def terraform_modules() -> None:
    repo = REPOS / "terraform-modules"
    common(repo)
    write(
        repo / ".gitignore",
        ".terraform/\n*.tfstate\n*.tfstate.*\n.terraform.lock.hcl\n.DS_Store\n",
    )
    write(
        repo / "README.md",
        """# terraform-modules

Versioned AWS modules consumed by [cloud-platform-blueprint](https://github.com/EtienneFokou-E18560/cloud-platform-blueprint).

Infrastructure **create and destroy** is the integration test. There is no permanent demo VPC.

## Modules

- `modules/vpc` — public/private subnets; NAT off by default
- `modules/eks` — EKS cluster IAM + control plane
- `modules/ecr` — immutable tags, scan on push
- `modules/rds` — PostgreSQL, deletion protection off for sandbox teardown
- `modules/secrets` — Secrets Manager placeholder version
- `modules/budget` — $10 monthly cost budget

Pin from consumers:

```hcl
module "vpc" {
  source = "git::https://github.com/EtienneFokou-E18560/terraform-modules.git//modules/vpc?ref=v0.1.0"
  name   = "portfolio-dev"
}
```

## Verify

```bash
make verify
```

Native `terraform test` uses a mocked AWS provider (no account required). The `integration` workflow applies in a sandbox and **destroys in `if: always()`**.

## Versioning

Git tags: `v0.1.0`, `v1.0.0`. Breaking changes bump the major version.
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
TERRAFORM_IMAGE ?= hashicorp/terraform:1.9.8
TF := docker run --rm -v "$(CURDIR):/src" -w /src $(TERRAFORM_IMAGE)

verify:
	$(TF) -chdir=modules/vpc fmt -check
	$(TF) -chdir=modules/vpc init -backend=false -input=false
	$(TF) -chdir=modules/vpc validate
	$(TF) test
	@echo terraform-modules verify passed
""",
    )
    src_root = REPOS / "cloud-platform-blueprint" / "modules"
    mapping = {
        "network": "vpc",
        "kubernetes": "eks",
        "registry": "ecr",
        "database": "rds",
        "secrets": "secrets",
        "observability": "budget",
    }
    for src, dest in mapping.items():
        text = (src_root / src / "main.tf").read_text()
        write(repo / "modules" / dest / "main.tf", text)

    write(
        repo / "tests" / "vpc.tftest.hcl",
        """\
mock_provider "aws" {}

run "plan_vpc" {
  command = plan

  module {
    source = "./modules/vpc"
  }

  variables {
    name               = "test-vpc"
    enable_nat_gateway = false
  }
}
""",
    )
    write(
        repo / "tests" / "ecr.tftest.hcl",
        """\
mock_provider "aws" {}

run "plan_ecr" {
  command = plan

  module {
    source = "./modules/ecr"
  }

  variables {
    name = "test-ecr"
  }
}
""",
    )
    write(
        repo / ".github/workflows/terraform.yml",
        """\
name: terraform-modules

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.8
      - name: validate modules
        run: |
          for d in modules/*; do
            terraform -chdir="$d" init -backend=false -input=false
            terraform -chdir="$d" fmt -check
            terraform -chdir="$d" validate
          done
      - name: terraform test
        run: terraform test

  integration:
    if: github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    environment: aws-sandbox
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.8
      - name: apply
        working-directory: examples/ephemeral
        run: terraform init && terraform apply -auto-approve
      - name: destroy
        if: always()
        working-directory: examples/ephemeral
        run: terraform destroy -auto-approve
""",
    )
    write(
        repo / "examples/ephemeral/main.tf",
        """\
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

module "budget" {
  source    = "../../modules/budget"
  name      = "tf-modules-ephemeral"
  limit_usd = "10"
}

module "ecr" {
  source = "../../modules/ecr"
  name   = "tf-modules-ephemeral"
}
""",
    )
    write(repo / "VERSION", "0.1.0\n")


# ---------------------------------------------------------------------------
# kubernetes-gitops
# ---------------------------------------------------------------------------
def kubernetes_gitops() -> None:
    repo = REPOS / "kubernetes-gitops"
    common(repo)
    write(repo / ".gitignore", ".DS_Store\n*.orig\n")
    write(
        repo / "README.md",
        """# kubernetes-gitops

Desired state for the shared kind (and later EKS) cluster. CI builds images in application repos; **this** repo changes tags and overlays. Humans do not `kubectl apply` in production.

## Promotion

| Overlay | How it moves |
| --- | --- |
| `dev` | Merge to `main` can update image tags automatically |
| `staging` | PR from `dev` values; smoke tests |
| `prod` | Protected environment, manual approval |

Argo CD reconciles, detects drift, and rolls back by reverting Git.

Optional later: Argo Rollouts canary 5% → 20% → 50% → 100% gated on error rate and latency (see `docs/rollouts.md`).

## Verify

```bash
make verify
```

## Bootstrap

After `make kind-up` in cloud-platform-blueprint:

```bash
kubectl apply -f bootstrap/root-application.yaml
```
""",
    )
    write(
        repo / "Makefile",
        """\
.PHONY: verify
verify:
	@command -v kubectl >/dev/null || { echo "kubectl missing (kustomize build still checked via docker)"; }
	docker run --rm -v "$(CURDIR):/src" -w /src registry.k8s.io/kustomize/kustomize:v5.4.3 build apps/root >/tmp/root.yaml
	docker run --rm -v "$(CURDIR):/src" -w /src registry.k8s.io/kustomize/kustomize:v5.4.3 build apps/career-workspace/overlays/dev >/dev/null
	docker run --rm -v "$(CURDIR):/src" -w /src registry.k8s.io/kustomize/kustomize:v5.4.3 build apps/distributed-job-processor/overlays/dev >/dev/null
	docker run --rm -v "$(CURDIR):/src" -w /src registry.k8s.io/kustomize/kustomize:v5.4.3 build apps/agentic-ai-platform/overlays/dev >/dev/null
	@echo kubernetes-gitops verify passed
""",
    )
    write(
        repo / "bootstrap/root-application.yaml",
        """\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: portfolio-root
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/EtienneFokou-E18560/kubernetes-gitops.git
    targetRevision: main
    path: apps/root
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
""",
    )
    write(
        repo / "apps/root/kustomization.yaml",
        """\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../career-workspace/overlays/dev
  - ../distributed-job-processor/overlays/dev
  - ../agentic-ai-platform/overlays/dev
  - ../observability-lab/overlays/dev
""",
    )
    write(repo / "docs/rollouts.md", """# Progressive delivery

When Argo Rollouts is installed on the cluster, canary weights are 5, 20, 50, then 100.

Promotion gates (to be wired to Prometheus):

- error rate below the overlay SLO
- p99 latency below the overlay SLO

Until Rollouts is enabled, Deployment rolling updates are the default.
""")
    write(
        repo / ".github/workflows/gitops.yml",
        """\
name: gitops

on:
  pull_request:
  push:
    branches: [main]

jobs:
  kustomize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: yokawasa/action-setup-kube-tools@v0.11.1
        with:
          setup-tools: |
            kustomize
            kubeconform
      - name: build overlays
        run: |
          set -euo pipefail
          for p in apps/career-workspace/overlays/* apps/distributed-job-processor/overlays/* apps/agentic-ai-platform/overlays/* apps/observability-lab/overlays/*; do
            echo "BUILD $p"
            kustomize build "$p" | kubeconform -strict -ignore-missing-schemas
          done
""",
    )

    apps = {
        "career-workspace": ("career-workspace", "8080", "ghcr.io/etiennefokou-e18560/career-workspace:dev"),
        "distributed-job-processor": ("job-processor", "8080", "ghcr.io/etiennefokou-e18560/distributed-job-processor:dev"),
        "agentic-ai-platform": ("agentic-ai", "8080", "ghcr.io/etiennefokou-e18560/agentic-ai-platform:dev"),
        "observability-lab": ("obs-lab", "8080", "ghcr.io/etiennefokou-e18560/observability-lab:dev"),
    }
    for app, (name, port, image) in apps.items():
        write(
            repo / f"apps/{app}/base/deployment.yaml",
            f"""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {name}
  template:
    metadata:
      labels:
        app: {name}
    spec:
      containers:
        - name: app
          image: {image}
          ports:
            - containerPort: {port}
          livenessProbe:
            httpGet:
              path: /healthz
              port: {port}
          readinessProbe:
            httpGet:
              path: /readyz
              port: {port}
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 500m
              memory: 256Mi
""",
        )
        write(
            repo / f"apps/{app}/base/service.yaml",
            f"""\
apiVersion: v1
kind: Service
metadata:
  name: {name}
spec:
  selector:
    app: {name}
  ports:
    - port: 80
      targetPort: {port}
""",
        )
        write(
            repo / f"apps/{app}/base/kustomization.yaml",
            f"""\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
""",
        )
        for overlay, replicas in [("dev", 1), ("staging", 2), ("prod", 2)]:
            write(
                repo / f"apps/{app}/overlays/{overlay}/kustomization.yaml",
                f"""\
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: {app}
resources:
  - ../../base
  - namespace.yaml
replicas:
  - name: {name}
    count: {replicas}
images:
  - name: {image.rsplit(':', 1)[0]}
    newTag: {overlay if overlay != 'prod' else 'prod'}
""",
            )
            write(
                repo / f"apps/{app}/overlays/{overlay}/namespace.yaml",
                f"""\
apiVersion: v1
kind: Namespace
metadata:
  name: {app}
  labels:
    env: {overlay}
""",
            )


print("partial - continuing in same file")


if __name__ == "__main__":
    terraform_modules()
    kubernetes_gitops()
    print("generated terraform-modules and kubernetes-gitops")
