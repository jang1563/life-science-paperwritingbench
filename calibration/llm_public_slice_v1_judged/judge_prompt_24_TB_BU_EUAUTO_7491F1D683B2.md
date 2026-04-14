You are an expert biomedical scientific-writing reviewer performing a rigorous peer-review-style evaluation.

Your job: score the candidate model's generated "Abstract" section against the source evidence for a abstract_from_evidence task, using the rubric below. Be strict and specific. Punish invented numbers, invented experiments, misattributed figures, and claims that cannot be traced to the provided evidence. Reward outputs whose details are demonstrably present in the evidence.

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

## Methods
Methods A systematic review and meta-analysis of randomized controlled trials (RCTs) comparing teprotumumab with placebo in TED was conducted. Primary outcomes included proptosis response, overall response, change in proptosis, diplopia response, achievement of a Clinical Activity Score (CAS) ≤1, changes in Graves’ ophthalmopathy–specific quality-of-life questionnaire (GO-QOL) scores and safety outcomes. Pooled risk ratios (RRs) and mean differences (MDs) with 95% confidence intervals (CIs) were calculated using random-effects models. Materials and methods This meta-analysis was conducted and reported in accordance with the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) guideline. The corresponding PRISMA flow diagram is shown in Figure 1 . Figure 1 Study selection flowchart. PRISMA flow diagram showing systematic review process: Two hundred eleven records identified, 127 screened after duplicates removed, 111 excluded, 16 full texts assessed, 9 excluded for ineligibility, and 7 included in synthesis and meta-analysis. Inclusion and exclusion criteria Studies were eligible for inclusion if they met the following criteria: 1) participants were diagnosed with TED; 2) the intervention group received eight infusions of teprotumumab (10 mg/kg for the first infusion and 20 mg/kg for each of the remaining seven infusions) administered once every three weeks; 3) primary and secondary end points reported in the trials included proptosis response rate (defined as a reduction in proptosis of ≥2 mm from baseline at week 24), overall response rate (defined as a composite of a ≥ 2 mm reduction in proptosis and ≥2-point reduction in CAS), change in proptosis from the baseline, diplopia response rate (defined as a reduction in diplopia of ≥1 grade from baseline according to the Gorman subjective diplopia score at week 24) ( 2 ) among patients with diplopia at baseline, the proportion of subjects achieving a CAS of 0/1 at week 24, change in GO-QOL score from baseline; 4) the study design was a randomized control trial; 5) the language used for the study was either English or Chinese; and 6) the full text was available online. Retrospective cohort studies, systematic reviews, case reports, studies without human data, conference abstracts and single-arm trials were excluded. Literature search and study selection A systematic literature search was conducted in PubMed, EMBASE, and the Cochrane Central Register of Controlled Trials (CENTRAL) from database inception to October 2025. The search strategy combined the following key terms: thyroid eye disease , thyroid-associated ophthalmopathy , Graves’ orbitopathy , teprotumumab , and randomized controlled trial . Additional relevant studies were identified through manual searches of Google Scholar and other sources. The detailed search strategy is provided in Supplementary Table S1 . Study selection was performed independently by two investigators according to the predefined eligibility criteria. Discrepancies were resolved by discussion and, when necessary, adjudicated by a third reviewer. Assessment of risk of bias and data collection Two reviewers independently assessed the methodological quality of each included study using the risk of bias tool outlined in the Cochrane Handbook for Systematic Reviews of Interventions . The following domains were evaluated: random sequence generation, allocation concealment, blinding of participants and personnel, blinding of outcome assessment, completeness of outcome data, selective reporting, and other potential sources of bias. Each domain was classified as having a low, high, or unclear risk of bias, and an overall judgment was summarized across domains. Data regarding baseline characteristics and all relevant outcomes were extracted in accordance with the predefined criteria. Any discrepancies between reviewers were resolved through consensus discussion. Statistical analysis Statistical analyses were performed using Review Ma...

## Results
Results Seven RCTs involving 438 participants were included. Teprotumumab significantly improved all efficacy outcomes: proptosis response (RR, 6.87; 95% CI, 3.32 to 14.24), overall response (RR, 7.82; 95% CI, 3.36 to 18.18), reduction in proptosis (MD, -2.46 mm; 95% CI, -2.96 to -1.96), diplopia response (RR, 1.85; 95% CI, 1.28 to 2.68), CAS ≤1 (RR, 3.39; 95% CI, 2.41 to 4.78) and increase in GO-QOL overall score (MD, 10.87; 95% CI, 9.91 to 11.83). Safety analysis indicated elevated risks of hyperglycemia (RR, 2.82; 95% CI, 1.08 to 7.37), muscle spasms (RR, 3.83; 95% CI, 1.97 to 7.43), dry skin (RR, 6.54; 95% CI, 1.52 to 28.09), and hearing impairment (RR, 3.74; 95% CI, 1.26 to 11.13). Results Literature search and study selection The detailed search strategy is presented in the Supplementary Table S1 , and the study selection process is summarized in Figure 1 . A total of 211 studies were identified through database searches (PubMed = 49, EMBASE = 98, and CENTRAL = 64) with no additional studies retrieved from other sources. After removal of duplicates, 127 unique records were screened by title and abstract, of which 111 were excluded. Sixteen full-text articles were subsequently assessed for eligibility, and nine were excluded with documented reasons (ineligible study design, ineligible population or ineligible outcome). Ultimately, seven randomized controlled trials met the inclusion criteria and were included in the meta-analysis, comprising 438 participants in total (teprotumumab, n = 240; placebo, n = 198) ( 2 , 6 , 8 , 11 , 12 , 17 , 18 ). Study characteristics and data extraction The characteristics of the studies included in this meta-analysis are summarized in Table 1 . The publications ranged from 2017 to 2025, and all were multicenter randomized controlled trials conducted across Asia, Europe, and the Americas. Sample sizes per study ranged from 10 to 54 participants per treatment arm. The enrolled populations consisted predominantly of adults, with no significant sex differences reported. Most studies included patients with a CAS greater than 3 at baseline except for the trial by Douglas et al. ( 6 ). The duration of TED ranged from 3.4 to 64.8 months, and mean baseline proptosis ranged between 20.4 mm and 24.6 mm. In most trials, the proportion of patients presenting with baseline diplopia was slightly higher in the teprotumumab group than in the placebo group. All studies administered eight intravenous infusions of teprotumumab in the intervention group and reported a follow-up period of 24 weeks. Relevant data were extracted and categorized according to the efficacy and safety profiles of teprotumumab. Efficacy outcomes comprised proptosis response rate, overall response rate, change in proptosis from baseline (mm), diplopia response rate, the proportion of patients achieving a CAS of 0 or 1, change in GO-QOL score from baseline. Safety outcomes were obtained from the included studies, defined as: ‘Muscle spasm’, ‘Alopecia’, ‘Nausea’, ‘Fatigue’, ‘Diarrhea’, ‘Headache’, ‘Dry skin’, ‘Dysgeusia’, ‘Stomatitis’ (or ‘Noninfective gingivitis’), ‘Hearing impairment’ (or ‘Hypoacusis’), ‘Hyperglycemia’ (or ‘Diabetes’, ‘Diabetes mellitus’), ‘Infusion reaction’. Table 1 Characteristics of the studies included in the meta-analysis. First author/publication year Study design Single vs multicenter Country Treatment groups (patients, n) Inclusion criteria Baseline characteristics (Teprotumumab/placebo) Interventions Follow-up duration (weeks) Age range (y) CAS Age (y) Female (n) Smokers (n) Duration of GO (months) Baseline proptosis (mm) Diplopia at baseline (n) Smith et al, 2017 ( 8 ) RCT multicenter Germany, Italy, United Kingdom, USA Teprotumumab (42) versus placebo (45) 18-75 ≥4/7 52/54 28/36 11/18 10.7/10.8 23.4/23.1 38/31 Eight infusions of teprotumumab* 24 Douglas et al, 2020 ( 2 ) RCT multicenter Germany, Italy, USA Teprotumumab (41) versus placebo (42) 18-80 ≥4/7 52/49 29/31 9/8 6.2/6.4 22.6/23.2 28/28 Eight infusions of teprotumumab* 24 Hiromatsu et al, 2025 ( 11 ) RCT multicenter Japan Teprotumumab (27) versus placebo (27) 20-80 ≥3/7 47/50 18/20 4/4 4.2/5.2 21.1/20.4 22/20 Eight infusions of teprotumumab* 24 Douglas et al, 2023 ( 6 ) RCT multicenter USA Teprotumumab (42) versus placebo (20) ≥18 ≤1/7 49/49 32/18 6/2 64.8/61.2 24.6/24.0 14/4 Eight infusions of teprotumumab* 24 Ugradar et al, 2022–1 ( 17 ) RCT multicenter Germany, Italy, United Kingdom, USA Teprotumumab (10) versus placebo (12) 18-80 >3/7...

## Figure captions
1. Figure 1. Study selection flowchart.
2. Figure 2. Risk of bias of studies comparing teprotumumab and placebo.
3. Figure 3. Risk of bias summary of studies comparing teprotumumab and placebo.
4. Figure 4. Proptosis response rate comparing teprotumumab and placebo.
5. Figure 5. Overall response rate comparing teprotumumab and placebo.
6. Figure 6. Change in proptosis from the baseline comparing teprotumumab and placebo.
7. Figure 7. Diplopia response rate comparing teprotumumab and placebo.
8. Figure 8. Proportion of subjects with a clinical activity score ≤1 comparing teprotumumab and placebo.

## Table snippets
1. Table 1. Characteristics of the studies included in the meta-analysis. | First author/publication year; Study design; Single vs multicenter; Country; Treatment groups (patients, n); Inclusion criteria
2. Table 2. Summary of sensitivity analysis with one study removed. | Outcomes; No. of studies; No. of patients in teprotumumab group; No. of patients in control group; Mean difference (95% Cl); Relative risk (95% Cl)

## Candidate output (to be judged)

Abstract

This systematic review and meta-analysis synthesizes the current evidence on the efficacy and safety of teprotumumab for treating active thyroid eye disease (TED). The **methods_section** details a comprehensive literature search across multiple databases up to October 2025, following PRISMA guidelines. Seven randomized controlled trials (RCTs), encompassing 438 participants, were included after a selection process documented in the **abstract_section** and a PRISMA flowchart. Pooled analyses using random-effects models were conducted for predefined outcomes. The **results_section** reports that teprotumumab demonstrated statistically significant superiority over placebo across all efficacy endpoints. This includes proptosis response (risk ratio [RR] 6.87), overall response (RR 7.82), mean reduction in proptosis (-2.46 mm), diplopia response (RR 1.85), achievement of a Clinical Activity Score ≤1 (RR 3.39), and improvement in quality of life (mean difference 10.87). However, safety analysis indicated elevated risks for several adverse events, including hyperglycemia, muscle spasms, dry skin, and hearing impairment. The **section_text** and associated tables summarize study characteristics and confirm the robustness of these pooled estimates. The collective **evidence** from these RCTs establishes teprotumumab as a highly effective intervention for improving ophthalmic and quality-of-life outcomes in TED, though with a distinct safety profile that requires consideration.

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