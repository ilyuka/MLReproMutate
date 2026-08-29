# Post-freeze impact audit for GitHub issue #1

Date: 2026-08-29

Issue:

    https://github.com/ilyuka/MLReproMutate/issues/1

This document records a post-freeze audit of whether the sandbox import-isolation
bug reported in GitHub issue #1 could have affected the already frozen empirical
study.

This audit does not change the corpus, mutation operators, selected candidates,
workflows, validation oracles, execution protocol, restoration protocol, or
canonical outcomes. No repository is re-executed as part of this assessment.

## 1. Defect under review

Issue #1 demonstrated that MLReproMutate sandbox execution could produce an
incorrect SURVIVED result when all of the following conditions held:

1. validation executed against a temporary sandbox copy;
2. the target project used an importable Python package rather than directly
   executing the mutated file;
3. an editable installation or equivalent Python import path still referred to
   the original source tree outside the sandbox; and
4. that external source location took precedence over the mutated sandbox copy.

Under those conditions, validation could import unchanged original code instead
of the mutated sandbox code.

The independently reproduced failure therefore concerns source-resolution
isolation, not mutation generation itself.

## 2. Audit question

The audit question is:

> Is there evidence that any canonical empirical outcome was produced under the
> source-resolution configuration required by issue #1, such that validation
> could have observed an unchanged external source tree instead of the frozen
> mutant?

The standard for this post-freeze audit is not to rerun cases with the corrected
software. The assessment uses only existing execution provenance and frozen
artifacts.

## 3. B02 execution isolation

The B02 execution harness ran candidate commands through the dedicated
`b02_isolation.py` Bubblewrap layer.

That layer clears the inherited process environment with `--clearenv` and
constructs the candidate environment explicitly. Host `PYTHONPATH` is therefore
not inherited implicitly into B02 candidate execution.

Later D025 execution additionally requires distinct baseline and mutant
environments and requires correction symmetry for evaluated mutations.

These properties differ materially from the issue #1 reproducer, where a Python
environment retained an editable reference to the unchanged original project
outside the temporary MLReproMutate workspace.

## 4. Cases with editable-install or explicit source-path evidence

Repository provenance was searched for editable installation, `PYTHONPATH`,
`site-packages`, and related source-resolution evidence.

### B02-01 — tslearn

The documented setup used:

    pip install -e .[docs,all_features]

from the frozen case source checkout.

The selected mutation was in:

    docs/examples/metrics/plot_frechet.py

and the validation command directly executed that file:

    python docs/examples/metrics/plot_frechet.py

The baseline and mutant therefore executed the selected source file from the
candidate workspace rather than importing that mutation target through an
external editable package location.

The canonical outcome was SURVIVED, with post-hoc semantic verification
confirming that the seed mutation changed the generated random series.

Finding:

    no issue-#1 source-resolution path identified

### B02-02 — TensorLy

B02-02 is the closest early case to the affected MLReproMutate execution path.

The selected target was:

    examples/decomposition/plot_parafac2.py

and the validation command directly executed the example script from the
temporary MLReproMutate workspace.

The mutation target was therefore the directly executed sandbox file rather
than an imported TensorLy package module that could be shadowed by an external
editable installation.

The recorded baseline and mutant output paths identify separate temporary
MLReproMutate source workspaces.

The canonical SURVIVED mutation was also independently confirmed
non-equivalent by post-hoc semantic verification of the generated factors,
noise, and synthesized tensor.

Finding:

    old MLReproMutate sandbox used, but the issue-#1 import-shadow condition is
    not present for the selected mutation target

### B02-03 — Braindecode

The documented setup used:

    pip install -e .[moabb,hub]

but setup exceeded the frozen timeout.

Baseline validation was not run and mutation validation was not run.

Finding:

    cannot affect a canonical mutation outcome

### B02-06 — Yellowbrick

An editable installation appeared in a compatibility-install attempt.

The canonical primary case did not reach mutation evaluation.

Finding:

    cannot affect a canonical mutation outcome

### B02-23 — setvaluedprediction

A compatibility correction explicitly normalized `PYTHONPATH` to the
corresponding unchanged checkout for each independent side.

The final unchanged baseline nevertheless failed during test collection and the
mutation was not evaluated.

Finding:

    cannot affect a canonical mutation outcome

### B02-26 — PolicySynth

The documented setup used:

    pip install -e .

for both baseline and mutant.

However, the execution provenance records independent environments:

    baseline-venv-valid
    mutant-venv

and the installation was performed separately for the corresponding baseline
and mutant checkouts.

The relevant configuration is therefore not an editable installation in one
shared validation environment that continues to resolve the unchanged original
checkout while MLReproMutate mutates a separate temporary copy.

The selected mutation was evaluated as SURVIVED. Post-hoc semantic verification
confirmed that removing stratification changed training membership and holdout
class counts.

Finding:

    editable installation present, but bound separately to the corresponding
    baseline and mutant source trees; no issue-#1 stale-original import path
    identified

## 5. B01 and remaining corpus evidence

The repository-wide provenance search did not identify an evaluated B01
canonical mutation using the issue-#1 combination of an external editable
original source tree together with a separately mutated temporary sandbox copy.

Other environment references observed in the corpus either:

- belong to setup-failed / non-evaluated cases;
- refer to corresponding baseline and mutant environments;
- execute the mutated target file directly; or
- are unrelated environment/runtime provenance.

No canonical outcome was identified for which the existing evidence shows that
validation imported the unchanged original mutation target instead of the
mutated candidate tree.

## 6. Assessment

Post-freeze assessment:

    NO EVIDENCE OF IMPACT ON CANONICAL EMPIRICAL OUTCOMES

This statement is intentionally narrower than claiming that the historical
software version was free of the defect.

Issue #1 is a real correctness bug in the released sandbox execution behavior.
The audit instead finds that the specific source-resolution conditions required
to turn that defect into a false empirical SURVIVED result are not evidenced in
the frozen canonical cases.

In particular:

- cases that used editable installation but failed before mutation evaluation
  cannot affect the mutation-outcome denominator;
- B02-01 and B02-02 directly executed the selected mutated source file;
- B02-23 did not reach mutation evaluation;
- B02-26 used corresponding independent baseline and mutant source
  environments rather than a stale external original checkout;
- B02 execution isolation cleared inherited host environment variables unless
  explicitly added.

## 7. Research-state consequence

No primary empirical artifact is changed as a result of this audit.

Specifically, this audit does not change:

- the frozen corpus;
- repository revisions;
- selected operator/candidate pairs;
- setup-failed classifications;
- KILLED or SURVIVED outcomes;
- semantic-equivalence classifications;
- RQ1 denominators or numerators;
- RQ2 workflow/oracle classifications; or
- restoration results.

No corrective corpus rerun is warranted on the evidence currently available.

If later provenance demonstrates that a canonical evaluated case actually
resolved its mutation target from an unchanged source tree outside the mutant
workspace, that would constitute new evidence and would require a separate
methodological assessment.

Until such evidence exists, the frozen empirical study remains unchanged.
