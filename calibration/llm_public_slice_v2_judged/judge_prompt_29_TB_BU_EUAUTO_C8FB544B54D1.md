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
The mammalian brain consists of millions to billions of cells that are organized into many cell types with specific spatial distribution patterns and structural and functional properties1-3. Here we report a comprehensive and high-resolution transcriptomic and spatial cell-type atlas for the whole adult mouse brain. The cell-type atlas was created by combining a single-cell RNA-sequencing (scRNA-seq) dataset of around 7 million cells profiled (approximately 4.0 million cells passing quality control), and a spatial transcriptomic dataset of approximately 4.3 million cells using multiplexed error-robust fluorescence in situ hybridization (MERFISH). The atlas is hierarchically organized into 4 nested levels of classification: 34 classes, 338 subclasses, 1,201 supertypes and 5,322 clusters. We present an online platform, Allen Brain Cell Atlas, to visualize the mouse whole-brain cell-type atlas along with the single-cell RNA-sequencing and MERFISH datasets. We systematically analysed the neuronal and non-neuronal cell types across the brain and identified a high degree of correspondence between transcriptomic identity and spatial specificity for each cell type. The results reveal unique features of cell-type organization in different brain regions-in particular, a dichotomy between the dorsal and ventral parts of the brain. The dorsal part contains relatively fewer yet highly divergent neuronal types, whereas the ventral part contains more numerous neuronal types that are more closely related to each other. Our study also uncovered extraordinary diversity and heterogeneity in neurotransmitter and neuropeptide expression and co-expression patterns in different cell types. Finally, we found that transcription factors are major determinants of cell-type classification and identified a combinatorial transcription factor code that defines cell types across all parts of the brain. The whole mouse brain transcriptomic and spatial cell-type atlas establishes a benchmark reference atlas and a foundational resource for integrative investigations of cellular and circuit function, development and evolution of the mammalian brain.

## Results
We present an online platform, Allen Brain Cell Atlas, to visualize the mouse whole-brain cell-type atlas along with the single-cell RNA-sequencing and MERFISH datasets. The results reveal unique features of cell-type organization in different brain regions-in particular, a dichotomy between the dorsal and ventral parts of the brain. Finally, we found that transcription factors are major determinants of cell-type classification and identified a combinatorial transcription factor code that defines cell types across all parts of the brain. The whole mouse brain transcriptomic and spatial cell-type atlas establishes a benchmark reference atlas and a foundational resource for integrative investigations of cellular and circuit function, development and evolution of the mammalian brain.

## Figure captions
1. Fig. 1. Transcriptomic cell-type taxonomy of the whole mouse brain. a , Left, the transcriptomic taxonomy tree of 338 subclasses organized in a dendrogram (10xv2: n = 1,699,939 cells; 10xv3: n = 2,341,350 cells; 10x Multiome: n = 1,687 nuclei). The neighbourhood and class levels are marked on the taxonomy tree. Classes marked with asterisks are included in the NN–IMN-GC neighbourhood. The IDs of every third subclass are shown to the right of the dendrogram. Full subclass names are provided in Supplementary Table 7 . Following subclass IDs, bar plots represent (left to right): major neurotra...
2. Fig. 2. Neuronal cell-type classification and distribution across the brain. a – l , UMAP representation ( a , c , e , g , i , k ) and representative MERFISH sections ( b , d , f , h , j , l ) of Pallium-Glut ( a , b ), Subpallium-GABA ( c , d ), HY–EA-Glut–GABA ( e , f ), TH–EPI-Glut ( g , h ), MB–HB-Glut–Sero–Dopa ( i , j ) and MB–HB–CB-GABA ( k , l ) neighbourhoods coloured by subclass. Each subclass is labelled with its ID and shown in the same colour in UMAP representations and MERFISH sections. a , c , e , g , i , k , Outlines in UMAP representations show cell classes. For full subcla...
3. Fig. 3. Modulatory neurotransmitter types and their distribution throughout the brain. a , b , Neuronal subclasses containing clusters that release modulatory neurotransmitters and their various co-release combinations with glutamate and/or GABA. UMAPs are coloured by subclass ( a ) and neurotransmitter type ( b ). c , Representative MERFISH sections showing the location of neuronal types expressing modulatory neurotransmitters. Cells are coloured by neurotransmitter type and labelled by subclass ID. See Supplementary Table 7 for detailed neurotransmitter assignment for each cluster. ADP, a...
4. Fig. 4. Non-neuronal cell types and immature neuronal types. a , UMAP representation of the NN–IMN–GC neighbourhood coloured by subclass. Outlines show cell classes. b – d , Three subpopulations indicated in a are highlighted and further investigated: astrocytes ( b ), ependymal cells ( c ) and VLMCs ( d ). UMAP representation and representative MERFISH sections of astrocytes ( b ), ependymal cells ( c ) and VLMCs ( d ) are coloured and numbered by cluster. b , c , Outlines in UMAPs show subclasses. e , Colocalization of tanycyte, ependymal cell and VLMC clusters around V3 and ME, as shown...
5. Fig. 5. Transcription factor modules across the whole mouse brain. a , Distribution of the number of differentially expressed transcription factors (TFs) between neuronal and non-neuronal classes, between classes, between subclasses, and within subclasses. b , Cross-validation accuracy for each cluster (left) or subclass (right) using classifiers built based on all 8,460 marker genes (all), 534 transcription factor marker genes (TF), 541 functional marker genes, 857 marker genes encoding adhesion molecules (adhesion), 534 randomly selected adhesion marker genes (random adhesion), or 534 ran...
6. Fig. 6. Brain region-specific features of cell types. a , Heat map showing the CCFv3 region distribution ( y axis) in each subclass ( x axis) for MERFISH cells. Bar graphs on the left show the broad CCFv3 regions, proportion of neuronal versus glial cells per region of interest (ROI), and proportion of neurotransmitter types per ROI. Bar graphs on the right show broad CCFv3 regions, Shannon diversity per subclass and supertype, and number of cells per ROI. Bar graphs on the top show number of cells per subclass, Gini coefficient and class assignment. Bar graphs on the bottom show subclass a...
7. Extended Data Fig. 1. scRNA-seq data analysis workflow. ( a ) Number of cells at each step in the scRNA-seq data analysis pipeline. The identification of doublets and low-quality clusters is described in more detail in Methods. The 10xv2 and 10xv3 data were first QC-ed and analyzed separately. After initial clustering the datasets were combined and QC-ed again before and after joint clustering. 10x Multiome snRNA-seq data was added to fill in gaps that were identified after joint clustering of 10xv2 and 10xv3 scRNA-seq data. ( b - c ) Gene count and qc score thresholds used for each of the...
8. Extended Data Fig. 2. MERFISH data generation, data processing and summary of results. ( a ) Workflow for generating and processing MERFISH data. ( b ) Correlation of gene detection between MERFISH and bulk RNA-sequencing for four different brain regions. ( c ) Histogram displaying the distribution of gene detection correlation between adjacent MERFISH sections. ( d - f ) Violin plots displaying distribution of cell volumes (d), gene detection (e), and mRNA molecule detection (f) for individual sections ordered from anterior to posterior (left panel) or cumulative distribution for the whole...

## Table snippets
1. Extended Data Table 1. Summary of the whole mouse brain cell type atlas

## Candidate output (to be judged)

Methods

This study generated a comprehensive transcriptomic and spatial cell-type atlas of the adult mouse brain. The atlas was constructed by integrating two primary datasets: a single-cell RNA sequencing (scRNA-seq) dataset and a spatial transcriptomic dataset generated using multiplexed error-robust fluorescence *in situ* hybridization (MERFISH).

The scRNA-seq dataset was generated from approximately 7 million profiled cells, of which approximately 4.0 million passed quality control (QC). This dataset combined cells from 10xv2 (n = 1,699,939 cells), 10xv3 (n = 2,341,350 cells), and 10x Multiome (n = 1,687 nuclei) platforms, as detailed in Fig. 1. The evidence does not specify the mouse strain, age, or detailed dissection protocols. Data processing involved separate initial QC and clustering for 10xv2 and 10xv3 datasets, followed by dataset combination, re-QC, and joint clustering. The 10x Multiome single-nucleus RNA-seq data was subsequently integrated to address gaps identified after joint clustering, as outlined in Extended Data Fig. 1a. Specific QC thresholds for gene counts and scores are shown in Extended Data Fig. 1b-c, but the exact numerical thresholds are not provided in the text.

The MERFISH spatial transcriptomic dataset comprised approximately 4.3 million cells. The workflow for MERFISH data generation and processing is summarized in Extended Data Fig. 2a. Data quality was assessed by correlating gene detection between MERFISH and bulk RNA-sequencing for four brain regions (Extended Data Fig. 2b) and by examining correlations between adjacent sections (Extended Data Fig. 2c). Distributions of cell volumes, gene detection, and mRNA molecule detection per section are shown in Extended Data Fig. 2d-f.

Cell-type classification was performed hierarchically, organizing cells into 4 nested levels: 34 classes, 338 subclasses, 1,201 supertypes, and 5,322 clusters, as summarized in the abstract. The transcriptomic taxonomy tree of 338 subclasses is presented in Fig. 1a. The correspondence between transcriptomic identity and spatial localization was analyzed by mapping cell types to anatomical regions in the Allen Common Coordinate Framework version 3 (CCFv3), with results visualized in a heat map in Fig. 6a.

All data are available through an online platform named the Allen Brain Cell Atlas, as stated in the abstract and results. Specific accession identifiers or repository URLs for the raw data are not provided in the evidence.

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