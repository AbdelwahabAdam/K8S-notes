# Kubernates K8s

- Built with google.

- Containers: Docker

- Container Orchestration

### Kubernates Architecture

- Nodes: Node is a machie physical or virtual machine, which Kubernates is installed on, 
a node is woker node, that is where containers will be launched by kubernates

- Cluster: set of nodes set together
 > share loads
 > if one down, the application is not down

- Master: a Node with Kubernates insatlled in, and is configured as a master\
watches over the nodes in cluster and do the Orchestration



### Components:

- API server
- etcd          : key-value store (store info for nodes and clusters and logs > make sure no conflicts)
- Sheduler: distubute work to nodes

- Controller: Brain behind Orchestration, notice of a node or cluster goes down
make decision to run new containers in such cases

- Container Runtime: software to run containers >> containerd (defualt)


- Kubelet: agent that runs on each node in the cluster, make sure that nodes run on container with no problems


-----


#### Master VS Worker Nodes

- Workder nodes :  Kublete  >>>> Containerd (container runtime)

- Master: Kube-apiServer >> etcd >> contoller >> scheduler


#### Kubectl

- kubectl run hellp-minikube   >>> deploy app on cluster

- kubectl cluster-info          >> view info about cluster

- kubectl get nodes             >> list all nodes on cluster

--------

### Diffrence between Docker VS Containerd

CRI: container Runtime interface >> OCI (open container initiative) >> image spec, runtime spec

- dockershim

### Diffrence between CLI tools (ctr, nerdctl, crictl)

- ctr: comes with containerd  <> not user freiendly <> Supports limited features only   **(only for debuging)**

- nerdctl: just like docker cli **(general purpose)**

- crictl: work with diffrent container runtime interface  **(only for debuging)**



- crictl

- crictl pull bustbox

- crictl images

- crictl ps -a

- crictl exec -i -t <container_id> ls

- crictl logs <container_id>

- crictl pods

|           | ctr   | nerdctl   | crictl|
|-----------|-----------|-----------|-----------|
|Purpose    |Debugging|General Purpose|Debugging|
|Community    |ContainerD|ContainerD|Kubernates|
|Works with    |ContainerD|ContainerD|All CRI-compatible Runtimes|


------


#### What is minikube?


#### what is pods?
- pod: is a single instatnce of an app
- a single bod can have multiple containers

#### what is cluster



-----


`kubectl run nginx --image nginx` >> deploy a pod from nginx container

`kubectl get pods`  >> list all pods

-----

In order to create a POD, we dont do that manually, we Create a Deployment, and then create a POD inside.
Deployment manages the POD, and offers:
- self healing
- Scaling
- Rolling Updates (No downtime)
- Rollback

-------


### Creating PODS with YAML


- apiVersion:
- kind:
    pod >>  v1
    service >> v1
    ReplicaSet >> app/v1
    Deployment >> app/v1

- metadata:


spec:


-----

To create a Pod, we can do it in 3 ways:

- kubectl run nginx --image=nginx
- kubectl apply -f nginx.yaml
- kubectl create -f nginx.yaml


>> The second and third commands create a Pod only if nginx.yaml defines a Pod resource.

### Important Pod commands:

- kubectl get pods

- kubectl descibe pod <pod_name>

- kubectl apply -f nginx.yaml


- kubectl delete pod nginx-2

-----


#### Replication Controller  VS replicSet