"""
Consent views for the MindSpace single-app project.

Expected location:
    mindspace/views/consent/views.py

The new models.py does not currently include a separate Consent model.
So consent is stored safely inside UserProfile:
    - consented
    - consent_at

An AuditLog entry is also created for tracking.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from mindspace.models import AuditLog, UserProfile


# ============================================================
# HELPERS
# ============================================================

def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": "user",
            "account_status": "active",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "is_email_verified": bool(user.email),
            "avatar": "avatar_1.png",
        },
    )
    return profile


def log_consent_action(request, action_name, metadata=None):
    try:
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_name=action_name,
            entity_name="Consent",
            entity_id=None,
            metadata_json=metadata or {},
        )
    except Exception:
        # Do not break consent flow if audit log fails.
        pass


# ============================================================
# CONSENT PAGE
# ============================================================

@login_required
def consent_view(request):
    """
    Consent page.

    Template:
        templates/accounts/consent.html

    Required checkbox names expected from your template:
        understand_screening
        understand_rights
        consent_text
        consent_voice
        consent_face

    Required text fields:
        full_name
        signature
    """

    profile = get_or_create_profile(request.user)

    if profile.consented:
        if not profile.profile_completed:
            return redirect("complete_profile")
        return redirect("check_in")

    if request.method == "POST":
        required_fields = [
            "understand_screening",
            "understand_rights",
            "consent_text",
            "consent_voice",
            "consent_face",
        ]

        missing_required = [
            field for field in required_fields
            if request.POST.get(field) != "on"
        ]

        full_name = request.POST.get("full_name", "").strip()
        signature = request.POST.get("signature", "").strip()

        if missing_required:
            messages.error(
                request,
                "Please accept all required consent confirmations before continuing."
            )
            return redirect("consent")

        if not full_name or not signature:
            messages.error(
                request,
                "Please enter your full name and digital signature."
            )
            return redirect("consent")

        if full_name.lower() != signature.lower():
            messages.error(
                request,
                "Digital signature must match your full name."
            )
            return redirect("consent")

        profile.consented = True
        profile.consent_at = timezone.now()
        profile.save(update_fields=["consented", "consent_at", "updated_at"])

        log_consent_action(request, "consent_given", {
            "consent_version": "v1.0",
            "full_name": full_name,
            "ip_address": get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "accepted_fields": required_fields,
            "consent_at": profile.consent_at.isoformat(),
        })

        messages.success(request, "Consent submitted successfully. Please complete your profile.")
        if not profile.profile_completed:
            return redirect("complete_profile")
        return redirect("check_in")

    return render(request, "accounts/consent.html", {
        "profile": profile,
    })


# ============================================================
# CONSENT STATUS API
# ============================================================

@login_required
def consent_status_api(request):
    """
    JSON API to check user's consent status.
    """

    profile = get_or_create_profile(request.user)

    return JsonResponse({
        "success": True,
        "consent": {
            "user_id": request.user.id,
            "consented": profile.consented,
            "consent_at": profile.consent_at.isoformat() if profile.consent_at else None,
            "profile_completed": profile.profile_completed,
            "next_url": "/accounts/complete-profile/" if not profile.profile_completed else "/assessments/check-in/",
        },
    })


# ============================================================
# CONSENT SUBMIT API
# ============================================================

@login_required
@require_POST
def submit_consent_api(request):
    """
    AJAX/API version of consent submit.
    """

    profile = get_or_create_profile(request.user)

    if profile.consented:
        return JsonResponse({
            "success": True,
            "message": "Consent already submitted.",
            "consented": True,
            "next_url": "/accounts/complete-profile/" if not profile.profile_completed else "/assessments/check-in/",
        })

    required_fields = [
        "understand_screening",
        "understand_rights",
        "consent_text",
        "consent_voice",
        "consent_face",
    ]

    missing_required = [
        field for field in required_fields
        if request.POST.get(field) != "on"
    ]

    full_name = request.POST.get("full_name", "").strip()
    signature = request.POST.get("signature", "").strip()

    if missing_required:
        return JsonResponse({
            "success": False,
            "error": "Please accept all required consent confirmations.",
            "missing_fields": missing_required,
        }, status=400)

    if not full_name or not signature:
        return JsonResponse({
            "success": False,
            "error": "Full name and digital signature are required.",
        }, status=400)

    if full_name.lower() != signature.lower():
        return JsonResponse({
            "success": False,
            "error": "Digital signature must match your full name.",
        }, status=400)

    profile.consented = True
    profile.consent_at = timezone.now()
    profile.save(update_fields=["consented", "consent_at", "updated_at"])

    log_consent_action(request, "consent_given_api", {
        "consent_version": "v1.0",
        "full_name": full_name,
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        "accepted_fields": required_fields,
        "consent_at": profile.consent_at.isoformat(),
        "next_url": "/accounts/complete-profile/" if not profile.profile_completed else "/assessments/check-in/",
    })

    return JsonResponse({
        "success": True,
        "message": "Consent submitted successfully.",
        "consented": True,
        "consent_at": profile.consent_at.isoformat(),
    })


# ============================================================
# WITHDRAW CONSENT
# ============================================================

@login_required
@require_POST
def withdraw_consent_api(request):
    """
    Allows user to withdraw consent.

    Important:
    This does not delete their uploaded activity data automatically.
    It only marks consent as withdrawn.
    You can connect this later with governance/data retention logic.
    """

    profile = get_or_create_profile(request.user)

    profile.consented = False
    profile.consent_at = None
    profile.save(update_fields=["consented", "consent_at", "updated_at"])

    log_consent_action(request, "consent_withdrawn", {
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        "withdrawn_at": timezone.now().isoformat(),
    })

    return JsonResponse({
        "success": True,
        "message": "Consent withdrawn successfully.",
        "consented": False,
    })