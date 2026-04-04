# Examples

This directory will contain small CPU-runnable examples demonstrating
MLReproMutate mutation operators.

Examples should be:

- fast to execute;
- deterministic where possible;
- independent of proprietary data;
- suitable for automated testing;
- focused on one reproducibility concept at a time.

## Available examples

### Dependency pin mutation

[`dependency-pin/`](dependency-pin/) demonstrates how relaxation of an exact
dependency constraint survives validation without a reproducibility safeguard
and is killed after the safeguard is introduced.