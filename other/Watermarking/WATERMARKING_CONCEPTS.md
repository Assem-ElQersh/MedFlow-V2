# CXR Watermarking Concepts – Future Work (Conceptual)

This document is **conceptual** and intended to outline **future work** directions for CXR integrity and authenticity. It does **not** implement watermarking, nor does it recommend clinical use without regulatory validation. The goal is to document SOTA ideas suitable for hospital‑grade deployment by professionals.

---

## 1) Zero‑Watermarking (Non‑Embedding)

**Idea:** Do not modify the image. Extract robust features from the original CXR and combine them with a watermark (e.g., hospital ID) to generate a **secret share** stored separately.

**Why for CXR:** Preserves diagnostic pixels 100% (no risk of artifacts).

**Future work concept:**
- Extract deep features (e.g., VGG19, context encoders).
- XOR features with watermark to create a server‑side share.
- Verify integrity by recomputing features and comparing shares.

**Conceptual pseudocode:**
```
features = DeepFeatureExtractor(CXR)
share = XOR(hash(features), watermark_bits)
store(share)

// verification
features2 = DeepFeatureExtractor(CXR_test)
share2 = XOR(hash(features2), watermark_bits)
if share2 == stored_share: integrity_ok
```

---

## 2) Reversible Data Hiding (RDH)

**Idea:** Embed metadata but allow perfect restoration of the original image.

**Techniques:** Prediction Error Expansion (PEE) and Histogram Shifting.

**Why for CXR:** If patient metadata must travel with the file, RDH allows exact recovery of the pristine image.

**Future work concept:**
- Embed only in RONI (Region of Non‑Interest) to protect lung fields.
- Target PSNR > 50 dB to ensure invisibility.

**Conceptual pseudocode (PEE in RONI):**
```
for each pixel p in RONI:
	pred = predict(p.neighbors)
	err = p - pred
	if err in embeddable_range:
		p' = pred + 2*err + bit_to_embed
extract:
	err' = p' - pred
	bit = err' mod 2
	p = pred + floor(err'/2)
```

---

## 3) Hybrid Transform‑Domain Dual Watermarking

**Idea:** Use combined transforms to embed robust and fragile watermarks simultaneously.

**Pipeline:** DWT → DCT → SVD

**Why for CXR:**
- **Robust watermark** survives compression/transfer.
- **Fragile watermark** breaks if any pixel is tampered.

**Future work concept:**
- Embed robust watermark in low‑frequency bands.
- Embed fragile watermark in sensitive bands for tamper detection.

**Conceptual pseudocode (DWT‑DCT‑SVD):**
```
LL, LH, HL, HH = DWT(CXR)
C = DCT(LL)
U, S, V = SVD(C)
S' = S + alpha * robust_watermark
C' = U * S' * V
LL' = IDCT(C')
CXR' = IDWT(LL', LH, HL, HH)
```

---

## 4) Blockchain & QR‑Coded Watermarking

**Idea:** Embed a QR code that contains a cryptographic hash and signature; verify against an immutable ledger.

**Why for CXR:** Protects against tampering and deepfake substitution.

**Future work concept:**
- Generate QR with image hash + doctor signature.
- Embed QR using a lightweight CNN decoder for robustness.
- Validate QR hash against a consortium blockchain ledger.

**Conceptual pseudocode:**
```
hash = SHA256(CXR)
qr = QRencode(hash + doctor_signature)
CXR' = embed_qr(CXR, qr)
ledger.append(hash, timestamp, signer_id)

// verification
qr_extracted = decode_qr(CXR_test)
if ledger.contains(qr_extracted.hash): integrity_ok
```

---

## Suggested Evaluation Protocol (Conceptual)
- **Image Quality:** PSNR, SSIM, and diagnostic review by radiologists.
- **Robustness Tests:** Compression, resizing, noise, transmission artifacts.
- **Security:** Tamper localization accuracy and false‑positive rate.

---

## Clinical Deployment Considerations (Conceptual)
- Zero diagnostic impact and radiologist approval.
- Compatibility with PACS/DICOM workflows.
- Regulatory compliance and auditability.

---

**Note:** This is a high‑level roadmap of watermarking techniques for CXR integrity/authenticity. Implementation requires medical governance, legal review, and extensive clinical validation.
