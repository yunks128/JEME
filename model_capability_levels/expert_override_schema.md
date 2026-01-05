# Expert Override Schema for MCL Assessment

## Purpose

Expert overrides allow domain experts to correct LLM-generated assessments where:
1. The LLM extracted evidence from the wrong sources (evidence contamination)
2. The LLM underestimated/overestimated capabilities due to limited context
3. A metric is not applicable to a particular model type
4. Expert knowledge provides more accurate assessment than citation analysis

## JSON Schema

```json
{
  "model_name": "MODEL_NAME",
  "expert_name": "Name or role of the expert",
  "override_date": "YYYY-MM-DD",
  "notes": "General notes about why overrides are needed",
  "overrides": {
    "MCL-X": {
      "category": "CATEGORY",
      "reason": "Detailed explanation of why this override is needed",
      "evidence": [
        "Specific evidence item 1",
        "Specific evidence item 2"
      ]
    }
  },
  "notes_on_llm_evidence_contamination": {
    "MCL-X": "Optional notes on what was wrong with LLM evidence"
  }
}
```

## Valid Categories

| Category | Description |
|----------|-------------|
| `NOT_ASSESSED` | Insufficient information to assess |
| `NOT_APPLICABLE` | Metric does not apply to this model type |
| `LOW` | Basic or limited capability |
| `MODERATE` | Functional capability with limitations |
| `HIGH` | Strong capability with validated approaches |
| `VERY_HIGH` | State-of-the-art, comprehensive capability |

## When to Use Each Override Reason

### NOT_APPLICABLE
Use when a metric fundamentally doesn't apply:
- **MCL-5 (Predictive Skill)**: For reanalysis/state estimation systems that don't do prediction
- **MCL-8 (Retrospective Analysis)**: For pure forward models with no DA

### Evidence Contamination Correction
When LLM extracted evidence about other models mentioned in citing papers:
```json
{
  "category": "VERY_HIGH",
  "reason": "LLM evidence was from ADCIRC citations, not ECCO. Actual ECCO capability is...",
  "evidence": ["Correct ECCO-specific evidence"]
}
```

### Domain Expert Knowledge
When expert knowledge supersedes citation-based assessment:
```json
{
  "category": "VERY_HIGH",
  "reason": "MITgcm is one of only 3-4 codes capable of global O(100m) resolution",
  "evidence": ["LLC4320 simulation at 1/48 degree", "Demonstrated 100K+ core scaling"]
}
```

## Usage

Run the v2 analyzer with expert overrides:

```bash
python llm_capability_analyzer_v2.py \
  ../citation_scraper/output/ECCO_citations_citations_only.json \
  --model-name ECCO \
  --expert-overrides ECCO_expert_overrides.json
```

The analyzer will:
1. Run LLM analysis as normal
2. Replace scores for overridden dimensions with expert values
3. Mark overridden dimensions in the report with ⚠️ indicator
4. Include expert reasoning in the detailed analysis

## Best Practices

1. **Document reasoning clearly**: Future users should understand why the override exists
2. **Provide authoritative evidence**: Use official documentation, published papers, or system specifications
3. **Note LLM errors**: Document what the LLM got wrong for methodology improvement
4. **Be specific**: Vague overrides undermine trust in the assessment
5. **Review periodically**: Model capabilities change; update overrides as needed
