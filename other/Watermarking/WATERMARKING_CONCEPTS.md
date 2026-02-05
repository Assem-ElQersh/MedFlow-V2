# CXR Watermarking – Conceptual Directions for Integrity & Authenticity (Future Work)

This document presents **conceptual watermarking strategies** for ensuring the integrity and authenticity of chest X-ray (CXR) images in hospital environments.
It **does not implement** watermarking mechanisms and **does not recommend clinical deployment** without regulatory approval and extensive validation.

The purpose is to document **state-of-the-art (SOTA) approaches** that may be explored by professionals for hospital-grade systems under controlled governance.

---

## 1. Zero-Watermarking (Non-Embedding)

### Concept

The image itself is never modified. Instead, robust features are extracted from the original CXR and combined with a watermark (e.g., hospital or device identifier) to generate a **verification share** stored externally.

### Rationale for CXR

* Preserves diagnostic pixels entirely
* Eliminates the risk of image artifacts
* Avoids radiologist rejection due to image alteration

### Future Work Direction

* Extract deep, robust representations using pretrained encoders (e.g., VGG-based or context encoders)
* Combine hashed features with watermark bits using a reversible operation
* Store verification shares securely on a server
* Recompute and compare shares for integrity verification

### Conceptual Pseudocode

```
features = DeepFeatureExtractor(CXR)
share = XOR(hash(features), watermark_bits)
store(share)

// Verification
features_test = DeepFeatureExtractor(CXR_test)
share_test = XOR(hash(features_test), watermark_bits)

if share_test == stored_share:
    integrity_ok
```

---

## 2. Reversible Data Hiding (RDH)

### Concept

Metadata is embedded into the image in a way that allows **perfect recovery** of the original CXR after extraction.

### Techniques

* Prediction Error Expansion (PEE)
* Histogram Shifting

### Rationale for CXR

When metadata must accompany the image (e.g., patient or acquisition identifiers), RDH enables transport **without permanent pixel alteration**.

### Future Work Direction

* Restrict embedding to **Regions of Non-Interest (RONI)** to protect lung fields
* Enforce high visual fidelity (target PSNR > 50 dB)
* Validate exact reversibility under controlled pipelines

### Conceptual Pseudocode (PEE in RONI)

```
for each pixel p in RONI:
    pred = predict(p.neighbors)
    err = p - pred

    if err in embeddable_range:
        p' = pred + 2 * err + bit_to_embed

// Extraction
err' = p' - pred
bit = err' mod 2
p = pred + floor(err' / 2)
```

---

## 3. Hybrid Transform-Domain Dual Watermarking

### Concept

Embed two complementary watermarks:

* **Robust watermark** for ownership and authenticity
* **Fragile watermark** for tamper detection

### Transform Pipeline

**Discrete Wavelet Transform (DWT) → Discrete Cosine Transform (DCT) → Singular Value Decomposition (SVD)**

### Rationale for CXR

* Robust watermark resists compression and transmission artifacts
* Fragile watermark breaks under pixel-level modification, enabling tamper localization

### Future Work Direction

* Embed robust watermark in low-frequency components
* Embed fragile watermark in high-sensitivity bands
* Evaluate diagnostic impact rigorously

### Conceptual Pseudocode

```
LL, LH, HL, HH = DWT(CXR)
C = DCT(LL)
U, S, V = SVD(C)

S_modified = S + alpha * robust_watermark
C_modified = U * S_modified * V
LL_modified = IDCT(C_modified)

CXR_watermarked = IDWT(LL_modified, LH, HL, HH)
```

---

## 4. Blockchain-Linked QR Watermarking

### Concept

A QR code encoding a cryptographic hash and digital signature is embedded in the image and verified against an immutable ledger.

### Rationale for CXR

* Protects against image substitution and deepfake attacks
* Enables auditability and provenance tracking
* Supports forensic verification across institutions

### Future Work Direction

* Compute cryptographic hash of the original CXR
* Generate QR code containing hash and signer identity
* Embed QR using a robust embedding or learned decoder
* Register hash and metadata on a consortium blockchain

### Conceptual Pseudocode

```
hash = SHA256(CXR)
qr = QRencode(hash + doctor_signature)
CXR_watermarked = embed_qr(CXR, qr)

ledger.append(hash, timestamp, signer_id)

// Verification
qr_extracted = decode_qr(CXR_test)
if ledger.contains(qr_extracted.hash):
    integrity_ok
```

---

## Suggested Evaluation Framework (Conceptual)

* **Image Quality:** PSNR, SSIM, and radiologist diagnostic review
* **Robustness:** Compression, resizing, noise, and transmission stress tests
* **Security:** Tamper detection accuracy and false-positive analysis

---

## Clinical Deployment Considerations (Conceptual)

* Zero or negligible diagnostic impact
* Radiologist approval and acceptance testing
* Full compatibility with PACS and DICOM workflows
* Compliance with regulatory and audit requirements

---

## Disclaimer

This document outlines **future research directions only**.
Any real-world deployment of CXR watermarking requires:

* Medical governance
* Legal and regulatory review
* Extensive technical and clinical validation

---
