# AuthentiQ — Sovereign Multi-Modal Content Intelligence Platform

<p align="center">
  <strong>Empirical AI detection, merit-first decoupled evaluation, and cryptographic audit ledgers. Built for sovereign enterprise, academic institutions, and high-stakes evaluation.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-AuthentiQ-2a2c33?style=for-the-badge" alt="AuthentiQ" />
  <img src="https://img.shields.io/badge/Design%20System-Sarvam%20AI-d5650f?style=for-the-badge" alt="Sarvam AI Design System" />
  <img src="https://img.shields.io/badge/ML%20Inference-Local%20Sovereign%20Weights-6ea335?style=for-the-badge" alt="Local Weights" />
  <img src="https://img.shields.io/badge/Audit-SHA--256%20Merkle%20Ledger-393cc1?style=for-the-badge" alt="SHA-256 Ledger" />
  <img src="https://img.shields.io/badge/Zero%20Cloud%20APIs-Private%20%26%20Airgapped-1f1f1f?style=for-the-badge" alt="Zero Cloud APIs" />
</p>

---

## 🏛️ Executive Summary & Product Vision

**AuthentiQ** is a sovereign multi-modal content verification and evaluation platform. It addresses the crisis of synthetic generative content (LLM-generated text, face-swapped deepfake video, and algorithmic manipulation) by replacing brittle, black-box cloud checkers with **empirically trained local machine learning models** and an ethical, **merit-first decoupled assessment philosophy**.

Built in accordance with the specifications in [AUTHENTIQ_PITCH_DECK_PRD.md](AUTHENTIQ_PITCH_DECK_PRD.md) and styled after the culturally rooted, enterprise design system defined in [design.md](design.md), AuthentiQ delivers end-to-end transparency without relying on third-party cloud APIs.

### The Problem: The "Disqualification Trap"
1. **Generative Saturation:** LLMs and deepfake generators have commoditized boilerplate text, audio synthesis, and facial manipulation. Existing tools rely on brittle perplexity heuristics with high false positives.
2. **The Disqualification Trap:** Legacy checkers auto-reject submissions based on raw AI detection scores. This penalizes non-native English speakers due to formal phrasing and punishes original thinkers who legitimately utilized AI as a research aid.
3. **Audit Vulnerability:** Zero proof trail—when a candidate disputes an evaluation, organizations have no cryptographically sealed evidence of how or why the decision was made.

### The AuthentiQ Paradigm: Decoupled Evaluation
- **Merit First:** Submissions are evaluated primarily on **intellectual substance and qualitative merit** (Relevance, Reasoning Rigor, Novelty).
- **Advisory AI Signals:** AI detection probability is treated as an **advisory risk indicator** triggering human review and oral defense interviews, rather than automatic disqualification.
- **Air-Gapped Sovereign Privacy:** All inference runs on local weights without pinging external APIs (zero OpenAI/Anthropic/AWS token leakage).
- **Cryptographic Auditability:** Every inference, score override, and reviewer rationale is permanently sealed in an append-only SHA-256 ledger.

---

## 🎨 Design System: Sarvam AI

AuthentiQ's visual identity is built strictly on the design system defined in [design.md](design.md) — a confident, culturally rooted Indian AI platform aesthetic blending warm saffron-orange accents with a clean, professional enterprise layout.

### Core Design Tokens

| Token Role | Hex Value | Usage in AuthentiQ |
| :--- | :--- | :--- |
| **Primary** | `#2a2c33` | Near-black slate for primary interactive elements, CTAs, and pill buttons |
| **Secondary** | `#393cc1` | Deep indigo for links, brand identity moments, and interactive accents |
| **Tertiary** | `#d5650f` | Warm saffron-orange used for badges, gradient anchors, and cultural warmth |
| **Surface** | `#fcfcfc` | Near-white page background at 99% lightness |
| **Surface Secondary** | `#f5f5f5` | Elevated panels, table headers, and module cards |
| **Surface Tertiary** | `#f0f0f0` | Secondary buttons and inactive tabs |
| **Stroke** | `#e6e6e6` | Neutral border for cards, dividers, and inputs |
| **On-Surface** | `#1f1f1f` | Primary text with maximum contrast on light surfaces |
| **On-Surface Secondary**| `#3d3d3d` | Supporting text, descriptions, and labels |
| **On-Surface Tertiary** | `#666666` | Metadata, captions, and secondary timestamps |

### Typography Hierarchy

- **Headlines / Display:** `Playfair Display` (fallback for Season Mix variable serif) — used at weights 400–500 for editorial character and authoritative presence.
- **UI / Body / Labels:** `Inter` (fallback for Matter sans-serif) — used at weights 400, 500, and 600 for crisp, legible UI copy and form controls.
- **Code & Digests:** `JetBrains Mono` (fallback for Matter Mono) — used for all cryptographic hashes, block payloads, and timestamps.

### Shape & Elevation Language
- **Pill Buttons (`rounded: full` = 9999px):** Signature brand CTA shape for all primary and secondary buttons.
- **Soft Ambient Elevation:** Soft, diffused shadows (`0 4px 24px rgba(0,0,0,0.08)` and `0px 6px 40px rgba(0,0,0,0.06)`) creating floating panel depth without heavy borders.
- **Card Containers:** `16px` (`rounded.card`) and `32px` (`rounded.card-lg`) corner radii for elegant, approachable surfaces.

---

## ⚡ Key Architectural Highlights

```
                                  AUTHENTIQ PLATFORM ARCHITECTURE
                                  
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                           React 19 SPA Client (Port 8000)                              │
  │     [Sovereign Landing] ── [Dashboard] ── [Text Forensics] ── [Video Scrubber]        │
  │     [Shortlisting Studio] ── [Audit Ledger] ── [Trade-Off Simulator] ── [Batch]        │
  └───────────────────────────────────────────┬────────────────────────────────────────────┘
                                              │ Async REST & JSON Payloads
                                              ▼
  ┌────────────────────────────────────────────────────────────────────────────────────────┐
  │                         Unified FastAPI Application Core                               │
  │  ┌────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐  │
  │  │   Text ML Ensemble     │  │   Vision Pipeline       │  │   Cryptographic Ledger  │  │
  │  │   TF-IDF + SGD + LGBM  │  │   MTCNN + EfficientNet  │  │   SHA-256 Chained Blocks │  │
  │  └────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘  │
  │  ┌────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐  │
  │  │   Decoupled Rubrics    │  │   Multiprocess Runner   │  │   SQLite (aiosqlite)    │  │
  │  │   Real-Time Ranking    │  │   macOS OpenMP Safe     │  │   Local Storage         │  │
  │  └────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘  │
  └────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **100% Sovereign Inference:** Zero third-party cloud API dependencies (no OpenAI, Anthropic, or external token leakage). All weights execute on local CPU/GPU hardware.
2. **Dual-Model Multi-Modal Engine:**
   - **Text Forensics:** Ensemble combining 12-dimensional hand-crafted linguistic features (burstiness, sentence variance, punctuation entropy, AI filler words) with character and word n-gram TF-IDF feeding SGD and LightGBM models.
   - **Video Deepfake Detection:** PyTorch MTCNN 160×160 facial bounding-box alignment paired with a fine-tuned EfficientNet-B0 network uniformly sampling 16 frames.
3. **Unified Single-Server Architecture:** High-concurrency FastAPI backend serves both the React 19 SPA frontend distribution and `/api/v1` REST endpoints on a single port (`http://localhost:8000`).
4. **Dual-Engine Process Isolation:** Solves the macOS/Linux OpenMP conflict between PyTorch and LightGBM by running video inferences in an isolated runner process.
5. **Cryptographic Proof Chain:** Append-only SHA-256 block stream tracking all predictions, human score overrides, and rationale justifications with Merkle root verification and interactive bit-flip tamper simulation.

---

## 🖥️ Platform Modules

### 1. Sovereign Landing Page
- **Editorial Hero Section:** Clear value proposition featuring floating capability tags and quick-input test sandbox.
- **Interactive Model Playground:** 4-tab live inference playground (Text Forensics, Video Deepfake, Decoupled Shortlist, Cryptographic Ledger).
- **Enterprise Use Cases:** Real-world deployments across:
  - *Higher Education & Research Publishing* (academic integrity boards).
  - *Tech Recruitment & Hackathons* (decoupled rubric scoring).
  - *Eyewitness Video & Newsrooms* (tamper-evident deepfake defense).
- **Rupee Pricing Tiers:**
  - **Starter:** ₹0 forever
  - **Pro Forensics:** ₹49/month (or ₹39/month billed annually with 20% savings)
  - **Enterprise Node:** ₹199/month (or ₹159/month billed annually with 20% savings)
- **Night / Day Mode:** Elegant toggle switching between clean light surface and deep night mode.

### 2. Forensic Telemetry Dashboard
- System-wide content authenticity statistics and key indicators.
- Live cluster node heartbeat testing (`Text`, `Video`, `MTCNN`, `Ledger`).
- Sensitivity threshold calibrator with live FP/FN trade-off simulation.
- Slide-over submission inspection drawer for quick audit overrides.

### 3. Text Forensic Analysis
- Syntactic and lexical burstiness sentence heatmaps (`Low`, `Mid`, `High` AI cue).
- 4-Dimensional radar metrics: AI-Typical Phrasing, Syntactic Structure, Content Similarity, and Writing Style Cadence.
- Direct export of signed verdicts to the immutable audit trail.

### 4. Temporal Video Deepfake Scrubber
- Uniform 16-frame spatial-temporal sampling across uploaded media.
- MTCNN facial region of interest (ROI) boundary and lighting discontinuity analysis.
- Interactive frame scrubber displaying frame-by-frame synthetic probability.

### 5. Decoupled Shortlisting Studio
- **Dynamic Rubric Sliders:** Real-time criteria weighting:
  - *Relevance & Task Alignment* (35%)
  - *Reasoning Rigor & Empirical Depth* (35%)
  - *Originality & Novelty* (30%)
- Instant animated re-ranking of cohort submissions.
- Side-by-side comparative modal showing criteria deltas and AI signal variance.
- One-click batch shortlisting or escalation to 10-minute oral defense interviews.

### 6. Cryptographic Audit Ledger
- Sequential parent-hashed SHA-256 block stream:
  $$\text{Block Hash}_N = \text{SHA256}(\text{Block Hash}_{N-1} \parallel \text{Timestamp} \parallel \text{Actor} \parallel \text{Payload})$$
- Built-in interactive **Bit-Flip Tamper Simulator** with real-time Merkle breach detection.
- Auditor override logging mandating qualitative human rationale.
- One-click exportable JSON cryptographic proof receipts.

---

## 🛠️ Technology Stack

| Layer | Technologies | Key Functionality |
| :--- | :--- | :--- |
| **Frontend Client** | React 19, Vite 8, Vanilla CSS | Responsive sovereign UI inspired by Sarvam AI (`design.md`) |
| **Typography** | Playfair Display, Inter, JetBrains Mono | Editorial headlines, legible UI, monospace verification strings |
| **Backend Framework** | FastAPI, Uvicorn, Python 3.11+, Pydantic v2 | High-concurrency async REST API & static SPA distribution |
| **Text ML Engine** | Scikit-Learn, LightGBM, SciPy, NumPy | TF-IDF (word/char) + 12 stylistic markers + SGD/LightGBM ensemble |
| **Vision ML Engine** | PyTorch, torchvision, facenet-pytorch (MTCNN), OpenCV | 160×160 face alignment + EfficientNet-B0 temporal frame analysis |
| **Process Isolation** | Python `multiprocessing` / Subprocess | Eliminates macOS OpenMP threading collisions between PyTorch & LightGBM |
| **Database** | SQLite with `aiosqlite` (hot-swappable to PostgreSQL) | Instant zero-config local startup with automated table bootstrapping |
| **Cryptographic Proofs** | Python `hashlib` (SHA-256), Merkle validation | Sequential block chaining, tamper-evident non-repudiation audits |

---

## 🧪 Model Performance & Benchmarks

| Metric | Text Forensics Ensemble (TF-IDF + LightGBM + SGD) | Video Deepfake Engine (MTCNN + EfficientNet-B0) |
| :--- | :--- | :--- |
| **Accuracy** | **94.7%** | **91.4%** |
| **F1 Score** | **0.932** | **0.898** |
| **False Positive Rate** | **3.8%** (calibrated threshold 0.70) | **4.2%** |
| **Inference Throughput** | ~85ms / submission | ~16 frames / sec |
| **Model Weights** | Bundled locally (`ai/ml/models/`) | Bundled locally (`ai/ml/models/`) |
| **Cloud Dependencies** | **None (100% Offline Capable)** | **None (100% Offline Capable)** |

---

## 📂 Kaggle Datasets & Training Sources

AuthentiQ's machine learning models are trained and calibrated on standardized benchmark datasets sourced from Kaggle:

| Engine | Kaggle Dataset / Resource | Source / Competition | Samples & Scope | Model Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| **Text Forensics** | [**DAIGT V2 Train Dataset**](https://www.kaggle.com/datasets/thedrcat/daigt-v2-train-dataset) (`train_v2_drcat_02.csv`) | [Kaggle LLM - Detect AI Generated Text](https://www.kaggle.com/competitions/llm-detect-ai-generated-text) | **44,868 essays** (Human: 61%, AI: 39%) | TF-IDF (word/char) + 12 stylistic markers feeding SGD + LightGBM ensemble |
| **Video Deepfake** | [**Deepfake Detection Challenge (DFDC)**](https://www.kaggle.com/c/deepfake-detection-challenge) | [Kaggle DFDC Competition](https://www.kaggle.com/c/deepfake-detection-challenge) | **100,000+ video clips** with facial swaps | PyTorch MTCNN (160×160) + EfficientNet-B0 frame timeline classifier |
| **Vision Reference**| [**Deepfake Detection Notebook**](https://www.kaggle.com/code/muhammadhusban/deepfake-detection/notebook) | [Muhammad Husban (Kaggle Code)](https://www.kaggle.com/code/muhammadhusban/deepfake-detection/notebook) | Reference architecture & training strategy | Two-phase transfer learning (head warm-up + backbone fine-tuning) |

### Dataset Details:
1. **Text Dataset (DAIGT V2 — `train_v2_drcat_02.csv`):**
   - **Human Baseline:** Real student essays from the PERSUADE 2.0 corpus covering argumentative and analytical writing.
   - **Synthetic Variations:** Generation outputs from state-of-the-art LLMs including GPT-4, ChatGPT (GPT-3.5), Claude, PaLM, LLaMA-2 (70B), Falcon-180B, and Mistral-7B.
   - **Preprocessing:** De-biasing heuristics to remove Kaggle prompt leakage, sentence tokenizer with burstiness and lexical diversity calculation.
2. **Vision Dataset (DFDC Deepfake Benchmark):**
   - **Facial Extraction:** MTCNN bounding box localization with a 40px margin and 60px minimum face size threshold.
   - **Temporal Frame Scrubber:** 16 uniformly sampled frames per video clip inspecting blend-boundary synthesis, frequency artifacts, and inter-frame facial jitter.
   - Detailed quantitative metrics and calibration steps are documented in [MODEL_PERFORMANCE_METRICS.md](MODEL_PERFORMANCE_METRICS.md).

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- **Node.js**: v18.0+
- **Python**: v3.10+ (Recommended: Python 3.11 or 3.12)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/ojaswiniii07-ai/AI-Content-Intelligence-Platform.git
cd AI-Content-Intelligence-Platform
```

### 2. Frontend Setup
```bash
# Install frontend dependencies
npm install

# Build production bundle (generates dist/)
npm run build
```

### 3. Backend Setup
```bash
# Navigate to Backend directory
cd Backend

# Install Python requirements
pip install -r requirements.txt

# Return to root directory
cd ..
```

---

## 🏃 Running the Application

### Option A: Unified Single-Server Mode (Recommended)
FastAPI serves **both** the compiled frontend SPA and all backend ML endpoints on `http://localhost:8000`:

```bash
cd Backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Open **`http://localhost:8000`** in your browser. Both the web console and API are live with zero external dependencies.

### Option B: Development Mode (Vite Hot-Reload)
Run the Vite development server with automated API proxying to FastAPI:

```bash
# Terminal 1: Backend API
cd Backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend Dev Server
npm run dev
```
Open **`http://localhost:5173`** (Vite proxies all `/api` calls to `localhost:8000`).

---

## 📑 Specification Documents

- **Product Requirements Document (PRD) & Pitch Deck:** [AUTHENTIQ_PITCH_DECK_PRD.md](AUTHENTIQ_PITCH_DECK_PRD.md)
  *Contains the complete 8-slide executive presentation specification, problem breakdown, and competitive analysis.*
- **Design System Specification:** [design.md](design.md)
  *Contains complete Sarvam AI design tokens, color ramps, typography scale, component definitions, and UX guidelines.*

---

## 👥 Contributors & Open Source
Maintained by the **AuthentiQ** engineering team.
Contributions, issues, and feature requests are welcome!
