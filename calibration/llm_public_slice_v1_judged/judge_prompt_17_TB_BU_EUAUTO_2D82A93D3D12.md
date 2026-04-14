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
Accurate prediction of antibody-antigen complex structures is pivotal in drug discovery, vaccine design and disease treatment and can facilitate the development of more effective therapies and diagnostics. In this work, we first review the antibody-antigen docking (ABAG-docking) datasets. Then, we present the creation and characterization of a comprehensive benchmark dataset of antibody-antigen complexes. We categorize the dataset based on docking difficulty, interface properties and structural characteristics, to provide a diverse set of cases for rigorous evaluation. Compared with Docking Benchmark 5.5, we have added 112 cases, including 14 single-domain antibody (sdAb) cases and 98 monoclonal antibody (mAb) cases, and also increased the proportion of Difficult cases. Our dataset contains diverse cases, including human/humanized antibodies, sdAbs, rodent antibodies and other types, opening the door to better algorithm development. Furthermore, we provide details on the process of building the benchmark dataset and introduce a pipeline for periodic updates to keep it up to date. We also utilize multiple complex prediction methods including ZDOCK, ClusPro, HDOCK and AlphaFold-Multimer for testing and analyzing this dataset. This benchmark serves as a valuable resource for evaluating and advancing docking computational methods in the analysis of antibody-antigen interaction, enabling researchers to develop more accurate and effective tools for predicting and designing antibody-antigen complexes. The non-redundant ABAG-docking structure benchmark dataset is available at https://github.com/Zhaonan99/Antibody-antigen-complex-structure-benchmark-dataset.

## Methods
MATERIALS AND METHODS Benchmark construction summary In the data construction phase, three sources were utilized to ensure comprehensive coverage and obtain a large number of antibody–antigen complexes. We obtained two lists of antibody-containing structures from the SACS [ 28 ] resource and the SAbDab [ 29 ] resource. Furthermore, we also identified antibody–antigen complexes by an advanced search in the PDB resource. While the SACS and SAbDab databases already contain data from the PDB, our approach is driven by the fact that our initial PDB searches rely on keywords like ‘antibody’ and ‘complex’, which could potentially overlook certain complexes. However, any antibody–antigen complexes that are missed via advanced search in the PDB can be located and added to our dataset from the other two databases for supplementation. Our analysis revealed that the antibody–antigen complexes sourced from the three resources are complementary, and no resource can fully cover them. Complexes were only released after 1 June 2019 (based on the BM5.5 dataset update in May 2019), and structures that only contained antibodies were not included in our dataset. To identify the unbound structures of antibodies and antigens within each antibody–antigen complex, we performed the BLAST [ 31 , 32 ] program to search against all amino acid sequences in the PDB. Various criteria were used to identify the unbound structures: (1) \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} \begin{equation*} Identity > 93\%, Alignment\ coverange > 80\%, E- value < {10}^{-5} \end{equation*}\end{document} To ensure a fair evaluation of the docking accuracy, we have performed the de-redundancy on the dataset. Two structures are considered redundant if the sequence alignments evaluated by Identity and E-value [Equation ( 2 )], and structure alignment results evaluated by root-mean-square distance (RMSD) [Equation ( 3 )] satisfy (2) \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} \begin{equation*} Identity > 60\%,\ E- value<{10}^{-30} \end{equation*}\end{document} (3) \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} \begin{equation*} RMSD < 5 \overset{\circ}{\text A} \end{equation*}\end{document} After the de-redundancy stage, 105 antibody–antigen complexes were screened that contained both unbound antibodies and antigens structures. We prepared structure files for the bound and unbound structures of the above complexes as a benchmark dataset. Similar to the data processing in BM5, each complex in the dataset contains the fewest protein chains that correctly reflect the binding process [ 6 ]. For the structure files, we aligned the bound and unbound structures and kept only the ATOM fields. For some complexes containing two antibody–antigen interfaces, we also prepared two sets of structure files accordingly. As shown in Figure 1 , complex 7A5S has two interfaces. Comparing the two interfaces, the antibody and antigen components have different binding sites. Some unbound sequences are much longer than bound sequences. For these cases, we truncated the unbound sequences to match the lengths of the bound sequences, leaving only a portion of the unbound structure to facilitate docking. For convenience of use, we also provided untruncated PDB format files for the 25 truncated cases. Figure 1 An illustration of the case with two antibody–antigen interfaces. Complex 7A5S has two distinct interfaces: interface 1 and interface 2, which are highlig...

## Figure captions
1. Figure 1. An illustration of the case with two antibody–antigen interfaces. Complex 7A5S has two distinct interfaces: interface 1 and interface 2, which are highlighted in circles.
2. Figure 2. Several representative cases for three difficulty levels: Rigid, Medium and Difficult. ( A ) Rigid case: sdAb case 6JB8( \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} $\mathrm{I}-\mathrm{RMSD}=0.938 \overset{\circ}{\text A},{f}_{non- nat}=0.344$\end{document} ) and mAb case 6Q0O ( \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepac...
3. Figure 3. Dataset classification. The antibody and antigen components of the antibody–antigen complexes were individually aligned with sequences in PDB. Based on the availability of corresponding unbound structures for the antibody/antigen's bound configurations within the comparative analysis, these complexes can be categorized into four distinct groups: unbound-unbound, unbound-bound, bound-unbound, and bound-bound. Non-redundant datasets can be further divided based on resolution and antigen length.
4. Figure 4. Pipeline for constructing antibody–antigen complex dataset.
5. Figure 5. Cases with similar sequences but distinct structures. ( A ) Structure of complex 6ZDG. ( B ) Structure of complex 6ZER. Despite having highly similar sequences (100% identity in all three chain types), these two complexes exhibit markedly different structures.
6. Figure 6. A pipeline for removing redundant.
7. Figure 7. A pipeline for updating the antibody–antigen complex structure dataset.
8. Figure 8. The antibody and antigen components of complex 6OTC and their unbound structures. ( A ) The antibody component of 6OTC and its unbound structures. According to the sequence alignment results, the antibody component of 6OTC has multiple unbound structures and shows different conformational changes (5VZ1: RMSD = 0.790 Å; 6B6Z: RMSD = 0.784 Å; 7T98: RMSD = 1.975 Å; 7VMZ: RMSD = 2.127 Å; 7T99: RMSD = 2.254 Å). ( B ) The antigen component of 6OTC and its unbound structures. The antigen component of 6OTC also has multiple unbound structures (4GH9: RMSD = 0.538 Å; 4GHA: RMSD = 0.416 Å; 4...

## Table snippets
1. Table 1. Composition of the updated docking benchmarks | Benchmark version 4.0; Benchmark version 5.0; Benchmark version 5.5; All; 175; 230
2. Table 2. Antibody-antigen complex structure composition of the different docking benchmarks | Benchmark version 4.0; Benchmark version 5.0; Benchmark version 5.5; All antibody-antigen cases; 24; 40
3. Table 3. The statistical data and criteria for classifying cases by \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} $\mathrm{I}-\mathrm{RMSD}$\end{document} and \documentclass[12pt]{minimal} \usepackage{amsmath} \usepackage{wasysym} \usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsbsy} \usepackage{upgreek} \usepackage{mathrsfs} \setlength{\oddsidemargin}{-69pt} \begin{document} ${f}_{non- nat}$\end{docum...

## Candidate output (to be judged)

Results

We constructed and characterized a comprehensive, non-redundant benchmark dataset for antibody-antigen (ABAG) docking, designed as an updated and expanded resource for method evaluation. The full methodological details for this construction are provided in the **methods_section**. In total, 112 new antibody-antigen complexes were curated and added to the existing Docking Benchmark 5.5 (BM5.5). This expansion includes 14 single-domain antibody (sdAb) and 98 monoclonal antibody (mAb) cases, and intentionally increases the proportion of complexes classified as 'Difficult' to pose a more rigorous challenge to docking algorithms. The final dataset encompasses diverse antibody types, including human/humanized, sdAb, and rodent antibodies, as summarized in the **abstract_section**.

Following a multi-source data collection strategy, a stringent de-redundancy process was applied. This process, detailed in the **results_section** evidence, employed criteria of sequence identity, E-value, and structural RMSD to yield 105 high-quality complexes for which unbound structures for both the antibody and antigen components were available. For some complexes, such as 7A5S which features two distinct binding interfaces, multiple structure files were prepared. To facilitate docking, unbound sequences longer than their bound counterparts were truncated in 25 cases, though untruncated files are also supplied.

Each complex was characterized and categorized by docking difficulty based on interface RMSD (I-RMSD) and the fraction of non-native contacts (*f*<sub>non-nat</sub>). Cases were classified as Rigid, Medium, or Difficult, providing a stratified benchmark. Further analysis categorized complexes into four groups (e.g., unbound-unbound) based on the availability of unbound structures, as illustrated in the **section_text** of the associated figures. This structured characterization provides clear **evidence** for the dataset's utility in testing algorithmic performance across a spectrum of docking challenges. The completed benchmark dataset is publicly available to support the development of more accurate computational docking methods.

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