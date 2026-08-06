# Idempotency

An operation is idempotent if doing it twice has the same effect as doing it
once -- GET and DELETE usually are, "charge the customer" is not. Retries are
only safe on idempotent operations, which is why payment APIs accept an
idempotency key: the client generates a unique key per logical operation and
the server deduplicates repeats. When designing tools for an agent, prefer
idempotent tools -- an LLM may call the same tool twice with the same
arguments, and the system should survive that.
