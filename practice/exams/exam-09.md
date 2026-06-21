# Exam 09

**Namespace:** `exam-9`

---

## Q1 — Pod creation

**Task:** Create Pod `init-demo` with one container `nginx`. RestartPolicy `Never`. Verify restart count stays 0 after 1 minute.

### Answer

```bash
kubectl create namespace exam-9

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
  namespace: exam-9
spec:
  restartPolicy: Never
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod init-demo -n exam-9
```

**Expected:**

```
init-demo   1/1   Running   0   1m
```

`restartPolicy: Never` — kubelet does not restart container on exit.

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet, then **replace** entire spec changing image to `nginx:1.25` using `kubectl replace -f` (not apply).

### Answer

```bash
cat <<EOF > /tmp/rs-replace.yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: replace-rs
  namespace: exam-9
spec:
  replicas: 2
  selector:
    matchLabels:
      app: replace
  template:
    metadata:
      labels:
        app: replace
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl create -f /tmp/rs-replace.yaml
# Edit image to nginx:1.25, bump resourceVersion not needed — replace uses full object
sed -i 's|image: nginx|image: nginx:1.25|' /tmp/rs-replace.yaml
kubectl replace -f /tmp/rs-replace.yaml
kubectl get rs replace-rs -n exam-9 -o jsonpath='{.spec.template.spec.containers[0].image}'; echo
```

**Expected:**

```
nginx:1.25
```

`replace` = full object replacement (must include all required fields).

---

## Q3 — Node behaviour

**Task:** Compare `kubectl get nodes` vs `kubectl describe node node01` — list 3 conditions you should check for node health.

### Answer

```bash
kubectl describe node node01 | grep -A1 "Conditions:"
```

**Expected conditions:**

| Type | Healthy value |
|------|---------------|
| Ready | True |
| MemoryPressure | False |
| DiskPressure | False |
| PIDPressure | False |
| NetworkUnavailable | False |

---

## Q4 — Scheduler

**Task:** Create Deployment 9 replicas (no affinity). Verify roughly 3 Pods per worker node.

### Answer

```bash
kubectl create deployment nine -n exam-9 --image=nginx --replicas=9
kubectl get pods -n exam-9 -l app=nine -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort | uniq -c
```

**Expected:**

```
   3 node01
   3 node02
   3 node03
```

(Approximate — scheduler balances load.)

---

## Q5 — Imperative vs Declarative

**Task:** Write down when to use `create`, `apply`, and `replace` in a table from your own understanding after testing:
- Create new Pod with apply
- Try create again (fail)
- Delete and use create (success)

### Answer

| Command | When | Test result |
|---------|------|-------------|
| `create -f` | One-time create | Fails if exists |
| `apply -f` | Create or update (GitOps) | Idempotent |
| `replace -f` | Full object swap | Needs complete YAML |

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: cmd-test
  namespace: exam-9
spec:
  containers:
    - name: nginx
      image: nginx
EOF
kubectl create -f cmd-test.yaml 2>&1 | grep -i already
kubectl delete pod cmd-test -n exam-9
kubectl create -f cmd-test.yaml
```

**Expected:**

```
AlreadyExists  →  then after delete:  pod/cmd-test created
```

---

## Q6 — Manual scheduling

**Task:** Create Pod without nodeName. Wait until Running. Record node. Create second Pod with `nodeName` set to **same** node — both must run on that node.

### Answer

```bash
kubectl run first -n exam-9 --image=nginx --restart=Never
NODE=$(kubectl get pod first -n exam-9 -o jsonpath='{.spec.nodeName}')
echo "First pod on: $NODE"

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: second
  namespace: exam-9
spec:
  nodeName: $NODE
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pods first second -n exam-9 -o wide
```

**Expected:** Both Pods on **same node**.

---

## Q7 — Labels & selectors

**Task:** Create Service selecting `app=nine` (from Q4 Deployment). Verify endpoint count matches replica count.

### Answer

```bash
kubectl expose deployment nine -n exam-9 --port=80 --target-port=80 --name=nine-svc
kubectl get endpoints nine-svc -n exam-9
kubectl get deployment nine -n exam-9
```

**Expected:**

```
ENDPOINTS: 9 IP addresses (one per Pod)
DEPLOYMENT: 9/9 replicas
```

---

## Q8 — Taints & tolerations

**Task:** Replicate production pattern: master has control-plane taint. Create DaemonSet that runs on **all 4 nodes** including master.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: all-nodes
  namespace: exam-9
spec:
  selector:
    matchLabels:
      app: all-nodes
  template:
    metadata:
      labels:
        app: all-nodes
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: nginx
          image: nginx
EOF

kubectl get ds all-nodes -n exam-9
kubectl get pods -n exam-9 -l app=all-nodes -o custom-columns=POD:.metadata.name,NODE:.spec.nodeName
```

**Expected:**

```
DESIRED 4  CURRENT 4  READY 4

master, node01, node02, node03
```

---

## Q9 — Node selectors & node affinity

**Task:** Pod `only-workers`: affinity excluding master using `node-role.kubernetes.io/control-plane` **NotIn** `["true"]` or hostname NotIn master.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: only-workers
  namespace: exam-9
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: NotIn
                values: [master]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod only-workers -n exam-9 -o wide
```

**Expected:** NODE = node01, node02, or node03 — never master.

---

## Q10 — Resource requests, limits & quotas

**Task:** Create Pod with **Guaranteed** QoS (requests = limits for CPU and memory). Verify class.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed
  namespace: exam-9
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 250m
          memory: 256Mi
        limits:
          cpu: 250m
          memory: 256Mi
EOF

kubectl describe pod guaranteed -n exam-9 | grep "QoS Class"
```

**Expected:**

```
QoS Class:  Guaranteed
```

---

## Q11 — DaemonSets

**Task:** Compare Pod count: DaemonSet `all-nodes` (Q8) vs Deployment `nine` (Q4). Explain difference.

### Answer

```bash
kubectl get ds all-nodes -n exam-9
kubectl get deployment nine -n exam-9
```

**Expected:**

| Controller | Pods | Rule |
|------------|------|------|
| DaemonSet `all-nodes` | 4 | One per **node** (with toleration) |
| Deployment `nine` | 9 | Fixed **replica count**, scheduler places freely |

DaemonSet scales with cluster nodes; Deployment scales with `replicas` field.

---

## Q12 — Static Pods

**Task:** Create a **test static Pod** on **node01** (lab only): write manifest to node's static path, verify mirror Pod appears. Then remove it.

### Answer

```bash
ssh node01 "sudo tee /etc/kubernetes/manifests/static-nginx.yaml" <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: static-nginx
  namespace: default
spec:
  containers:
    - name: nginx
      image: nginx
EOF

sleep 30
kubectl get pods -A | grep static-nginx
```

**Expected:**

```
default   static-nginx-node01   1/1   Running   node01
```

```bash
ssh node01 "sudo rm /etc/kubernetes/manifests/static-nginx.yaml"
```

**Note:** Path may differ — check `staticPodPath` in kubelet config first. On workers it is often empty/not used.

---

## Cleanup

```bash
kubectl delete namespace exam-9
ssh node01 "sudo rm -f /etc/kubernetes/manifests/static-nginx.yaml" 2>/dev/null
```
