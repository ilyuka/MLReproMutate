# MLReproMutate

MLReproMutate is an early-stage research software project for evaluating
reproducibility safeguards in machine-learning experiments using
domain-specific mutation testing.

The core research question is:

> If a realistic reproducibility fault is deliberately introduced into a
> machine-learning experiment, do the project's existing tests, CI checks,
> and experiment safeguards detect it?

## Status

MLReproMutate is currently under active early-stage development.

The initial focus is on CPU-runnable Python machine-learning projects and
reproducibility faults involving:

- dependency versions;
- dataset and artifact identity;
- experiment configuration;
- preprocessing;
- random state;
- artifact provenance.

The project does **not** aim to test neural-network robustness, adversarial
examples, or model-level mutation testing.

## Planned workflow

MLReproMutate will:

1. detect applicable reproducibility mutation candidates;
2. create an isolated project copy;
3. execute a baseline validation command;
4. introduce one controlled reproducibility mutation;
5. execute the validation command again;
6. classify the mutation outcome;
7. produce a machine-readable report.

Planned outcome classes include:

- `KILLED`
- `SURVIVED`
- `INVALID`
- `EQUIVALENT`
- `TIMEOUT`
- `ERROR`

## Development

The project is being developed publicly as research software.

See:

- `docs/threat-model.md`
- `docs/research-log.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`

## License

MIT License.
