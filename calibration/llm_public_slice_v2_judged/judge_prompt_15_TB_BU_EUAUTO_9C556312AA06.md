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
Although Upadacitinib has proven success in inflammatory bowel diseases (IBD), there is less data on its efficacy and safety in Asian patients with refractory IBD. This multicenter study evaluated the real-world effectiveness and safety of UPA in patients with refractory IBD. This multicenter retrospective cohort analysis included adult refractory IBD patients who received UPA therapy at three tertiary hospitals from January 2023 to March 2025. Clinical, endoscopic, and laboratory outcomes were effectiveness goals. Safety measures included AEs and and rates of discontinuation. A total of 80 eligible patients were enrolled, including 52 with CD and 28 with UC. During the induction period, for CD: steroid-free clinical remission: 59.6%; clinical response: 61.5%; endoscopic remission: 30.8%; endoscopic response: 57.7%. For UC, steroid-free clinical remission: 67.9%; clinical response: 71.4%; endoscopic remission: 46.4%; endoscopic response: 60.7%. In the maintenance phase (12 months), CD had 78.8% steroid-free clinical remission and 75.0% endoscopic remission. UC had 85.7% steroid-free clinical remission and 78.6% endoscopic remission. Inflammatory indicators and nutritional parameters improved significantly. The incidence of adverse events in CD and UC was 23.1% and 14.3%, respectively, and the discontinuation rates during the 12-month maintenance treatment period were 7.1% and 21.5%, respectively. The most common adverse reaction is acne (8.75%). UPA demonstrated robust real-world effectiveness and an acceptable safety profile in Asian patients with refractory IBD.

## Methods
Methods This multicenter study evaluated the real-world effectiveness and safety of UPA in patients with refractory IBD. This multicenter retrospective cohort analysis included adult refractory IBD patients who received UPA therapy at three tertiary hospitals from January 2023 to March 2025. Clinical, endoscopic, and laboratory outcomes were effectiveness goals. Safety measures included AEs and and rates of discontinuation. Materials and Methods Data Selection This multicenter retrospective cohort study collected data from IBD patients treated with UPA at three tertiary hospitals in China from 1 January 2023 to 30 March 2025. Patients were diagnosed as IBD using established criteria. 26 To ensure reproducibility of patient selection, data were abstracted from the standardized electronic medical records (EMR) of each center using a pre-defined, structured case report form. Two trained investigators per center independently extracted the data; a third senior reviewer cross-checked a random 20% sample, with inter-rater agreement exceeding 95%. Discrepancies were resolved by consensus. The research received approval from the Medical Ethics Committees of each hospital (Ethics Approval Numbers: 2025-KL-321-02, No. 2025-0521, 2025No. 1106-18). Patient anonymity was preserved, and informed consent was exempted due to the retrospective nature of the study. Data were acquired from electronic medical records by personnel at each center.All data were systematically acquired from the standardized electronic medical records (EMR) systems of each participating center by trained data abstractors. All methods were performed in accordance with the Declaration of Helsinki. Inclusion and Exclusion Criteria Patient selection aimed to include a well-defined “difficult-to-treat” (DTT) IBD cohort, based on the criteria outlined by the International Organization for the Study of IOIBD: (1) failure of at least two biologics or small molecule agents with distinct mechanisms of action, (2) recurrence following a minimum of two surgeries in adult Crohn’s disease patients (one surgery in pediatric patients), (3) combined with chronic antibiotic-refractory pouchitis, (4) combined with complex perianal disease, (5) combined with psychosocial diseases affecting disease management. Patients were identified via a systematic query of each hospital’s EMR for IBD diagnoses and Upadacitinib prescriptions within the study period, and their medical charts were individually reviewed to confirm DTT status against the IOIBD criteria. Inclusion criteria: (1) refractory IBD patients from three centers between January 2023 and March 2025; (2) Received at least 8 weeks (for UC) or 12 weeks (for CD) of UPA treatment, corresponding to the induction periods. Exclusion criteria: (1) pregnancy and breastfeeding; (2) serious infections or history of malignancy; (3) liver impairment (ALT or AST > 3 times the upper limit of normal) or kidney impairment (estimated glomerular filtration rate < 30 mL/min/1.73m 2 ); (4) history of total colectomy for UC; (5) Patients lacking sufficient baseline or follow-up data in their medical records to adequately assess the pre-defined primary therapeutic efficacy endpoints or safety, as detailed in section 2.3 and 2.4. Such patients were excluded to ensure data completeness for the core analyses. (6) Patients receiving concomitant biological agents (eg, infliximab, vedolizumab) during upadacitinib therapy. Given the retrospective, observational nature and the specific, real-world DTT-IBD population, a formal a priori sample size calculation was not performed. The cohort size represents all eligible patients treated within the study period across the three centers. Demographic and Clinical Data Data Abstraction:Baseline and follow-up data were extracted from the hospital electronic medical records by two physicians at each center. One collected data using a standardized form, while the other verified it. Discrepancies were resolved through discu...

## Figure captions
1. Figure 1. Lasso regression screening variables. ( A ) Elastic net regression model and 10-fold cross-validation to select the most appropriate features (λ = 0.130900498904221); ( B ) Predictors and corresponding coefficients of elastic network selection. Only variables with non-zero coefficients after elastic network selection were displayed. All variables were included and collinearity interference was excluded.
2. Figure 2. Boruta method for variable selection. The variables screened by Lasso were further constructed into a random forest to obtain the importance ranking of the variables. Green, important; yellow, tentative; red, unimportant, blue, shadow. The vertical axis lists the name of each variable, and the horizontal axis is the Z value.
3. Figure 3. ROC curve and AUC of multivariate model.
4. Figure 4. Patient selection flow chart.
5. Figure 5. ( A ) Clinical remission rates in UC and CD patients during the induction period and maintenance therapy. ( B ) Clinical response rates. ( C ) Endoscopic remission rates. ( D ) Endoscopic response rates. ( E ) CRP Normalization. ( F ) FC Normalization.
6. Figure 6. ( A ) Baseline and post-treatment trends of total FC levels. ( B ) Baseline and post-treatment trends of total CRP levels. ( C ) Baseline and post-treatment trends of total ESR levels. ( D ) Baseline and post-treatment trends of total FC levels. ( E ) Baseline and post-treatment trends of total FC levels.
7. Figure 7. Baseline and post-treatment trends of other laboratory outcomes. ( A ) WBC. ( B ) Hb. ( C ) PLT. ( D ) ALT. ( E ) AST. ( F ) HDL-C/TC. ( G ) LDL-C.
8. Figure 8. Discontinuation rates and adverse events in UC and CD patients.

## Table snippets
1. Table 1. Patient Demographics and Baseline Characteristics | Characteristic; Diagnosis; p-value; 0 N = 28; 1 N = 52; Age
2. Table 2. Multivariate Logistic Regression for Training Cohort | Characteristic; N; Event N; OR; 95% CI; p-value
3. Table 3. Baseline Characteristics | Variables; N=80; CD Patients N=52; UC Patients N=28; General data; Male, n (%)
4. Table 4. Comparison of the Incidence of Adverse Event Types | N=80; CD (N=52); UC (N=28); Skin (acne); 7(8.75%); 5(9.6%)

## Candidate output (to be judged)

Results

A total of 80 eligible patients with refractory IBD were enrolled from three tertiary hospitals, comprising 52 with Crohn’s disease (CD) and 28 with ulcerative colitis (UC) (Table 3, Fig. 4). During the induction period, upadacitinib demonstrated substantial effectiveness. For CD patients, steroid-free clinical remission was achieved in 59.6% and clinical response in 61.5%, while endoscopic remission and response rates were 30.8% and 57.7%, respectively (Fig. 5A-D). For UC patients, the corresponding rates were 67.9% for steroid-free clinical remission, 71.4% for clinical response, 46.4% for endoscopic remission, and 60.7% for endoscopic response (Fig. 5A-D). These efficacy outcomes were sustained during the 12-month maintenance phase, with CD patients achieving 78.8% steroid-free clinical remission and 75.0% endoscopic remission, and UC patients achieving 85.7% and 78.6%, respectively (Fig. 5A, C).

Significant improvements in inflammatory and nutritional laboratory parameters were observed post-treatment. Trends showing reductions in fecal calprotectin (FC), C-reactive protein (CRP), and erythrocyte sedimentation rate (ESR) levels are depicted in Fig. 6. Normalization rates for CRP and FC are shown in Fig. 5E-F. Trends for other laboratory outcomes, including white blood cell count (WBC), hemoglobin (Hb), platelet count (PLT), and lipid profiles, are presented in Fig. 7.

The safety profile was acceptable. The overall incidence of adverse events was 23.1% in CD patients and 14.3% in UC patients (Fig. 8). The most common adverse reaction was acne, occurring in 8.75% of all patients (Table 4). Discontinuation rates during the 12-month maintenance period were 7.1% for CD and 21.5% for UC (Fig. 8). Predictors of treatment response were analyzed using Lasso regression (Fig. 1) and the Boruta method (Fig. 2), with the performance of the resulting multivariate model shown by its receiver operating characteristic curve (Fig. 3, Table 2). Specific demographic and baseline characteristics of the cohort are detailed in Table 1 and Table 3.

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