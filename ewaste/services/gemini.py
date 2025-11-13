"""Utilities for estimating device values via Gemini."""
from __future__ import annotations

import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised through patched calls in tests
    import google.generativeai as genai  # type: ignore
except ImportError:  # pragma: no cover - handled gracefully in runtime
    genai = None

_GEMINI_MODEL_CACHE: Optional[Any] = None

DEFAULT_MODEL_NAME = "gemini-2.5-flash"


class GeminiUnavailable(RuntimeError):
    """Raised when Gemini cannot be reached or configured."""


def _get_model() -> Any:
    """Return a configured GenerativeModel instance or raise."""
    global _GEMINI_MODEL_CACHE

    if _GEMINI_MODEL_CACHE is not None:
        return _GEMINI_MODEL_CACHE

    api_key =  "AIzaSyBMY4EPNctAvZQKau2eKIyLzTJfbQ3_Nnw"
    if not api_key:
        raise GeminiUnavailable("GEMINI_API_KEY is not configured")

    if genai is None:
        raise GeminiUnavailable("google-generativeai package is not installed")

    try:
        genai.configure(api_key=api_key)
        model_name = getattr(settings, "GEMINI_MODEL_NAME", DEFAULT_MODEL_NAME)
        _GEMINI_MODEL_CACHE = genai.GenerativeModel(model_name)
        return _GEMINI_MODEL_CACHE
    except Exception as exc:  # pragma: no cover - depends on external SDK
        raise GeminiUnavailable("Failed to initialise Gemini client") from exc


def _clean_response_text(raw_text: str) -> str:
    """Strip common markdown fences returned by LLMs."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if line.strip()]
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _coerce_decimal(value: Any) -> Optional[Decimal]:
    if value in (None, ""):
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _build_prompt(payload: Dict[str, Any]) -> str:
    device_name = payload.get("device_name") or "Unknown device"
    category = payload.get("device_category") or "Unknown category"
    facility = payload.get("facility_name") or "Unknown facility"
    user_mass = payload.get("user_estimated_mass")
    components: Iterable[str] = payload.get("components") or []
    user_notes = payload.get("user_notes") or ""

    component_list = "\n".join(f"- {component}" for component in components) or "- None provided"
    user_mass_line = f"User supplied estimated precious metal mass (grams): {user_mass or 'Not provided'}"

    prompt = f"""
You are an e-waste recovery analyst. Estimate the potential precious metal mass and recycling credits for a device drop-off.

Device name: {device_name}
Device category: {category}
Facility: {facility}
{user_mass_line}
Relevant hazardous components:\n{component_list}
Additional user notes: {user_notes or 'None'}

Respond strictly as compact JSON with the following keys:
  "estimated_precious_metal_mass_grams" (number, >= 0)
  "estimated_credit_value" (number, >= 0)
  "confidence" (string label such as "low", "medium", "high")
Include no explanatory text outside the JSON.
"""
    return prompt.strip()


def _extract_text(response: Any) -> Optional[str]:  # pragma: no cover - SDK behaviour
    if not response:
        return None

    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    candidates = getattr(response, "candidates", None)
    if candidates:
        for candidate in candidates:
            content_parts = getattr(candidate, "content", None)
            if not content_parts:
                continue
            # candidate.content may expose a parts list
            parts = getattr(content_parts, "parts", None) or getattr(candidate, "parts", None)
            if not parts:
                continue
            texts = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
            joined = "\n".join(texts).strip()
            if joined:
                return joined
    return None


def estimate_device_metrics(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call Gemini to estimate device recovery metrics.

    Returns a dictionary containing Decimal values when successful, otherwise None.
    """
    try:
        model = _get_model()
    except GeminiUnavailable as exc:
        logger.info("Gemini unavailable: %s", exc)
        return None

    prompt = _build_prompt(payload)
    if not prompt:
        return None

    try:
        response = model.generate_content(prompt)
    except Exception as exc:  # pragma: no cover - depends on external SDK
        logger.warning("Gemini request failed: %s", exc)
        return None

    text = _extract_text(response)
    if not text:
        logger.debug("Gemini response missing text payload")
        return None

    try:
        structured = json.loads(_clean_response_text(text))
    except json.JSONDecodeError as exc:
        logger.debug("Failed to decode Gemini response as JSON: %s", exc)
        return None

    mass = _coerce_decimal(structured.get("estimated_precious_metal_mass_grams"))
    credit_value = _coerce_decimal(structured.get("estimated_credit_value"))
    confidence = structured.get("confidence")

    result: Dict[str, Any] = {"raw_response": text}

    if mass is not None and mass >= 0:
        result["estimated_precious_metal_mass_grams"] = mass
    if credit_value is not None and credit_value >= 0:
        result["estimated_credit_value"] = credit_value
    if isinstance(confidence, str) and confidence:
        result["confidence"] = confidence

    if len(result) == 1:  # only raw_response
        return None

    return result
