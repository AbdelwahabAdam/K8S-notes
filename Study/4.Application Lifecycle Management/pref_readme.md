# Application Lifecycle — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Rollouts

| Strategy | Effect |
|----------|--------|
| **RollingUpdate** (default) | Zero downtime |
| **Recreate** | Downtime — kill all, then create |

```bash
kubectl apply -f deploy.yaml          # best — triggers rollout
kubectl set image deploy/x c=img:tag  # imperative — may drift from file
kubectl rollout status/history/undo deployment/x
kubectl rollout undo deployment/x --to-revision=2
```

---

## Docker → Pod mapping

| Docker | Pod field |
|--------|-----------|
| ENTRYPOINT | `command` |
| CMD | `args` |

---

## Config injection

| Source | Sensitive? |
|--------|------------|
| `env.value` | No |
| **ConfigMap** | No |
| **Secret** | Yes (base64 in etcd, not encrypted by default) |

```bash
kubectl create configmap x --from-literal=k=v
kubectl create secret generic x --from-literal=k=v
echo -n "val" | base64   # encode for YAML
echo 'xxx' | base64 -d   # decode
```

**Pod refs:** `envFrom`, `configMapKeyRef`/`secretKeyRef`, volume mount

---

## Encrypt secrets at rest

Add to kube-apiserver static Pod:
- `--encryption-provider-config=/etc/kubernetes/enc/enc.yaml`
- Mount enc directory
- Re-encrypt: `kubectl get secrets -A -o json | kubectl replace -f -`

---

## Multi-container Pod

- Shared network → `localhost` between containers
- Shared volumes via `volumeMounts`
- **Whole Pod restarts** — not individual containers (main containers)

---

## Init vs sidecar

| | Init | Sidecar (native) |
|--|------|------------------|
| Block main? | Yes — sequential | No — `restartPolicy: Always` in initContainers |
| On failure | Restart all inits | Sidecar keeps running |

---

## Probes

| Probe | On failure |
|-------|------------|
| **Liveness** | Restart container |
| **Readiness** | Remove from Service |
| **Startup** | Blocks other probes |

---

## Autoscaling

| Tool | Scales | Needs |
|------|--------|-------|
| **HPA** | Pod count | Metrics Server |
| **VPA** | Pod resources | VPA installed |
| **Cluster Autoscaler** | Node count | Cloud provider |

```bash
kubectl autoscale deployment x --cpu-percent=50 --min=1 --max=10
kubectl get hpa
```

**HPA** = stateless/web; **VPA** = stateful/DB (restarts Pods)

---

## Stateful vs stateless

- **Stateless** — no local state; safe to scale/replace (web, API)
- **Stateful** — persistent identity/data (DB) — use StatefulSet + PVC

---

## Exam tips

1. Prefer `kubectl apply` over `set image` for rollouts
2. Secret values in YAML must be base64
3. Multi-container logs need `-c`
4. Init containers run **in order**, all must succeed
5. HPA v2 uses `autoscaling/v2` with `averageUtilization`

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs (YAML examples) |
|-------|-------------------------------|
| Deployment / rollout | [Run a Stateless Application](https://kubernetes.io/docs/tasks/run-application/run-stateless-application-deployment/) |
| Command & args | [Define Command and Arguments](https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/) |
| ConfigMap | [Configure Pod with ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) |
| Secret | [Distribute Credentials with Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/) |
| Encrypt secrets at rest | [Encrypt Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/) |
| Init / sidecar containers | [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/) · [Sidecar Containers](https://kubernetes.io/docs/concepts/workloads/pods/sidecar-containers/) |
| Probes | [Configure Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) |
| HPA | [Horizontal Pod Autoscale](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) |
| In-place resize | [Resize Container Resources](https://kubernetes.io/docs/tasks/configure-pod-container/resize-container-resources/) |
