# GitHub org setup

The org **[efokou-labs](https://github.com/efokou-labs)** exists. Portfolio repositories have been transferred from the personal account.

## Org profile repository

```bash
gh repo create efokou-labs/.github --public --description "Org profile, security policy, and support links"
```

Copy `org-profile/profile/README.md` to `.github/profile/README.md` in that repo (GitHub renders it on the org overview).

## Branch protection template

On each `main` branch:

- Require a pull request
- Require the CI status check named in that repo's workflow
- Do not allow force pushes
- Do not allow deletions

Reusable workflows live in `cloud-platform-blueprint` so app repos can call `uses: efokou-labs/cloud-platform-blueprint/.github/workflows/python-ci.yml@main`.
