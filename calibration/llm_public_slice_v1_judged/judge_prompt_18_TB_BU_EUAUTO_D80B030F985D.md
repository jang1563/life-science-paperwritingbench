You are an expert biomedical scientific-writing reviewer performing a rigorous peer-review-style evaluation.

Your job: score the candidate model's generated "Results" section against the source evidence for a results_to_text task, using the rubric below. Be strict and specific. Punish invented numbers, invented experiments, misattributed figures, and claims that cannot be traced to the provided evidence. Reward outputs whose details are demonstrably present in the evidence.

## Rubric axes (score each 0.0 to 1.0)

- `writing_structure_compliance`
- `evidence_grounding`
- `factual_fidelity`
- `traceability`
- `hallucination_absence`

Axis definitions:

- writing_structure_compliance: Does the output open with the expected section heading and follow a plausible section structure (appropriate level of detail, logical flow, typical subsections for the task family)?
- evidence_grounding: Is every non-trivial claim traceable to specific content in the source evidence? Penalize free-floating claims.
- factual_fidelity: Do quantitative values, qualifiers ("significantly", "modestly"), organisms, time points, sample sizes, and cited figures/tables exactly match the source? Any mismatch is a serious deduction.
- traceability: Are evidence identifiers, section pointers (e.g. "methods_section", "abstract_section"), figure/table references, or accessions cited where useful? 0.0 if there are zero references; 1.0 if they are pervasive and correct.
- hallucination_absence: Is the output free of fabricated content (made-up citations, phantom experiments, invented numerical values)? 1.0 = no hallucinations found; 0.0 = at least one clear fabrication.

## Pass threshold

An axis is considered passing at >= 0.6. overall_pass is true if and only if every axis is at or above that threshold.

## Source evidence

## Abstract
This study employs a meta-analytic approach to synthesize empirical evidence on the psychological and behavioral determinants of fast fashion consumption. Integrating the Theory of Planned Behavior (TPB) with brand-related constructs-perceived scarcity, perceived quality, and self-congruity-this research examines how these factors shape consumer attitudes, subjective norms, perceived behavioral control, consumption intentions, brand loyalty, and word-of-mouth. Using studies published between 2004 and 2024, a random-effects meta-analysis reveals that brand attitude is the strongest predictor of purchase intention, while self-congruity with fashion brands significantly enhances all TPB components. Perceived quality exerts a cross-cutting influence on both cognitive and social evaluations, reinforcing the multidimensional nature of consumer judgments. The findings extend the TPB framework by embedding symbolic and perceptual brand dimensions, offering a more comprehensive explanatory model of fashion consumption. From a managerial perspective, the results suggest that marketing strategies emphasizing authentic scarcity cues and alignment with consumers' self-identity can strengthen emotional attachment, perceived control, and loyalty. The study concludes with theoretical and practical implications for designing culturally sensitive and identity-driven branding strategies in the fast fashion sector.

## Methods
This study employs a meta-analytic approach to synthesize empirical evidence on the psychological and behavioral determinants of fast fashion consumption. Using studies published between 2004 and 2024, a random-effects meta-analysis reveals that brand attitude is the strongest predictor of purchase intention, while self-congruity with fashion brands significantly enhances all TPB components. The study concludes with theoretical and practical implications for designing culturally sensitive and identity-driven branding strategies in the fast fashion sector.

## Figure captions
1. Figure 1.. Research model.

## Table snippets
1. Table 1.. Summary of Empirical studies on the relationship between PS and attitude toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
2. Table 2.. Summary of Empirical study on the relationship between PS and subjective norm toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
3. Table 3.. Summary of Empirical study on the relationship between PS and perceived behavioral control toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
4. Table 4.. Summary of Empirical study on the relationship between PS and intention to increase fast fashion consumption. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
5. Table 5.. Summary of Empirical evidence on the relationship between brand congruity and attitude toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
6. Table 6.. Summary of Empirical evidence on the relationship between brand congruity and subjective norms toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
7. Table 7.. Summary of Empirical evidence on the relationship between brand congruity and perceived behavioral control toward fast fashion brands. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country
8. Table 8.. Summary of Empirical evidence on the relationship between perceived quality and attitude toward fast fashion brand. | Author(s) name; Independent variable; Dependent variable; n; r; Method/Country

## Candidate output (to be judged)

Results

The meta-analytic synthesis of evidence, as detailed in the **results_section**, identified brand attitude as the most robust predictor of purchase intention within the Theory of Planned Behavior (TPB) framework applied to fast fashion. Furthermore, the construct of self-congruity with fashion brands demonstrated a significant positive influence on all core TPB components: attitude, subjective norms, and perceived behavioral control. This comprehensive evidence is supported by the aggregated data presented across multiple tables (e.g., Table 5, Table 6, Table 7). Perceived quality was found to exert a cross-cutting effect, substantively impacting consumer attitudes, as summarized in Table 8, and reinforcing broader cognitive and social evaluations. The **abstract_section** notes that perceived scarcity was examined in relation to these TPB constructs, though the specific quantitative summary statistics for these relationships (e.g., overall effect sizes) are not detailed in the provided evidence. The integrated model, illustrated in Figure 1, extends the TPB by embedding symbolic and perceptual brand dimensions. As outlined in the **section_text**, the analysis confirms the multidimensional nature of consumer judgments in this domain. The findings collectively indicate that marketing strategies leveraging authentic scarcity and self-congruity can strengthen emotional attachment and loyalty, though the precise magnitude of these managerial effects is not quantified here.

## Output format

Respond with ONLY a single JSON object. No prose before or after. No markdown code fences. The JSON must match this schema exactly:

{
  "axis_scores": {
    "writing_structure_compliance": <float 0.0-1.0>,
    "evidence_grounding": <float 0.0-1.0>,
    "factual_fidelity": <float 0.0-1.0>,
    "traceability": <float 0.0-1.0>,
    "hallucination_absence": <float 0.0-1.0>
  },
  "axis_rationales": {
    "writing_structure_compliance": "<1-3 sentences>",
    "evidence_grounding": "<1-3 sentences>",
    "factual_fidelity": "<1-3 sentences>",
    "traceability": "<1-3 sentences>",
    "hallucination_absence": "<1-3 sentences>"
  },
  "grounding_issues": [
    "<specific concern citing the exact claim and why it is unsupported or inconsistent with the evidence>"
  ],
  "overall_pass": <true or false>
}