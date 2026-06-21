# Exam 04

**Namespace:** `exam-4`

---

## Q1 — Pod creation

**Task:** Create Pod `sleepy` in `exam-4` with image `busybox`, command `sleep 7200`, label `job=batch`. Verify it stays Running.

### Answer

```bash
kubectl create namespace exam-4

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sleepy
  namespace: exam-4
  labels:
    job: batch
spec:
  containers:
    - name: busybox
      image: busybox
      command: ["sleep", "7200"]
EOF

kubectl get pod sleepy -n exam-4
```

**Expected:**

```
NAME     READY   STATUS    RESTARTS   AGE
sleepy   1/1     Running   0          10s
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet `batch-rs` with selector `matchExpressions: job In [batch]`. Template label `job=batch`, 2 replicas, image `busybox`, command `sleep 3600`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: batch-rs
  namespace: exam-4
spec:
  replicas: 2
  selector:
    matchExpressions:
      - key: job
        operator: In
        values: [batch]
  template:
    metadata:
      labels:
        job: batch
        rs: batch-rs
    spec:
      containers:
        - name: busybox
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get rs batch-rs -n exam-4
kubectl get pods -n exam-4 -l rs=batch-rs
```

**Expected:**

```
NAME       DESIRED   CURRENT   READY   AGE
batch-rs   2         2         2       15s
```

---

## Q3 — Node behaviour

**Task:** Show allocatable CPU and memory on **node01**. Compare with Capacity. Explain the difference.

### Answer

```bash
kubectl describe node node01 | grep -A8 "Capacity:\|Allocatable:"
```

**Expected:**

```
Capacity:
  cpu:                2
  memory:             4Gi
Allocatable:
  cpu:                1900m    # less than capacity
  memory:             3.8Gi    # system reserved
```

**Explanation:** kubelet reserves resources for system daemons — scheduler uses **Allocatable**, not Capacity.

---

## Q4 — Scheduler

**Task:** Label node01 `priority=high`. Create Pod with **preferred** node affinity for `priority=high` (weight 100). Note which node it lands on.

### Answer

```bash
kubectl label nodes node01 priority=high --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pref-high
  namespace: exam-4
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: priority
                operator: In
                values: [high]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod pref-high -n exam-4 -o wide
```

**Expected:** Likely **node01** (soft preference — not guaranteed if node01 full).

---

## Q5 — Imperative vs Declarative

**Task:** Create ReplicaSet YAML with 2 replicas. Apply it. Change replicas to 5 in YAML and apply again. Then try `kubectl replace` after deleting a field — note behaviour.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: scale-rs
  namespace: exam-4
spec:
  replicas: 2
  selector:
    matchLabels:
      app: scale
  template:
    metadata:
      labels:
        app: scale
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

# Edit replicas to 5, then:
kubectl apply -f scale-rs.yaml   # or re-apply heredoc with replicas: 5
kubectl get rs scale-rs -n exam-4
```

**Expected:**

```
NAME       DESIRED   CURRENT   READY
scale-rs   5         5         5
```

`apply` patches in place. `replace` requires complete object definition.

---

## Q6 — Manual scheduling

**Task:** Create 3 Pods pinned to **node01**, **node02**, **node03** respectively using `nodeName`. Verify each lands on the correct node.

### Answer

```bash
for NODE in node01 node02 node03; do
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: pin-$NODE
  namespace: exam-4
spec:
  nodeName: $NODE
  containers:
    - name: nginx
      image: nginx
EOF
done

kubectl get pods -n exam-4 -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName | grep pin-
```

**Expected:**

```
pin-node01   node01
pin-node02   node02
pin-node03   node03
```

---

## Q7 — Labels & selectors

**Task:** Remove label `job` from Pod `sleepy`. Verify ReplicaSet `batch-rs` does **not** adopt it (still 2 replicas). Re-add label and observe.

### Answer

```bash
kubectl label pod sleepy -n exam-4 job-
kubectl get rs batch-rs -n exam-4
kubectl label pod sleepy -n exam-4 job=batch
kubectl get rs batch-rs -n exam-4
```

**Expected:** ReplicaSet stays at 2 — it only manages Pods with `job=batch` **and** created by its template. `sleepy` is independent unless labels match and RS adopts orphans (only if selector matches and no owner).

---

## Q8 — Taints & tolerations

**Task:** Apply `PreferNoSchedule` taint `env=staging` on node02. Create 6 Pods — observe most avoid node02 but scheduling still possible.

### Answer

```bash
kubectl taint nodes node02 env=staging:PreferNoSchedule

for i in $(seq 1 6); do
  kubectl run pref-$i -n exam-4 --image=nginx --restart=Never
done
kubectl get pods -n exam-4 -o wide | grep pref-
kubectl taint nodes node02 env=staging:PreferNoSchedule-
```

**Expected:** Most Pods on node01/node03; 1–2 may land on node02 if scheduler has no better option.

---

## Q9 — Node selectors & node affinity

**Task:** Create Pod that must run on node01 **OR** node02 but **not** node03. Use `nodeAffinity` with `hostname In [node01, node02]`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: no-node03
  namespace: exam-4
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: [node01, node02]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod no-node03 -n exam-4 -o wide
```

**Expected:** NODE = **node01** or **node02**, never node03.

---

## Q10 — Resource requests, limits & quotas

**Task:** Create Pod with `requests.cpu=500m`, `limits.cpu=500m`, same for memory `512Mi` — identify QoS class. Create second Pod with no resources — identify its QoS class.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: guaranteed-pod
  namespace: exam-4
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 500m
          memory: 512Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF

kubectl run best-effort -n exam-4 --image=nginx --restart=Never
kubectl describe pod guaranteed-pod -n exam-4 | grep "QoS Class"
kubectl describe pod best-effort -n exam-4 | grep "QoS Class"
```

**Expected:**

```
QoS Class:  Guaranteed
QoS Class:  BestEffort
```

---

## Q11 — DaemonSets

**Task:** Delete one DaemonSet Pod manually (from exam-3 if exists, or create new DS). Confirm DaemonSet recreates it on the same node.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: watch-ds
  namespace: exam-4
spec:
  selector:
    matchLabels:
      app: watch-ds
  template:
    metadata:
      labels:
        app: watch-ds
    spec:
      containers:
        - name: bb
          image: busybox
          command: ["sleep", "3600"]
EOF

POD=$(kubectl get pods -n exam-4 -l app=watch-ds --field-selector spec.nodeName=node01 -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD -n exam-4
kubectl get pods -n exam-4 -l app=watch-ds --field-selector spec.nodeName=node01
```

**Expected:** New Pod recreated on **node01** with different suffix name.

---

## Q12 — Static Pods

**Task:** List mirror Pods for kube-scheduler on master. What happens if you delete `kube-scheduler-master` with kubectl?

### Answer

```bash
kubectl get pod kube-scheduler-master -n kube-system
kubectl delete pod kube-scheduler-master -n kube-system
sleep 10
kubectl get pod kube-scheduler-master -n kube-system
```

**Expected:** Pod is **recreated** by kubelet (static manifest still exists).

```
kube-scheduler-master   1/1   Running   0   10s   # new instance
```

Deleting mirror Pod does not remove manifest — kubelet recreates it.

---

## Cleanup

```bash
kubectl delete namespace exam-4
kubectl label nodes node01 priority-
```
