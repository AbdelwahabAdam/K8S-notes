# AWS (Certified Kubernetes Administrator (CKA))

## Core Concepts
### Cluster Architecture


#### Master Node
- ectd Cluster: store key-value formate data (Database)
- Kube-schaduler
- Node controller
- controll manager
- Replication controller

- kube api servers (orchastration )
- Conteriner runtime Engin (Docker, containerd, rocket)

#### Worker Node

- kubelet: lisen to kube api server, give status of nodes
- kube-proxy: make containers reach each others


----

### Docker VS containerd

- at the first, k8s supported only docker
- to support more container runtime (ex: Rocket)
- CRI (container runtime interface) >> lets us work with any contaienr runtime, but as long as they follow the OCI (open container intiative)

- Docker wasn't built to support OCI starterd
- in order for k8s to keep supporting docker, k8s interoduce Dockershim 
and that's to continue support docker outside of the CRI

- in version 1.4 >> support for docker was removed, but it keep supporting containerd

### Container-d
- it comes with builtin cli tool called: cli-ctr  (not use firendly, and used for debuging)

- nerdctl provide a docker-like cli for containerd
- nerdctl support docker-compose
- nerdctl support newest features in containerd
    - Encripted containers images
    - Lazy Pulling
    - p2p image distrbution
    - image signing and variaton
    - Namespaces in k8s

- crictl (debuging)
- interact with CRI (maintain with k8s community)
- used to inspect and debug container runtime
- work with many containers runtime


### ETCD
- What is etcd?                     >> Distibuted reliable key-value store (simple-secure-fast)
- what is a key-value store?        >> Relational DB VS Document Store VS key-value Store
- how to get started?               >> downlaod Binaries >> Extract >>  run
- how to operate etcd?          

etcd, store data about the cluster ex:
- nodes
- pods
- configs
- secrets
- accounts
- roles
- bindings
- others

ETCDCTL is the CLI tool used to interact with ETCD.ETCDCTL can interact with ETCD Server using 2 API versions – Version 2 and Version 3. By default it’s set to use Version 2. Each version has different sets of commands.

To set the right version of API set the environment variable ETCDCTL_API command

`export ETCDCTL_API=3`

------
### TO Understand more:

Master Node:
- kube-apiserver                    >>> when we run a command (kubectl), ex: `kubectl get nodes` it reachs the kube-apiserver    
                                    >>> it authenticate and validate the request  
                                    >>> fetch data from etcd cluster
                                    >>> and get back with the requested info 
                                    >>> we can send post request to the kube-apiserver without (kubectl) command line ex: 

ex: creating a pod (POST request OR `kubectl create ...`)
                                    >>> first the kube-apiserver validate and authenticate the request
                                    >>> create a new pod object without assigning it to a node 
                                    >>> then update the info in etcd 
                                    >>> update the user that the pod is created

                        Underline   >>> the kube-scheduler keep monitor the api-server, and relaise that a new pod was created and not assigned
                                    >>> the kube-scheduler idnetify which node to assign the pod, and get that info back to the kube-apiserver
                                    >>> the kube-apiserver update the info in etcd

    send info outside the master    >>> the kube-apiserver passes the info to the kubelet in the appropiate workernode 
                                    >>> the kubelet create the pod, and inform the container runtime to deploy the app image, once done
                                    >>> the kubelet update the status to the kube-apiserver
                                    >>> the kube-apiserver update the status in the etcd



- etcd                              >>> key, value database
- controller manager
- kube-scheduler


Worker Node:
- kubelet
- container Runtime engin ex: (containerd, rkt)



------
### Kube apiServer

- authenticate User
- Validate Request
- Retrieve data
- update etcd
- sheduler
- kubelet



all services related to K8s, can be installed using kube admin, but it will be running as a pod, or non-cubeadmin setup, and it will be as a service
- service :  /etc/systemd/system/kube-controller-manager.service
- pod:  /etc/kuberantes/manifests/kube-contoller-manager.yaml

------
### Kube Contoller manager

- Deployment controller
- Namespace controller
- Endpoint controller
- Conjob
- job controller
- PV protection controller
- service account controller
- statefuk set controller
- replicaset controller
- node controller
- PV binder controller
- Repliction controller

-----


- watch status
- remediate situation 

the Contoller check the status of the nodes every 5s, so if kube-apiserver stop recieving hearbeat from a node, the node is marked as unreachable (waits 40s before this mark)

- after a node is marked as unreachable, it is given 5min to get backup, if it doesn't, the contoller removes the pods assigned to that node, and provide the healthy ones if the pod is part of replicaset

- Reaplication controller >> make sure the desired number of pods are up all time, if one die, it create another one


all contoller are in a service called "Kube-contoller-manager"



kubeadmin tool deploy the kube contoller manager as a pod, same for apiserver


all services related to K8s, can be installed using kube admin, but it will be running as a pod, or non-cubeadmin setup, and it will be as a service
- service :  /etc/systemd/system/kube-controller-manager.service
- pod:  /etc/kuberantes/manifests/kube-contoller-manager.yaml


-----

#### Kube-schaduler
- desciding which pod should go to each node

how schauler decide?
- filter nodes 
- Rank Nodes (pirorty function with score)


all services related to K8s, can be installed using kube admin, but it will be running as a pod, or non-cubeadmin setup, and it will be as a service
- service :  /etc/systemd/system/kube-controller-manager.service
- pod:  /etc/kuberantes/manifests/kube-contoller-manager.yaml

------

### Kubelet

kubelet on the worker node, register it with the cluster!
when it recive a container to load a pod or container on the node,. it request the container run time and run an instance
it also monitor pods and container and inform the kube-apiserver on regurely bases

NOTE: this needs to be installed manually in all cases

-----
### Kube proxy

in every cluser, every pod can reach every other pods, and that by lunching pod network.

we create a service to expose the app thoiught the cluster.

----------
--------
### pods
### replicaset, replicacontroller
### deploment
### service

-----

### Name spaces

- kube default
- kube public
- kube system

- each has polices and resources

`kubectl get pods --namespace=dev`  >> we can also add it in the yaml under metadata

to create namespace

- kubectl create -f namepace-dev.yaml 
`
apiVersion: v1
kind: NameSpace
metadata:
    name:dev
`

- kubectl create namespace dev



to switch to another namespace

- `kubectl config set-context $(kubectl config current-context) --namespace=dev`

`kubectl get pods --all-namespace`

we can create ResourceQuota attached to a namespace

-------------------------

### Imperative vs Declarative

#### Imperative (what to do, and how to do it)
ex:

- `kubectl run --image=nginx nginx`                         >> create a pod
- `kubectl create deployment --image=nginx nginx`           >> create a deployment

- `kubectl expose deployment nginx --port 80`               >> create service for deployment, and can be `expoes pod`
- `kubectl edit deployment nginx`                           >> edit a deployment

- `kubectl scale deployment  nginx --replicas=5`            >> scale replicaset
- `kubectl set image deployment nginx nginx=nginx:1.18`     >> change image in deployment

- `kubectl create -f nginx.yaml`                            >> create object
- `kubectl replace -f  nginx.yaml`                          >> update object
- `kubectl delete -f nginx.yaml`                            >> delete object

- `kubectl api-resource `                                   >> get all api resources
- `kubectl explain pod`                                     >> get description and details
- `kubectl explain pod.spec.containers`                     >> what under contaienr and explain

>> kubectl explain ..  can be used with `--recursive`

#### Declarative (declaring the final desctination)
- teraform
- puppet
- Ansible

here we can run single apply command
`kubectl apply -f nginx.yaml`
and apply will look at the exsiting configuration and figure out what needs to be done



### how kubectl apply works!

- if the object is not exsist >> created
- convert yaml object to json formate, then compare it with the live object
- if a fields was deleted, it delete it from the live conf

we have 3 fiels

- local file
- Last applied configuration
- Live object configuration

the last applied conf is stored in annotations scetion in the live object conf, only when we use aplly (create does not do that) 

-------
-------


## Scheduling 
- manual Schdeuling
-Labels and selectors
- Resource limits
- Demonsets
- muliple Schdeulers
- Schdeuler events


### Manual Schdeuling
- we can add nodeName in the pod definition, but this can be done in creation time only.
 - by default the nodeName is empty (the Schdeuler assign a node for it)

```
apiVersion: v1
kind: Pod
metadata: 
  name: nginx
  labels:
    app: nginx
    tier: frontend
spec:
  containers:
    - name: nginx
      image: nginx
  nodeName: node02
```

if we want to bing a pod to a node in the runtime (after creation)
we can create a Binding file
```
apiVersion: v1
kind: Binding
metadata: 
  name: nginx
target:
    apiVersion: v1
    Kind: Node
    name: node02
```
then convert the yaml to the equivelant json formate, and send it to the kube-apiserver

`curl --header "" --request POST --data '{"apiVersion:"V1","kind":"Binding"....  "}' http://$server/api/v1/namespace/default/pods/$podname/binding`

- we can check the status of any kube-system service with
` kubectl get pods --namespace kube-system`


-----
### labels and selectors

- to get pod with  specifit label

`kubectl get pods --selector env=dev`


-----
## Taints and Tolerations


- we use this to give a pod the aplility to go to a certain node, and the othet cant

and that by adding a taint on the node, and add a toleation on the pod

UPDATE: it tells the Node to only accept certain pod, but it can go to other nodes


- Taints:

taint-effecf:
- NoSchadule        >>> the pod will not be schadule on the node
- PreferNoShdule    >>> the system will try not to put it on the node, but not 100%
- NoEXecute         >>> new pod will not schaduled on the node. and old will remain the same (even if they cant tolerant the taint) !!! #TODO: check if this is correct!


`kubectl taint nodes node-name key=value:taint-effect`

`kubectl taint nodes node1 app=blue:NoSchadule`


```
apiVersion: v1
kind: Pod
metadata: 
  name: myapp-pod
spec:
  containers:
    - name: nginx
      image: nginx
  tolerations:
    -key: app                           ## app=blue:NoSchadule
     operator: "Equal"
     value: blue
     effect: NoSchadule
```


to see any taints:
`kubectl descripe node kubemaster |grep taint`

to remove taints, we add -
`kubectl taint nodes controlplane node-role.kubernetes.io/control-plane:NoSchedule-`





-------
## Node Selectors
- Simple equality only.
we can add in a pod spec
```
nodeSelector:
    size: Large
```

but we need first to label the nodes

`kubectl label nodes <node-name> <label-key>=<label-value>`
`kubectl label nodes node01 size=large`
`kubectl get nodes --show-labels`

but we cant say here, assign the pod to Large or medium
or nay node that is not small, so we need #Node_Affinity

## Node Affinity
More powerful:

In
NotIn
Exists
Gt
Lt
Multiple conditions

- required During Scheduling Ignore During Execution
- required During Scheduling required During Exceution
- Preferre During Scheduling Ignore During Exceution

```
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: size
            operator: In
            values:
            - large
  containers:
  - name: nginx
    image: nginx

```

-----
#### Resource Requirments

kube-schaduler keep in account the node resources and the amount of resource requried by each pod, to assign


each pod we can sepecify CPU and MEMORY

```
apiVersion: v1
kind: Pod
metadata: 
  name: nginx
  labels:
    app: nginx
    tier: frontend

spec:
  containers:
    - name: nginx
      image: nginx
    resources:
        requests:
            memory: "4Gi"
            cpu: 2
```


1 CPU   >>> 1 AWS vCPU
        >>> 1 GCP core
        >>> 1 Azure Core
        >>> 1 Hyperthred


1 Mem   >>> 1G (gigabyte)
        >>> 1 M
        >>> 1 K  >>> 1000 byte

        >>> 1Gi (gibibyte)
        >>> 1 Mi (Mebibyte)
        >>> 1Ki (kibibyte)  >> 1024 byte


we can also set limits

```
apiVersion: v1
kind: Pod
metadata: 
  name: nginx
  labels:
    app: nginx
    tier: frontend

spec:
  containers:
    - name: nginx
      image: nginx
    resources:
        requests:
            memory: "1Gi"
            cpu: 2
        limits:
            memory: "2Gi"
            cpu: 2
```

Default Behavior:
- there is no resource request or limitation
- better is Requests and No Limits




#### LimitRange
to set default resource limit for newly created pods (CPU and MEMORY)
```
apiVersion: v1
kind: LimitRange
metadata: 
    name: cpu-resource-constrain
spec:
    limits:
        -default:
            cpu: 500m
            memory: 1Gi
        defaultRequest:
            cpu: 500m
            memory: 1Gi
        
        max:
            cpu: "1"
            memory: 1Gi
        min:
            cpu: 100m
            memory: 500MI
        type: Container
```


to set resource limitation for all pod together we create ResourceQuotas
#### Resource Quotas
Namespace level
```
apiVersion: v1
kind: ResourceQuota
metadata: 
    name: cpu-resource-quota
spec:
    hard:
        requests.cpu: 4
        requests.memory: 4Gi
        limitts.cpu: 10
        limits.memory: 10Gi
```


## NOTE:
to extract pod definition in yaml run:
`kubectl get pod webapp -o yaml > my-new-pod.yaml`


--------------
## DaemonSets

ensure is one copy of the pod exsist in all nodes
- Monitoring solution
- logs Veiwers

the kube-proxy can be run as Demonset


```
apiVersion: apps/v1
kind: DaemonSet
metadata:
  labels:
    app: elasticsearch
  name: elasticsearch
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - image: registry.k8s.io/fluentd-elasticsearch:1.20
        name: fluentd-elasticsearch
```


`kubectl get daemonset`

--------

#### static Pods

we can reconfig the kubelet to read the pods difination files without the kube-apiserver
the kubelet check this folder , and create those pods on the host
and it can ensure that the pod stay alive, and if a pod dies, kubelet restart it
and if you edit a pod file, it updates it, and if you delete the file, the kubelet delete the pod

the pods created from the kubelet called static-pods. 
kubelet can only create pods

- we can config that by passing option while running the service, the opiton is:
`--pod-manifest-path=/etc/kubernates/manifests`

another way to do that, instead of put the option in the kubelet service file, we can pass a file path from the --config function
`--config=kubeconfig.yaml`
and put inside 
`staticPodPath:  /etc/kubenates/manifests`