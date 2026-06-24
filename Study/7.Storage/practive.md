# CKA Practice — Storage

> Practice questions aligned with [enhanced_readme.md](./enhanced_readme.md). Answers include **Imperative** (`kubectl`) and **Declarative** (YAML) where applicable.

---

## Topic Questions

### 1. Storage Overview

**Q1.1** What are the four core storage abstractions in Kubernetes, and who typically creates each?

<details>
<summary>Answer</summary>

| Concept | Creator | Purpose |
|---------|---------|---------|
| **PersistentVolume (PV)** | Cluster admin | Cluster-wide storage pool |
| **PersistentVolumeClaim (PVC)** | Developer / user | Request for storage |
| **StorageClass** | Cluster admin | Template for dynamic provisioning |
| **Volume (in Pod spec)** | Developer | Mount point inside a container |

**Imperative — inspect all storage resources:**

```bash
kubectl get pv,pvc,sc
```

</details>

**Q1.2** Draw the binding flow: how does a Pod end up using persistent storage?

<details>
<summary>Answer</summary>

Flow: **StorageClass** (optional) → **PV** provisioned → **PVC** binds to PV → **Pod** mounts PVC.

**Declarative — minimal binding chain:**

```yaml
# 1. StorageClass (admin)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
---
# 2. PVC (user)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
  storageClassName: fast
---
# 3. Pod (user)
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: app-data
```

</details>

---

### 2. Docker & Ephemeral Storage

**Q2.1** Why is data written inside a container's writable layer lost when the container is removed? How does Kubernetes solve this?

<details>
<summary>Answer</summary>

Container filesystem layers are ephemeral — the writable layer is destroyed with the container. Kubernetes **volumes** survive container restarts within a Pod; **PVs/PVCs** survive Pod deletion for cluster-wide persistence.

**Imperative — compare ephemeral vs persistent in a running Pod:**

```bash
kubectl exec mypod -- ls /var/www/html          # data on PVC mount
kubectl delete pod mypod --force --grace-period=0
kubectl get pvc                                  # PVC still exists
```

**Declarative — ephemeral scratch space (emptyDir):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: scratch-pod
spec:
  containers:
    - name: worker
      image: busybox
      command: ["sh", "-c", "echo hello > /cache/temp.txt && sleep 3600"]
      volumeMounts:
        - name: cache
          mountPath: /cache
  volumes:
    - name: cache
      emptyDir: {}
```

</details>

**Q2.2** Create a Pod with an `emptyDir` volume shared between two containers.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl run shared --image=nginx --dry-run=client -o yaml > pod.yaml
# Edit pod.yaml to add emptyDir volume and second container, then:
kubectl apply -f pod.yaml
```

**Declarative:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared
spec:
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c", "echo data > /shared/file.txt && sleep 3600"]
      volumeMounts:
        - name: shared-vol
          mountPath: /shared
    - name: reader
      image: busybox
      command: ["sh", "-c", "cat /shared/file.txt && sleep 3600"]
      volumeMounts:
        - name: shared-vol
          mountPath: /shared
  volumes:
    - name: shared-vol
      emptyDir: {}
```

</details>

---

### 3. Container Storage Interface (CSI)

**Q3.1** What problem does CSI solve, and what replaced legacy in-tree volume plugins?

<details>
<summary>Answer</summary>

CSI is a standard interface between orchestrators and storage vendors. It replaces deprecated in-tree plugins (e.g. `awsElasticBlockStore`, `gcePersistentDisk`) with out-of-tree CSI drivers (`ebs.csi.aws.com`, etc.).

**Imperative — list CSI drivers and StorageClasses:**

```bash
kubectl get csidrivers
kubectl get storageclass
kubectl describe sc <name> | grep -i provisioner
```

</details>

**Q3.2** Name three CSI RPC operations and what they do.

<details>
<summary>Answer</summary>

| Operation | Purpose |
|-----------|---------|
| **CreateVolume / DeleteVolume** | Provision or remove storage backend |
| **ControllerPublishVolume / ControllerUnpublishVolume** | Attach/detach volume to a node |
| **NodeStageVolume / NodePublishVolume** | Mount volume into Pod on the node |

**Declarative — Pod using generic CSI volume:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: csi-pod
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: csi-vol
          mountPath: /data
  volumes:
    - name: csi-vol
      csi:
        driver: ebs.csi.aws.com
        volumeAttributes:
          storage.kubernetes.io/csiProvisionerIdentity: ebs.csi.aws.com
        fsType: ext4
        readOnly: false
```

> In practice, use a PVC backed by a CSI StorageClass rather than inline CSI volumes.

</details>

---

### 4. PersistentVolumes (PV)

**Q4.1** Create a 2 Gi `hostPath` PV named `pv-local` with `ReadWriteOnce`, reclaim policy `Retain`, and storageClassName `manual`.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  capacity:
    storage: 2Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/data
EOF

kubectl get pv pv-local
kubectl describe pv pv-local
```

**Declarative:** Same YAML as above saved to `pv-local.yaml` and applied with `kubectl apply -f pv-local.yaml`.

</details>

**Q4.2** A PV shows status `Released`. What does this mean and how do you make it `Available` again?

<details>
<summary>Answer</summary>

`Released` means the bound PVC was deleted but reclaim policy is **Retain** — data remains, PV is not reusable until admin clears `claimRef`.

**Imperative:**

```bash
kubectl get pv
kubectl patch pv pv-local -p '{"spec":{"claimRef": null}}'
kubectl get pv pv-local   # should show Available
```

</details>

---

### 5. PersistentVolumeClaims (PVC)

**Q5.1** Create a PVC `web-claim` requesting 500 Mi, `ReadWriteOnce`, storageClassName `manual`, with selector `type: local`.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl create -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: web-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Mi
  storageClassName: manual
  selector:
    matchLabels:
      type: local
EOF

kubectl get pvc web-claim
```

**Declarative:** Save the YAML above to `web-claim.yaml` and `kubectl apply -f web-claim.yaml`.

</details>

**Q5.2** List the binding rules that must be satisfied for a PVC to bind to a PV.

<details>
<summary>Answer</summary>

1. PV capacity ≥ PVC request
2. Access modes compatible (PVC mode ⊆ PV modes)
3. `storageClassName` matches (or both empty for static binding)
4. Optional label **selector** on PVC matches PV labels

**Imperative — debug binding failure:**

```bash
kubectl describe pvc web-claim
kubectl get pv --show-labels
kubectl get events --sort-by='.lastTimestamp'
```

</details>

---

### 6. Using PVCs in Pods

**Q6.1** Create a Pod `mypod` that mounts PVC `myclaim` at `/var/www/html`.

<details>
<summary>Answer</summary>

**Imperative (generate base, then apply edited YAML):**

```bash
kubectl run mypod --image=nginx --dry-run=client -o yaml > mypod.yaml
# Add volumes and volumeMounts sections, then:
kubectl apply -f mypod.yaml
```

**Declarative:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mypod
spec:
  containers:
    - name: myfrontend
      image: nginx
      volumeMounts:
        - mountPath: /var/www/html
          name: mypd
  volumes:
    - name: mypd
      persistentVolumeClaim:
        claimName: myclaim
```

```bash
kubectl apply -f mypod.yaml
kubectl describe pod mypod | grep -A5 Mounts
```

</details>

**Q6.2** Create a Deployment `web` (2 replicas) using PVC `myclaim`. What scheduling constraint applies with `ReadWriteOnce`?

<details>
<summary>Answer</summary>

**Declarative:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx
          volumeMounts:
            - mountPath: /usr/share/nginx/html
              name: web-storage
      volumes:
        - name: web-storage
          persistentVolumeClaim:
            claimName: myclaim
```

**Constraint:** `ReadWriteOnce` volumes attach to **one node** at a time — only one Pod (or multiple Pods on the same node) can use the PVC. The second replica may stay `Pending` if scheduled on a different node.

**Imperative — verify:**

```bash
kubectl apply -f web-deploy.yaml
kubectl get pods -o wide
kubectl describe pod <pending-pod>
```

</details>

---

### 7. Access Modes & Reclaim Policies

**Q7.1** Match each access mode to its abbreviation and typical backend.

<details>
<summary>Answer</summary>

| Mode | Abbrev | Typical backend |
|------|--------|-----------------|
| ReadWriteOnce | RWO | EBS, local disk |
| ReadOnlyMany | ROX | NFS (read-only mount) |
| ReadWriteMany | RWX | NFS, CephFS, Azure Files |
| ReadWriteOncePod | RWOP | Block storage (K8s 1.22+) |

**Imperative:**

```bash
kubectl get pv -o custom-columns=NAME:.metadata.name,ACCESS:.spec.accessModes,RECLAIM:.spec.persistentVolumeReclaimPolicy
```

</details>

**Q7.2** What happens to the PV and underlying data when a PVC is deleted under each reclaim policy?

<details>
<summary>Answer</summary>

| Policy | PV | Data |
|--------|-----|------|
| **Retain** | Kept (status `Released`) | Preserved — manual cleanup |
| **Delete** | Deleted | Underlying volume deleted (dynamic default) |
| **Recycle** | Deprecated | Do not use |

**Declarative — PV with Retain:**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: retain-pv
spec:
  persistentVolumeReclaimPolicy: Retain
  # ... capacity, accessModes, etc.
```

**Imperative — delete PVC and observe:**

```bash
kubectl delete pvc myclaim
kubectl get pv    # Retain → Released; Delete → PV gone
```

</details>

---

### 8. StorageClasses & Dynamic Provisioning

**Q8.1** Create a StorageClass `fast` with provisioner `kubernetes.io/gce-pd`, parameter `type: pd-ssd`, reclaimPolicy `Delete`, `allowVolumeExpansion: true`, and `volumeBindingMode: WaitForFirstConsumer`.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
provisioner: kubernetes.io/gce-pd
parameters:
  type: pd-ssd
  replication-type: none
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
EOF

kubectl describe sc fast
```

**Declarative:** Same YAML saved to `sc-fast.yaml`.

</details>

**Q8.2** Create a PVC `dynamic-claim` (20 Gi, RWO, storageClassName `fast`) and explain static vs dynamic provisioning.

<details>
<summary>Answer</summary>

| Type | Flow |
|------|------|
| **Static** | Admin pre-creates PV → user creates matching PVC → bind |
| **Dynamic** | User creates PVC with StorageClass → provisioner creates PV automatically |

**Declarative:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dynamic-claim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: fast
```

```bash
kubectl apply -f dynamic-claim.yaml
kubectl get pvc dynamic-claim
kubectl get pv    # new PV created automatically
```

</details>

**Q8.3** Mark StorageClass `fast` as the cluster default.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl patch storageclass fast -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
kubectl get sc
```

**Declarative:**

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
# ... rest of spec
```

</details>

---

### 9. Volume Types Reference

**Q9.1** Create a Pod that mounts a ConfigMap `app-config` as a volume at `/etc/config`.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl create configmap app-config --from-literal=key1=value1
kubectl apply -f pod-with-cm.yaml
```

**Declarative:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: config-pod
spec:
  containers:
    - name: app
      image: nginx
      volumeMounts:
        - name: config
          mountPath: /etc/config
  volumes:
    - name: config
      configMap:
        name: app-config
```

</details>

**Q9.2** When would you use `hostPath` vs `nfs` vs `persistentVolumeClaim`?

<details>
<summary>Answer</summary>

| Type | Use case |
|------|----------|
| **hostPath** | Dev/test, node-local data, DaemonSets |
| **nfs** | Shared ReadWriteMany across nodes |
| **persistentVolumeClaim** | Production persistent app data (cloud block, CSI) |

**Declarative — NFS volume in Pod:**

```yaml
volumes:
  - name: nfs-vol
    nfs:
      server: 192.168.1.100
      path: /exports/data
```

</details>

---

### 10. Cheat Sheet & Resources

**Q10.1** A Pod is stuck `ContainerCreating` with a volume mount error. What commands do you run to diagnose?

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl describe pod <pod-name>
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pvc <claim-name>
kubectl describe pv <pv-name>
kubectl get pv,pvc,sc
```

Look for: PVC `Pending`, access mode mismatch, node affinity (WaitForFirstConsumer), or CSI driver errors.

</details>

**Q10.2** What are the possible PV and PVC status values?

<details>
<summary>Answer</summary>

| Resource | Statuses |
|----------|----------|
| **PV** | `Available`, `Bound`, `Released`, `Failed` |
| **PVC** | `Pending`, `Bound`, `Lost` |

**Imperative:**

```bash
kubectl get pv,pvc
```

</details>

---

## Mixed Topic Questions

### Scenario 1 — Static Provisioning End-to-End

An admin must provide 5 Gi local storage for a dev team. Create a labeled PV (`type: dev`), a matching PVC, and a Pod that writes a test file. Verify the file persists after Pod deletion.

<details>
<summary>Answer</summary>

**Declarative:**

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: dev-pv
  labels:
    type: dev
spec:
  capacity:
    storage: 5Gi
  accessModes: [ReadWriteOnce]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: manual
  hostPath:
    path: /tmp/dev-data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dev-claim
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 2Gi
  storageClassName: manual
  selector:
    matchLabels:
      type: dev
---
apiVersion: v1
kind: Pod
metadata:
  name: dev-writer
spec:
  containers:
    - name: app
      image: busybox
      command: ["sh", "-c", "echo persistent > /data/test.txt && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: dev-claim
```

**Imperative — verify persistence:**

```bash
kubectl apply -f dev-stack.yaml
kubectl exec dev-writer -- cat /data/test.txt
kubectl delete pod dev-writer
# Recreate pod with same PVC — data should still exist
kubectl run dev-reader --image=busybox --restart=Never \
  --overrides='{"spec":{"volumes":[{"name":"d","persistentVolumeClaim":{"claimName":"dev-claim"}}],"containers":[{"name":"c","image":"busybox","command":["cat","/data/test.txt"],"volumeMounts":[{"name":"d","mountPath":"/data"}]}]}}'
kubectl logs dev-reader
```

</details>

---

### Scenario 2 — PVC Binding Failure

A PVC `app-claim` stays `Pending`. The cluster has PVs but none bind. Diagnose and fix.

<details>
<summary>Answer</summary>

**Imperative — diagnose:**

```bash
kubectl describe pvc app-claim
kubectl get pv -o wide
kubectl get sc
```

Common fixes:
- **storageClassName mismatch** — patch PVC or PV to match
- **Capacity too small** — increase PV capacity or decrease PVC request
- **Access mode incompatible** — PVC requests RWX but PV is RWO
- **Selector mismatch** — remove selector or add labels to PV

**Imperative — fix storageClassName example:**

```bash
kubectl patch pvc app-claim -p '{"spec":{"storageClassName":"manual"}}'
```

**Declarative — corrected PVC:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-claim
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 1Gi
  storageClassName: manual    # must match PV
```

</details>

---

### Scenario 3 — Dynamic Provisioning with StatefulSet

Deploy a 3-replica StatefulSet `db` with per-Pod storage (1 Gi each) using StorageClass `fast` via `volumeClaimTemplates`.

<details>
<summary>Answer</summary>

**Declarative:**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels:
      app: db
  template:
    metadata:
      labels:
        app: db
    spec:
      containers:
        - name: db
          image: nginx
          volumeMounts:
            - name: data
              mountPath: /var/lib/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        storageClassName: fast
        resources:
          requests:
            storage: 1Gi
```

**Imperative:**

```bash
kubectl apply -f db-statefulset.yaml
kubectl get pvc    # data-db-0, data-db-1, data-db-2
kubectl get pv
kubectl get pods -o wide
```

</details>

---

### Scenario 4 — RWO Multi-Replica Deployment Conflict

A Deployment with 3 replicas and a single RWO PVC has 2 Pods `Pending`. Fix the architecture.

<details>
<summary>Answer</summary>

**Problem:** `ReadWriteOnce` allows one node attachment — multiple replicas on different nodes cannot share one RWO PVC.

**Solutions:**

1. **Scale to 1 replica** (if shared storage not needed):
   ```bash
   kubectl scale deployment web --replicas=1
   ```

2. **Use ReadWriteMany** storage (NFS/Azure Files):
   ```yaml
   accessModes: [ReadWriteMany]
   ```

3. **Use StatefulSet** with `volumeClaimTemplates` (one PVC per Pod).

**Declarative — StatefulSet approach (preferred for stateful apps):**

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  replicas: 3
  serviceName: web
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: nginx
          image: nginx
          volumeMounts:
            - name: www
              mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
    - metadata:
        name: www
      spec:
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 1Gi
```

</details>

---

### Scenario 5 — Expand a PVC

A PVC `app-data` (10 Gi) is running out of space. The StorageClass supports expansion. Grow it to 20 Gi.

<details>
<summary>Answer</summary>

**Prerequisites:** StorageClass must have `allowVolumeExpansion: true`.

**Imperative:**

```bash
kubectl get sc
kubectl describe sc fast | grep -i expansion
kubectl patch pvc app-data -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
kubectl get pvc app-data -w
```

**Declarative:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 20Gi    # increased from 10Gi
  storageClassName: fast
```

```bash
kubectl apply -f app-data-pvc.yaml
# May need to restart Pod or expand filesystem inside container depending on FS
kubectl exec <pod> -- df -h /mount/path
```

</details>

---

### Scenario 6 — Retain Policy Recovery

After deleting PVC `prod-claim`, the PV is `Released` but data must be preserved and rebound to a new PVC `prod-claim-v2`.

<details>
<summary>Answer</summary>

**Imperative:**

```bash
kubectl get pv
kubectl patch pv <pv-name> -p '{"spec":{"claimRef": null}}'
kubectl get pv    # status: Available
```

**Declarative — new PVC to rebind:**

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prod-claim-v2
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
  storageClassName: manual
  volumeName: <pv-name>    # explicit bind to existing PV
```

```bash
kubectl apply -f prod-claim-v2.yaml
kubectl get pv,pvc
```

</details>
