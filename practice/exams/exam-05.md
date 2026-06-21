# Exam 05

**Namespace:** `exam-5`

---

## Q1 — Pod creation

**Task:** Create Pod `nginx-a` and `nginx-b` in `exam-5` (image nginx). They must have different names but same label `app=nginx-pair`.

### Answer

```bash
kubectl create namespace exam-5
kubectl run nginx-a -n exam-5 --image=nginx --labels="app=nginx-pair" --restart=Never
kubectl run nginx-b -n exam-5 --image=nginx --labels="app=nginx-pair" --restart=Never
kubectl get pods -n exam-5 -l app=nginx-pair
```

**Expected:**

```
NAME      READY   STATUS    RESTARTS   AGE
nginx-a   1/1     Running   0          10s
nginx-b   1/1     Running   0          10s
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet with 0 replicas first, then scale to 3 using `kubectl scale`. Name: `zero-rs`, label `app=zero`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: zero-rs
  namespace: exam-5
spec:
  replicas: 0
  selector:
    matchLabels:
      app: zero
  template:
    metadata:
      labels:
        app: zero
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl scale rs zero-rs -n exam-5 --replicas=3
kubectl get rs,pods -n exam-5 -l app=zero
```

**Expected:**

```
NAME      DESIRED   CURRENT   READY   AGE
zero-rs   3         3         3       30s
```

---

## Q3 — Node behaviour

**Task:** Mark **node01** unschedulable, create 2 Pods, verify neither uses node01. Mark node01 schedulable again.

### Answer

```bash
kubectl cordon node01
kubectl run cordon-a -n exam-5 --image=nginx --restart=Never
kubectl run cordon-b -n exam-5 --image=nginx --restart=Never
kubectl get pods -n exam-5 -o wide | grep cordon
kubectl uncordon node01
```

**Expected:**

```
cordon-a   node02 or node03
cordon-b   node02 or node03
```

Never **node01** while cordoned.

---

## Q4 — Scheduler

**Task:** Create Pod with `nodeSelector` for a label that **no node has** (`gpu=true`). Observe Pending state. Fix by labeling node02 `gpu=true`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-want
  namespace: exam-5
spec:
  nodeSelector:
    gpu: "true"
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod gpu-want -n exam-5
kubectl describe pod gpu-want -n exam-5 | grep FailedScheduling
```

**Expected:**

```
STATUS: Pending

0/3 nodes are available: 3 node(s) didn't match Pod's node affinity/selector.
```

```bash
kubectl label nodes node02 gpu=true --overwrite
kubectl get pod gpu-want -n exam-5 -o wide
```

**Expected:** Running on **node02**.

---

## Q5 — Imperative vs Declarative

**Task:** Use `kubectl create deployment` (imperative). Export to file. Delete deployment. Recreate with `kubectl apply -f` only.

### Answer

```bash
kubectl create deployment redeploy -n exam-5 --image=nginx --replicas=2
kubectl get deployment redeploy -n exam-5 -o yaml > /tmp/redeploy.yaml
# Clean metadata (remove resourceVersion, uid, status, generation)
kubectl delete deployment redeploy -n exam-5
kubectl apply -f /tmp/redeploy.yaml
kubectl get deployment redeploy -n exam-5
```

**Expected:**

```
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
redeploy    2/2     2            2           10s
```

Declarative recreate from saved desired state.

---

## Q6 — Manual scheduling

**Task:** Write Pod YAML **without** `nodeName`. After creation, verify scheduler assigned a node. Document the node in the answer.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: auto-sched
  namespace: exam-5
spec:
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod auto-sched -n exam-5 -o jsonpath='{.spec.nodeName}'; echo
kubectl describe pod auto-sched -n exam-5 | grep "Successfully assigned"
```

**Expected:**

```
node0X

Successfully assigned exam-5/auto-sched to node0X
```

---

## Q7 — Labels & selectors

**Task:** Change ReplicaSet `zero-rs` selector to `app=zero,env=prod`. Add `env=prod` label to Pod template. Verify old Pods replaced.

### Answer

```bash
kubectl patch rs zero-rs -n exam-5 --type=strategic -p '
{
  "spec": {
    "selector": {"matchLabels": {"app": "zero", "env": "prod"}},
    "template": {"metadata": {"labels": {"app": "zero", "env": "prod"}}}
  }
}'
kubectl get pods -n exam-5 -l app=zero --show-labels
```

**Expected:** New Pods have `app=zero,env=prod`. Old Pods without `env=prod` terminated.

---

## Q8 — Taints & tolerations

**Task:** Create Pod with **Exists** toleration for key `node-role.kubernetes.io/control-plane`. Verify it **can** schedule on master.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: master-guest
  namespace: exam-5
spec:
  tolerations:
    - key: node-role.kubernetes.io/control-plane
      operator: Exists
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: [master]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod master-guest -n exam-5 -o wide
```

**Expected:**

```
NAME           NODE
master-guest   master
```

---

## Q9 — Node selectors & node affinity

**Task:** Use `matchExpressions` operator **Exists** for key `gpu` on node02. Pod must land on node02.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-exists
  namespace: exam-5
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: gpu
                operator: Exists
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod gpu-exists -n exam-5 -o wide
```

**Expected:** NODE = **node02** (only node with `gpu` label from Q4).

---

## Q10 — Resource requests, limits & quotas

**Task:** Create ResourceQuota limiting `limits.cpu: "1"`. Create Pod with `limits.cpu: 600m` — success. Create second Pod with `limits.cpu: 600m` — should fail.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: cpu-limit-quota
  namespace: exam-5
spec:
  hard:
    limits.cpu: "1"
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: cpu-a
  namespace: exam-5
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        limits:
          cpu: 600m
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: cpu-b
  namespace: exam-5
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        limits:
          cpu: 600m
EOF
```

**Expected:** `cpu-a` Running. `cpu-b` fails:

```
exceeded quota: cpu-limit-quota, requested: limits.cpu=600m
```

---

## Q11 — DaemonSets

**Task:** Create DaemonSet on **node02 only** using nodeSelector `kubernetes.io/hostname: node02`.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node02-only
  namespace: exam-5
spec:
  selector:
    matchLabels:
      app: node02-only
  template:
    metadata:
      labels:
        app: node02-only
    spec:
      nodeSelector:
        kubernetes.io/hostname: node02
      containers:
        - name: bb
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds node02-only -n exam-5
kubectl get pods -n exam-5 -l app=node02-only -o wide
```

**Expected:**

```
DESIRED   CURRENT   READY
1         1         1

NODE
node02
```

---

## Q12 — Static Pods

**Task:** Compare Pod `kube-proxy` (DaemonSet) vs `kube-apiserver-master` (static). Show owner reference difference.

### Answer

```bash
kubectl get pod -n kube-system -l k8s-app=kube-proxy -o jsonpath='{.items[0].metadata.ownerReferences[0].kind}'; echo
kubectl get pod kube-apiserver-master -n kube-system -o jsonpath='{.metadata.ownerReferences}'; echo
```

**Expected:**

```
DaemonSet

# empty (no ownerReferences for static Pod)
```

| kube-proxy | kube-apiserver-master |
|------------|----------------------|
| Owned by DaemonSet | No owner — static Pod |
| Recreated by DaemonSet controller | Recreated by kubelet |

---

## Cleanup

```bash
kubectl delete namespace exam-5
kubectl label nodes node02 gpu-
```
