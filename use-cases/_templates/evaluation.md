# UC-{NNN}: {Title} — Evaluation

## Evaluation Overview

{Brief description of how this use case was evaluated — what was measured, over what time period, and with what methodology.}

---

## Baseline (Before AI)

| Metric                      | Value              | Source                         |
|-----------------------------|--------------------|--------------------------------|
| **Processing Time**          | {e.g., 15 min/item} | {How this was measured}       |
| **Error Rate**               | {e.g., 8%}         | {How this was measured}        |
| **Throughput**               | {e.g., 50/day}     | {How this was measured}        |
| **Cost per Transaction**     | {e.g., $12}        | {How this was calculated}      |
| **Human FTEs Required**      | {e.g., 3}          | {Role and allocation}          |

---

## Results (After AI)

| Metric                      | Before AI     | After AI      | Change         |
|-----------------------------|---------------|---------------|----------------|
| **Processing Time**          | {15 min}      | {30 sec}      | {-97%}         |
| **Error Rate**               | {8%}          | {2%}          | {-75%}         |
| **Throughput**               | {50/day}      | {500/day}     | {+900%}        |
| **Cost per Transaction**     | {$12}         | {$0.50}       | {-96%}         |
| **Human Involvement**        | {100%}        | {15% review}  | {-85%}         |

---

## Quality Assessment

### Accuracy Evaluation

| Test Set                    | Sample Size | Accuracy      | Notes                  |
|-----------------------------|-------------|---------------|------------------------|
| {e.g., Standard cases}       | {200}       | {97%}         | {Well-structured input} |
| {e.g., Edge cases}           | {50}        | {82%}         | {Handwritten, poor quality} |
| {e.g., Adversarial inputs}   | {30}        | {90%}         | {Deliberately tricky}   |

### Failure Analysis

| Failure Mode                | Frequency    | Impact         | Mitigation Applied      |
|-----------------------------|-------------|----------------|-------------------------|
| {e.g., Incorrect extraction} | {3%}        | {Medium}       | {Validation + human review} |
| {e.g., Hallucinated fields}  | {1%}        | {High}         | {Schema enforcement}     |
| {e.g., Timeout on large docs}| {2%}        | {Low}          | {Chunking strategy}      |

---

## Cost Analysis

### Operational Costs

| Cost Component              | Monthly Cost | Notes                          |
|-----------------------------|-------------|--------------------------------|
| **LLM API (tokens)**        | {$X}        | {Based on Y volume at Z price} |
| **Compute**                  | {$X}        | {AKS/App Service sizing}       |
| **Storage**                  | {$X}        | {Data volume}                  |
| **Other Services**           | {$X}        | {Search, queues, etc.}         |
| **Total Operational**        | **{$X}**    |                                |

### ROI Calculation

| Factor                      | Value                              |
|-----------------------------|------------------------------------|
| **Previous Cost (monthly)**  | {e.g., $15,000 in labor + errors} |
| **AI Solution Cost (monthly)** | {e.g., $2,000}                 |
| **Net Savings (monthly)**    | {e.g., $13,000}                   |
| **Implementation Cost**      | {e.g., $30,000 one-time}          |
| **Payback Period**           | {e.g., 2.3 months}                |

---

## User Feedback

### Quantitative

| Question                                    | Score (1-5) | Responses |
|---------------------------------------------|-------------|-----------|
| {e.g., "The AI output is accurate"}          | {4.2}       | {25}      |
| {e.g., "The system saves me time"}           | {4.7}       | {25}      |
| {e.g., "I trust the AI's recommendations"}   | {3.8}       | {25}      |

### Qualitative

> "{Direct quote from a user about what works well}"
> — {Role}

> "{Direct quote about what needs improvement}"
> — {Role}

---

## Limitations Discovered

| Limitation                          | Severity   | Workaround / Plan                  |
|-------------------------------------|-----------|-------------------------------------|
| {e.g., Poor on handwritten input}    | {Medium}  | {Route to human for these cases}    |
| {e.g., Slow on documents > 50 pages} | {Low}     | {Parallel chunking in next release} |
| {e.g., Non-English text unsupported} | {High}    | {Multilingual model in roadmap}     |

---

## Lessons Learned

### What Worked Well

- {Lesson 1}
- {Lesson 2}
- {Lesson 3}

### What Didn't Work

- {Lesson 1 — what was tried and why it failed}
- {Lesson 2}

### What We'd Do Differently

- {Recommendation 1}
- {Recommendation 2}

---

## Next Steps

| Priority | Action                            | Expected Impact                  |
|----------|----------------------------------|----------------------------------|
| High     | {e.g., Add multilingual support}  | {Expand to 3 more markets}       |
| Medium   | {e.g., Fine-tune for edge cases}  | {Reduce error rate by 50%}       |
| Low      | {e.g., Add self-service dashboard}| {Reduce support tickets}         |
