# Cluster Maintenance

- Cluster Upgrade Process

- Operation System Upgrades

- Backup and restore methodologies



## Operation System Upgrade


tolerationSecounds: 3600

when a node goes offline, the master wait 5 min before consider the node dead

- if the node comes up after the eviction pod. it come online empty

- so, if we want to apply any update or upgrade for a node, and all it's load (pods) are part of a replicaset, and it will be online again in less than 5min, we can do the upgrade.

- but if we are not sure!, we can drain the loads fron the node
`kubectl drain node-1`
all loads levae it, and it is marked as non-schedulable (no pod can be schedule on this node)

- then when it come back online, it is still un-schedulable, so we need to make it scheduleable
`kubectl uncordon node-1`

- we can mark anode as un-schedulable but without moving the load (new pods are not scheduled on this node)
`kubectl cordon node-2`



## Kubernetes Releases

- the downloaded package, when extracted, contain all contol plan components in it, all of them of the same version 

NOTE:
- etcd cluster
- CoreDNS

has theier own versions as they are seperate projects


## Cluster Upgrade 

- control plane components can be at a diffrent version


- no component can be higher than kube-apiserver

- Contoller-manager and kube-scheduler          >> can be 1 version lower than the kube-apiserver
- Kubelet and kube-proxy                        >> can be 2 version lower than the kube-apiserver

- kubectl                                       >> can be 1 version higher or lower than the kube-apiserver

- k8s support only the latest 3 miner version
- it's recommended to upgrade 1 minor version at a time

we have 3 ways of upgrading

- Google: help us in upgrading in few clicks
- kubecadm: can help in applying upgrade  `kubeadm upgrde plan`  `kubeadm upgrade apply`

- if we manually installed everything, we have to upgrade one by one



#### Kubeadm-upgrade
`kubeadm upgrade plan`

- Kubeadm dones not install or upgrade kubelt, we need to upgrade it on each node


in order to upgrade from 1.11 to 1.13

1. upgrade the kubeadm first
`apt-get upgrade -y kubeadm=1.12.0-00`

2. `kubeadm upgrade apply v1.12.0` >> it upgrade the cluster components, once complete all controll plan conponent is upgraded to 1.12

3. if we then run `kubectl get nodes`
we will see all version at 1.11, because this shows the version of the kubelet on each node

NAME          STATUS   ROLES           AGE     VERSION
hopaserver1   Ready    control-plane   2d16h   v1.11.0
node01        Ready    <none>          2d5h    v1.11.0
node02        Ready    <none>          2d6h    v1.11.0
node03        Ready    <none>          2d6h    v1.11.0


4. upgrade the kubelet

`apt-get upgrade -y kubelet=1.12.0.-00`

5. if we then run `kubectl get nodes`
only the master node will be upgraded, but not the workers nodes

NAME          STATUS   ROLES           AGE     VERSION
hopaserver1   Ready    control-plane   2d16h   v1.12.0
node01        Ready    <none>          2d5h    v1.11.0
node02        Ready    <none>          2d6h    v1.11.0
node03        Ready    <none>          2d6h    v1.11.0


6. move the workload to other nodes, and mark an unshedulem

- upgrade the kubeadm: `apt-get upgrade -y kubeadm=1.12.0-00`
- upgrade kubelet: `apt-get upgrade -y kubelet=1.12.0.-00`
- upgrade node components using kubeadm: `kubeadm upgrade node config --kubelet-version v1.12.0`
- restart the kubelet: `systemctl restart kubelet`

- now the node is up again, but it is still un-shedulable, so we need to undo that by
`kubectl uncorn node-1`
- but pods does not come back

7.take down the sec one with same steps ...etc


----

## Backup and Restore Methods

- Declarative >> gocs >>. github


- we can also query the apiserver
`kubectl get all --all-namespaces -o yaml`
- VELERO, helps taking backups using apiserver

Backup ETCD
we can build the backup folder `/var/lib/etcd` where all data are saved

- etcd build with snapshot built it

`etcdctl snapshot save snapshot.db`

- to view snapshot status
`etcdctl snapshot status snapshot.db`

- to restore the snapshot

1. stop kube-apiserver
`systemctl stop kube-apiserver`

2. start with the new path
`etcdctl snapshot restore snapshot.db  --data-dit=/var/lib/etcd-from-backup`

3. reload deomn and etcd
`systemctl deomn-reload`
`systemctl restart etcd`

4. start apiserver
`systemctl start kube-apiserver`



Backing Up ETCD
Using etcdctl (Snapshot-based Backup)
To take a snapshot from a running etcd server, use:

ETCDCTL_API=3 etcdctl \ --endpoints=https://127.0.0.1:2379 \ --cacert=/etc/kubernetes/pki/etcd/ca.crt \ --cert=/etc/kubernetes/pki/etcd/server.crt \ --key=/etc/kubernetes/pki/etcd/server.key \ snapshot save /backup/etcd-snapshot.db

Required Options
--endpoints points to the etcd server (default: localhost:2379)
--cacert path to the CA cert
--cert path to the client cert
--key path to the client key
Using etcdutl (File-based Backup)
For offline file-level backup of the data directory:

etcdutl backup \ --data-dir /var/lib/etcd \ --backup-dir /backup/etcd-backup

This copies the etcd backend database and WAL files to the target location.

Checking Snapshot Status
You can inspect the metadata of a snapshot file using:

etcdctl snapshot status /backup/etcd-snapshot.db \ --write-out=table

This shows details like size, revision, hash, total keys, etc. It is helpful to verify snapshot integrity before restore.

Restoring ETCD
Using etcdutl
To restore a snapshot to a new data directory:

etcdutl snapshot restore /backup/etcd-snapshot.db \ --data-dir /var/lib/etcd-restored

To use a backup made with etcdutl backup, simply copy the backup contents back into /var/lib/etcd and restart etcd.

Notes
etcdctl snapshot save is used for creating .db snapshots from live etcd clusters.
etcdctl snapshot status provides metadata information about the snapshot file.
etcdutl snapshot restore is used to restore a .db snapshot file.
etcdutl backup performs a raw file-level copy of etcd’s data and WAL files without needing etcd to be running.




NOTE:

to save an etcd snapshot we have to provide all of that

```
etcdctl --endpoints=https://[127.0.0.1]:2379 \
--cacert=/etc/kubernetes/pki/etcd/ca.crt \
--cert=/etc/kubernetes/pki/etcd/server.crt \
--key=/etc/kubernetes/pki/etcd/server.key \
snapshot save /opt/snapshot-pre-boot.db

```
----
