# Manuscript syntax conventions (ICARUS)

The conventions used by every `NN_*.md` section in this directory.

## Mission tokens

A token is a double-braced upper-snake identifier, matched by
`[A-Z0-9_]+` between doubled braces. `resolve_manuscript_tree` substitutes each
one and then re-scans; any surviving token aborts the run in strict mode, so a
misspelled name fails loudly instead of rendering literal braces.

```markdown
The exposure ceiling is {{ICE_SAFE_EXPOSURE_S}} s across {{ICE_SQUADS}} squads.
```

Two families, produced by two functions in
`src/die_another_day/manuscript_variables.py`:

| Family | Generator | Example | Meaning |
| --- | --- | --- | --- |
| configured input | `generate_variables` | `ICE_ENV_TEMP_C` | a literal from `config.yaml` |
| measured output | `measured_variables` | `ICE_SAFE_EXPOSURE_S` | computed by a model in this run |

Naming: prefix by concept (`ID_`, `SEQ_`, `ICE_`, `HYP_`, `STRUCT_`, `MIRROR_`,
`ORBIT_`), suffix by unit (`_S`, `_C`, `_M2`, `_MPA`, `_MJ`, `_DEG`, `_TONS`).
A token whose meaning is a measured version of a configured threshold takes a
`_MEASURED` suffix (e.g. `SEQ_GENUINE_JACCARD_MEASURED` versus the configured
`SEQ_MATCH_JACCARD`).

## Which files are resolved

Only files matching `NN_*.md` (two leading digits) are token-resolved and
copied into `output/manuscript/`. Everything else in this directory —
`README.md`, `AGENTS.md`, this file, `preamble.md` — is a sidecar and is left
alone, so braces here are literal and harmless.

## Figures

Figures are referenced by path relative to the package root, with a
pandoc-crossref identifier:

```markdown
![Caption sentence describing what the reader should see.](output/figures/icarus_pass_profile.png){#fig:icarus_pass}
```

The four figures are written by `scripts/generate_figures.py` into
`output/figures/`. Captions state what the figure *shows*, not merely what it
is; numeric claims in a caption still go through tokens.

## Mathematics

Inline math uses `$...$`, display math `$$...$$`. Keep symbol definitions next
to their first use — the manuscript has no separate symbol table.

## Citations

Sections cite in author-year prose (`(Gold, 1971)`), with the machine-readable
entry in `references.bib` and a mirrored numbered entry in `99_references.md`.
Pandoc citation keys are deliberately not used, so a section renders correctly
with or without a citation processor in the chain.

## Style

- One sentence per line where practical; it keeps diffs reviewable.
- Wrap prose near 80 columns.
- ASCII punctuation for units and operators (`W/m^2`, `-34 C`).
- Tables for control comparisons; prose for the interpretation that follows.
