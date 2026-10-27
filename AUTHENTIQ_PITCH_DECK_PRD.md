# Product Requirements Document (PRD) & Slide-Deck Specification
## Project: AuthentiQ — Sovereign Multi-Modal Content Intelligence Platform

> **Instructions for Claude / Presentation AI:**
> Use this document to generate an **8-Slide Executive Pitch Deck / Presentation**.
> - **Slide Count:** Exactly 8 slides.
> - **Design Aesthetic:** Minimalist sovereign enterprise style inspired by **Sarvam.ai** (warm pearl and obsidian palettes, high-contrast monospace typography for metrics, architectural bounding boxes, clean pill tags, and zero cluttered clip-art).
> - **Visual Metaphors:** Architectural gateways, neural network node linkages, timeline scrubber bars, Merkle tree blocks, and weighted balance scales.
> - **Tone:** Technical, authoritative, enterprise-grade, privacy-first.

---

### Slide 1: Title & Opening Hook (Starting Slide)
* **Slide Title:** **AuthentiQ**
* **Subtitle:** Sovereign Multi-Modal AI Detection, Decoupled Evaluation & Cryptographic Audit Ledger
* **Tagline:** *"Detecting synthetic content with empirical precision, evaluating human merit without bias."*
* **Presenter / Team:** Core Engineering Team · AI Content Intelligence Initiative (Hackathon 2026)
* **Metadata Badges:**
  - `Sovereign Deployment`: 100% On-Premise / Edge Inference (Zero Cloud API Dependencies)
  - `Multi-Modal Scope`: Text Syntactic Forensics + Temporal Video Deepfake Frame Inspection
  - `Regulatory Standard`: GDPR Compliant · SHA-256 Non-Repudiation Chain
* **Visual Direction for Slide 1:**
  - Clean centered architectural gateway layout.
  - Floating pill tags indicating: `Text Ensemble (TF-IDF + LightGBM)`, `Vision Engine (EfficientNet-B0 + MTCNN)`, `Decoupled Rubrics`, `Chained Ledger`.
  - Contrast warm background with obsidian pill elements.

---

### Slide 2: Problem Statement — The Crisis of Synthetic Saturation
* **Header:** The Breakdown of Trust in Academic, Corporate & Media Submissions
* **The Dual Crisis:**
  1. **Generative Saturation:** LLMs and deepfake generators have commoditized boilerplate text, audio synthesis, and face-swapped video. Existing tools either rely on brittle perplexity heuristics (high false positives) or invasive third-party cloud APIs that leak proprietary candidate data.
  2. **The "Disqualification Trap":** Legacy checkers auto-reject submissions based on raw AI detection scores. This penalizes non-native English speakers (stylistic false positives) and punish authentic thinkers who legitimately used AI as an exploratory research aid.
* **Key Pain Points:**
  - **High False Positive Rates:** Innocent academic essays and student proposals flagged unjustly due to formal phrasing.
  - **Single-Modal Blindness:** Detectors inspect text or video in silos, missing multimodal synthetic workflows (e.g., video interviews with generated scripts).
  - **Audit Vulnerability:** Zero proof trail—when a candidate disputes a rejection, organizations have no cryptographically sealed evidence of how or why the decision was reached.

---

### Slide 3: The AuthentiQ Solution — Merit-First Content Intelligence
* **Header:** A New Paradigm: Decoupling Quality from AI Involvement
* **Core Philosophy:**
  - **Decoupled Evaluation:** Content is evaluated on **intellectual substance and weighted qualitative merit** (Relevance, Reasoning Rigor, Novelty). AI involvement is treated as an **advisory risk signal**, triggering secondary human review rather than automatic rejection.
  - **True Sovereign Privacy:** All inference runs on local weights without pinging external proprietary APIs (zero OpenAI/Anthropic/AWS leakage).
* **Platform Pillars:**
  1. **Forensic Text Engine:** Character + word TF-IDF and hand-crafted stylistic features feeding an ensemble of SGD and LightGBM with sentence-level heatmaps.
  2. **Temporal Video Deepfake Engine:** MTCNN face crop pipeline + fine-tuned EfficientNet-B0 with frame-by-frame scrubbers.
  3. **Decoupled Shortlisting Studio:** Live dynamic rubric sliders that recalculate cohort rankings in real-time.
  4. **Immutable Verification Ledger:** SHA-256 hash chaining where every automated inference and human override is tamper-evident.

---

### Slide 4: Unified System Architecture & Sovereign Stack
* **Header:** High-Throughput, Zero-Cloud-Dependency Architecture
* **System Component Breakdown:**
  - **Frontend Client (SPA):**
    - Built with **React 19** + **Vite**.
    - Pure Vanilla CSS design system with customized tokens (`Space Grotesk`, `Plus Jakarta Sans`, `JetBrains Mono`).
    - Responsive layout with zero bloated UI libraries.
  - **Backend API & Orchestration:**
    - High-concurrency **FastAPI** application serving both the SPA static distribution and `/api/v1` REST endpoints on a single unified server (`port 8000`).
    - **Dual-Engine Process Isolation:** Solves the macOS/Linux OpenMP conflict between PyTorch and LightGBM by running video inferences in an isolated runner process.
  - **Local Database & Storage:**
    - Lightweight async **SQLite (aiosqlite)** with automatic table bootstrapping for instant zero-config spin-up, fully hot-swappable to PostgreSQL.
  - **Cryptographic Engine:**
    - Chained block hashes linking each transaction to the parent block's SHA-256 digest with automated Merkle root validation.

---

### Slide 5: Multi-Modal AI Detection Engines & Performance
* **Header:** Empirical Text Forensics & Video Deepfake Frame Scrubber
* **Engine 1: Text Forensic Ensemble (TF-IDF + SGD + LightGBM)**
  - **Feature Matrix:** 12-dimensional hand-crafted linguistic vector (burstiness, sentence variance, punctuation entropy, AI filler words) stacked with word and char n-gram TF-IDF.
  - **Sentence Attribution Heatmap:** Identifies exact sentence spans with high syntactic uniformity (`Low`, `Mid`, `High` risk).
  - **Accuracy Metrics:** **94.7% accuracy**, F1 score **0.932**, False Positive rate **3.8%**.
* **Engine 2: Temporal Video Deepfake Engine (MTCNN + EfficientNet-B0)**
  - **Facial Localization:** PyTorch MTCNN aligns facial bounding boxes at 160×160 resolution.
  - **Spatial-Temporal Inspection:** 16-frame uniform sampling inspecting facial blend artifacts, jitter, and lighting discontinuity.
  - **Throughput:** ~16 frames/second locally on Apple Silicon / standard GPUs.

---

### Slide 6: Decoupled Shortlisting Studio & Rubric Tuner
* **Header:** Merit-Based Candidate Ranking with Dynamic Real-Time Weighting
* **Key Features:**
  - **Interactive Rubric Weight Sliders:** Reviewers adjust criteria weights in real-time:
    - *Relevance & Task Alignment* (default 35%)
    - *Reasoning Rigor & Empirical Depth* (default 35%)
    - *Originality & Novelty* (default 30%)
  - **Instant Dynamic Re-Ranking:** Cohort table immediately recalculates and animates candidate positions upon slider changes.
  - **Side-by-Side Comparison Modal:** Head-to-head comparison of two candidates displaying score deltas, criteria bars, and AI signal discrepancies.
  - **Batch Review Actions:** 1-click batch shortlisting or escalation to 10-minute oral defense interviews for submissions with high AI signals.
  - **Reviewer Rationale Templates:** One-click pre-populated justification chips that mandate human accountability.

---

### Slide 7: Verifiable Audit Ledger & Cryptographic Proofs
* **Header:** Append-Only SHA-256 Compliance Trail with Tamper Detection
* **Audit Guarantees:**
  - **Chained Blocks:** Every inference, score override, and reviewer rationale is hashed into a sequential block (`Block N Hash = SHA256(Block N-1 Hash + Payload)`).
  - **Live Tamper Simulator:** Built-in interactive simulator allowing auditors to test bit-flip tampering on any block, triggering instant real-time `COMPROMISED` Merkle violation alerts.
  - **One-Click Cryptographic Receipts:** Auditors and applicants can copy verifiable JSON receipts or full SHA-256 digests for external verification.
  - **Compliance Alignment:** Fully supports GDPR "Right to Explanation" and prevents retrospective grade or hiring tampering.

---

### Slide 8: Enterprise Advantages, Competitive Edge & Roadmap
* **Header:** Why AuthentiQ Wins in Regulated & Sovereign Environments
* **Comparative Advantages:**
  | Dimension | Legacy Detectors (Turnitin / GPTZero) | AuthentiQ Platform |
  | :--- | :--- | :--- |
  | **Deployment** | Closed cloud SaaS (Data leaves premises) | 100% Sovereign (Runs locally on-premise) |
  | **Policy** | Disqualification by AI percentage | Decoupled quality rubrics (Zero auto-drops) |
  | **Modalities** | Text-only or disjointed video tools | Unified Text Heatmap + Video Deepfake Scrubber |
  | **Auditability** | Proprietary black box score | Cryptographically verifiable SHA-256 ledger |
  | **Cost / Call** | Per-token / API monthly fees | **$0.00 marginal inference cost** |
* **Future Roadmap:**
  - **Q1 2027:** Audio synthetic voice-cloning detection (wav2vec spectrogram analysis).
  - **Q2 2027:** Decentralized multi-institution Merkle notarization via consortium chains.
  - **Q3 2027:** Multi-language Hindi/Indic vernacular syntactic calibration.
* **Closing Call to Action:**
  - Production-ready local console running on `http://localhost:8000`.
  - Zero external API setup required. Clone, run, and evaluate with sovereign certainty.
