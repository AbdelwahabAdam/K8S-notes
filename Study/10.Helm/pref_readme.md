# Helm — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## What Helm does

Package manager for K8s — **Chart** → **Release** → K8s objects

```bash
helm install / upgrade / rollback / uninstall
```

---

## Helm 2 vs 3 (know this)

| | Helm 2 | Helm 3 |
|--|--------|--------|
| Tiller | Yes (security risk) | **No** |
| Merge | 2-way | **3-way** (chart + live + last release) |

---

## Key components

| Term | Meaning |
|------|---------|
| **Chart** | Package (Chart.yaml, values.yaml, templates/) |
| **Release** | Deployed instance of a chart |
| **Repository** | Chart hosting (Bitnami, Artifact Hub) |
| **values.yaml** | Default config; override with `-f` or `--set` |

---

## Common commands

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update && helm repo list
helm search hub/repo wordpress
helm install my-release bitnami/wordpress
helm install my-release bitnami/wordpress -f custom-values.yaml
helm install my-release bitnami/wordpress --set key=val
helm upgrade my-release bitnami/wordpress
helm rollback my-release 1
helm history / list / status / uninstall my-release
helm pull bitnami/wordpress --untar
helm template my-release ./chart    # dry render
```

---

## Customize values

| Method | Example |
|--------|---------|
| `--set` | `--set replicaCount=3` |
| `-f` file | `-f custom-values.yaml` |
| Local chart | `helm pull --untar` → edit → `helm install ./chart` |

---

## Chart hooks (awareness)

Annotations: `helm.sh/hook` — pre/post install, upgrade, delete, rollback

---

## Exam tips

1. Helm 3 = no Tiller
2. Each upgrade = new **revision** (see `helm history`)
3. `helm rollback <release> <revision>`
4. Chart version ≠ appVersion in Chart.yaml
5. Release metadata stored as **Secrets** in namespace (Helm 3)

---

## Kubernetes Docs — YAML Example Locations

| Resource charts deploy | Official docs |
|------------------------|---------------|
| Deployment, Service, Ingress | [Workloads](https://kubernetes.io/docs/concepts/workloads/) · [Service](https://kubernetes.io/docs/concepts/services-networking/service/) |
| Job (hooks) | [Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/) |
| Helm charts | [Helm Chart Guide](https://helm.sh/docs/topics/charts/) |
