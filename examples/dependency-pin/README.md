# Dependency Pin Mutation Fixture

This fixture provides a small deterministic demonstration of a dependency reproducibility mutation.

The project declares an exact dependency constraint:

```text
scikit-learn==1.5.2
```

MLReproMutate relaxes this constraint to:

```text
scikit-learn>=1.5.2
```

## Unguarded validation

`validate_unguarded.py` checks only the experiment output.

It does not verify the dependency specification.

The dependency mutation therefore survives:

```text
baseline PASS
mutation applied
validation PASS
→ SURVIVED
```

## Guarded validation

`validate_guarded.py` additionally verifies that the exact dependency pin remains present.

The same mutation is therefore detected:

```text
baseline PASS
mutation applied
validation FAIL
→ KILLED
```

## Purpose

This fixture demonstrates the core MLReproMutate evaluation semantics in a small controlled environment.

It does not attempt to demonstrate actual dependency resolution drift. Changing a dependency specification does not guarantee that a different package version is installed.