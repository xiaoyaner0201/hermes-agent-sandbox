# Changelog

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
