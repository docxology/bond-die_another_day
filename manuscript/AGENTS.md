# manuscript/ — Agent Guide (ICARUS)

Rules for any agent editing the `die_another_day` paper source. These are
constraints, not style preferences: the tests in `tests/test_manuscript_variables.py`
enforce most of them and will fail the suite.

## Hard rules

1. **Never type a number into results prose.** Not a score, not a duration, not
   a count. If you need one, add it to
   `src/die_another_day/manuscript_variables.py` and cite the token.
2. **Know which generator you need.**
   - The value is a *configured input* (something a human chose in
     `config.yaml`) → add it to `generate_variables`.
   - The value is a *measured output* (something a model computed) → add it to
     `measured_variables`, reading it off the `ConceptResults` record returned
     by `mission_results.run_all_concepts`. Never recompute it locally with a
     second call — that is exactly how a paper drifts from its code.
3. **No orphan tokens.** Every token you generate must be cited by some
   `NN_*.md` section, and every token you cite must be generated. Both
   directions are tested.
4. **References must be real.** `references.bib` holds checkable sources with
   real authors, titles, and years. If you are not confident a reference exists,
   remove it rather than ship it. Keep `99_references.md` in step with the
   `.bib` file.
5. **Sidecars are not sections.** Only `NN_*.md` files are token-resolved and
   copied to `output/manuscript/`. `README.md`, `AGENTS.md`, `SYNTAX.md`, and
   `preamble.md` are not, so tokens in them stay literal.

## Adding a measured result

1. Compute it inside a `src/die_another_day/` domain module (never in the
   manuscript layer, never in `scripts/`).
2. Surface it on `ConceptResults` if it is not already reachable.
3. Format it in `measured_variables` with an explicit precision — use `_fixed`,
   not `str(float)`, so the rendered digits are stable.
4. Cite the token in a section.
5. Run `uv run pytest tests/test_manuscript_variables.py` — it checks the token
   equals the runner's value, is cited, and moves when the config moves.

## Editing `config.yaml`

`config.yaml` is a live input, not documentation. Changing a value under
`concepts:` changes what the mission computes, what the figures show, and what
this paper reports. After any edit:

```bash
uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/generate_figures.py
uv run pytest tests/
```

Check that the prose still *reads* correctly, too: a token keeps the number
honest, but an adjacent adjective ("comfortably clears", "well past") can go
stale silently. Prefer wording that survives a parameter change.
