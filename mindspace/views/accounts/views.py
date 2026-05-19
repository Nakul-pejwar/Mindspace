"""
Accounts views for the current MindSpace single-app structure.

Compatible with the new PostgreSQL models.py where:
- models live in mindspace/models.py
- UserProfile uses profile_completed, not is_profile_completed
- AccountStatus values are: pending, active, suspended, deleted
- PendingSignup and Consent models are not present
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from mindspace.models import AuditLog, UserProfile

User = get_user_model()


# ======================================================
# SMALL HELPERS
# ======================================================

def safe_redirect(*route_names, fallback="/"):
    """
    Try multiple route names and return the first valid redirect.
    Useful while your urls.py is still changing.
    """
    for route_name in route_names:
        try:
            reverse(route_name)
            return redirect(route_name)
        except NoReverseMatch:
            continue

    return redirect(fallback)


def get_or_create_profile(user):
    """
    Your new models.py has UserProfile related_name='profile'.
    This helper prevents 'user has no profile' errors.
    """
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


def is_profile_complete(profile):
    """
    New models.py field name: profile_completed.
    Old code used: is_profile_completed.
    """
    return bool(getattr(profile, "profile_completed", False))


def mark_profile_complete(profile):
    profile.profile_completed = True
    profile.save(update_fields=["profile_completed", "updated_at"])


def role_redirect(user):
    """
    Redirect user according to saved role in UserProfile.
    Normal users go to wellness check-in after onboarding.
    """

    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": "user",
            "account_status": "active",
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "avatar": "avatar_1.png",
            "is_email_verified": bool(user.email),
        }
    )

    if not profile.avatar:
        profile.avatar = "avatar_1.png"
        profile.save(update_fields=["avatar"])

    if profile.role == "admin" or user.is_superuser:
        return redirect("/admin/")

    if profile.role == "counselor":
        return redirect("counselor_support")

    return safe_redirect("check_in", fallback="/assessments/check-in/")


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


# ======================================================
# SIGNUP
# ======================================================

def signup_view(request):
    """
    New models.py does not include PendingSignup.
    So this version creates the user directly.

    Development behavior:
    - user signup: active immediately
    - counselor signup: pending until admin changes account_status to active
    - admin creation from public signup is blocked
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        role = request.POST.get("role", "user").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        terms = request.POST.get("terms")

        if role not in ["user", "counselor"]:
            role = "user"

        if not name or not email or not password or not confirm_password:
            messages.error(request, "All fields are required.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        if not terms:
            messages.error(request, "Please accept terms and policy.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        if User.objects.filter(email=email).exists() or User.objects.filter(username=email).exists():
            messages.error(request, "This email is already registered.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        first_name = name.split(" ", 1)[0]
        last_name = name.split(" ", 1)[1] if " " in name else ""

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                )

                UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "role": role,
                        "account_status": "pending" if role == "counselor" else "active",
                        "is_email_verified": True,
                        "first_name": first_name,
                        "last_name": last_name,
                        "profile_completed": False,
                        "consented": False,
                    },
                )

                AuditLog.objects.create(
                    user=user,
                    action_name="account_signup",
                    entity_name="UserProfile",
                    metadata_json={
                        "role": role,
                        "email": email,
                        "ip_address": get_client_ip(request),
                    },
                )

        except IntegrityError:
            messages.error(request, "Could not create account. Please try again.")
            return safe_redirect("accounts:signup", "signup", fallback="/accounts/signup/")

        if role == "counselor":
            messages.success(
                request,
                "Counselor account created. Please wait for admin approval before login.",
            )
        else:
            messages.success(request, "Account created successfully. Please login.")

        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    return render(request, "accounts/signup.html")


# ======================================================
# VERIFY EMAIL SIGNUP
# ======================================================

def verify_signup_view(request, token=None):
    """
    Kept only so old urls.py does not break.
    Your new models.py has no PendingSignup/token table.
    """
    messages.info(
        request,
        "Email verification is not enabled in the current database model. Please login directly.",
    )
    return safe_redirect("accounts:login", "login", fallback="/accounts/login/")


def verify_success_view(request):
    return render(request, "accounts/verify-success.html")


# ======================================================
# LOGIN
# ======================================================

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        user = authenticate(request, username=email, password=password)

        if user is None:
            messages.error(request, "Invalid email or password.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        profile = get_or_create_profile(user)

        if profile.account_status == "pending":
            messages.error(request, "Your account is pending admin approval.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        if profile.account_status == "suspended":
            messages.error(request, "Your account has been suspended.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        if profile.account_status == "deleted":
            messages.error(request, "This account has been deleted.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        if profile.account_status != "active":
            messages.error(request, "Your account is not active.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        login(request, user)

        if not profile.consented:
            return safe_redirect("consent", fallback="/accounts/consent/")

        if not is_profile_complete(profile):
            return safe_redirect("complete_profile", fallback="/accounts/complete-profile/")

        return role_redirect(user)

    return render(request, "accounts/login.html")


# ======================================================
# GOOGLE LOGIN/SIGNUP REDIRECT
# ======================================================

@login_required
def google_login_redirect_view(request):
    """
    After successful Google login/signup:
    - create UserProfile if missing
    - force unknown roles to user
    - continue flow: consent -> complete profile -> dashboard
    """
    user = request.user

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "role": "user",
            "account_status": "active",
            "is_email_verified": True,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "profile_completed": False,
            "consented": False,
        },
    )

    changed_fields = []

    if profile.role not in ["user", "counselor", "admin", "researcher"]:
        profile.role = "user"
        changed_fields.append("role")

    if not profile.account_status:
        profile.account_status = "active"
        changed_fields.append("account_status")

    if not profile.first_name and user.first_name:
        profile.first_name = user.first_name
        changed_fields.append("first_name")

    if not profile.last_name and user.last_name:
        profile.last_name = user.last_name
        changed_fields.append("last_name")

    if not profile.is_email_verified:
        profile.is_email_verified = True
        changed_fields.append("is_email_verified")

    if changed_fields:
        changed_fields.append("updated_at")
        profile.save(update_fields=changed_fields)

    if profile.account_status == "pending":
        messages.error(request, "Your account is pending admin approval.")
        logout(request)
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    if profile.account_status == "suspended":
        messages.error(request, "Your account has been suspended.")
        logout(request)
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    if profile.account_status == "deleted":
        messages.error(request, "This account has been deleted.")
        logout(request)
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    if profile.account_status != "active":
        messages.error(request, "Your account is not active.")
        logout(request)
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    if not profile.consented:
        return safe_redirect("consent", fallback="/accounts/consent/")

    if not is_profile_complete(profile):
        return safe_redirect("complete_profile", fallback="/accounts/complete-profile/")

    return role_redirect(user)


# ======================================================
# COMPLETE PROFILE
# ======================================================

@login_required
def complete_profile_view(request):
    profile = get_or_create_profile(request.user)

    if not profile.consented:
        messages.info(request, "Please accept consent before completing your profile.")
        return safe_redirect("consent", fallback="/accounts/consent/")

    if is_profile_complete(profile):
        return role_redirect(request.user)

    allowed_avatars = [
        "avatar_1.png",
        "avatar_2.png",
        "avatar_3.png",
        "avatar_4.png",
        "avatar_5.png",
        "avatar_6.png",
        "avatar_7.png",
        "avatar_8.png",
    ]

    if request.method == "POST":
        profile.first_name = request.POST.get("first_name", "").strip()
        profile.last_name = request.POST.get("last_name", "").strip()
        profile.mobile_number = request.POST.get("mobile_number", "").strip()
        profile.address = request.POST.get("address", "").strip()
        profile.state = request.POST.get("state", "").strip()
        profile.district = request.POST.get("district", "").strip()
        profile.gender = request.POST.get("gender", "").strip()

        date_of_birth = request.POST.get("date_of_birth")
        profile.date_of_birth = date_of_birth if date_of_birth else None


        avatar = request.POST.get("avatar", "avatar_1.png")

        if avatar not in allowed_avatars:
            avatar = "avatar_1.png"

        profile.avatar = avatar

        profile.profile_completed = True
        profile.save()

        request.user.first_name = profile.first_name
        request.user.last_name = profile.last_name
        request.user.save(update_fields=["first_name", "last_name"])

        AuditLog.objects.create(
            user=request.user,
            action_name="profile_completed",
            entity_name="UserProfile",
            metadata_json={"ip_address": get_client_ip(request)},
        )

        return safe_redirect("check_in", fallback="/assessments/check-in/")

    return render(
        request,
        "accounts/complete_profile.html",
        {
            "profile": profile,
            "avatars": allowed_avatars,
        },
    )


# ======================================================
# PROFILE PAGE
# ======================================================

@login_required
def profile_view(request):
    profile = get_or_create_profile(request.user)

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
        },
    )


# ======================================================
# FORGOT PASSWORD
# ======================================================

def forgot_password_view(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)

        if form.is_valid():
            form.save(
                request=request,
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name="accounts/password-reset-email.html",
                subject_template_name="accounts/password-reset-subject.txt",
            )

            messages.success(request, "Password reset link sent.")
            return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

        messages.error(request, "Please enter a valid email address.")

    return render(request, "accounts/forgot-password.html")


# ======================================================
# LOGOUT
# ======================================================

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    return safe_redirect("accounts:login", "login", fallback="/accounts/login/")


# ======================================================
# DELETE ACCOUNT
# ======================================================

@login_required
def delete_account_view(request):
    user = request.user

    if request.method == "POST":
        confirm = request.POST.get("confirm_delete")

        if confirm != "DELETE":
            messages.error(request, "Please type DELETE to confirm account deletion.")
            return safe_redirect(
                "accounts:delete_account",
                "delete_account",
                fallback="/accounts/delete-account/",
            )

        profile = get_or_create_profile(user)
        profile.account_status = "deleted"
        profile.deleted_at = timezone.now()
        profile.save(update_fields=["account_status", "deleted_at", "updated_at"])

        AuditLog.objects.create(
            user=user,
            action_name="account_deleted",
            entity_name="UserProfile",
            metadata_json={"ip_address": get_client_ip(request)},
        )

        logout(request)

        # Soft-delete profile status first, then deactivate user.
        user.is_active = False
        user.save(update_fields=["is_active"])

        messages.success(request, "Your account has been deleted.")
        return safe_redirect("accounts:login", "login", fallback="/accounts/login/")

    return render(request, "accounts/delete_account.html")