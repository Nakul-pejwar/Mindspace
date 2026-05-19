"""
Profile views for the MindSpace single-app project.

Expected location:
    mindspace/views/profiles/views.py

These views use the current models.py structure:
    - UserProfile
    - AuditLog

Your project currently has one Django app:
    mindspace
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

ALLOWED_AVATARS = [
    "avatar_1.png",
    "avatar_2.png",
    "avatar_3.png",
    "avatar_4.png",
    "avatar_5.png",
    "avatar_6.png",
    "avatar_7.png",
    "avatar_8.png",
]


def clean_avatar(value):
    avatar = (value or "avatar_1.png").strip()
    if avatar not in ALLOWED_AVATARS:
        return "avatar_1.png"
    return avatar


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

    if not profile.avatar:
        profile.avatar = "avatar_1.png"
        profile.save(update_fields=["avatar"])

    return profile


def log_profile_action(request, action_name, metadata=None):
    try:
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action_name=action_name,
            entity_name="UserProfile",
            entity_id=None,
            metadata_json=metadata or {},
        )
    except Exception:
        # Never break user flow because audit logging failed.
        pass


def save_profile_from_post(request, profile):
    """
    Shared save logic for profile form/API.
    Works with the current UserProfile fields:
        avatar, first_name, last_name, mobile_number, gender,
        date_of_birth, state, district, address, profile_completed
    """

    profile.avatar = clean_avatar(request.POST.get("avatar", profile.avatar or "avatar_1.png"))
    profile.first_name = request.POST.get("first_name", profile.first_name or "").strip()
    profile.last_name = request.POST.get("last_name", profile.last_name or "").strip()
    profile.mobile_number = request.POST.get("mobile_number", profile.mobile_number or "").strip()
    profile.gender = request.POST.get("gender", profile.gender or "").strip()

    date_of_birth = request.POST.get("date_of_birth", "").strip()
    profile.date_of_birth = date_of_birth or None

    profile.state = request.POST.get("state", profile.state or "").strip()
    profile.district = request.POST.get("district", profile.district or "").strip()
    profile.address = request.POST.get("address", profile.address or "").strip()

    if profile.first_name:
        profile.profile_completed = True

    profile.save()

    request.user.first_name = profile.first_name or ""
    request.user.last_name = profile.last_name or ""
    request.user.save(update_fields=["first_name", "last_name"])

    return profile


def profile_payload(request, profile):
    return {
        "user_id": request.user.id,
        "email": request.user.email,
        "username": request.user.username,
        "public_id": str(profile.public_id),
        "role": profile.role,
        "account_status": profile.account_status,
        "is_email_verified": profile.is_email_verified,
        "avatar": profile.avatar or "avatar_1.png",
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "mobile_number": profile.mobile_number,
        "gender": profile.gender,
        "date_of_birth": profile.date_of_birth.isoformat() if profile.date_of_birth else None,
        "state": profile.state,
        "district": profile.district,
        "address": profile.address,
        "profile_completed": profile.profile_completed,
        "consented": profile.consented,
        "consent_at": profile.consent_at.isoformat() if profile.consent_at else None,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
    }


# ============================================================
# PROFILE PAGE
# ============================================================

@login_required
def profile_view(request):
    """
    Show current user's profile.
    Template:
        templates/accounts/profile.html
    """
    profile = get_or_create_profile(request.user)

    return render(request, "accounts/profile.html", {
        "profile": profile,
    })


# ============================================================
# COMPLETE PROFILE
# ============================================================

@login_required
def complete_profile_view(request):
    """
    Complete profile page.

    This matches your current UserProfile fields:
        avatar, first_name, last_name, mobile_number, gender,
        date_of_birth, state, district, address, profile_completed
    """

    profile = get_or_create_profile(request.user)

    if profile.profile_completed:
        return redirect("user_dashboard")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()

        if not first_name:
            messages.error(request, "First name is required.")
            return redirect("complete_profile")

        save_profile_from_post(request, profile)

        log_profile_action(request, "profile_completed", {
            "ip_address": get_client_ip(request),
            "completed_at": timezone.now().isoformat(),
        })

        messages.success(request, "Profile completed successfully.")
        return redirect("user_dashboard")

    return render(request, "accounts/complete_profile.html", {
        "profile": profile,
        "allowed_avatars": ALLOWED_AVATARS,
    })


# ============================================================
# EDIT PROFILE
# ============================================================

@login_required
def edit_profile_view(request):
    """
    Edit existing profile.
    You can point this to the same template as complete_profile.html,
    or create:
        templates/accounts/edit_profile.html
    """

    profile = get_or_create_profile(request.user)

    if request.method == "POST":
        save_profile_from_post(request, profile)

        log_profile_action(request, "profile_updated", {
            "ip_address": get_client_ip(request),
            "updated_at": timezone.now().isoformat(),
        })

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "accounts/profile.html", {
        "profile": profile,
        "edit_mode": True,
    })


# ============================================================
# PROFILE API
# ============================================================

@login_required
def profile_detail_api(request):
    """
    JSON profile detail for frontend AJAX.
    """

    profile = get_or_create_profile(request.user)

    return JsonResponse({
        "success": True,
        "profile": profile_payload(request, profile),
    })


@login_required
@require_POST
def update_profile_api(request):
    """
    Small JSON/POST API to update profile.
    Works with normal form POST also.
    """

    profile = get_or_create_profile(request.user)
    save_profile_from_post(request, profile)

    log_profile_action(request, "profile_updated_api", {
        "ip_address": get_client_ip(request),
    })

    return JsonResponse({
        "success": True,
        "message": "Profile updated successfully.",
        "profile": profile_payload(request, profile),
    })


# IMPORTANT:
# config/urls.py currently expects profile_update_api.
# Keep this alias so urls.py does not break.
@login_required
@require_POST
def profile_update_api(request):
    return update_profile_api(request)
