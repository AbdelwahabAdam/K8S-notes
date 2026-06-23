# JSON Path in Kubernetes

what is json path?



Using Json path in kubectl
- identify the kubectl command                      >>> kubectl get nodes
- Familiarize with JSON output                      >>> kubectl get nodes -o json
- Form the Jsin Path query                          >>> .items[0].spec.containers[0].image
- user the json path query with kubectl command     >>> kubectl get pods -o=jsonpath='{.items[0].spec.containers[0].image}'


how to pretify this: `kubectl get nodes -o=jsonpath='{.items[*].metadata.name}{.item[*].status.capacity.cpu}'`
we can add a new line

`kubectl get nodes -o=jsonpath='{.items[*].metadata.name} {"\n"} {.item[*].status.capacity.cpu}'`


## Loops- Range

`kubectl get nodes -o=jsonpath='{range .items[*]} {.metadata.name} {"\t"} {.status.capacity.cpu} {"\t"} {end}' `

we can add columns:
`kubectl get nodes -o=custom-columns=<column name>:<json path>`


`kubectl get nodes -o=custom-columns=NODE:.metadata.name,CPU:.status.capacity.cpu`


we can sort too

`kubectl get nodes --sort-by=.metadata.name`

