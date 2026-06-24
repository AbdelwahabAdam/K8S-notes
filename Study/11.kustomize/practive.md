# CKA Practice — Kustomize

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. Problem Statement & Ideology

**Q1.** You maintain identical nginx Deployment YAML copied into `dev/`, `stg/`, and `prod/` folders with only replica counts differing. What Kustomize pattern eliminates this duplication?

**Answer:**

Use a **base** directory with shared manifests and **overlays** per environment that patch only what differs.

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── nginx-depl.yaml
│   └── service.yaml
└── overlays/
    ├── dev/kustomization.yaml
    ├── stg/kustomization.yaml
    └── prod/kustomization.yaml
```

- **Imperative:** `kubectl apply -k overlays/dev/`
- **Declarative:** Base + overlay `kustomization.yaml` files define the desired state

---

**Q2.** What is the core ideology of Kustomize compared to copying YAML files?

**Answer:**

**Don't repeat yourself** — keep one canonical base; environments apply **transformers** and **patches** instead of maintaining full duplicate manifests.

- **Imperative:** `kustomize build overlays/prod/ | kubectl apply -f -`
- **Declarative:** `overlays/prod/kustomization.yaml` references `../../base` and adds prod-specific patches

---

### 2. Kustomize vs Helm

**Q1.** When should you choose Kustomize over Helm for managing an in-house application across dev/stg/prod?

**Answer:**

Choose **Kustomize** when you have native YAML manifests and need environment variants via patches/overlays — no templating, built into `kubectl`. Choose **Helm** for distributable packaged apps with repos, releases, and Go templates.

- **Imperative:** `kubectl apply -k overlays/prod/`
- **Declarative:** Overlay `kustomization.yaml` files (no Helm chart templates)

---

### 3. Installation & kubectl Integration

**Q1.** Apply all manifests under `./k8s/` using built-in kubectl Kustomize support (no standalone binary).

**Answer:**

- **Imperative:**

```bash
kubectl apply -k ./k8s/
kubectl delete -k ./k8s/
kubectl kustomize ./k8s/    # preview — same as kustomize build
```

- **Declarative:** The `kustomization.yaml` in `./k8s/` is the declarative entry point

---

**Q2.** Install standalone `kustomize` CLI and preview rendered YAML before applying.

**Answer:**

- **Imperative:**

```bash
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
kustomize build k8s/
kustomize build k8s/ | kubectl apply -f -
```

- **Declarative:** N/A for CLI install; manifests remain in `kustomization.yaml`

---

### 4. The kustomization.yaml File

**Q1.** Create a minimal base that deploys one nginx Deployment and adds label `company: hopa` to all resources.

**Answer:**

- **Imperative:** `kubectl apply -k base/`
- **Declarative:**

**base/nginx-deployment.yaml:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx
```

**base/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - nginx-deployment.yaml
commonLabels:
  company: hopa
```

---

**Q2.** What file must exist in every Kustomize directory for `kubectl apply -k` to work?

**Answer:**

`kustomization.yaml` (with `apiVersion: kustomize.config.k8s.io/v1beta1` and `kind: Kustomization`).

- **Imperative:** `kubectl apply -k <dir>/`
- **Declarative:** The `kustomization.yaml` itself

---

### 5. Building & Applying

**Q1.** Preview the fully rendered manifests for `overlays/dev/` without applying, then apply them.

**Answer:**

- **Imperative:**

```bash
kustomize build overlays/dev/
kubectl apply -k overlays/dev/
```

- **Declarative:** `kubectl apply -k overlays/dev/` applies the built output from declarative kustomization config

---

**Q2.** Delete all resources previously applied from `overlays/stg/`.

**Answer:**

- **Imperative:**

```bash
kubectl delete -k overlays/stg/
# or
kustomize build overlays/stg/ | kubectl delete -f -
```

- **Declarative:** Same kustomization that created resources is used to compute deletion set

---

### 6. Managing Directories

**Q1.** Organize `api/` and `db/` subdirectories under `k8s/`, each with its own `kustomization.yaml`. Deploy everything with one command.

**Answer:**

- **Imperative:** `kubectl apply -k ./k8s/`
- **Declarative:**

**k8s/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api/
  - db/
```

**k8s/api/kustomization.yaml:**

```yaml
resources:
  - api-deployment.yaml
  - api-service.yaml
```

---

### 7. Common Transformers

**Q1.** Add namespace `lap`, prefix `start-`, suffix `-end`, label `owner: hopa`, and annotation `branch: master` to all resources in a kustomization.

**Answer:**

- **Imperative:** `kubectl apply -k .` after editing kustomization
- **Declarative:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - nginx-deployment.yaml
namespace: lap
namePrefix: start-
nameSuffix: -end
commonLabels:
  owner: hopa
commonAnnotations:
  branch: master
```

Result: Deployment named `start-nginx-deployment-end` in namespace `lap` with added labels/annotations.

---

**Q2.** What does `commonLabels` do beyond adding labels to metadata?

**Answer:**

Kustomize also updates **label selectors** in Deployments, Services, etc., so selectors stay consistent with pod template labels.

- **Imperative:** `kustomize build .` and inspect `spec.selector.matchLabels`
- **Declarative:** Set `commonLabels` in `kustomization.yaml`

---

### 8. Image Transformers

**Q1.** Replace all references to image `nginx` with `haproxy:2.4` across every resource in the kustomization.

**Answer:**

- **Imperative:** `kubectl apply -k .`
- **Declarative:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - nginx-deployment.yaml
images:
  - name: nginx
    newName: haproxy
    newTag: "2.4"
```

---

**Q2.** Change only the tag of `nginx` to `1.25` without changing the image name.

**Answer:**

- **Imperative:** `kubectl apply -k overlays/prod/`
- **Declarative:**

```yaml
images:
  - name: nginx
    newTag: "1.25"
```

---

### 9. Patches

**Q1.** Set `nginx-deployment` replicas to 6 using a JSON 6902 inline patch.

**Answer:**

- **Imperative:** `kubectl apply -k .`
- **Declarative:**

```yaml
patches:
  - target:
      kind: Deployment
      name: nginx-deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 6
```

---

**Q2.** Patch replicas using a strategic merge patch (Kubernetes-aware merge) for Deployment `myapp-deployment`.

**Answer:**

- **Imperative:** `kubectl apply -k overlays/prod/`
- **Declarative:**

```yaml
patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: myapp-deployment
      spec:
        replicas: 6
```

---

**Q3.** Apply a patch from external file `replica-patch.yaml` targeting Deployment `nginx-deployment`.

**Answer:**

- **Imperative:** `kubectl apply -k .`
- **Declarative:**

**kustomization.yaml:**

```yaml
patches:
  - path: replica-patch.yaml
    target:
      kind: Deployment
      name: nginx-deployment
```

**replica-patch.yaml:**

```yaml
- op: replace
  path: /spec/replicas
  value: 6
```

---

### 10. Overlays (Base + Environment)

**Q1.** Dev overlay: 2 replicas for nginx; prod overlay: 5 replicas plus an HPA resource only in prod.

**Answer:**

- **Imperative:**

```bash
kubectl apply -k overlays/dev/
kubectl apply -k overlays/prod/
```

- **Declarative:**

**overlays/dev/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 2
    target:
      kind: Deployment
      name: nginx-deployment
```

**overlays/prod/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
  - hpa.yaml
patches:
  - patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
    target:
      kind: Deployment
      name: nginx-deployment
```

---

**Q2.** Modern syntax: reference base using `resources: [../../base]` instead of deprecated `bases:`. Write the dev overlay kustomization.

**Answer:**

- **Imperative:** `kubectl apply -k overlays/dev/`
- **Declarative:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
```

---

### 11. Components

**Q1.** Dev overlay imports base plus optional `db` component; premium overlay imports base plus `db` and `caching` components.

**Answer:**

- **Imperative:**

```bash
kubectl apply -k overlays/dev/
kubectl apply -k overlays/premium/
```

- **Declarative:**

**overlays/dev/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
components:
  - ../../components/db
```

**overlays/premium/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
components:
  - ../../components/db
  - ../../components/caching
```

---

### 12. Cheat Sheet & Resources

**Q1.** Quick reference: build, apply, delete, and preview with kubectl only.

**Answer:**

- **Imperative:**

```bash
kustomize build <dir>
kubectl apply -k <dir>
kubectl delete -k <dir>
kubectl kustomize <dir>
```

- **Declarative:** `<dir>/kustomization.yaml` drives all operations

---

## Mixed Topic Questions

### Scenario 1 — Three-environment rollout

Base has nginx (1 replica) and redis. Dev: 2 nginx replicas + dev ConfigMap. Stg: 3 replicas. Prod: 5 replicas + HPA. Deploy dev and prod.

**Answer:**

```bash
kustomize build overlays/dev/
kubectl apply -k overlays/dev/
kubectl apply -k overlays/prod/
kubectl get deploy,hpa -n <namespace>
```

Ensure each overlay's `kustomization.yaml` references `../../base` and applies replica patches; prod adds `hpa.yaml` in `resources`.

---

### Scenario 2 — Image promotion pipeline

Base uses `nginx:latest`. Stg overlay retags to `nginx:1.25`. Prod overlay switches image to `haproxy:2.4`. Show both overlay `images` blocks.

**Answer:**

**overlays/stg/kustomization.yaml:**

```yaml
resources:
  - ../../base
images:
  - name: nginx
    newTag: "1.25"
```

**overlays/prod/kustomization.yaml:**

```yaml
resources:
  - ../../base
images:
  - name: nginx
    newName: haproxy
    newTag: "2.4"
```

```bash
kubectl apply -k overlays/stg/
kubectl apply -k overlays/prod/
```

---

### Scenario 3 — Global transformers + surgical patch

All resources need namespace `lap`, label `team: platform`, and Deployment `api-deployment` needs 10 replicas via JSON patch.

**Answer:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - api-deployment.yaml
  - api-service.yaml
namespace: lap
commonLabels:
  team: platform
patches:
  - target:
      kind: Deployment
      name: api-deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 10
```

```bash
kubectl apply -k .
```

---

### Scenario 4 — Multi-directory monorepo

`k8s/` contains `api/` and `db/` subdirs. Deploy entire stack and verify all pods.

**Answer:**

```bash
kubectl apply -k ./k8s/
kubectl get pods -A -l team=platform   # if commonLabels used
kubectl get all -n <namespace>
```

Root `kustomization.yaml` lists `api/` and `db/` under `resources`.

---

### Scenario 5 — Kustomize vs Helm (exam scenario)

Your team ships an internal API with environment-specific ConfigMaps and replica counts. Another team distributes a public database chart. Which tool for each?

**Answer:**

- **Internal API (env variants):** Kustomize — base + overlays, `kubectl apply -k`
- **Public DB chart (versioned package):** Helm — `helm install` from repo with `values.yaml`

---

### Scenario 6 — Component-based optional features

Premium tenants get redis caching; standard tenants get base only. Use Kustomize components.

**Answer:**

```bash
kubectl apply -k overlays/standard/    # base only
kubectl apply -k overlays/premium/     # base + components/db + components/caching
```

**overlays/premium/kustomization.yaml:**

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
components:
  - ../../components/db
  - ../../components/caching
```
