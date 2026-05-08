"""Confidence mapping - complexity score to engine confidence.

This module centralizes the interpretation of complexity scores into
engine-specific confidence values, eliminating duplication across engines.

Usage:
    from scripts.converters.confidence import markitdown_confidence, mineru_confidence

    score = detector.analyze(file_path).score
    markitdown_conf = markitdown_confidence(score)
    mineru_conf = mineru_confidence(score)
"""

from dataclasses import dataclass


@dataclass
class ConfidenceThreshold:
    """A single confidence mapping threshold."""
    max_score: float
    confidence: float


# MarkItDown performs best on simple documents (score 0-3)
MARKITDOWN_CONFIDENCE = [
    ConfidenceThreshold(3, 0.8),    # Simple: high confidence
    ConfidenceThreshold(7, 0.4),    # Medium: reduced confidence
    ConfidenceThreshold(float('inf'), 0.2),  # Complex: low confidence
]

# MinerU performs best on complex documents (score 8+)
MINERU_CONFIDENCE = [
    ConfidenceThreshold(3, 0.3),    # Simple: mineru overkill
    ConfidenceThreshold(7, 0.5),    # Medium: viable
    ConfidenceThreshold(float('inf'), 0.9),  # Complex: mineru recommended
]


def get_confidence(score: float, thresholds: list[ConfidenceThreshold]) -> float:
    """
    Map a complexity score to a confidence value using threshold rules.

    Args:
        score: Complexity score from ComplexityDetector (0-10)
        thresholds: List of ConfidenceThreshold sorted by max_score ascending

    Returns:
        Confidence value between 0 and 1
    """
    for threshold in thresholds:
        if score <= threshold.max_score:
            return threshold.confidence
    return thresholds[-1].confidence


def markitdown_confidence(score: float) -> float:
    """Get MarkItDown confidence for a given complexity score."""
    return get_confidence(score, MARKITDOWN_CONFIDENCE)


def mineru_confidence(score: float) -> float:
    """Get MinerU confidence for a given complexity score."""
    return get_confidence(score, MINERU_CONFIDENCE)