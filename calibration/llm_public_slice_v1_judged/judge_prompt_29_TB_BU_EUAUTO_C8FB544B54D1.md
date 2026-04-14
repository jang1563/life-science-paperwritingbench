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

The methodological approach for generating the whole adult mouse brain cell-type atlas integrated large-scale single-cell transcriptomic profiling with spatially resolved molecular imaging. The complete workflow is detailed in the **methods_section** of the source publication. In brief, the atlas was constructed by combining two primary datasets. First, a single-cell RNA sequencing (scRNA-seq) resource was generated, profiling approximately 7 million cells, of which around 4.0 million passed stringent quality control metrics. Second, a spatial transcriptomic dataset was produced using multiplexed error-robust fluorescence in situ hybridization (MERFISH), encompassing approximately 4.3 million cells. The integration and joint analysis of these complementary datasets provided the foundational **evidence** for a spatially informed taxonomy. As noted in the **abstract_section**, the resulting atlas is hierarchically organized into 4 nested classification levels: 34 classes, 338 subclasses, 1,201 supertypes, and 5,322 clusters. All analytical procedures for data processing, integration, clustering, and annotation, including the specific quality control thresholds and computational pipelines referenced in Extended Data Figures, are described in the primary **section_text**. The exact parameters for scRNA-seq library preparation, MERFISH probe design, tissue processing, and imaging are not detailed in the provided evidence but are contained within the full methods of the source paper. The online Allen Brain Cell Atlas platform was developed to enable public exploration and visualization of both the integrated atlas and the underlying single-cell and MERFISH datasets.

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