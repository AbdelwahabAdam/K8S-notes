# Kubernetes Practice Exams

10 hands-on exams for your lab cluster. Each exam tests the **same skill areas** with different scenarios.

## Lab Environment

| VM | Role |
|----|------|
| **master** | Control plane |
| **node01** | Worker |
| **node02** | Worker |
| **node03** | Worker |

Run `kubectl` from **master**. Use namespace `exam-N` (N = exam number).

```bash
kubectl get nodes
# Expect: master, node01, node02, node03 — all Ready
```

## Skills Tested (every exam)

| # | Skill |
|---|-------|
| 1 | Pod creation |
| 2 | ReplicaSet creation |
| 3 | Node behaviour |
| 4 | Scheduler |
| 5 | Imperative vs Declarative |
| 6 | Manual scheduling |
| 7 | Labels & selectors |
| 8 | Taints & tolerations |
| 9 | Node selectors & node affinity |
| 10 | Resource requests, limits & quotas |
| 11 | DaemonSets |
| 12 | Static Pods |

## How to use

1. Read the **Task** only — do not peek at the answer.
2. Perform the task on your cluster.
3. Compare your result with the **Answer** (commands + expected output).

## Exams

| # | File |
|---|------|
| 1 | [exam-01.md](./exam-01.md) |
| 2 | [exam-02.md](./exam-02.md) |
| 3 | [exam-03.md](./exam-03.md) |
| 4 | [exam-04.md](./exam-04.md) |
| 5 | [exam-05.md](./exam-05.md) |
| 6 | [exam-06.md](./exam-06.md) |
| 7 | [exam-07.md](./exam-07.md) |
| 8 | [exam-08.md](./exam-08.md) |
| 9 | [exam-09.md](./exam-09.md) |
| 10 | [exam-10.md](./exam-10.md) |

## Cleanup (after each exam)

```bash
kubectl delete namespace exam-N
```

Remove any node labels/taints added during the exam (listed in each exam's cleanup section).
