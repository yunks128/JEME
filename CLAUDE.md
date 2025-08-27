# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run test` - Run tests
- `npm run deploy` - Deploy to GitHub Pages

## Architecture Overview

This is a React-based dashboard for visualizing citation metrics across multiple scientific models. The codebase is designed with a modular, multi-model architecture that supports both model-specific and generic implementations.

### Key Architectural Components

**Model Configuration System (`src/config/modelConfig.js`)**
- Centralized configuration for all supported models (RAPID, CARDAMOM, CMS-Flux, ECCO, ISSM, MOMO-CHEM)
- Each model has display name, description, data path, color theme, domain, and links
- Use `getModelConfig(modelName)` to retrieve model-specific settings

**Routing Architecture (`src/AppWithRouting.js`)**
- Main dashboard route: `/science-model-dashboard`
- Model-specific routes: `/science-model-dashboard/{modelName}`
- Generic sub-pages: `/science-model-dashboard/{modelName}/citations`, `/geographic-impact`, `/research-domains`
- Legacy routes maintained for backward compatibility

**Generic vs Model-Specific Components**
- Generic components (e.g., `GenericDashboard.js`) work with any model using the model configuration
- Model-specific components exist in `src/views/{MODEL_NAME}/` directories
- Generic components are parameterized by `modelName` and use `citationsData` prop

**Data Processing (`src/utils/dataUtils.js`)**
- `extractPublicationData()` - Standardizes publication data from different JSON formats
- `calculateMetrics()` - Computes overview metrics (total papers, citations, growth rate)
- `processGeographicData()` - Extracts geographic information from abstracts/titles
- `processCitationTrends()` - Analyzes citation patterns over time
- `processResearchDomains()` - Groups publications by research domain

**Data Structure**
- Citation data stored as JSON files in `src/data/` with format `{MODEL_NAME}_analyzed.json`
- Each entry contains standardized fields: title, authors, year, citations, DOI, research_domain, etc.
- Geographic data inferred from text analysis of abstracts and titles

### Component Structure

**Charts (`src/components/charts/`)**
- All chart components built with Recharts library
- Reusable across different models
- Handle data transformation internally

**Views (`src/views/`)**
- `Dashboard.js` - Main multi-model overview
- `Generic*.js` - Template pages that work with any model
- `{MODEL_NAME}/` - Model-specific implementations when needed

**Utilities (`src/utils/`)**
- `dataUtils.js` - Core data processing functions
- `colors.js` - Color palette definitions

## Development Patterns

**Adding New Models**
1. Add model configuration to `src/config/modelConfig.js`
2. Add JSON data file to `src/data/`
3. Create route in `src/AppWithRouting.js`
4. Use generic components or create model-specific ones in `src/views/{MODEL_NAME}/`

**Working with Citation Data**
- Always use `extractPublicationData()` to normalize data structure
- Use processing functions in `dataUtils.js` for consistent data transformation
- Handle missing/malformed data gracefully with try-catch blocks

**Styling**
- Uses Tailwind CSS for styling
- Lucide React for icons
- Model-specific colors defined in model configuration
- Responsive design with mobile-first approach

## Testing & Deployment

- Built with Create React App
- Deployed to GitHub Pages via `npm run deploy`
- No specific test framework beyond React Testing Library (included with CRA)
- Homepage configured for GitHub Pages deployment