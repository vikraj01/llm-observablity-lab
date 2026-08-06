# Circuit breakers

A circuit breaker stops calling a dependency that keeps failing. Closed =
normal traffic; after N consecutive failures it opens and requests fail
immediately without hitting the dependency; after a cooldown it goes
half-open and lets one probe request through -- success closes it again.
This protects both sides: your service stops wasting time on doomed calls,
and the struggling dependency gets room to recover. Pair breakers with
fallbacks (cached data, a degraded answer) where possible.
