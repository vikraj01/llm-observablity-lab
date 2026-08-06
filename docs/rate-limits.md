# Rate limits

APIs return 429 Too Many Requests when you exceed their quota. Respect the
Retry-After header when present. Client-side, use a token bucket to smooth
bursts instead of hammering until rejected. For LLM APIs specifically, both
requests-per-minute and tokens-per-minute limits apply -- batch small calls
and stream long ones. Track 429 counts per endpoint in your metrics; a rising
rate usually means a runaway loop, not real traffic growth.
