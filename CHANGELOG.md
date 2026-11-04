# Changelog

Versions follow the Hermes Agent release each one is tested against: `0.22.7` means tested with
Hermes v0.22.7. A plugin-only fix on the same Hermes release adds a suffix: `0.22.7-1`, `0.22.7-2`.
`requires_hermes` in `plugin.yaml` stays the oldest release the plugin is known to work with.

## 0.22.7

- Versioning now follows Hermes (this release is tested with Hermes v0.22.7 and still works on 0.21.5).
- Acceptance suites pass on the official `nousresearch/hermes-agent:v0.22.7` image (24/24 and 15/15).
- README: the official image's `HERMES_WRITE_SAFE_ROOT=/opt/data` must include your code dirs.

## 0.2.1 — rename

- Project renamed from `hermes-agent-sandbox` to `hermes-sandbox-cluster` to say what it is: a self-hosted, multi-node sandbox cluster. The plugin name (`agent-sandbox-backend`) and backend name (`agent_sandbox`) are unchanged; old GitHub URLs redirect.

## 0.2.0 — first public release

- `agent_sandbox` terminal backend: Hermes terminal, file and `execute_code` tools run in gVisor
  sandboxes claimed from a kubernetes-sigs/agent-sandbox warm pool.
- Wholesale environment forwarding (host-identity names skipped), declared config-file sync,
  two-way code sync including `.git` and empty directories.
- Credentialed commands (`git push/fetch/clone/ls-remote`, listed CLIs) run on the host.
- One sandbox per Hermes session, released at session close or idle reap, plus a cluster-side
  expiry renewed while active.
- Cluster scripts: per-node pod memory budget with pod swap off, gVisor install, least-privilege
  RBAC, per-tenant pool renderer with per-node package caches, daily cache GC.
