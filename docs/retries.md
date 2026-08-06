# Retries

Retry only operations that are safe to repeat (idempotent). Use exponential
backoff with jitter: wait 1s, 2s, 4s... plus a random offset so many clients
don't retry in lockstep (the "thundering herd" problem). Cap total attempts
at 3-5. Never retry on 4xx client errors -- the request is wrong and will
fail again; retry on 429 and 5xx only. Log every retry with the attempt
number so the pattern is visible in observability tools.
