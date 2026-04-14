You are an expert biomedical scientific-writing reviewer performing a rigorous peer-review-style evaluation.

Your job: score the candidate model's generated "Methods" section against the source evidence for a methods_to_text task, using the rubric below. Be strict and specific. Punish invented numbers, invented experiments, misattributed figures, and claims that cannot be traced to the provided evidence. Reward outputs whose details are demonstrably present in the evidence.

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
3D segmentation of the upper airway is crucial for dental and medical practices. However, it is a difficult and daunting task. Like almost all other areas, AI can theoretically help in airway segmentation. Nevertheless, AI's efficacy remains unknown. This meta-analysis investigated this matter for the first time. ‎Various search engines/databases/articles were searched for articles published until April 25, 2025. All English-language articles on the use of AI for upper airway evaluations based on CBCT or CT scans were included in the study. The desired population was considered studies assessing the upper airway. Intervention was the use of any tool of AI such as deep learning and machine learning for image analysis. The comparator was the manual analysis of CBCT or CT scans by human. The outcome was the analysis of upper airway on CBCT or CT images. The recorded and analyzed effect sizes were: accuracies, precisions, dice similarity scores, total volume differences, intersection over union (IoU), recall, or any other parameters relevant to segmentation. A meta-analysis was conducted for each of the mentioned parameters if adequate data were available. The outcome was the analysis of upper airway on CBCT or CT images (PROSPERO: CRD42024508004). Eleven studies were included, with 6 studies included in meta-analyses. Most studies had a low risk of bias in most aspects. The qualitative part of review showed promising results for AI segmentation. Four of the effects sizes were meta-analyzed: Precision,‎ dice similarity score, intersection over union, ‎ and recall were all above 90%.‎ Total volume difference was small but significantly above zero. Sensitivity analyses showed robustness of all meta-analysis results. Publication bias was insignificant. The results showed promising AI efficacies in 3D segmentation of the upper airway in CBCTs. However, much more studies are needed before decisive conclusions.

## Results
Results Eleven studies were included, with 6 studies included in meta‐analyses. Most studies had a low risk of bias in most aspects. The qualitative part of review showed promising results for AI segmentation. Four of the effects sizes were meta‐analyzed: Precision,‎ dice similarity score, intersection over union, ‎ and recall were all above 90%.‎ Total volume difference was small but significantly above zero. Sensitivity analyses showed robustness of all meta‐analysis results. Publication bias was insignificant. 2.9 Synthesis of Results and Meta‐Analysis The effect sizes were the following estimates: accuracies, precisions, dice similarity scores, total volume differences, intersection over union (IoU), recall, or any other parameters relevant to segmentation. A meta‐analysis was conducted for each of the mentioned parameters, if more than one article had reported adequate information about it. In most cases, studies did not report all the necessary information, therefore meta‐analyses could be conducted for four parameters: weighted means for dice similarity score, precision, recall, and total volume difference. Sensitivity analysis was conducted through the leave‐one‐out meta‐analysis. Publication bias was estimated using the Egger regression; funnel plots were evaluated as well (if applicable). The software in use was STATA 17 (Stata, USA). The level of significance was set at 0.05. 3 Results 3.1 Study Selection A total of 113 studies were found in search (Figure 1 ). Any duplicates were identified and removed, resulting in 70 unique articles. The abstracts of these 70 articles were screened. A total of 36 articles were marked as not relevant. The rest of articles ( n = 34) were read and checked against the exclusion and inclusion criteria. A total of 23 articles were excluded because (Orhan et al. 2022 ) their full‐text was not available, (Mupparapu et al. 2021 ) AI was not used, (Neelapu et al. 2017 ) CBCT or CT was not used, (Sobouti et al. 2022 ) the upper airway was not assessed, (Parks 2014 ) skeletal malocclusions were evaluated, (Rasteau et al. 2022 ) they lacked the comparison with human gold standard, and (Obermeyer and Emanuel 2016 ) their results were not clear. Finally, 11 studies were included in the qualitative analyses and 6 of them were also eligible for meta‐analyses (Figure 1 ). Most of the studies showed low risks of bias in all measurements (Table 1 ). The summary of the included studies is given in Table 2 . Figure 1 The flow diagram of studies included in this systematic review and meta‐analysis. Table 1 Risk of bias assessment. Author, year (reference) Bias due to confounding Bias in the selection of participants into the study Bias in the measurement of interventions Bias due to departures from intended interventions Bias due to missing data Bias in measurement outcomes Bias in the selection of the reported result Overall bias Alsufyani et al. ( 2016 ) L L L L L L L L Leonardi et al. ( 2021 ) L L L L L B L B Park et al. ( 2021 ) a L L L L L B L a Shujaat et al. ( 2021 ) L L L L L L L L Sin et al. ( 2021 ) L L L L L L L L Orhan et al. ( 2022 ) L B L L L B L B Cho et al. ( 2022 ) L L L L L L L L Chu et al. ( 2023 ) L L L L L L L L Jin et al. ( 2023 ) L L L L L L L L Gao et al. ( 2024 ) L L L L L L L L Süküt et al. ( 2025 ) L L L L L L L L a The report by Park et al. ( 2021 ) had inconsistencies in terms of the reported sample size as well as the total volume difference. The items of this ‎table were all green from the report.‎ The sample size is once reported as 63 and once as 61. The total volume difference is once reported as ‎85.256 (‎‎86.504) and once as ‎‎137.256 (‎‎146.517). L, a l ow risk of bias; B, a high risk of b ias. John Wiley & Sons, Ltd. Table 2 A summary of the included studies. Author, year (reference) Data Dataset size (train/valid/test) AI task Hardware Model structures Outcome Outcome mean (SD) Comments Alsufyani et al. ( 2016 ) CBCT 10 case/10 control Segmentation Segura software (University of Alberta, Edmonton, Alberta, Canada) Total volume difference (mm 3 ) 1.9 (1.4) They concluded the software is worthwhile in terms of precision and convenience. Total surface difference (mm 2 ) 5.4 (3.6) Time of segmentation‐human (s) 109 (9.4) Time of segmentation‐Segura (s) 49 (11) Leonardi et al. ( 2021 ) CBCT 20 training/20 test Segmentation Titan X Pascal GPU (NVIDIA Corporate, Santa Clara, Calif), Core i7 CPU with 8 GB RAM (Intel, Santa Clara, Calif) CNN: Mimics software (...

## Figure captions
1. Figure 1. The flow diagram of studies included in this systematic review and meta‐analysis.
2. Figure 2. Weighted mean differences (and 95% CIs) for the precision of the AI systems.
3. Figure 3. Sensitivity analysis for the precision of the AI systems.
4. Figure 4. Weighted mean differences (and 95% CIs) for the dice score of the AI systems.
5. Figure 5. Sensitivity analysis for the dice score of the AI systems.
6. Figure 6. Weighted mean differences (and 95% CIs) for the total volume difference of the AI.
7. Figure 7. Sensitivity analysis for the total volume difference of the AI.
8. Figure 8. Weighted mean differences (and 95% CIs) for the recall of the AI systems.

## Table snippets
1. Table 1. Risk of bias assessment. | Author, year (reference); Bias due to confounding; Bias in the selection of participants into the study; Bias in the measurement of interventions; Bias due to departures from intended interventions; Bias due to missing data
2. Table 2. A summary of the included studies. | Author, year (reference); Data; Dataset size (train/valid/test); AI task; Hardware; Model structures

## Candidate output (to be judged)

Methods

This systematic review and meta-analysis was conducted to evaluate the efficacy of artificial intelligence (AI) tools for the three-dimensional segmentation of the upper airway using cone-beam computed tomography (CBCT) or CT scans. The review protocol was registered in PROSPERO (CRD42024508004).

A comprehensive search of various databases and search engines was performed to identify all relevant English-language articles published up to April 25, 2025. The population of interest was studies assessing the upper airway. The intervention was the use of any AI tool, such as deep learning or machine learning, for image analysis. The comparator was manual analysis of CBCT or CT scans by a human. The primary outcome was the analysis of the upper airway on CBCT or CT images, with effect sizes including accuracy, precision, dice similarity score (DSC), total volume difference, intersection over union (IoU), recall, and other relevant segmentation parameters.

Study selection followed the PRISMA flow diagram (**Figure 1**). From an initial 113 records, 70 unique articles remained after duplicate removal. Abstract screening excluded 36 articles. Full-text review of 34 articles against eligibility criteria led to the exclusion of 23 studies for the following reasons: full-text unavailability, no use of AI, no use of CBCT/CT, upper airway not assessed, evaluation of skeletal malocclusions, lack of comparison with a human gold standard, or unclear results. Ultimately, 11 studies were included for qualitative synthesis, with 6 providing adequate data for meta-analysis (**Figure 1**).

The risk of bias for included studies was assessed, with most studies demonstrating a low risk of bias across most domains (**Table 1**). A summary of study characteristics, including data type, dataset sizes, AI tasks, hardware, and model structures, is provided in **Table 2**.

Meta-analysis was conducted for any parameter reported by more than one study with adequate information. This was possible for four effect sizes: precision, DSC, recall, and total volume difference. Weighted mean differences and 95% confidence intervals were calculated. All analyses were performed using STATA 17 software, with a significance level set at 0.05. Sensitivity analysis was performed using leave-one-out meta-analysis. Publication bias was estimated using Egger's regression test, with funnel plots evaluated where applicable. The specific results of these analyses for precision, DSC, total volume difference, and recall are shown in **Figures 2, 4, 6, and 8**, respectively, with corresponding sensitivity analyses in **Figures 3, 5, and 7**.

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