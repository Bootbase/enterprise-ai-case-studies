# UC-059: Autonomous Clinical Trial Patient Matching and Recruitment with Agentic AI

## Metadata

| Field            | Value                        |
|------------------|------------------------------|
| **ID**           | UC-059                       |
| **Category**     | Industry-Specific            |
| **Industry**     | Pharmaceutical / Life Sciences |
| **Complexity**   | High                         |
| **Status**       | `research`                   |

---

## Problem Statement

Clinical trial patient recruitment is the single largest bottleneck in drug development. Approximately 80% of clinical trials are delayed or closed because of enrollment failures (Antidote Technologies). Patient recruitment accounts for 32-40% of total trial costs — roughly $1.89 billion annually in the US pharmaceutical sector alone (Tufts CSDD). The average cost to recruit one patient is $6,500+, while replacing a patient who drops out costs $19,000+. Screen failures — patients who are evaluated but do not qualify — cost sponsors an average of $1,200 each and occur at rates of 15-30% across therapeutic areas. Meanwhile, 37% of trial sites under-enroll and 11% fail to enroll a single patient (Tufts CSDD). Each day a trial is delayed costs sponsors between $600,000 and $8 million in lost revenue from postponed product launch (Eastern Research Group / FDA). The manual process of matching patients in electronic health records (EHR) to complex, multi-criteria eligibility protocols is slow, error-prone, and fundamentally unscalable.

---

## Business Impact

| Dimension       | Description                               |
|-----------------|-------------------------------------------|
| **Cost**        | $6,500+ per enrolled patient; $1,200 per screen failure; recruitment = 32-40% of total trial budget ($1.89B/year in US). Average Phase III trial costs $11.5M in recruitment alone (Tufts CSDD). |
| **Time**        | 80% of trials delayed by enrollment; average enrollment period is 12-18 months for Phase III; each day of delay costs $600K-$8M in lost revenue (ERG/FDA). |
| **Error Rate**  | 15-30% screen failure rate across therapeutic areas; manual chart review misses ~20% of eligible patients due to unstructured data buried in clinical notes (JAMIA). |
| **Scale**       | ~440,000 active clinical trials globally (ClinicalTrials.gov, 2025); average Phase III trial requires 1,000-3,000 patients across 50-200 sites; each site coordinator manually reviews 50-100 charts per week. |
| **Risk**        | Trials that fail to enroll on time face protocol amendments ($500K+ each), site closures, regulatory timeline slippage, and potential loss of patent exclusivity window — each month of delay can cost a blockbuster drug ~$100M in revenue (Deloitte). |

---

## Current Process (Before AI)

1. **Protocol finalization**: Sponsor and CRO finalize inclusion/exclusion criteria — often 30-50 discrete eligibility requirements per protocol, including lab values, comorbidities, prior treatments, and demographic constraints.
2. **Site identification**: Clinical operations teams manually evaluate potential investigator sites based on historical enrollment performance, therapeutic area expertise, and geographic coverage. Feasibility questionnaires are sent to 200-500 candidate sites.
3. **Site activation**: Selected sites (typically 50-200) undergo regulatory submissions, IRB/ethics approvals, contract negotiation, and training — a process taking 3-6 months per site.
4. **Patient identification**: Site coordinators and study nurses manually review electronic health records, searching for patients who might meet eligibility criteria. This involves reading through unstructured clinical notes, lab results, imaging reports, and medication histories.
5. **Pre-screening**: Coordinators assess identified patients against each inclusion/exclusion criterion, often using spreadsheets or paper checklists. Ambiguous criteria require consultation with the principal investigator.
6. **Patient outreach**: Qualifying candidates are contacted by phone or during clinic visits. Many patients are unaware of relevant trials; physicians often lack time to discuss trial options.
7. **Formal screening**: Consented patients undergo screening visits with protocol-specified assessments. 15-30% are screen failures — disqualified after consuming site time and sponsor resources.
8. **Enrollment monitoring**: Sponsors track enrollment via clinical trial management systems (CTMS), but reactive intervention (adding sites, extending timelines) occurs only after enrollment shortfalls become apparent — typically months late.

### Bottlenecks & Pain Points

- **Unstructured EHR data**: 80% of clinical data is locked in unstructured notes, radiology reports, and pathology narratives — invisible to keyword-based searches and simple queries.
- **Complex eligibility logic**: Modern protocols have 30-50+ criteria with Boolean combinations, temporal constraints (e.g., "no chemotherapy within 6 months"), and lab value thresholds that require clinical reasoning to evaluate.
- **Site coordinator burden**: Coordinators spend 15-20 hours per week on manual chart review, limiting the number of patients they can screen and contributing to burnout and turnover.
- **Information asymmetry**: Patients and their treating physicians are often unaware of relevant trials — only 5-7% of adult cancer patients enroll in clinical trials (NCI).
- **Geographic and demographic bias**: Manual site selection perpetuates enrollment at the same high-performing academic centers, under-representing rural populations, minorities, and community oncology settings.
- **Reactive enrollment management**: Sponsors lack real-time visibility into enrollment velocity; corrective actions (protocol amendments, site additions) are triggered too late and are expensive.

---

## Desired Outcome (After AI)

An agentic AI system that autonomously orchestrates clinical trial patient matching and recruitment across the entire workflow — from protocol analysis through patient identification, site optimization, and enrollment monitoring. The system deploys specialized AI agents that: (1) parse and decompose complex eligibility criteria into machine-executable logic; (2) continuously scan structured and unstructured EHR data across health system networks to identify candidate patients in near real-time; (3) score and rank candidates by match confidence and enrollment likelihood; (4) optimize site selection using predictive analytics on historical performance, patient proximity, and diversity targets; (5) monitor enrollment velocity and autonomously trigger corrective actions when sites fall behind targets. Human clinical teams remain in the loop for final patient consent, clinical judgment on edge cases, and regulatory oversight.

### Success Criteria

| Metric                       | Target                                      |
|------------------------------|---------------------------------------------|
| Patient identification speed | From weeks to hours per cohort              |
| Screen failure rate          | Reduce from 15-30% to < 5%                 |
| Enrollment timeline          | 25-50% reduction vs. historical baseline (ConcertAI ACT) |
| Site activation time         | 30-40% reduction through automated feasibility |
| Patient-trial match accuracy | > 95% concordance with manual expert review |
| Diversity enrollment         | Meet FDA diversity action plan targets      |
| Coordinator time on screening| Reduce by 60-80% (from 15-20 hrs/wk to 3-5 hrs/wk) |

---

## Stakeholders

| Role                              | Interest                                                |
|-----------------------------------|---------------------------------------------------------|
| VP Clinical Operations (Sponsor)  | Reduce enrollment timelines and cost per patient; accelerate time-to-market |
| Principal Investigators (Sites)   | Reduce coordinator burden; improve screen success rate; increase enrollment credits |
| Site Study Coordinators           | Automated patient identification to replace manual chart review |
| Chief Medical Officer (Sponsor)   | Protocol feasibility validation; ensure patient safety in matching logic |
| Regulatory Affairs                | Compliance with ICH-GCP, 21 CFR Part 11, FDA diversity guidance |
| Patients                          | Increased awareness of relevant trials; reduced screen failure burden |
| Data Privacy / IT Security        | HIPAA-compliant EHR access; de-identification; audit trails |
| CRO Project Management            | Real-time enrollment dashboards; predictive site performance |
| Health Equity / DEI Officers       | Ensure diverse patient populations are identified and enrolled |

---

## Constraints

| Constraint              | Detail                          |
|-------------------------|---------------------------------|
| **Data Privacy**        | HIPAA (US), GDPR (EU) compliance for all patient data; EHR access requires BAA agreements with health systems; patient data must be de-identified or accessed under IRB-approved waivers; 21 CFR Part 11 for electronic records and signatures. |
| **Latency**             | Patient matching can be near-real-time (within hours of new EHR data); site feasibility is batch (daily/weekly); enrollment monitoring is continuous with alerting thresholds. |
| **Budget**              | AI platform costs must be offset by recruitment cost savings; typical ROI threshold: $2M+ savings on a Phase III trial to justify platform licensing ($200K-$500K/year). Market for AI in clinical trials projected to reach $18.62B by 2040 (GlobeNewsWire). |
| **Existing Systems**    | Must integrate with major EHR systems (Epic, Cerner/Oracle Health, MEDITECH); must feed into CTMS (Medidata Rave, Oracle Siebel CTMS, Veeva Vault); HL7 FHIR APIs required for interoperability. |
| **Compliance**          | ICH-GCP (Good Clinical Practice) guidelines; FDA 21 CFR Parts 11 and 50; EU Clinical Trials Regulation (CTR) No 536/2014; FDA Diversity Action Plans for clinical trial enrollment (2024 guidance). AI-assisted matching must produce auditable reasoning trails. |
| **Scale**               | Must support concurrent matching across 50-200 trial sites, 10-50 active protocols simultaneously, and health system networks with millions of patient records. Peak load during large oncology or cardiovascular Phase III trials. |

---

## Scope Boundaries

### In Scope

- Automated parsing of trial protocols and decomposition of eligibility criteria into structured, executable rules
- NLP-powered scanning of structured and unstructured EHR data (clinical notes, labs, imaging reports, medication histories) for patient identification
- Patient-trial matching with confidence scoring and explainable reasoning
- Predictive site selection and feasibility assessment using historical enrollment data
- Real-time enrollment monitoring with automated alerts and corrective action recommendations
- Integration with EHR systems (Epic, Cerner) via FHIR APIs and CTMS platforms (Medidata, Veeva)
- Diversity and inclusion analytics to support FDA diversity action plan compliance
- Audit trails and explainability for regulatory inspection readiness

### Out of Scope

- Electronic informed consent (eConsent) platforms and patient-facing consent workflows
- Clinical data management and EDC (electronic data capture) within the trial itself
- Adverse event detection and pharmacovigilance (covered by UC-050)
- Clinical documentation and medical coding (covered by UC-055)
- Drug discovery, target identification, and preclinical research
- Site payment and financial management
- Decentralized / virtual trial technology (wearables, remote monitoring devices)
