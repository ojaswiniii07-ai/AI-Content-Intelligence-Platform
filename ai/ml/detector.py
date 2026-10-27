"""
AuthentiQ ML Inference Engine
==============================
detector.py — loads the trained TF-IDF + ensemble (SGD + LightGBM) models
and exposes detect() and detect_spans() for FastAPI.

Usage (in FastAPI endpoint):
    from ai.ml.detector import get_detector
    result       = get_detector().detect(req.text)
    span_result  = get_detector().detect_spans(req.text)
"""

import joblib
import json
import re
import numpy as np
from pathlib import Path
from scipy.sparse import hstack, csr_matrix
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Models are stored next to this file in ./models/
MODELS_DIR = Path(__file__).parent / "models"


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class SentenceSpan:
    """One sentence and its AI-probability heat level."""
    text:  str
    heat:  str    # 'low' | 'mid' | 'high'
    score: float
    start: int
    end:   int


@dataclass
class DetectionResult:
    """Full detection result returned by AuthentiQDetector.detect()."""
    ai_probability:   float
    overall_score:    float   # 0–100
    verdict:          str
    confidence_level: str
    model_version:    str
    word_count:       int
    char_count:       int
    sentence_spans:   List[SentenceSpan]
    dimensions:       dict

    def to_dict(self) -> dict:
        return {
            'ai_probability': self.ai_probability,
            'overall_score': self.overall_score,
            'verdict': self.verdict,
            'confidence_level': self.confidence_level,
            'model_version': self.model_version,
            'word_count': self.word_count,
            'char_count': self.char_count,
            'sentence_spans': [
                {
                    'text': s.text,
                    'heat': s.heat,
                    'score': s.score,
                    'start': s.start,
                    'end': s.end,
                }
                for s in self.sentence_spans
            ],
            'dimensions': [
                {'name': k, 'pct': v, 'description': ''}
                for k, v in self.dimensions.items()
            ],
        }



# ── Main detector class ──────────────────────────────────────────────────────

class AuthentiQDetector:
    """
    Singleton inference engine for AI-text detection.
    Wraps TF-IDF char/word n-grams + linguistic features + SGD + LightGBM ensemble.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        if not self.models_dir.exists():
            raise FileNotFoundError(
                f"Models directory not found: {self.models_dir}\n"
                "Run notebook 02_model_training.ipynb first."
            )
        self.tfidf_char = joblib.load(self.models_dir / "tfidf_char.pkl")
        self.tfidf_word = joblib.load(self.models_dir / "tfidf_word.pkl")
        self.sgd_clf    = joblib.load(self.models_dir / "sgd_classifier.pkl")
        self.lgb_model  = joblib.load(self.models_dir / "lgb_classifier.pkl")
        with open(self.models_dir / "model_meta.json") as f:
            self.meta = json.load(f)
        self.threshold = self.meta["optimal_threshold"]
        self.w_sgd     = self.meta["sgd_weight"]
        self.w_lgb     = self.meta["lgb_weight"]

    # ── Preprocessing ────────────────────────────────────────────────────────

    @staticmethod
    def _preprocess(text: str) -> str:
        """Normalise whitespace and lowercase — matches training preprocessing."""
        text = str(text).strip()
        text = re.sub(r'\r\n|\r', '\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        return text.lower()

    # ── Feature engineering ──────────────────────────────────────────────────

    @staticmethod
    def _linguistic_features(texts: List[str]) -> np.ndarray:
        """12-dimensional hand-crafted feature vector per text."""
        if not texts:
            return np.empty((0, 12), dtype=np.float32)
        rows = []
        for text in texts:
            words = text.split()
            sents = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            sl    = [len(s.split()) for s in sents]
            rows.append([
                len(text),                                                      # char_len
                len(words),                                                     # word_count
                len(sents),                                                     # sent_count
                len(set(words)) / max(len(words), 1),                          # vocab_richness
                float(np.std(sl)) if len(sl) > 1 else 0.0,                     # sent_burstiness
                float(np.mean(sl)) if sl else 0.0,                              # avg_sent_len
                text.count(',') / max(len(words), 1),                          # comma_density
                text.count('!') / max(len(words), 1),                          # excl_density
                text.count('\n\n') + 1,                                         # paragraph_count
                text.count('furthermore') + text.count('additionally'),         # ai_connectors
                text.count('moreover') + text.count('delve'),                   # ai_filler
                sum(1 for w in words if w.isupper() and len(w) > 1) /
                max(len(words), 1),                                             # caps_ratio
            ])
        return np.array(rows, dtype=np.float32)

    def _build_features(self, texts: List[str]):
        """Stack char TF-IDF + word TF-IDF + linguistic features."""
        X_char = self.tfidf_char.transform(texts)
        X_word = self.tfidf_word.transform(texts)
        X_ling = self._linguistic_features(texts)
        return hstack([X_char, X_word, csr_matrix(X_ling)])

    def _ensemble_proba(self, X) -> np.ndarray:
        """Weighted average of SGD and LightGBM probabilities."""
        p_sgd = self.sgd_clf.predict_proba(X)[:, 1]
        p_lgb = self.lgb_model.predict_proba(X)[:, 1]
        return self.w_sgd * p_sgd + self.w_lgb * p_lgb

    # ── Helper classifiers ───────────────────────────────────────────────────

    @staticmethod
    def _heat_label(score: float) -> str:
        if score >= 0.70: return 'high'
        if score >= 0.40: return 'mid'
        return 'low'

    @staticmethod
    def _verdict(prob: float, threshold: float) -> Tuple[str, str]:
        if prob >= 0.85:       return 'Highly Likely AI',  'High Confidence'
        if prob >= threshold:  return 'Likely AI',         'Medium Confidence'
        if prob >= 0.35:       return 'Uncertain / Mixed', 'Low Confidence'
        return 'Likely Human',                             'Medium Confidence'

    # ── Public API ───────────────────────────────────────────────────────────

    def detect(self, text: str) -> DetectionResult:
        """
        Run full detection on a single text string.
        Returns a DetectionResult with global score + sentence-level spans.
        """
        if not text or not text.strip() or len(text.strip().split()) < 3:
            return DetectionResult(
                ai_probability=0.0,
                overall_score=0.0,
                verdict="Insufficient Text",
                confidence_level="Low Confidence",
                model_version=self.meta.get("model_version", "1.0.0"),
                word_count=len(text.split()) if text else 0,
                char_count=len(text) if text else 0,
                sentence_spans=[],
                dimensions={
                    "AI-Typical Phrasing": 0.0,
                    "Structural Patterns": 0.0,
                    "Source Similarity": 0.0,
                    "Style Consistency": 0.0,
                },
            )

        clean    = self._preprocess(text)
        X_global = self._build_features([clean])
        ai_prob  = float(self._ensemble_proba(X_global)[0])

        # Sentence-level attribution
        raw_sentences = [
            s.strip() for s in re.split(r'(?<=[.!?])\s+', text)
            if len(s.strip()) > 10
        ]
        sent_spans: List[SentenceSpan] = []
        if raw_sentences:
            clean_sents = [self._preprocess(s) for s in raw_sentences]
            X_sents     = self._build_features(clean_sents)
            sent_scores = self._ensemble_proba(X_sents)
            cursor = 0
            for sent, score in zip(raw_sentences, sent_scores):
                start = text.find(sent, cursor)
                if start == -1:
                    start = cursor
                end = start + len(sent)
                sent_spans.append(SentenceSpan(
                    text=sent,
                    heat=self._heat_label(float(score)),
                    score=round(float(score), 3),
                    start=max(start, 0),
                    end=end,
                ))
                cursor = end

        # Dimension breakdown
        words   = clean.split()
        sents_c = [s.strip() for s in re.split(r'[.!?]+', clean) if s.strip()]
        sl      = [len(s.split()) for s in sents_c]
        burstiness = np.std(sl) / max(np.mean(sl), 1) if sl else 0
        dims = {
            'AI-Typical Phrasing': round(min(100,
                (clean.count('furthermore') + clean.count('additionally') +
                 clean.count('delve') + clean.count('moreover')) * 12 + ai_prob * 40), 1),
            'Structural Patterns': round(min(100, max(0,
                (1 - burstiness) * 60 + ai_prob * 40)), 1),
            'Source Similarity':   round(ai_prob * 50, 1),
            'Style Consistency':   round(min(100,
                (1 - len(set(words)) / max(len(words), 1)) * 50 + ai_prob * 50), 1),
        }

        verdict, confidence = self._verdict(ai_prob, self.threshold)
        return DetectionResult(
            ai_probability=round(ai_prob, 4),
            overall_score=round(ai_prob * 100, 1),
            verdict=verdict,
            confidence_level=confidence,
            model_version=self.meta['model_version'],
            word_count=len(text.split()),
            char_count=len(text),
            sentence_spans=sent_spans,
            dimensions=dims,
        )

    def detect_spans(self, text: str, method: str = 'window') -> dict:
        """
        Detect which specific parts of a mixed text are AI vs Human written.
        Returns per-sentence scores AND merged consecutive blocks.

        Args:
            text:   The text to analyse (can be mixed human + AI)
            method: 'sentence' — score each sentence independently
                    'window'   — sliding window of 3 sentences (recommended)
        """
        min_len     = 15
        window_size = 3

        # Split into sentences
        raw = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in raw if len(s.strip()) >= min_len]

        if not sentences:
            return {
                'document_summary': {},
                'sentence_spans':   [],
                'merged_blocks':    [],
                'model_version':    self.meta['model_version'],
                'threshold':        self.threshold,
            }

        # Score each sentence
        if method == 'sentence':
            # Each sentence scored independently
            clean_sents = [self._preprocess(s) for s in sentences]
            X = self._build_features(clean_sents)
            scores = self._ensemble_proba(X).tolist()

        else:
            # Sliding window — context-aware scoring
            n      = len(sentences)
            scores = np.zeros(n)
            counts = np.zeros(n)
            for i in range(n):
                start = max(0, i - window_size // 2)
                end   = min(n, start + window_size)
                window_text = ' '.join(sentences[start:end])
                X_win = self._build_features([self._preprocess(window_text)])
                score = float(self._ensemble_proba(X_win)[0])
                for j in range(start, end):
                    scores[j] += score
                    counts[j] += 1
            scores = (scores / np.maximum(counts, 1)).tolist()

        # Build span objects with char offsets
        spans  = []
        cursor = 0
        for sent, score in zip(sentences, scores):
            start = text.find(sent, cursor)
            if start == -1:
                start = cursor
            end = start + len(sent)
            spans.append({
                'text':  sent,
                'label': 'AI' if score >= self.threshold else 'Human',
                'score': round(float(score), 3),
                'heat':  self._heat_label(float(score)),
                'start': max(start, 0),
                'end':   end,
            })
            cursor = end

        # Merge consecutive same-label spans into blocks
        merged = []
        if spans:
            current = {
                'text': spans[0]['text'],
                'label': spans[0]['label'],
                'heat': spans[0]['heat'],
                'start': spans[0]['start'],
                'end': spans[0]['end'],
                'score': spans[0]['score'],
                '_scores': [spans[0]['score']],
            }
            for span in spans[1:]:
                if span['label'] == current['label']:
                    current['text'] += ' ' + span['text']
                    current['end'] = span['end']
                    current['_scores'].append(span['score'])
                    current['score'] = round(float(np.mean(current['_scores'])), 3)
                    current['heat'] = self._heat_label(current['score'])
                else:
                    del current['_scores']
                    merged.append(current)
                    current = {
                        'text': span['text'],
                        'label': span['label'],
                        'heat': span['heat'],
                        'start': span['start'],
                        'end': span['end'],
                        'score': span['score'],
                        '_scores': [span['score']],
                    }
            if '_scores' in current:
                del current['_scores']
            merged.append(current)

        # Document summary stats
        ai_spans    = [s for s in spans if s['label'] == 'AI']
        human_spans = [s for s in spans if s['label'] == 'Human']
        total_chars = sum(len(s['text']) for s in spans) or 1
        ai_chars    = sum(len(s['text']) for s in ai_spans)
        summary = {
            'total_sentences': len(spans),
            'ai_sentences':    len(ai_spans),
            'human_sentences': len(human_spans),
            'ai_percentage':   round(len(ai_spans) / max(len(spans), 1) * 100, 1),
            'ai_char_pct':     round(ai_chars / total_chars * 100, 1),
            'avg_ai_score':    round(
                float(np.mean([s['score'] for s in ai_spans])), 3
            ) if ai_spans else 0.0,
            'avg_human_score': round(
                float(np.mean([s['score'] for s in human_spans])), 3
            ) if human_spans else 0.0,
        }

        return {
            'document_summary': summary,
            'sentence_spans':   spans,
            'merged_blocks':    merged,
            'model_version':    self.meta['model_version'],
            'threshold':        self.threshold,
        }


# ── Module-level lazy singleton ──────────────────────────────────────────────

_instance: Optional[AuthentiQDetector] = None


def get_detector() -> AuthentiQDetector:
    """
    Returns the shared AuthentiQDetector singleton.
    Call from FastAPI endpoints — models are loaded only once at startup.
    """
    global _instance
    if _instance is None:
        _instance = AuthentiQDetector()
    return _instance
