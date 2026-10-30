from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.review import Review
from app.models.rubric import Rubric
from app.models.submission import Submission
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.common import APIResponse

DEFAULT_COHORT_RUBRICS = {
    "p1": {
        "id": "p1",
        "name": "Hackathon 2026 — Final Round",
        "version": 2,
        "criteria": [
            {"key": "relevance", "name": "Relevance & Problem Fit", "description": "Addresses core technical challenge and meets hackathon theme requirements.", "scale_max": 10.0},
            {"key": "reasoning", "name": "Technical Reasoning & Architecture", "description": "Sound engineering principles, architectural feasibility, and rigorous logic.", "scale_max": 10.0},
            {"key": "originality", "name": "Originality & Innovation", "description": "Novel approaches, distinct creative contributions, and avoidance of generic templates.", "scale_max": 10.0},
        ],
        "weights": {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30},
        "scoring_scale": 10.0,
        "style_rules": ["Concise technical prose", "Evidence-backed claims"],
    },
    "p2": {
        "id": "p2",
        "name": "Engineering Hiring Q4",
        "version": 1,
        "criteria": [
            {"key": "relevance", "name": "System Design & Relevance", "description": "Relevance to distributed, low-latency, and high-throughput systems.", "scale_max": 10.0},
            {"key": "reasoning", "name": "Analytical Rigor", "description": "Failure analysis, trade-off evaluation, and algorithmic reasoning.", "scale_max": 10.0},
            {"key": "originality", "name": "Architectural Innovation", "description": "Unique architectural paradigms and non-trivial problem solving.", "scale_max": 10.0},
        ],
        "weights": {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30},
        "scoring_scale": 10.0,
        "style_rules": ["Production-grade considerations"],
    },
    "p3": {
        "id": "p3",
        "name": "University Essay Competition",
        "version": 1,
        "criteria": [
            {"key": "relevance", "name": "Thesis Relevance", "description": "Adherence to essay prompt and clear argumentative direction.", "scale_max": 10.0},
            {"key": "reasoning", "name": "Critical Reasoning", "description": "Logical flow, persuasive arguments, and critical analysis.", "scale_max": 10.0},
            {"key": "originality", "name": "Original Insights", "description": "Unique perspectives and fresh synthesis of ideas.", "scale_max": 10.0},
        ],
        "weights": {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30},
        "scoring_scale": 10.0,
        "style_rules": ["Formal academic tone"],
    },
    "p4": {
        "id": "p4",
        "name": "Media Grant Applications",
        "version": 1,
        "criteria": [
            {"key": "relevance", "name": "Public Interest & Relevance", "description": "Significance of investigative topic to public interest.", "scale_max": 10.0},
            {"key": "reasoning", "name": "Methodological Soundness", "description": "Rigorous verification methods and investigative integrity.", "scale_max": 10.0},
            {"key": "originality", "name": "Story Novelty", "description": "Unreported angles and original investigative sourcing.", "scale_max": 10.0},
        ],
        "weights": {"relevance": 0.35, "reasoning": 0.35, "originality": 0.30},
        "scoring_scale": 10.0,
        "style_rules": ["Journalistic verification standards"],
    },
}

DEFAULT_COHORT_SUBMISSIONS = {
    "sub_0041": {
        "id": "sub_0041",
        "title": "Team Nexus — Multi-Agent Consensus Verification",
        "text": "We present an enterprise-scale architecture combining multi-agent consensus verification with verifiable cryptographic watermarking. By leveraging decentralized Byzantine fault tolerance, our system verifies distributed state without central bottlenecks. Extensive empirical benchmarks on edge nodes validate high lexical diversity, low latency (<42ms), and resilience against synthetic injection attacks.",
        "ai_context": {"ai_score": 18.0, "ai_signal": "Low"},
    },
    "sub_0027": {
        "id": "sub_0027",
        "title": "DataForge AI — Statistical Burstiness & Perplexity Distributions",
        "text": "This paper analyzes statistical burstiness and semantic perplexity distributions across edge devices with robust benchmarks. Our framework decomposes n-gram frequency shifts to isolate machine-generated syntactic repetitions from human creative variance. Experimental evaluation across 10,000 corpus samples confirms high technical rigor and deterministic classification boundaries.",
        "ai_context": {"ai_score": 54.0, "ai_signal": "Medium"},
    },
    "sub_0012": {
        "id": "sub_0012",
        "title": "AISolve Co. — Generic Architectural Framework",
        "text": "In the modern era of rapid digital transformation, organizations must leverage synergistic cloud-native paradigms to optimize operational efficiencies. We implement an end-to-end scalable pipeline utilizing standardized microservices and container orchestration. The methodology adheres to industry best practices and establishes foundational capabilities.",
        "ai_context": {"ai_score": 82.0, "ai_signal": "High"},
    },
    "sub_0089": {
        "id": "sub_0089",
        "title": "Quantum Leap Labs — Multimodal Vision Transformer Artifacts",
        "text": "We investigate subtle artifacts in multimodal vision transformers (ViT) when handling high-framerate video compression. By evaluating attention heatmaps across temporal boundaries, our model identifies spatial frequency anomalies indicative of deepfake synthesis while preserving robust detection accuracy across varied lighting conditions.",
        "ai_context": {"ai_score": 24.0, "ai_signal": "Low"},
    },
    "sub_0063": {
        "id": "sub_0063",
        "title": "BuildRight Infrastructure — Enterprise Cloud Migration Blueprint",
        "text": "This case study details a multi-region zero-downtime database migration for a tier-1 financial platform. We document the dual-write sync architecture, rollback mechanisms, and performance profiling under 50k QPS peak loads. Practical lessons and infrastructure-as-code manifests demonstrate solid engineering execution.",
        "ai_context": {"ai_score": 31.0, "ai_signal": "Low"},
    },
    "sub_0078": {
        "id": "sub_0078",
        "title": "Sovereign Edge Labs — Decentralized Biometric Auditing",
        "text": "We design a privacy-preserving biometric verification protocol using local MTCNN face localization and zero-knowledge proof generation. All sensitive facial embeddings remain strictly on-device, preventing centralized credential breaches while enabling cryptographically tamper-evident identity verification.",
        "ai_context": {"ai_score": 21.0, "ai_signal": "Low"},
    },
    # Mock Hackathon Submissions (from mock_data/hackathon_submissions.csv)
    "sub_h01": {
        "id": "sub_h01",
        "title": "Team Chronos — Decentralized Temporal Oracles",
        "text": "We present Chronos, a decentralized temporal oracle protocol designed to eliminate front-running and miner-extractable value (MEV) in high-throughput decentralized finance. Chronos combines threshold BLS signatures with verifiable delay functions (VDFs) running on edge nodes. Our formal mathematical verification proves that transactions are sequenced with sub-second finality while preserving cryptographic secrecy until block finalization.",
        "ai_context": {"ai_score": 14.0, "ai_signal": "Low"},
    },
    "sub_h02": {
        "id": "sub_h02",
        "title": "NeuralShield Labs — Adversarial Robustness Benchmark",
        "text": "NeuralShield is an automated adversarial testing harness for multimodal vision-language architectures. The framework subjects vision transformers to targeted gradient-based perturbations and cross-modal prompt injections. Across 15,000 synthetic test vectors, NeuralShield isolates vulnerability boundaries and dynamically computes safety containment metrics.",
        "ai_context": {"ai_score": 22.0, "ai_signal": "Low"},
    },
    "sub_h03": {
        "id": "sub_h03",
        "title": "EcoGrid Core — P2P Microgrid Energy Balancing",
        "text": "EcoGrid addresses urban distribution bottlenecks through an open decentralized microgrid ledger. Local residential solar producers trade excess capacity using dynamic spot auctions governed by an optimized Raft consensus algorithm. We deployed hardware prototypes across 12 test nodes, demonstrating 99.4% balancing efficiency with sub-45ms routing latency.",
        "ai_context": {"ai_score": 19.0, "ai_signal": "Low"},
    },
    "sub_h04": {
        "id": "sub_h04",
        "title": "OmniSync Protocol — Generic Realtime Synchronization Engine",
        "text": "In today's fast-paced digital ecosystem, real-time data synchronization is paramount for enterprise applications. OmniSync delivers a scalable microservice architecture leveraging standard WebSocket protocols and Redis caching. It follows standard software engineering best practices to ensure reliable packet delivery across modern cloud web applications.",
        "ai_context": {"ai_score": 88.0, "ai_signal": "High"},
    },
    "sub_h05": {
        "id": "sub_h05",
        "title": "Vanguard Quantum — Post-Quantum Lattice Key Exchange",
        "text": "We present an optimized pure-C implementation of the CRYSTALS-Kyber-1024 post-quantum key encapsulation mechanism tailored for constrained ARM Cortex-M4 microcontrollers. Through assembly-level NTT optimizations and constant-time modular arithmetic, our design cuts cycle latency by 38% compared to reference benchmarks while maintaining side-channel attack resilience.",
        "ai_context": {"ai_score": 12.0, "ai_signal": "Low"},
    },
    "sub_h06": {
        "id": "sub_h06",
        "title": "HyperFlow Analytics — Distributed Stream Processing Pipeline",
        "text": "HyperFlow is a distributed streaming pipeline that ingests, filters, and correlates telemetry events across distributed server fleets. By partitioning event logs across local NVMe storage and utilizing vectorized SIMD parsing, HyperFlow achieves sustained throughput of 1.2M events per second per worker node.",
        "ai_context": {"ai_score": 48.0, "ai_signal": "Medium"},
    },
    # Mock Resume Candidates (from mock_data/resume_candidates.csv)
    "sub_r01": {
        "id": "sub_r01",
        "title": "Dr. Marcus Thorne — Principal Distributed Systems Architect",
        "text": "Dr. Marcus Thorne is a Principal Infrastructure Engineer with 12+ years of experience leading distributed consensus teams. At Apex Capital, designed a proprietary lock-free order-matching engine in Rust achieving p99 latency <8 microseconds. Holds a Ph.D. in Computer Science from MIT with 6 peer-reviewed papers on Byzantine fault tolerance and formal verification using TLA+.",
        "ai_context": {"ai_score": 11.0, "ai_signal": "Low"},
    },
    "sub_r02": {
        "id": "sub_r02",
        "title": "Aisha Al-Mansoor — Senior ML Safety & Alignment Engineer",
        "text": "Aisha Al-Mansoor brings 6 years of focused experience in AI safety and mechanistic interpretability. Formerly at Alignment Labs, spearheaded research discovering steering vectors for representation engineering in 70B+ parameter transformer models. Led red-teaming campaigns and authored automated safety filters deployed in production APIs handling 50M requests daily.",
        "ai_context": {"ai_score": 16.0, "ai_signal": "Low"},
    },
    "sub_r03": {
        "id": "sub_r03",
        "title": "Vikramaditya Rao — Lead Site Reliability Engineer",
        "text": "Vikram Rao is a Staff SRE with deep expertise in cloud-native platform engineering. Designed a global multi-cloud Kubernetes deployment spanning AWS and GCP with Istio service mesh and Cilium eBPF observability. Reduced mean-time-to-detection (MTTD) by 64% and sustained 99.995% SLA across critical transactional banking workloads.",
        "ai_context": {"ai_score": 23.0, "ai_signal": "Low"},
    },
    "sub_r04": {
        "id": "sub_r04",
        "title": "Jordan Hayes — Full-Stack AI Software Engineer",
        "text": "I am an experienced full-stack developer with comprehensive expertise in React, Next.js, Python, Django, TensorFlow, PyTorch, Kubernetes, Docker, and Cloud Computing. Proven track record of leveraging best-in-class methodologies to drive cross-functional excellence and deliver modern scalable digital solutions. Passionate about synergizing innovative artificial intelligence technologies.",
        "ai_context": {"ai_score": 86.0, "ai_signal": "High"},
    },
    "sub_r05": {
        "id": "sub_r05",
        "title": "Kavita Iyer — Senior Cryptography Engineer",
        "text": "Kavita Iyer has 7 years of specialized production experience in applied cryptography. Designed and audited PLONK-based proving systems for decentralized identity, cutting proof generation time by 45%. Active contributor to open-source cryptographic libraries and W3C Verifiable Credentials specification working group.",
        "ai_context": {"ai_score": 14.0, "ai_signal": "Low"},
    },
    "sub_r06": {
        "id": "sub_r06",
        "title": "David Lindqvist — Staff Backend Engineer",
        "text": "Staff backend engineer with 9 years of experience optimizing relational databases and distributed caching. Engineered a CDC (Change Data Capture) streaming pipeline using Debezium and Apache Kafka that synced 20,000 writes/sec to Snowflake without data loss. Strong foundations in operating system internals and concurrent programming.",
        "ai_context": {"ai_score": 42.0, "ai_signal": "Medium"},
    },
}
from app.schemas.review import (
    BatchEvaluationRequest,
    BatchEvaluationResponse,
    CriterionEvaluation,
    DecoupledSignals,
    EvaluationResult,
    ReviewRead,
    ShortlistCandidateItem,
    ShortlistedCandidateItem,
    ShortlistOverrideRequest,
    StyleEvaluation,
)
from app.services.audit.service import append_audit_event
from app.services.evaluation.base import EvaluatorUnavailableError
from app.services.evaluation.ranking import rank_and_shortlist
from app.services.evaluation.registry import get_evaluator

router = APIRouter(prefix="/shortlisting", tags=["Shortlisting"])


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(shortlisted|pending|flagged|rejected)$")
    override_reason: Optional[str] = None


# ── 1. Cohort Projects (frontend compatible) ──────────────────────────────────
@router.get("/projects", summary="Returns active shortlisting rubric cohorts and candidate volume")
async def get_shortlist_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[Dict[str, Any]]]:
    """Returns active shortlisting rubric cohorts and candidate volume."""
    # Check if there are real rubrics in DB
    rubrics_res = await db.execute(sa.select(Rubric).order_by(Rubric.created_at.desc()))
    db_rubrics = rubrics_res.scalars().all()

    if db_rubrics:
        projects = []
        colors = ["purple", "cyan", "green", "orange"]
        for idx, r in enumerate(db_rubrics):
            # Count reviews for this rubric
            cnt_res = await db.execute(
                sa.select(sa.func.count(Review.id)).where(Review.rubric_id == r.id)
            )
            count = cnt_res.scalar() or 0
            projects.append({
                "id": r.id,
                "name": r.name,
                "count": count,
                "status": "In progress" if r.status == "published" else r.status.capitalize(),
                "color": colors[idx % len(colors)],
            })
        return APIResponse(data=projects, message="Projects retrieved")

    # Fallback default cohorts for initial demo view
    projects = [
        {"id": "p1", "name": "Hackathon 2026 — Final Round", "count": 84, "status": "In progress", "color": "purple"},
        {"id": "p2", "name": "Engineering Hiring Q4", "count": 231, "status": "Reviewing", "color": "cyan"},
        {"id": "p3", "name": "University Essay Competition", "count": 1204, "status": "Complete", "color": "green"},
        {"id": "p4", "name": "Media Grant Applications", "count": 47, "status": "Draft", "color": "orange"},
    ]
    return APIResponse(data=projects, message="Projects retrieved")


# ── 2. Submissions / Shortlist (frontend compatible + dynamic DB) ──────────────
@router.get("/submissions", response_model=APIResponse[List[ShortlistedCandidateItem]])
async def get_shortlist_submissions(
    project_id: Optional[str] = Query("p1"),
    status: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("score_desc"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ShortlistedCandidateItem]]:
    """
    Returns candidate submissions scored against calibrated rubrics.
    Decouples rubric quality score from AI involvement signal.
    """
    # Check if project_id matches a real rubric in DB
    reviews_res = await db.execute(
        sa.select(Review, Submission)
        .join(Submission, Review.submission_id == Submission.id)
        .where(Review.rubric_id == project_id)
    )
    db_reviews = reviews_res.all()

    if db_reviews:
        evaluations: List[EvaluationResult] = []
        overrides_map: Dict[str, Dict[str, Any]] = {}

        for rev, sub in db_reviews:
            crit_scores = []
            if rev.criterion_scores:
                for c in rev.criterion_scores:
                    crit_scores.append(CriterionEvaluation.model_validate(c))

            ev = EvaluationResult(
                submission_id=sub.id,
                submission_title=sub.title,
                rubric_id=rev.rubric_id or "",
                rubric_name="Project Rubric",
                rubric_version=1,
                total_score=rev.total_score,
                criterion_scores=crit_scores,
                missing_requirements=rev.missing_requirements or [],
                signals=DecoupledSignals(
                    quality_score=rev.total_score,
                    ai_signal=rev.ai_signal or "Low",
                    ai_score=rev.ai_score or 0.0,
                    similarity_score=rev.similarity_score or 0.0,
                ),
                evaluator_metadata=rev.evaluation_metadata or {},
            )
            evaluations.append(ev)
            overrides_map[sub.id] = {
                "status": rev.status,
                "override_flag": rev.override_flag,
                "override_reason": rev.override_reason,
                "total_score": rev.total_score,
            }

        candidates = rank_and_shortlist(evaluations, status_overrides=overrides_map)
        # Merge in any default cohort candidates not yet reviewed
        reviewed_ids = {ev.submission_id for ev in evaluations}
        default_baseline = [
            ShortlistedCandidateItem(
                id="sub_0041",
                rank="#1",
                name="Team Nexus",
                relevance=9.2,
                reasoning=8.8,
                originality=9.5,
                total=91.7,
                ai_signal="Low",
                ai_score=18.0,
                status="shortlisted",
                summary="Proposes multi-agent consensus verification with verifiable cryptographic watermarking.",
            ),
            ShortlistedCandidateItem(
                id="sub_0027",
                rank="#2",
                name="DataForge",
                relevance=8.5,
                reasoning=9.0,
                originality=7.8,
                total=84.4,
                ai_signal="Medium",
                ai_score=54.0,
                status="pending",
                summary="Analyzes statistical burstiness and semantic perplexity distributions across edge devices.",
            ),
            ShortlistedCandidateItem(
                id="sub_0012",
                rank="#3",
                name="AISolve Co.",
                relevance=8.8,
                reasoning=7.5,
                originality=6.2,
                total=74.2,
                ai_signal="High",
                ai_score=82.0,
                status="flagged",
                summary="Generic architectural boilerplate with high AI sentence repetition cues. Quality is moderate.",
            ),
            ShortlistedCandidateItem(
                id="sub_0089",
                rank="#4",
                name="Quantum Leap",
                relevance=7.9,
                reasoning=8.2,
                originality=8.4,
                total=81.7,
                ai_signal="Low",
                ai_score=24.0,
                status="shortlisted",
                summary="Empirical benchmark analyzing multimodal vision transformer artifacts.",
            ),
            ShortlistedCandidateItem(
                id="sub_0063",
                rank="#5",
                name="BuildRight",
                relevance=7.2,
                reasoning=6.8,
                originality=7.7,
                total=71.9,
                ai_signal="Low",
                ai_score=31.0,
                status="pending",
                summary="Practical enterprise deployment case study. Good structure, moderate reasoning rigor.",
            ),
        ]
        for db_c in default_baseline:
            if db_c.id not in reviewed_ids:
                candidates.append(db_c)
        candidates.sort(key=lambda x: x.total, reverse=True)
        for idx, c in enumerate(candidates):
            c.rank = f"#{idx + 1}"
    else:
        # Default baseline candidates for demonstration / demo project
        candidates = [
            ShortlistedCandidateItem(
                id="sub_0041",
                rank="#1",
                name="Team Nexus",
                relevance=9.2,
                reasoning=8.8,
                originality=9.5,
                total=91.7,
                ai_signal="Low",
                ai_score=18.0,
                status="shortlisted",
                summary="Proposes multi-agent consensus verification with verifiable cryptographic watermarking.",
            ),
            ShortlistedCandidateItem(
                id="sub_0027",
                rank="#2",
                name="DataForge",
                relevance=8.5,
                reasoning=9.0,
                originality=7.8,
                total=84.4,
                ai_signal="Medium",
                ai_score=54.0,
                status="pending",
                summary="Analyzes statistical burstiness and semantic perplexity distributions across edge devices.",
            ),
            ShortlistedCandidateItem(
                id="sub_0012",
                rank="#3",
                name="AISolve Co.",
                relevance=8.8,
                reasoning=7.5,
                originality=6.2,
                total=74.2,
                ai_signal="High",
                ai_score=82.0,
                status="flagged",
                summary="Generic architectural boilerplate with high AI sentence repetition cues. Quality is moderate.",
            ),
            ShortlistedCandidateItem(
                id="sub_0089",
                rank="#4",
                name="Quantum Leap",
                relevance=7.9,
                reasoning=8.2,
                originality=8.4,
                total=81.7,
                ai_signal="Low",
                ai_score=24.0,
                status="shortlisted",
                summary="Empirical benchmark analyzing multimodal vision transformer artifacts.",
            ),
            ShortlistedCandidateItem(
                id="sub_0063",
                rank="#5",
                name="BuildRight",
                relevance=7.2,
                reasoning=6.8,
                originality=7.7,
                total=71.9,
                ai_signal="Low",
                ai_score=31.0,
                status="pending",
                summary="Practical enterprise deployment case study. Good structure, moderate reasoning rigor.",
            ),
        ]

    # Filter
    if status and status != "all":
        candidates = [c for c in candidates if c.status == status]

    # Sort
    if sort_by in ("score_desc", "score-desc"):
        candidates.sort(key=lambda x: x.total, reverse=True)
    elif sort_by in ("score_asc", "score-asc"):
        candidates.sort(key=lambda x: x.total)
    elif sort_by in ("ai_desc", "ai-desc"):
        candidates.sort(key=lambda x: x.ai_score, reverse=True)
    elif sort_by in ("ai_asc", "ai-asc"):
        candidates.sort(key=lambda x: x.ai_score)

    return APIResponse(data=candidates, message="Submissions retrieved successfully")


# ── 3. Batch Evaluation ────────────────────────────────────────────────────────
@router.post(
    "/evaluate",
    response_model=APIResponse[BatchEvaluationResponse],
    summary="Evaluate multiple submissions against a shared rubric",
)
async def evaluate_submissions_batch(
    req: BatchEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[BatchEvaluationResponse]:
    """
    Evaluates submissions against a shared rubric using specified evaluator ('heuristic' or 'llm').
    Persists reviews in database and returns ranked shortlist with deterministic tie handling.
    """
    # 1. Ensure default workspace exists
    ws_res = await db.execute(sa.select(Workspace).where(Workspace.id == "ws_default"))
    if not ws_res.scalars().first():
        db.add(Workspace(id="ws_default", name="Default Workspace", description="Default evaluation cohort workspace", owner_id=str(current_user.id)))
        await db.flush()

    # 2. Find or create Rubric
    rubric_res = await db.execute(sa.select(Rubric).where(Rubric.id == req.rubric_id))
    rubric = rubric_res.scalars().first()
    if not rubric:
        preset = DEFAULT_COHORT_RUBRICS.get(req.rubric_id, DEFAULT_COHORT_RUBRICS["p1"])
        rubric = Rubric(
            id=req.rubric_id,
            workspace_id="ws_default",
            created_by_id=str(current_user.id),
            name=preset["name"],
            version=preset.get("version", 1),
            criteria=preset["criteria"],
            weights=preset["weights"],
            scoring_scale={"max_score": 10.0, "min_score": 0.0},
            style_rules={"rules": preset.get("style_rules", [])},
            status="published",
        )
        db.add(rubric)
        await db.flush()

    try:
        evaluator = get_evaluator(req.evaluator_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    rubric_dict = {
        "id": rubric.id,
        "name": rubric.name,
        "version": rubric.version,
        "criteria": rubric.criteria or [],
        "weights": rubric.weights,
        "scoring_scale": rubric.scoring_scale,
        "style_rules": rubric.style_rules,
    }

    # 3. Gather items to evaluate
    items_to_eval = []
    if req.submissions_inline:
        for item in req.submissions_inline:
            title = item.get("title") or item.get("name") or item.get("project_title") or item.get("role_applied") or "Inline Submission"
            text_val = item.get("text") or item.get("text_content") or item.get("summary") or ""
            ai_ctx = item.get("ai_context") or {
                "ai_score": float(item.get("ai_score") or item.get("aiScore") or 0.0),
                "ai_signal": str(item.get("ai_signal") or item.get("aiSignal") or "Low"),
            }
            items_to_eval.append({
                "id": str(item.get("id", str(uuid.uuid4()))),
                "title": title,
                "text": text_val,
                "ai_context": ai_ctx,
            })
    elif req.submission_ids:
        subs_res = await db.execute(sa.select(Submission).where(Submission.id.in_(req.submission_ids)))
        db_subs = {s.id: s for s in subs_res.scalars().all()}
        for sid in req.submission_ids:
            if sid in db_subs:
                s = db_subs[sid]
                items_to_eval.append({
                    "id": s.id,
                    "title": s.title,
                    "text": s.text_content or "",
                    "ai_context": {},
                })
            elif sid in DEFAULT_COHORT_SUBMISSIONS:
                items_to_eval.append(DEFAULT_COHORT_SUBMISSIONS[sid])
            else:
                items_to_eval.append({
                    "id": sid,
                    "title": f"Candidate {sid}",
                    "text": "Detailed architectural specification and engineering submission for peer evaluation.",
                    "ai_context": {},
                })
    else:
        # Evaluate all default cohort submissions
        items_to_eval = list(DEFAULT_COHORT_SUBMISSIONS.values())

    if not items_to_eval:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No submissions found to evaluate.",
        )

    evaluations: List[EvaluationResult] = []

    for item in items_to_eval:
        try:
            ev = await evaluator.evaluate(
                submission_id=item["id"],
                submission_title=item["title"],
                submission_text=item["text"],
                rubric_data=rubric_dict,
                ai_context=item.get("ai_context"),
            )
            evaluations.append(ev)
        except EvaluatorUnavailableError as e:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

    # 4. Persist or update submissions and reviews in DB
    item_map = {it["id"]: it for it in items_to_eval}
    for ev in evaluations:
        sub_check = await db.execute(sa.select(Submission).where(Submission.id == ev.submission_id))
        sub_exists = sub_check.scalars().first()

        if not sub_exists:
            source_item = item_map.get(ev.submission_id, {})
            text_body = source_item.get("text", "")
            sub_exists = Submission(
                id=ev.submission_id,
                workspace_id="ws_default",
                submitter_id=str(current_user.id),
                title=ev.submission_title,
                content_type="text",
                text_content=text_body,
                word_count=len(text_body.split()),
                status="shortlisted" if ev.total_score >= 80.0 else "pending",
                source_identifier=ev.submission_id,
            )
            db.add(sub_exists)
            await db.flush()

        # Upsert Review
        rev_check = await db.execute(
            sa.select(Review).where(Review.submission_id == ev.submission_id, Review.rubric_id == rubric.id)
        )
        existing_rev = rev_check.scalars().first()

        rel_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "relevance"), 0.0)
        rea_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "reasoning"), 0.0)
        ori_score = next((c.score for c in ev.criterion_scores if c.criterion_key == "originality"), 0.0)
        crit_payload = [c.model_dump() for c in ev.criterion_scores]

        if existing_rev:
            existing_rev.total_score = ev.total_score
            existing_rev.relevance_score = rel_score
            existing_rev.reasoning_score = rea_score
            existing_rev.originality_score = ori_score
            existing_rev.criterion_scores = crit_payload
            existing_rev.missing_requirements = ev.missing_requirements
            existing_rev.evaluation_metadata = ev.evaluator_metadata
            existing_rev.ai_signal = ev.signals.ai_signal
            existing_rev.ai_score = ev.signals.ai_score
            existing_rev.similarity_score = ev.signals.similarity_score
            existing_rev.status = "shortlisted" if ev.total_score >= 80.0 else "pending"
        else:
            new_rev = Review(
                id=str(uuid.uuid4()),
                submission_id=ev.submission_id,
                reviewer_id=str(current_user.id),
                rubric_id=rubric.id,
                relevance_score=rel_score,
                reasoning_score=rea_score,
                originality_score=ori_score,
                total_score=ev.total_score,
                status="shortlisted" if ev.total_score >= 80.0 else "pending",
                criterion_scores=crit_payload,
                missing_requirements=ev.missing_requirements,
                evaluation_metadata=ev.evaluator_metadata,
                ai_signal=ev.signals.ai_signal,
                ai_score=ev.signals.ai_score,
                similarity_score=ev.signals.similarity_score,
            )
            db.add(new_rev)

        evidence_refs = [
            {"reference_type": "sentence_offset", "identifier": f"crit_{c.criterion_key}", "location": f"{len(c.evidence_excerpts)} excerpts"}
            for c in ev.criterion_scores
        ]
        await append_audit_event(
            db=db,
            event_type="Submission Analyzed",
            target_type="submission",
            target_id=ev.submission_id,
            description=f"{ev.submission_id} · Rubric: {rubric.name} v{rubric.version} · Score: {ev.total_score}% · Evaluator: {req.evaluator_type}",
            actor_id=str(current_user.id),
            decision_rationale=f"Evaluated against rubric '{rubric.name}' with weighted total {ev.total_score}% via {req.evaluator_type}",
            model_version=f"{req.evaluator_type}-v1.2",
            rubric_version=rubric.version,
            result_version="v1",
            uncertainty_status="supported" if not ev.is_incomplete else "inconclusive",
            evidence_references=evidence_refs,
            raw_metadata=ev.evaluator_metadata,
        )

    await db.commit()

    shortlist = rank_and_shortlist(evaluations)

    return APIResponse(
        data=BatchEvaluationResponse(
            rubric_id=rubric.id,
            rubric_name=rubric.name,
            evaluated_count=len(evaluations),
            evaluations=evaluations,
            shortlist=shortlist,
        ),
        message=f"Successfully evaluated {len(evaluations)} submissions against '{rubric.name}'.",
    )


# ── 4. Cohort Shortlist Endpoint ───────────────────────────────────────────────
@router.get(
    "/cohorts/{rubric_id}/shortlist",
    response_model=APIResponse[List[ShortlistedCandidateItem]],
    summary="Get ranked shortlist for a rubric cohort with tie breaking",
)
async def get_cohort_shortlist(
    rubric_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[List[ShortlistedCandidateItem]]:
    rubric_res = await db.execute(sa.select(Rubric).where(Rubric.id == rubric_id))
    rubric = rubric_res.scalars().first()
    if not rubric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Rubric '{rubric_id}' not found.")

    reviews_res = await db.execute(
        sa.select(Review, Submission)
        .join(Submission, Review.submission_id == Submission.id)
        .where(Review.rubric_id == rubric_id)
    )
    pairs = reviews_res.all()

    evaluations: List[EvaluationResult] = []
    overrides_map: Dict[str, Dict[str, Any]] = {}

    for rev, sub in pairs:
        crit_scores = []
        if rev.criterion_scores:
            for c in rev.criterion_scores:
                crit_scores.append(CriterionEvaluation.model_validate(c))

        ev = EvaluationResult(
            submission_id=sub.id,
            submission_title=sub.title,
            rubric_id=rubric.id,
            rubric_name=rubric.name,
            rubric_version=rubric.version,
            total_score=rev.total_score,
            criterion_scores=crit_scores,
            missing_requirements=rev.missing_requirements or [],
            signals=DecoupledSignals(
                quality_score=rev.total_score,
                ai_signal=rev.ai_signal or "Low",
                ai_score=rev.ai_score or 0.0,
                similarity_score=rev.similarity_score or 0.0,
            ),
            evaluator_metadata=rev.evaluation_metadata or {},
        )
        evaluations.append(ev)
        overrides_map[sub.id] = {
            "status": rev.status,
            "override_flag": rev.override_flag,
            "override_reason": rev.override_reason,
            "total_score": rev.total_score,
        }

    shortlist = rank_and_shortlist(evaluations, status_overrides=overrides_map)
    return APIResponse(data=shortlist, message="Cohort shortlist retrieved")


# ── 5. Detailed Submission Evaluation Result ──────────────────────────────────
@router.get(
    "/results/{submission_id}",
    response_model=APIResponse[EvaluationResult],
    summary="Get full evaluation result, criterion excerpts, and decoupled signals for a submission",
)
async def get_submission_evaluation_result(
    submission_id: str,
    rubric_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[EvaluationResult]:
    query = sa.select(Review, Submission, Rubric).join(Submission, Review.submission_id == Submission.id).outerjoin(Rubric, Review.rubric_id == Rubric.id).where(Review.submission_id == submission_id)
    if rubric_id:
        query = query.where(Review.rubric_id == rubric_id)

    res = await db.execute(query)
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No evaluation result found for submission '{submission_id}'.")

    rev, sub, rub = row
    crit_scores = []
    if rev.criterion_scores:
        for c in rev.criterion_scores:
            crit_scores.append(CriterionEvaluation.model_validate(c))

    ev = EvaluationResult(
        submission_id=sub.id,
        submission_title=sub.title,
        rubric_id=rub.id if rub else "",
        rubric_name=rub.name if rub else "Rubric",
        rubric_version=rub.version if rub else 1,
        total_score=rev.total_score,
        criterion_scores=crit_scores,
        missing_requirements=rev.missing_requirements or [],
        signals=DecoupledSignals(
            quality_score=rev.total_score,
            ai_signal=rev.ai_signal or "Low",
            ai_score=rev.ai_score or 0.0,
            similarity_score=rev.similarity_score or 0.0,
        ),
        evaluator_metadata=rev.evaluation_metadata or {},
    )
    return APIResponse(data=ev, message="Evaluation result retrieved")


# ── 6. Reviewer Override & Manual Adjustment ──────────────────────────────────
@router.post(
    "/reviews/{review_id}/override",
    response_model=APIResponse[ReviewRead],
    summary="Authorized reviewer manual score adjustment with mandatory rationale and audit logging",
)
async def override_review(
    review_id: str,
    req: ShortlistOverrideRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ReviewRead]:
    """
    Applies manual reviewer adjustment or status change.
    Requires non-empty override_reason for accountability and records an audit event.
    """
    res = await db.execute(sa.select(Review).where(Review.id == review_id))
    review = res.scalars().first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Review '{review_id}' not found.")

    prev_status = review.status
    prev_score = review.total_score

    review.override_flag = True
    review.override_reason = req.override_reason
    if req.status:
        review.status = req.status
    if req.new_total_score is not None:
        review.total_score = req.new_total_score
    if req.notes:
        review.notes = req.notes

    # Append immutable audit event with hash chaining
    await append_audit_event(
        db=db,
        event_type="Override Recorded",
        target_type="review",
        target_id=review_id,
        description=f"Review {review_id} · Override: {prev_status} → {review.status} · Reason: {req.override_reason}",
        actor_id=str(current_user.id),
        decision_rationale=req.override_reason,
        uncertainty_status="supported",
        raw_metadata={
            "review_id": review_id,
            "previous_status": prev_status,
            "new_status": review.status,
            "previous_score": prev_score,
            "new_score": review.total_score,
            "override_reason": req.override_reason,
        },
    )

    await db.commit()
    await db.refresh(review)

    return APIResponse(data=ReviewRead.model_validate(review), message="Reviewer override applied and audit event logged.")


@router.patch("/submissions/{submission_id}/status")
async def update_submission_status(
    submission_id: str,
    update_req: StatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """Updates candidate status with optional reviewer override rationale (frontend compatibility)."""
    # Check if a review exists for this submission in DB
    rev_res = await db.execute(sa.select(Review).where(Review.submission_id == submission_id))
    rev = rev_res.scalars().first()
    if rev:
        rev.status = update_req.status
        if update_req.override_reason:
            rev.override_flag = True
            rev.override_reason = update_req.override_reason
        await db.commit()

    return APIResponse(
        data={"submission_id": submission_id, "new_status": update_req.status, "updated_by": current_user.email},
        message=f"Submission {submission_id} updated to {update_req.status}",
    )
