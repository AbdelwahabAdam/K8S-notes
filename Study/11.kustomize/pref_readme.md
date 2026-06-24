# Kustomize — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Core idea

**Base** (shared YAML) + **Overlays** (env-specific patches) — no templating

```
base/ + overlays/dev|stg|prod/
```

---

## Kustomize vs Helm

| Kustomize | Helm |
|-----------|------|
| Native YAML patches | Templated charts |
| Built into kubectl (`-k`) | Separate package manager |

---

## Essential files

Every directory needs **`kustomization.yaml`**:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
```

---

## Build & apply

```bash
kustomize build k8s/
kubectl apply -k k8s/
kubectl delete -k k8s/
kubectl kustomize k8s/    # same as build
```

---

## Common transformers

| Transformer | Effect |
|-------------|--------|
| `commonLabels` | Labels on all resources |
| `namespace` | Namespace for all |
| `namePrefix` / `nameSuffix` | Rename all resources |
| `commonAnnotations` | Annotations on all |
| `images` | Change image name/tag |

```yaml
images:
  - name: nginx
    newName: haproxy
    newTag: "2.4"
```

---

## Patches

| Type | Syntax |
|------|--------|
| **JSON 6902** | `op: replace`, `path`, `value` |
| **Strategic merge** | Partial resource YAML |

```yaml
patches:
  - target:
      kind: Deployment
      name: nginx-deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
```

Inline or separate file (`path: patch.yaml`)

---

## Overlays

```yaml
# overlays/prod/kustomization.yaml
resources:
  - ../../base
patches:
  - ...
```

```bash
kubectl apply -k overlays/prod/
```

---

## Components

Optional reusable modules (`components/db/`) imported via `components:` key

---

## Exam tips

1. `kubectl apply -k` = built-in Kustomize
2. `resources:` lists YAML files or subdirs (with own kustomization.yaml)
3. Overlays reference base with `resources: [../../base]`
4. Patches need `target` (kind, name) for JSON 6902
5. No Helm-style templating — pure YAML + patches

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs |
|-------|---------------|
| Kustomize | [Kustomization task](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/) |
| Deployment / Service | [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) |
| Patches & overlays | [Kustomize reference](https://kubectl.docs.kubernetes.io/references/kustomize/) |
