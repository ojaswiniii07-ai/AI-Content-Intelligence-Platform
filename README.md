# ContentIQ — AI Content Intelligence Platform

An enterprise-grade AI content intelligence and verification platform built with **React**, **Vite**, and modern UI/UX design patterns. Designed to help institutions, educators, and enterprise reviewers detect AI-generated text, analyze media for deepfake anomalies, shortlist responses against calibrated rubrics, and maintain tamper-evident audit trails.

---

## 🚀 Key Modules & Capabilities

- **Executive Intelligence Dashboard**: Real-time platform metrics, sparklines, circular progress gauges, recent submissions activity feed, module launcher, and SVG detection trend analytics.
- **Text AI-Involvement Analysis**: Sentence-level heatmap highlighting AI signal probability (low, medium, high), word count metrics, signal dimension breakdown, and calibrated caveats.
- **Media Deepfake Analysis**: Frame-level artifact visualization, multi-detector chips (face blend, lighting inconsistency, facial motion, audio/video synchronization), and interactive timeline scrubber.
- **Response Shortlisting**: Evaluates written responses against customizable rubrics (Relevance, Reasoning, Originality) with decoupled AI involvement signals.
- **Audit Trail & Compliance**: Tamper-evident, cryptographically verifiable ledger with SHA-256 hashes, review overrides, and full accountability logging.
- **FP/FN Simulator**: Dynamic confidence threshold calibration on labeled datasets with live confusion matrix (TP, FP, FN, TN) and trade-off metrics.
- **Batch Processing & Cohort Intelligence**: Asynchronous batch queue orchestration, cohort integrity distribution histograms, and batch export tools.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite 8
- **Styling**: Modern CSS Design System (Custom variables, dark glassmorphism, responsive grid)
- **Icons & Visuals**: Inline SVG icons, charts, sparklines, and heatmaps

---

## 💻 Getting Started Locally

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ojaswiniii07-ai/AI-Content-Intelligence-Platform.git
   cd AI-Content-Intelligence-Platform
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start the local development server**:
   ```bash
   npm run dev
   ```

4. **Build for production**:
   ```bash
   npm run build
   ```

---

## 📄 Compliance & Human-in-the-Loop Principles

In compliance with the product requirements (PRD):
- AI involvement and answer quality are strictly separated outputs.
- Detection outputs serve as decision-support indicators rather than standalone proof of authorship.
- Every consequential decision or override is captured with reviewer rationale and SHA-256 checksums in the audit ledger.
