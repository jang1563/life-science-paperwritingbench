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
Methods A retrospective observational study was conducted in 614 patients treated with parenteral nutrition. Anthropometric assessments were realized. Morphofunctional assessments included bioelectrical impedance analysis to determine phase angle and dynamometry to measure handgrip strength. Survival analysis was performed using Cox proportional hazards models and Kaplan‐Meier curves and cutoff values by receiver operating characteristic curve analysis. MATERIAL AND METHODS Study design and participants In this retrospective observational study conducted within a single center, a cohort of patients requiring parenteral nutrition for diverse clinical indications was recruited. Anthropometric assessments, bioelectrical impedance vector analysis, and handgrip strength evaluations were conducted during the period extending from November 2019 to November 2024. The study included adult patients (>18 years old) with parenteral nutrition and long hospital stay (>72 h). The study excluded patients based on specific criteria, including pediatric individuals, pregnant patients, and those with a brief hospital stay (defined as <72 h postadmission), as well as individuals who declined participation and those unable to undergo bioelectrical impedance analysis because of confounding factors such as ethnicity, extensive dermatological lesions, fluid extravasation, localized hematomas, or amputations (Supporting Information S1: Figure 1 ). Demographic, clinical, and anthropometric measurements Demographic characteristics, comorbidities, and clinical and anthropometric data, as well as additional nutrition assessments, were meticulously documented as part of routine hospital practice upon patient admission (first day). Within 72 h after the start of parenteral nutrition treatment, a qualified nurse visited participants in their respective rooms to collect the necessary information. The anthropometric assessments encompassed measurements of weight and height. Weight was accurately obtained in kilograms using a scale with a precision of 100 g, whereas height was assessed in meters using a laser rod with a precision of 2 mm. Body mass index (kg/m²) was calculated. Bioelectrical impedance analysis and bioelectrical impedance vector analysis The body composition of the patients participating in the study was evaluated via bioelectrical impedance analysis within 72 h after receiving treatment with parenteral nutrition, performed by endocrinology nursing staff in the mornings. Whole‐body bioimpedance assessments were performed by using a single‐frequency bioelectrical impedance analysis apparatus (Nutrilab Whole Body Bioimpedance Vector Analyzer; Akern). Phase angle is expressed in degrees as arctan (reactance/R) × (180º/π). Bioelectrical impedance vector analysis measurements of patients were standardized for sex and age using data from healthy Italian adults. 18 , 19 , 20 Handgrip strength Muscle strength was tested by handgrip strength using a JAMAR hand dynamometer: The patient was in a sitting position with the elbow at 90°, using the dominant hand, and we performed three attempts; the median of the best hand was used; the assessment of strength was recorded in kilograms; we provided verbal encouragement. 21 Malnutrition and sarcopenia diagnosis The Global Leadership Initiative on Malnutrition includes five criteria to diagnose malnutrition in adults in a clinical setting. 22 The Global Leadership Initiative on Malnutrition criteria for disease‐related malnutrition combine both phenotypic and etiologic factors. European Working Group on Sarcopenia 2 defines sarcopenia as the presence of both low muscle strength and low muscle mass quantity. 23 Outcome measures Hospital stay was recorded as the number of days hospitalized. Lastly, mortality was defined as death within 1 year of follow‐up, either during hospitalization or after discharge, and patients' deaths were identified through a review of their medical records. Statistical analysis The sta...

## Results
Results Six hundred fourteen patients received parenteral nutrition, with a mean age of 64 ± 14.6 years; 58.2% were male. After 1 year, the mortality rate was 26.1%, and the average hospital stay was 27.9 ± 23.8 days. Twelve‐month survival was reduced in patients with low phase angle (57%) and low handgrip strength (62.8%) compared with those with preserved values (84% and 82.2%, respectively). In the multivariable logistic regression model adjusted for age, sex, and body mass index, each unit increase in phase angle and handgrip strength was associated with a 4% and 2% reduction in mortality odds, respectively (phase angle: odds ratio [OR], 0.6; 95% CI, 0.5–0.7; P < 0.001; handgrip strength: OR, 0.9; 95% CI, 0.9–1.0; P = 0.03624). Outcome measures Hospital stay was recorded as the number of days hospitalized. Lastly, mortality was defined as death within 1 year of follow‐up, either during hospitalization or after discharge, and patients' deaths were identified through a review of their medical records. RESULTS In this study, we examined data from 614 patients with parenteral nutrition. The average age of participants was 64 ± 14.6 years, and slightly more than half were men (58.2%, n = 358). At 1 year of follow‐up, the mortality rate was 26.1% ( n = 160). The mean length of admission was 27.9 ± 23.8 days. Some differences in general, nutrition, and functional status were observed between survivors and nonsurvivors. Survival showed significant differences ( P < 0.05) between variables, with younger patients (62.7 years), higher mean values for weight (71 vs 66.7 kg), body mass index (25.4 vs 24.2 kg/m 2 ), phase angle (4.9° vs 4.2°), body cell mass (24.7 vs 20.8 kg), appendicular skeletal muscle mass index (7.2 vs 6.8 kg/m 2 ), and handgrip strength (19.4 vs 15 kg). Other variables also demonstrated significant differences between survivors and nonsurvivors (Table 1 ). The data concerning the other variables obtained from the bioelectrical impedance analysis in estimated form are shown in Supporting Information S2: Table 1 . In addition, the same variables have been calculated specific to sex to see the differences in Supporting Information S2: Table 2 . Table 1 Anthropometric parameters, nutrition tools, bioelectrical impedance analysis, and functional test by survival or nonsurvival with PN. Parameters Total Survival Nonsurvival P value N 614 454 (73.9%) 160 (26.1%) 64 ± 14.6 62.7 ± 14.7 67.4 ± 13.9 <0.001 Height, cm 166 ± 9.48 166.7 ± 9.57 165.7 ± 9.25 0.279 Male sex 356 (58.1%) 265 (74.4%) 91 (25.6%) 0.720 Weight, kg 69.9 ± 18.0 71 ± 18 66.7 ± 17.7 0.009 BMI, kg/m² 24.6 ± 5.6 25.4 ± 5.6 24.2 ± 5.8 0.021 Rz, ohms 514 ± 120 506.3 ± 107.9 535 ± 147.6 0.009 Xc, ohms 42.5 ± 14.1 43.6 ± 14 39.2 ± 14 <0.001 PA, ° 4.7 ± 1.2 4.9 ± 1.2 4.2 ± 1 <0.001 SPA −1.2 ± 1.4 −1.0 ± 1.4 −1.6 ± 1.4 <0.001 Hydration, % 73.8 ± 5.4 76.4 ± 5.1 78.0 ± 6.1 0.001 Nutrition 679.0 ± 210 737.4 ± 204.5 623.2 ± 202.4 <0.001 BCM, kg 23.7 ± 7.4 24.7 ± 7.2 20.8 ± 7 <0.001 Na/K 1.3 ± 0.5 1.3 ± 0.4 1.6 ± 0.6 <0.001 HGS, kg 17.8 ± 10.5 19.4 ± 10.7 15 ± 10.1 <0.001 Enteral nutrition, % 53.6% 56.8% (79) 41% (16) 0.08 Surgical indication, % 50.8% 55.4% (77) 33.3% (13) 0.02 Prealbumin, mg/dl 15.5 ± 9.42 16.3 ± 9.9 12.9 ± 7 0.06 CRP/prealbumin ratio 1.3 ± 1.7 1.3 ± 1.8 1.3 ± 1.4 0.86 PN bags (numbers) 14.5 ± 14.8 12.5 ± 11 21.1 ± 22.6 0.01 Energy, kcal 1766 ± 243 1770.9 ± 220.4 1773.8 ± 310.2 0.49 Volume, ml 1706 ± 265 1729.5 ± 240.4 1608 ± 327.8 0.03 Protein, g nitrogen 13.6 ± 2.9 13.6 ± 2.9 13.2 ± 2.8 0.5 Carbohydrate, g 218 ± 41.9 221.9 ± 36.1 204.7 ± 57.5 0.06 Lipid, g 54.3 ± 9.2 54.2 ± 8.7 54 ± 10.2 0.93 Note : Data included are expressed as means ± standard deviations, percentages, or absolute numbers; P for comparison by survival and nonsurvival. Abbreviations: BCM, body cell mass; BMI, body mass index; CRP, C‐reactive protein; HGS, handgrip strength; Na/K, sodium‐potassium ratio; PA, phase angle differentiated by sex; PN, parenteral nutrition; Rz, resistance; SPA, standardized phase angle; Xc, reactance. John Wiley & Sons, Ltd. Malnutrition and sarcopenia status In the overall sample, 63.9% met the Global Leadership Initiative on Malnutrition criteria for malnutrition, and 20.6% were identified as having sarcopenia. The following frequencies were also observed in men: 34.3% met Global Leadership Initiative on Malnutrition criteria for undernutrition, and 29.1% were identified as sarcopenic. In women, 23.9% met Global Leadership Initiative on Maln...

## Figure captions
1. Figure 1. Receiver operating characteristic (ROC) curve of PA by mortality in women (A) and men (B). ROC curve of HGS by mortality in women (C) and men (D). Abbreviations: AUC, area under the curve; HGS, handgrip strength; PA, phase angle.
2. Figure 2. Kaplan‐Meier curves of PA (A) and HGS (B), adjusted for sex, in patients receiving parenteral nutrition. Abbreviations: HGS, handgrip strength; PA, phase angle.

## Table snippets
1. Table 1. Anthropometric parameters, nutrition tools, bioelectrical impedance analysis, and functional test by survival or nonsurvival with PN. | Parameters; Total; Survival; Nonsurvival; P value; N
2. Table 2. PA and HGS cutoff points for predicting mortality with parenteral nutrition. | Parameters; Sex; Cutoff point; Sensitivity, %; Specificity, %; AUC
3. Table 3. Univariable and multivariable logistic regression analysis for mortality with parenteral nutrition. | Parameters; Survivors; Nonsurvivors; OR (Univariable); OR (Multivariable); Age

## Candidate output (to be judged)

Abstract

This retrospective observational study investigated the prognostic value of morphofunctional assessments for 12-month mortality in hospitalized adults receiving parenteral nutrition (PN). The cohort comprised 614 patients (mean age 64 ± 14.6 years; 58.2% male). Within the **abstract_section** of this analysis, the primary outcomes were one-year mortality and hospital stay duration. Methods included bioelectrical impedance analysis to determine phase angle (PA) and dynamometry to measure handgrip strength (HGS). Mortality at one year was 26.1%. Survival was significantly lower in patients with low PA (57%) and low HGS (62.8%) compared to those with preserved values (84% and 82.2%, respectively). Receiver operating characteristic analysis established sex-specific cutoff points for PA and HGS predictive of mortality. In a multivariable logistic regression model adjusted for age, sex, and body mass index, each unit increase in PA and HGS was associated with a reduced odds of mortality (OR 0.6 and 0.9, respectively). The **section_text** further details that malnutrition and sarcopenia were significantly more prevalent among nonsurvivors. The evidence from this study indicates that low PA and low HGS, obtained early during PN, are strong and independent prognostic indicators for increased one-year mortality in this clinically complex population. These morphofunctional parameters provide valuable tools for risk stratification.

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