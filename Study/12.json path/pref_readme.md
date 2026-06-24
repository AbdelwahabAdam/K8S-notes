# JSON Path — Pref Revision (CKA)

Quick exam revision. See [enhanced_readme.md](./enhanced_readme.md) for full detail.

---

## Workflow (4 steps)

1. `kubectl get nodes`
2. `kubectl get nodes -o json` — see structure
3. Build path: `.items[0].spec.containers[0].image`
4. `kubectl get pods -o=jsonpath='{.items[0].spec.containers[0].image}'`

---

## JSONPath symbols

| Symbol | Meaning |
|--------|---------|
| `.items[0]` | First item in list |
| `.items[*]` | All items |
| `.metadata.name` | Field access |
| `{range .items[*]}...{end}` | Loop |

---

## Common queries

```bash
# All Pod names
kubectl get pods -o=jsonpath='{.items[*].metadata.name}'

# First container image
kubectl get pods -o=jsonpath='{.items[0].spec.containers[0].image}'

# Node name + CPU (range)
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'

# Single Pod field
kubectl get pod nginx -o=jsonpath='{.status.podIP}'
```

---

## Formatting

```bash
# Newline
'{"\n"}'

# Tab
'{"\t"}'

# Space between fields
'{.items[*].metadata.name}{" "}{.items[*].status.capacity.cpu}'
```

---

## Custom columns (often easier on exam)

```bash
kubectl get nodes -o=custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu
```

Format: `HEADER:JSONPath`

---

## Sorting

```bash
kubectl get nodes --sort-by=.metadata.name
kubectl get pods --sort-by=.status.startTime
```

---

## Output formats quick ref

| Flag | Use |
|------|-----|
| `-o json` | Full JSON (explore structure) |
| `-o yaml` | YAML |
| `-o jsonpath='...'` | Filter fields |
| `-o custom-columns=...` | Custom table |
| `-o wide` | Extra columns |
| `-o name` | resource/name only |

---

## Exam tips

1. Wrap JSONPath in **single quotes**: `-o=jsonpath='{...}'`
2. List objects always under `.items[]`
3. Containers are array: `.spec.containers[0]`
4. Use `custom-columns` when asked for a table with headers
5. `range` + `{"\n"}` for one value per line

---

## Kubernetes Docs — YAML Example Locations

| Topic | Official docs |
|-------|---------------|
| JSONPath | [kubectl jsonpath](https://kubernetes.io/docs/reference/kubectl/jsonpath/) |
| Custom columns | [kubectl custom columns](https://kubernetes.io/docs/reference/kubectl/#custom-columns) |
| Pod fields | [Pod API reference](https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/pod-v1/) |
| Node fields | [Node API reference](https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/node-v1/) |
