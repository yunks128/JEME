#!/usr/bin/env python3
"""
LLM-Based Model Capability Level Analyzer

Uses Google Gemini API to perform sophisticated contextual analysis of
citation papers to determine model capability levels across 14 dimensions.

This approach:
1. Samples papers strategically across research domains and engagement levels
2. Uses LLM to extract specific capability evidence from each paper
3. Aggregates evidence across papers to determine dimension scores
4. Provides detailed justifications with paper citations
"""

import json
import os
import sys
import time
import random
from pathlib import Path
from collections import defaultdict
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    print("Installing google-generativeai...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "google-generativeai"])
    import google.generativeai as genai

# Configuration
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

# MCL Dimensions with descriptions for LLM context
MCL_DIMENSIONS = {
    "MCL-1": {
        "name": "Process Representation",
        "description": "Accuracy and completeness of modeled physical processes",
        "indicators": [
            "Physical processes represented (turbulence, advection, convection)",
            "Parameterization sophistication (sea ice, mixed layer, biogeochemistry)",
            "Process interaction complexity (air-sea, ice-ocean coupling)",
            "Validation against theoretical benchmarks"
        ],
        "levels": {
            0: "Highly simplified processes, basic parameterizations",
            1: "Low complexity physics, limited process interactions",
            2: "Moderate complexity with some validated parameterizations",
            3: "State-of-the-art physics with comprehensive process representation"
        }
    },
    "MCL-2": {
        "name": "Spatial Resolution",
        "description": "Ability to resolve relevant spatial scales",
        "indicators": [
            "Resolution ranges mentioned (degrees, km, meters)",
            "Grid types (structured, unstructured, nested)",
            "Scale coverage (global, regional, mesoscale, submesoscale)",
            "Adaptive mesh refinement capabilities"
        ],
        "levels": {
            0: "Single set of scales (coarse-resolution only)",
            1: "Broader set of spatial scales represented",
            2: "Nearly full set of spatial scales covered",
            3: "All relevant scales fully resolved for intended applications"
        }
    },
    "MCL-3": {
        "name": "Temporal Resolution",
        "description": "Frequency of outputs relevant to prediction needs",
        "indicators": [
            "Time scales covered (hourly to centennial)",
            "Time-stepping flexibility",
            "Temporal variability representation",
            "Long-term record generation"
        ],
        "levels": {
            0: "Single set of limited time scales only",
            1: "Broader set of time scales represented",
            2: "Nearly full set of time scales covered",
            3: "Full spectrum of time scales for intended applications"
        }
    },
    "MCL-4": {
        "name": "Process Coupling Sophistication",
        "description": "Process coupling complexity and fidelity",
        "indicators": [
            "Number of coupled components",
            "Coupling frequency and bidirectionality",
            "Earth System Model integration",
            "Biogeochemical/ecosystem coupling"
        ],
        "levels": {
            0: "Uncoupled, single-component model",
            1: "Off-line coupling to one other model/component",
            2: "Off-line coupling to multiple models OR full coupling between 2 components",
            3: "Fully coupled Earth System Model with validated interactions"
        }
    },
    "MCL-5": {
        "name": "Predictive Skill",
        "description": "Ability to simulate and predict observed variability",
        "indicators": [
            "Forecast/prediction applications",
            "Skill scores (RMSE, correlation, bias)",
            "Ensemble capabilities",
            "Operational prediction system usage"
        ],
        "levels": {
            0: "Not used for prediction purposes",
            1: "Limited use in prediction applications",
            2: "Routine use for prediction in limited settings",
            3: "Demonstrated skill in comprehensive long-term assessments"
        }
    },
    "MCL-6": {
        "name": "Computational Performance",
        "description": "Scalability on HPC, cloud, or exascale architectures",
        "indicators": [
            "Parallel scaling (MPI, OpenMP)",
            "GPU acceleration",
            "Cloud deployment (AWS, Azure)",
            "Exascale readiness"
        ],
        "levels": {
            0: "Not scalable, limited to small systems",
            1: "Scalable within one architecture (HPC only)",
            2: "Scalable across multiple architectures (HPC + GPU, not cloud)",
            3: "Exascale-ready with full portability"
        }
    },
    "MCL-7": {
        "name": "Observational Constraint",
        "description": "Degree of observational constraint on model state/parameters",
        "indicators": [
            "Satellite data assimilation (altimetry, SST, GRACE)",
            "In-situ observations (Argo, moorings, CTD)",
            "Multi-source integration",
            "Observation impact studies"
        ],
        "levels": {
            0: "No observational constraints",
            1: "Limited set of observations assimilated",
            2: "Comprehensive observational dataset (NASA missions only)",
            3: "Multi-source constraint (satellite + in-situ + airborne)"
        }
    },
    "MCL-8": {
        "name": "Retrospective Analysis",
        "description": "Use of data assimilation for long-term record generation",
        "indicators": [
            "Reanalysis product generation",
            "Data assimilation methods (4D-Var, Kalman, adjoint)",
            "Record length and consistency",
            "Comparison with established reanalyses"
        ],
        "levels": {
            0: "No retrospective analysis capability",
            1: "DA used for bias correction or limited temporal records",
            2: "Multi-observation DA over long records for limited systems",
            3: "Coupled, fully integrated, benchmarked reanalysis products"
        }
    },
    "MCL-9": {
        "name": "Uncertainty Quantification",
        "description": "Capability to assess uncertainty propagation and sensitivity",
        "indicators": [
            "Ensemble methods",
            "Sensitivity analysis",
            "Error propagation",
            "Probabilistic frameworks"
        ],
        "levels": {
            0: "No uncertainty quantification",
            1: "UQ limited to subset of initial conditions or parameters",
            2: "Experimental design for IC, parameters, and forcing for limited cases",
            3: "Fully quantified with probabilistic analysis framework"
        }
    },
    "MCL-10": {
        "name": "Verification & Validation",
        "description": "Robustness of model evaluation methods",
        "indicators": [
            "Independent validation datasets",
            "Model intercomparison (CMIP, OMIP)",
            "Field campaign validation",
            "Systematic benchmarking"
        ],
        "levels": {
            0: "Minimal validation efforts",
            1: "Validated against limited datasets or case studies",
            2: "Routine validation against multiple datasets for limited cases",
            3: "Rigorously validated with systematic benchmarking"
        }
    },
    "MCL-11": {
        "name": "ML/AI Integration",
        "description": "Use of ML/AI for process emulation, bias correction, data fusion",
        "indicators": [
            "ML algorithms implemented",
            "Neural network emulators",
            "Deep learning applications",
            "Integration into core workflows"
        ],
        "levels": {
            0: "No ML/AI integration",
            1: "ML tested on limited processes or parameterizations",
            2: "ML extensively tested, transitioning to core model activities",
            3: "Fully integrated into core modeling workflows"
        }
    },
    "MCL-12": {
        "name": "Future Mission Support",
        "description": "Role in satellite mission formulation and observational strategies",
        "indicators": [
            "OSSE capabilities",
            "Mission support (GRACE, SWOT, etc.)",
            "Synthetic observation generation",
            "Sensor planning contributions"
        ],
        "levels": {
            0: "No mission support capability",
            1: "Products used to support mission formulation",
            2: "Forward models integrated for limited mission sets",
            3: "Key contributor to OSSEs and comprehensive sensor planning"
        }
    },
    "MCL-13": {
        "name": "Interoperability & Open Science",
        "description": "Community accessibility and compatibility with adjacent tools",
        "indicators": [
            "Code repository accessibility",
            "Open-source licensing",
            "API standardization",
            "Community adoption"
        ],
        "levels": {
            0: "Proprietary, core developers only",
            1: "Available within institution, closed to external users",
            2: "Available to institution + external partners, not fully open",
            3: "Fully open source with standardized interfaces"
        }
    },
    "MCL-14": {
        "name": "Stakeholder & Decision Support",
        "description": "Use in real-world decision-making processes",
        "indicators": [
            "Operational agency usage",
            "Coastal/marine management applications",
            "Policy impact and regulatory usage",
            "Stakeholder engagement"
        ],
        "levels": {
            0: "Research only, no operational applications",
            1: "Tested in limited applications",
            2: "Broadly tested for limited applications",
            3: "Critical tool for operational decision-makers"
        }
    }
}


def create_analysis_prompt(papers_batch, model_name):
    """Create a compact prompt for LLM to analyze papers for capability evidence."""

    prompt = f"""Analyze these papers citing {model_name} model. Extract evidence for 14 capability dimensions.

## Dimensions (each 0-3 scale):
MCL-1: Process Representation (physics complexity)
MCL-2: Spatial Resolution (scale coverage)
MCL-3: Temporal Resolution (time scale coverage)
MCL-4: Process Coupling (component integration)
MCL-5: Predictive Skill (forecast accuracy)
MCL-6: Computational Performance (HPC/GPU/cloud)
MCL-7: Observational Constraint (data assimilation)
MCL-8: Retrospective Analysis (reanalysis capability)
MCL-9: Uncertainty Quantification (error/sensitivity)
MCL-10: Verification & Validation (benchmarking)
MCL-11: ML/AI Integration (machine learning use)
MCL-12: Future Mission Support (OSSE/satellite)
MCL-13: Interoperability (open source/community)
MCL-14: Decision Support (operational use)

## Papers:
"""

    for i, paper in enumerate(papers_batch, 1):
        title = paper.get('title', 'Unknown')[:100]
        abstract = paper.get('abstract', '')[:500]
        year = paper.get('year', 'N/A')
        domain = paper.get('research_domain', 'Unknown')

        prompt += f"""
[{i}] {title} ({year}, {domain})
{abstract}
"""

    prompt += """

## Output JSON format (be concise):
{
  "MCL-1": {"evidence": ["short evidence 1"], "levels": [2], "papers": [1]},
  ...
}

Return ONLY valid JSON. Use empty arrays [] if no evidence. Keep evidence strings under 50 words each."""

    return prompt


def analyze_batch_with_gemini(papers_batch, model_name, batch_num, total_batches, max_retries=3):
    """Send a batch of papers to Gemini for analysis with retry logic."""

    # Use gemini-2.5-pro for better stability
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = create_analysis_prompt(papers_batch, model_name)

    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=8192,
                ),
                safety_settings={
                    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
                    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
                    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',
                }
            )

            # Check if response has content
            if not response.parts:
                if attempt < max_retries - 1:
                    print(f"  ⟳ Batch {batch_num}: Empty response, retrying ({attempt+1}/{max_retries})...")
                    time.sleep(2)
                    continue
                else:
                    print(f"  ✗ Batch {batch_num}: Empty response after {max_retries} attempts")
                    return None

            response_text = response.text.strip()

            # Extract JSON from response
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0]
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0]

            result = json.loads(response_text.strip())
            print(f"  ✓ Batch {batch_num}/{total_batches} analyzed successfully")
            return result

        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                print(f"  ⟳ Batch {batch_num}: JSON error, retrying ({attempt+1}/{max_retries})...")
                time.sleep(2)
                continue
            else:
                print(f"  ✗ Batch {batch_num}: JSON parse error - {str(e)[:50]}")
                return None

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                wait_time = 30 * (attempt + 1)
                print(f"  ⟳ Batch {batch_num}: Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            elif attempt < max_retries - 1:
                print(f"  ⟳ Batch {batch_num}: Error, retrying ({attempt+1}/{max_retries})...")
                time.sleep(2)
                continue
            else:
                print(f"  ✗ Batch {batch_num}: API error - {str(e)[:50]}")
                return None

    return None


def stratified_sample_papers(papers, sample_size=200):
    """Stratified sampling across research domains and engagement levels."""

    # Group papers by domain and engagement level
    groups = defaultdict(list)
    for paper in papers:
        domain = paper.get('research_domain', 'Unknown')
        engagement = paper.get('engagement_level', 'Unknown')
        key = (domain, engagement)
        groups[key].append(paper)

    # Calculate samples per group
    total_groups = len(groups)
    base_per_group = max(1, sample_size // total_groups)

    sampled = []
    for key, group_papers in groups.items():
        # Prioritize papers with abstracts
        with_abstract = [p for p in group_papers if p.get('abstract')]
        without_abstract = [p for p in group_papers if not p.get('abstract')]

        # Sample from papers with abstracts first
        n_to_sample = min(base_per_group, len(with_abstract))
        if n_to_sample > 0:
            sampled.extend(random.sample(with_abstract, n_to_sample))

        # If we need more, sample from without abstract
        remaining = base_per_group - n_to_sample
        if remaining > 0 and without_abstract:
            n_extra = min(remaining, len(without_abstract))
            sampled.extend(random.sample(without_abstract, n_extra))

    # If we haven't reached sample_size, add more randomly
    if len(sampled) < sample_size:
        remaining_papers = [p for p in papers if p not in sampled and p.get('abstract')]
        n_more = min(sample_size - len(sampled), len(remaining_papers))
        if n_more > 0:
            sampled.extend(random.sample(remaining_papers, n_more))

    random.shuffle(sampled)
    return sampled[:sample_size]


def aggregate_evidence(all_batch_results):
    """Aggregate evidence from all batches into final assessment."""

    aggregated = {}

    for mcl_id in MCL_DIMENSIONS.keys():
        aggregated[mcl_id] = {
            "all_evidence": [],
            "level_votes": [],
            "paper_count": 0
        }

    for batch_result in all_batch_results:
        if batch_result is None:
            continue

        for mcl_id in MCL_DIMENSIONS.keys():
            if mcl_id in batch_result:
                mcl_data = batch_result[mcl_id]

                # Handle different key names
                evidence = mcl_data.get('evidence', [])
                if isinstance(evidence, list):
                    aggregated[mcl_id]["all_evidence"].extend(evidence)

                levels = mcl_data.get('levels', mcl_data.get('level_indicators', []))
                if isinstance(levels, list):
                    aggregated[mcl_id]["level_votes"].extend([l for l in levels if isinstance(l, (int, float))])

                refs = mcl_data.get('papers', mcl_data.get('paper_refs', []))
                if isinstance(refs, list):
                    aggregated[mcl_id]["paper_count"] += len(refs)

    return aggregated


def calculate_final_scores(aggregated_evidence):
    """Calculate final MCL scores from aggregated evidence."""

    final_scores = {}

    for mcl_id, data in aggregated_evidence.items():
        votes = data["level_votes"]
        evidence = data["all_evidence"]

        if votes:
            # Calculate weighted average
            avg_score = sum(votes) / len(votes)

            # Adjust based on evidence quantity (boost for more evidence)
            evidence_factor = min(1.0, len(evidence) / 15)
            final_score = avg_score + (evidence_factor * 0.2)
            final_score = min(3.0, max(0.0, final_score))
        else:
            final_score = 0.0

        # Deduplicate evidence
        unique_evidence = list(dict.fromkeys(evidence))[:10]

        level_int = min(3, max(0, round(final_score)))
        final_scores[mcl_id] = {
            "score": round(final_score, 2),
            "evidence_count": len(evidence),
            "vote_count": len(votes),
            "top_evidence": unique_evidence,
            "level_description": MCL_DIMENSIONS[mcl_id]["levels"].get(level_int, "Unknown")
        }

    return final_scores


def generate_report(model_name, final_scores, total_papers, sample_size, output_path):
    """Generate markdown report from final scores."""

    report = f"""# {model_name} Model Capability Level Assessment
## LLM-Based Analysis Report

**Assessment Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Methodology**: Gemini 2.5 Pro LLM-based contextual analysis
**Total Papers in Dataset**: {total_papers:,}
**Papers Analyzed (Stratified Sample)**: {sample_size}

---

## Executive Summary

"""

    # Calculate overall score
    scores = [data["score"] for data in final_scores.values()]
    overall_score = sum(scores) / len(scores) if scores else 0

    level_3_count = sum(1 for s in scores if s >= 2.5)
    level_2_count = sum(1 for s in scores if 1.5 <= s < 2.5)
    level_1_count = sum(1 for s in scores if 0.5 <= s < 1.5)

    # Determine maturity category
    if overall_score >= 2.5:
        maturity = "**Mature Capability** - Operational Readiness"
    elif overall_score >= 1.5:
        maturity = "**Intermediate Development** - Transitioning to Applications"
    else:
        maturity = "**Early Development** - Research-Focused"

    # Get scores for radar chart
    s = {k: final_scores.get(k, {}).get('score', 0) for k in [f'MCL-{i}' for i in range(1, 15)]}

    report += f"""### Overall Maturity Score: {overall_score:.2f} / 3.0

**Category**: {maturity}

| Level | Count | Description |
|-------|-------|-------------|
| Level 3 (Advanced) | {level_3_count} | State-of-the-art capability |
| Level 2 (Intermediate) | {level_2_count} | Moderate capability with validated approaches |
| Level 1 (Basic) | {level_1_count} | Limited but functional capability |
| Level 0 (Minimal) | {14 - level_3_count - level_2_count - level_1_count} | Minimal or no capability |

---

## Capability Radar Chart

```mermaid
%%{{init: {{'theme': 'base', 'themeVariables': {{ 'primaryColor': '#4f46e5'}}}}}}%%
radar-beta
  title {model_name} Model Capability Levels (0-3 Scale)
  axis Process Representation["Process Repr. ({s['MCL-1']:.2f})"], Spatial Resolution["Spatial Res. ({s['MCL-2']:.2f})"], Temporal Resolution["Temporal Res. ({s['MCL-3']:.2f})"], Process Coupling["Coupling ({s['MCL-4']:.2f})"], Predictive Skill["Prediction ({s['MCL-5']:.2f})"], Computational Perf["Computing ({s['MCL-6']:.2f})"], Observational Constraint["Obs. Constraint ({s['MCL-7']:.2f})"], Retrospective Analysis["Retrospective ({s['MCL-8']:.2f})"], Uncertainty Quant["UQ ({s['MCL-9']:.2f})"], V&V Framework["V&V ({s['MCL-10']:.2f})"], ML/AI Integration["ML/AI ({s['MCL-11']:.2f})"], Mission Support["Mission ({s['MCL-12']:.2f})"], Interoperability["Open Science ({s['MCL-13']:.2f})"], Decision Support["Decision ({s['MCL-14']:.2f})"]
  curve a["{model_name} Scores"]{{
    Process Representation: {s['MCL-1']:.2f}
    Spatial Resolution: {s['MCL-2']:.2f}
    Temporal Resolution: {s['MCL-3']:.2f}
    Process Coupling: {s['MCL-4']:.2f}
    Predictive Skill: {s['MCL-5']:.2f}
    Computational Perf: {s['MCL-6']:.2f}
    Observational Constraint: {s['MCL-7']:.2f}
    Retrospective Analysis: {s['MCL-8']:.2f}
    Uncertainty Quant: {s['MCL-9']:.2f}
    V&V Framework: {s['MCL-10']:.2f}
    ML/AI Integration: {s['MCL-11']:.2f}
    Mission Support: {s['MCL-12']:.2f}
    Interoperability: {s['MCL-13']:.2f}
    Decision Support: {s['MCL-14']:.2f}
  }}
  max 3
```

### Capability Score Distribution

| Category | Dimensions | Avg Score |
|----------|------------|-----------|
| 🟢 **Core Strengths** | Top 2-3 scoring dimensions | **{sum(sorted(s.values(), reverse=True)[:3])/3:.2f}** |
| 🟡 **Solid Capabilities** | Middle tier dimensions | **{sum(sorted(s.values(), reverse=True)[3:8])/5:.2f}** |
| 🟠 **Development Areas** | Lower-middle dimensions | **{sum(sorted(s.values(), reverse=True)[8:11])/3:.2f}** |
| 🔴 **Priority Gaps** | Bottom 3 scoring dimensions | **{sum(sorted(s.values())[:3])/3:.2f}** |

---

## Detailed Dimension Scores

| Dimension | Score | Level | Evidence | Description |
|-----------|-------|-------|----------|-------------|
"""

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        name = MCL_DIMENSIONS[mcl_id]["name"]
        score = data["score"]
        evidence_count = data["evidence_count"]

        if score >= 2.5:
            level = "🟢 Advanced"
        elif score >= 1.5:
            level = "🟡 Intermediate"
        elif score >= 0.5:
            level = "🟠 Basic"
        else:
            level = "🔴 Minimal"

        short_desc = data["level_description"][:60] + "..." if len(data["level_description"]) > 60 else data["level_description"]
        report += f"| {mcl_id}: {name} | **{score:.2f}** | {level} | {evidence_count} | {short_desc} |\n"

    report += "\n---\n\n## Dimension Analysis\n\n"

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        mcl_info = MCL_DIMENSIONS[mcl_id]
        score = data['score']

        # Score visualization
        filled = int(score * 10)
        bar = "█" * filled + "░" * (30 - filled)

        report += f"""### {mcl_id}: {mcl_info['name']}

**Score**: {score:.2f} / 3.0 `[{bar}]`

**Level Description**: {data['level_description']}

**Key Indicators Assessed**:
"""
        for indicator in mcl_info['indicators']:
            report += f"- {indicator}\n"

        report += f"""
**Evidence Extracted** ({data['evidence_count']} items from {data['vote_count']} paper assessments):

"""
        if data['top_evidence']:
            display_count = min(5, len(data['top_evidence']))
            for i, evidence in enumerate(data['top_evidence'][:display_count], 1):
                report += f"{i}. {evidence}\n"
            remaining = data['evidence_count'] - display_count
            if remaining > 0:
                report += f"\n*...and {remaining} additional evidence items*\n"
        else:
            report += "*No specific evidence extracted for this dimension*\n"

        report += "\n---\n\n"

    # Strengths and Gaps
    sorted_scores = sorted(final_scores.items(), key=lambda x: x[1]['score'], reverse=True)

    report += """## Capability Assessment

### Top Strengths (Highest Scores)

"""
    for mcl_id, data in sorted_scores[:5]:
        if data['score'] > 0:
            report += f"1. **{MCL_DIMENSIONS[mcl_id]['name']}** ({data['score']:.2f}): {data['level_description']}\n"

    report += """
### Development Priorities (Lowest Scores)

"""
    for mcl_id, data in sorted_scores[-5:]:
        if data['score'] < 3.0:
            report += f"1. **{MCL_DIMENSIONS[mcl_id]['name']}** ({data['score']:.2f}): Needs improvement from current level\n"

    report += f"""
---

## Methodology

This assessment used **Google Gemini 2.5 Pro** for sophisticated contextual analysis of scientific publications.

### Analysis Pipeline:

1. **Data Loading**: Loaded {total_papers:,} citing papers from JSON dataset
2. **Stratified Sampling**: Selected {sample_size} papers across research domains and engagement levels
3. **Batch Processing**: Papers analyzed in batches of 5 for optimal LLM context
4. **Evidence Extraction**: LLM identified specific capability evidence for each MCL dimension
5. **Level Assignment**: LLM assigned preliminary levels (0-3) based on paper content
6. **Aggregation**: Evidence aggregated across all successfully analyzed batches
7. **Final Scoring**: Weighted average with evidence quantity adjustment

### Advantages over Keyword Analysis:

| Aspect | Keyword Analysis | LLM-Based Analysis |
|--------|------------------|-------------------|
| Context Understanding | Word presence only | Full semantic understanding |
| Evidence Quality | Binary (present/absent) | Nuanced quality assessment |
| Multi-factor Assessment | Single keyword per check | Multiple indicators evaluated |
| Ambiguity Handling | Poor | Strong disambiguation |
| Novel Evidence | Misses new terminology | Captures novel descriptions |

### Limitations:

- Sample-based (not all papers analyzed)
- LLM interpretation may vary
- Dependent on abstract/title quality
- Some batches may fail API calls

---

*Generated by LLM-Based Model Capability Analyzer v2.0*
*Model: Gemini 2.5 Pro | Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}*
"""

    # Save report
    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✓ Report saved to: {output_path}")

    return report


def _score_bar(score):
    """Generate a simple score indicator."""
    if score >= 2.5:
        return f"[{score:.1f}]●●●"
    elif score >= 1.5:
        return f"[{score:.1f}]●●○"
    elif score >= 0.5:
        return f"[{score:.1f}]●○○"
    else:
        return f"[{score:.1f}]○○○"


def main():
    """Main analysis pipeline."""

    import argparse
    parser = argparse.ArgumentParser(description='LLM-based Model Capability Analyzer')
    parser.add_argument('input_file', help='Path to JSON file with citation data')
    parser.add_argument('--model-name', default='ECCO', help='Name of the model being analyzed')
    parser.add_argument('--sample-size', type=int, default=200, help='Number of papers to sample')
    parser.add_argument('--batch-size', type=int, default=5, help='Papers per LLM batch')
    parser.add_argument('--output', default=None, help='Output report path')

    args = parser.parse_args()

    print("="*60)
    print("LLM-BASED MODEL CAPABILITY ANALYZER")
    print("="*60)

    # Load data
    print(f"\n📂 Loading data from {args.input_file}...")
    with open(args.input_file) as f:
        papers = json.load(f)

    print(f"   Total papers: {len(papers):,}")

    # Stratified sampling
    print(f"\n🎯 Performing stratified sampling ({args.sample_size} papers)...")
    sampled_papers = stratified_sample_papers(papers, args.sample_size)
    print(f"   Sampled {len(sampled_papers)} papers across domains")

    # Show sampling distribution
    domain_counts = defaultdict(int)
    for p in sampled_papers:
        domain_counts[p.get('research_domain', 'Unknown')] += 1
    print("   Domain distribution:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"     - {domain}: {count}")

    # Create batches
    batches = []
    for i in range(0, len(sampled_papers), args.batch_size):
        batches.append(sampled_papers[i:i + args.batch_size])

    print(f"\n📦 Created {len(batches)} batches of ~{args.batch_size} papers each")

    # Analyze batches
    print(f"\n🤖 Analyzing with Gemini 2.5 Pro API...\n")
    all_results = []
    successful = 0

    for i, batch in enumerate(batches, 1):
        result = analyze_batch_with_gemini(batch, args.model_name, i, len(batches))
        all_results.append(result)
        if result:
            successful += 1

        # Rate limiting - be gentle with API
        if i < len(batches):
            time.sleep(2)

    print(f"\n   Successfully analyzed: {successful}/{len(batches)} batches ({100*successful/len(batches):.0f}%)")

    # Aggregate results
    print("\n📊 Aggregating evidence...")
    aggregated = aggregate_evidence(all_results)

    # Calculate final scores
    print("🧮 Calculating final scores...")
    final_scores = calculate_final_scores(aggregated)

    # Generate report
    script_dir = Path(__file__).parent
    if args.output:
        output_path = args.output
        if not output_path.startswith('/'):
            output_path = str(script_dir / output_path)
    else:
        output_path = str(script_dir / f"{args.model_name}_LLM_Capability_Assessment.md")

    generate_report(args.model_name, final_scores, len(papers), len(sampled_papers), output_path)

    # Also save raw scores as JSON
    json_output = output_path.replace('.md', '.json')
    with open(json_output, 'w') as f:
        json.dump({
            "model_name": args.model_name,
            "assessment_date": datetime.now().isoformat(),
            "total_papers": len(papers),
            "sample_size": len(sampled_papers),
            "batches_successful": successful,
            "batches_total": len(batches),
            "scores": final_scores,
            "aggregated_evidence": {k: {"evidence_count": len(v["all_evidence"]), "vote_count": len(v["level_votes"])} for k, v in aggregated.items()}
        }, f, indent=2)
    print(f"✓ Raw scores saved to: {json_output}")

    # Print summary
    print("\n" + "="*60)
    print("CAPABILITY ASSESSMENT SUMMARY")
    print("="*60 + "\n")

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        name = MCL_DIMENSIONS[mcl_id]["name"]
        score = data["score"]
        filled = int(score * 10)
        bar = "█" * filled + "░" * (30 - filled)
        print(f"{mcl_id}: {name:35} [{bar}] {score:.2f}")

    overall = sum(d["score"] for d in final_scores.values()) / 14
    print("\n" + "="*60)
    print(f"OVERALL SCORE: {overall:.2f} / 3.0")
    print("="*60)


if __name__ == "__main__":
    main()
