## Designing a Kubernetes Cluster

- Purpose
1. Education
2. Development & testing
3. Hosting Production Application


- Cloud or on-Prem



- Workloads
1. How Many?
2. What kind?
    1. Web
    2. Big Data/Analytics
3. Application Resources Requirments
    1. CPU intensive
    2. Memory Intensive
4. Traffic
    1. Heavy Traffic
    2. Burset Traffic
-----

## Purpose:

Education:
- MiniKube
- Single-node Cluster with kubeadm/GCP/AWS

Development & testing
- Multi-node cluster with a single master and multiple workers
- Set up using kubeadm tool or quick provision on GCP ir AWS or AKS


Hosting Production Application
- HIGH-Availability multi-node cluster with multiple master nodes
- kubeadm or GCP or kops on AWS
- up to 5000 nodes
- up to 150k pods in the cluster
- up to 300k containers
- up to 100 pods/nodes

---------

Storage:


--------

## Choosing Kubernetes Infrastructure


- miniKube          >> Deploy vms                   >> single Node Cluster
- kubeadm           >> Requires VMs to be ready     >> single/multi Node Cluster


on prodcution we have two ways:

### Turnkey solutions
- you provision VMs
- You Configure VMs
- You use scripts to deploy cluster
- You maintain VMs yourself
EX: Kubernates on AWS using KOPS



### Hosted Solutions (Managed Solutions)
- Kubernates as a service
- Provider Provisions VMs
- Provider install Kubernates
- Provider maintain VMs
EX: Google Container Engin (GKE)



### Turnkey solutions Examples
- OpenShift (built on top of Kubernates)
- Cloud Foundry Container RunTime
- VMWARE Cloup PKS
- Vagrant

### Hosted Solutions examples
- Google Kubernates Engin (GKE)
- OpenShift Online
- Azure Kubernates Service
- Amazon Elastic Container service for kubernates (EKS)


------

## Configuring High Availability

redendancy over all components

loadbalancer >> Master1 , Master2 (kube-apiserver)

for controll-managger and scheduler

> kube-controller-manager --leader-elect true --leader-elect-lease-duration 15s --leader-elect-renew-duration=10s --leader-elect-retry-pertiod 2s

for etcd, 
1. stacked topology  >> where etcd on the master nodes
2. External  etcd Topology      >> run etcd on seperate server

for poth tepologies, we must make kube-apiserver point to the etcd servers
cat /etc/systemd/system/kube-apiserver.service

`--etcd-servers=https://10.240.0.10:2379,https://10.240.0.11:2379`


-----------
## ETCD in HA

same consistent time of the data, avialable on all at any time

for multi instanaces, they elect a leader and the other are follower, only the leader handle the writes, and make sure the followers has a copy of it

- RAFT protocal (Leader Election)


write is complete only when a copy is on the others (majiroty of the nodes) >> Quorun=N/2+1

Quorun >> least number of nodes for the cluster to work properly

it is recommended to select ODD number >> network segmentation >> 5 better than 6

-------------------
-----------------

# Install kubernates the kubeadm way

## Deployment With kubeadm - Introduction
steps:

- multiple systems or vms for the clusters
- set 1 node as master and others as workers
- instsall containrd on all nodes
- install kubeadm tool on all nodes
- initalize the master server (all component installed on it)
- POD network
- Join worker Nodes



