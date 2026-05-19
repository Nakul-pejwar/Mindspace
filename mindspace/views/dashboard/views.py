from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from mindspace.models import (
    AuditLog,
    FusionPrediction,
    ModalityResult,
    PlatformScreeningSession,
    SecurityEvent,
    UserProfile
)


# ============================================================
# SMALL ROLE HELPER
# ============================================================

def role_required(*allowed_roles):
    """
    Lightweight replacement for old apps.accounts.decorators.role_required.
    Your current project is a single app named mindspace, so importing
    from apps.accounts.decorators will fail.
    """
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            profile = getattr(request.user, "profile", None)
            role = getattr(profile, "role", "user")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if role not in allowed_roles:
                return HttpResponseForbidden("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================
# PAGE VIEWS
# ============================================================

def landing_page(request):
    return render(request, "pages/landing.html")


def contact_page(request):
    return render(request, "pages/contact.html")


def support_page(request):
    return render(request, "pages/support.html")


def learn_more_page(request):
    return render(request, "pages/learn_more.html")


def under_maintenance_view(request):
    return render(request, "dashboard/under_maintenance.html")


# ============================================================
# DASHBOARD HELPERS
# ============================================================

def get_user_analysis_summary(user):
    """
    New-model replacement for old apps.analysis.services.get_user_analysis_summary.

    Reads latest fusion prediction and latest modality results from:
    - FusionPrediction
    - ModalityResult
    """
    latest_fusion = (
        FusionPrediction.objects
        .filter(screening_session__user=user)
        .order_by("-predicted_at")
        .first()
    )

    latest_modality_results = (
        ModalityResult.objects
        .filter(screening_session__user=user)
        .order_by("modality", "-created_at")
    )

    summary = {
        "face": None,
        "voice": None,
        "text": None,
        "fusion": None,
    }

    seen_modalities = set()
    for result in latest_modality_results:
        if result.modality in seen_modalities:
            continue

        seen_modalities.add(result.modality)
        summary[result.modality] = {
            "dominant_risk": None,
            "risk_probability": float(result.confidence_score) if result.confidence_score is not None else None,
            "scores": result.result_payload or {},
            "created_at": result.created_at,
        }

    if latest_fusion:
        summary["fusion"] = {
            "dominant_risk": latest_fusion.overall_risk,
            "risk_probability": float(latest_fusion.confidence_score) if latest_fusion.confidence_score is not None else None,
            "scores": {
                "anxiety": float(latest_fusion.anxiety_score) if latest_fusion.anxiety_score is not None else None,
                "depression": float(latest_fusion.depression_score) if latest_fusion.depression_score is not None else None,
                "stress": float(latest_fusion.stress_score) if latest_fusion.stress_score is not None else None,
                "bipolar": float(latest_fusion.bipolar_score) if latest_fusion.bipolar_score is not None else None,
                "suicidal": float(latest_fusion.suicidal_score) if latest_fusion.suicidal_score is not None else None,
            },
            "created_at": latest_fusion.predicted_at,
            "raw": latest_fusion.final_prediction_json or {},
        }

    return summary


def get_activity_progress(user):
    """
    Calculate activity progress from latest PlatformScreeningSession.
    Total flow: face + voice + text = 3 activities.
    """
    latest_session = (
        PlatformScreeningSession.objects
        .filter(user=user)
        .order_by("-started_at")
        .first()
    )

    activities_total = 3
    activities_completed = 0

    if latest_session:
        activities_completed = latest_session.completed_activities_count or 0
        activities_completed = min(activities_completed, activities_total)

    activity_percent = int((activities_completed / activities_total) * 100) if activities_total else 0

    return latest_session, activities_completed, activities_total, activity_percent


def get_dashboard_notifications(user):
    """
    New schema does not have Notification model.
    So we build dashboard notifications from latest sessions, audit logs,
    and security events. This avoids migration/import errors while still
    showing useful dashboard messages.
    """
    notifications = []

    latest_session = (
        PlatformScreeningSession.objects
        .filter(user=user)
        .order_by("-started_at")
        .first()
    )

    if latest_session:
        if latest_session.session_status == "completed":
            notifications.append(SimpleNamespace(
                title="Assessment completed",
                message="Your latest wellness screening has been completed.",
                is_read=True,
                created_at=latest_session.completed_at or latest_session.started_at,
            ))
        elif latest_session.session_status in ["started", "processing"]:
            notifications.append(SimpleNamespace(
                title="Assessment in progress",
                message="Continue your pending MindSpace activity session.",
                is_read=False,
                created_at=latest_session.started_at,
            ))
        elif latest_session.session_status == "failed":
            notifications.append(SimpleNamespace(
                title="Assessment needs attention",
                message="Your last activity could not be processed. Please try again.",
                is_read=False,
                created_at=latest_session.started_at,
            ))

    security_events = (
        SecurityEvent.objects
        .filter(user=user)
        .order_by("-created_at")[:2]
    )

    for event in security_events:
        notifications.append(SimpleNamespace(
            title=f"Security: {event.event_type}",
            message=f"Severity: {event.severity}",
            is_read=True,
            created_at=event.created_at,
        ))

    audit_logs = (
        AuditLog.objects
        .filter(user=user)
        .order_by("-created_at")[:2]
    )

    for log in audit_logs:
        notifications.append(SimpleNamespace(
            title=log.action_name,
            message=f"{log.entity_name} activity recorded.",
            is_read=True,
            created_at=log.created_at,
        ))

    if not notifications:
        notifications.append(SimpleNamespace(
            title="Welcome to MindSpace",
            message="Start your first check-in to see your wellness progress here.",
            is_read=False,
            created_at=None,
        ))

    notifications = sorted(
        notifications,
        key=lambda item: item.created_at or 0,
        reverse=True,
    )

    return notifications[:5]


def build_weekly_scores(user):
    """
    Lightweight placeholder using latest fusion score when available.
    Keeps your dashboard template stable.
    """
    latest_fusion = (
        FusionPrediction.objects
        .filter(screening_session__user=user)
        .order_by("-predicted_at")
        .first()
    )

    if latest_fusion and latest_fusion.confidence_score is not None:
        base = int(float(latest_fusion.confidence_score) * 100)
        base = max(0, min(base, 100))
        return [max(0, min(100, base + diff)) for diff in [-8, -5, -2, 0, 3, 5, 7]]

    return [65, 72, 80, 75, 85, 78, 82]


# ============================================================
# DASHBOARD VIEWS
# ============================================================

@login_required
def user_dashboard_view(request):
    analysis_summary = get_user_analysis_summary(request.user)

    latest_session, activities_completed, activities_total, activity_percent = get_activity_progress(request.user)

    notifications = get_dashboard_notifications(request.user)
    unread_notifications_count = sum(1 for n in notifications if not getattr(n, "is_read", True))

    context = {
        "analysis_summary": analysis_summary,
        "latest_session": latest_session,

        "activities_completed": activities_completed,
        "activities_total": activities_total,
        "activity_percent": activity_percent,

        "notifications": notifications,
        "unread_notifications_count": unread_notifications_count,

        "weekly_scores": build_weekly_scores(request.user),

        "daily_tip": (
            "Take 5 slow breaths before your next activity. "
            "Small calm actions make the session easier to complete."
        ),
    }

    return render(request, "dashboard/user_dashboard.html", context)


@login_required
@role_required("counselor", "admin", "researcher")
def counselor_dashboard_view(request):
    analysis_summary = get_user_analysis_summary(request.user)

    context = {
        "analysis_summary": analysis_summary,
    }

    return render(request, "dashboard/counselor_dashboard.html", context)

@login_required
def counselor_support_view(request):
    return render(request, "counselor/counselor_support.html")


@login_required
@require_POST
def mark_notifications_read(request):
    """
    The new models.py has no Notification table.
    This endpoint remains so existing frontend JS does not break.
    """
    return JsonResponse({
        "success": True,
        "message": "Notification table is not enabled in the new schema. UI acknowledged.",
    })


@login_required
def badges_view(request):
    latest_session, activities_completed, activities_total, activity_percent = get_activity_progress(request.user)

    completed_sessions = PlatformScreeningSession.objects.filter(
        user=request.user,
        session_status="completed",
    ).count()

    earned_badges_count = 0
    if activities_completed >= 1:
        earned_badges_count += 1
    if activities_completed >= 3:
        earned_badges_count += 1
    if completed_sessions >= 3:
        earned_badges_count += 1

    total_badges = 6
    locked_badges_count = max(total_badges - earned_badges_count, 0)

    context = {
        "earned_badges_count": earned_badges_count,
        "locked_badges_count": locked_badges_count,
        "current_streak": completed_sessions,
        "seven_day_streak_percent": min(completed_sessions * 14, 100),
        "voice_badge_percent": activity_percent if activities_completed >= 2 else 0,
        "weekly_consistency_percent": min(completed_sessions * 20, 100),
        "reflection_badge_percent": activity_percent,
        "latest_session": latest_session,
    }

    return render(request, "dashboard/badges.html", context)