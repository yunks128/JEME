#!/usr/bin/env python3
"""
LLM-Based Model Capability Level Analyzer v2.0

Improvements over v1:
1. Categorical scoring (Not Assessed / Low / Moderate / High / Very High)
2. Better evidence filtering to avoid contamination from non-target model citations
3. Expert override support
4. N/A applicability flags for non-applicable metrics
5. Clearer metric definitions

Uses Google Gemini API for contextual analysis of citation papers.
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

# Categorical scoring system
SCORE_CATEGORIES = {
    "NOT_ASSESSED": {"label": "Not Assessed", "numeric_range": (None, None), "symbol": "⚪"},
    "NOT_APPLICABLE": {"label": "N/A", "numeric_range": (None, None), "symbol": "➖"},
    "LOW": {"label": "Low", "numeric_range": (0, 1), "symbol": "🔴"},
    "MODERATE": {"label": "Moderate", "numeric_range": (1, 2), "symbol": "🟡"},
    "HIGH": {"label": "High", "numeric_range": (2, 2.5), "symbol": "🟢"},
    "VERY_HIGH": {"label": "Very High", "numeric_range": (2.5, 3), "symbol": "🔵"}
}

def numeric_to_category(score):
    """Convert numeric score (0-3) to categorical rating."""
    if score is None:
        return "NOT_ASSESSED"
    if score >= 2.5:
        return "VERY_HIGH"
    elif score >= 2.0:
        return "HIGH"
    elif score >= 1.0:
        return "MODERATE"
    else:
        return "LOW"

# MCL Dimensions with IMPROVED descriptions for clearer assessment
MCL_DIMENSIONS = {
    "MCL-1": {
        "name": "Process Representation",
        "description": "Accuracy and completeness of modeled physical processes",
        "definition": """
        Measures the sophistication of physical/biogeochemical processes represented in the model itself.

        For ocean models: turbulence, advection, convection, mixed layer dynamics, sea ice thermodynamics/dynamics,
        biogeochemistry, air-sea fluxes, etc.

        Level definitions:
        - LOW: Highly simplified processes, basic parameterizations only
        - MODERATE: Multiple processes with some validated parameterizations
        - HIGH: Comprehensive process suite with validated interactions
        - VERY HIGH: State-of-the-art physics, cutting-edge parameterizations
        """,
        "indicators": [
            "Physical processes represented (turbulence, advection, convection)",
            "Parameterization sophistication (sea ice, mixed layer, biogeochemistry)",
            "Process interaction complexity (air-sea, ice-ocean coupling)",
            "Validation against theoretical benchmarks"
        ],
        "levels": {
            "LOW": "Highly simplified processes, basic parameterizations",
            "MODERATE": "Moderate complexity with some validated parameterizations",
            "HIGH": "Comprehensive process representation with validated interactions",
            "VERY_HIGH": "State-of-the-art physics with cutting-edge parameterizations"
        }
    },
    "MCL-2": {
        "name": "Spatial Resolution",
        "description": "Ability to resolve relevant spatial scales",
        "definition": """
        Measures the range of spatial scales the model can resolve.

        Scale categories for ocean models:
        - Coarse: >1 degree (~100km+)
        - Eddy-permitting: 1/4 to 1 degree (~25-100km)
        - Eddy-resolving: 1/10 to 1/4 degree (~10-25km)
        - Submesoscale-permitting: 1/48 to 1/10 degree (~2-10km)
        - Submesoscale-resolving: <1/48 degree (<2km)

        Level definitions:
        - LOW: Single resolution, coarse only (>50km)
        - MODERATE: Multiple resolutions available, eddy-permitting to eddy-resolving
        - HIGH: Eddy-resolving to submesoscale-permitting capability
        - VERY HIGH: Full range from global to submesoscale (<2km) demonstrated
        """,
        "indicators": [
            "Resolution range (degrees, km)",
            "Grid types (structured, unstructured, nested)",
            "Regional vs global capability",
            "Demonstrated submesoscale capability"
        ],
        "levels": {
            "LOW": "Coarse resolution only (>50km)",
            "MODERATE": "Eddy-permitting to eddy-resolving (10-100km)",
            "HIGH": "Submesoscale-permitting capability (2-10km)",
            "VERY_HIGH": "Global submesoscale-resolving capability (<2km)"
        }
    },
    "MCL-3": {
        "name": "Temporal Resolution",
        "description": "Frequency of outputs relevant to prediction needs",
        "definition": """
        Measures the range of temporal scales the model can represent.

        Scale categories:
        - Sub-daily: hourly or higher frequency
        - Daily to weekly
        - Monthly to seasonal
        - Interannual to decadal
        - Multi-decadal to centennial

        Level definitions:
        - LOW: Single time scale only (e.g., monthly means only)
        - MODERATE: 2-3 time scales (e.g., daily to seasonal)
        - HIGH: Most relevant time scales (sub-daily to decadal)
        - VERY HIGH: Full spectrum from sub-daily to multi-decadal with consistent physics
        """,
        "indicators": [
            "Output frequency range",
            "Time-stepping capabilities",
            "Record length produced",
            "Temporal consistency across scales"
        ],
        "levels": {
            "LOW": "Single time scale only",
            "MODERATE": "Multiple time scales (daily to seasonal)",
            "HIGH": "Broad range (sub-daily to decadal)",
            "VERY_HIGH": "Full spectrum with consistent physics across all scales"
        }
    },
    "MCL-4": {
        "name": "Process Coupling Sophistication",
        "description": "Number and fidelity of coupled model components",
        "definition": """
        Measures how many Earth system components are coupled and the coupling fidelity.

        Components for ocean-focused systems:
        - Ocean circulation
        - Sea ice (thermodynamic + dynamic)
        - Biogeochemistry
        - Ice sheets/glaciers
        - Atmosphere
        - Waves

        Level definitions:
        - LOW: Single component, uncoupled
        - MODERATE: 2 components coupled (e.g., ocean + sea ice)
        - HIGH: 3-4 components with validated coupling
        - VERY HIGH: 5+ components OR fully coupled Earth System Model
        """,
        "indicators": [
            "Number of coupled components",
            "Coupling frequency (synchronous vs asynchronous)",
            "Two-way vs one-way coupling",
            "Conservation across interfaces"
        ],
        "levels": {
            "LOW": "Uncoupled, single-component model",
            "MODERATE": "2 components coupled (e.g., ocean + sea ice)",
            "HIGH": "3-4 components with validated coupling",
            "VERY_HIGH": "5+ components or fully coupled ESM"
        }
    },
    "MCL-5": {
        "name": "Predictive Skill",
        "description": "Ability to simulate and predict observed variability",
        "definition": """
        Measures forecast/prediction capability and demonstrated skill.

        NOTE: This metric may be N/A for:
        - Reanalysis/state estimation systems (retrospective only)
        - Nature run simulations
        - Historical reconstructions

        For such systems, consider assessing "Reconstruction Skill" instead.

        Level definitions:
        - N/A: System is not designed for prediction (reanalysis, nature runs)
        - LOW: Limited prediction use, no skill assessment
        - MODERATE: Routine prediction use in limited settings
        - HIGH: Demonstrated skill in multiple prediction contexts
        - VERY HIGH: Operational prediction with comprehensive skill assessment
        """,
        "indicators": [
            "Operational prediction usage",
            "Skill scores (RMSE, correlation, bias)",
            "Ensemble forecasting capability",
            "Lead time range"
        ],
        "levels": {
            "NOT_APPLICABLE": "System is retrospective analysis, not designed for prediction",
            "LOW": "Limited prediction use, no skill assessment",
            "MODERATE": "Routine use for prediction in limited settings",
            "HIGH": "Demonstrated skill in multiple prediction contexts",
            "VERY_HIGH": "Operational prediction with comprehensive skill metrics"
        }
    },
    "MCL-6": {
        "name": "Computational Performance",
        "description": "Scalability on HPC, cloud, or exascale architectures",
        "definition": """
        Measures computational scalability and performance optimization.

        Level definitions:
        - LOW: Desktop/workstation only, limited parallelism
        - MODERATE: HPC scalable (MPI), thousands of cores
        - HIGH: Multi-architecture (HPC + GPU acceleration)
        - VERY HIGH: Exascale-ready, demonstrated at 100K+ cores, GPU-native

        Note: Being one of few codes capable of global O(100m) resolution is VERY HIGH.
        """,
        "indicators": [
            "Parallel scaling (MPI, OpenMP)",
            "GPU acceleration",
            "Maximum demonstrated core count",
            "Efficiency at scale"
        ],
        "levels": {
            "LOW": "Limited to small systems, poor scaling",
            "MODERATE": "HPC scalable, demonstrated at 1000s of cores",
            "HIGH": "Multi-architecture support, GPU acceleration",
            "VERY_HIGH": "Exascale-ready, demonstrated at 100K+ cores"
        }
    },
    "MCL-7": {
        "name": "Observational Constraint",
        "description": "Degree of observational constraint on model state/parameters",
        "definition": """
        Measures the extent of data assimilation / observational constraint.

        Observation types:
        - Satellite: altimetry, SST, SSS, GRACE, ice extent/thickness
        - In-situ: Argo, moorings, CTD, XBT
        - Airborne: campaigns

        Level definitions:
        - LOW: No or minimal observational constraint
        - MODERATE: Single observation type assimilated
        - HIGH: Multiple satellite + some in-situ
        - VERY HIGH: Comprehensive multi-source (satellite + in-situ + derived), billions of observations
        """,
        "indicators": [
            "Observation types assimilated",
            "Data assimilation method",
            "Observation count/coverage",
            "Constraint on model parameters vs state"
        ],
        "levels": {
            "LOW": "No or minimal observational constraints",
            "MODERATE": "Single observation type assimilated",
            "HIGH": "Multiple satellite and in-situ sources",
            "VERY_HIGH": "Comprehensive multi-source constraint (~10^9 observations)"
        }
    },
    "MCL-8": {
        "name": "Retrospective Analysis",
        "description": "Use of data assimilation for long-term record generation",
        "definition": """
        Measures reanalysis/state estimation capability.

        Level definitions:
        - LOW: No retrospective analysis capability
        - MODERATE: DA for bias correction or short records (<10 years)
        - HIGH: Multi-decadal reanalysis with multiple data types
        - VERY HIGH: Coupled, fully integrated, benchmarked reanalysis products spanning 30+ years
        """,
        "indicators": [
            "Reanalysis product availability",
            "Record length and consistency",
            "DA methodology (4D-Var, Kalman, adjoint)",
            "Comparison with established products"
        ],
        "levels": {
            "LOW": "No retrospective analysis capability",
            "MODERATE": "Limited DA or short records (<10 years)",
            "HIGH": "Multi-decadal reanalysis available",
            "VERY_HIGH": "Coupled, benchmarked reanalysis products (30+ years)"
        }
    },
    "MCL-9": {
        "name": "Uncertainty Quantification",
        "description": "Capability to assess uncertainty propagation and sensitivity",
        "definition": """
        Measures UQ methodology and implementation.

        Level definitions:
        - LOW: No formal UQ
        - MODERATE: Basic sensitivity analysis or small ensembles
        - HIGH: Formal UQ for ICs, parameters, or forcing
        - VERY HIGH: Comprehensive probabilistic framework with full error attribution
        """,
        "indicators": [
            "Ensemble methods and size",
            "Sensitivity analysis capability",
            "Error propagation quantification",
            "Probabilistic output products"
        ],
        "levels": {
            "LOW": "No uncertainty quantification",
            "MODERATE": "Basic sensitivity analysis or small ensembles",
            "HIGH": "Formal UQ for ICs, parameters, or forcing",
            "VERY_HIGH": "Comprehensive probabilistic framework"
        }
    },
    "MCL-10": {
        "name": "Verification & Validation",
        "description": "Robustness of model evaluation methods",
        "definition": """
        Measures V&V rigor and comprehensiveness.

        Level definitions:
        - LOW: Minimal validation
        - MODERATE: Validation against limited datasets
        - HIGH: Routine validation against multiple independent datasets
        - VERY HIGH: Continuous/systematic validation, model intercomparison participation

        Note: Systems with continuous V&V against billions of observations are VERY HIGH.
        """,
        "indicators": [
            "Independent validation datasets",
            "Model intercomparison participation (CMIP, OMIP)",
            "Systematic benchmarking",
            "Continuous validation processes"
        ],
        "levels": {
            "LOW": "Minimal validation efforts",
            "MODERATE": "Validation against limited datasets",
            "HIGH": "Routine validation against multiple datasets",
            "VERY_HIGH": "Continuous systematic validation (~10^9 observations)"
        }
    },
    "MCL-11": {
        "name": "ML/AI Integration",
        "description": "Use of ML/AI for process emulation, bias correction, data fusion",
        "definition": """
        Measures ML/AI adoption in modeling workflows.

        Level definitions:
        - LOW: No ML/AI integration
        - MODERATE: ML tested for limited applications
        - HIGH: ML extensively used for specific tasks (emulation, bias correction)
        - VERY HIGH: ML fully integrated into core modeling workflows
        """,
        "indicators": [
            "ML algorithms implemented",
            "Neural network emulators",
            "Integration into core workflows",
            "ML-based data products"
        ],
        "levels": {
            "LOW": "No ML/AI integration",
            "MODERATE": "ML tested for limited applications",
            "HIGH": "ML extensively used for specific tasks",
            "VERY_HIGH": "ML fully integrated into core workflows"
        }
    },
    "MCL-12": {
        "name": "Future Mission Support",
        "description": "Role in satellite mission formulation and observational strategies",
        "definition": """
        Measures contribution to satellite mission planning and OSSEs.

        Level definitions:
        - LOW: No mission support
        - MODERATE: Products used to support mission formulation
        - HIGH: Forward models for specific missions
        - VERY HIGH: Key contributor to OSSEs, multiple mission support
        """,
        "indicators": [
            "OSSE capabilities",
            "Mission support (GRACE, SWOT, etc.)",
            "Synthetic observation generation",
            "Observing system design contributions"
        ],
        "levels": {
            "LOW": "No mission support capability",
            "MODERATE": "Products used to support mission formulation",
            "HIGH": "Forward models for specific missions",
            "VERY_HIGH": "Key OSSE contributor, multiple mission support"
        }
    },
    "MCL-13": {
        "name": "Interoperability & Open Science",
        "description": "Community accessibility and compatibility with adjacent tools",
        "definition": """
        Measures openness, accessibility, and standards compliance.

        Level definitions:
        - LOW: Proprietary, core developers only
        - MODERATE: Available to institution + partners
        - HIGH: Open source with some community adoption
        - VERY HIGH: Fully open source, CF/ACDD compliant, active community

        Note: 100% open source with mandated CF/ACDD compliance = VERY HIGH
        """,
        "indicators": [
            "Open source status",
            "Standards compliance (CF, ACDD)",
            "API/interface standardization",
            "Community adoption metrics"
        ],
        "levels": {
            "LOW": "Proprietary, core developers only",
            "MODERATE": "Available to institution + external partners",
            "HIGH": "Open source with community adoption",
            "VERY_HIGH": "Fully open source, CF/ACDD compliant, active community"
        }
    },
    "MCL-14": {
        "name": "Stakeholder & Decision Support",
        "description": "Use in real-world decision-making processes",
        "definition": """
        Measures operational and policy applications.

        Level definitions:
        - LOW: Research only
        - MODERATE: Tested in limited applications
        - HIGH: Broadly used for specific applications
        - VERY HIGH: Critical tool for operational decision-makers
        """,
        "indicators": [
            "Operational agency usage",
            "Policy applications",
            "Decision support tools",
            "Stakeholder engagement"
        ],
        "levels": {
            "LOW": "Research only, no operational applications",
            "MODERATE": "Tested in limited applications",
            "HIGH": "Broadly used for specific applications",
            "VERY_HIGH": "Critical tool for operational decision-makers"
        }
    }
}


def load_expert_overrides(override_path):
    """Load expert override file if it exists."""
    if override_path and Path(override_path).exists():
        with open(override_path) as f:
            return json.load(f)
    return None


def create_analysis_prompt(papers_batch, model_name):
    """Create an IMPROVED prompt that filters for model-specific evidence."""

    prompt = f"""Analyze these papers for evidence about the **{model_name}** model SPECIFICALLY.

CRITICAL: Only extract evidence that is DIRECTLY about {model_name} itself, NOT about:
- Other models mentioned in the paper (ADCIRC, SWAN, CICE standalone, CESM, etc.)
- Generic statements about modeling
- Methods used on data derived from {model_name}

## Dimensions to assess (categorical: LOW/MODERATE/HIGH/VERY_HIGH or N/A):

MCL-1: Process Representation - Physical/biogeochemical processes IN {model_name}
MCL-2: Spatial Resolution - Resolution capabilities OF {model_name}
MCL-3: Temporal Resolution - Time scales covered BY {model_name}
MCL-4: Process Coupling - Components coupled IN {model_name}
MCL-5: Predictive Skill - Forecast ability OF {model_name} (N/A if reanalysis only)
MCL-6: Computational Performance - HPC/GPU capabilities OF {model_name} code
MCL-7: Observational Constraint - Data assimilated INTO {model_name}
MCL-8: Retrospective Analysis - Reanalysis products FROM {model_name}
MCL-9: Uncertainty Quantification - UQ methods IN {model_name}
MCL-10: Verification & Validation - V&V performed ON {model_name}
MCL-11: ML/AI Integration - ML used IN {model_name}
MCL-12: Future Mission Support - Mission support BY {model_name}
MCL-13: Interoperability - Open science status OF {model_name}
MCL-14: Decision Support - Operational use OF {model_name}

## Papers:
"""

    for i, paper in enumerate(papers_batch, 1):
        title = paper.get('title', 'Unknown')[:120]
        abstract = paper.get('abstract', '')[:600]
        year = paper.get('year', 'N/A')
        domain = paper.get('research_domain', 'Unknown')

        prompt += f"""
[{i}] {title} ({year}, {domain})
{abstract}
"""

    prompt += f"""

## Output JSON format:
{{
  "MCL-1": {{"evidence": ["specific evidence about {model_name}"], "category": "HIGH", "papers": [1]}},
  ...
}}

RULES:
1. evidence strings MUST be about {model_name} specifically, not other models
2. category must be: "LOW", "MODERATE", "HIGH", "VERY_HIGH", or "N/A"
3. Use empty arrays [] and "NOT_ASSESSED" if no {model_name}-specific evidence
4. Keep evidence under 50 words each
5. Return ONLY valid JSON"""

    return prompt


def analyze_batch_with_gemini(papers_batch, model_name, batch_num, total_batches, max_retries=3):
    """Send a batch of papers to Gemini for analysis with retry logic."""

    model = genai.GenerativeModel('gemini-2.0-flash')
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

    groups = defaultdict(list)
    for paper in papers:
        domain = paper.get('research_domain', 'Unknown')
        engagement = paper.get('engagement_level', 'Unknown')
        key = (domain, engagement)
        groups[key].append(paper)

    total_groups = len(groups)
    base_per_group = max(1, sample_size // total_groups)

    sampled = []
    for key, group_papers in groups.items():
        with_abstract = [p for p in group_papers if p.get('abstract')]
        without_abstract = [p for p in group_papers if not p.get('abstract')]

        n_to_sample = min(base_per_group, len(with_abstract))
        if n_to_sample > 0:
            sampled.extend(random.sample(with_abstract, n_to_sample))

        remaining = base_per_group - n_to_sample
        if remaining > 0 and without_abstract:
            n_extra = min(remaining, len(without_abstract))
            sampled.extend(random.sample(without_abstract, n_extra))

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
            "category_votes": [],
            "paper_count": 0
        }

    category_to_numeric = {
        "NOT_ASSESSED": None,
        "NOT_APPLICABLE": None,
        "N/A": None,
        "LOW": 0.5,
        "MODERATE": 1.5,
        "HIGH": 2.25,
        "VERY_HIGH": 2.75
    }

    for batch_result in all_batch_results:
        if batch_result is None:
            continue

        for mcl_id in MCL_DIMENSIONS.keys():
            if mcl_id in batch_result:
                mcl_data = batch_result[mcl_id]

                evidence = mcl_data.get('evidence', [])
                if isinstance(evidence, list):
                    aggregated[mcl_id]["all_evidence"].extend(evidence)

                # Handle category votes
                category = mcl_data.get('category', 'NOT_ASSESSED')
                if category and category.upper() in category_to_numeric:
                    aggregated[mcl_id]["category_votes"].append(category.upper())

                # Handle legacy numeric levels
                levels = mcl_data.get('levels', [])
                if isinstance(levels, list):
                    for l in levels:
                        if isinstance(l, (int, float)):
                            cat = numeric_to_category(l)
                            aggregated[mcl_id]["category_votes"].append(cat)

                refs = mcl_data.get('papers', [])
                if isinstance(refs, list):
                    aggregated[mcl_id]["paper_count"] += len(refs)

    return aggregated


def calculate_final_scores(aggregated_evidence, expert_overrides=None):
    """Calculate final MCL scores from aggregated evidence, with expert override support."""

    final_scores = {}

    # Category voting weights
    category_weights = {
        "LOW": 1,
        "MODERATE": 2,
        "HIGH": 3,
        "VERY_HIGH": 4,
        "NOT_APPLICABLE": None,
        "NOT_ASSESSED": None
    }

    for mcl_id, data in aggregated_evidence.items():
        votes = [v for v in data["category_votes"] if v in ["LOW", "MODERATE", "HIGH", "VERY_HIGH"]]
        evidence = data["all_evidence"]

        # Check for expert override first
        if expert_overrides and mcl_id in expert_overrides.get("overrides", {}):
            override = expert_overrides["overrides"][mcl_id]
            final_category = override["category"]
            override_reason = override.get("reason", "Expert assessment")
            override_evidence = override.get("evidence", [])

            final_scores[mcl_id] = {
                "category": final_category,
                "category_label": SCORE_CATEGORIES.get(final_category, {}).get("label", final_category),
                "evidence_count": len(evidence),
                "vote_count": len(votes),
                "top_evidence": override_evidence if override_evidence else list(dict.fromkeys(evidence))[:5],
                "level_description": MCL_DIMENSIONS[mcl_id]["levels"].get(final_category, ""),
                "expert_override": True,
                "override_reason": override_reason
            }
            continue

        # Check for N/A votes
        na_votes = [v for v in data["category_votes"] if v in ["NOT_APPLICABLE", "N/A"]]
        if len(na_votes) > len(votes) / 2 and len(na_votes) > 2:
            final_category = "NOT_APPLICABLE"
        elif votes:
            # Weighted voting
            vote_sum = sum(category_weights[v] for v in votes)
            vote_avg = vote_sum / len(votes)

            if vote_avg >= 3.5:
                final_category = "VERY_HIGH"
            elif vote_avg >= 2.5:
                final_category = "HIGH"
            elif vote_avg >= 1.5:
                final_category = "MODERATE"
            else:
                final_category = "LOW"
        else:
            final_category = "NOT_ASSESSED"

        unique_evidence = list(dict.fromkeys(evidence))[:10]

        final_scores[mcl_id] = {
            "category": final_category,
            "category_label": SCORE_CATEGORIES.get(final_category, {}).get("label", final_category),
            "evidence_count": len(evidence),
            "vote_count": len(votes),
            "top_evidence": unique_evidence,
            "level_description": MCL_DIMENSIONS[mcl_id]["levels"].get(final_category, ""),
            "expert_override": False
        }

    return final_scores


def generate_report(model_name, final_scores, total_papers, sample_size, output_path, expert_overrides=None):
    """Generate markdown report from final scores using categorical ratings."""

    report = f"""# {model_name} Model Capability Level Assessment
## Categorical Assessment Report (v2.0)

**Assessment Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Methodology**: Gemini LLM-based contextual analysis with categorical scoring
**Total Papers in Dataset**: {total_papers:,}
**Papers Analyzed (Stratified Sample)**: {sample_size}
"""

    if expert_overrides:
        report += f"""**Expert Overrides Applied**: Yes ({len(expert_overrides.get('overrides', {}))} dimensions)
**Expert**: {expert_overrides.get('expert_name', 'Anonymous')}

> ⚠️ **Note on Expert Overrides**: Expert overrides in this report represent domain expert feedback
> that has been interpreted and structured by an LLM (Claude). They are a **combination of expert
> knowledge + LLM interpretation**, not direct expert-authored assessments. For authoritative
> assessments, the expert override file should be reviewed and edited directly by domain experts.
"""

    report += f"""
---

## Assessment Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              📥 INPUTS                                      │
├─────────────────────┬─────────────────────┬─────────────────────────────────┤
│  📄 {model_name} Citation    │  📋 MCL Framework     │  👤 Expert Feedback           │
│  Papers             │  (14 Capability     │  (Domain Knowledge)           │
│  ({total_papers:,} papers)   │   Dimensions)        │                               │
└──────────┬──────────┴──────────┬──────────┴───────────────┬───────────────────┘
           │                     │                          │
           ▼                     ▼                          ▼
┌─────────────────────────────────────────┐  ┌─────────────────────────────────┐
│         🤖 LLM ANALYSIS (Gemini)        │  │      👨‍🔬 EXPERT REVIEW            │
├─────────────────────────────────────────┤  ├─────────────────────────────────┤
│  1. Stratified Sampling                 │  │  1. Override Incorrect          │
│     ({sample_size} papers across domains)        │  │     LLM Assessments             │
│                                         │  │                                 │
│  2. Evidence Extraction                 │  │  2. Add Authoritative           │
│     ({model_name}-specific filtering)          │  │     Evidence                    │
│                                         │  │                                 │
│  3. Categorical Classification          │  │  3. Mark N/A for                │
│     (Low/Moderate/High/Very High)       │  │     Non-applicable Metrics      │
└──────────────────┬──────────────────────┘  └───────────────┬─────────────────┘
                   │                                         │
                   └──────────────────┬──────────────────────┘
                                      ▼
                   ┌─────────────────────────────────────────┐
                   │            📊 OUTPUT                    │
                   ├─────────────────────────────────────────┤
                   │     Combined Assessment (LLM + Expert)  │
                   │                  ▼                      │
                   │       📑 {model_name} Capability Report        │
                   └─────────────────────────────────────────┘
```

---

## Scoring System

This assessment uses **categorical ratings** rather than false-precision numeric scores:

| Category | Symbol | Description |
|----------|--------|-------------|
| **Very High** | 🔵 | State-of-the-art, comprehensive capability |
| **High** | 🟢 | Strong capability with validated approaches |
| **Moderate** | 🟡 | Functional capability with limitations |
| **Low** | 🔴 | Basic or limited capability |
| **N/A** | ➖ | Not applicable to this model type |
| **Not Assessed** | ⚪ | Insufficient evidence to assess |

---

## Executive Summary

"""

    # Count categories
    counts = defaultdict(int)
    for data in final_scores.values():
        counts[data["category"]] += 1

    # Determine overall maturity
    high_count = counts.get("VERY_HIGH", 0) + counts.get("HIGH", 0)
    if high_count >= 10:
        maturity = "**Mature Capability** - Operational Readiness"
    elif high_count >= 6:
        maturity = "**Advanced Development** - Near Operational"
    elif high_count >= 3:
        maturity = "**Intermediate Development** - Transitioning to Applications"
    else:
        maturity = "**Early Development** - Research-Focused"

    report += f"""### Overall Maturity: {maturity}

| Category | Count |
|----------|-------|
| 🔵 Very High | {counts.get("VERY_HIGH", 0)} |
| 🟢 High | {counts.get("HIGH", 0)} |
| 🟡 Moderate | {counts.get("MODERATE", 0)} |
| 🔴 Low | {counts.get("LOW", 0)} |
| ➖ N/A | {counts.get("NOT_APPLICABLE", 0)} |
| ⚪ Not Assessed | {counts.get("NOT_ASSESSED", 0)} |

---

## Capability Summary

| Dimension | Rating | Evidence | Notes |
|-----------|--------|----------|-------|
"""

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        name = MCL_DIMENSIONS[mcl_id]["name"]
        category = data["category"]
        symbol = SCORE_CATEGORIES.get(category, {}).get("symbol", "⚪")
        label = data["category_label"]

        # Show correct evidence count for expert overrides
        if data.get("expert_override"):
            evidence_count = len(data.get("top_evidence", []))
            notes = data.get('override_reason', '')
        else:
            evidence_count = data["evidence_count"]
            notes = data["level_description"] if data.get("level_description") else ""

        report += f"| {mcl_id}: {name} | {symbol} **{label}** | {evidence_count} | {notes} |\n"

    report += "\n---\n\n## Detailed Dimension Analysis\n\n"

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        mcl_info = MCL_DIMENSIONS[mcl_id]
        category = data["category"]
        symbol = SCORE_CATEGORIES.get(category, {}).get("symbol", "⚪")
        label = data["category_label"]

        report += f"""### {mcl_id}: {mcl_info['name']}

**Rating**: {symbol} **{label}**
"""

        if data.get("expert_override"):
            report += f"""
> ⚠️ **Expert Override Applied** (Expert feedback + LLM interpretation)
> Reason: {data.get('override_reason', 'Expert assessment')}
"""

        report += f"""
**Definition**: {mcl_info['description']}

**Level Criteria**:
"""
        for level, desc in mcl_info['levels'].items():
            level_symbol = SCORE_CATEGORIES.get(level, {}).get("symbol", "")
            marker = "→" if level == category else " "
            report += f"- {marker} {level_symbol} **{level}**: {desc}\n"

        # Show evidence count correctly for expert overrides
        if data.get("expert_override"):
            evidence_list = data['top_evidence']
            report += f"""
**Evidence**:
"""
        else:
            evidence_list = data['top_evidence']
            report += f"""
**Evidence** ({data['evidence_count']} items from {data['vote_count']} LLM assessments):
"""
        if evidence_list:
            for i, evidence in enumerate(evidence_list[:5], 1):
                report += f"{i}. {evidence}\n"
        else:
            report += "*No specific evidence extracted*\n"

        report += "\n---\n\n"

    # Strengths and gaps
    very_high = [(k, v) for k, v in final_scores.items() if v["category"] == "VERY_HIGH"]
    high = [(k, v) for k, v in final_scores.items() if v["category"] == "HIGH"]
    low_moderate = [(k, v) for k, v in final_scores.items() if v["category"] in ["LOW", "MODERATE"]]

    report += """## Capability Assessment

### Core Strengths (Very High / High)

"""
    for mcl_id, data in very_high + high:
        symbol = SCORE_CATEGORIES.get(data["category"], {}).get("symbol", "")
        report += f"- {symbol} **{MCL_DIMENSIONS[mcl_id]['name']}**: {data['level_description']}\n"

    if low_moderate:
        report += """
### Development Opportunities (Low / Moderate)

"""
        for mcl_id, data in low_moderate:
            symbol = SCORE_CATEGORIES.get(data["category"], {}).get("symbol", "")
            report += f"- {symbol} **{MCL_DIMENSIONS[mcl_id]['name']}**: {data['level_description']}\n"

    report += f"""
---

## Methodology

This assessment uses **categorical scoring** to avoid false precision.

### Approach:
1. **Categorical ratings** instead of decimal scores (2.31 → "High")
2. **Evidence filtering** - extracts evidence about {model_name} specifically
3. **Expert override support** - domain experts can correct assessments
4. **N/A handling** - metrics can be marked non-applicable

### Limitations:
- Sample-based analysis (not all papers reviewed)
- LLM interpretation may vary between runs
- Evidence quality depends on paper abstracts
"""

    with open(output_path, 'w') as f:
        f.write(report)

    print(f"\n✓ Report saved to: {output_path}")
    return report


def main():
    """Main analysis pipeline."""

    import argparse
    parser = argparse.ArgumentParser(description='LLM-based Model Capability Analyzer v2.0')
    parser.add_argument('input_file', help='Path to JSON file with citation data')
    parser.add_argument('--model-name', default='ECCO', help='Name of the model being analyzed')
    parser.add_argument('--sample-size', type=int, default=200, help='Number of papers to sample')
    parser.add_argument('--batch-size', type=int, default=5, help='Papers per LLM batch')
    parser.add_argument('--output', default=None, help='Output report path')
    parser.add_argument('--expert-overrides', default=None, help='Path to expert override JSON file')

    args = parser.parse_args()

    print("="*60)
    print("LLM-BASED MODEL CAPABILITY ANALYZER v2.0")
    print("(Categorical Scoring with Expert Override Support)")
    print("="*60)

    # Load expert overrides
    expert_overrides = None
    if args.expert_overrides:
        expert_overrides = load_expert_overrides(args.expert_overrides)
        if expert_overrides:
            print(f"\n✓ Loaded expert overrides from {args.expert_overrides}")
            print(f"  Expert: {expert_overrides.get('expert_name', 'Anonymous')}")
            print(f"  Overrides: {len(expert_overrides.get('overrides', {}))} dimensions")

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
    print(f"\n🤖 Analyzing with Gemini API...\n")
    all_results = []
    successful = 0

    for i, batch in enumerate(batches, 1):
        result = analyze_batch_with_gemini(batch, args.model_name, i, len(batches))
        all_results.append(result)
        if result:
            successful += 1

        if i < len(batches):
            time.sleep(1.5)

    print(f"\n   Successfully analyzed: {successful}/{len(batches)} batches ({100*successful/len(batches):.0f}%)")

    # Aggregate results
    print("\n📊 Aggregating evidence...")
    aggregated = aggregate_evidence(all_results)

    # Calculate final scores with expert overrides
    print("🧮 Calculating final categorical scores...")
    final_scores = calculate_final_scores(aggregated, expert_overrides)

    # Generate report
    script_dir = Path(__file__).parent
    if args.output:
        output_path = args.output
        if not output_path.startswith('/'):
            output_path = str(script_dir / output_path)
    else:
        output_path = str(script_dir / f"{args.model_name}_Capability_Assessment_v2.md")

    generate_report(model_name=args.model_name,
                   final_scores=final_scores,
                   total_papers=len(papers),
                   sample_size=len(sampled_papers),
                   output_path=output_path,
                   expert_overrides=expert_overrides)

    # Save raw data as JSON
    json_output = output_path.replace('.md', '.json')
    with open(json_output, 'w') as f:
        json.dump({
            "model_name": args.model_name,
            "assessment_date": datetime.now().isoformat(),
            "version": "2.0",
            "scoring_type": "categorical",
            "total_papers": len(papers),
            "sample_size": len(sampled_papers),
            "batches_successful": successful,
            "batches_total": len(batches),
            "expert_overrides_applied": expert_overrides is not None,
            "scores": final_scores
        }, f, indent=2)
    print(f"✓ Raw scores saved to: {json_output}")

    # Print summary
    print("\n" + "="*60)
    print("CAPABILITY ASSESSMENT SUMMARY (Categorical)")
    print("="*60 + "\n")

    for mcl_id in sorted(final_scores.keys(), key=lambda x: int(x.split('-')[1])):
        data = final_scores[mcl_id]
        name = MCL_DIMENSIONS[mcl_id]["name"]
        category = data["category"]
        symbol = SCORE_CATEGORIES.get(category, {}).get("symbol", "⚪")
        label = data["category_label"]
        override = " [EXPERT]" if data.get("expert_override") else ""
        print(f"{mcl_id}: {name:35} {symbol} {label:12}{override}")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
