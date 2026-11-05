# Changelog

Versions have four parts: the first three are the Hermes release the plugin was tested with, the
fourth is the plugin's own revision on that release (`0.22.7.3` = third plugin revision tested with
Hermes v0.22.7). This is a project-specific scheme, not SemVer. It replaces the earlier `-N`
suffix (`0.22.7-2`), which reads as a pre-release under SemVer. Hermes compares plugin versions
with Python's `packaging.version` (PEP 440), where `0.22.7.3` > `0.22.7-2` > `0.22.7`.
`requires_hermes` in `plugin.yaml` stays the oldest release the plugin is known to work with.

## 0.22.7.3

Tested with Hermes v0.22.7 and 0.21.5. Vendors self-hosted-agent-sandbox v0.2.0.

- **Dangerous-command approval stays on.** The provider sets `skip_container_guards = False`:
  results are mirrored to the host and git network commands run there, so Hermes no longer treats
  this backend as a sealed container.
- **Environment variables are an allowlist.** Only names listed in `agent_sandbox_forward_env`
  (`AGENT_SANDBOX_FORWARD_ENV`), by name or glob, reach the sandbox; the default is empty.
  `agent_sandbox_env_skip` still withholds names the allowlist matches.
  Upgrading: list what your builds need, e.g. `MY_BUILD_FLAG,NPM_CONFIG_REGISTRY`. Never list tokens or keys.
- A variable forwarded earlier in the session and then dropped is unset in the sandbox.
- **Git config is an exact key allowlist,** for `~/.gitconfig` and for each repository's
  `.git/config` and `config.worktree` in the code dirs: no aliases, `core.sshCommand`, `core.askpass`, helpers,
  includes, `http.*`, `url.*`, nor values with `user:pass@`.
- Version scheme: four parts instead of the `-N` suffix (see the top of this file).

## 0.22.7-2

- The sandbox itself moved to [self-hosted-agent-sandbox](https://github.com/xiaoyaner0201/self-hosted-agent-sandbox):
  cluster scripts, the core library and the offline routing tests live there now.
- The plugin is a thin Hermes adapter over a vendored, unmodified copy of that core
  (`_vendor/agent_sandbox`, checked by `tests/vendored_core.py`); behaviour is unchanged
  (acceptance suites pass on Hermes 0.21.5 and 0.22.7).
- Claim labels are now `agent-sandbox/session` and `agent-sandbox/app`; the in-sandbox state dir is
  `/tmp/.agent-sbx`. Claims made by older versions keep their own TTL and expire on their own.

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
