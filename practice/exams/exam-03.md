# Exam 03

**Namespace:** `exam-3`

---

## Q1 — Pod creation

**Task:** Create Pod `api-pod` in `exam-3` from a YAML file you write yourself (do not use `kubectl run`). Image `nginx`, label `app=api`, container port 80.

### Answer

```bash
kubectl create namespace exam-3

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: api-pod
  namespace: exam-3
  labels:
    app: api
spec:
  containers:
    - name: nginx
      image: nginx
      ports:
        - containerPort: 80
EOF

kubectl get pod api-pod -n exam-3 --show-labels
```

**Expected output:**

```
NAME      READY   STATUS    RESTARTS   AGE   LABELS
api-pod   1/1     Running   0          10s   app=api
```

---

## Q2 — ReplicaSet creation

**Task:** Create ReplicaSet `api-rs` (4 replicas, label `app=api`, nginx). Delete one Pod manually. Verify ReplicaSet recreates it.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: api-rs
  namespace: exam-3
spec:
  replicas: 4
  selector:
    matchLabels:
      app: api-rs
  template:
    metadata:
      labels:
        app: api-rs
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

POD=$(kubectl get pods -n exam-3 -l app=api-rs -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD -n exam-3
kubectl get rs api-rs -n exam-3
kubectl get pods -n exam-3 -l app=api-rs --no-headers | wc -l
```

**Expected output:**

```
NAME     DESIRED   CURRENT   READY   AGE
api-rs   4         4         4       1m

4
```

ReplicaSet controller maintains desired count.

---

## Q3 — Node behaviour

**Task:** Drain **node02** (ignore DaemonSets). Observe Pods rescheduled to other nodes. Uncordon node02.

### Answer

```bash
kubectl drain node02 --ignore-daemonsets --delete-emptydir-data
kubectl get pods -A -o wide | grep node02
kubectl uncordon node02
```

**Expected:** User Pods evicted from node02 and recreated on node01/node03. DaemonSet Pods remain (ignored).

```
node02   Ready,SchedulingDisabled   # during drain
node02   Ready                        # after uncordon
```

---

## Q4 — Scheduler

**Task:** Create Pod requesting `cpu: 8` (more than any node has). Observe scheduler failure. Then fix requests to `cpu: 100m` and confirm scheduling.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hungry
  namespace: exam-3
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: "8"
EOF

kubectl describe pod hungry -n exam-3 | grep FailedScheduling
```

**Expected:**

```
0/3 nodes are available: 3 Insufficient cpu.
```

```bash
kubectl delete pod hungry -n exam-3
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: hungry
  namespace: exam-3
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 100m
EOF

kubectl get pod hungry -n exam-3 -o wide
```

**Expected:** Pod Running on node01, node02, or node03.

---

## Q5 — Imperative vs Declarative

**Task:**
1. Create Pod `decl-pod` with `kubectl apply -f` (nginx).
2. Check for `last-applied-configuration` annotation.
3. Create Pod `imp-only` with `kubectl run` — confirm annotation is **missing**.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: decl-pod
  namespace: exam-3
spec:
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod decl-pod -n exam-3 -o yaml | grep last-applied-configuration

kubectl run imp-only -n exam-3 --image=nginx --restart=Never
kubectl get pod imp-only -n exam-3 -o yaml | grep last-applied-configuration
```

**Expected:**

- `decl-pod`: annotation **present**
- `imp-only`: **no output** (annotation absent)

`apply` stores last-applied config for three-way merge.

---

## Q6 — Manual scheduling

**Task:** Create unscheduled Pod `bind-me` (no nodeName). Use the **Binding** API to assign it to **node03**. (Patch `nodeName` is acceptable for lab practice.)

### Answer

```bash
kubectl run bind-me -n exam-3 --image=nginx --restart=Never
kubectl patch pod bind-me -n exam-3 -p '{"spec":{"nodeName":"node03"}}'
kubectl get pod bind-me -n exam-3 -o wide
```

**Expected output:**

```
NAME      NODE
bind-me   node03
```

CKA method: POST Binding JSON to `/api/v1/namespaces/exam-3/pods/bind-me/binding`.

---

## Q7 — Labels & selectors

**Task:** Add label `version=v1` to all Pods with label `app=api-rs`. List Pods matching `app=api-rs,version=v1`.

### Answer

```bash
kubectl label pods -n exam-3 -l app=api-rs version=v1
kubectl get pods -n exam-3 -l app=api-rs,version=v1
```

**Expected:** All 4 ReplicaSet Pods listed with both labels.

---

## Q8 — Taints & tolerations

**Task:**
1. Taint node03 `maintenance=true:NoExecute`.
2. Create Pod on node03 without toleration — observe eviction or avoidance.
3. Create Pod with NoExecute toleration that stays on node03.
4. Remove taint.

### Answer

```bash
kubectl taint nodes node03 maintenance=true:NoExecute

kubectl run exec-test -n exam-3 --image=nginx --restart=Never --overrides='{"spec":{"nodeName":"node03"}}'
sleep 15
kubectl get pod exec-test -n exam-3
```

**Expected:** Pod evicted or not running (NoExecute evicts without toleration).

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: exec-tol
  namespace: exam-3
spec:
  nodeName: node03
  tolerations:
    - key: maintenance
      operator: Equal
      value: "true"
      effect: NoExecute
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod exec-tol -n exam-3
kubectl taint nodes node03 maintenance=true:NoExecute-
```

**Expected:** `exec-tol` stays **Running**.

---

## Q9 — Node selectors & node affinity

**Task:** Label node01 `disk=hdd`, node02 `disk=ssd`. Create Deployment `db` (2 replicas) with **required** affinity: `disk In [ssd]`.

### Answer

```bash
kubectl label nodes node01 disk=hdd --overwrite
kubectl label nodes node02 disk=ssd --overwrite

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: db
  namespace: exam-3
spec:
  replicas: 2
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: disk
                    operator: In
                    values: [ssd]
      containers:
        - name: nginx
          image: nginx
EOF

kubectl get pods -n exam-3 -l app=db -o wide
```

**Expected:** Both Pods on **node02** only.

---

## Q10 — Resource requests, limits & quotas

**Task:** Create ResourceQuota: max 6 pods, max 1Gi memory requests. Create 3 Pods each requesting `256Mi` memory. Show quota usage.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-quota
  namespace: exam-3
spec:
  hard:
    pods: "6"
    requests.memory: 1Gi
EOF

for i in 1 2 3; do
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: mem-$i
  namespace: exam-3
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          memory: 256Mi
EOF
done

kubectl describe quota mem-quota -n exam-3
```

**Expected:**

```
requests.memory   768Mi   1Gi
pods              3+      6
```

---

## Q11 — DaemonSets

**Task:** Create DaemonSet `fluentd` in `exam-3`. Then add toleration for control-plane taint and a second DaemonSet `master-agent` that runs on **all 4 nodes** including master.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: exam-3
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
        - name: fluentd
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds fluentd -n exam-3
```

**Expected:** DESIRED = 3 (workers only).

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: master-agent
  namespace: exam-3
spec:
  selector:
    matchLabels:
      app: master-agent
  template:
    metadata:
      labels:
        app: master-agent
    spec:
      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds master-agent -n exam-3
kubectl get pods -n exam-3 -l app=master-agent -o wide
```

**Expected:** DESIRED = 4 (master + node01 + node02 + node03).

---

## Q12 — Static Pods

**Task:** SSH to **master**. Find the kubelet flag or config for static Pod path. Confirm editing a manifest file would change the static Pod (describe only — do not edit).

### Answer

```bash
ssh master "sudo cat /var/lib/kubelet/config.yaml | grep staticPodPath"
# OR
ssh master "ps aux | grep kubelet | grep -o 'config=[^ ]*'"
```

**Expected:**

```
staticPodPath: /etc/kubernetes/manifests
```

kubelet watches this directory — add/remove YAML → Pod created/deleted locally.

---

## Cleanup

```bash
kubectl delete namespace exam-3
kubectl label nodes node01 disk-
kubectl label nodes node02 disk-
```
