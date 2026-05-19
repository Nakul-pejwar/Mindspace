from django.contrib import admin

from .models import (
    UserProfile,
    PlatformScreeningSession,
    MediaAsset,
    VideoActivity,
    VideoSession,
    FaceFeatureVector,
    FacialAnalysisResult,
    PhonationSound,
    PhonationSession,
    PhonationAttempt,
    AudioExtractionResult,
    PhonationFeature,
    VoiceAnalysisResult,
    AudioScenario,
    ScenarioSession,
    Transcript,
    TextParameterResult,
    TextAnalysisResult,
    PcaPipelineResult,
    FusionPrediction,
    AiApiRegistry,
    ApiExecutionLog,
    ModalityResult,
    AuditLog,
    SecurityEvent,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "account_status", "profile_completed", "consented", "created_at")
    list_filter = ("role", "account_status", "profile_completed", "consented")
    search_fields = ("user__username", "user__email", "first_name", "last_name", "mobile_number")


@admin.register(PlatformScreeningSession)
class PlatformScreeningSessionAdmin(admin.ModelAdmin):
    list_display = ("screening_session_id", "user", "session_status", "workflow_stage", "overall_risk", "started_at")
    list_filter = ("session_status", "overall_risk")
    search_fields = ("user__username", "user__email")


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("media_id", "user", "media_type", "file_name", "upload_status", "storage_provider", "created_at")
    list_filter = ("media_type", "upload_status", "storage_provider")
    search_fields = ("user__username", "file_name", "object_key")


admin.site.register(VideoActivity)
admin.site.register(VideoSession)
admin.site.register(FaceFeatureVector)
admin.site.register(FacialAnalysisResult)

admin.site.register(PhonationSound)
admin.site.register(PhonationSession)
admin.site.register(PhonationAttempt)
admin.site.register(AudioExtractionResult)
admin.site.register(PhonationFeature)
admin.site.register(VoiceAnalysisResult)

admin.site.register(AudioScenario)
admin.site.register(ScenarioSession)
admin.site.register(Transcript)
admin.site.register(TextParameterResult)
admin.site.register(TextAnalysisResult)

admin.site.register(PcaPipelineResult)
admin.site.register(FusionPrediction)
admin.site.register(AiApiRegistry)
admin.site.register(ApiExecutionLog)
admin.site.register(ModalityResult)

admin.site.register(AuditLog)
admin.site.register(SecurityEvent)