# Separation of Concerns: The Recommended Architecture for Medical VLMs

This folder documents and prototypes the **architecturally correct** approach to using a Vision-Language Model (e.g. MedGemma) in a clinical setting. It is presented as the **production-grade design that should be applied** in real hospital systems, even though the main MedFlow implementation uses a simplified integration due to resource and scope constraints.

---

## Purpose of This Document

The MedFlow system was implemented using a **simplified VLM integration** (direct text generation for findings and chat) because of:

- Limited labeled clinical data  
- Limited compute (single-GPU / Colab-scale)  
- Project scope and timeline  

**However**, the recommended and more robust approach is a **modular architecture** where:

1. The VLM is used **strictly for representation and explanation**
2. A **dedicated classifier** handles all decision-making
3. Language is used to **explain** decisions, not to **make** them  

This folder contains the design rationale, architecture description, and a **proof-of-concept notebook** that implements this separation. The aim is to show awareness of best practice and to provide a clear path for future, production-ready deployment.

---

## The Problem We Avoid

If a system is built naïvely as:

> *"Here's an X-ray → MedGemma → Diagnosis: X"*

then it suffers from:

- No calibrated probabilities  
- No reproducible metrics or thresholding  
- No clear audit trail for decisions  
- No regulatory defensibility  
- Hallucinations presented as "reasoning"  

That is **not** a medical system—it is a chatbot with a stethoscope. The separation of concerns exists to prevent that.

---

## The Architecture (Separation of Concerns)

The notebook and this document enforce a **three-part** split:

### 1. MedGemma = Representation + Language Only

- Extracts **high-level visual semantics** from the image  
- Produces **embeddings** and **natural-language descriptions**  
- **Does not** output diagnoses or risk scores  
- **Does not** "decide" anything  

```
Image → MedGemma → embedding + text (descriptive only)
```

### 2. Classifier = The Only Decision Maker

- Consumes **embeddings** (and optionally other features)  
- Outputs **numeric, auditable probabilities** (e.g. risk scores)  
- Can be **trained, calibrated, and benchmarked** on labeled data  
- This is the **only** component that performs classification or risk assessment  

```
Embedding → classifier → risk scores / labels
```

### 3. Explanation = After the Fact

- Uses the **already-computed** scores and, if needed, the image  
- Generates **explanatory text** (e.g. visual patterns, consistency with scores)  
- **Explicitly avoids** diagnostic or decision language in the generation prompt  
- The explanation **cannot influence** the decision; that is deliberate  

```
Risk scores + image → explanation text (no decision)
```

---

## Why the Notebook Is Complex

MedGemma is **not** designed as a drop-in backbone like ResNet or ViT. Implementing this architecture required:

- Respecting chat templates and image token placement  
- Avoiding double-loading of large (~8.6GB) models  
- Handling token pooling and dtype issues  
- Avoiding misuse of `.generate()` and prompt-based "classification"  
- Managing VRAM and Colab constraints  

That complexity is the cost of doing it **correctly** instead of **conveniently**.

---

## What This Design Proves

The notebook in this folder demonstrates that:

- MedGemma **can** be used in a medical pipeline  
- **Without** using it as a classifier  
- **Without** letting the VLM output drive diagnostic decisions  
- **With** measurable, replaceable, and auditable decision logic  
- **With** language restricted to representation and explanation  

That is the right foundation for a system like MedFlow in a real clinical environment.

---

## What Was Not Applied in the Main MedFlow Implementation

For clarity and honesty in reporting:

| Not applied | Reason |
|-------------|--------|
| Separation between representation and classification | Limited labeled clinical data; no dedicated classifier training pipeline |
| Independent classifier training and calibration | Same data/compute constraints |
| Embedding-based audit logging | Scope and infra limits |
| Retrieval-grounded or score-grounded explanations | Simplified pipeline chosen for prototype |

This is **not** an excuse—it is a **scope boundary**. The correct approach was identified, designed, and prototyped here; full deployment was out of scope given available data and compute.

---

## What This Enables (The Payoff)

With this architecture in place, you can:

- **Train** the classifier head on proper datasets  
- **Calibrate** and threshold outputs for clinical use  
- **Swap** MedGemma (or the backbone) without redoing decision logic  
- **Add** federated learning or other training strategies  
- **Log** embeddings and scores for audits  
- **Defend** the system to clinicians, reviewers, and regulators  

—without rewriting the overall architecture.

---

## One-Sentence Takeaway

> **We did all this to force MedGemma to behave like a tool, not a judge.**

Everything else is implementation detail. This folder is the place where that principle is designed and demonstrated.

---

## Relation to MedFlow

- **MedFlow (main repo):** Uses a simplified integration (VLM for findings and doctor–AI chat) suitable for a constrained prototype.  
- **This folder:** Describes and prototypes the **better approach** that should be applied when data, compute, and scope allow—and that should be cited as the target architecture for production use.
