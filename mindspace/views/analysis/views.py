"""
Analysis views for the new MindSpace PostgreSQL schema.

This file is designed for your current structure:
    mindspace/views/analysis/views.py

Your models are stored in:
    mindspace/models.py

So imports must come from `mindspace.models`, not `.models`.
"""

from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from mindspace.models import (
    FacialAnalysisResult,
    FusionPrediction,
    ModalityResult,
    PlatformScreeningSession,
    TextAnalysisResult,
    VoiceAnalysisResult,
)


# ============================================================
# HELPERS
# ============================================================

def _json_value(value):
    """Convert Decimal/UUID/date-like values into JSON-safe values."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _score_dict(*, stress=None, depression=None, anxiety=None, speech_impairment=None,
                bipolar=None, suicidal=None, confidence=None):
    """Return only non-null scores as plain JSON numbers."""
    data = {
        "stress": _json_value(stress),
        "depression": _json_value(depression),
        "anxiety": _json_value(anxiety),
        "speech_impairment": _json_value(speech_impairment),
        "bipolar": _json_value(bipolar),
        "suicidal": _json_value(suicidal),
        "confidence": _json_value(confidence),
    }
    return {key: value for key, value in data.items() if value is not None}


def _dominant_from_scores(scores):
    """Pick the highest clinical score, ignoring confidence."""
    ignored = {"confidence"}
    clean_scores = {
        key: value
        for key, value in scores.items()
        if key not in ignored and isinstance(value, (int, float))
    }
    if not clean_scores:
        return None, None

    dominant_key = max(clean_scores, key=clean_scores.get)
    return dominant_key, clean_scores[dominant_key]


def _risk_from_score(score):
    """Simple dashboard label from 0-100 score."""
    if score is None:
        return None
    if score >= 75:
        return "high"
    if score >= 40:
        return "moderate"
    return "low"


def _facial_result_payload(result):
    scores = _score_dict(
        stress=result.stress_score,
        depression=result.depression_score,
        anxiety=result.anxiety_score,
        confidence=result.confidence_score,
    )
    dominant, probability = _dominant_from_scores(scores)

    return {
        "id": str(result.facial_analysis_id),
        "analysis_type": "face",
        "source_type": "facial_analysis_result",
        "source_id": str(result.feature_id),
        "status": "completed",
        "dominant_risk": result.risk_label or dominant,
        "risk_level": _risk_from_score(probability),
        "risk_probability": probability,
        "scores": scores,
        "api_version": result.api_version,
        "processed_at": _json_value(result.processed_at),
        "created_at": _json_value(result.processed_at),
    }


def _voice_result_payload(result):
    scores = _score_dict(
        stress=result.stress_score,
        depression=result.depression_score,
        speech_impairment=result.speech_impairment_score,
        confidence=result.confidence_score,
    )
    dominant, probability = _dominant_from_scores(scores)

    return {
        "id": str(result.voice_analysis_id),
        "analysis_type": "voice",
        "source_type": "voice_analysis_result",
        "source_id": str(result.feature_id),
        "status": "completed",
        "dominant_risk": dominant,
        "risk_level": _risk_from_score(probability),
        "risk_probability": probability,
        "scores": scores,
        "api_version": result.api_version,
        "processed_at": _json_value(result.processed_at),
        "created_at": _json_value(result.processed_at),
    }


def _text_result_payload(result):
    scores = _score_dict(
        stress=result.stress_score,
        depression=result.depression_score,
        anxiety=result.anxiety_score,
        confidence=result.confidence_score,
    )
    dominant, probability = _dominant_from_scores(scores)

    return {
        "id": str(result.text_analysis_id),
        "analysis_type": "text",
        "source_type": "text_analysis_result",
        "source_id": str(result.text_parameter_id),
        "status": "completed",
        "dominant_risk": dominant,
        "risk_level": _risk_from_score(probability),
        "risk_probability": probability,
        "scores": scores,
        "api_version": result.api_version,
        "processed_at": _json_value(result.processed_at),
        "created_at": _json_value(result.processed_at),
    }


def _fusion_result_payload(result):
    scores = _score_dict(
        stress=result.stress_score,
        depression=result.depression_score,
        anxiety=result.anxiety_score,
        bipolar=result.bipolar_score,
        suicidal=result.suicidal_score,
        confidence=result.confidence_score,
    )
    dominant, probability = _dominant_from_scores(scores)

    return {
        "id": str(result.prediction_id),
        "analysis_type": "fusion",
        "source_type": "fusion_prediction",
        "source_id": str(result.screening_session_id),
        "status": "completed",
        "dominant_risk": dominant,
        "risk_level": result.overall_risk or _risk_from_score(probability),
        "risk_probability": probability,
        "scores": scores,
        "final_prediction_json": result.final_prediction_json,
        "created_at": _json_value(result.predicted_at),
    }


def _get_user_sessions(user):
    return PlatformScreeningSession.objects.filter(user=user)


# ============================================================
# API: ALL ANALYSIS RESULTS FOR CURRENT USER
# ============================================================

@login_required
def analysis_results_view(request):
    """
    Return analysis results for the current user.

    Optional query params:
        ?type=face
        ?type=voice
        ?type=text
        ?type=fusion
    """
    analysis_type = request.GET.get("type", "").strip().lower()
    sessions = _get_user_sessions(request.user)

    results = []

    if analysis_type in ["", "face"]:
        face_results = FacialAnalysisResult.objects.filter(
            feature__video_session__screening_session__in=sessions
        ).select_related("feature").order_by("-processed_at")
        results.extend(_facial_result_payload(item) for item in face_results)

    if analysis_type in ["", "voice"]:
        voice_results = VoiceAnalysisResult.objects.filter(
            feature__audio_extraction__attempt__phonation_session__screening_session__in=sessions
        ).select_related("feature").order_by("-processed_at")
        results.extend(_voice_result_payload(item) for item in voice_results)

    if analysis_type in ["", "text"]:
        text_results = TextAnalysisResult.objects.filter(
            text_parameter__transcript__scenario_session__screening_session__in=sessions
        ).select_related("text_parameter").order_by("-processed_at")
        results.extend(_text_result_payload(item) for item in text_results)

    if analysis_type in ["", "fusion", "final"]:
        fusion_results = FusionPrediction.objects.filter(
            screening_session__in=sessions
        ).select_related("screening_session").order_by("-predicted_at")
        results.extend(_fusion_result_payload(item) for item in fusion_results)

    # Sort safely by created_at/processed_at. Null dates go last.
    results.sort(key=lambda item: item.get("created_at") or "", reverse=True)

    return JsonResponse({
        "success": True,
        "count": len(results),
        "results": results,
    })


# ============================================================
# API: SINGLE ANALYSIS RESULT DETAIL
# ============================================================

@login_required
def analysis_result_detail(request, result_id):
    """
    Return a single result detail.

    Use query param to avoid ambiguity:
        /analysis/result/<uuid>/?type=face
        /analysis/result/<uuid>/?type=voice
        /analysis/result/<uuid>/?type=text
        /analysis/result/<uuid>/?type=fusion
    """
    analysis_type = request.GET.get("type", "").strip().lower()
    sessions = _get_user_sessions(request.user)

    if analysis_type == "face":
        result = get_object_or_404(
            FacialAnalysisResult,
            facial_analysis_id=result_id,
            feature__video_session__screening_session__in=sessions,
        )
        payload = _facial_result_payload(result)
        payload["features"] = {
            "feature_id": str(result.feature_id),
            "model_version": result.feature.model_version,
            "frame_number": result.feature.frame_number,
            "emotion_scores": result.feature.emotion_scores,
            "head_pose": result.feature.head_pose,
            "eye_tracking": result.feature.eye_tracking,
            "blink_rate": _json_value(result.feature.blink_rate),
        }
        return JsonResponse({"success": True, "result": payload})

    if analysis_type == "voice":
        result = get_object_or_404(
            VoiceAnalysisResult,
            voice_analysis_id=result_id,
            feature__audio_extraction__attempt__phonation_session__screening_session__in=sessions,
        )
        payload = _voice_result_payload(result)
        payload["features"] = {
            "feature_id": str(result.feature_id),
            "model_version": result.feature.model_version,
            "pitch_mean": _json_value(result.feature.pitch_mean),
            "jitter": _json_value(result.feature.jitter),
            "shimmer": _json_value(result.feature.shimmer),
            "hnr": _json_value(result.feature.hnr),
            "voice_energy": _json_value(result.feature.voice_energy),
            "mfcc_features": result.feature.mfcc_features,
        }
        return JsonResponse({"success": True, "result": payload})

    if analysis_type == "text":
        result = get_object_or_404(
            TextAnalysisResult,
            text_analysis_id=result_id,
            text_parameter__transcript__scenario_session__screening_session__in=sessions,
        )
        payload = _text_result_payload(result)
        payload["features"] = {
            "text_parameter_id": str(result.text_parameter_id),
            "api_version": result.text_parameter.api_version,
            "sentiment_score": _json_value(result.text_parameter.sentiment_score),
            "emotion_distribution": result.text_parameter.emotion_distribution,
            "keyword_analysis": result.text_parameter.keyword_analysis,
            "linguistic_features": result.text_parameter.linguistic_features,
        }
        return JsonResponse({"success": True, "result": payload})

    if analysis_type in ["fusion", "final"]:
        result = get_object_or_404(
            FusionPrediction,
            prediction_id=result_id,
            screening_session__in=sessions,
        )
        payload = _fusion_result_payload(result)
        return JsonResponse({"success": True, "result": payload})

    return JsonResponse(
        {
            "success": False,
            "message": "Please pass result type: ?type=face, ?type=voice, ?type=text, or ?type=fusion",
        },
        status=400,
    )


# ============================================================
# API: DASHBOARD SUMMARY
# ============================================================

@login_required
def analysis_summary_api(request):
    """Return latest analysis summary for dashboard AJAX."""
    sessions = _get_user_sessions(request.user)

    latest_face = FacialAnalysisResult.objects.filter(
        feature__video_session__screening_session__in=sessions
    ).order_by("-processed_at").first()

    latest_voice = VoiceAnalysisResult.objects.filter(
        feature__audio_extraction__attempt__phonation_session__screening_session__in=sessions
    ).order_by("-processed_at").first()

    latest_text = TextAnalysisResult.objects.filter(
        text_parameter__transcript__scenario_session__screening_session__in=sessions
    ).order_by("-processed_at").first()

    latest_fusion = FusionPrediction.objects.filter(
        screening_session__in=sessions
    ).order_by("-predicted_at").first()

    summary = {}

    if latest_face:
        summary["face"] = _facial_result_payload(latest_face)

    if latest_voice:
        summary["voice"] = _voice_result_payload(latest_voice)

    if latest_text:
        summary["text"] = _text_result_payload(latest_text)

    if latest_fusion:
        summary["fusion"] = _fusion_result_payload(latest_fusion)

    return JsonResponse({
        "success": True,
        "summary": summary,
    })


# ============================================================
# API: MODALITY RESULTS
# ============================================================

@login_required
def modality_results_api(request):
    """Return saved ModalityResult rows for the current user."""
    sessions = _get_user_sessions(request.user)

    modality = request.GET.get("modality", "").strip().lower()

    results = ModalityResult.objects.filter(
        screening_session__in=sessions
    ).order_by("-created_at")

    if modality:
        results = results.filter(modality=modality)

    payload = []
    for result in results:
        payload.append({
            "id": str(result.modality_result_id),
            "screening_session_id": str(result.screening_session_id),
            "modality": result.modality,
            "face_result_id": str(result.face_result_id) if result.face_result_id else None,
            "voice_result_id": str(result.voice_result_id) if result.voice_result_id else None,
            "text_result_id": str(result.text_result_id) if result.text_result_id else None,
            "confidence_score": _json_value(result.confidence_score),
            "result_payload": result.result_payload,
            "created_at": _json_value(result.created_at),
        })

    return JsonResponse({
        "success": True,
        "count": len(payload),
        "results": payload,
    })