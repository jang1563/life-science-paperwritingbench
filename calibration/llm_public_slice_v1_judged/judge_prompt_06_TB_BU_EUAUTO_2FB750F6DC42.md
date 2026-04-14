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
Methods Eight electronic databases were searched from their inception until December 22, 2024. Two independent reviewers performed study screening, data extraction, and quality assessment using the Cochrane Collaboration’s Risk of Bias tool. A random-effects meta-analysis was conducted to synthesize data from included studies using mean differences (MDs). This study was registered with the Open Science Framework (OSF) (DOI: 10.17605/OSF.IO/VBPSM). Materials and methods This systematic review was conducted in accordance with the Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 Statement ( 39 ). The study protocol was registered prospectively with the Open Science Framework (OSF) (DOI: 10.17605/OSF.IO/VBPSM). Ethical approval was not required for this study. Eligibility criteria Studies were considered eligible for inclusion if they met the following criteria: (a) Study design: Parallel assignment randomized controlled trials (RCTs). (b) Population: Patients diagnosed with PCOS, provided the diagnosis met established criteria, according to those outlined by the 2003 Rotterdam Consensus Workshop of the European Society of Human Reproduction and Embryology and the American Society of Reproductive Medicine ( 40 ). (c) Intervention: Studies investigating the use of AT for the management of PCOS, including studies where AT was used as a standalone intervention or as an adjunctive therapy combined with conventional or complementary interventions. The specific AT methods considered were ear-point pressure seeds and electrical stimulation of the auricular VN. (d) Outcome measures: Trials that provided sufficient data for effect size estimation in the meta-analysis regarding clinical, hormonal, or metabolic outcomes. The exclusion criteria were as follows: (a) non-randomized studies, animal studies, reviews, protocols, case reports, and conference abstracts. In the case of duplicate studies, the most comprehensive or recent version was selected; (b) women with other underlying conditions, such as congenital adrenal hyperplasia, Cushing’s syndrome, thyroid hormone abnormalities, hyperprolactinemia, ovarian/adrenal tumors, or any severe medical, neurological, or psychiatric conditions, were excluded. Data sources and search strategy Two reviewers (XL and SX) independently performed a comprehensive search of the following electronic databases from their inception until December 22, 2024: PubMed, Embase, Web of Science, the Cochrane Library, China National Knowledge Infrastructure (CNKI), Wanfang Database, China Science and Technology Journal Database (VIP), and the Chinese Biomedical Literature Database (CBM). The searches were conducted without language restrictions. The search strategies were developed using a combination of keywords and controlled vocabulary (e.g., Medical Subject Headings (MeSH) in PubMed and Emtree in Embase) where available. The detailed search strategy for PubMed was as follows: “Ear acupuncture”[MeSH Terms] OR “auricular acupuncture”[MeSH Terms]. “ear”[tiab] OR “ear acupuncture”[tiab] OR “auricular therapy”[tiab] OR “auricular acupuncture”[tiab] OR “auricular acupressure”[tiab] OR “auricular acupoints”[tiab] OR “auricular point-sticking”[tiab] OR “auricular point pressing with bean”[tiab]. #1 OR #2. “Polycystic ovary syndrome”[MeSH Terms] OR “Stein–Leventhal Syndrome”[MeSH Terms]. “Polycystic ovary syndrome”[tiab] OR “polycystic ovarian syndrome”[tiab] OR “Stein–Leventhal syndrome”[tiab] OR “polycystic ovary disease”[tiab] OR “syndrome and polycystic ovary”[tiab] OR “PCOS”[tiab]. #4 OR #5. #3 AND #6. The complete search strategies for each database are provided in Supplementary Material S1 . Selection process Two reviewers (XL and SX) independently screened titles and abstracts for eligibility and performed deduplication using EndNote 2025. Full texts of the selected studies were then reviewed, and reasons for exclusion were systematically documented. Disagreements between the two ...

## Results
Results This systematic review and meta-analysis, which included 18 RCTs involving 1,231 patients with PCOS, found insufficient evidence to support the efficacy of AT as a stand-alone intervention for PCOS. However, AT used as an adjunct therapy exerted beneficial effects on PCOS outcomes. For AT combined with traditional Chinese medicine (TCM) formula versus TCM formula alone, a reduction in body mass index (BMI) (MD: –0.82, 95% confidence interval (CI): –1.60 to –0.03, P = 0.04) was observed. Moreover, the reductions were associated with scores on the Self-rating Anxiety Scale (SAS) (MD: –3.81, 95% CI: –6.26 to –1.36, P = 0.002) and Self-rating Depression Scale (SDS) (MD: –4.22, 95% CI: –7.74 to –0.69, P = 0.02). No significant effect was identified for hormonal profiles (luteinizing hormone (LH) levels, LH/follicle-stimulating hormone (FSH) ratio, testosterone (T) levels), metabolic parameters (fasting blood glucose (FBG) levels, fasting insulin (FINS) levels, or Homeostasis Model Assessment of Insulin Resistance (HOMA-IR)), or waist-hip ratio (WHR). For AT combined with metformin versus metformin alone, a reduction was observed in BMI (MD: –0.77, 95% CI: –1.23 to –0.31, P = 0.0009), WHR (MD: –0.03, 95% CI: –0.05 to –0.02, P < 0.0001), and LH levels (MD: –0.81, 95% CI: –1.05 to –0.57, P < 0.0001). For AT combined with acupuncture versus acupuncture alone, a reduction was observed in BMI (MD: –3.21, 95% CI: –5.09 to –1.33, P = 0.0008), LH levels (MD: –0.80, 95% CI: –1.16 to –0.43, P < 0.0001), and HOMA-IR (MD: –0.10, 95% CI: –0.16 to –0.05, P < 0.0001). A reduction was also associated with the LH/FSH ratio (MD: –1.39, 95% CI: –1.76 to –1.02, P < 0.0001). However, no significant effect was identified for WHR, and the evidence was insufficient for the effect on FINS levels. Results Study selection The study selection process is illustrated in Figure 1 . A systematic search identified 504 studies, of which 359 remained after duplicates were removed. During screening of titles and abstracts, 69 studies were deemed potentially relevant, and their full texts were retrieved for further assessment. Subsequently, a total of 47 studies were excluded for the following reasons: non-RCTs ( n = 6), failure to meet the intervention criteria ( n = 37), and lack of outcome data ( n = 4). In total, 18 RCTs met the eligibility criteria and were included in the systematic review and meta-analysis. Study characteristics The primary characteristics of the included studies are summarized in Tables 1 , 2 provides a summary of auricular acupoint application in the included studies. This systematic review included 18 RCTs (1,231 participants) from mainland China, published between 2011 and 2024. The mean age of participants ranged from 15.89 to 36.89 years, with a mean BMI ranging from 21.37 to 29.52 kg/m² across the studies. Intervention durations ranged from 1 to 6 months. Table 1 Main characteristics of all studies included in the meta-analysis. Author (year) Country PCOS definition criteria Sample size (I/C) Age (years, I/C) BMI (kg/m², I/C) Intervention Control Duration Outcome indicators Adverse reaction Zuo (2011) China Rotterdam 20/20 23.80 ± 4.56/24.50 ± 4.37 27.77 ± 2.42/28.00 ± 2.41 AT, 3 times/d + TCMF TCMF, 2 times/d 3mth ①③④⑤ None Ling (2015) China Rotterdam 36/36 NM/NM NM/NM AT, 3 times/d + TCMF TCMF, 2 times/d 3mth ③④⑤ None Chen (2021) China CMA 37/36 27.78 ± 4.52/28.06 ± 4.27 28.63 ± 3.51/27.92 ± 2.17 AT, 3 times/d + TCMF TCMF, 2 times/d 3mth ①②③④⑤ None Wan (2022) China CMA 35/36 26.43 ± 4.47/25.75 ± 4.83 22.56 ± 5.27/23.29 ± 2.11 AT, 2 times/d + TCMF TCMF, 2 times/d 3mth ①④⑤ None Zhang (2023) China Rotterdam 28/28 27.46 ± 4.24/28.49 ± 3.40 27.51 ± 3.94/27.80 ± 3.19 AT, 3 times/d + TCMF TCMF, 2 times/d 3mth ①②③④⑤⑥⑦⑧⑨⑩ None Zhu (2023) China Rotterdam 25/29 28.70 ± 3.71/28.00 ± 4.16 21.37 ± 1.91/21.61 ± 1.82 AT, 3 times/d + TCMF TCMF, 2 times/d 6mth ③⑤⑥⑦⑧⑨⑩ None Gan (2012) China Rotterdam 20/20 NM/NM NM/NM AT, 3 times/d + MET MET 500 mg, 3 times/d 3mth ①② NM Li (2020) China Rotterdam 30/30 29.70 ± 2.60/29.50 ± 2.40 26.30 ± 1.10/26.20 ± 1.00 AT, 3 times/d + MET MET 500 mg, 3 times/d 3mth ①⑥⑦⑧ NM Li (2021) China CMA 57/57 31.42 ± 3.22/31.48 ± 3.25 NM/NM AT, 3 times/d + MET MET 500 mg, 3 times/d 3mth ⑥⑦⑧ NM Sun (2023) China CMA 38/37 30.63 ± 4.22/30.89 ± 3.84 28.27 ± 1.28/27.94 ± 1.28 AT, 4 times/d + MET MET 500 mg, 3 times/d 3mth ①②③④⑤⑥⑦⑧ None Zhong (2023) China CMA 38/37 15.89 ± 1.72/15.97 ± 1.50 26.95 ± 0.63/27.19 ± 0.55 A...

## Figure captions
1. Figure 1. Literature screening process and results.
2. Figure 2. Quality of bias assessment of the included studies.
3. Figure 3. Forest plot displaying the effects of auricular therapy on BMI.
4. Figure 4. Forest plot displaying the effects of auricular therapy on SAS.
5. Figure 5. Forest plot displaying the effects of auricular therapy on SDS.
6. Figure 6. Forest plot displaying the effects of auricular therapy on WHR.
7. Figure 7. Forest plot displaying the effects of auricular therapy on T.
8. Figure 8. Forest plot displaying the effects of auricular therapy on LH.

## Table snippets
1. Table 1. Main characteristics of all studies included in the meta-analysis. | Author (year); Country; PCOS definition criteria; Sample size (I/C); Age (years, I/C); BMI (kg/m², I/C)
2. Table 2. Statistics of auricular acupoint application in the included studies. | Auricular acupoint (corresponding to GB standard number); Frequency of application; References; CO11 (Uterus); 13/19; Chen S Y 2021, Ling W 2015, Wan X 2022, Zhang W F 2023, Zuo J 2011, Gan L 2012, Li Y C 2020, Li Y C 2021, Li L N 2015, Li Q Q 2017, Liu H J 2016, Liu Y 2018, Ma J J 2017

## Candidate output (to be judged)

Abstract

This systematic review and meta-analysis evaluated the efficacy of auricular therapy (AT) for managing polycystic ovary syndrome (PCOS). The **methods_section** details a comprehensive search across eight databases up to December 2024, following PRISMA guidelines. Randomized controlled trials (RCTs) comparing AT, either alone or as an adjunct, to control treatments in patients with PCOS were included. Two reviewers independently conducted screening, data extraction, and risk-of-bias assessment. Data from 18 RCTs (n=1,231 patients) were synthesized via random-effects meta-analysis. The **results_section** indicates insufficient **evidence** for AT as a stand-alone intervention. However, as an adjunct, AT showed specific benefits. When combined with a traditional Chinese medicine formula, AT was associated with reductions in body mass index (BMI) and scores on anxiety and depression scales, but not with hormonal or most metabolic parameters. Adjunctive AT with metformin led to improvements in BMI, waist-hip ratio, and luteinizing hormone levels. Adjunctive AT with acupuncture yielded benefits for BMI, luteinizing hormone, the LH/FSH ratio, and insulin resistance. No significant effect on waist-hip ratio was found in this comparison, and the **section_text** notes that evidence for an effect on fasting insulin levels here was insufficient. Detailed methodologies and full results are provided in the **abstract_section** and subsequent report. In conclusion, while AT alone lacks demonstrated efficacy for PCOS, it may provide complementary benefits for certain anthropometric, hormonal, and psychological outcomes when combined with other therapies.

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