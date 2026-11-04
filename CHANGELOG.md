# Changelog

Versions follow the Hermes Agent release each one is tested against: `0.22.7` means tested with
Hermes v0.22.7. A plugin-only fix on the same Hermes release adds a suffix: `0.22.7-1`, `0.22.7-2`.
`requires_hermes` in `plugin.yaml` stays the oldest release the plugin is known to work with.

## 0.22.7-1

- README: kitchen illustration of the design (English and Chinese). No code change.

## 0.22.7 — first public release

Tested with Hermes v0.22.7 (official `nousresearch/hermes-agent:v0.22.7` image: acceptance
suites 24/24 and 15/15) and Hermes 0.21.5. Formerly published as `hermes-agent-sandbox`.

- `agent_sandbox` terminal backend: Hermes terminal, file and `execute_code` tools run in gVisor
  sandboxes claimed from a kubernetes-sigs/agent-sandbox warm pool on your own k3s nodes.
- One sandbox per Hermes session, released at session close or idle reap, plus a cluster-side
  expiry renewed while commands run.
- Environment forwarding with a skip list that takes globs (`*_TOKEN`), declared config-file sync,
  two-way code sync of the task's code dirs (deletes included; empty dirs created in the sandbox
  come back; in `.git` only history and index come back).
- Git network commands run on the host so git credentials stay there, confined to the code dirs;
  other CLIs only when you list their exact sub-commands.
- Cluster scripts: node install, gVisor, least-privilege RBAC and kubeconfig, per-tenant pool
  renderer with per-node package caches, guarded daily cache GC.
- Offline router tests (fixed table and a bash-backed fuzzer) and end-to-end acceptance suites.
- README: the official image's `HERMES_WRITE_SAFE_ROOT=/opt/data` must include your code dirs.
