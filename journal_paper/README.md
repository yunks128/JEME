# Journal Paper Bundle

Self-contained submission package for the JEME/JEOE platform paper.

## Contents

```
journal_paper/
├── journal_paper_draft.md         # Master source (Markdown)
├── journal_paper_draft.docx       # Pandoc-rendered Word version
├── figures/
│   ├── fig1_citation_overview.{png,pdf}
│   ├── fig2_mcl_heatmap.{png,pdf}
│   ├── fig3_mcl_radar.{png,pdf}
│   ├── fig4_gap_analysis.{png,pdf}
│   ├── fig5_network_matrix.{png,pdf}
│   ├── fig6_tier1_averages.{png,pdf}
│   ├── fig7_uq_pipeline.{png,pdf}
│   ├── fig8_sphere_coverage.{png,pdf}
│   ├── fig9_full_text_pipeline.mmd  # Mermaid: tiered fetch pipeline
│   └── architecture.mmd             # Mermaid: overall system
└── README.md
```

## Regenerating the DOCX

```
pandoc journal_paper_draft.md -o journal_paper_draft.docx --resource-path=. --standalone
```

## Rendering the Mermaid figures

If a target journal needs raster output for figures 9 / 10, render with `mmdc`
(install: `npm install -g @mermaid-js/mermaid-cli`):

```
mmdc -i figures/fig9_full_text_pipeline.mmd -o figures/fig9_full_text_pipeline.png -w 1600 -H 1200
mmdc -i figures/architecture.mmd            -o figures/architecture.png            -w 1800 -H 1000
```

## Updates from the previous draft

This revision (2026-04-25) reflects the current state of the platform after:

- Peer-review filtering and multi-agent cleanup → **27,494 papers / 1.16M citations**
  (down from 44,452 / 1.33M in the prior draft due to preprint/off-topic removal).
- Addition of **TROPESS** as a third JEOE mission.
- New **multi-source full-text retrieval pipeline** (Section 3.2 + Figure 9):
  Copernicus → Wiley TDM → Elsevier TDM → Unpaywall → OpenAlex → Semantic
  Scholar → DOI redirect. ~180 cumulative DAS-enrichment flips applied.
- Documented **team-paper classification limitation** (Section 5.2): abstract-only
  reclassification systematically demotes team papers that use the model only in
  the methods section. The platform retains team papers' existing labels as the
  defensible default.

## Target journal

Earth and Space Science (AGU) — gold OA, IF 3.1, in-scope for model assessment
and informatics.
