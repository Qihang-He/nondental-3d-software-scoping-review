# Pipeline

The review is reproduced in the stages listed below. Each folder under
`02_scripts/` corresponds to one stage; `02_scripts/MANIFEST.csv` lists every
script with a one-line purpose, line count and checksum.

```
01_protocol/           prompts, codebook, sampling design, config template
02_scripts/00_lib/     shared API client, prompts and response parsers
02_scripts/01_screening/                title/abstract screening and exclusion reasons
02_scripts/02_fulltext_reassessment/    the stage-2 full-text pass of excluded records
02_scripts/03_selection/                building the locked included set and the PRISMA chain
02_scripts/04_charting/                 software canonicalisation, dates, journals, country, design
02_scripts/05_analysis/                 statistics, contingency analysis, clustering, RQ3
02_scripts/06_figures/                  Figures 1-6 and Supplementary Figure S1
02_scripts/07_documents/                supplementary files, provenance table, manuscript checks
02_scripts/08_verification/             sample re-examination: evidence pack and per-record verdicts
02_scripts/99_exploratory/              superseded one-off QC scripts (kept for the audit trail)
```

## Execution order

Model-assisted steps produce the logs in `04_logs/`; the analysis steps turn those
logs into the reported numbers. Only the analysis steps are needed to regenerate
every statistic, table and figure, because the model logs are already deposited.

**Analysis steps (no API key required)**

| # | Script | Produces |
|---|---|---|
| 1 | `04_charting/_tools_fix_dates_journals.py` | half-year periods, normalised journal names |
| 2 | `05_analysis/_tools_archetype.py` | workflow archetypes |
| 3 | `05_analysis/_tools_stats_core.py` | **`05_results/statistics_core.json` — the single source of truth** |
| 4 | `05_analysis/_tools_extra_stats.py` | trend regression, contingency analysis, co-occurrence |
| 5 | `03_selection/_update_prisma.py` | two-stage PRISMA chain |
| 6 | `05_analysis/_rq3_summarize.py` | RQ3 frequencies |
| 7 | `06_figures/_run_figs.py`, `make_supp_fig.py` | Figures 1-5, Supplementary Figure S1 |
| 8 | `07_documents/_tools_supp2.py`, `_tools_supp3.py` | Supplementary Files 2 and 3, provenance table |

`python run_pipeline.py` runs this list; `--with-model` additionally re-runs the
model-assisted steps (requires an API key).

## Path configuration

All scripts resolve the project root as

```python
ROOT = os.environ.get('SCOPING_ROOT') or <derived from the file location>
```

so they run unchanged from either the original project layout or a clone of this
repository once `SCOPING_ROOT` points at the working copy that contains the data
folders. Scripts in `99_exploratory/` were **not** normalised and keep the original
absolute paths.
