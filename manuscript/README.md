# manuscript/ — ICARUS paper source

The publication source for `die_another_day` (mission codename **ICARUS**,
*Die Another Day*, 2002). Sections are plain Markdown with mission tokens; the
tokens are hydrated from code, never typed by hand.

## Files

| File | Role |
| --- | --- |
| `00_abstract.md` | What the package does and the headline measured outcomes. |
| `01_introduction.md` | The three theatres, the six domain modules, the runner/adapter split. |
| `02_methodology.md` | The mathematics of each concept, the control design, and the execution structure. |
| `03_results.md` | Measured outcomes of one deterministic run, with four figures. |
| `04_conclusion.md` | What the integration shows, including the two negative results. |
| `05_experimental_setup.md` | Every configured input, plus the configured-vs-measured boundary. |
| `06_reproducibility.md` | Seeds, byte-reproducible figures, and the gates that enforce all of it. |
| `07_scope_and_related_work.md` | Scope, prior work, and per-model limitations. |
| `99_references.md` | Human-readable reference list mirroring `references.bib`. |
| `preamble.md` | LaTeX preamble fragment for PDF rendering. |
| `config.yaml` | Paper metadata **and** the `concepts:` parameter block the code reads. |
| `references.bib` | Machine-readable bibliography (real, checkable sources only). |
| `SYNTAX.md` | The token and figure-reference conventions used in these sections. |
| `AGENTS.md` | Rules for agents editing this directory. |

## Rendering

```bash
uv run python scripts/generate_figures.py                   # output/figures/*.png
uv run python scripts/z_generate_manuscript_variables.py    # output/manuscript/*.md
```

The second command is strict: any unresolved token fails the run rather than
rendering literal braces. `--allow-draft` relaxes it for intentional drafts.

## The one rule

Numbers are never typed into prose. A configured input becomes a token in
`generate_variables`; a measured output becomes a token in
`measured_variables`, computed by `mission_results.run_all_concepts` — the same
call the `MissionProvider` uses. Two tests enforce the loop: every token cited
here must be generated, and every token generated must be cited.
