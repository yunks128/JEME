# Diego's Core Model Capability Levels (MCL) Framework
## Framework Definition Document

**Version**: 1.0
**Date**: January 7, 2026
**Author**: Diego

---

## 1. Executive Summary

The Core Model Capability Levels (MCL) framework provides a standardized method to assess the technical and scientific maturity of high-fidelity models. By shifting away from qualitative "labels" (such as "Machine Learning based"), the MCL provides a "Maturity Profile" that identifies specific strengths and gaps in a model's predictive credibility and operational readiness.

---

## 2. Design Philosophy & Framework Integration

The MCL is a synthesis of two established benchmarks, adapted for the unique needs of scientific modeling.

### A. NASA Technology Readiness Level (TRL)
- **The Frame**: TRL focuses on **Readiness** and deployment status
- **Integration**: Utilized the TRL concept of "Environments" to define our levels (Conceptual, Operational, and State-of-the-Art)
- **Modification**: Discarded the linear 1–9 progression. Unlike hardware, software and scientific models often mature unevenly across different dimensions

### B. Sandia National Labs PCMM
- **The Frame**: PCMM focuses on **Credibility** and V&V (Verification and Validation)
- **Integration**: Adopted the Multi-Dimensional (Radar Chart) approach. This ensures that a model's maturity is assessed across separate axes rather than a single numerical score
- **Scientific Anchor**: Adapted the PCMM "Physics Fidelity" axis to create our **Budget Closure** requirement—the definitive maturity marker for earth science models like ECCO

---

## 3. The Nine Dimensions

| # | Dimension | Scope |
|---|-----------|-------|
| 1 | Physics & Conservation | Adherence to laws of nature; budget closure |
| 2 | Data Integration | How observations combine with model logic |
| 3 | Verification | Mathematical correctness ("solved right?") |
| 4 | Validation | Predictive skill against real data ("right model?") |
| 5 | Uncertainty (UQ) | Confidence and error quantification |
| 6 | Numerical Fidelity | Resolution and boundary handling |
| 7 | Portability & Scaling | Hardware architecture performance |
| 8 | Interoperability | I/O standards and model coupling |
| 9 | Sustainability | Documentation, maintenance, community |

---

## 4. Level Definitions Matrix

### Dimension 1: Physics & Conservation

> *Evaluates adherence to laws of nature. Checks for "leaks" in the system.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | Empirical or "Nudged" physics; budgets do not close or are ignored |
| 2 | Operational / Medium | Primary physics present; global budgets monitored but not strictly enforced |
| 3 | State-of-Art / High | **Strictly Closed Budgets.** Full Adjoint/Finite Element consistency across all scales |

**Key Indicators**:
- Level 1: Nudging terms, unphysical sources/sinks
- Level 2: Budget diagnostics exist but may have residuals
- Level 3: Exact conservation verified, adjoint consistency

---

### Dimension 2: Data Integration

> *Assesses how observations are combined with model logic.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Forced**: Model is driven by data; physics may be violated at data points |
| 2 | Operational / Medium | **Sequential**: Periodic updates (e.g., Kalman Filter); results in "jumps" in state |
| 3 | State-of-Art / High | **Synthesis**: 4D-Var or MCMC. Data and physics are mathematically inseparable |

**Key Indicators**:
- Level 1: Direct forcing, data overwrites model state
- Level 2: EnKF, 3D-Var, IAU with visible discontinuities
- Level 3: 4D-Var adjoint, strong constraint, continuous trajectory

---

### Dimension 3: Verification

> *Mathematical correctness of the code. "Are equations solved right?"*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Functional**: "Code runs" without crashing; basic output looks plausible |
| 2 | Operational / Medium | **Structured**: Unit/Regression tests; grid and time-step convergence studies |
| 3 | State-of-Art / High | **Algorithmic**: Adjoint/Taylor tests for gradient accuracy; exact benchmarks |

**Key Indicators**:
- Level 1: Compiles and produces output
- Level 2: CI/CD with test suite, convergence documented
- Level 3: Taylor test verification, MMS (Method of Manufactured Solutions)

---

### Dimension 4: Validation

> *Predictive skill against real-world data. "Is this the right model?"*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Subjective**: "Eyeball" fits to training data; qualitative agreement |
| 2 | Operational / Medium | **Statistical**: Global RMSE and Bias metrics reported on known datasets |
| 3 | State-of-Art / High | **Process-Level**: Blind validation against independent, global datasets |

**Key Indicators**:
- Level 1: Visual comparison, "looks reasonable"
- Level 2: Quantitative metrics on assimilated data
- Level 3: Witheld data validation, process fidelity, blind tests

---

### Dimension 5: Uncertainty Quantification (UQ)

> *Ability to quantify confidence and error bounds.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Heuristic**: Expert judgment or arbitrary error bars (e.g., +/- 10%) |
| 2 | Operational / Medium | **Ensemble**: Sensitivity analysis; spread of multiple runs used as error proxy |
| 3 | State-of-Art / High | **Probabilistic**: Formal Bayesian UQ; posterior probability distributions |

**Key Indicators**:
- Level 1: Ad-hoc error estimates
- Level 2: Ensemble spread, adjoint sensitivities
- Level 3: MCMC posteriors, full error propagation, covariance matrices

---

### Dimension 6: Numerical Fidelity

> *Spatial/temporal resolution and boundary handling.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Coarse**: Low-resolution static grids; simplified/square boundaries |
| 2 | Operational / Medium | **Refined**: Nested grids or regional refinement; realistic topography |
| 3 | State-of-Art / High | **Dynamic**: Anisotropic mesh refinement; time-varying/moving boundaries |

**Key Indicators**:
- Level 1: Regular lat-lon, staircase boundaries
- Level 2: Partial cells, nesting, realistic bathymetry
- Level 3: Adaptive mesh, unstructured grids, moving boundaries

---

### Dimension 7: Portability & Scaling

> *Performance across different hardware architectures.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Static**: Serial code; runs only on local machines or specific hardware |
| 2 | Operational / Medium | **Parallel**: MPI/OpenMP parallelization; scales on standard HPC clusters |
| 3 | State-of-Art / High | **Architecture-Agnostic**: Cloud-native; GPU-accelerated; linear scaling |

**Key Indicators**:
- Level 1: Single processor, specific machine
- Level 2: MPI parallelization, cluster scaling
- Level 3: GPU support, cloud deployment, exascale demonstrated

---

### Dimension 8: Interoperability

> *Standards for I/O and coupling with other models.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Isolated**: Proprietary/non-standard I/O; no standard coupling interfaces |
| 2 | Operational / Medium | **Standardized**: Uses NetCDF/HDF5; basic metadata; one-off coupling (e.g., wrappers) |
| 3 | State-of-Art / High | **Plug-and-Play**: FAIR compliant (Zarr); ESMF/NUOPC compliant interfaces |

**Key Indicators**:
- Level 1: Binary output, custom formats
- Level 2: NetCDF with CF conventions
- Level 3: Zarr/cloud-optimized, ESMF coupling, full FAIR

---

### Dimension 9: Sustainability

> *Documentation, maintenance, and community health.*

| Level | Name | Criteria |
|-------|------|----------|
| 1 | Conceptual / Low | **Ad-hoc**: No version control; documentation is sparse or non-existent |
| 2 | Operational / Medium | **Maintained**: Git versioning; public repo; basic install guides and user group |
| 3 | State-of-Art / High | **Institutional**: Full CI/CD pipelines; complete developer docs; long-term roadmap |

**Key Indicators**:
- Level 1: No git, no docs
- Level 2: GitHub repo, README, user mailing list
- Level 3: CI/CD, comprehensive docs, funded roadmap, training workshops

---

## 5. Rationale for Major Decisions

### I. Algorithm Neutrality (The "ML" Decision)

We explicitly moved away from using "Machine Learning" as a qualifier or a level of maturity.

**Reasoning**: Sophistication of an algorithm does not equate to maturity of the output. In this framework, an ML-based model is judged by the same rigorous standards of Physics Fidelity and Verification as any other model.

### II. The "Budget Closure" Requirement

**Reasoning**: Inspired by models like ECCO, we determined that "State-of-Art" data integration must not result in unphysical state "jumps." True maturity is the ability to synthesize data while remaining perfectly consistent with physical laws, allowing for accurate causal and budget analysis.

### III. Software as a Science Capability

**Reasoning**: The addition of dimensions 7–9 (Portability, Interoperability, Sustainability) acknowledges that a core capability must be reproducible and accessible. If a model is physically perfect but cannot be shared, scaled, or maintained, its scientific value is severely diminished in an operational context.

### IV. Moving from "Labels" to "Profiles"

**Reasoning**: Following the PCMM philosophy, we prioritize the "Radar Chart" view. This prevents a model from being hidden behind a single average number and instead highlights exactly where investment is needed (e.g., "High Physics, Low Uncertainty Quantification").

---

## 6. Assessment Methodology

### Evidence Requirements

For each dimension level claim, assessors must provide:

1. **Paper Citation**: DOI or title of source paper
2. **Evidence Passage**: Relevant text excerpt (with page/line if available)
3. **Justification**: How the evidence maps to the level criteria

### Scoring Rules

1. **Conservative Default**: If evidence is ambiguous, default to lower level
2. **Highest Demonstrated**: Level assigned based on highest capability demonstrated (not average)
3. **Documentation Required**: Undocumented capabilities cannot be assessed

### Profile Visualization

Results should be presented as:
1. **Table**: 9 dimensions with level (1-3) and key evidence
2. **Radar Chart**: Visual representation of maturity profile
3. **Gap Analysis**: Dimensions below Level 3 with recommendations

---

## 7. Comparison with Other Frameworks

| Aspect | NASA TRL | Sandia PCMM | Diego MCL |
|--------|----------|-------------|-----------|
| Primary Focus | Hardware Readiness | Model Credibility | Scientific Model Maturity |
| Structure | Linear 1-9 | Multi-dimensional | 9 dimensions × 3 levels |
| Scientific Anchor | N/A | Physics Fidelity | Budget Closure |
| Software Dimensions | Minimal | Basic | Comprehensive (3 dims) |
| Algorithm Neutral | N/A | Yes | Yes |

---

## 8. Application Guidelines

### When to Use This Framework

- Assessing core science model maturity
- Identifying investment priorities
- Comparing similar models objectively
- Communicating model capabilities to stakeholders

### When NOT to Use This Framework

- Operational prediction system assessment (use TRL instead)
- Software quality assessment only (use software maturity models)
- Comparison of fundamentally different model types

---

## References

1. NASA Technology Readiness Levels (TRL) Definition
2. Sandia National Laboratories PCMM (Predictive Capability Maturity Model)
3. ASME V&V Standards for Computational Modeling
4. FAIR Data Principles (Wilkinson et al., 2016)
5. ESMF/NUOPC Coupling Framework Documentation

---

*Document Version: 1.0*
*Last Updated: January 7, 2026*
