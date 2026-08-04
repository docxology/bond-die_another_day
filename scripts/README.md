# scripts/ — ICARUS Mission CLIs

Thin orchestrators. Each script adds `src/` to `sys.path` and delegates to
`src/die_another_day/` — no business logic lives here.

| Script | Mission phase / task |
| --- | --- |
| `00_preflight.py` | Identity + frozen-protocol surface report. |
| `run_mission.py` | Full five-stage lifecycle (brief→recon→plan→execute→debrief) + outcome JSON. |
| `brief.py` | Brief phase. |
| `recon.py` | Recon phase (optional goal argument). |
| `plan.py` | Plan phase. |
| `execute.py` | Execute phase (prints outcome JSON). |
| `debrief.py` | Debrief phase (prints lessons). |
| `generate_figures.py` | Renders both concept figures into `output/figures/`. |
| `z_generate_manuscript_variables.py` | Hydrates `{{TOKEN}}`s from `manuscript/config.yaml` (strict by default). |

Run from the package root, e.g. `uv run python scripts/run_mission.py`.
