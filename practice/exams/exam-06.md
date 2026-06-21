# Exam 06

**Namespace:** `exam-6`

---

## Q1 — Pod creation

**Task:** Create Pod `fail-pod` with image `nginx:definitely-not-a-real-tag-xyz`. Observe status. Fix image to `nginx` and verify recovery (delete and recreate).

### Answer

```bash
kubectl create namespace exam-6
kubectl run fail-pod -n exam-6 --image=nginx:definitely-not-a-real-tag-xyz --restart=Never
kubectl get pod fail-pod -n exam-6
kubectl describe pod fail-pod -n exam-6 | grep -A2 "Failed\|ErrImage"
```

**Expected:**

```
STATUS: ErrImagePull / ImagePullBackOff

Failed to pull image "nginx:definitely-not-a-real-tag-xyz": ...
```

```bash
kubectl delete pod fail-pod -n exam-6
kubectl run fail-pod -n exam-6 --image=nginx --restart=Never
kubectl get pod fail-pod -n exam-6
```

**Expected:**

```
fail-pod   1/1   Running   0   10s
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet `web-4` with 4 replicas. Reduce to 1 with `kubectl scale`. Confirm 3 Pods terminated.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: web-4
  namespace: exam-6
spec:
  replicas: 4
  selector:
    matchLabels:
      app: web-4
  template:
    metadata:
      labels:
        app: web-4
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl scale rs web-4 -n exam-6 --replicas=1
kubectl get rs web-4 -n exam-6
kubectl get pods -n exam-6 -l app=web-4 --no-headers | wc -l
```

**Expected:**

```
NAME    DESIRED   CURRENT   READY   AGE
web-4   1         1         1       1m

1
```

---

## Q3 — Node behaviour

**Task:** Simulate node failure understanding: stop kubelet on **node03** (or describe what happens). What status does the node get after ~40s? After ~5 min?

### Answer

**Theory answer (if you cannot stop kubelet):**

| Time | Node status | Controller action |
|------|-------------|-------------------|
| ~40s no heartbeat | **Unreachable** | Pods marked unknown |
| ~5 min still down | **Unreachable** | Pods evicted, rescheduled if part of RS/Deployment |

```bash
# If testing with kubelet stop on node03:
ssh node03 "sudo systemctl stop kubelet"
# Wait and observe:
kubectl get nodes node03
kubectl describe node node03 | grep -i condition
# Restore:
ssh node03 "sudo systemctl start kubelet"
```

**Expected after 40s:**

```
Ready   False   NodeStatusUnknown / Ready   False
```

---

## Q4 — Scheduler

**Task:** Create Deployment with 6 replicas, no affinity. Count how many Pods land on each worker node.

### Answer

```bash
kubectl create deployment spread6 -n exam-6 --image=nginx --replicas=6
kubectl get pods -n exam-6 -l app=spread6 -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort | uniq -c
```

**Expected (approximate spread):**

```
      2 node01
      2 node02
      2 node03
```

Scheduler tries to balance across nodes.

---

## Q5 — Imperative vs Declarative

**Task:** Create Pod with `kubectl run`. Generate YAML with `kubectl get -o yaml`. Apply same YAML after changing label — verify label updated.

### Answer

```bash
kubectl run edit-me -n exam-6 --image=nginx --restart=Never
kubectl get pod edit-me -n exam-6 -o yaml > /tmp/edit-me.yaml
# Edit metadata.labels: add team: dev
kubectl apply -f /tmp/edit-me.yaml
kubectl get pod edit-me -n exam-6 --show-labels
```

**Expected:**

```
LABELS
team=dev,...
```

Many Pod spec fields are immutable — labels in metadata can be patched via apply.

---

## Q6 — Manual scheduling

**Task:** Create Pod assigned to **node02** using only YAML `nodeName` field — do not use `kubectl run` or patch.

### Answer

```yaml
# Write exam-6/pin.yaml yourself, then:
```

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: yaml-pin
  namespace: exam-6
spec:
  nodeName: node02
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod yaml-pin -n exam-6 -o wide
```

**Expected:**

```
yaml-pin   1/1   Running   node02
```

---

## Q7 — Labels & selectors

**Task:** Create ReplicaSet selector `tier In [web, api]`. Create template with `tier=web`. Verify 3 replicas run. Add standalone Pod with `tier=api` — check if RS count changes.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: tier-rs
  namespace: exam-6
spec:
  replicas: 3
  selector:
    matchExpressions:
      - key: tier
        operator: In
        values: [web, api]
  template:
    metadata:
      labels:
        tier: web
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl run orphan-api -n exam-6 --image=nginx --labels="tier=api" --restart=Never
kubectl get rs tier-rs -n exam-6
```

**Expected:**

```
DESIRED 3  CURRENT 4   # RS may count orphan Pod with tier=api
```

ReplicaSet adopts matching Pods without controller owner if selector matches.

---

## Q8 — Taints & tolerations

**Task:** Taint all workers `pool=worker:NoSchedule`. Create Pod with toleration `pool=worker:NoSchedule`. Verify it schedules. Workers: node01, node02, node03.

### Answer

```bash
kubectl taint nodes node01 pool=worker:NoSchedule
kubectl taint nodes node02 pool=worker:NoSchedule
kubectl taint nodes node03 pool=worker:NoSchedule

kubectl run blocked -n exam-6 --image=nginx --restart=Never
kubectl get pod blocked -n exam-6   # stays Pending

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: allowed
  namespace: exam-6
spec:
  tolerations:
    - key: pool
      operator: Equal
      value: worker
      effect: NoSchedule
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod allowed -n exam-6 -o wide

kubectl taint nodes node01 pool=worker:NoSchedule-
kubectl taint nodes node02 pool=worker:NoSchedule-
kubectl taint nodes node03 pool=worker:NoSchedule-
```

**Expected:** `blocked` = Pending. `allowed` = Running on a worker.

---

## Q9 — Node selectors & node affinity

**Task:** Deployment `frontend` — 3 replicas, `nodeAffinity` required: `role In [frontend]`. Label node01 and node03 `role=frontend`. Verify Pods only on those nodes.

### Answer

```bash
kubectl label nodes node01 role=frontend --overwrite
kubectl label nodes node03 role=frontend --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: exam-6
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: role
                    operator: In
                    values: [frontend]
      containers:
        - name: nginx
          image: nginx
EOF

kubectl get pods -n exam-6 -l app=frontend -o wide
```

**Expected:** All Pods on **node01** and/or **node03** only — never node02.

---

## Q10 — Resource requests, limits & quotas

**Task:** Create LimitRange min `cpu: 50m`, max `cpu: 1`. Create Pod request `cpu: 25m` — fails. Fix to `cpu: 100m` — succeeds.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: cpu-range
  namespace: exam-6
spec:
  limits:
    - type: Container
      min:
        cpu: 50m
      max:
        cpu: "1"
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: too-small
  namespace: exam-6
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 25m
EOF
```

**Expected:** Pod rejected — minimum cpu is 50m.

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: ok-cpu
  namespace: exam-6
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 100m
EOF

kubectl get pod ok-cpu -n exam-6
```

**Expected:** Running.

---

## Q11 — DaemonSets

**Task:** Create DaemonSet that tolerates worker taint from Q8 (if still applied) OR create fresh DS `worker-agent` on all 3 workers.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: worker-agent
  namespace: exam-6
spec:
  selector:
    matchLabels:
      app: worker-agent
  template:
    metadata:
      labels:
        app: worker-agent
    spec:
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds worker-agent -n exam-6
```

**Expected:**

```
DESIRED   CURRENT   READY
3         3         3
```

---

## Q12 — Static Pods

**Task:** On master, count how many YAML files exist in `/etc/kubernetes/manifests/`. Match each to a running Pod in kube-system.

### Answer

```bash
ssh master "sudo ls /etc/kubernetes/manifests/"
kubectl get pods -n kube-system --field-selector spec.nodeName=master
```

**Expected:**

| Manifest | Pod |
|----------|-----|
| etcd.yaml | etcd-master |
| kube-apiserver.yaml | kube-apiserver-master |
| kube-controller-manager.yaml | kube-controller-manager-master |
| kube-scheduler.yaml | kube-scheduler-master |

4 files → 4 static control-plane Pods.

---

## Cleanup

```bash
kubectl delete namespace exam-6
kubectl label nodes node01 role-
kubectl label nodes node03 role-
```
