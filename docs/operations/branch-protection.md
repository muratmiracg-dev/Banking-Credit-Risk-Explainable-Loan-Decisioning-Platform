# Recommended `main` branch protection

After the initial project publication, create a GitHub ruleset for the default branch.

## Suggested settings

1. Target branch: `main`
2. Require a pull request before merging
3. Require at least one approval
4. Dismiss stale approvals when new commits are pushed
5. Require review from Code Owners
6. Require conversation resolution
7. Require status checks:
   - `quality (3.11)`
   - `quality (3.12)`
   - `package`
   - `analyze`
   - `dependencies-and-filesystem`
8. Require branches to be up to date
9. Block force pushes and deletion
10. Require signed commits and linear history if they fit the repository workflow

For a solo portfolio repository, enable “Do not allow bypassing” only after confirming that
required checks have stable names and are passing; otherwise an owner can accidentally lock
themselves out of maintenance.
