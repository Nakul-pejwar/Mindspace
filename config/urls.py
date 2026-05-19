from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView


from mindspace.views.pages import views as pages_views
from mindspace.views.accounts import views as account_views
from mindspace.views.dashboard import views as dashboard_views
from mindspace.views.assessments import views as assessment_views
from mindspace.views.consent import views as consent_views
from mindspace.views.profiles import views as profile_views
from mindspace.views.security import views as security_views
from mindspace.views.governance import views as governance_views
from mindspace.views.analysis import views as analysis_views


urlpatterns = [
    # ============================================================
    # ADMIN
    # ============================================================
    path("admin/", admin.site.urls),

    # Serve favicon.ico from static files
    path(
        "favicon.ico",
        RedirectView.as_view(url=settings.STATIC_URL + "favicon.ico", permanent=True),
    ),

    # ============================================================
    # PAGES
    # ============================================================
    path("", pages_views.landing_page, name="landing"),
    path("support/", pages_views.support_page, name="support"),
    path("contact/", pages_views.contact_page, name="contact"),
    path("learn-more/", pages_views.learn_more_page, name="learn_more"),

    # ============================================================
    # ACCOUNTS
    # ============================================================
    path("accounts/signup/", account_views.signup_view, name="signup"),
    path("accounts/login/", account_views.login_view, name="login"),
    path("accounts/logout/", account_views.logout_view, name="logout"),

    path(
        "accounts/google/redirect/",
        account_views.google_login_redirect_view,
        name="google_login_redirect",
    ),

    path(
        "accounts/complete-profile/",
        account_views.complete_profile_view,
        name="complete_profile",
    ),
    path("accounts/profile/", account_views.profile_view, name="profile"),
    path(
        "accounts/forgot-password/",
        account_views.forgot_password_view,
        name="forgot_password",
    ),
    path(
        "accounts/delete-account/",
        account_views.delete_account_view,
        name="delete_account",
    ),
    path(
        "accounts/verify-success/",
        account_views.verify_success_view,
        name="verify_success",
    ),

    # ============================================================
    # CONSENT
    # ============================================================
    path("accounts/consent/", consent_views.consent_view, name="consent"),
    path("consent/status/", consent_views.consent_status_api, name="consent_status_api"),
    path("consent/submit/", consent_views.submit_consent_api, name="submit_consent_api"),
    path("consent/withdraw/", consent_views.withdraw_consent_api, name="withdraw_consent_api"),

    # Allauth URLs after custom URLs
    path("accounts/", include("allauth.urls")),
    
    # ============================================================
    # DASHBOARD
    # ============================================================
    path("dashboard/", dashboard_views.user_dashboard_view, name="user_dashboard"),
    path("dashboard/badges/", dashboard_views.badges_view, name="badges"),
    path(
        "dashboard/under-maintenance/",
        dashboard_views.under_maintenance_view,
        name="under_maintenance",
    ),
    path(
        "dashboard/notifications/read/",
        dashboard_views.mark_notifications_read,
        name="mark_notifications_read",
    ),

    # Counselor support page
    path(
        "counselor/support/",
        dashboard_views.counselor_support_view,
        name="counselor_support",
    ),

    # ============================================================
    # ASSESSMENTS PAGE ROUTES
    # ============================================================
    path("assessments/check-in/", assessment_views.check_in_view, name="check_in"),
    path(
        "assessments/activity-session/",
        assessment_views.activity_session_view,
        name="activity_session",
    ),
    path(
        "assessments/voice-phonation/",
        assessment_views.voice_phonation_view,
        name="voice_phonation",
    ),
    path(
        "assessments/scenario-voice-response/",
        assessment_views.scenario_voice_response_view,
        name="scenario_voice_response",
    ),
    path(
        "assessments/activity-complete/",
        assessment_views.activity_complete_view,
        name="activity_complete",
    ),

    # ============================================================
    # ASSESSMENTS API ROUTES
    # ============================================================
    path(
        "assessments/multimodal/start/",
        assessment_views.start_multimodal_session,
        name="start_multimodal_session",
    ),
    path(
        "assessments/multimodal/status/",
        assessment_views.multimodal_session_status,
        name="multimodal_session_status",
    ),
    path(
        "assessments/upload-face-video/",
        assessment_views.upload_face_video,
        name="upload_face_video",
    ),
    path(
        "assessments/upload-voice-phonation/",
        assessment_views.upload_voice_phonation,
        name="upload_voice_phonation",
    ),
    path(
        "assessments/upload-scenario-voice-response/",
        assessment_views.upload_scenario_voice_response,
        name="upload_scenario_voice_response",
    ),
    path(
        "assessments/run-multimodal-fusion/",
        assessment_views.run_multimodal_fusion,
        name="run_multimodal_fusion",
    ),

    # ============================================================
    # ANALYSIS APIs
    # ============================================================
    path(
        "analysis/results/",
        analysis_views.analysis_results_view,
        name="analysis_results",
    ),
    path(
        "analysis/results/<uuid:result_id>/",
        analysis_views.analysis_result_detail,
        name="analysis_result_detail",
    ),
    path(
        "analysis/summary/",
        analysis_views.analysis_summary_api,
        name="analysis_summary_api",
    ),
    path(
        "analysis/modality-results/",
        analysis_views.modality_results_api,
        name="modality_results_api",
    ),

    # ============================================================
    # PROFILE APIs
    # ============================================================
    path(
        "profiles/me/",
        profile_views.profile_detail_api,
        name="profile_detail_api",
    ),
    path(
        "profiles/update/",
        profile_views.profile_update_api,
        name="profile_update_api",
    ),

    # ============================================================
    # SECURITY APIs
    # ============================================================
    path(
        "security/",
        security_views.security_dashboard_view,
        name="security_dashboard",
    ),
    path(
        "security/events/",
        security_views.security_events_api,
        name="security_events_api",
    ),
    path(
        "security/audit-logs/",
        security_views.audit_logs_api,
        name="audit_logs_api",
    ),
    path(
        "security/my-events/",
        security_views.my_security_events_api,
        name="my_security_events_api",
    ),
    path(
        "security/log-client-event/",
        security_views.log_client_security_event_api,
        name="log_client_security_event_api",
    ),

    # ============================================================
    # GOVERNANCE APIs
    # ============================================================
    path(
        "governance/",
        governance_views.governance_home_view,
        name="governance_home",
    ),
    path(
        "governance/user-data-summary/",
        governance_views.user_data_summary_api,
        name="user_data_summary_api",
    ),
    path(
        "governance/consent-status/",
        governance_views.consent_status_api,
        name="governance_consent_status_api",
    ),
    path(
        "governance/data-retention-request/",
        governance_views.data_retention_request_api,
        name="data_retention_request_api",
    ),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)