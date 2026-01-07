#!/usr/bin/env python3
"""
ECCO MCL Evidence Extraction Script
====================================
Extracts evidence for Diego's Core Model Capability Levels framework
from ECCO team papers using Gemini 2.5 Pro.

Cost Estimate (Gemini 2.5 Pro):
- Input: $1.25 per 1M tokens
- Output: $5.00 per 1M tokens

Per Paper Analysis:
- System prompt: ~2,000 tokens
- Paper abstract: ~400 tokens average
- Total input per paper: ~2,400 tokens
- Output per paper: ~800 tokens

Total for Full Analysis (2,038 papers):
- Input: 2,038 × 2,400 = 4.89M tokens = $6.11
- Output: 2,038 × 800 = 1.63M tokens = $8.15
- TOTAL: ~$14.26

Recommended Approach (Stratified Sample of 200 papers):
- Input: 200 × 2,400 = 0.48M tokens = $0.60
- Output: 200 × 800 = 0.16M tokens = $0.80
- TOTAL: ~$1.40

Usage:
    python extract_mcl_evidence.py --input ecco_team_papers.json --output mcl_evidence.json
    python extract_mcl_evidence.py --input ecco_team_papers.json --sample 200 --output mcl_evidence_sample.json
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path
import google.generativeai as genai

# MCL Framework Definitions
MCL_DIMENSIONS = {
    "physics_conservation": {
        "name": "Physics & Conservation",
        "description": "Evaluates adherence to laws of nature. Checks for 'leaks' in the system.",
        "levels": {
            1: "Empirical or 'Nudged' physics; budgets do not close or are ignored",
            2: "Primary physics present; global budgets monitored but not strictly enforced",
            3: "Strictly Closed Budgets. Full Adjoint/Finite Element consistency across all scales"
        },
        "keywords": ["budget", "conservation", "adjoint", "primitive equations", "nudging", "closed", "mass balance", "heat budget", "salt budget"]
    },
    "data_integration": {
        "name": "Data Integration",
        "description": "Assesses how observations are combined with model logic.",
        "levels": {
            1: "Forced: Model is driven by data; physics may be violated",
            2: "Sequential: Periodic updates (e.g., Kalman Filter); results in 'jumps'",
            3: "Synthesis: 4D-Var or MCMC. Data and physics mathematically inseparable"
        },
        "keywords": ["4D-Var", "assimilation", "optimization", "adjoint", "observations", "constraint", "MCMC", "Kalman", "synthesis"]
    },
    "verification": {
        "name": "Verification",
        "description": "Mathematical correctness of the code. 'Are equations solved right?'",
        "levels": {
            1: "Functional: 'Code runs' without crashing",
            2: "Structured: Unit/Regression tests; convergence studies",
            3: "Algorithmic: Adjoint/Taylor tests for gradient accuracy; exact benchmarks"
        },
        "keywords": ["Taylor test", "adjoint verification", "convergence", "benchmark", "regression test", "gradient", "tangent linear"]
    },
    "validation": {
        "name": "Validation",
        "description": "Predictive skill against real-world data. 'Is this the right model?'",
        "levels": {
            1: "Subjective: 'Eyeball' fits; qualitative agreement",
            2: "Statistical: Global RMSE and Bias metrics",
            3: "Process-Level: Blind validation against independent, global datasets"
        },
        "keywords": ["validation", "comparison", "independent", "RMSE", "bias", "skill", "withheld", "blind test", "intercomparison"]
    },
    "uncertainty_quantification": {
        "name": "Uncertainty Quantification",
        "description": "Ability to quantify confidence and error bounds.",
        "levels": {
            1: "Heuristic: Expert judgment or arbitrary error bars",
            2: "Ensemble: Sensitivity analysis; spread of runs as error proxy",
            3: "Probabilistic: Formal Bayesian UQ; posterior distributions"
        },
        "keywords": ["uncertainty", "ensemble", "error", "sensitivity", "Bayesian", "posterior", "probability", "covariance", "confidence"]
    },
    "numerical_fidelity": {
        "name": "Numerical Fidelity",
        "description": "Spatial/temporal resolution and boundary handling.",
        "levels": {
            1: "Coarse: Low-resolution static grids; simplified boundaries",
            2: "Refined: Nested grids or regional refinement; realistic topography",
            3: "Dynamic: Anisotropic mesh refinement; time-varying/moving boundaries"
        },
        "keywords": ["resolution", "grid", "mesh", "boundary", "topography", "partial cell", "adaptive", "refinement", "submesoscale"]
    },
    "portability_scaling": {
        "name": "Portability & Scaling",
        "description": "Performance across different hardware architectures.",
        "levels": {
            1: "Static: Serial code; specific hardware only",
            2: "Parallel: MPI/OpenMP; scales on HPC clusters",
            3: "Architecture-Agnostic: Cloud-native; GPU-accelerated; linear scaling"
        },
        "keywords": ["parallel", "MPI", "GPU", "scaling", "HPC", "cloud", "performance", "cores", "exascale"]
    },
    "interoperability": {
        "name": "Interoperability",
        "description": "Standards for I/O and coupling with other models.",
        "levels": {
            1: "Isolated: Proprietary I/O; no coupling interfaces",
            2: "Standardized: NetCDF/HDF5; basic metadata",
            3: "Plug-and-Play: FAIR compliant (Zarr); ESMF/NUOPC compliant"
        },
        "keywords": ["NetCDF", "CF convention", "FAIR", "Zarr", "ESMF", "coupling", "standard", "interoperable", "open"]
    },
    "sustainability": {
        "name": "Sustainability",
        "description": "Documentation, maintenance, and community health.",
        "levels": {
            1: "Ad-hoc: No version control; sparse documentation",
            2: "Maintained: Git versioning; public repo; basic guides",
            3: "Institutional: Full CI/CD; complete docs; long-term roadmap"
        },
        "keywords": ["documentation", "GitHub", "open source", "community", "CI/CD", "roadmap", "maintenance", "tutorial", "release"]
    }
}


def create_analysis_prompt(paper: dict, dimension: str) -> str:
    """Create a prompt for analyzing a paper against a specific MCL dimension."""
    dim_info = MCL_DIMENSIONS[dimension]

    prompt = f"""Analyze the following paper for evidence relevant to the MCL dimension: {dim_info['name']}

DIMENSION DESCRIPTION: {dim_info['description']}

LEVEL CRITERIA:
- Level 1 (Low): {dim_info['levels'][1]}
- Level 2 (Medium): {dim_info['levels'][2]}
- Level 3 (High): {dim_info['levels'][3]}

PAPER INFORMATION:
Title: {paper.get('title', 'Unknown')}
Authors: {paper.get('authors', 'Unknown')}
Journal: {paper.get('journal', paper.get('venue', 'Unknown'))}
Year: {paper.get('year', 'Unknown')}
DOI: {paper.get('doi', 'Unknown')}
Abstract: {paper.get('abstract', 'No abstract available')}

INSTRUCTIONS:
1. Identify any evidence in this paper relevant to the {dim_info['name']} dimension
2. Quote the specific passage(s) that provide evidence
3. Determine which level (1, 2, or 3) the evidence supports
4. If no relevant evidence is found, indicate "NO_EVIDENCE"

RESPONSE FORMAT (JSON):
{{
    "dimension": "{dimension}",
    "has_evidence": true/false,
    "evidence_level": 1/2/3 or null,
    "evidence_passages": ["quote1", "quote2", ...],
    "justification": "explanation of how evidence maps to level",
    "paper_doi": "{paper.get('doi', 'Unknown')}",
    "paper_title": "{paper.get('title', 'Unknown')}"
}}

Respond ONLY with the JSON object, no additional text."""

    return prompt


def analyze_paper_for_dimension(
    model: genai.GenerativeModel,
    paper: dict,
    dimension: str
) -> dict:
    """Analyze a single paper for a specific dimension."""
    prompt = create_analysis_prompt(paper, dimension)

    try:
        response = model.generate_content(prompt)
        result_text = response.text.strip()

        # Try to parse JSON from response
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        result = json.loads(result_text.strip())
        return result
    except json.JSONDecodeError as e:
        return {
            "dimension": dimension,
            "has_evidence": False,
            "evidence_level": None,
            "evidence_passages": [],
            "justification": f"JSON parse error: {str(e)}",
            "paper_doi": paper.get('doi', 'Unknown'),
            "paper_title": paper.get('title', 'Unknown'),
            "raw_response": result_text[:500] if 'result_text' in locals() else None
        }
    except Exception as e:
        return {
            "dimension": dimension,
            "has_evidence": False,
            "evidence_level": None,
            "evidence_passages": [],
            "justification": f"Error: {str(e)}",
            "paper_doi": paper.get('doi', 'Unknown'),
            "paper_title": paper.get('title', 'Unknown')
        }


def analyze_paper_all_dimensions(
    model: genai.GenerativeModel,
    paper: dict,
    delay: float = 0.5
) -> list:
    """Analyze a paper across all MCL dimensions."""
    results = []
    for dimension in MCL_DIMENSIONS.keys():
        result = analyze_paper_for_dimension(model, paper, dimension)
        results.append(result)
        time.sleep(delay)  # Rate limiting
    return results


def stratified_sample(papers: list, sample_size: int) -> list:
    """Create a stratified sample of papers by year."""
    from collections import defaultdict
    import random

    # Group by year
    by_year = defaultdict(list)
    for paper in papers:
        year = paper.get('year', 'unknown')
        by_year[year].append(paper)

    # Calculate papers per year
    years = sorted([y for y in by_year.keys() if isinstance(y, int)])
    papers_per_year = max(1, sample_size // len(years)) if years else sample_size

    sampled = []
    for year in years:
        year_papers = by_year[year]
        n_sample = min(papers_per_year, len(year_papers))
        sampled.extend(random.sample(year_papers, n_sample))

    # If we need more, sample from remaining
    if len(sampled) < sample_size:
        remaining = [p for p in papers if p not in sampled]
        additional = min(sample_size - len(sampled), len(remaining))
        sampled.extend(random.sample(remaining, additional))

    return sampled[:sample_size]


def aggregate_evidence(all_results: list) -> dict:
    """Aggregate evidence across all papers by dimension."""
    aggregated = {}

    for dimension in MCL_DIMENSIONS.keys():
        dim_evidence = [r for r in all_results if r.get('dimension') == dimension and r.get('has_evidence')]

        # Collect all evidence passages with citations
        evidence_items = []
        for item in dim_evidence:
            for passage in item.get('evidence_passages', []):
                evidence_items.append({
                    "passage": passage,
                    "level": item.get('evidence_level'),
                    "paper_doi": item.get('paper_doi'),
                    "paper_title": item.get('paper_title'),
                    "justification": item.get('justification')
                })

        # Determine overall level (highest demonstrated)
        levels = [item.get('evidence_level') for item in dim_evidence if item.get('evidence_level')]
        overall_level = max(levels) if levels else None

        aggregated[dimension] = {
            "dimension_name": MCL_DIMENSIONS[dimension]['name'],
            "overall_level": overall_level,
            "evidence_count": len(evidence_items),
            "evidence_items": evidence_items,
            "level_distribution": {
                1: sum(1 for l in levels if l == 1),
                2: sum(1 for l in levels if l == 2),
                3: sum(1 for l in levels if l == 3)
            }
        }

    return aggregated


def main():
    parser = argparse.ArgumentParser(description='Extract MCL evidence from ECCO papers using Gemini 2.5 Pro')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file with papers')
    parser.add_argument('--output', '-o', default='mcl_evidence.json', help='Output JSON file')
    parser.add_argument('--sample', '-s', type=int, default=0, help='Sample size (0 = all papers)')
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--model', default='gemini-2.5-pro', help='Gemini model to use')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between API calls (seconds)')
    parser.add_argument('--cost-estimate-only', action='store_true', help='Only print cost estimate')

    args = parser.parse_args()

    # Load papers
    with open(args.input, 'r') as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, dict) and 'ECCO' in data:
        papers = data['ECCO']
    elif isinstance(data, list):
        papers = data
    else:
        papers = list(data.values())[0] if data else []

    total_papers = len(papers)

    # Calculate cost estimate
    sample_size = args.sample if args.sample > 0 else total_papers

    # Tokens per paper (approximate)
    input_tokens_per_paper = 2400  # System prompt + abstract
    output_tokens_per_paper = 800
    calls_per_paper = len(MCL_DIMENSIONS)  # 9 dimensions

    total_input_tokens = sample_size * input_tokens_per_paper * calls_per_paper
    total_output_tokens = sample_size * output_tokens_per_paper * calls_per_paper

    # Gemini 2.5 Pro pricing
    input_cost = (total_input_tokens / 1_000_000) * 1.25
    output_cost = (total_output_tokens / 1_000_000) * 5.00
    total_cost = input_cost + output_cost

    print(f"\n{'='*60}")
    print("ECCO MCL Evidence Extraction - Cost Estimate")
    print(f"{'='*60}")
    print(f"Total papers available: {total_papers}")
    print(f"Papers to analyze: {sample_size}")
    print(f"Dimensions per paper: {calls_per_paper}")
    print(f"Total API calls: {sample_size * calls_per_paper}")
    print(f"\nToken estimates:")
    print(f"  Input tokens: {total_input_tokens:,} ({total_input_tokens/1_000_000:.2f}M)")
    print(f"  Output tokens: {total_output_tokens:,} ({total_output_tokens/1_000_000:.2f}M)")
    print(f"\nCost breakdown (Gemini 2.5 Pro):")
    print(f"  Input cost ($1.25/1M tokens): ${input_cost:.2f}")
    print(f"  Output cost ($5.00/1M tokens): ${output_cost:.2f}")
    print(f"  TOTAL ESTIMATED COST: ${total_cost:.2f}")
    print(f"{'='*60}\n")

    if args.cost_estimate_only:
        return

    # Configure API
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("ERROR: No API key provided. Set GEMINI_API_KEY or use --api-key")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(args.model)

    # Sample if requested
    if args.sample > 0:
        papers = stratified_sample(papers, args.sample)
        print(f"Using stratified sample of {len(papers)} papers")

    # Analyze papers
    all_results = []
    for i, paper in enumerate(papers):
        print(f"Analyzing paper {i+1}/{len(papers)}: {paper.get('title', 'Unknown')[:50]}...")
        results = analyze_paper_all_dimensions(model, paper, args.delay)
        all_results.extend(results)

        # Progress save every 10 papers
        if (i + 1) % 10 == 0:
            with open(args.output + '.progress', 'w') as f:
                json.dump(all_results, f, indent=2)

    # Aggregate results
    aggregated = aggregate_evidence(all_results)

    # Save results
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "framework": "Diego's Core MCL Framework v1.0",
            "model": "ECCO",
            "papers_analyzed": len(papers),
            "total_papers_available": total_papers,
            "llm_model": args.model,
            "estimated_cost_usd": round(total_cost, 2)
        },
        "aggregated_evidence": aggregated,
        "raw_results": all_results
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\nResults saved to: {args.output}")

    # Print summary
    print(f"\n{'='*60}")
    print("ECCO MCL Assessment Summary")
    print(f"{'='*60}")
    for dim_key, dim_data in aggregated.items():
        level = dim_data['overall_level'] or 'N/A'
        evidence = dim_data['evidence_count']
        print(f"{dim_data['dimension_name']:30} Level {level}  ({evidence} evidence items)")


if __name__ == '__main__':
    main()
