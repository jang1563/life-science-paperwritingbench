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
Atypical oxytocinergic functioning and altered microbiome compositions have both been implicated in autism, with growing evidence of interactions between these systems. However, how exogenous oxytocin influences the oral microbiome remains largely unexplored. This exploratory study examined for the first time how oral microbiome alterations link to oxytocinergic signalling in school-aged autistic (n = 80) and non-autistic children (n = 40). Additionally, we investigated the effect of four-weeks of intranasal oxytocin administration in autistic children on oral microbiome compositions immediately post-treatment (T1) and at four-weeks follow-up (T2). At baseline, lower endogenous salivary oxytocin levels were linked to greater microbial evenness and diversity, with twelve genera showing significant associations with oxytocin levels. In autistic children, four weeks of oxytocin administration was associated with significant increases in the abundances of Centipeda immediately post-treatment (T0-T1), alongside decreases in Moraxella (T0-T1), and subsequent reductions in Rothia observed at the four-week follow-up (T1-T2). Particularly, the genus Moraxella emerged as relevant, as lower baseline abundance was associated with higher endogenous oxytocin levels, and a stronger oxytocin-induced downregulation of its abundance correlated with greater increases in endogenous oxytocin levels, accompanied by hypomethylation of the oxytocin receptor gene. All results persisted after adjusting for nutrition and dental care. This exploratory study provides initial evidence for a role of the oxytocinergic system in shaping the oral microbiome in autistic children. These results may facilitate the integration of oral microbiome profiling into autism diagnostic criteria and stimulate future studies on the use of oxytocin as a therapeutic option targeting oral microbiome alterations.

## Methods
Methods Participant characteristics and general study design A single-center, double-blind, randomized placebo-controlled study was performed at Leuven University Hospital (Belgium) to assess the effects of four-weeks of twice daily intranasal administration of oxytocin (12 IU in the morning and 12 IU in the afternoon) on oral microbiome compositions in school-aged autistic children. Participants, assisted by their parents, self-administered either oxytocin or a placebo nasal spray at a dose of 12 IU in the morning and 12 IU in the afternoon (total daily dose 24 IU), corresponding to three puffs of 2 IU per nostril per administration. This dosing regimen was consistent with a conservative protocol previously applied in young autistic children [ 62 ]. The four-week treatment duration was in line with prior trials conducted in both children [ 63 ] and adults [ 28 ] with autism. Outcome measures were assessed at baseline ( T0 ), within 24 h after the 4-week administration period ( T1 ), and at a follow-up session, 4 weeks after cessation of the daily administrations ( T2 ). Eighty children with a formal autism diagnosis, aged between 8-12 years with a 4/1 boys/girls’ ratio, were recruited through the Leuven Autism Expertise Centre between July 2019 and January 2021. Alongside, forty age- and sex-matched non-autistic peers were recruited. The autistic children were randomized to receive either oxytocin (Syntocinon®, Sigma-tau) or placebo (all ingredients used in the active solution except the oxytocin compound) nasal sprays using a 1:1 randomization scheme (see Table 1 for the number of participants analyzed and Fig. 1 for the flow diagram). All research staff conducting the trial, participants and their parents were blinded to treatment allocation, as reported before in [ 35 ]. During the course of the treatment, participants were screened for potential side effects. Overall, side effects were minimal and not treatment-specific (see [ 35 ]). To assess potential baseline diagnosis-related differences, 40 neurotypical control children underwent similar assessments at baseline ( T0 ), but did not proceed into the nasal spray administration regimen. Fig. 1 Flow diagram of the baseline analyses and the effect of oxytocin administration on oral microbiome compositions at baseline (T0), at the end of four weeks of treatment (T1) and 4 weeks after cessation of the daily administrations (T2). Table 1 Participant characteristics. Autistic children Non-autistic children Independent t-test N Mean ± SD N Mean ± SD t-value p -value Age (years) 80 10.5 ±1.3 40 10.3 ±1.3 0.790 0.431 IQ Verbal IQ 78 107.7 ±15.2 40 117.3 ±12.2 -3.441 < 0.001** Performance IQ 79 102.3 ±14.1 40 107.8 ±12.2 -2.093 0.039* Gender Girl 16 (20%) 8 (20%) Boy 64 (80%) 32 (80%) Handedness Left 10 (12%) 6 (15%) Right 70 (88%) 34 (85%) ADOS-2 Social affect 65 7.3 ±3.7 / Restricted and repetitive behavior 65 1.9 ±1.2 / Total 65 9.4 ±4.1 / MWU-test Z p -value Clinical characteristics Social responsiveness SRS-2 80 89.2 ±21.3 40 21.9 ±12.7 8.833 <0.001** Repetitive/restrictive behavior RBS-R 80 27.4 ±15.7 40 2.5 ±4.7 8.376 <0.001** SCARED Child report 80 40.1±21.8 40 26.9±15.3 3.394 <0.001** Parent report 80 43.1±20.1 40 15.2±12.7 6.776 <0.001** Oxytocin group Placebo group Independent t-test N Mean ± SD N Mean ± SD t-value p -value Age (years) 40 10.5 ±1.3 40 10.5 ±1.3 0.188 0.851 IQ Verbal IQ 39 105.6 ±14.5 39 109.9 ±15.1 -3.247 0.216 Performance IQ 40 103.1 ±15.6 39 101.6 ±12.6 0.449 0.655 Gender Girl 8 (20%) 8 (20%) Boy 32 (80%) 32 (80%) Handedness Left 4 (10%) 6 (15%) Right 36 (90%) 34 (85%) ADOS-2 Social affect 33 7.4 ±3.7 33 7.3 ±3.8 0.164 0.870 Restricted and repetitive behavior 33 2.1 ±1.2 32 1.7 ±1.3 1.328 0.189 Total 35 9.8 ±3.9 33 9.0 ±4.2 0.813 0.419 MWU-test Z p -value Clinical characteristics Social responsiveness SRS-2 40 90.1 ±22.8 40 88.3 ±19.9 -0.197 0.844 Repetitive/restrictive behavior RBS-R 40 28.1 ±15.3 40 26.8 ±16.2 -0.506 0.613 SCARED Child report 40 ...

## Figure captions
1. Fig. 1. Flow diagram of the baseline analyses and the effect of oxytocin administration on oral microbiome compositions at baseline (T0), at the end of four weeks of treatment (T1) and 4 weeks after cessation of the daily administrations (T2).
2. Fig. 2. Associations between oral microbiota and endogenous oxytocin levels across all children independent of diagnosis. Linear regression lines are plotted across diagnostic groups (autistic: light-grey dots; non-autistic: dark- grey dots). Spearman correlation analyses were conducted for alpha-diversity indices, while microbial abundance was assessed using MaAsLin2. Multiple testing correction was applied, yielding adjusted p -values for the alpha-diversity analyses and q-values for the MaAsLin2 results, with significance defined as q <0.25. A visualizes the association with alpha-divers...
3. Fig. 3. Effects of four-week oxytocin administration on oral microbiome compositions. CLR-transformed abundances of the identified bacterial genera are visualized separately for the oxytocin and placebo groups at baseline (T0), at the end of four weeks of treatment (T1), and four-week after ending the treatment (T2). Specifically, the abundance of Tannerella is shown in Panel A, Moraxella in Panel B, Fusobacterium in Panel C, Actinomyces in Panel D, Centipeda in Panel E, Capnocytophaga in Panel F, and Rothia in Panel G.
4. Fig. 4. Associations between previous identified oxytocin-induced changes in bacterial abundance and oxytocin-induced changes in oxytocinergic signalling and behavioral characteristics. A visualizes the association between T0-T1 oxytocin-induced change in CLR-transformed Moraxella abundance and T0-T1 oxytocin-induced change in endogenous oxytocin levels. B visualizes the association between T0-T1 oxytocin-induced change in CLR-transformed Moraxella abundance and T0-T1 oxytocin-induced change in OXTR DNAm at CpG site -924. C visualizes the association between T0-T1 oxytocin-induced change in...

## Table snippets
1. Table 1. Participant characteristics. | Autistic children; Non-autistic children; Independent t-test; N; Mean ± SD; N
2. Table 2. Effect of oxytocin on oral microbiome compositions. | Post-hoc analyses; Correction confounding lifestyle variables; F-value; p -value; q-value; t-ratio

## Candidate output (to be judged)

Results

This exploratory study provides initial evidence for a link between the oxytocinergic system and the oral microbiome in children. As detailed in the **methods_section**, we conducted a double-blind, randomized, placebo-controlled trial in 80 autistic and 40 non-autistic children, assessing outcomes at baseline (T0), after four weeks of intranasal oxytocin or placebo administration (T1), and at a four-week follow-up (T2). Baseline analyses across all participants revealed that lower endogenous salivary oxytocin levels were associated with greater microbial alpha-diversity. Furthermore, the abundances of twelve specific bacterial genera showed significant associations with oxytocin levels, as illustrated in the **section_text** corresponding to Figure 2.

In autistic children, the four-week oxytocin administration regimen induced specific, time-dependent shifts in oral microbiome composition compared to placebo. Immediately post-treatment (T0-T1), oxytocin was associated with a significant increase in the abundance of *Centipeda* and a decrease in *Moraxella*. At the four-week follow-up (T1-T2), a subsequent reduction in *Rothia* was observed. These microbial changes are summarized in the **results_section** and depicted in Figure 3. The genus *Moraxella* was of particular relevance: its lower baseline abundance correlated with higher endogenous oxytocin levels. Moreover, within the oxytocin group, a stronger treatment-induced downregulation of *Moraxella* was associated with greater increases in endogenous oxytocin levels and with hypomethylation of the oxytocin receptor gene (Figure 4). All reported microbial associations and treatment effects persisted after adjusting for nutrition and dental care, a robustness check noted in the **abstract_section**. No significant baseline differences in age or gender were found between the autistic and non-autistic groups or between the treatment arms, as shown in Table 1.

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