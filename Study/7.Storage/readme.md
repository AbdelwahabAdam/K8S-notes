# Storage 

storage types:
- Persistent volumes
- Persistent volumes claims
- Configuring Applications with persistent storage
- Access Modes for volumes
- K8s Storage Object


----------------------------

## Storage in Docker

docker build image with layers


#### Container Storage Interface

- portworx
- AWS EBS
- DELL LMC

it's a universal standerd 

#### RPC

- Create Volume
- Delete Volume
- Controller Publish Volume

---------------------------

### Volumes

- docker container are meant to not stay live long time, it should up and process data and then destoyed.
- and same thing applies for the data within the container

- to make the data presestant, we attach a volume to the app when it is created

- the data proccsed are stored in volume

- for a multi pod system, user will have to add volum in each pod, insetad we would like to deal with volums centrualy


- a persistent volume: is a cluster-wide pool of storage volumes configured by an adminsitrator to be used by users deploying applications on the cluster

To create a presistent volumes (PV)

```yaml

apiVersion: v1
kind: PersistentVolume
metadata:
    name: pv-vol1
spec:
    accessModes:
        - ReadWriteOnce
    capacity:
        storage: 1Gi
    hostPath:
        path: /tmp/data  ## Node local dir
```

AccessModes types are:

- ReadWriteOnce
- ReadOnlyMany
-ReadWriteMany



to create the PersistentVolume

`kubectl apply -f pv-definitaion.yaml`

to list all PersistentVolume
`kubectl get persistentvolume`

we can replace the hostPath with any providers ex:aws

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
    name: pv-vol1
spec:
    accessModes:
        - ReadWriteOnce
    capacity:
        storage: 1Gi
    awsElasticBlockStore:
        volumeID: <volume-id>
        fsType: ext4
```


----

### Persistent Volume Claims


- each Persistent Volume Claims and attached to single Persistent Volume

- Sufficient Capacity
- Access Modes
- Volume Modes
- Storage Class
- Selectors

smaller claim pound to large volumes if all matches


to create a Persistent Volume Claims


```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
    name: myclaim
spec:
    accessModes:
        - ReadWriteOnce
    resources:
        requests:
            storage: 500Mi
```


to create the PersistentVolume

`kubectl apply -f pvc-definitaion.yaml`

to list all PersistentVolume
`kubectl get persistentvolumeclaims`

to delete

`kubectl delete persistentvolumeclaims myclaim`

when we delete the PVC, we have options tfor the PV attached to it

- Retain:  keeps PV and it's data
- Delete: Deletes PV
- Recycle: Data is Scrubbed and PV is made avaiable for claims again


### Using PVC in Pods


Once you create a PVC use it in a POD definition file by specifying the PVC Claim name under persistentVolumeClaim section in the volumes section like this:


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
   - mountPath: "/var/www/html"
    name: mypd
 volumes:
  - name: mypd
   persistentVolumeClaim:
    claimName: myclaim
```
The same is true for ReplicaSets or Deployments. Add this to the pod template section of a Deployment on ReplicaSet.


### Storage Classes

- create PV, then PVC
- then use the PVC in pod difination as volume


- static provising
- Dynamic Provisioning >> creating SC (storage Class)


```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
    name: google-storage
    provisioner: kubernates.io/gce-pd