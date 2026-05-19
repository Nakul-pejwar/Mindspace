"""
Security views for MindSpace.

These views are compatible with the current single-app project structure:

    mindspace/models.py
    mindspace/views/security/views.py

They use the new PostgreSQL-ready models:
    - SecurityEvent
    - AuditLog

No old imports like apps.security.models or .models are used.
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from mindspace.models import AuditLog, SecurityEvent


# ============================================================
# HELPERS
# ============================================================

def is_admin_user(user):
    """
    Allow Django superusers and users whose profile role is admin.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == "admin")


def get_client_ip(request):
    """
    Get client IP safely.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def create_security_event(
    *,
    request,
    event_type,
    severity="info",
    metadata=None,
):
    """
    Small reusable helper for logging security events.
    """
    return SecurityEvent.objects.create(
        user=request.user if request.user.is_authenticated else None,
        event_type=event_type,
        severity=severity,
        ip_address=get_client_ip(request),
        metadata_json=metadata or {},
    )


def create_audit_log(
    *,
    request,
    action_name,
    entity_name,
    entity_id=None,
    metadata=None,
):
    """
    Small reusable helper for creating audit logs.
    """
    return AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action_name=action_name,
        entity_name=entity_name,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )


# ============================================================
# PAGE VIEWS
# ============================================================

@login_required
@user_passes_test(is_admin_user)
def security_dashboard_view(request):
    """
    Admin-only security dashboard page.
    Create template later:
        templates/security/security_dashboard.html
    """
    recent_events = SecurityEvent.objects.select_related("user").order_by("-created_at")[:20]
    recent_audits = AuditLog.objects.select_related("user").order_by("-created_at")[:20]

    severity_counts = {
        "info": SecurityEvent.objects.filter(severity="info").count(),
        "low": SecurityEvent.objects.filter(severity="low").count(),
        "medium": SecurityEvent.objects.filter(severity="medium").count(),
        "high": SecurityEvent.objects.filter(severity="high").count(),
        "critical": SecurityEvent.objects.filter(severity="critical").count(),
    }

    context = {
        "recent_events": recent_events,
        "recent_audits": recent_audits,
        "severity_counts": severity_counts,
        "total_events": SecurityEvent.objects.count(),
        "total_audit_logs": AuditLog.objects.count(),
    }

    return render(request, "security/security_dashboard.html", context)


# ============================================================
# API VIEWS
# ============================================================

@login_required
@user_passes_test(is_admin_user)
def security_events_api(request):
    """
    Admin-only API: list latest security events.

    Optional query params:
        ?severity=high
        ?event_type=login_failed
    """
    events = SecurityEvent.objects.select_related("user").order_by("-created_at")

    severity = request.GET.get("severity", "").strip()
    event_type = request.GET.get("event_type", "").strip()

    if severity:
        events = events.filter(severity=severity)

    if event_type:
        events = events.filter(event_type=event_type)

    events = events[:100]

    return JsonResponse({
        "success": True,
        "events": [
            {
                "id": str(event.security_event_id),
                "user_id": event.user_id,
                "username": event.user.username if event.user else None,
                "event_type": event.event_type,
                "severity": event.severity,
                "ip_address": event.ip_address,
                "metadata": event.metadata_json or {},
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    })


@login_required
@user_passes_test(is_admin_user)
def audit_logs_api(request):
    """
    Admin-only API: list latest audit logs.

    Optional query params:
        ?action=LOGIN
        ?entity=UserProfile
    """
    logs = AuditLog.objects.select_related("user").order_by("-created_at")

    action = request.GET.get("action", "").strip()
    entity = request.GET.get("entity", "").strip()

    if action:
        logs = logs.filter(action_name__icontains=action)

    if entity:
        logs = logs.filter(entity_name__icontains=entity)

    logs = logs[:100]

    return JsonResponse({
        "success": True,
        "logs": [
            {
                "id": str(log.audit_log_id),
                "user_id": log.user_id,
                "username": log.user.username if log.user else None,
                "action_name": log.action_name,
                "entity_name": log.entity_name,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "metadata": log.metadata_json or {},
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    })


@login_required
def my_security_events_api(request):
    """
    User API: show only the logged-in user's security events.
    Useful for account activity page.
    """
    events = SecurityEvent.objects.filter(
        user=request.user
    ).order_by("-created_at")[:50]

    return JsonResponse({
        "success": True,
        "events": [
            {
                "id": str(event.security_event_id),
                "event_type": event.event_type,
                "severity": event.severity,
                "ip_address": event.ip_address,
                "metadata": event.metadata_json or {},
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ],
    })


@login_required
@require_POST
def log_client_security_event_api(request):
    """
    User/client API for low-risk frontend events.

    Example POST fields:
        event_type=suspicious_browser_activity
        severity=low

    Do not use this for trusted server-side security decisions.
    """
    event_type = request.POST.get("event_type", "client_event").strip()
    severity = request.POST.get("severity", "info").strip()

    allowed_severities = ["info", "low", "medium", "high", "critical"]
    if severity not in allowed_severities:
        severity = "info"

    event = create_security_event(
        request=request,
        event_type=event_type or "client_event",
        severity=severity,
        metadata={
            "source": "frontend",
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        },
    )

    create_audit_log(
        request=request,
        action_name="CLIENT_SECURITY_EVENT_LOGGED",
        entity_name="SecurityEvent",
        entity_id=event.security_event_id,
        metadata={
            "event_type": event.event_type,
            "severity": event.severity,
        },
    )

    return JsonResponse({
        "success": True,
        "message": "Security event logged.",
        "event_id": str(event.security_event_id),
    })