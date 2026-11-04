<div align="center">

# 🧊 hermes-sandbox-cluster

**A self-hosted sandbox cluster for Hermes Agent: every command the agent runs goes into a disposable gVisor sandbox on k3s nodes you own, with a shared warm pool and per-node package caches.**

English · [简体中文](README.zh-CN.md)

![License](https://img.shields.io/badge/license-Apache--2.0-blue) ![Hermes](https://img.shields.io/badge/Hermes-terminal%20backend-8A2BE2) ![k3s](https://img.shields.io/badge/k3s-v1.37-FFC61C) ![gVisor](https://img.shields.io/badge/isolation-gVisor-4285F4) ![agent-sandbox](https://img.shields.io/badge/kubernetes--sigs%2Fagent--sandbox-v1.0.9-326CE5) ![Self-hosted](https://img.shields.io/badge/self--hosted-multi--node-2E8B57) ![Status](https://img.shields.io/badge/status-early-orange)

</div>

---

[Hermes Agent](https://github.com/NousResearch/hermes-agent) keeps running where it runs today.
Model calls, chat, MCP, the browser and every credential stay on that host. Only the **commands the
agent executes** move into a sandbox pod. The pod is claimed in about 0.2 s and thrown away when the
session ends.

Built on [k3s](https://k3s.io), [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox)
and [gVisor](https://gvisor.dev). It needs no KVM, so ordinary cloud VMs work.

## ✨ Highlights

- **⚡ Fast:** a warm-pool claim takes 0.18 s (median) and the first command finishes at 0.31 s. A cold start takes 0.73 s.
- **🧱 Hard limits:** each node gets a memory budget for all of its sandboxes (for example 4 GiB), and existing services keep the rest of the machine. A sandbox that exceeds its own limit is killed within seconds, and the other sandboxes keep running.
- **🔁 Transparent sync:**
  - The host's environment variables are forwarded wholesale.
  - Declared config files are re-checked before every command.
  - The task's code, including `.git`, is synced both ways, so the host tree stays the source of truth.
- **🔐 Credentialed commands run on the host:** `git push/pull/fetch/clone/ls-remote` and any exact sub-commands you list (for example `gh pr create`) run on the host when issued as their own command, so their tokens and credential helpers stay there. Env vars you mark as secret (`agent_sandbox_env_skip: "*_TOKEN,*_SECRET"`) stay there too.
- **📦 Warm caches:** every node keeps a separate package cache per tenant (Maven, npm, pnpm, pip, uv, Go, Gradle), and a daily job prunes old entries.
- **♻️ Nothing leaks:** a sandbox is deleted at session close or after 5 idle minutes. Every claim also carries a cluster-side expiry, so the cluster reclaims it even if Hermes crashes.

## 🗺️ How it works

```mermaid
flowchart TB
    subgraph HOST["🖥️ Hermes host"]
        H["Hermes Agent<br/>LLM · chat · MCP · browser"] --> P["agent_sandbox plugin"]
        C[("credentials<br/>git push · CLIs run here")] <-.-> P
        P <-. "two-way code sync" .-> W[("task workdir<br/>source of truth")]
    end
    P == "claim · exec · release · TCP 6443 only" ==> API
    subgraph K3S["☸️ k3s cluster · capped per node"]
        API["API server"] --> S1["🧊 sandbox · gVisor"]
        API --> S2["🧊 warm spare"]
        S1 --- K1[("per-tenant package cache")]
    end
    S1 -- "dependencies" --> R["Maven · npm · PyPI mirrors"]
```

**One command, step by step**

1. When the session starts, the plugin claims a ready sandbox from the tenant's warm pool, and the pool refills itself.
2. Before each command, the plugin pushes whatever changed on the host: environment variables, declared config files and code.
3. The command runs in the sandbox through `kubectl exec`.
4. Afterwards, files the sandbox created, changed or deleted are applied back to the host.
5. At session close, after 5 idle minutes, or when the cluster-side expiry passes, the sandbox is deleted. The package cache stays on the node.

## 📊 Measured

Three-node lab, 4 GiB pod budget per node, Hermes `main`.

| Scenario | Result |
|---|---|
| Claim from warm pool | 0.18 s median, first command done at 0.31 s |
| Cold start | 0.73 s · 18 concurrent cold starts ≤ 1.6 s |
| Over capacity | extra claims wait as Pending · hosts unaffected |
| Sandbox asks for 5 GiB (limit 3.5 GiB) | killed within 3 s · neighbours unaffected |
| Real Java project, 98 030 tests | all pass · peak 2.6 GiB |
| Maven rebuild, offline | resolved entirely from the node cache |

## 🚀 Quick start

**1. Nodes** (on every Linux machine; the script fetches the official k3s installer, or uses `$SBX_DL/install-k3s.sh` when air-gapped)

```bash
# first node (becomes the k3s server)
SBX_NODE_IP=10.0.0.11 cluster/node-install.sh server
sudo cat /var/lib/rancher/k3s/server/node-token     # copy this to the other nodes as ./node-token

# every other node
SBX_NODE_IP=10.0.0.12 cluster/node-install.sh agent https://10.0.0.11:6443 ./node-token

# every node
cluster/gvisor-node.sh
cluster/cache-gc-install.sh      # optional: daily cache prune
```

**2. Cluster** (once, on the first node, where `kubectl` is `k3s kubectl`)

```bash
kubectl apply --server-side -f https://github.com/kubernetes-sigs/agent-sandbox/releases/download/v1.0.9/sandbox-with-extensions.yaml
kubectl create namespace sbx
kubectl apply -f cluster/runtimeclass.yaml -f cluster/rbac.yaml
cluster/render-pool.py --tenant team-a --image nousresearch/hermes-agent:v0.22.7 \
    --cache-mount /var/cache/pkg | kubectl apply -f -
cluster/make-kubeconfig.sh https://10.0.0.11:6443 > agent-sandbox.kubeconfig   # copy to the Hermes host
```

> [!TIP]
> Use the **same image** your Hermes host runs (the official `nousresearch/hermes-agent` image above, or your own). Paths, toolchains and cache env vars then match on both sides with no extra configuration.

**3. Hermes host**

```bash
cp -r plugin/agent_sandbox_backend "$HERMES_HOME/plugins/"
export AGENT_SANDBOX_KUBECONFIG=$PWD/agent-sandbox.kubeconfig   # from make-kubeconfig.sh
export AGENT_SANDBOX_POOL=sbx-team-a
hermes config set terminal.backend agent_sandbox
hermes plugins enable agent-sandbox-backend
```

`kubectl` must be on the host's `PATH`, or set `AGENT_SANDBOX_KUBECTL`. Rolling back takes one line:
`hermes config set terminal.backend local`.

> [!NOTE]
> The official `nousresearch/hermes-agent` image sets `HERMES_WRITE_SAFE_ROOT=/opt/data`, which makes the file tools refuse writes into your code dirs. Add them, e.g. `HERMES_WRITE_SAFE_ROOT=/opt/data:/workspaces`.

## 🧭 What runs where

| In the sandbox 🧊 | On the host 🖥️ |
|---|---|
| `terminal`: builds, tests, scripts, background processes | LLM calls and API keys |
| `read_file` · `write_file` · `patch` · `search_files` | chat platforms, MCP servers, browser |
| `execute_code` | `git push/pull/fetch/clone/ls-remote` and listed sub-commands, when issued alone |
| package installs, served from the node cache | the task working tree, which remains the git source of truth |

A command runs on the host only when it is listed commands plus glue that cannot touch files: a leading `cd <dir> &&` (an existing directory reached without symlinks), `echo`/`printf`, and filters fed by a pipe (`grep`, `jq`, `head`, `tail`, `sort`, `uniq`, `cut`, `tr`, `wc`) with short options from a fixed list, plus `>/dev/null`. It must also stay inside the code dirs: the working directory, every `cd` and every local path in a git command (a clone target, a `file://` remote) must resolve inside them, and `$VAR`, `~` and unquoted globs are not expanded on the host. Anything with a substitution, subshell, heredoc, file redirection, another program, an env prefix other than on/off switches such as `GIT_TRACE=1`, or a git option that runs a program (`--upload-pack`, `clone -u/-c/--template`, …) stays in the sandbox.

> [!IMPORTANT]
> List **exact sub-commands**, never a whole CLI that can run user-defined code. `gh` aliases and extensions, for example, execute arbitrary programs, so list `gh pr create`, `gh pr view` rather than `gh`. There the CLI is a
stub that prints a hint and exits with code 97, so the agent learns to issue it separately.

## ⚙️ Configuration

Every option can be set as an env var or under `terminal:` in `config.yaml`.

| Env | Config key | Default | Purpose |
|---|---|---|---|
| `AGENT_SANDBOX_POOL` | `agent_sandbox_pool` | `hermes-4g` | warm pool to claim from |
| `AGENT_SANDBOX_NAMESPACE` | `agent_sandbox_namespace` | `sbx` | namespace of pool and claims |
| `AGENT_SANDBOX_KUBECONFIG` | `agent_sandbox_kubeconfig` | `~/.kube/agent-sandbox.yaml` | least-privilege kubeconfig |
| `AGENT_SANDBOX_KUBECTL` | `agent_sandbox_kubectl` | `kubectl` | kubectl binary |
| `AGENT_SANDBOX_SYNC_PATHS` | `agent_sandbox_sync_paths` | – | config files/dirs pushed at the same path |
| `AGENT_SANDBOX_CODE_DIRS` | `agent_sandbox_code_dirs` | task dir | two-way synced code dirs |
| `AGENT_SANDBOX_HOST_COMMANDS` | `agent_sandbox_host_commands` | git network ops, `git remote add/set-url` | command prefixes that run on the host, matched word by word (replaces the default list) |
| `AGENT_SANDBOX_ENV_SKIP` | `agent_sandbox_env_skip` | – | extra env names not to forward; globs like `*_TOKEN` work |
| `AGENT_SANDBOX_TASK_FILES` | `agent_sandbox_task_files` | – | files in a task root (`/workspaces/<ws>/<task>/`) pushed with the workdir, never pulled back |
| `AGENT_SANDBOX_IDLE_TTL` | `agent_sandbox_idle_ttl` | `1800` | cluster-side expiry in seconds, renewed while active |
| `AGENT_SANDBOX_PERSISTENT` | `agent_sandbox_persistent` | `false` | reuse one claim per task across sessions |
| `AGENT_SANDBOX_CLAIM_TIMEOUT` | `agent_sandbox_claim_timeout` | `180` | seconds to wait for a sandbox before giving up |

## 🌐 Network allowlist

Each arrow starts at the side that opens the connection.

**Hermes host → cluster** · the only path the plugin needs

| Port | To | Why |
|---|---|---|
| TCP 6443 | k3s server | Kubernetes API: claim and release sandboxes, and `kubectl exec`, which is tunnelled through the API server |

**Between cluster nodes**

| Port | Direction | Why |
|---|---|---|
| TCP 6443 | agents → server | node registration and API |
| TCP 10250 | server → every node | kubelet: exec and logs are proxied to the node running the pod |
| UDP 8472 | every node ↔ every node | flannel VXLAN pod network |
| TCP 2379–2380 | server ↔ server | only for multi-server (embedded etcd HA) |

**Sandboxes → outside:** open only what your builds need, such as your Maven/npm/PyPI mirrors, a
Go proxy, and container registries for the nodes' image pulls.

> [!NOTE]
> No inbound rule is needed toward the Hermes host or toward any sandbox. Code sync and host commands are always started by the host. If the host can reach the cluster only through a proxy, add `proxy-url:` to the kubeconfig cluster entry; `kubectl exec` works through HTTP and SOCKS proxies.

## 🔒 Security

- Sandboxes run under **gVisor**, as a non-root uid, with no service-account token and no service links.
- The git config copied into the sandbox drops credential helpers, includes, `extraheader`/cookie/SSL-key settings and any URL with `user:pass@`.
- Pull-back into `.git` is an allowlist (objects, refs, logs, `HEAD`, `index`, `packed-refs`, …). Config, hooks, gitfiles and everything else stay as the host has them, host-side git runs with `safe.bareRepository=explicit`, and writes through host symlinks that lead out of the code dirs are refused, so nothing built in the sandbox can plant a hook that a later host-side `git push` runs.
- Package caches are per tenant, so one tenant cannot poison another tenant's cache.
- The Hermes host's service account may only manage `sandboxclaims` and exec into pods in one namespace.
- Host commands run with the Hermes process's own `PATH`; the plugin checks the command text, not which `git` binary that `PATH` resolves to, so keep the host `PATH` free of directories the agent can write.

> [!WARNING]
> Environment forwarding is wholesale by default, so secrets in the host environment reach the sandbox unless you withhold them, e.g. `agent_sandbox_env_skip: "*_TOKEN,*_SECRET,*_PASSWORD,*_API_KEY"`.

## 🧪 Tests

`tests/route_table.py` (fixed cases) and `tests/route_fuzz.py` (random commands run through real
bash, asserting nothing is written outside the code dir) check host-command routing offline, with the Python of a Hermes install:
`HERMES_SRC=~/hermes-agent ~/hermes-agent/.venv/bin/python tests/route_table.py`.

`tests/accept.py` and `tests/task_layout.py` drive a real Hermes against a real cluster; their
docstrings describe the arguments. They cover:

- environment forwarding, and changes seen by the next command;
- config-file hot sync, and two-way code sync including deletes (empty directories created in the sandbox come back to the host);
- git commits made in the sandbox showing up on the host;
- host-command routing, and keeping secrets out of the sandbox;
- Maven resolution through your mirror, and offline cache hits;
- release at session close, and the cluster-side expiry.

## 📁 Layout

```text
plugin/agent_sandbox_backend/   Hermes plugin (terminal environment provider)
cluster/node-install.sh         k3s node with a hard pod memory budget, pod swap off
cluster/gvisor-node.sh          install runsc and register it with k3s containerd
cluster/runtimeclass.yaml       RuntimeClass "gvisor"
cluster/rbac.yaml               least-privilege service account for the Hermes host
cluster/make-kubeconfig.sh      kubeconfig for that service account
cluster/render-pool.py          per-tenant SandboxTemplate + SandboxWarmPool
cluster/example-pool.yaml       minimal generic pool
cluster/cache-gc*.sh            daily cache prune (age + size cap)
tests/                          end-to-end acceptance scripts
```

## 🛣️ Status

Early. Tested with Hermes `main` (terminal environment provider API) on Linux x86_64 nodes.

## 🔍 What the plugin touches

- **Runs** `kubectl` (the binary you point it at) as a subprocess, with the kubeconfig you name, against that kubeconfig's API server only.
- **Sends into the sandbox:** the host process environment (minus the skip list), the files in `agent_sandbox_sync_paths` and `agent_sandbox_task_files`, the task's code directories, the Hermes skills directory (read-only copy) and the host git config without credential-bearing settings.
- **Writes on the host:** only inside the code directories, with files the sandbox created, changed or deleted there (in `.git` only history and index; never through symlinks that leave the code dirs).
- **No other network calls,** no telemetry, no stored credentials, no background process of its own. Dangerous-command approval stays on.

## 📄 License

[Apache-2.0](LICENSE)
