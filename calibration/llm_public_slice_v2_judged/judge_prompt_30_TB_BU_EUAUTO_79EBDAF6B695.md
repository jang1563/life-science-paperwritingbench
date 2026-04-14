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
Obesity is a complex condition marked by excessive body fat, linked to comorbidities such as type 2 diabetes and cardiovascular disease. Glucagon-like peptide-1 (GLP-1) receptor agonists, initially developed for diabetes, are increasingly used for weight management. We conducted a systematic review and meta-analysis of randomized controlled trials (PubMed, last 5 years, English language) evaluating GLP-1-based pharmacotherapies versus placebo or active comparators for weight loss. The primary endpoint was the proportion of participants achieving any weight loss during follow-up. Pooled odds ratios were estimated using a fixed-effect model with 95% confidence intervals; heterogeneity was quantified with I2. A frequentist network meta-analysis generated SUCRA rankings. This review followed the Preferred Reporting Items for Systematic Reviews and Meta-Analyses 2020 guidelines. No protocol was registered. Twenty-one trials met the inclusion criteria (n = 7024 in pairwise analyses). Across 16 placebo-controlled trials, a higher proportion of participants achieved weight loss with GLP- 1-based agents than with placebo: 78.54% (3231/4114) versus 26.53% (772/2910); pooled odds ratio: 11.37 (95% confidence interval: 8.10-15.98), P < .0001; I2 = 82%. In the network meta-analysis, tirzepatide and semaglutide ranked highest (surface under the cumulative ranking curve 91.2% and 85.4%, respectively). GLP-1 receptor agonists significantly increase the likelihood of weight loss versus placebo, with tirzepatide and semaglutide demonstrating the greatest relative efficacy among agents evaluated. These findings support GLP-1-based therapy as an effective component of clinical obesity management.

## Results
Results: Twenty-one trials met the inclusion criteria (n = 7024 in pairwise analyses). Across 16 placebo-controlled trials, a higher proportion of participants achieved weight loss with GLP- 1–based agents than with placebo: 78.54% (3231/4114) versus 26.53% (772/2910); pooled odds ratio: 11.37 (95% confidence interval: 8.10–15.98), P < .0001; I 2 = 82%. In the network meta-analysis, tirzepatide and semaglutide ranked highest (surface under the cumulative ranking curve 91.2% and 85.4%, respectively). 3. Results The current analysis incorporated published clinical studies on GLP-1 agonists for weight loss from PubMed. The keywords “GLP-1 agonists” and “weight loss” yielded 2085 studies. The analysis removed studies that were not clinical trials or were submitted in languages other than English (1885 studies were excluded). We further narrowed the search to include trials conducted during the last 5 years (104 trials were excluded). Following that, the remaining 96 studies were evaluated for eligibility, with 21 trials included in the analysis (Table 1 and Fig. 1 ). [ 17 – 37 ] Table 1 The included studies. Study Year Medications Participants Inagaki et al [ 17 ] 2022 Tirzepatide vs dulaglutide Patients with type 2 diabetes Lingvay et al [ 18 ] 2023 Tirzepatide vs placebo Patients with type 2 diabetes Elkind-Hirsch et al [ 19 ] 2022 Liraglutide vs placebo Women with PCOS Rosenstock et al [ 20 ] 2023 Retatrutide vs placebo Patients with type 2 diabetes Jensen et al [ 21 ] 2023 Liraglutide vs semaglutide Patients having bariatric surgery Aroda et al [ 22 ] 2019 Semaglutide vs placebo Patients with type 2 diabetes Rodbard et al [ 23 ] 2019 Semaglutide vs empagliflozin Patients with type 2 diabetes Rubino et al [ 24 ] 2022 Semaglutide vs liraglutide Adults with obesity without diabetes Zhang et al [ 25 ] 2024 Mazdutide vs placebo Patients with type 2 diabetes Wadden et al [ 26 ] 2023 Tirzepatide vs placebo Adults with obesity without diabetes Mok et al [ 27 ] 2023 Liraglutide vs placebo Adults with obesity without diabetes Jastreboff et al [ 28 ] 2023 Retatrutide vs placebo Adults with obesity without diabetes Silver et al [ 29 ] 2023 Liraglutide vs sitagliptin Adults with obesity and prediabetes Weghuber et al [ 30 ] 2022 Semaglutide vs placebo Adults with obesity without diabetes Jastreboff et al [ 31 ] 2022 Tirzepatide vs placebo Adults with obesity without diabetes Dahl et al [ 32 ] 2022 Tirzepatide vs placebo Adults with type 2 diabetes Nahra et al [ 33 ] 2021 Cotadutide vs placebo Adults with type 2 diabetes Rubino et al [ 34 ] 2021 Semaglutide vs placebo Adults with obesity without diabetes Wadden et al [ 35 ] 2021 Semaglutide vs placebo Adults with obesity without diabetes Wilding et al [ 36 ] 2021 Semaglutide vs placebo Adults with obesity without diabetes Ji et al [ 37 ] 2021 Semaglutide vs sitagliptin Adults with type 2 diabetes PCOS = polycystic ovary syndrome. Figure 1. Flowchart of included studies. Sixteen clinical trials evaluated the rates of weight reduction among participants who took drugs (GLP-1 agonists: semaglutide, tirzepatide, liraglutide, retatrutide, mazdutide, and cotadutide) compared with those who got a placebo (Table 2 ). Semaglutide trials (6 trials) revealed that 79.90% of patients reduced weight against 30.30% with a placebo. Tirzepatide trials (4 trials) demonstrated that 79.38% of patients decreased weight compared with 24.72% with a placebo. Furthermore, liraglutide trials (2 trials) revealed that 63.16% of individuals decreased weight, compared with 14.04% with placebos. Retatrutide trials (2 trials) revealed that 73.03% of patients decreased weight, compared with 18.63% with a placebo. Furthermore, the mazdutide research found that 77.5% of participants lost weight versus 19.6% with placebo. The cotadutide experiment indicated that 40.0% of participants decreased weight, compared with 9.9% with a placebo. In all cases, people who got the medicine lost much more weight than those who took the placebo. Nine studies evaluated the rates of weight reduction among participants who took different drugs (Table 3 ). All of the included studies were randomized, and some of the studies had a low risk of bias (Table 4 ). Table 2 The percentage of people who lost weight after taking either GLP-1 agonists or a placebo. Study Event Total Percentage Event Total Percentage Zhang et al [ 25 ] Mazdutide Placebo 38 49 77.5% 10 51 19.6% Wadden et al [ 26 ] Tirzepatide Placebo 251 287 87.5% 48 282 17.0% ...

## Figure captions
1. Figure 1.. Flowchart of included studies.
2. Figure 2.. Forest plot (the rate of weight loss of the GLP-1 agonists group and the placebo group). CI = confidence interval, GLP-1 = glucagon-like peptide-1, M-H = Mantel–Haenszel.
3. Figure 3.. The percentage of people who lost weight after taking either semaglutide or other agents. CI = confidence interval.
4. Figure 4.. The percentage of people who lost weight after taking either dulaglutide or other agents. CI = confidence interval.
5. Figure 5.. The proportion of patients who lost weight while taking tirzepatide or other drugs. CI = confidence interval.
6. Figure 6.. The proportion of individuals who lost weight while on liraglutide or other medications. CI = confidence interval.
7. Figure 7.. SUCRA ranking of treatments in network meta-analysis. SUCRA = surface under the cumulative ranking curve.

## Table snippets
1. Table 1. The included studies. | Study; Year; Medications; Participants; Inagaki et al [ 17 ]; 2022
2. Table 2. The percentage of people who lost weight after taking either GLP-1 agonists or a placebo. | Study; Event; Total; Percentage; Event; Total
3. Table 3. The percentage of people who lost weight after taking different GLP-1 agonists. | Study; Event; Total; Percentage; Event; Total
4. Table 4. Risk of bias assessment for all included RCTs. | Study; Randomization; Deviations; Missing data; Outcome measurement; Reporting

## Candidate output (to be judged)

Methods

This systematic review and meta-analysis was conducted in accordance with the Preferred Reporting Items for Systematic Reviews and Meta-Analyses 2020 guidelines. No protocol was registered for this review.

A literature search was performed in PubMed, restricted to studies published in English within the last five years. The search utilized the keywords “GLP-1 agonists” and “weight loss,” which initially yielded 2085 studies. The screening process excluded 1885 studies that were not clinical trials or were in languages other than English. A further 104 trials were excluded by limiting the search to the last five years. The remaining 96 studies were assessed for eligibility, resulting in 21 randomized controlled trials (RCTs) being included in the final analysis (n = 7024 in pairwise analyses). The study selection process is detailed in a flowchart (Fig. 1), and the characteristics of the included studies are listed (Table 1).

The primary endpoint was the proportion of participants achieving any weight loss during follow-up. Data from 16 placebo-controlled trials were used for pairwise meta-analysis. The specific agents evaluated against placebo were semaglutide, tirzepatide, liraglutide, retatrutide, mazdutide, and cotadutide, with outcome data presented (Table 2). A fixed-effect model was used to calculate pooled odds ratios (OR) with 95% confidence intervals (CI). Heterogeneity was quantified using the I² statistic. The evidence for this analysis is presented in a forest plot (Fig. 2).

A frequentist network meta-analysis was performed to compare the relative efficacy of different GLP-1-based pharmacotherapies, including both placebo and active comparators. Data for active-comparator trials are shown (Table 3). The results of the network meta-analysis were used to generate rankings based on the surface under the cumulative ranking curve (SUCRA), presented in a ranking plot (Fig. 7). The risk of bias for all included RCTs was assessed, but the specific assessment tool used is not stated in the provided evidence; the results of this assessment are summarized (Table 4).

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