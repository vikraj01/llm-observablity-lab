# Pricing and running costs

Published prices as of August 2026, plus what the Langfuse stack actually consumes on this machine.

## Pricing

Prices as published in August 2026. Check them before you commit to anything.

### LangSmith

| Plan | Price | Included traces | Seats | Self-hosting |
|---|---|---|---|---|
| Developer | **$0** then pay as you go | 5k base traces / month | 1 only | no |
| Plus | **$39 / seat / month** then pay as you go | 10k base traces / month | unlimited | no |
| Enterprise | custom | custom | custom | **yes** |

Past the included allowance you pay per trace, and retention is what drives the price:

| Trace type | Price | Retention |
|---|---|---|
| Base | **$0.50 per 1,000 traces** (0.05 cents each) | 14 days |
| Extended | **$5.00 per 1,000 traces** (0.50 cents each) | 400 days |

Extended retention is **10x** the base price. Upgrading a base trace afterwards costs 0.45 cents. Traces with feedback attached (evaluator scores, human labels) get upgraded, which is exactly what your eval runs produce. Worth knowing before you run a large experiment.

Two things gated behind Enterprise: **self-hosting** and **custom SSO**. Deployments and Sandboxes are paid on top of the plan. On the Developer plan you get 5 LCU and 1 LSU of sandbox usage a month, capped at 10 sandboxes.

### Langfuse

**Self-hosted:**

| Tier | Price | What you get |
|---|---|---|
| Open Source | **Free, MIT licence** | Everything in this document. Unlimited projects, users, traces. |
| Self-hosted Enterprise | custom | RBAC, audit logs, data masking, retention policies, SOC 2 / ISO 27001 docs, SLA |

**Cloud:**

| Plan | Price | Included units | Extra units | Retention |
|---|---|---|---|---|
| Hobby | **$0** | 50k / month | none | 30 days |
| Core | **$29 / month** | 100k / month | $8 per 100k | 90 days |
| Pro | **$199 / month** | 100k / month | $8 per 100k | 3 years |
| Enterprise | **$2,499 / month** | 100k / month | $8 per 100k | 3 years |

### The trap: units are not traces

LangSmith bills per **trace**. Langfuse bills per **unit**, which is roughly one observation (one span).

This lab's own dashboard settles it: **20 traces produced 198 observations**, so this agent averages **9.9 units per trace**.

That changes the free tiers completely:

| | Free allowance | In traces, for this agent |
|---|---|---|
| LangSmith Developer | 5k traces | **5,000 traces / month** |
| Langfuse Cloud Hobby | 50k units | **~5,050 traces / month** |
| Langfuse Cloud Core ($29) | 100k units | **~10,100 traces / month** |

The free tiers land within one percent of each other. A per-unit price that looks ten times cheaper is not, once your agent has a few tool calls in the loop. A chattier agent makes this worse.

---

## What Langfuse actually costs to run

Measured on this machine (14 cores, 15 GiB RAM) with the stack idle after the lab runs.

### Memory and CPU, per container

| Container | Memory | CPU |
|---|---|---|
| `langfuse-web` | **888.3 MiB** | 0.24% |
| `clickhouse` | **669.4 MiB** | 4.61% |
| `langfuse-worker` | **533.0 MiB** | 0.26% |
| `minio` | 78.5 MiB | 3.64% |
| `postgres` | 47.1 MiB | 0.00% |
| `redis` | 6.4 MiB | 2.06% |
| **Total** | **2.16 GiB** | ~11% of one core |

### Disk

| What | Size |
|---|---|
| Docker images (6) | **~6.0 GB** |
| Git clone | 261 MB |
| ClickHouse data + logs | 360 MB |
| Postgres data | 46 MB |
| MinIO + Redis data | < 1 MB |
| **Total after 20 traces** | **~6.7 GB** |

Note the shape of that. Almost all of it is **images, not data**. `langfuse-worker` alone is 2.07 GB and `langfuse-web` is 1.75 GB. You pay 6 GB of disk before recording a single trace.

### Measured versus recommended

Langfuse officially recommends **4 cores, 16 GiB RAM, and 100 GiB storage** (a `t3.xlarge` class VM).

The gap is large: 2.16 GiB measured against 16 GiB recommended. Both numbers are honest. The recommendation covers production ingest, where ClickHouse is absorbing continuous writes rather than sitting idle. For a lab or a small team, the real figure is closer to what is measured here.

The practical read on a 16 GiB laptop:

- Langfuse takes about **14%** of total RAM at idle
- That is fine alongside an IDE and a browser, but it is not free
- **ClickHouse is the reason this is six containers and not one binary.** It is the largest memory user, the largest disk user, and the busiest at idle. It is also what makes trace queries fast at volume.

The docs are explicit that docker compose is for trying Langfuse out, not for running it. It has **no high availability, no horizontal scaling, and no backup**. Production means Kubernetes.

### Operational friction, measured in this lab

| | LangSmith | Langfuse |
|---|---|---|
| Setup | Nothing to run | 6 containers, ~6.7 GB |
| RAM | 0 | 2.16 GiB idle, 16 GiB recommended |
| Ports claimed | none | 3000, 3030, 5432, 8123, 9000, 9090, 9091, 6379 |
| Your data | leaves your network | stays local |
| Ongoing work | none | port clashes, container health, backups are your problem |

Port `5432` is the one that actually bit. Any other local Postgres stops the whole stack from starting, and Compose aborts the entire `up` when one container fails to bind.

### When does self-hosting actually save money

The licence is free. The machine is not.

A 4 core / 16 GiB VM plus 100 GiB of storage is the floor, and at typical cloud on-demand rates that lands somewhere around **$100 to $150 a month**. That figure is an estimate from published instance pricing, not something measured here.

Compare that against Langfuse Cloud Core at **$29 a month** for 100k units, plus **$8 per additional 100k**:

```
self-hosted VM  ~= $130 / month, flat
Langfuse Cloud  =  $29 + $8 per extra 100k units
break-even      ~=  1.3 million units / month
                ~=  130,000 traces / month for this agent
```

**Below roughly 130k traces a month, self-hosting costs more, not less.** You are paying for a VM that is mostly idle.

So the reason to self-host is almost never the bill. It is that the data cannot leave your network. If that constraint is real, the cost question does not arise. If it is not real, cloud is cheaper until you are at serious volume.

One more thing the price lists do not show: **someone has to run it.** Upgrades, backups, disk filling with ClickHouse data, the 3am page when the worker dies. That is not on any pricing page and it usually costs more than the VM.

---

---

[Index](README.md) · [Tracing](01-tracing.md) · [Evaluation](02-evaluation.md) · [Features](03-features.md) · [Cost](04-cost.md) · [Scale](05-scale.md) · [Feature matrix](06-feature-matrix.md) · [Cost model](07-cost-model.md)
