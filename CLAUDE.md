# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `npm start` - Start development server (binds to `0.0.0.0:3000`)
- `npm run build` - Build for production
- `npm test` - Run tests (React Testing Library / Jest)
- `npm run deploy` - Build and deploy to GitHub Pages
- `node scripts/clean_citation_data.js --all --dry-run` - Preview citation data cleanup across all models
- `node scripts/clean_citation_data.js --model ECCO` - Clean a specific model's data
- `python scripts/compute_uncertainty.py --model RAPID` - Compute Phase 1 uncertainty scores
- `python scripts/phase2_llm_confidence.py --model RAPID --sample 10` - Phase 2 multi-temperature LLM sampling
- `python scripts/phase3_skeptic_agent.py --model RAPID` - Phase 3 skeptic agent review
- `python scripts/verify_peer_review.py --all --dry-run` - Preview non-peer-reviewed paper removal
- `python scripts/verify_peer_review.py --all` - Remove non-peer-reviewed papers from all models
- `python scripts/classify_peer_review.py --all` - Classify peer-review status without removing

## Architecture Overview

React-based dashboard (CRA) for visualizing citation metrics across scientific models and NASA missions. Split into two sites:

- **JEME** (JPL's Earth Modeling Enterprise) — 8 science models at `/science-model-dashboard/`
- **JEOE** (JPL Earth Observation Enterprise) — NASA missions at `/science-model-dashboard/JEOE`

Each site has its own branding, favicon, browser tab title, and context-aware NavBar that links to the other.

**Supported Models (JEME):** RAPID, CARDAMOM, CMS-Flux, ECCO, ISSM, MOMO-CHEM, LES, EDMF
**Supported Missions (JEOE):** GRACE, SWOT

### Model Configuration (`src/config/modelConfig.js`)

Centralized config for all models and missions. Each entry has: name, displayName, description, dataPath, color, domain, github, website, fullDescription. Missions additionally have `type: 'mission'`.
- `getModelConfig(modelName)` - Retrieve model-specific settings
- `getModelList()` - Get array of all model names

### Routing (`src/AppWithRouting.js`)

- `/science-model-dashboard` - JEME main dashboard (8 models)
- `/science-model-dashboard/JEOE` - JEOE main dashboard (missions)
- `/science-model-dashboard/{modelName}` - Model/mission-specific dashboard
- `/science-model-dashboard/{modelName}/citations` - Citations page
- `/science-model-dashboard/{modelName}/geographic-impact` - Geographic impact
- `/science-model-dashboard/{modelName}/research-domains` - Research domains
- `/science-model-dashboard/how-it-works` - Methodology page
- Some models (CMS-Flux, ECCO, ISSM, CARDAMOM, MOMO-CHEM) have model-specific research-domains routes
- Legacy routes maintained for backward compatibility

### JEME/JEOE Navigation (`src/components/NavBar.js`)

The NavBar is context-aware based on the `activeItem` prop:
- **JEME context** (models): Shows `Dashboard | Models | JEOE | How It Works`
- **JEOE context** (missions): Shows `Dashboard | Missions | JEME | How It Works`
- Logo, title, subtitle, favicon (`public/favicon.svg` vs `public/favicon-jeoe.svg`), and browser tab title all swap dynamically
- `isJEOE` is true when `activeItem` is `'JEOE Dashboard'` or a mission name (GRACE, SWOT)

### Generic vs Model-Specific Components

- Generic components (`GenericDashboard.js`, `GenericCitationsPage.js`, etc.) work with any model via `modelName` route param
- Model-specific overrides live in `src/views/{MODEL_NAME}/` directories (including `src/views/GRACE/` and `src/views/SWOT/` for missions)
- `src/views/JEOEDashboard.js` is the JEOE main dashboard
- Generic components dynamically import `src/data/{MODEL_NAME}_analyzed.json`

### Data Processing (`src/utils/dataUtils.js`)

- `extractPublicationData(entry)` - Normalizes both Crossref format (nested `title[]`, `author[]`, `published-print['date-parts']`) and simplified scraper format (flat `title`, `authors`, `year`)
- `calculateMetrics(citationsData)` - Total papers, citations, growth rate, domains
- `processGeographicData(citationsData)` - Geographic extraction from abstract/title keywords
- `processCitationTrends(citationsData)` - Yearly trends with cumulative calculations
- `processResearchDomains(citationsData)` - Group by research domain
- `processMissionData(citationsData)` - Satellite mission/instrument statistics
- `extractMissions(entry)` - Extract mission data from `missions_instruments` field
- `getAgencyColor(agency)` / `getMissionTypeIcon(type)` - Agency/mission display helpers

### Network Analysis (`src/utils/networkAnalysis.js`)

Cross-model connectivity analysis shown on the main dashboard:
- `performNetworkAnalysis()` - Orchestrates full analysis: loads all model data, finds bridge papers (shared across models), calculates connection matrix, analyzes cross-model authors and domain overlap
- Components in `src/components/network/`: NetworkGraph, ConnectionMatrix, BridgePapersTable, NetworkInsightsCard

### Data Structure

Citation data stored as JSON in `src/data/{MODEL_NAME}_analyzed.json`. Two formats coexist:
- **Crossref format:** `title[]`, `author[]`, `published-print['date-parts']`, `is-referenced-by-count`, `DOI`, `abstract`, `container-title[]`
- **Simplified format:** `title` (string), `authors` (string array), `year`, `doi`, `citation_count`, `venue`, `paper_id`, `research_domain`, `engagement_level`, `missions_instruments[]`, `citing_team_paper`

Always use `extractPublicationData()` to normalize before processing.

### Data Cleaning (`scripts/clean_citation_data.js`)

Removes spam and metadata noise from citation JSON files. Three filter categories:
1. "Review of:" spam entries (auto-generated nano-electronics papers)
2. Placeholder/corrupted entries ("Insight Review Articles", "Digital Commons", etc.)
3. Supplementary material/metadata (interactive comments, printer-friendly versions)

Supports `--model NAME`, `--all`, and `--dry-run` flags. Idempotent.

### Peer-Review Filtering (`scripts/verify_peer_review.py`)

**Rule: Only peer-reviewed papers are included in the dashboard.** Non-peer-reviewed entries (preprints, theses, conference abstracts, technical reports, etc.) must be removed from all model/mission data files.

Three-tier classification:
1. **Tier 1 — Deterministic venue patterns:** Blocklist matching (arxiv, preprints, discussions, meeting abstracts, theses, posters, etc.) with exceptions for peer-reviewed venues that contain blocklist words (PNAS, Proc. Royal Society, IEEE, etc.)
2. **Tier 2 — Crossref DOI type lookup:** Queries Crossref API for `journal-article` vs `posted-content` etc.
3. **Tier 3 — LLM fallback:** For ambiguous cases (uses the shared Bedrock client; see LLM Backend below). Skip with `--no-llm`.

Non-peer-reviewed papers are removed from JSON files and logged in `scripts/removed_non_peer_reviewed.json`.

- `python scripts/verify_peer_review.py --all --dry-run` — Preview removals across all models
- `python scripts/verify_peer_review.py --model TROPESS` — Process a specific model
- `python scripts/classify_peer_review.py --all` — Add/update `is_peer_reviewed` field without removing

**Supported models:** CARDAMOM, CMS-Flux, ECCO, EDMF, GRACE, ISSM, LES, MOMO-CHEM, RAPID, SWOT, TROPESS

### Venue Enrichment (`scripts/fetch_ecco_venues.py`)

Fetches missing journal/venue info for citation papers using external APIs:
- **Crossref API** for entries with DOIs (`https://api.crossref.org/works/{doi}`)
- **Semantic Scholar batch API** for entries with only `paper_id`
- Caches results in `scripts/ecco_venue_cache.json` for incremental reruns
- Run with: `python3 scripts/fetch_ecco_venues.py`

### Data Quality & Multi-Agent Verification

Citation data is collected from Semantic Scholar via `citing_team_paper` / `team_paper_id` links. A multi-agent verification pipeline cross-validates entries:

1. **Team Paper Categorizer** — Classifies each team paper by relevance tier (Core > Infrastructure > Data/Methods > Domain Science > Tangential/Unrelated) using hierarchical keyword matching against the team paper title
2. **Crossref Agent** — Resolves DOIs to validate existence and retrieve journal/venue metadata
3. **Semantic Scholar Agent** — Batch API for title recovery (broken metadata) and venue enrichment for DOI-less entries
4. **Keyword Classifier** — Scores citing paper relevance via domain-specific keyword matching on title + abstract
5. **Deduplication Agent** — DOI-first, title-fallback duplicate detection

**Verification outcomes:**
- ECCO: Removed ~3,900 entries (EGM2008 geodesy, island biogeography, PFAS chemistry, off-topic citing papers); enriched 7,600+ venue fields
- ISSM: Repaired 1,904 broken team paper titles (42 "Untitled"/truncated IDs resolved via Semantic Scholar)
- All other models: Verified clean (91-96% keyword relevance match)

**Uncertainty estimates:** ~8-12% false removal rate among removed entries; ~3-5% false retention rate among kept entries. Primary uncertainty source is the 50% of ECCO entries lacking abstracts (title-only verification).

The `GenericCitationsPage` handles both Crossref and simplified data formats, normalizing field name differences (e.g., `DOI` vs `doi`, `URL` vs `url`, `container-title` vs `venue`).

### Uncertainty Quantification Pipeline

Three-phase pipeline for quantifying classification confidence. Each phase adds data to the `uncertainty` block on each citation entry.

**Phase 1 — Deterministic scoring (`scripts/compute_uncertainty.py`):**
- Evidence confidence from metadata completeness (abstract, DOI, venue, authors, keyword matches)
- Pipeline variance from keyword classifier vs LLM label disagreement
- Heuristic reasoning confidence (0.85 with abstract, 0.5 without)
- Composite: `0.45 * evidence + 0.45 * reasoning - 0.10 * pipeline_variance`

**Phase 2 — Multi-temperature LLM sampling (`scripts/phase2_llm_confidence.py`):**
- Calls the LLM 3x at temperatures [0.1, 0.5, 1.0] per entry
- `stochastic_variance`: fraction of runs disagreeing with majority label (0.0-0.67)
- `reasoning_confidence`: average of the model's self-assessed confidence (1-5), normalized to 0-1
- Updated composite: `0.35 * evidence + 0.35 * reasoning + 0.20 * (1 - stochastic_variance) - 0.10 * pipeline_variance`
- Uses the shared Bedrock client (see LLM Backend below), caches in `scripts/phase2_cache.json`

**Phase 3 — Skeptic agent (`scripts/phase3_skeptic_agent.py`):**
- Reviews high-risk entries: `miscalibration_risk == "high"`, `stochastic_variance > 0.3`, or high engagement with low confidence
- Asks the LLM to challenge existing classification, rates agreement (1-5)
- `override_flag: true` when skeptic agreement <= 2/5
- Adds `skeptic_review` block with agreement score, alternative classifications, and review reason
- Uses the shared Bedrock client, caches in `scripts/phase3_cache.json`

**Run order:** Phase 1 → Phase 2 → Phase 1 (recompute with Phase 2 data) → Phase 3

### LLM Backend (`scripts/llm_client.py`)

All analysis scripts call the LLM through one shared client, `scripts/llm_client.py`, which uses **AWS Bedrock** (Anthropic Claude). Do not add per-script API calls — import `call_llm` instead:

```python
from llm_client import call_llm
data = call_llm(prompt, system=SYSTEM_PROMPT, temperature=0.1)  # returns parsed JSON by default
text = call_llm(prompt, json_mode=False)                        # raw text
```

- **Auth:** bearer token in `.env.bedrock` (`AWS_BEARER_TOKEN_BEDROCK`), git-ignored. The client auto-loads it.
- **Model/region via env:** `BEDROCK_MODEL_ID` (default `us.anthropic.claude-sonnet-4-5-20250929-v1:0`), `BEDROCK_REGION` (default `us-east-1`). The `us.` inference-profile prefix is required.
- Handles retry/backoff on throttling and strips ```` ```json ```` fences before parsing. Requires `boto3>=1.35`.
- A deprecated `call_gemini(...)` shim forwards legacy call sites to `call_llm`; prefer `call_llm` in new code.

**UI:** Uncertainty page at `/{modelName}/uncertainty` (`GenericUncertaintyPage.js`). Phase 2/3 sections (`StochasticVarianceCard`, `SkepticReviewCard`) render conditionally when data exists.

## Development Patterns

**Adding New Models (JEME):**
1. Add config to `src/config/modelConfig.js` MODELS object
2. Add route in MODEL_ROUTES and in `src/AppWithRouting.js`
3. Add `src/data/{MODEL_NAME}_analyzed.json`
4. Add dynamic import case in `src/utils/networkAnalysis.js` `loadAllModelData()`
5. Add dynamic import case in `src/views/Dashboard.js` data loading
6. Add model to MODELS array in `scripts/clean_citation_data.js`
7. Add model to MODELS array in `scripts/verify_peer_review.py` and `scripts/classify_peer_review.py`
8. Run `python scripts/verify_peer_review.py --model {MODEL_NAME}` to remove non-peer-reviewed papers
9. Add color to `modelColors` in `ModelComparisonChart.js` and `MultiModelCitationTrendsChart.js`
10. Use generic components or create model-specific ones in `src/views/{MODEL_NAME}/`

**Adding New Missions (JEOE):**
1. Add config to `src/config/modelConfig.js` MODELS object with `type: 'mission'`
2. Add route in `src/AppWithRouting.js`
3. Add `src/data/{MISSION_NAME}_analyzed.json`
4. Add mission to MISSION_LINKS in `src/components/NavBar.js`
5. Add mission card to `src/views/JEOEDashboard.js` missions array
6. Add mission to MODELS array in `scripts/verify_peer_review.py` and `scripts/classify_peer_review.py`
7. Run `python scripts/verify_peer_review.py --model {MISSION_NAME}` to remove non-peer-reviewed papers
8. Add color to `modelColors` in `ModelComparisonChart.js` and `MultiModelCitationTrendsChart.js`
9. Create dashboard in `src/views/{MISSION_NAME}/Dashboard.js`

**Data Loading Pattern:**
- Pages dynamically import JSON via switch/case on model name
- Use `useMemo` for data processing
- Wrap in DataLoader component for loading/error/empty states

**Styling:** Tailwind CSS v2.2.19, Lucide React icons, Recharts charts, D3/TopoJSON for maps. Model-specific colors from `modelConfig.color`.

## Git Commit Rules

- Do NOT include `Co-Authored-By` lines in commit messages

## Deployment

- Default port: `3000` (set `PORT` in `.env` to override)
- Set `PUBLIC_URL=/science-model-dashboard` when building for GCP (`npm run build:gcp`)
- GitHub Pages is NOT used
