# Application of Nondental 3D Software in Dentistry: A Scoping Review
## Reproducibility repository

**Repository:** https://github.com/Qihang-He/nondental-3d-software-scoping-review
**Archived release (DOI):** 10.6084/m9.figshare.33684943.v1 — https://doi.org/10.6084/m9.figshare.33684943.v1

Everything needed to reproduce the review is here: the search strategies, the screening and coding
prompts, every script, the raw model responses, the locked dataset, all derived statistics, the
figures' inputs, and the author-verification materials.

**Locked dataset:** `06_data/locked_analysis_dataset_v4.csv` (n = 863 included studies).
Every quantitative value in the manuscript is generated from this file by
`02_scripts/05_analysis/_tools_stats_core.py`.
See `PIPELINE.md` for the execution order and `02_scripts/MANIFEST.csv` for the full script index.

---

## 1. What changed in this version of the analysis

The decisive eligibility criterion of this review is the **explicit use of a named third-party
nondental 3D software package**. That information is normally reported in the *methods section of
the full text*, not in the abstract. In the first version of this analysis the criterion was
nevertheless applied at title/abstract level, which excluded a large number of eligible studies.

This revision therefore applies the criterion in two stages:

| Stage | Scope | Outcome |
|---|---|---|
| 1. Title/abstract screening | 2,556 unique records | 1,639 excluded |
| 2. Full-text re-assessment of excluded records | every excluded record with a retrievable full text: 1,168 records | **304 studies met the criteria and were added** |
| Reverse check of the previously included set | same standard applied in reverse | 4 records removed (no named package in the full text); 3 software annotations corrected |
| Date-window check | publication after 30 June 2026 | 3 records removed |

The included set consequently changed from 566 to **863 studies**.
775 excluded records had no retrievable
full text and could not be re-assessed; this residual uncertainty is stated in the manuscript.

### PRISMA chain (from `05_results/PRISMA_链路_v2.json`)

```
identified            PubMed 1,727 | Web of Science 1,695 | IEEE Xplore 304   = 3,726
duplicates removed    1,170
screened (title/abs)  2,556
excluded at stage 1   1,639   (of which 1,168 re-assessed in full text, 775 without full text)
assessed at full text 1,781
excluded at full text 918
INCLUDED              863
```

---

## 2. Repository map

| Folder | Contents |
|---|---|
| `01_protocol/` | Screening prompt, config template, sampling design |
| `02_scripts/` | Every script, organised by analysis stage (see `MANIFEST.csv`) |
| `03_search_strategies/` | Complete search strings and database exports for PubMed, Web of Science and IEEE Xplore |
| `04_logs/` | Raw JSON responses of all screening runs, agreement analysis, exclusion reasons, the full-text re-assessment pass, outcome coding |
| `05_results/` | Statistics core, PRISMA chain, contingency statistics, clustering parameters and labels, per-record traceability of every dataset change |
| `06_data/` | Locked analysis dataset (v4), eligibility audit, software glossary, screening corpus, PDF-to-record matching |
| `07_supplementary/` | Supplementary Files 2 and 3, dataset provenance table |
| `08_verification/` | Sampling outputs and the author verification workbook |

---

## 3. Model and API details

Screening and coding used the DeepSeek chat-completions API with the identifier `deepseek-chat`,
decoding parameters `temperature = 0.1`, `max_tokens = 300-500`, `stream = false`. The identifier is
a rolling alias and is not pinned to a version; the `model` field returned by the API resolved to
`deepseek-flash` (DeepSeek-V4.1-Flash) at the time of the calls. Every entry in `04_logs/` records
the request timestamp, returned model identifier, provider response id, returned content and latency.

**No API key is stored in this repository.** `01_protocol/config.example.json` shows the expected
shape. The scripts read the key from a local `config.local.json` placed in the project's
`07_AI重跑原始记录/` folder; that file is git-ignored and is **not** part of this repository. To
re-run the model-assisted steps you must supply your own key there.

Note that the analysis steps (§PIPELINE.md) do **not** require a key at all: they consume the
model logs already deposited in `04_logs/`.

## 4. What these materials do and do not establish

- Agreement across the three screening runs (94.3%; Fleiss' kappa = 0.936) measures the
  **reproducibility** of the procedure, not its accuracy.
- No population-level sensitivity, specificity or confusion matrix is reported, because no complete
  human reference standard exists for the whole corpus.
- Study-design agreement (97.6%; Cohen's kappa = 0.966) is **coding stability** across two
  model-assisted passes, not agreement between two human raters.
- The workflow archetypes are **algorithmically derived** groupings, reproducible from this dataset;
  they are not manually coded categories, and no inter-rater reliability is claimed for them.
- Reported advantages, challenges and gaps were coded from **titles and abstracts** of the included
  studies, so the frequencies reflect what authors state prominently rather than every qualification
  in the full text.

## 5. Licensing and citation

Code and data are released for reuse with attribution; see `LICENSE`.

**Please cite the archived release rather than the moving `main` branch.**

- **DOI (archive, version-pinned):** 10.6084/m9.figshare.33684943.v1 —
  https://doi.org/10.6084/m9.figshare.33684943.v1
- **Source repository, release `v1.0`:**
  https://github.com/Qihang-He/nondental-3d-software-scoping-review/releases/tag/v1.0
- **Machine-readable citation metadata:** `CITATION.cff` (GitHub shows a "Cite this repository" button)

The archived deposit and the release tag both pin the exact state of every script, log, dataset and
statistic reported in the manuscript. If you use these materials, please cite the article together
with the DOI above.
