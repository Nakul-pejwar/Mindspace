"""
MindSpace Django models generated from mindspace_django_schema.sql.

Important setup:
1. Do NOT create Django auth tables manually in models.py.
   Django creates auth_user, auth_group, django_session, django_content_type,
   and django_migrations automatically.

2. These models use Django's built-in user model through settings.AUTH_USER_MODEL.

3. Because the SQL schema uses PostgreSQL VECTOR fields, install pgvector:
      pip install pgvector
   and add this migration operation before using VectorField:
      VectorExtension()

4. If you already created the database tables manually using SQL, keep
   managed = False in Meta. If you want Django migrations to create/manage
   these tables, change MANAGED_BY_DJANGO to True below.
"""

import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from pgvector.django import VectorField


# Set this to False if tables already exist from raw SQL/imported schema.
# Set this to True if you want Django migrations to create these tables.
MANAGED_BY_DJANGO = True


class UserRole(models.TextChoices):
    USER = "user", "User"
    ADMIN = "admin", "Admin"
    COUNSELOR = "counselor", "Counselor"
    RESEARCHER = "researcher", "Researcher"


class AccountStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    DELETED = "deleted", "Deleted"


class SessionStatus(models.TextChoices):
    STARTED = "started", "Started"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MODERATE = "moderate", "Moderate"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class Modality(models.TextChoices):
    FACE = "face", "Face"
    VOICE = "voice", "Voice"
    TEXT = "text", "Text"


class MediaType(models.TextChoices):
    ACTIVITY_VIDEO = "activity_video", "Activity Video"
    PHONATION_AUDIO = "phonation_audio", "Phonation Audio"
    SCENARIO_AUDIO = "scenario_audio", "Scenario Audio"
    IMAGE = "image", "Image"


class UploadStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    UPLOADING = "uploading", "Uploading"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    DELETED = "deleted", "Deleted"


class ProcessingStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    """
    Custom profile table connected to Django's built-in auth user.
    This replaces the custom SQL users table.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="profile",
        db_column="user_id",
    )
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)
    account_status = models.CharField(
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING,
    )
    is_email_verified = models.BooleanField(default=False)

    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)

    avatar = models.CharField(
        max_length=100,
        default="avatar_1.png",
        blank=True,
        null=True,
    )
    
    mobile_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    profile_completed = models.BooleanField(default=False)
    consented = models.BooleanField(default=False)
    consent_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "user_profiles"
        indexes = [
            models.Index(fields=["role"], name="idx_user_profiles_role"),
            models.Index(fields=["account_status"], name="idx_user_profiles_status"),
        ]

    def __str__(self):
        return f"{self.user} - {self.role}"


class PlatformScreeningSession(models.Model):
    screening_session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="screening_sessions",
        db_column="user_id",
    )
    session_status = models.CharField(
        max_length=20,
        choices=SessionStatus.choices,
        default=SessionStatus.STARTED,
    )
    current_activity = models.CharField(max_length=100, blank=True, null=True)
    workflow_stage = models.PositiveIntegerField(default=1)
    completed_activities_count = models.PositiveIntegerField(default=0)
    overall_risk = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        blank=True,
        null=True,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "platform_screening_sessions"
        indexes = [
            models.Index(fields=["user", "-started_at"], name="idx_screening_user_created"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(workflow_stage__gte=1), name="screening_workflow_stage_gte_1"),
            models.CheckConstraint(condition=Q(completed_activities_count__gte=0), name="screening_completed_count_gte_0"),
        ]

    def __str__(self):
        return f"Session {self.screening_session_id} - {self.user}"


class MediaAsset(TimeStampedModel):
    media_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="media_assets",
        db_column="user_id",
    )
    media_type = models.CharField(max_length=30, choices=MediaType.choices)
    file_name = models.CharField(max_length=500)
    content_type = models.CharField(max_length=100)
    size_bytes = models.BigIntegerField()
    duration_seconds = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    storage_provider = models.CharField(max_length=50, default="gcp")
    bucket_name = models.CharField(max_length=255, blank=True, null=True)
    bucket_region = models.CharField(max_length=100, blank=True, null=True)
    storage_class = models.CharField(max_length=100, blank=True, null=True)
    object_key = models.TextField()
    cdn_url = models.TextField(blank=True, null=True)
    checksum_hash = models.CharField(max_length=255, blank=True, null=True)
    upload_status = models.CharField(
        max_length=20,
        choices=UploadStatus.choices,
        default=UploadStatus.PENDING,
    )
    metadata_json = models.JSONField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "media_assets"
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_media_assets_user_created"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(size_bytes__gte=0), name="media_size_bytes_gte_0"),
            models.CheckConstraint(condition=Q(duration_seconds__gte=0) | Q(duration_seconds__isnull=True),
                name="media_duration_seconds_gte_0",
            ),
        ]

    def __str__(self):
        return self.file_name


class VideoActivity(models.Model):
    video_activity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    instruction_text = models.TextField()
    image_set_json = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "video_activities"

    def __str__(self):
        return self.title


class VideoSession(models.Model):
    video_session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.ForeignKey(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="video_sessions",
        db_column="screening_session_id",
    )
    video_activity = models.ForeignKey(
        VideoActivity,
        on_delete=models.PROTECT,
        related_name="video_sessions",
        db_column="video_activity_id",
    )
    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.SET_NULL,
        related_name="video_sessions",
        db_column="media_id",
        blank=True,
        null=True,
    )
    extraction_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    analysis_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    session_status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.STARTED)
    processing_started_at = models.DateTimeField(blank=True, null=True)
    processing_completed_at = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "video_sessions"

    def __str__(self):
        return f"Video session {self.video_session_id}"


class FaceFeatureVector(models.Model):
    feature_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    video_session = models.ForeignKey(
        VideoSession,
        on_delete=models.CASCADE,
        related_name="face_feature_vectors",
        db_column="video_session_id",
    )
    frame_number = models.PositiveIntegerField()
    face_landmarks = models.JSONField(blank=True, null=True)
    emotion_scores = models.JSONField(blank=True, null=True)
    head_pose = models.JSONField(blank=True, null=True)
    eye_tracking = models.JSONField(blank=True, null=True)
    blink_rate = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    embedding_vector = VectorField(dimensions=512, blank=True, null=True)
    model_version = models.CharField(max_length=100, blank=True, null=True)
    api_processed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "face_feature_vectors"
        constraints = [
            models.CheckConstraint(condition=Q(frame_number__gte=0), name="face_frame_number_gte_0"),
            models.CheckConstraint(condition=Q(blink_rate__gte=0) | Q(blink_rate__isnull=True), name="face_blink_rate_gte_0"),
        ]

    def __str__(self):
        return f"Face feature frame {self.frame_number}"


class FacialAnalysisResult(models.Model):
    facial_analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.OneToOneField(
        FaceFeatureVector,
        on_delete=models.CASCADE,
        related_name="facial_analysis_result",
        db_column="feature_id",
    )
    stress_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    depression_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    anxiety_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    risk_label = models.CharField(max_length=100, blank=True, null=True)
    api_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "facial_analysis_results"
        constraints = [
            models.CheckConstraint(condition=Q(stress_score__gte=0, stress_score__lte=100) | Q(stress_score__isnull=True), name="face_stress_score_0_100"),
            models.CheckConstraint(condition=Q(depression_score__gte=0, depression_score__lte=100) | Q(depression_score__isnull=True), name="face_depression_score_0_100"),
            models.CheckConstraint(condition=Q(anxiety_score__gte=0, anxiety_score__lte=100) | Q(anxiety_score__isnull=True), name="face_anxiety_score_0_100"),
            models.CheckConstraint(condition=Q(confidence_score__gte=0, confidence_score__lte=1) | Q(confidence_score__isnull=True), name="face_confidence_score_0_1"),
        ]


class PhonationSound(models.Model):
    sound_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language_code = models.CharField(max_length=10)
    sound_character = models.CharField(max_length=50)
    sound_name = models.CharField(max_length=255)
    sound_order = models.IntegerField()

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "phonation_sounds"
        ordering = ["sound_order"]

    def __str__(self):
        return f"{self.sound_character} - {self.sound_name}"


class PhonationSession(models.Model):
    phonation_session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.OneToOneField(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="phonation_session",
        db_column="screening_session_id",
    )
    session_status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.STARTED)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "phonation_sessions"


class PhonationAttempt(models.Model):
    attempt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phonation_session = models.ForeignKey(
        PhonationSession,
        on_delete=models.CASCADE,
        related_name="attempts",
        db_column="phonation_session_id",
    )
    sound = models.ForeignKey(
        PhonationSound,
        on_delete=models.PROTECT,
        related_name="attempts",
        db_column="sound_id",
    )
    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="phonation_attempts",
        db_column="media_id",
    )
    pronunciation_detected = models.BooleanField(blank=True, null=True)
    character_accuracy_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    noise_level = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    silence_duration_ms = models.PositiveIntegerField(blank=True, null=True)
    response_time_ms = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "phonation_attempts"
        constraints = [
            models.UniqueConstraint(fields=["phonation_session", "sound"], name="unique_phonation_session_sound"),
            models.CheckConstraint(condition=Q(character_accuracy_score__gte=0, character_accuracy_score__lte=100) | Q(character_accuracy_score__isnull=True),
                name="phonation_accuracy_score_0_100",
            ),
            models.CheckConstraint(condition=Q(silence_duration_ms__gte=0) | Q(silence_duration_ms__isnull=True), name="phonation_silence_duration_gte_0"),
            models.CheckConstraint(condition=Q(response_time_ms__gte=0) | Q(response_time_ms__isnull=True), name="phonation_response_time_gte_0"),
        ]


class AudioExtractionResult(models.Model):
    audio_extraction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attempt = models.OneToOneField(
        PhonationAttempt,
        on_delete=models.CASCADE,
        related_name="audio_extraction_result",
        db_column="attempt_id",
    )
    raw_wave_features = models.JSONField(blank=True, null=True)
    noise_profile = models.JSONField(blank=True, null=True)
    frequency_profile = models.JSONField(blank=True, null=True)
    extraction_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "audio_extraction_results"


class PhonationFeature(models.Model):
    feature_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    audio_extraction = models.OneToOneField(
        AudioExtractionResult,
        on_delete=models.CASCADE,
        related_name="phonation_feature",
        db_column="audio_extraction_id",
    )
    pitch_mean = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    jitter = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    shimmer = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    hnr = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    voice_energy = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    mfcc_features = models.JSONField(blank=True, null=True)
    embedding_vector = VectorField(dimensions=256, blank=True, null=True)
    model_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "phonation_features"


class VoiceAnalysisResult(models.Model):
    voice_analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.OneToOneField(
        PhonationFeature,
        on_delete=models.CASCADE,
        related_name="voice_analysis_result",
        db_column="feature_id",
    )
    stress_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    depression_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    speech_impairment_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    api_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "voice_analysis_results"
        constraints = [
            models.CheckConstraint(condition=Q(stress_score__gte=0, stress_score__lte=100) | Q(stress_score__isnull=True), name="voice_stress_score_0_100"),
            models.CheckConstraint(condition=Q(depression_score__gte=0, depression_score__lte=100) | Q(depression_score__isnull=True), name="voice_depression_score_0_100"),
            models.CheckConstraint(condition=Q(speech_impairment_score__gte=0, speech_impairment_score__lte=100) | Q(speech_impairment_score__isnull=True), name="voice_speech_score_0_100"),
            models.CheckConstraint(condition=Q(confidence_score__gte=0, confidence_score__lte=1) | Q(confidence_score__isnull=True), name="voice_confidence_score_0_1"),
        ]


class AudioScenario(models.Model):
    audio_scenario_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    prompt_text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "audio_scenarios"

    def __str__(self):
        return self.title


class ScenarioSession(models.Model):
    scenario_session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.ForeignKey(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="scenario_sessions",
        db_column="screening_session_id",
    )
    audio_scenario = models.ForeignKey(
        AudioScenario,
        on_delete=models.PROTECT,
        related_name="scenario_sessions",
        db_column="audio_scenario_id",
    )
    media = models.ForeignKey(
        MediaAsset,
        on_delete=models.PROTECT,
        related_name="scenario_sessions",
        db_column="media_id",
        blank=True,
        null=True,
    )
    session_status = models.CharField(max_length=20, choices=SessionStatus.choices, default=SessionStatus.STARTED)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "scenario_sessions"


class Transcript(models.Model):
    transcript_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_session = models.OneToOneField(
        ScenarioSession,
        on_delete=models.CASCADE,
        related_name="transcript",
        db_column="scenario_session_id",
    )
    transcript_text = models.TextField()
    language_code = models.CharField(max_length=10, blank=True, null=True)
    transcript_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "transcripts"

    def __str__(self):
        return self.transcript_text[:80]


class TextParameterResult(models.Model):
    text_parameter_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transcript = models.OneToOneField(
        Transcript,
        on_delete=models.CASCADE,
        related_name="text_parameter_result",
        db_column="transcript_id",
    )
    sentiment_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    emotion_distribution = models.JSONField(blank=True, null=True)
    keyword_analysis = models.JSONField(blank=True, null=True)
    linguistic_features = models.JSONField(blank=True, null=True)
    embedding_vector = VectorField(dimensions=1536, blank=True, null=True)
    api_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "text_parameter_results"
        constraints = [
            models.CheckConstraint(condition=Q(sentiment_score__gte=-100, sentiment_score__lte=100) | Q(sentiment_score__isnull=True),
                name="text_sentiment_score_minus100_100",
            ),
        ]


class TextAnalysisResult(models.Model):
    text_analysis_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text_parameter = models.OneToOneField(
        TextParameterResult,
        on_delete=models.CASCADE,
        related_name="text_analysis_result",
        db_column="text_parameter_id",
    )
    stress_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    depression_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    anxiety_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    api_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "text_analysis_results"
        constraints = [
            models.CheckConstraint(condition=Q(stress_score__gte=0, stress_score__lte=100) | Q(stress_score__isnull=True), name="text_stress_score_0_100"),
            models.CheckConstraint(condition=Q(depression_score__gte=0, depression_score__lte=100) | Q(depression_score__isnull=True), name="text_depression_score_0_100"),
            models.CheckConstraint(condition=Q(anxiety_score__gte=0, anxiety_score__lte=100) | Q(anxiety_score__isnull=True), name="text_anxiety_score_0_100"),
            models.CheckConstraint(condition=Q(confidence_score__gte=0, confidence_score__lte=1) | Q(confidence_score__isnull=True), name="text_confidence_score_0_1"),
        ]


class PcaPipelineResult(models.Model):
    pca_result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.OneToOneField(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="pca_pipeline_result",
        db_column="screening_session_id",
    )
    reduced_feature_vector = VectorField(dimensions=128, blank=True, null=True)
    dimensionality_reduction_metadata = models.JSONField(blank=True, null=True)
    api_version = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "pca_pipeline_results"


class FusionPrediction(models.Model):
    prediction_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.OneToOneField(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="fusion_prediction",
        db_column="screening_session_id",
    )
    pca_result = models.OneToOneField(
        PcaPipelineResult,
        on_delete=models.PROTECT,
        related_name="fusion_prediction",
        db_column="pca_result_id",
        blank=True,
        null=True,
    )
    anxiety_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    depression_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    stress_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    bipolar_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    suicidal_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    overall_risk = models.CharField(max_length=20, choices=RiskLevel.choices, blank=True, null=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    final_prediction_json = models.JSONField(blank=True, null=True)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "fusion_predictions"
        constraints = [
            models.CheckConstraint(condition=Q(anxiety_score__gte=0, anxiety_score__lte=100) | Q(anxiety_score__isnull=True), name="fusion_anxiety_score_0_100"),
            models.CheckConstraint(condition=Q(depression_score__gte=0, depression_score__lte=100) | Q(depression_score__isnull=True), name="fusion_depression_score_0_100"),
            models.CheckConstraint(condition=Q(stress_score__gte=0, stress_score__lte=100) | Q(stress_score__isnull=True), name="fusion_stress_score_0_100"),
            models.CheckConstraint(condition=Q(bipolar_score__gte=0, bipolar_score__lte=100) | Q(bipolar_score__isnull=True), name="fusion_bipolar_score_0_100"),
            models.CheckConstraint(condition=Q(suicidal_score__gte=0, suicidal_score__lte=100) | Q(suicidal_score__isnull=True), name="fusion_suicidal_score_0_100"),
            models.CheckConstraint(condition=Q(confidence_score__gte=0, confidence_score__lte=1) | Q(confidence_score__isnull=True), name="fusion_confidence_score_0_1"),
        ]


class AiApiRegistry(models.Model):
    api_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_name = models.CharField(max_length=255, unique=True)
    service_type = models.CharField(max_length=100)
    base_url = models.TextField()
    port = models.IntegerField(unique=True, blank=True, null=True)
    endpoint_path = models.TextField(blank=True, null=True)
    model_version = models.CharField(max_length=100, blank=True, null=True)
    timeout_seconds = models.PositiveIntegerField(default=30)
    retry_count = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    health_status = models.CharField(max_length=50, default="healthy")
    metadata_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "ai_api_registry"
        constraints = [
            models.CheckConstraint(condition=Q(timeout_seconds__gt=0), name="api_timeout_seconds_gt_0"),
            models.CheckConstraint(condition=Q(retry_count__gte=0), name="api_retry_count_gte_0"),
        ]

    def __str__(self):
        return self.api_name


class ApiExecutionLog(models.Model):
    execution_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.ForeignKey(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="api_execution_logs",
        db_column="screening_session_id",
    )
    api = models.ForeignKey(
        AiApiRegistry,
        on_delete=models.PROTECT,
        related_name="execution_logs",
        db_column="api_id",
    )
    request_payload = models.JSONField(blank=True, null=True)
    response_payload = models.JSONField(blank=True, null=True)
    response_status = models.IntegerField(blank=True, null=True)
    execution_status = models.CharField(max_length=20, choices=ProcessingStatus.choices, default=ProcessingStatus.PENDING)
    error_message = models.TextField(blank=True, null=True)
    processing_time_ms = models.PositiveIntegerField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "api_execution_logs"
        indexes = [
            models.Index(fields=["screening_session", "-created_at"], name="idx_api_logs_screening"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(processing_time_ms__gte=0) | Q(processing_time_ms__isnull=True), name="api_processing_time_gte_0"),
        ]


class ModalityResult(models.Model):
    modality_result_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screening_session = models.ForeignKey(
        PlatformScreeningSession,
        on_delete=models.CASCADE,
        related_name="modality_results",
        db_column="screening_session_id",
    )
    modality = models.CharField(max_length=20, choices=Modality.choices)
    face_result = models.OneToOneField(
        FacialAnalysisResult,
        on_delete=models.PROTECT,
        related_name="modality_result",
        db_column="face_result_id",
        blank=True,
        null=True,
    )
    voice_result = models.OneToOneField(
        VoiceAnalysisResult,
        on_delete=models.PROTECT,
        related_name="modality_result",
        db_column="voice_result_id",
        blank=True,
        null=True,
    )
    text_result = models.OneToOneField(
        TextAnalysisResult,
        on_delete=models.PROTECT,
        related_name="modality_result",
        db_column="text_result_id",
        blank=True,
        null=True,
    )
    confidence_score = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)
    result_payload = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "modality_results"
        constraints = [
            models.CheckConstraint(condition=Q(confidence_score__gte=0, confidence_score__lte=1) | Q(confidence_score__isnull=True), name="modality_confidence_score_0_1"),
        ]


class AuditLog(models.Model):
    audit_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
        db_column="user_id",
        blank=True,
        null=True,
    )
    action_name = models.CharField(max_length=255)
    entity_name = models.CharField(max_length=255)
    entity_id = models.UUIDField(blank=True, null=True)
    metadata_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "audit_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action_name} - {self.entity_name}"


class SecurityEvent(models.Model):
    security_event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="security_events",
        db_column="user_id",
        blank=True,
        null=True,
    )
    event_type = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    metadata_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = MANAGED_BY_DJANGO
        db_table = "security_events"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.severity}: {self.event_type}"
