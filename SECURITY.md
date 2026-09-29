# Security policy

## Credential response

If a credential appears in the repository or its history:

1. Revoke or rotate it at the provider immediately.
2. Replace application access with an environment variable or GitHub Actions secret.
3. Remove the value from the current tree.
4. Decide with the repository owner whether a coordinated history rewrite is required.

The repository does not contain live provider credentials in its current tree.
Historical commits may still contain values from earlier prototypes. Removing a
value from the current tree does not revoke it and does not remove it from public
Git history.

## Local configuration

Copy `.env.example` to a local, ignored `.env` only when needed. Never commit
`.env`, API keys, model tokens, or raw user data. CI runs
`python -m tools.security_scan` on every push and pull request.

## Reporting

Do not open a public issue for an active credential. Revoke it first, then report
the affected commit and remediation plan to the repository maintainer.
