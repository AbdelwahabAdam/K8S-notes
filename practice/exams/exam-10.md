# Exam 10 — Final Simulation

**Namespace:** `exam-10`  
**Time:** 90 minutes — complete all 12 tasks without looking at answers first.

---

## Q1 — Pod creation

**Task:** Create Pod `final-web` in `exam-10`:
- Image `nginx:1.25`
- Labels: `app=final`, `version=v1`
- Annotation: `owner=cka-student`
- Container port 80

### Answer

```bash
kubectl create namespace exam-10

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: final-web
  namespace: exam-10
  labels:
    app: final
    version: v1
  annotations:
    owner: cka-student
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
EOF

kubectl get pod final-web -n exam-10 --show-labels
kubectl get pod final-web -n exam-10 -o jsonpath='{.metadata.annotations.owner}'; echo
```

**Expected:**

```
final-web   1/1   Running   app=final,version=v1

cka-student
```

---

## Q2 — ReplicaSet creation

**Task:** ReplicaSet `final-rs`: 4 replicas, label `app=final-rs`, nginx. Scale to 6. Then scale to 2.

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: final-rs
  namespace: exam-10
spec:
  replicas: 4
  selector:
    matchLabels:
      app: final-rs
  template:
    metadata:
      labels:
        app: final-rs
    spec:
      containers:
        - name: nginx
          image: nginx
EOF

kubectl scale rs final-rs -n exam-10 --replicas=6
kubectl scale rs final-rs -n exam-10 --replicas=2
kubectl get rs final-rs -n exam-10
```

**Expected:**

```
NAME       DESIRED   CURRENT   READY   AGE
final-rs   2         2         2       2m
```

---

## Q3 — Node behaviour

**Task:**
1. Cordon **node02**
2. Create 2 Pods — confirm none on node02
3. Uncordon node02
4. Drain **node01** with `--ignore-daemonsets`, then uncordon

### Answer

```bash
kubectl cordon node02
kubectl run nb1 -n exam-10 --image=nginx --restart=Never
kubectl run nb2 -n exam-10 --image=nginx --restart=Never
kubectl get pods nb1 nb2 -n exam-10 -o wide
kubectl uncordon node02

kubectl drain node01 --ignore-daemonsets --delete-emptydir-data
kubectl uncordon node01
kubectl get nodes
```

**Expected:**

- While node02 cordoned: nb1/nb2 on node01 or node03
- After drain/uncordon: node01 Ready, schedulable

---

## Q4 — Scheduler

**Task:** Create 3 Pods with no constraints. Document which node each landed on. Then create Pod with `requests.cpu: 250m` on each — verify scheduler still places them.

### Answer

```bash
for i in 1 2 3; do kubectl run sch-$i -n exam-10 --image=nginx --restart=Never; done
kubectl get pods -n exam-10 -o wide | grep sch-

for i in 4 5 6; do
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: sch-$i
  namespace: exam-10
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 250m
EOF
done
kubectl get pods sch-4 sch-5 sch-6 -n exam-10
```

**Expected:** All 6 Pods Running across node01–03.

---

## Q5 — Imperative vs Declarative

**Task:**
1. Imperative: `kubectl create deployment final-dep --image=nginx:1.24 --replicas=3`
2. Declarative: apply YAML changing image to `nginx:1.25` and replicas to 4
3. Verify `last-applied-configuration` on Deployment

### Answer

```bash
kubectl create deployment final-dep -n exam-10 --image=nginx:1.24 --replicas=3

cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: final-dep
  namespace: exam-10
spec:
  replicas: 4
  selector:
    matchLabels:
      app: final-dep
  template:
    metadata:
      labels:
        app: final-dep
    spec:
      containers:
        - name: nginx
          image: nginx:1.25
EOF

kubectl get deployment final-dep -n exam-10
kubectl get deployment final-dep -n exam-10 -o yaml | grep last-applied-configuration | head -1
```

**Expected:**

```
final-dep   4/4   4   4
# annotation present
```

---

## Q6 — Manual scheduling

**Task:**
- Pod `on-01` → node01 via `nodeName`
- Pod `on-02` → node02 via `nodeName`
- Pod `on-03` → node03 via `nodeName`

All in one apply command (multi-document YAML).

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: on-01
  namespace: exam-10
spec:
  nodeName: node01
  containers:
    - name: nginx
      image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: on-02
  namespace: exam-10
spec:
  nodeName: node02
  containers:
    - name: nginx
      image: nginx
---
apiVersion: v1
kind: Pod
metadata:
  name: on-03
  namespace: exam-10
spec:
  nodeName: node03
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pods on-01 on-02 on-03 -n exam-10 -o wide
```

**Expected:**

```
on-01   node01
on-02   node02
on-03   node03
```

---

## Q7 — Labels & selectors

**Task:**
1. Label nodes: node01 `env=prod`, node02 `env=staging`, node03 `env=prod`
2. List nodes with `env=prod`
3. Create Service selecting `app=final-dep` — verify endpoints

### Answer

```bash
kubectl label nodes node01 env=prod --overwrite
kubectl label nodes node02 env=staging --overwrite
kubectl label nodes node03 env=prod --overwrite
kubectl get nodes -l env=prod

kubectl expose deployment final-dep -n exam-10 --port=80 --name=final-svc
kubectl get endpoints final-svc -n exam-10
```

**Expected:**

```
node01, node03

4 endpoints (matches 4 deployment replicas)
```

---

## Q8 — Taints & tolerations

**Task:**
1. Taint node03 `dedicated=gpu:NoSchedule`
2. Pod without toleration — not on node03
3. Pod `gpu-workload` with toleration + affinity to node03 — on node03
4. Remove taint

### Answer

```bash
kubectl taint nodes node03 dedicated=gpu:NoSchedule

kubectl run plain -n exam-10 --image=nginx --restart=Never
kubectl get pod plain -n exam-10 -o wide

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: gpu-workload
  namespace: exam-10
spec:
  tolerations:
    - key: dedicated
      operator: Equal
      value: gpu
      effect: NoSchedule
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values: [node03]
  containers:
    - name: nginx
      image: nginx
EOF

kubectl get pod gpu-workload -n exam-10 -o wide
kubectl taint nodes node03 dedicated=gpu:NoSchedule-
```

**Expected:**

```
plain         node01 or node02
gpu-workload  node03
```

---

## Q9 — Node selectors & node affinity

**Task:** Deployment `prod-app`, 2 replicas:
- Required affinity: `env In [prod]`
- Must NOT run on node01 (use hostname `NotIn [node01]`)

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prod-app
  namespace: exam-10
spec:
  replicas: 2
  selector:
    matchLabels:
      app: prod-app
  template:
    metadata:
      labels:
        app: prod-app
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: env
                    operator: In
                    values: [prod]
                  - key: kubernetes.io/hostname
                    operator: NotIn
                    values: [node01]
      containers:
        - name: nginx
          image: nginx
EOF

kubectl get pods -n exam-10 -l app=prod-app -o wide
```

**Expected:** Both Pods on **node03** only (prod env, not node01).

---

## Q10 — Resource requests, limits & quotas

**Task:** Complete resource setup in `exam-10`:
- ResourceQuota: 15 pods max, `requests.cpu: 4`, `requests.memory: 4Gi`
- LimitRange: default request `cpu: 100m`, `memory: 128Mi`; max `memory: 1Gi` per container
- Pod `res-final` with requests `200m/256Mi`, limits `500m/512Mi`

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ResourceQuota
metadata:
  name: final-quota
  namespace: exam-10
spec:
  hard:
    pods: "15"
    requests.cpu: "4"
    requests.memory: 4Gi
---
apiVersion: v1
kind: LimitRange
metadata:
  name: final-lr
  namespace: exam-10
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      max:
        memory: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: res-final
  namespace: exam-10
spec:
  containers:
    - name: nginx
      image: nginx
      resources:
        requests:
          cpu: 200m
          memory: 256Mi
        limits:
          cpu: 500m
          memory: 512Mi
EOF

kubectl describe quota final-quota -n exam-10
kubectl describe pod res-final -n exam-10 | grep -A6 "Limits:"
```

**Expected:** Quota shows Used/Hard. Pod Burstable QoS with specified resources.

---

## Q11 — DaemonSets

**Task:**
- DaemonSet `prod-agent` on nodes with `env=prod` (node01, node03) — use node affinity
- Must have 2 Pods

### Answer

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: prod-agent
  namespace: exam-10
spec:
  selector:
    matchLabels:
      app: prod-agent
  template:
    metadata:
      labels:
        app: prod-agent
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: env
                    operator: In
                    values: [prod]
      containers:
        - name: agent
          image: busybox
          command: ["sleep", "3600"]
EOF

kubectl get ds prod-agent -n exam-10
kubectl get pods -n exam-10 -l app=prod-agent -o wide
```

**Expected:**

```
DESIRED 2  CURRENT 2  READY 2

node01, node03
```

---

## Q12 — Static Pods

**Task:** Final static Pod checklist:
1. List 4 control-plane static Pods on master
2. State manifest directory path
3. Explain why deleting `kube-controller-manager-master` via kubectl does not permanently remove it
4. Name which component is **not** a static Pod on workers (kube-proxy)

### Answer

```bash
kubectl get pods -n kube-system --field-selector spec.nodeName=master
ssh master "sudo ls /etc/kubernetes/manifests/"
kubectl get ds kube-proxy -n kube-system
```

**Expected:**

**1. Static Pods on master:**
```
etcd-master
kube-apiserver-master
kube-controller-manager-master
kube-scheduler-master
```

**2. Manifest path:** `/etc/kubernetes/manifests/`

**3. kubelet recreates** Pod from manifest file — delete via kubectl only removes mirror until kubelet reconciles.

**4. kube-proxy** = DaemonSet (controller-managed), not static Pod.

---

## Self-score

| Tasks passed | Level |
|--------------|-------|
| 12/12 | Ready for CKA scheduling & workloads |
| 9–11 | Review weak topics |
| < 9 | Repeat exams 1–9 |

---

## Cleanup

```bash
kubectl delete namespace exam-10
kubectl label nodes node01 env-
kubectl label nodes node02 env-
kubectl label nodes node03 env-
```
