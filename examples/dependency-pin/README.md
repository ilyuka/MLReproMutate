# Dependency pin fixture

This fixture demonstrates a dependency reproducibility mutation.

The project declares an exact dependency pin:

```text
scikit-learn==1.5.2
```

The initial validation command checks only the experiment result and does not
verify that the dependency specification remains exactly pinned.

MLReproMutate should therefore classify relaxation of the dependency pin as
SURVIVED.

A dependency-manifest safeguard can then be added to demonstrate the same
mutation being classified as KILLED.

