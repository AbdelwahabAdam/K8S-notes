# Logging 

## monitoring Cluster Components

k8s does not come with full features built in monitoring 
we have other opensource solutions:
- Metric Server
- Prometheus
- Elastic Stack
- Datdog
- Dynatrace


### Heapster VS Metric Server


Heapster >> deprecated 
> converted to Metric Server (only 1/cluster)
> in memory metric solution (not in the disk, and cant get history)

kubelt contain >> Cadvisor, that is responsible for retreving performance metrics, and make them aviable for the metrics server

viewing metrics:


- to deploy metric server:

` kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`

- to check:
    `kubectl get pods -n kube-system | grep metrics-server`



`kubectl top node`

`kubectl top pode`

------

## Managing Application Logs

- to view log
`kubectl logs  ecf`

- to view live logs
`kubectl logs -f ecf`


- if more than 1 container in a pod,we have to specify

 `kubectl logs -f ecf ,container-name> `










------

## Monitoring Applications

## Monitoring Cluster Component Logs

## Application Logs