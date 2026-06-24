# CKA Practice — Helm

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. What is Helm?

**Q1.** What problem does Helm solve compared to managing dozens of loose YAML manifests manually?

**Answer:**

Helm packages Kubernetes applications as **charts** — versioned, installable bundles with defaults and templates. A single `helm install` creates a **release** (running instance) and tracks all generated resources together, with built-in upgrade, rollback, and uninstall.

- **Imperative:** `helm install my-release bitnami/nginx`
- **Declarative:** Install from a local chart directory after editing `values.yaml`: `helm install my-release ./nginx`

---

**Q2.** You need to deploy WordPress with MariaDB as one coordinated application. Which Helm concept represents the installed running instance in the cluster?

**Answer:**

A **release** is the running instance of a chart. Each install/upgrade creates a new **revision** stored as a Secret in the release namespace.

- **Imperative:** `helm list` and `helm status my-release`
- **Declarative:** N/A — release state is managed by Helm CLI against the API server

---

### 2. Helm 2 vs Helm 3

**Q1.** An older guide references **Tiller** and a cluster-side component with elevated permissions. Which Helm version should you use on CKA, and what replaced Tiller?

**Answer:**

Use **Helm 3**. Tiller was removed; Helm 3 talks directly to the **kube-apiserver** using your kubeconfig credentials. Release metadata is stored in **Secrets** in the release namespace (not via Tiller).

- **Imperative:** `helm version` — confirm `version.BuildInfo.Version` is v3.x
- **Declarative:** N/A

---

**Q2.** After a manual `kubectl edit` changed a Deployment replica count, you run `helm upgrade`. Why might Helm 3 preserve your live change better than Helm 2?

**Answer:**

Helm 3 uses **3-way strategic merge**: chart templates + **live cluster state** + **last release manifest**. Helm 2 used 2-way merge and could overwrite live edits.

- **Imperative:** `helm upgrade my-release bitnami/nginx --reuse-values`
- **Declarative:** Update `values.yaml` and run `helm upgrade my-release ./nginx -f values.yaml`

---

### 3. Helm Components

**Q1.** Name the four main parts of a Helm chart directory and what each contains.

**Answer:**

| Part | Purpose |
|------|---------|
| `Chart.yaml` | Chart metadata (name, version, dependencies) |
| `values.yaml` | Default configuration parameters |
| `templates/` | Go-templated Kubernetes manifests |
| `crds/` | Custom Resource Definitions (Helm 3; not auto-deleted on uninstall) |

- **Imperative:** `helm pull bitnami/wordpress --untar` then `ls wordpress/`
- **Declarative:** Example `Chart.yaml`:

```yaml
apiVersion: v2
name: myapp
description: My application chart
type: application
version: 0.1.0
appVersion: "1.0.0"
```

---

**Q2.** A chart depends on Bitnami MariaDB. Where do you declare that dependency?

**Answer:**

In `Chart.yaml` under `dependencies`, then run `helm dependency update` to vendor subcharts into `charts/`.

- **Imperative:**

```bash
helm dependency update ./mychart
helm install my-release ./mychart
```

- **Declarative:**

```yaml
# Chart.yaml
dependencies:
  - name: mariadb
    version: "9.x.x"
    repository: https://charts.bitnami.com/bitnami
    condition: mariadb.enabled
```

---

### 4. Installation

**Q1.** Install Helm 3 on a Linux exam node and verify it works.

**Answer:**

- **Imperative:**

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

- **Declarative:** N/A — Helm CLI is installed on the workstation, not as a Kubernetes manifest

---

### 5. Charts & Repositories

**Q1.** Add the Bitnami chart repository, update the local cache, and search for `wordpress` charts.

**Answer:**

- **Imperative:**

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo wordpress
helm search hub wordpress    # searches Artifact Hub
```

- **Declarative:** N/A — repository configuration is CLI-managed (`helm repo add`)

---

**Q2.** Remove a repository named `bitnami` from your local Helm config.

**Answer:**

- **Imperative:** `helm repo remove bitnami`
- **Declarative:** N/A

---

### 6. Installing Releases

**Q1.** Install release `blog` from `bitnami/wordpress` in namespace `blog`, creating the namespace if needed.

**Answer:**

- **Imperative:**

```bash
helm install blog bitnami/wordpress --namespace blog --create-namespace
helm list -n blog
helm status blog -n blog
```

- **Declarative:** Same install command with a values file:

```bash
helm install blog bitnami/wordpress -n blog --create-namespace -f blog-values.yaml
```

---

**Q2.** Completely remove release `blog` and all chart-managed resources from namespace `blog`.

**Answer:**

- **Imperative:** `helm uninstall blog -n blog`
- **Declarative:** N/A — uninstall is imperative; CRDs in `crds/` are **not** removed automatically

---

### 7. Customizing Chart Parameters

**Q1.** Install `bitnami/wordpress` with blog title `"CKA Practice"` using a one-line override.

**Answer:**

- **Imperative:**

```bash
helm install wp bitnami/wordpress --set wordpressBlogName="CKA Practice"
```

- **Declarative:** `custom-values.yaml`:

```yaml
wordpressBlogName: "CKA Practice"
replicaCount: 3
service:
  type: NodePort
```

```bash
helm install wp bitnami/wordpress -f custom-values.yaml
```

---

**Q2.** Download the chart locally, change `replicaCount` to 3 in `values.yaml`, and install from the local directory.

**Answer:**

- **Imperative:**

```bash
helm pull bitnami/wordpress --untar
# Edit wordpress/values.yaml — set replicaCount: 3
helm install wp ./wordpress
```

- **Declarative:** Edit `wordpress/values.yaml` (declarative config) then `helm install wp ./wordpress`

---

### 8. Lifecycle Management

**Q1.** Upgrade release `wp` to 5 replicas, view revision history, then roll back to revision 1.

**Answer:**

- **Imperative:**

```bash
helm upgrade wp bitnami/wordpress --set replicaCount=5
helm history wp
helm rollback wp 1
```

- **Declarative:**

```yaml
# values.yaml
replicaCount: 5
```

```bash
helm upgrade wp bitnami/wordpress -f values.yaml
helm rollback wp 1
```

---

**Q2.** Preview rendered manifests without installing anything (debug a failed install).

**Answer:**

- **Imperative:**

```bash
helm template wp bitnami/nginx
helm install wp bitnami/nginx --dry-run --debug
```

- **Declarative:** `helm template wp ./mychart -f values.yaml` renders the declarative chart + values into YAML output

---

### 9. Chart Hooks

**Q1.** Run a database migration Job **after** install and upgrade, delete the Job on success, and run it before other post-install hooks (weight 1).

**Answer:**

- **Imperative:** Hooks deploy with the chart; trigger via `helm install` or `helm upgrade`
- **Declarative:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "1"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: migrate-tool:latest
          command: ["./migrate.sh"]
      restartPolicy: Never
```

---

**Q2.** Which hook runs immediately **before** chart resources are deleted during `helm uninstall`?

**Answer:**

`pre-delete` — runs before resources are removed; `post-delete` runs after.

- **Imperative:** `helm uninstall my-release` triggers hooks automatically
- **Declarative:** Annotate the hook resource with `"helm.sh/hook": pre-delete`

---

### 10. Cheat Sheet & Resources

**Q1.** List all releases across all namespaces and show the current revision number for release `wp`.

**Answer:**

- **Imperative:**

```bash
helm list -A
helm history wp
helm status wp
```

- **Declarative:** N/A

---

## Mixed Topic Questions

### Scenario 1 — Fresh WordPress deployment

Add Bitnami repo, search for WordPress, install release `cms` in namespace `cms` with blog name `"Hopa Blog"` and `service.type=NodePort`, then verify status.

**Answer:**

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm search repo wordpress
helm install cms bitnami/wordpress -n cms --create-namespace \
  --set wordpressBlogName="Hopa Blog" \
  --set service.type=NodePort
helm status cms -n cms
kubectl get all -n cms
```

---

### Scenario 2 — Upgrade gone wrong

Release `api` is at revision 3 after a bad upgrade. Roll back to revision 2 and confirm history.

**Answer:**

```bash
helm history api
helm rollback api 2
helm status api
kubectl get deploy -n <namespace>
```

---

### Scenario 3 — Local chart workflow

Pull `bitnami/nginx` untarred, add a `commonLabels` entry via `values.yaml`, dry-run install as `edge`, then install for real.

**Answer:**

```bash
helm pull bitnami/nginx --untar
# Edit nginx/values.yaml — add labels or replicaCount
helm install edge ./nginx --dry-run --debug
helm install edge ./nginx
helm list
```

---

### Scenario 4 — Helm 3 security question

Explain why Helm 3 is preferred over Helm 2 for production clusters (exam short answer + command to confirm version).

**Answer:**

Helm 3 removes **Tiller** (no cluster-wide component with excessive RBAC). Releases stored as Secrets; direct API access. Command: `helm version`.

---

### Scenario 5 — Post-install migration hook

Your chart must run a one-time schema Job after every install and upgrade. Write the hook Job manifest and the install command.

**Answer:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: schema-init
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: schema
          image: mydb-schema:1.0
      restartPolicy: Never
```

```bash
helm install myapp ./mychart -n prod --create-namespace
kubectl get jobs -n prod
```

---

### Scenario 6 — Uninstall and cleanup

Uninstall release `cms` from namespace `cms`. What remains in the cluster? How do you list releases before and after?

**Answer:**

```bash
helm list -n cms
helm uninstall cms -n cms
helm list -n cms
```

Chart-managed resources (Deployments, Services, etc.) are removed. **CRDs** from `crds/` folder are **not** auto-deleted. Hook resources follow their `hook-delete-policy`.
