# CKA Practice — JSON Path in Kubernetes

> Based on [enhanced_readme.md](./enhanced_readme.md)

---

## Topic Questions

### 1. What is JSONPath?

**Q1.** What is JSONPath and how does kubectl use it?

**Answer:**

JSONPath is a query language for extracting fields from JSON documents. `kubectl` uses it with `-o jsonpath='...'` to filter API server responses without external tools.

| Symbol | Meaning |
|--------|---------|
| `$` or `.` | Root object |
| `.field` | Child field |
| `[0]` | Array index |
| `[*]` | All elements |
| `['field']` | Field with special characters |

- **Imperative:** `kubectl get pods -o=jsonpath='{.items[0].metadata.name}'`
- **Declarative:** N/A — JSONPath queries live API objects, not manifest files

---

**Q2.** In a Pod list JSON response, what path returns all Pod names?

**Answer:**

`.items[*].metadata.name`

- **Imperative:** `kubectl get pods -o=jsonpath='{.items[*].metadata.name}'`
- **Declarative:** N/A

---

### 2. kubectl JSON Output Workflow

**Q1.** List the four steps to construct a JSONPath query for node CPU capacity.

**Answer:**

1. **Identify command** — `kubectl get nodes`
2. **See JSON structure** — `kubectl get nodes -o json`
3. **Form JSONPath** — `.items[0].status.capacity.cpu`
4. **Query** — `kubectl get nodes -o=jsonpath='{.items[0].status.capacity.cpu}'`

- **Imperative:** Full workflow above; optionally pipe to `jq .` for exploration
- **Declarative:** N/A

---

**Q2.** Explore Pod JSON structure before writing a JSONPath for container images.

**Answer:**

- **Imperative:**

```bash
kubectl get pods -o json | jq .
kubectl get pods -o json
# Then extract:
kubectl get pods -o=jsonpath='{.items[*].spec.containers[*].image}'
```

- **Declarative:** N/A

---

### 3. JSONPath Syntax

**Q1.** Given a Pod list, write JSONPath expressions for: (a) first Pod name, (b) all Pod names, (c) first container image in first Pod, (d) all images across all Pods.

**Answer:**

| Query | Expression |
|-------|------------|
| First Pod name | `.items[0].metadata.name` |
| All Pod names | `.items[*].metadata.name` |
| First container image (first Pod) | `.items[0].spec.containers[0].image` |
| All images | `.items[*].spec.containers[*].image` |

- **Imperative:**

```bash
kubectl get pods -o=jsonpath='{.items[0].metadata.name}'
kubectl get pods -o=jsonpath='{.items[*].metadata.name}'
kubectl get pods -o=jsonpath='{.items[0].spec.containers[0].image}'
kubectl get pods -o=jsonpath='{.items[*].spec.containers[*].image}'
```

- **Declarative:** N/A

---

### 4. Common Examples

**Q1.** Get the Pod IP of a Pod named `nginx` in the current namespace.

**Answer:**

- **Imperative:** `kubectl get pod nginx -o=jsonpath='{.status.podIP}'`
- **Declarative:** N/A

---

**Q2.** List all node names and CPU capacity in one command (space-separated pairs).

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=jsonpath='{.items[*].metadata.name}{" "}{.items[*].status.capacity.cpu}'
```

- **Declarative:** N/A

---

**Q3.** Get kubelet version of the first node and InternalIP addresses of all nodes.

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=jsonpath='{.items[0].status.nodeInfo.kubeletVersion}'
kubectl get nodes -o=jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'
```

- **Declarative:** N/A

---

**Q4.** Get available replicas for Deployment `myapp`.

**Answer:**

- **Imperative:** `kubectl get deploy myapp -o=jsonpath='{.status.availableReplicas}'`
- **Declarative:** N/A

---

### 5. Formatting Output

**Q1.** Print each node name on its own line.

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=jsonpath='{.items[*].metadata.name}{"\n"}'
```

- **Declarative:** N/A

---

**Q2.** Print a tab-separated table of node name and CPU capacity (one node per line).

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=jsonpath='{.items[*].metadata.name}{"\t"}{.items[*].status.capacity.cpu}{"\n"}'
```

Note: For aligned per-row output, prefer **range loops** (Section 6).

- **Declarative:** N/A

---

### 6. Range Loops

**Q1.** Print each node's name and CPU capacity on separate lines (name tab CPU).

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
```

- **Declarative:** N/A

---

**Q2.** Print Pod name and phase for every Pod in the namespace.

**Answer:**

- **Imperative:**

```bash
kubectl get pods -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

- **Declarative:** N/A

---

**Q3.** List namespace and Pod name for all Pods cluster-wide (tab-separated, one per line).

**Answer:**

- **Imperative:**

```bash
kubectl get pods -A -o=jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\n"}{end}'
```

- **Declarative:** N/A

---

### 7. Custom Columns

**Q1.** Display nodes with columns NODE, CPU, and MEMORY using custom-columns.

**Answer:**

- **Imperative:**

```bash
kubectl get nodes -o=custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory
```

- **Declarative:** N/A — custom-columns is an imperative output format flag

---

**Q2.** Show Pod NAME, NAMESPACE, STATUS, and first container IMAGE in a custom table.

**Answer:**

- **Imperative:**

```bash
kubectl get pods -o=custom-columns=NAME:.metadata.name,NAMESPACE:.metadata.namespace,STATUS:.status.phase,IMAGE:.spec.containers[0].image
```

- **Declarative:** N/A

---

**Q3.** Show Pod NAME, IP, and Ready condition status.

**Answer:**

- **Imperative:**

```bash
kubectl get pods -o=custom-columns=NAME:.metadata.name,IP:.status.podIP,READY:.status.conditions[?(@.type=="Ready")].status
```

- **Declarative:** N/A

---

### 8. Sorting

**Q1.** List Pods sorted by start time (oldest first).

**Answer:**

- **Imperative:** `kubectl get pods --sort-by=.status.startTime`
- **Declarative:** N/A — sorting is a `kubectl get` flag on table output

---

**Q2.** List nodes sorted alphabetically by name.

**Answer:**

- **Imperative:** `kubectl get nodes --sort-by=.metadata.name`
- **Declarative:** N/A

---

**Q3.** Does `--sort-by` work with `-o jsonpath`?

**Answer:**

No. `--sort-by` works with default **table** output, not JSONPath. Use custom-columns or process JSON externally if sorted JSONPath output is needed.

- **Imperative:** `kubectl get pods --sort-by=.spec.nodeName` (table output)
- **Declarative:** N/A

---

### 9. Other Output Formats

**Q1.** Match each output flag to its use case: wide, yaml, json, name, go-template.

**Answer:**

| Flag | Use |
|------|-----|
| `-o wide` | Extra columns (IP, node) |
| `-o yaml` | Full YAML manifest |
| `-o json` | Full JSON (for exploration) |
| `-o name` | `resource/name` only (good for piping to delete) |
| `-o go-template` | Go template syntax (alternative to JSONPath) |

- **Imperative:**

```bash
kubectl get pods -o wide
kubectl get pods -o yaml
kubectl get pods -o name
kubectl get nodes -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
```

- **Declarative:** `-o yaml` displays the declarative manifest of live objects

---

**Q2.** Print only resource names for all Deployments (for piping to `xargs kubectl delete`).

**Answer:**

- **Imperative:** `kubectl get deploy -o name`
- **Declarative:** N/A

---

### 10. Cheat Sheet & Resources

**Q1.** One-liner cheat sheet: explore JSON, extract all Pod names, range-loop node info, custom columns, sort Pods.

**Answer:**

- **Imperative:**

```bash
kubectl get pods -o json
kubectl get pods -o=jsonpath='{.items[*].metadata.name}'
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
kubectl get nodes -o=custom-columns=NAME:.metadata.name,CPU:.status.capacity.cpu
kubectl get pods --sort-by=.status.startTime
```

- **Declarative:** N/A

---

## Mixed Topic Questions

### Scenario 1 — Troubleshoot failing Pod

A Pod `web-7x9k2` is not Ready. Get its phase, Pod IP, first container image, and Ready condition status.

**Answer:**

```bash
kubectl get pod web-7x9k2 -o=jsonpath='{.status.phase}{"\n"}'
kubectl get pod web-7x9k2 -o=jsonpath='{.status.podIP}{"\n"}'
kubectl get pod web-7x9k2 -o=jsonpath='{.spec.containers[0].image}{"\n"}'
kubectl get pod web-7x9k2 -o=jsonpath='{.status.conditions[?(@.type=="Ready")].status}{"\n"}'
```

Or single custom-columns:

```bash
kubectl get pod web-7x9k2 -o=custom-columns=PHASE:.status.phase,IP:.status.podIP,IMAGE:.spec.containers[0].image,READY:.status.conditions[?(@.type=="Ready")].status
```

---

### Scenario 2 — Cluster inventory report

Print every node's name, Internal IP, and CPU capacity (one line per node). Then sort nodes by name in table view.

**Answer:**

```bash
kubectl get nodes -o=jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.addresses[?(@.type=="InternalIP")].address}{"\t"}{.status.capacity.cpu}{"\n"}{end}'
kubectl get nodes --sort-by=.metadata.name
```

---

### Scenario 3 — Multi-container Pod images

List all container images for every Pod in namespace `prod`.

**Answer:**

```bash
kubectl get pods -n prod -o=jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[*].image}{"\n"}{end}'
```

---

### Scenario 4 — Deployment health check

For Deployment `api`, show desired replicas, available replicas, and unavailable replicas.

**Answer:**

```bash
kubectl get deploy api -o=custom-columns=DESIRED:.spec.replicas,AVAILABLE:.status.availableReplicas,UNAVAILABLE:.status.unavailableReplicas
```

Or JSONPath:

```bash
kubectl get deploy api -o=jsonpath='desired={.spec.replicas} available={.status.availableReplicas} unavailable={.status.unavailableReplicas}{"\n"}'
```

---

### Scenario 5 — JSONPath vs custom-columns vs go-template

Print all Pod names cluster-wide. Show three equivalent approaches.

**Answer:**

```bash
# JSONPath
kubectl get pods -A -o=jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}'

# Custom columns
kubectl get pods -A -o=custom-columns=NAME:.metadata.name

# Go template
kubectl get pods -A -o go-template='{{range .items}}{{.metadata.name}}{{"\n"}}{{end}}'
```

---

### Scenario 6 — Exam workflow under time pressure

You need the namespace and name of every Pod not in `Running` phase. Build the query using the four-step workflow.

**Answer:**

```bash
# Step 1 & 2 — explore
kubectl get pods -A -o json | jq '.items[] | select(.status.phase!="Running") | .metadata.namespace + "\t" + .metadata.name'

# Step 3 & 4 — JSONPath (filtering limited; jq better for conditions)
# JSONPath alone cannot filter; get all and use range, or use jq:
kubectl get pods -A -o=jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}' | grep -v Running

# Custom columns + grep
kubectl get pods -A -o=custom-columns=NS:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase | grep -v Running
```

**Key exam tip:** JSONPath in kubectl has **no filter predicate** like `[?(@.field)]` for Pod lists in all versions — use `custom-columns` + `grep`, `jq`, or `--field-selector` where possible:

```bash
kubectl get pods -A --field-selector=status.phase!=Running -o=custom-columns=NS:.metadata.namespace,NAME:.metadata.name,PHASE:.status.phase
```
