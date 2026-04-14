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
Single-cell atlases often include samples that span locations, laboratories and conditions, leading to complex, nested batch effects in data. Thus, joint analysis of atlas datasets requires reliable data integration. To guide integration method choice, we benchmarked 68 method and preprocessing combinations on 85 batches of gene expression, chromatin accessibility and simulation data from 23 publications, altogether representing >1.2 million cells distributed in 13 atlas-level integration tasks. We evaluated methods according to scalability, usability and their ability to remove batch effects while retaining biological variation using 14 evaluation metrics. We show that highly variable gene selection improves the performance of data integration methods, whereas scaling pushes methods to prioritize batch removal over conservation of biological variation. Overall, scANVI, Scanorama, scVI and scGen perform well, particularly on complex integration tasks, while single-cell ATAC-sequencing integration performance is strongly affected by choice of feature space. Our freely available Python module and benchmarking pipeline can identify optimal data integration methods for new data, benchmark new methods and improve method development.

## Results
Results Single-cell integration benchmarking (scIB) We benchmarked 16 popular data integration methods on 13 preprocessed integration tasks: two simulation tasks, five scRNA-seq tasks and six scATAC-seq tasks (Fig. 1 ). Each task posed a unique challenge (for example, nested batch effects caused by protocols and donors, batch effects in a different data modality and scalability up to 1 million cells) that revolved around integrating data on a particular biological system from multiple laboratories (Table 1 ). Our simulation tasks allowed us to assess the integration methods in a setting where the nature of the batch effect could be determined and the ground truth is known. In real data, we predetermined the ground truth by preprocessing and annotating data from 23 publications separately for each batch ( Methods ). Fig. 1 Design of single-cell integration benchmarking (scIB). Schematic diagram of the benchmarking workflow. Here, 16 data integration methods with four preprocessing decisions are tested on 13 integration tasks. Integration results are evaluated using 14 metrics that assess batch removal, conservation of biological variance from cell identity labels (label conservation) and conservation of biological variance beyond labels (label-free conservation). The scalability and usability of the methods are also evaluated. Table 1 Integration tasks for benchmarking Integration task Cell number Batches Tested features Pancreas 16,382 9 batches Widely used test data, protocols Lung 32,472 16 donors Human variation, protocols, spatial locations, high resolution subtypes, laboratories Immune (human) 33,506 10 donors Tissues, laboratories, similar cell types Immune (human and mouse) 97,952 23 samples Tissues, laboratories, similar cell types, species Mouse brain (RNA) 978,734 4 datasets Large dataset, spatial locations, nucleus versus cell, protocols Mouse brain small (ATAC, 3 tasks: windows, peaks, gene activity) 10,761, 11,597, 11,270 3 datasets Different modality, laboratories, technologies and feature spaces Mouse brain large (ATAC, 3 tasks: windows, peaks gene activity) 84,813 11 samples Different samples from 3 unbalanced datasets; different modality, laboratories, technologies and feature spaces Simulation 1 12,097 6 batches Variation in cellular compositions Simulation 2 19,318 16 batches Nested batch effects, composition variation Overview of the tasks used to benchmark data integration methods. The tested feature describes the unique challenge presented by the integration task. Donor refers to human individuals, sample is used when mice are involved and batches is the general term that includes dataset and sample batches. The six ATAC tasks are summarized in two entries. Each integration method was evaluated with regards to accuracy, usability and scalability ( Methods ). Integration accuracy was evaluated using 14 performance metrics divided into two categories: removal of batch effects and conservation of biological variance (Fig. 1 ). Batch effect removal per cell identity label was measured via the k -nearest-neighbor batch effect test (kBET) 11 , k- nearest-neighbor ( k NN) graph connectivity and the average silhouette width (ASW) 11 across batches. Independently of cell identity labels, we further measured batch removal using the graph integration local inverse Simpson’s Index (graph iLISI, extended from iLISI 21 ) and PCA regression 11 . Conservation of biological variation in single-cell data can be captured at the scale of cell identity labels (label conservation) and beyond this level of annotation (label-free conservation). Therefore, we used both classical label conservation metrics, which assess local neighborhoods (graph cLISI, extended from cLISI 21 ), global cluster matching (Adjusted Rand Index (ARI) 26 , normalized mutual information (NMI) 27 ) and relative distances (cell-type ASW) as well as two new metrics evaluating rare cell identity annotations (isolated label scores) and three new label-free conservation metrics: (1) cell-cycle variance conservation, (2) overlaps of highly variable genes (HVGs) per batch before and after integration and (3) conservation of trajectories ( Methods ). Two central challenges to benchmarking data integration methods are: (1) the diversity of output formats 28 , and (2) the inconsistent requirement on data preprocessing before integration. We addressed these challenges in three ways. First, all integration outputs were treated as separate integration run...

## Figure captions
1. Fig. 1. Design of single-cell integration benchmarking (scIB). Schematic diagram of the benchmarking workflow. Here, 16 data integration methods with four preprocessing decisions are tested on 13 integration tasks. Integration results are evaluated using 14 metrics that assess batch removal, conservation of biological variance from cell identity labels (label conservation) and conservation of biological variance beyond labels (label-free conservation). The scalability and usability of the methods are also evaluated.
2. Fig. 2. Benchmarking results for the human immune cell task. a , Overview of top and bottom ranked methods by overall score for the human immune cell task. Metrics are divided into batch correction (blue) and bio-conservation (pink) categories. Overall scores are computed using a 40/60 weighted mean of these category scores (see Methods for further visualization details and Supplementary Fig. 2 for the full plot). b , c , Visualization of the four best performers on the human immune cell integration task colored by cell identity ( b ) and batch annotation ( c ). The plots show uniform manif...
3. Fig. 3. Overview of benchmarking results on all RNA integration tasks and simulations, including usability and scalability results. a , Scatter plot of the mean overall batch correction score against mean overall bio-conservation score for the selected methods on RNA tasks. Error bars indicate the standard error across tasks on which the methods ran. b , The overall scores for the best performing method, preprocessing and output combinations on each task as well as their usability and scalability. Methods that failed to run for a particular task were assigned the unintegrated ranking for th...
4. Fig. 4. Benchmarking results for mouse brain ATAC tasks. a , Overview of top ranked methods by overall score for the combined large ATAC tasks. Metrics are divided into batch correction (blue) and bio-conservation (pink) categories. Overall scores are computed using a 40:60 weighted mean of these category scores (see Extended Data Fig. 5 for the full plot). b , The overall scores for the best performing methods on each task. Methods that failed to run for a particular task were assigned the unintegrated ranking for that task. Methods ranking below unintegrated are not suitable for integrati...
5. Fig. 5. Guidelines to choose an integration method. a , Table of criteria to consider when choosing an integration method, and which methods fulfill each criterion. Ticks show which methods fulfill each criterion and gray dashes indicate partial fulfillment. When more than half of the methods fulfill a criterion, we instead highlight the methods that do not by a cross; hence blank spaces denote a cross except in the three rows with labeled crosses. Method outputs are ordered by their overall rank on RNA tasks. Python and R symbols indicate the primary language in which the method is program...
6. Extended Data Fig. 1. Trajectories of the best and worst performers on the immune cell human integration task ordered by overall score on the set of cells belonging to the erythrocyte lineage. UMAP plots for the unintegrated data (left), the top 4 performers (upper rows a, b and c), and the worst 4 performers (lower rows a and b). Plots are colored by ( a ) diffusion pseudotime, ( b ) batch labels, and ( c ) cell identity annotations.
7. Extended Data Fig. 2. Diffusion maps of diffusion pseudotime (dpt) trajectories on integrated immune cell human data of the best and worst performers ordered by overall score. Diffusion maps of erythrocyte lineage cells of the 4 best (upper rows a, b and c) and 4 worst (lower rows a, b and c) integration methods, ordered by the overall score. Plots are colored by ( a ) diffusion pseudotime, ( b ) batch labels, and ( c ) cell identity annotations. In cases where it wasn’t possible to compute a trajectory due to disconnected clusters, all cells are colored yellow in (a).
8. Extended Data Fig. 3. Diffusion maps of diffusion pseudotime (dpt) trajectories on integrated immune cell human data of the best and worst performers ordered by trajectory score. Diffusion maps of erythrocyte lineage cells of the 4 best (upper row a, b and c) and 4 worst (lower row a, b and c) integration methods, ordered by the overall score. Plots are colored by ( a ) diffusion pseudotime, ( b ) batch labels, and ( c ) cell identity annotations. In cases where it wasn’t possible to compute a trajectory due to disconnected clusters, all cells are colored yellow in (a).

## Table snippets
1. Table 1. Integration tasks for benchmarking | Integration task; Cell number; Batches; Tested features; Pancreas; 16,382

## Candidate output (to be judged)

Methods

We benchmarked 16 data integration methods on 13 distinct integration tasks, comprising two simulation tasks, five single-cell RNA sequencing (scRNA-seq) tasks, and six single-cell ATAC sequencing (scATAC-seq) tasks (Fig. 1). These tasks represented challenges such as nested batch effects, integration across species and modalities, and scalability, drawing data from 23 publications and encompassing over 1.2 million cells (Table 1). Specific tasks included pancreas (16,382 cells; 9 batches), lung (32,472 cells; 16 donors), human immune (33,506 cells; 10 donors), human and mouse immune (97,952 cells; 23 samples), mouse brain RNA (978,734 cells; 4 datasets), and multiple mouse brain ATAC tasks with varying cell numbers and feature spaces (Table 1). Two simulation tasks (12,097 and 19,318 cells) provided ground truth for evaluation.

Each method was evaluated in up to 68 different setups per task, incorporating preprocessing decisions for scaling and highly variable gene (HVG) selection, resulting in 590 attempted integration runs. Methods that could not accept scaled input (LIGER, trVAE, scVI, scANVI) or required cell-type labels (scGen, scANVI) were run accordingly. Integration outputs (e.g., corrected matrices, embeddings) were evaluated separately, even from the same method.

Performance was assessed using 14 metrics across three categories: batch effect removal, conservation of biological variance from cell identity labels (label conservation), and conservation of biological variance beyond labels (label-free conservation) (Fig. 1). Batch removal metrics included kBET, k-nearest-neighbor graph connectivity, average silhouette width (ASW), graph iLISI, and PCA regression. Label conservation metrics included graph cLISI, Adjusted Rand Index (ARI), normalized mutual information (NMI), cell-type ASW, and isolated label scores. Label-free conservation metrics assessed cell-cycle variance, overlap of HVGs per batch, and trajectory conservation. New extensions to kBET and LISI scores were developed to handle diverse output formats consistently. An overall accuracy score was computed as a weighted mean of all applicable metrics, with a 40% weight for batch removal and a 60% weight for biological conservation. Usability and scalability were also evaluated, though specific measurement details are not provided in the evidence.

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