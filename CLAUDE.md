# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `npm start` - Start development server (binds to `0.0.0.0:3000`)
- `npm run build` - Build for production
- `npm test` - Run tests (React Testing Library / Jest)
- `npm run deploy` - Build and deploy to GitHub Pages
- `node scripts/clean_citation_data.js --all --dry-run` - Preview citation data cleanup across all models
- `node scripts/clean_citation_data.js --model ECCO` - Clean a specific model's data

## Architecture Overview

React-based dashboard (CRA) for visualizing citation metrics across 8 scientific models. Uses a modular, multi-model architecture with both generic and model-specific implementations.

**Supported Models:** RAPID, CARDAMOM, CMS-Flux, ECCO, ISSM, MOMO-CHEM, LES, EDMF

### Model Configuration (`src/config/modelConfig.js`)

Centralized config for all models. Each entry has: name, displayName, description, dataPath, color, domain, github, website, fullDescription.
- `getModelConfig(modelName)` - Retrieve model-specific settings
- `getModelList()` - Get array of all model names

### Routing (`src/AppWithRouting.js`)

- `/science-model-dashboard` - Main multi-model dashboard
- `/science-model-dashboard/{modelName}` - Model-specific dashboard
- `/science-model-dashboard/{modelName}/citations` - Citations page
- `/science-model-dashboard/{modelName}/geographic-impact` - Geographic impact
- `/science-model-dashboard/{modelName}/research-domains` - Research domains
- `/science-model-dashboard/how-it-works` - Methodology page
- Some models (CMS-Flux, ECCO, ISSM, CARDAMOM, MOMO-CHEM) have model-specific research-domains routes
- Legacy routes maintained for backward compatibility

### Generic vs Model-Specific Components

- Generic components (`GenericDashboard.js`, `GenericCitationsPage.js`, etc.) work with any model via `modelName` route param
- Model-specific overrides live in `src/views/{MODEL_NAME}/` directories
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

## Development Patterns

**Adding New Models:**
1. Add config to `src/config/modelConfig.js` MODELS object
2. Add route in MODEL_ROUTES and in `src/AppWithRouting.js`
3. Add `src/data/{MODEL_NAME}_analyzed.json`
4. Add dynamic import case in `src/utils/networkAnalysis.js` `loadAllModelData()`
5. Add dynamic import case in `src/views/Dashboard.js` data loading
6. Add model to MODELS array in `scripts/clean_citation_data.js`
7. Use generic components or create model-specific ones in `src/views/{MODEL_NAME}/`

**Data Loading Pattern:**
- Pages dynamically import JSON via switch/case on model name
- Use `useMemo` for data processing
- Wrap in DataLoader component for loading/error/empty states

**Styling:** Tailwind CSS v2.2.19, Lucide React icons, Recharts charts, D3/TopoJSON for maps. Model-specific colors from `modelConfig.color`.

## Deployment

- GitHub Pages at `https://yunks128.github.io/science-model-dashboard`
- `npm run deploy` runs build then `gh-pages -d build`
