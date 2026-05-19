"""
Governance views for MindSpace.

This file is compatible with the current single-app structure:

    mindspace/
        models.py
        views/governance/views.py

It does not import from apps.* or local .models because your models live in:

    mindspace.models
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from mindspace.models import AuditLog, PlatformScreeningSession, UserProfile


# ============================================================
# GOVERNANCE HOME / SETTINGS PAGE
# ============================================================

@login_required
def governance_home_view(request):
    """
    Simple governance page.

    Shows account/data governance information:
    - profile status
    - consent status
    - screening session count
    - last activity timestamp

    Template:
        templates/dashboard/under_maintenance.html

    You can later create:
        templates/governance/governance_home.html
    """

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    total_sessions = PlatformScreeningSession.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).count()

    latest_session = PlatformScreeningSession.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).order_by("-started_at").first()

    context = {
        "profile": profile,
        "total_sessions": total_sessions,
        "latest_session": latest_session,
        "page_title": "Data Governance",
        "message": (
            "This section will manage consent history, data retention, "
            "download requests, and account safety settings."
        ),
    }

    return render(request, "dashboard/under_maintenance.html", context)


# ============================================================
# USER DATA SUMMARY API
# ============================================================

@login_required
def user_data_summary_api(request):
    """
    Returns a small data summary for the logged-in user.

    Useful for dashboard/governance AJAX.
    """

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    sessions = PlatformScreeningSession.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    )

    completed_sessions = sessions.filter(
        session_status="completed",
    ).count()

    latest_session = sessions.order_by("-started_at").first()

    return JsonResponse({
        "success": True,
        "user": {
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username,
        },
        "profile": {
            "role": profile.role,
            "account_status": profile.account_status,
            "profile_completed": profile.profile_completed,
            "consented": profile.consented,
            "consent_at": profile.consent_at.isoformat() if profile.consent_at else None,
        },
        "screening": {
            "total_sessions": sessions.count(),
            "completed_sessions": completed_sessions,
            "latest_session_id": (
                str(latest_session.screening_session_id)
                if latest_session else None
            ),
            "latest_session_status": (
                latest_session.session_status
                if latest_session else None
            ),
        },
    })


# ============================================================
# CONSENT STATUS API
# ============================================================

@login_required
def consent_status_api(request):
    """
    Returns current consent status from UserProfile.

    Your new models.py does not have a separate Consent model,
    so consent is stored on UserProfile:
        consented
        consent_at
    """

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return JsonResponse({
        "success": True,
        "consented": profile.consented,
        "consent_at": profile.consent_at.isoformat() if profile.consent_at else None,
    })


# ============================================================
# DATA RETENTION REQUEST PLACEHOLDER
# ============================================================

@login_required
def data_retention_request_api(request):
    """
    Placeholder endpoint for future data retention/deletion request workflow.

    For now, this only writes an AuditLog record.
    Later you can add:
    - export my data
    - delete old media
    - anonymize completed sessions
    - soft-delete account data
    """

    if request.method != "POST":
        return JsonResponse({
            "success": False,
            "error": "POST request required.",
        }, status=405)

    request_type = request.POST.get("request_type", "retention_request").strip()

    AuditLog.objects.create(
        user=request.user,
        action_name="governance_request_created",
        entity_name="governance",
        metadata_json={
            "request_type": request_type,
            "created_at": timezone.now().isoformat(),
        },
    )

    return JsonResponse({
        "success": True,
        "message": "Governance request recorded.",
        "request_type": request_type,
    })