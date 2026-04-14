# LLM Evaluation

- model: `deepseek-chat` (request model: `deepseek-chat`)
- task source: `inspection-slice`
- prompt version: `v2`
- temperature: 0.2
- tasks: 30
- deterministic checks passed: 0 / 30
- mean citation_specificity score: 0.822
- forbidden-pointer-free outputs: 30 / 30
- total tokens: prompt=93692, completion=13134

## Per task family

| task_family | det. passed / total | mean citation | pointer-free / total | failure notes |
| --- | ---: | ---: | ---: | --- |
| abstract_from_evidence | 0 / 12 | 0.583 | 12 / 12 | traceability coverage below threshold (12) |
| methods_to_text | 0 / 12 | 0.972 | 12 / 12 | traceability coverage below threshold (12) |
| results_to_text | 0 / 6 | 1.000 | 6 / 6 | traceability coverage below threshold (6) |

## Per task

### abstract_from_evidence — DOI:10.1128/mbio.00933-24

- task_bundle_id: `TB:BU:EUAUTO:EFABE066E1CC`
- deterministic_checks_passed: **False**
- output words: 203
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1007/s00520-026-10393-8

- task_bundle_id: `TB:BU:EUAUTO:E372771DAE12`
- deterministic_checks_passed: **False**
- output words: 178
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1002/jpen.70069

- task_bundle_id: `TB:BU:EUAUTO:F383AAF2D9C8`
- deterministic_checks_passed: **False**
- output words: 221
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1002/advs.202500369

- task_bundle_id: `TB:BU:EUAUTO:EA7AA161E315`
- deterministic_checks_passed: **False**
- output words: 176
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1016/j.jmr.2022.107268

- task_bundle_id: `TB:BU:EUAUTO:4B6B808009BE`
- deterministic_checks_passed: **False**
- output words: 218
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.3389/fendo.2026.1726938

- task_bundle_id: `TB:BU:EUAUTO:2FB750F6DC42`
- deterministic_checks_passed: **False**
- output words: 218
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1111/cas.13569

- task_bundle_id: `TB:BU:EUAUTO:0647BFACA729`
- deterministic_checks_passed: **False**
- output words: 338
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.3389/fimmu.2026.1768201

- task_bundle_id: `TB:BU:EUAUTO:4EE60B35277A`
- deterministic_checks_passed: **False**
- output words: 286
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.3389/fpubh.2026.1763175

- task_bundle_id: `TB:BU:EUAUTO:9B993FC003FA`
- deterministic_checks_passed: **False**
- output words: 416
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.3389/fonc.2024.1389136

- task_bundle_id: `TB:BU:EUAUTO:8F1919A560A4`
- deterministic_checks_passed: **False**
- output words: 417
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1038/s41592-021-01336-8

- task_bundle_id: `TB:BU:EUAUTO:574F9D766255`
- deterministic_checks_passed: **False**
- output words: 327
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1002/cre2.70314

- task_bundle_id: `TB:BU:EUAUTO:DBF39730EECC`
- deterministic_checks_passed: **False**
- output words: 387
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.1186/s13018-023-04496-9

- task_bundle_id: `TB:BU:EUAUTO:DE9706E77A3C`
- deterministic_checks_passed: **False**
- output words: 236
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.1038/s41398-026-03964-0

- task_bundle_id: `TB:BU:EUAUTO:258F224C1556`
- deterministic_checks_passed: **False**
- output words: 247
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.2147/dddt.s585709

- task_bundle_id: `TB:BU:EUAUTO:9C556312AA06`
- deterministic_checks_passed: **False**
- output words: 302
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.1016/j.heliyon.2024.e30110

- task_bundle_id: `TB:BU:EUAUTO:03FB6686FE89`
- deterministic_checks_passed: **False**
- output words: 302
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.1093/bib/bbae048

- task_bundle_id: `TB:BU:EUAUTO:2D82A93D3D12`
- deterministic_checks_passed: **False**
- output words: 325
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### results_to_text — DOI:10.12688/f1000research.170388.2

- task_bundle_id: `TB:BU:EUAUTO:D80B030F985D`
- deterministic_checks_passed: **False**
- output words: 191
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1038/s41598-018-29441-3

- task_bundle_id: `TB:BU:EUAUTO:2A956C890C93`
- deterministic_checks_passed: **False**
- output words: 208
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1097/md.0000000000048111

- task_bundle_id: `TB:BU:EUAUTO:8613E1B4CEB3`
- deterministic_checks_passed: **False**
- output words: 236
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1097/md.0000000000047858

- task_bundle_id: `TB:BU:EUAUTO:4E02B5B6E6B7`
- deterministic_checks_passed: **False**
- output words: 196
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1007/s12672-024-01496-x

- task_bundle_id: `TB:BU:EUAUTO:D9F982457632`
- deterministic_checks_passed: **False**
- output words: 202
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.1002/cpz1.1028

- task_bundle_id: `TB:BU:EUAUTO:E427AF85C37D`
- deterministic_checks_passed: **False**
- output words: 189
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### abstract_from_evidence — DOI:10.3389/fendo.2026.1735660

- task_bundle_id: `TB:BU:EUAUTO:7491F1D683B2`
- deterministic_checks_passed: **False**
- output words: 241
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1111/cpr.70078

- task_bundle_id: `TB:BU:EUAUTO:4EB4DEC74F35`
- deterministic_checks_passed: **False**
- output words: 380
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.3390/nu18060904

- task_bundle_id: `TB:BU:EUAUTO:0A61A085F8E3`
- deterministic_checks_passed: **False**
- output words: 341
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 0.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1080/07853890.2026.2628353

- task_bundle_id: `TB:BU:EUAUTO:23CD58731E80`
- deterministic_checks_passed: **False**
- output words: 273
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1158/1541-7786.mcr-22-0835

- task_bundle_id: `TB:BU:EUAUTO:203BF5F7D3BE`
- deterministic_checks_passed: **False**
- output words: 495
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1038/s41586-023-06812-z

- task_bundle_id: `TB:BU:EUAUTO:C8FB544B54D1`
- deterministic_checks_passed: **False**
- output words: 362
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

### methods_to_text — DOI:10.1097/md.0000000000047994

- task_bundle_id: `TB:BU:EUAUTO:79EBDAF6B695`
- deterministic_checks_passed: **False**
- output words: 313
- scores: `{'traceability_coverage': 0.0, 'structure_compliance': 1.0, 'non_empty_output': 1.0, 'length_floor': 1.0, 'answer_support': 1.0}`
- notes: ['traceability coverage below threshold']

