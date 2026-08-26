# Contributing

This workspace is a **meta repository**. Application and platform code lives in sibling git repositories under `repos/`. Do not dump those trees into this git history.

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` user-visible capability
- `fix:` bug fix
- `docs:` documentation only
- `ci:` GitHub Actions / Make targets
- `chore:` tooling, license, ignore files

## Pull requests

- Open a PR against `main`. Direct pushes to `main` should be blocked once GitHub branch protection is enabled.
- Every PR must include a verify command in the description (the same command documented in that repo's README).
- Do not include secrets, `.env` files, or `*.tfstate`.

## Repo boundaries

Implement **one repository per change set**. Link to the shared platform instead of copying Terraform, Helm bootstrap, or observability stacks.

## Local defaults

- Cluster: kind (`make kind-up` in `cloud-platform-blueprint`)
- GitOps: Argo CD
- Cloud: AWS, documented and teardown-safe — `terraform plan` unless the maintainer asked to apply
