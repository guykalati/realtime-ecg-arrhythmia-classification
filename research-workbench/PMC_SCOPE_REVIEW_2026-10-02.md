# PMC frozen 32 source-scope review —2026-10-02

**Status: draft labels from one Codex reviewer. No training admission; no gold labels; no independent expert validation.**

## Review basis

All six source JSONL SHA256 values, the candidate-file hash, and the review-packet hash match the frozen manifest. All 32 selected source objects were matched to the verified input files. The review used full extracted narrative paragraphs, including population/methods and the study question, rather than only abstracts or the short packet. The JSONL records preserve exact source quote substrings, paragraph indices, sections, XML SHA256 and verified source URLs.

Packet SHA256: `30df73638337136c3966cc456419652eafd3bdfb055e57904f5fda8a2e632df0`. Manifest SHA256 recorded for provenance: `904aaedeaeab78c62919ad62474fbb2ae304ba9152e97393ee7a6fe53e7d1c15`.

Separate figure/table objects, external supplements and raw participant data were not independently assessed. XML extraction completeness, retraction/notice reconciliation beyond the frozen holds, study quality, statistical validity, licensing, benchmark identity, split integrity and text-policy eligibility remain separate gates. Source publication year or research-article metadata does not establish an original human cardiac study.

## Draft counts

| Study tier | Count |
|---|---:|
| human_clinical_empirical | 21 |
| human_health_services | 2 |
| preclinical | 4 |
| veterinary | 0 |
| review_consensus | 1 |
| case_report | 1 |
| methods_only_or_unresolved | 1 |
| other | 2 |

| Cardiac centrality | Count |
|---|---:|
| core | 22 |
| background_only | 3 |
| uncertain | 7 |

These describe the selected 32 only, not prevalence in the 3,892 structural candidates or 5,819 discovery documents. Human clinical empirical is used broadly for original human health/physiology observations, including healthy volunteer and nutrition studies. Core includes direct cardiac physiology, cardiac-arrest/resuscitation and explicit cardiovascular risk questions; it is not equivalent to patient cardiac disease. Health services covers commissioning and delivered emergency-training studies; their boundary with clinical epidemiology is recorded.

## Per-article draft judgments

| Verified source | Tier | Cardiac centrality | Population/design or scope boundary |
|---|---|---|---|
| [PMC11353756](https://pmc-oa-opendata.s3.amazonaws.com/PMC11353756.1/PMC11353756.1.xml) | human_clinical_empirical | uncertain | 150 psoriasis patients,74 also with metabolic syndrome; retrospective cross-sectional. |
| [PMC7499680](https://pmc-oa-opendata.s3.amazonaws.com/PMC7499680.1/PMC7499680.1.xml) | human_clinical_empirical | uncertain | 10 children,6 confirmed and 4 suspected COVID cases. |
| [PMC11211012](https://pmc-oa-opendata.s3.amazonaws.com/PMC11211012.1/PMC11211012.1.xml) | review_consensus | uncertain | 15 RCTs totaling 2,956 participants; no new participant collection. |
| [PMC9269959](https://pmc-oa-opendata.s3.amazonaws.com/PMC9269959.1/PMC9269959.1.xml) | human_clinical_empirical | core | 30 FALD patients screened,27 analyzed;10 controls. |
| [PMC9738010](https://pmc-oa-opendata.s3.amazonaws.com/PMC9738010.1/PMC9738010.1.xml) | human_clinical_empirical | background_only | 1,771 Japanese health-promotion participants; cross-sectional biomarkers. |
| [PMC5994394](https://pmc-oa-opendata.s3.amazonaws.com/PMC5994394.1/PMC5994394.1.xml) | human_clinical_empirical | core | 206 selected referred outpatients without CAD evidence on PET/follow-up. |
| [PMC13217667](https://pmc-oa-opendata.s3.amazonaws.com/PMC13217667.1/PMC13217667.1.xml) | human_health_services | core | 10 caregiver volunteers; single-group pre/post simulation. |
| [PMC13500855](https://pmc-oa-opendata.s3.amazonaws.com/PMC13500855.1/PMC13500855.1.xml) | preclinical | core | Mouse MI models; purchased human coronary endothelial cells; secondary public human MI snRNAseq comparison. |
| [PMC7762686](https://pmc-oa-opendata.s3.amazonaws.com/PMC7762686.1/PMC7762686.1.xml) | methods_only_or_unresolved | uncertain | 16 schools; planned child recruitment and cardiovascular-risk measurements. |
| [PMC13080744](https://pmc-oa-opendata.s3.amazonaws.com/PMC13080744.1/PMC13080744.1.xml) | human_clinical_empirical | core | 550 patients; clinically indicated CMR and same-day echocardiography; retrospective follow-up. |
| [PMC9692711](https://pmc-oa-opendata.s3.amazonaws.com/PMC9692711.1/PMC9692711.1.xml) | case_report | core | Family pedigree, peripheral blood and exome investigation. |
| [PMC10808226](https://pmc-oa-opendata.s3.amazonaws.com/PMC10808226.1/PMC10808226.1.xml) | human_clinical_empirical | core | 1,377 patients; retrospective analysis of prospective single-center registry. |
| [PMC7211405](https://pmc-oa-opendata.s3.amazonaws.com/PMC7211405.1/PMC7211405.1.xml) | human_clinical_empirical | core | 3,015 retained community participants with repeated ECG heart-rate measurements. |
| [PMC9570993](https://pmc-oa-opendata.s3.amazonaws.com/PMC9570993.1/PMC9570993.1.xml) | human_clinical_empirical | core | 105 TOF patients undergoing CT angiography. |
| [PMC5460254](https://pmc-oa-opendata.s3.amazonaws.com/PMC5460254.1/PMC5460254.1.xml) | preclinical | core | Transgenic fly muscular/cardiac tissues and physiological recordings. |
| [PMC12755106](https://pmc-oa-opendata.s3.amazonaws.com/PMC12755106.1/PMC12755106.1.xml) | human_clinical_empirical | core | 436 male military police officers over 40; cross-sectional clinical risk assessment. |
| [PMC12340430](https://pmc-oa-opendata.s3.amazonaws.com/PMC12340430.1/PMC12340430.1.xml) | human_clinical_empirical | uncertain | 33,551 combined participants from CHARLS/HRS; cross-sectional analyses of longitudinal-cohort waves. |
| [PMC5074518](https://pmc-oa-opendata.s3.amazonaws.com/PMC5074518.1/PMC5074518.1.xml) | other | background_only | Kluyveromyces lactis enzyme, recombinant expression, crystallography and beer samples. |
| [PMC6733485](https://pmc-oa-opendata.s3.amazonaws.com/PMC6733485.1/PMC6733485.1.xml) | human_clinical_empirical | core | 669 CRT recipients;143 SonRtip atrial leads. |
| [PMC8096277](https://pmc-oa-opendata.s3.amazonaws.com/PMC8096277.1/PMC8096277.1.xml) | preclinical | core | Wild-type/transgenic and knockout zebrafish; human HEK293T cell work. |
| [PMC9286443](https://pmc-oa-opendata.s3.amazonaws.com/PMC9286443.1/PMC9286443.1.xml) | human_clinical_empirical | core | 301 retained Portuguese blue-collar workers; cross-sectional BP/cholesterol and schedule assessment. |
| [PMC6772048](https://pmc-oa-opendata.s3.amazonaws.com/PMC6772048.1/PMC6772048.1.xml) | human_health_services | core | 1,132,016 test results from 256,525 adult individuals; area-level analyses. |
| [PMC9598265](https://pmc-oa-opendata.s3.amazonaws.com/PMC9598265.1/PMC9598265.1.xml) | human_clinical_empirical | core | 13 female and 13 male amateur-trained team-sport players; crossover hypoxia exposure. |
| [PMC8905559](https://pmc-oa-opendata.s3.amazonaws.com/PMC8905559.2/PMC8905559.2.xml) | other | uncertain | Second-year medical students, cardiovascular physiology course; academic achievement and attitudes. |
| [PMC8391914](https://pmc-oa-opendata.s3.amazonaws.com/PMC8391914.1/PMC8391914.1.xml) | human_clinical_empirical | uncertain | 127 adult cancer patients testing positive for SARS-CoV-2; retrospective cohort. |
| [PMC12292771](https://pmc-oa-opendata.s3.amazonaws.com/PMC12292771.1/PMC12292771.1.xml) | human_clinical_empirical | core | 18 healthy men completing training/detraining follow-up. |
| [PMC10117984](https://pmc-oa-opendata.s3.amazonaws.com/PMC10117984.1/PMC10117984.1.xml) | human_clinical_empirical | core | 49 affected and 47 exposed healthy neonatal cord samples; fetal tissue and THP-1/human fibroblast experiments. |
| [PMC9387187](https://pmc-oa-opendata.s3.amazonaws.com/PMC9387187.1/PMC9387187.1.xml) | human_clinical_empirical | core | 26 PD patients in two groups of 13 and 24 matched controls. |
| [PMC9394444](https://pmc-oa-opendata.s3.amazonaws.com/PMC9394444.1/PMC9394444.1.xml) | preclinical | core | Murine RAW264.7, rat H9C2, and mouse-derived macrophages; parasite assays. |
| [PMC7540875](https://pmc-oa-opendata.s3.amazonaws.com/PMC7540875.1/PMC7540875.1.xml) | human_clinical_empirical | core | 27 young healthy volunteers; repeated lighting/time conditions with ICG/ECG. |
| [PMC4730864](https://pmc-oa-opendata.s3.amazonaws.com/PMC4730864.1/PMC4730864.1.xml) | human_clinical_empirical | background_only | Canadian grades6-12 school survey,47,203 respondents. |
| [PMC7961400](https://pmc-oa-opendata.s3.amazonaws.com/PMC7961400.1/PMC7961400.1.xml) | human_clinical_empirical | core | Nationwide multicenter prospective observational cardiac-arrest registry. |

## Cases needing scope adjudication

- Cancer/COVID and pediatric PICU COVID studies analyze cardiac comorbidity or arrhythmias within broader infection questions. They are marked uncertain, since analyzed subsidiary evidence is stronger than a background-only mention.
- Psoriasis/metabolic syndrome, stroke/sarcopenia, school-exergame protocol, cardiovascular-physiology education and noncardiac-surgery fluid meta-analysis need an explicit decision about cardiometabolic, cerebrovascular, educational and secondary-outcome scope. They remain uncertain.
- Three mixed translational cases preserve their components: S100A4 combines human clinical/tissue/cell work; ADAM17 combines mice, purchased human endothelial cells and secondary public human MI data; Mto1 combines zebrafish and human HEK293T cells. Human material does not automatically make the mechanistic latter studies original human clinical research.
- The SonR, imaging-comparison and shortened PET studies have genuine human clinical measurements despite method/device questions. The BOOSTH article is explicitly a protocol; the MVP paper is a family case investigation; the colloid paper explicitly synthesizes prior trials.

No article is admitted by this report. The next step is adjudicating the stated scope boundaries and confirming all independent eligibility gates before any corpus use.
