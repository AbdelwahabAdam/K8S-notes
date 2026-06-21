# Exam 07

**Namespace:** `exam-7`

---

## Q1 — Pod creation

**Task:** Create Pod `probe-pod` (nginx) in `exam-7`. Add annotation `description=exam-7-test`. Verify annotation exists.

### Answer

```bash
kubectl create namespace exam-7

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: probe-pod
  namespace: exam-7
  annotations:
    description: exam-7-test
  labels:
    app: probe
spec:
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod probe-pod -n exam-7 -o jsonpath='{.metadata.annotations.description}'; echo
```

**Expected:**

```
exam-7-test
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet `ha-rs` with 3 replicas for high availability. Kill the node (simulate) by deleting **all** its Pods via label — verify RS recreates them on other nodes.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: ha-rs
  namespace: exam-7
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ha
  template:
    metadata:
      labels:
        app: ha
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl delete pods -n exam-7 -l app=ha --grace-period=0 --force 2>/dev/null || \
  kubectl delete pods -n exam-7 -l app=ha
sleep 15
kubectl get rs ha-rs -n exam-7
kubectl get pods -n exam-7 -l app=ha -o wide
```

**Expected:**

```
DESIRED 3  CURRENT 3  READY 3
```

3 new Pods Running (possibly on different nodes than before).

---

## Q3 — Node behaviour

**Task:** Show all labels on **node02**. Add custom label `rack=a1`. Verify with `--show-labels`.

### Answer

```bash
kubectl label nodes node02 rack=a1 --overwrite
kubectl get node node02 --show-labels
```

**Expected:**

```
NAME     STATUS   ROLES    AGE   VERSION   LABELS
node02   Ready    <none>   ...   v1.xx.x   ...,rack=a1,...
```

---

## Q4 — Scheduler

**Task:** Create 2 Pods with anti-affinity: second Pod should prefer **not** same node as first (use hostname NotIn after first Pod is scheduled — or create 2 Pods with podAntiAffinity).

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: anti-1
  namespace: exam-7
  labels:
    app: anti
spec:
  containers:
    - name: nginx
      image: nginx
EOF

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: anti-2
  namespace: exam-7
  labels:
    app: anti
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchLabels:
              app: anti
          topologyKey: kubernetes.io/hostname
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pods anti-1 anti-2 -n exam-7 -o wide
```

**Expected:** `anti-1` and `anti-2` on **different nodes**.

---

## Q5 — Imperative vs Declarative

**Task:** Demonstrate `kubectl replace --force` vs `kubectl apply` on a ReplicaSet (change replica count in file from 2 to 3).

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: rep-rs
  namespace: exam-7
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rep
  template:
    metadata:
      labels:
        app: rep
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

# Change replicas to 3 in YAML, then:
kubectl apply -f rep-rs.yaml
kubectl get rs rep-rs -n exam-7
```

**Expected:**

```
DESIRED 3  CURRENT 3  READY 3
```

`apply` = patch. `replace --force` = delete and recreate resource.

---

## Q6 — Manual scheduling

**Task:** Create 3 Pods in one YAML file (multi-document `---`), each pinned to node01, node02, node03.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: m-node01
  namespace: exam-7
spec:
  nodeName: node01
  containers:
    - name: nginx
      image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: m-node02
  namespace: exam-7
spec:
  nodeName: node02
  containers:
    - name: nginx
      image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: m-node03
  namespace: exam-7
spec:
  nodeName: node03
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pods -n exam-7 | grep m-node
```

**Expected:**

```
m-node01   Running   node01
m-node02   Running   node02
m-node03   Running   node03
```

---

## Q7 — Labels & selectors

**Task:** Remove label `app` from Pod `probe-pod`. Add it back. Use `kubectl label ... --overwrite`.

### Answer

```bash
kubectl label pod probe-pod -n exam-7 app-
kubectl get pod probe-pod -n exam-7 --show-labels
kubectl label pod probe-pod -n exam-7 app=probe --overwrite
kubectl get pod probe-pod -n exam-7 --show-labels
```

**Expected:**

```
# After remove: no app label
# After add: app=probe
```

Trailing `-` removes label.

---

## Q8 — Taints & tolerations

**Task:** Document three taint effects. Demonstrate **NoSchedule** on node01 with taint `type=cache:NoSchedule`.

### Answer

| Effect | Behaviour |
|--------|-----------|
| NoSchedule | New Pods without toleration not scheduled |
| PreferNoSchedule | Scheduler tries to avoid |
| NoExecute | Evicts existing Pods without toleration |

```bash
kubectl taint nodes node01 type=cache:NoSchedule
kubectl run cache-test -n exam-7 --image=nginx --restart=Never
kubectl get pod cache-test -n exam-7 -o wide
kubectl taint nodes node01 type=cache:NoSchedule-
```

**Expected:** `cache-test` NOT on node01.

---

## Q9 — Node selectors & node affinity

**Task:** Pod with **both** `nodeSelector: rack=a1` AND nodeAffinity `kubernetes.io/hostname In [node02]`. Where does it schedule?

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: both-rules
  namespace: exam-7
spec:
  nodeSelector:
    rack: a1
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: [node02]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod both-rules -n exam-7 -o wide
```

**Expected:**

```
both-rules   node02   Running
```

Both constraints must match — only node02 has `rack=a1` (from Q3).

---

## Q10 — Resource requests, limits & quotas

**Task:** Create ResourceQuota + LimitRange together. Quota: max 5 pods. LimitRange: default request 100m CPU. Create 5 small Pods — all succeed. Create 6th — fails.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: five-pods
  namespace: exam-7
spec:
  hard:
    pods: "5"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-cpu
  namespace: exam-7
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
EOF

for i in 1 2 3 4 5; do
  kubectl run qpod-$i -n exam-7 --image=nginx --restart=Never
done
kubectl run qpod-6 -n exam-7 --image=nginx --restart=Never 2>&1 | tail -1
```

**Expected:**

```
exceeded quota: five-pods, requested: pods=1, used: 5, limited: pods=5
```

---

## Q11 — DaemonSets

**Task:** Update DaemonSet image (busybox → nginx) and observe rolling update on all nodes.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: rolling-ds
  namespace: exam-7
spec:
  selector:
    matchLabels:
      app: rolling-ds
  template:
    metadata:
      labels:
        app: rolling-ds
    spec:
      containers:
        - name: c
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl set image ds/rolling-ds -n exam-7 c=nginx
kubectl rollout status ds/rolling-ds -n exam-7
kubectl get pods -n exam-7 -l app=rolling-ds -o jsonpath='{range .items[*]}{.spec.containers[0].image}{"\n"}{end}' | sort -u
```

**Expected:**

```
nginx
```

All 3 worker Pods updated to nginx image.

---

## Q12 — Static Pods

**Task:** What file on master controls kube-scheduler static Pod? What happens if you rename that file to `.bak`? (Describe — do not do on real cluster unless lab.)

### Answer

**File:** `/etc/kubernetes/manifests/kube-scheduler.yaml`

**If renamed to `.bak`:**

1. kubelet stops watching that manifest
2. Static Pod `kube-scheduler-master` terminated
3. **No new Pods scheduled** (scheduler down)
4. Existing Pods keep running
5. Restore file → kubelet recreates scheduler Pod

```bash
# Verify path only:
ssh master "sudo ls /etc/kubernetes/manifests/kube-scheduler.yaml"
```

---

## Cleanup

```bash
kubectl delete namespace exam-7
kubectl label nodes node02 rack-
```
