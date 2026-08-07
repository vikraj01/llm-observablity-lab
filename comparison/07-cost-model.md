# Cost model: LangSmith vs Langfuse

A worked cost comparison for a real workload, with every line itemised and every
assumption stated.

**Headline finding: at this volume you are not buying traces, you are buying seats.**
Trace ingestion costs between $0 and $1.50 a month. Everything else on the bill is
per-user pricing.

---

## What you are actually paying for

The two vendors meter completely different things, which is why a naive price
comparison misleads.

### LangSmith bills on five dimensions

| Dimension | Rate | Notes |
|---|---|---|
| **Seats** | **$39 / seat / month** (Plus) | Developer is free but capped at **1 seat** |
| **Base traces** | $0.50 per 1,000 | 14-day retention. 5k included on Developer, 10k on Plus |
| **Extended traces** | $5.00 per 1,000 | 400-day retention, **10x the base rate** |
| **Engine** | **$1.50 per LCU** | LangChain Compute Unit. Consumption not published |
| **Insights** | ~$1 to $2 per 1,000 threads | OpenAI models. $3 to $4 with Anthropic |

Deployments, Sandboxes and Fleet are also metered in LCU and LSU ($1.00 per LangChain
Storage Unit), but they are not part of an observability decision.

### Langfuse bills on one dimension

| Dimension | Rate |
|---|---|
| **Units** (roughly one span) | Graduated: **$8** per 100k up to 1M, then **$7**, then **$6.50**, then **$6** |
| **Seats** | **Unlimited on every paid plan.** Hobby is capped at 2 users |

Plan floors: Hobby $0 (50k units, 30-day retention), Core $29 (100k units, 90 days),
Pro $199 (100k units, 3-year retention), Enterprise $2,499.

### The unit conversion that matters

Langfuse units are not traces. This lab measured it directly: **20 traces produced 198
observations**, so this agent averages **9.9 units per trace**. Every Langfuse figure
below uses that multiplier. An agent with more tool calls will be worse; a single-shot
completion will be better.

---

## The scenario

**300 to 400 traces per day**, which is 9,000 to 12,000 traces per month, from a team
of engineers who all need access to the tool.

| | 300/day | 400/day |
|---|---|---|
| Traces per month | 9,000 | 12,000 |
| Langfuse units per month | 89,100 | 118,800 |
| Storage growth, self-hosted | 65 MB/month | 87 MB/month |

Note the storage line. At this volume, disk is irrelevant. The 100 GB Langfuse
recommends would last decades.

---

## Cost build-up at 400 traces/day

### LangSmith

Trace cost is effectively zero. 12,000 traces against a 10,000 allowance leaves 2,000
billable at $0.50 per thousand, so **$1.00 a month**.

| Team size | Seats | Traces | **Total** | Seats as % of bill |
|---|---|---|---|---|
| 1 engineer | $39 | $1.00 | **$40** | 98% |
| 3 engineers | $117 | $1.00 | **$118** | 99% |
| 5 engineers | $195 | $1.00 | **$196** | 99.5% |
| 10 engineers | $390 | $1.00 | **$391** | 99.7% |

Add the optional intelligence features:

| Feature | Cost at this volume |
|---|---|
| Insights | **$12 to $24/month** if you analyse all 12,000 threads with OpenAI models. Less if you sample |
| Engine | **Cannot be forecast.** See the warning below |

> [!WARNING]
> **Engine cost is genuinely unpredictable.** It is metered at $1.50 per LCU, and
> LangChain publishes no LCU-per-trace consumption figure. Their documentation says
> usage "depends on the number of traces Engine analyses, the depth of analysis
> required, and the amount of work it performs". If you plan to use Engine, get a
> consumption estimate from LangChain before committing. Do not model it from list
> price alone.

**The Developer plan is worth knowing about.** It is free, includes 5,000 traces, and
would cost **$3.50/month** at this volume. But it is capped at **one seat** and excludes
Engine and Insights entirely. It is a single-developer plan, not a team plan.

### Langfuse Cloud

| Line | Cost |
|---|---|
| Core plan base | $29.00 |
| Units: 118,800 against 100,000 included, 18,800 over at $8/100k | $1.50 |
| Seats | **$0, unlimited** |
| **Total** | **$30.50/month** |

Flat regardless of team size. Ten engineers cost the same as one.

### Langfuse self-hosted

Treated as an independent infrastructure cost, since that is what it is.

| Line | Monthly | Basis |
|---|---|---|
| Compute: 1 VM, 4 vCPU / 16 GiB | **~$120** | Langfuse's recommended sizing. Replace with your own infrastructure rate |
| Storage: 100 GB block | **~$10** | Lasts decades at this volume |
| Backups and snapshots | ~$5 | |
| Langfuse licence | **$0** | MIT. All core features |
| **Infrastructure subtotal** | **~$135** | |
| **Operations** | **see below** | The line that actually decides this |

The measured resource profile backs the sizing. From [05-scale.md](05-scale.md): the
stack idles at **2.16 GiB** and peaks at **3.2 GiB** under a 395 traces/second load. At
400 traces per **day** you are using a fraction of one percent of that capacity. A
4 vCPU / 16 GiB box is generous, and the recommendation exists for production ingest,
not for this.

Committed or long-term capacity typically cuts the compute line by 30 to 60 percent,
and an existing internal host or shared cluster can absorb it at close to zero marginal
cost. This is the line most worth replacing with your own number.

---

## Side by side, 400 traces/day, 5 engineers

| Option | Monthly | Seats | Data location |
|---|---|---|---|
| LangSmith Developer | **$3.50** | **1 only** | Their cloud |
| **Langfuse Cloud Core** | **$30.50** | Unlimited | Their cloud |
| Langfuse self-hosted, infra only | **~$135** | Unlimited | **Your network** |
| LangSmith Plus | **$196** | 5 | Their cloud |
| LangSmith Plus + Insights | **~$214** | 5 | Their cloud |
| Langfuse self-hosted, infra + ops | **~$535 to $935** | Unlimited | **Your network** |

Two things jump out.

**Langfuse Cloud is roughly one sixth the price of LangSmith Plus** at this team size,
and the gap widens with every engineer you add.

**Self-hosting is not the cheap option at this volume.** Once you count the person who
runs it, it is the most expensive line on the page. Self-hosting is a data-residency
decision, not a cost-saving one, until you are at far higher volume.

---

## The operations line

This is the number that gets left off vendor comparisons, and it dominates everything
else at this scale.

A single-node Docker Compose deployment realistically needs **4 to 8 hours a month** of
someone's attention: version upgrades, ClickHouse disk management, backup verification,
certificate renewal, and responding when the worker stops draining.

| Loaded engineering rate | 4 hrs/month | 8 hrs/month |
|---|---|---|
| $50/hour | $200 | $400 |
| $100/hour | $400 | $800 |

At $100/hour and 8 hours, **operations costs six times the infrastructure**. Substitute
your own rate, but do not leave the line at zero.

Langfuse's own documentation is explicit that Docker Compose "lacks high-availability,
scaling capabilities, and backup functionality", and recommends Kubernetes for
production. Kubernetes raises both the infrastructure and the operations line.

---

## What changes the answer

### Team size

At 400 traces/day, holding volume constant:

| Engineers | LangSmith Plus | Langfuse Cloud | Ratio |
|---|---|---|---|
| 1 | $40 | $30.50 | 1.3x |
| 3 | $118 | $30.50 | **3.9x** |
| 5 | $196 | $30.50 | **6.4x** |
| 10 | $391 | $30.50 | **12.8x** |
| 20 | $781 | $30.50 | **25.6x** |

Team size is the single biggest cost driver in this comparison. It is worth deciding
deliberately who genuinely needs a LangSmith seat rather than buying one per engineer.

### Volume

Holding the team at 5 engineers:

| Traces/month | LangSmith Plus | Langfuse Cloud | Self-hosted infra | Self-host storage growth |
|---|---|---|---|---|
| 9,000 | $195 | $29 | ~$135 | 0.1 GB/mo |
| 12,000 | $196 | $31 | ~$135 | 0.1 GB/mo |
| 100,000 | $240 | $100 | ~$135 | 0.7 GB/mo |
| 1,000,000 | $690 | $724 | ~$135 | 7.1 GB/mo |
| 10,000,000 | $5,190 | $6,271 | **~$350** | 71 GB/mo |

The crossovers:

- **Langfuse Cloud beats LangSmith** until about 1 million traces a month, where the
  per-unit multiplier catches up with LangSmith's per-trace rate.
- **Self-hosting beats both** from roughly 200,000 traces a month on infrastructure
  alone, and decisively past 1 million.
- **At 10 million a month, self-hosting is 15 to 18 times cheaper**, and that is where
  the operations cost genuinely pays for itself.

Storage figures come from the measured **7.27 MB per 1,000 traces** in
[05-scale.md](05-scale.md). At 10M traces a month you add roughly 850 GB a year, so
disk becomes a real line item rather than a rounding error.

### Retention

Easy to miss and expensive. LangSmith base traces are kept **14 days**. Extended
retention is **400 days at 10x the price**, and traces with feedback attached are
upgraded automatically, which is exactly what your evaluation runs produce.

At 12,000 traces a month, if a quarter get upgraded that is 3,000 traces at $5.00 per
thousand, so **$15/month** against $1.00 for the base tier. Small here, but it scales
linearly and it surprises people.

Self-hosted Langfuse keeps everything until you delete it, at 7.27 MB per 1,000 traces.

---

## Recommendation

For **300 to 400 traces a day with a team of engineers**:

**1. Langfuse Cloud Core at $29 to $31/month** is the best value by a wide margin.
Unlimited seats, 90-day retention, and no infrastructure to run. It costs less than a
single LangSmith seat.

**2. Add a small number of LangSmith Plus seats** only if the team needs Studio for
LangGraph debugging or wants Engine and Insights. Two seats is $78/month. Buying a seat
per engineer at $39 is where the budget disappears.

**3. Self-host Langfuse only if data residency requires it.** At this volume it costs
more than Langfuse Cloud once operations are counted. It becomes the obvious answer past
roughly 1 million traces a month, or immediately if trace data cannot leave your network.

**4. Revisit at 1 million traces a month.** That is where every crossover in this
document sits.

---

## Assumptions and provenance

Being explicit about which numbers are hard and which are estimates.

**Measured in this lab:**
- 9.9 Langfuse units per trace (20 traces produced 198 observations)
- 7.27 MB of storage per 1,000 traces
- 2.16 GiB idle, 3.2 GiB peak memory for the six-container stack
- 395 traces/second end-to-end ingest ceiling on 14 cores

**Published by the vendors** (August 2026, verify before committing):
- LangSmith: $39/seat, $0.50 per 1k base traces, $5.00 per 1k extended, $1.50/LCU,
  $1.00/LSU, Insights at $1 to $2 per 1k threads
- Langfuse: $0 / $29 / $199 / $2,499 plan floors, graduated $8 / $7 / $6.50 / $6 per
  100k units, unlimited seats on paid plans, MIT licence for self-hosted

**Estimated, and the weakest numbers here:**
- ~$120/month for a 4 vCPU / 16 GiB VM. Indicative only, not measured, and not tied to
  any particular provider. Substitute your own infrastructure rate
- 4 to 8 hours/month of operations effort for a single-node deployment
- 30 days per month for the daily-to-monthly conversion

**Not forecastable:**
- LangSmith Engine consumption. Metered per LCU with no published rate per trace. Get a
  quote from LangChain

### Sources

- [LangSmith pricing](https://www.langchain.com/pricing)
- [LangSmith Insights documentation](https://docs.langchain.com/langsmith/insights)
- [LangSmith Engine](https://www.langchain.com/langsmith/engine)
- [Langfuse pricing](https://langfuse.com/pricing)
- [Langfuse self-hosting pricing](https://langfuse.com/pricing-self-host)
- [Langfuse Docker Compose sizing](https://langfuse.com/self-hosting/deployment/docker-compose)

---

[Index](README.md) · [Tracing](01-tracing.md) · [Evaluation](02-evaluation.md) · [Features](03-features.md) · [Cost](04-cost.md) · [Scale](05-scale.md) · [Feature matrix](06-feature-matrix.md)
