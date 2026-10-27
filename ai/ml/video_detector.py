"""
AuthentiQ Video Deepfake Detection — Inference Engine
=====================================================
video_detector.py — loads fine-tuned EfficientNet-B0 + MTCNN face detector
and exposes detect_video() and detect_frame() for FastAPI.

Usage (in FastAPI endpoint):
    from ai.ml.video_detector import get_video_detector
    result = get_video_detector().detect_video(video_path)
    result = get_video_detector().detect_frame(image_path_or_array)

Architecture:
    Video → Frame Sampling → MTCNN Face Crop → EfficientNet-B0 → P(fake)
    Per-frame predictions are aggregated (mean + max) for video-level verdict.

Reference:
    https://www.kaggle.com/code/muhammadhusban/deepfake-detection/notebook
"""

import json
import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

try:
    from facenet_pytorch import MTCNN
except ImportError:
    MTCNN = None

try:
    from efficientnet_pytorch import EfficientNet
except ImportError:
    EfficientNet = None

from PIL import Image

# Models stored alongside this file in ./models/
MODELS_DIR = Path(__file__).parent / "models"

# ImageNet normalization constants
IMAGENET_MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
IMAGENET_STD  = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class FrameResult:
    """Detection result for a single video frame."""
    frame_index: int
    fake_probability: float
    verdict: str       # 'Real' | 'Fake'
    confidence: str    # 'High' | 'Medium' | 'Low'
    face_detected: bool


@dataclass
class VideoDetectionResult:
    """Full detection result for a video file."""
    fake_probability: float     # Aggregated probability (0–1)
    overall_score: float        # 0–100
    verdict: str                # 'Likely Deepfake' | 'Likely Authentic' | 'Uncertain'
    confidence_level: str       # 'High Confidence' | 'Medium Confidence' | 'Low Confidence'
    model_version: str
    total_frames_sampled: int
    faces_detected: int
    frame_results: List[FrameResult]
    aggregation_method: str     # 'mean+max weighted'

    def to_dict(self) -> dict:
        return {
            'fake_probability': self.fake_probability,
            'overall_score': self.overall_score,
            'verdict': self.verdict,
            'confidence_level': self.confidence_level,
            'model_version': self.model_version,
            'total_frames_sampled': self.total_frames_sampled,
            'faces_detected': self.faces_detected,
            'frame_results': [
                {
                    'frame_index': f.frame_index,
                    'fake_probability': f.fake_probability,
                    'verdict': f.verdict,
                    'confidence': f.confidence,
                    'face_detected': f.face_detected,
                }
                for f in self.frame_results
            ],
            'aggregation_method': self.aggregation_method,
        }


# ── Model Architecture ──────────────────────────────────────────────────────

class DeepfakeDetector(nn.Module):
    """
    EfficientNet-based deepfake detector with custom classification head.

    Architecture:
        EfficientNet-B0 backbone (pre-trained on ImageNet, fine-tuned on DFDC)
        → AdaptiveAvgPool → Dropout → FC(1280, 512) → ReLU → BN → Dropout → FC(512, 1)
    """

    def __init__(self, model_name='efficientnet-b0', dropout=0.3):
        super().__init__()

        if EfficientNet is None:
            raise ImportError(
                "efficientnet-pytorch is required. Install with: pip install efficientnet-pytorch"
            )

        self.backbone = EfficientNet.from_name(model_name)
        in_features = self.backbone._fc.in_features  # 1280 for B0
        self.backbone._fc = nn.Identity()

        self.classifier = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, 512),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(512),
            nn.Dropout(p=dropout / 2),
            nn.Linear(512, 1),
        )

    def forward(self, x):
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits.squeeze(1)


# ── Main Inference Engine ────────────────────────────────────────────────────

class AuthentiQVideoDetector:
    """
    Singleton inference engine for video deepfake detection.
    Wraps MTCNN face extractor + fine-tuned EfficientNet-B0.
    """

    def __init__(self, models_dir: Path = MODELS_DIR):
        self.models_dir = Path(models_dir)
        self.device = torch.device(
            'cuda' if torch.cuda.is_available()
            else 'mps' if torch.backends.mps.is_available()
            else 'cpu'
        )

        # Load metadata
        meta_path = self.models_dir / "deepfake_meta.json"
        if meta_path.exists():
            with open(meta_path) as f:
                self.meta = json.load(f)
        else:
            self.meta = {
                'model_version': '1.0.0',
                'model_name': 'efficientnet-b0',
                'image_size': 224,
                'n_frames': 16,
                'margin': 40,
                'min_face_size': 60,
                'threshold': 0.5,
            }

        self.image_size = self.meta.get('image_size', 224)
        self.n_frames = self.meta.get('n_frames', 16)
        self.threshold = self.meta.get('threshold', 0.5)

        # Initialize MTCNN face detector
        if MTCNN is not None:
            self.face_detector = MTCNN(
                image_size=self.image_size,
                margin=self.meta.get('margin', 40),
                min_face_size=self.meta.get('min_face_size', 60),
                thresholds=[0.6, 0.7, 0.7],
                post_process=False,
                device=self.device,
            )
        else:
            self.face_detector = None

        # Load model
        self.model = DeepfakeDetector(
            model_name=self.meta.get('model_name', 'efficientnet-b0'),
        ).to(self.device)

        # Load trained weights if available
        ckpt_path = self.models_dir / "deepfake_efficientnet_b0.pth"
        if ckpt_path.exists():
            checkpoint = torch.load(ckpt_path, map_location=self.device, weights_only=True)
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)

        self.model.eval()

        # Normalization tensors on device
        self._mean = IMAGENET_MEAN.to(self.device)
        self._std = IMAGENET_STD.to(self.device)

    # ── Frame extraction ─────────────────────────────────────────────────────

    def _extract_frames(self, video_path: str, n_frames: int = None) -> list:
        """Sample n_frames evenly from a video file."""
        n_frames = n_frames or self.n_frames
        cap = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if total <= 0:
            cap.release()
            return []

        indices = np.linspace(0, total - 1, min(n_frames, total), dtype=int)
        frames = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append((int(idx), Image.fromarray(frame_rgb)))

        cap.release()
        return frames

    # ── Face detection ───────────────────────────────────────────────────────

    def _detect_face(self, pil_image: Image.Image) -> Optional[torch.Tensor]:
        """Run MTCNN on a PIL Image, return face crop tensor or None."""
        if self.face_detector is None:
            # Fallback: center crop and resize
            img = pil_image.resize((self.image_size, self.image_size))
            arr = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(arr).permute(2, 0, 1)

        try:
            face = self.face_detector(pil_image)
            if face is not None:
                return face.float() / 255.0
        except Exception:
            pass
        return None

    # ── Prediction helpers ───────────────────────────────────────────────────

    @torch.no_grad()
    def _predict_face(self, face_tensor: torch.Tensor) -> float:
        """Predict fake probability for a single face tensor."""
        # Normalize on target device
        face = face_tensor.to(self.device)
        x = (face - self._mean) / self._std
        x = x.unsqueeze(0)
        logit = self.model(x)
        return float(torch.sigmoid(logit).item())

    @staticmethod
    def _confidence_label(prob: float) -> str:
        if prob >= 0.85 or prob <= 0.15:
            return 'High'
        if prob >= 0.65 or prob <= 0.35:
            return 'Medium'
        return 'Low'

    @staticmethod
    def _verdict(prob: float, threshold: float) -> Tuple[str, str]:
        if prob >= 0.80:
            return 'Highly Likely Deepfake', 'High Confidence'
        if prob >= threshold:
            return 'Likely Deepfake', 'Medium Confidence'
        if prob >= 0.35:
            return 'Uncertain / Mixed', 'Low Confidence'
        if prob >= 0.15:
            return 'Likely Authentic', 'Medium Confidence'
        return 'Highly Likely Authentic', 'High Confidence'

    # ── Public API ───────────────────────────────────────────────────────────

    def detect_video(self, video_path: str, n_frames: int = None) -> VideoDetectionResult:
        """
        Detect if a video is a deepfake.

        Args:
            video_path: Path to the video file (.mp4, .avi, .mov, etc.)
            n_frames:   Number of frames to sample (default: from config)

        Returns:
            VideoDetectionResult with per-frame and aggregated scores.
        """
        frames = self._extract_frames(video_path, n_frames)

        if not frames:
            return VideoDetectionResult(
                fake_probability=0.0,
                overall_score=0.0,
                verdict="No Frames Extracted",
                confidence_level="Low Confidence",
                model_version=self.meta.get('model_version', '1.0.0'),
                total_frames_sampled=0,
                faces_detected=0,
                frame_results=[],
                aggregation_method='none',
            )

        # Process each frame
        frame_results = []
        face_probs = []

        for frame_idx, pil_image in frames:
            face_tensor = self._detect_face(pil_image)

            if face_tensor is not None:
                prob = self._predict_face(face_tensor)
                face_probs.append(prob)
                frame_results.append(FrameResult(
                    frame_index=frame_idx,
                    fake_probability=round(prob, 4),
                    verdict='Fake' if prob >= self.threshold else 'Real',
                    confidence=self._confidence_label(prob),
                    face_detected=True,
                ))
            else:
                frame_results.append(FrameResult(
                    frame_index=frame_idx,
                    fake_probability=0.0,
                    verdict='No Face',
                    confidence='Low',
                    face_detected=False,
                ))

        # Aggregate frame-level predictions
        if face_probs:
            mean_prob = float(np.mean(face_probs))
            max_prob = float(np.max(face_probs))
            # Weighted: 70% mean + 30% max (catches even occasional deepfake frames)
            agg_prob = 0.7 * mean_prob + 0.3 * max_prob
        else:
            agg_prob = 0.0

        verdict, confidence = self._verdict(agg_prob, self.threshold)

        return VideoDetectionResult(
            fake_probability=round(agg_prob, 4),
            overall_score=round(agg_prob * 100, 1),
            verdict=verdict,
            confidence_level=confidence,
            model_version=self.meta.get('model_version', '1.0.0'),
            total_frames_sampled=len(frames),
            faces_detected=len(face_probs),
            frame_results=frame_results,
            aggregation_method='mean(0.7)+max(0.3) weighted',
        )

    def detect_frame(self, image) -> dict:
        """
        Detect if a single image/frame contains a deepfake face.

        Args:
            image: PIL Image, numpy array (H,W,3 RGB), or file path string.

        Returns:
            dict with 'fake_probability', 'verdict', 'confidence', 'face_detected'.
        """
        # Convert input to PIL Image
        if isinstance(image, str) or isinstance(image, Path):
            img = cv2.imread(str(image))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img)
        elif isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        elif isinstance(image, Image.Image):
            pil_image = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")

        face_tensor = self._detect_face(pil_image)

        if face_tensor is not None:
            prob = self._predict_face(face_tensor)
            return {
                'fake_probability': round(prob, 4),
                'verdict': 'Fake' if prob >= self.threshold else 'Real',
                'confidence': self._confidence_label(prob),
                'face_detected': True,
            }
        else:
            return {
                'fake_probability': 0.0,
                'verdict': 'No Face Detected',
                'confidence': 'Low',
                'face_detected': False,
            }


# ── Module-level lazy singleton ──────────────────────────────────────────────

_instance: Optional[AuthentiQVideoDetector] = None


def get_video_detector() -> AuthentiQVideoDetector:
    """
    Returns the shared AuthentiQVideoDetector singleton.
    Call from FastAPI endpoints — models are loaded only once at startup.
    """
    global _instance
    if _instance is None:
        _instance = AuthentiQVideoDetector()
    return _instance
