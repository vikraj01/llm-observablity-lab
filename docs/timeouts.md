# Timeouts

Every network call needs a timeout; the default of "wait forever" is how one
slow dependency freezes a whole service. Set connect timeouts short (1-3s)
and read timeouts based on the p99 latency of the dependency plus headroom.
Timeouts should shrink as you go deeper in the call chain (the "timeout
budget" pattern) so the outermost caller fails fast instead of stacking
waits. A timeout firing is a signal -- record it, don't swallow it.
