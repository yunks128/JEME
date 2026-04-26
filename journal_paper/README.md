# Journal Paper Bundle

Self-contained submission package for the JEME/JEOE platform paper.

## Contents

```
journal_paper/
├── journal_paper_draft.md             # Master source (Markdown, prose form)
├── journal_paper_draft.docx           # Pandoc-rendered Word version (plain black text)
├── generate_figures.py                # Reproducible figure + PPT generator
├── capture_screenshots.py             # Playwright capture of live dashboards
├── figures/
│   ├── fig1_citation_overview.png     # Papers/citations per model (12pt fonts)
│   ├── fig5_network_matrix.png        # Cross-model bridge-paper matrix
│   ├── fig7_uq_pipeline.png           # Three-phase UQ schematic
│   ├── fig8_sphere_coverage.png       # Earth-system-sphere coverage
│   ├── fig9_full_text_pipeline.mmd    # Mermaid: tiered fetch pipeline
│   ├── architecture.mmd               # Mermaid: overall system
│   ├── fig11_jeme_dashboard.png       # Screenshot: JEME main dashboard
│   ├── fig12_ecco_model.png           # Screenshot: ECCO model page
│   ├── fig13_ecco_uncertainty.png     # Screenshot: ECCO UQ page
│   ├── fig14_jeoe_dashboard.png       # Screenshot: JEOE missions
│   ├── fig15_jesp_dashboard.png       # Screenshot: JESP scientist profiles
│   └── journal_paper_figures.pptx     # Editable PowerPoint (figures 1, 5, 7, 8, 9, 10)
└── README.md
```

## Reproducing the artifacts

```
# Recompute statistics from current public/data/*_analyzed.json,
# regenerate PNG figures, and rebuild the editable PPT.
python3 generate_figures.py

# Capture fresh dashboard screenshots (requires the JEME/JEOE dev
# server on :3000 and the JESP server on :3002 to be running).
python3 capture_screenshots.py

# Rebuild the DOCX from the markdown.
pandoc journal_paper_draft.md -o journal_paper_draft.docx \
       -f markdown-autolink_bare_uris --resource-path=. --standalone
```

## Editable PowerPoint

`figures/journal_paper_figures.pptx` contains six slides — one per figure.
Slide 1 (Figure 1) is a native PowerPoint chart whose categories and
values are editable. Slide 5 (Figure 9, fetch pipeline) and Slide 6
(Figure 10, architecture) are built from native PowerPoint shapes
(rounded rectangles, connectors), so labels and arrows can be edited
directly. Slides 2–4 (Figures 5, 7, 8) embed PNGs that can be replaced
by re-running `generate_figures.py`. All text uses 12 pt black, matching
the main-text font size.

## Numbers consistency

Figure 1 and Table 1 are both populated from `generate_figures.py`'s
`compute_stats()` function reading the same per-model JSON files in
`public/data/`. They are consistent by construction.

## Scope of this revision

- Removed the Model Capability Level (MCL) framework (sections, figures,
  references, and tables).
- Converted enumerated stage / phase / tier blocks to flowing prose.
- Removed all horizontal rules between sections.
- Body text contains no inline hyperlinks; URLs appear only in the
  References section. Pandoc is invoked with
  `-f markdown-autolink_bare_uris` so even bare URLs in the references
  remain plain black text rather than blue hyperlinks.
- Figure fonts standardised to ≥12 pt to match main-text size.

## Target journal

Earth and Space Science (AGU) — gold OA, IF 3.1, in-scope for model
assessment and informatics.
