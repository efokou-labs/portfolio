# GitHub org setup

GitHub.com does not expose a public API to **create** a new organization. The logged-in token also has `read:org` only (not `admin:org`), so this workspace is published to the personal account first and is ready to transfer.

## Create the org (one-time, in the browser)

1. Open [Create a new organization](https://github.com/account/organizations/new).
2. Choose the **Free** plan.
3. Name the org **`efokou-labs`** (or another short professional name).
4. Skip inviting extra owners until the repos exist.

## Create the org profile repository

After the org exists:

```bash
# from this meta repo, after you have org admin rights
gh repo create efokou-labs/.github --public --description "Org profile, security policy, and support links"
```

Copy `org-profile/profile/README.md` to `.github/profile/README.md` in that repo (GitHub renders it on the org overview).

## Transfer repositories

```bash
gh api -X POST repos/EtienneFokou-E18560/cloud-platform-blueprint/transfer \
  -f new_owner=efokou-labs
```

Repeat for every repo listed in [TRACKER.md](TRACKER.md). Update README URLs after transfer.

## Branch protection template

On each `main` branch:

- Require a pull request
- Require the CI status check named in that repo's workflow
- Do not allow force pushes
- Do not allow deletions

Reusable workflows will live in `cloud-platform-blueprint` (see `uses:` examples there) so app repos do not copy YAML forever.
