"""Lineage: pipeline runs, raw (bronze) payloads and normalized (silver) source records."""

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from apps.geo.models import Precision, Village


class PipelineRun(models.Model):
    class Kind(models.TextChoices):
        BATCH = "batch"
        ON_DEMAND = "on_demand"

    class Status(models.TextChoices):
        QUEUED = "queued"
        RUNNING = "running"
        SUCCEEDED = "succeeded"
        FAILED = "failed"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    scope = models.JSONField(default=dict)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    config_hash = models.CharField(max_length=64, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    stats = models.JSONField(default=dict, blank=True)
    errors = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.kind} run {self.pk} ({self.status})"


class BronzeRecord(models.Model):
    """One raw response from a source, stored as fetched. content_hash makes re-runs idempotent."""

    source = models.CharField(max_length=40)
    query = models.JSONField(default=dict)
    fetched_at = models.DateTimeField(auto_now_add=True)
    content_hash = models.CharField(max_length=64)
    payload = models.JSONField()
    run = models.ForeignKey(
        PipelineRun, on_delete=models.SET_NULL, null=True, blank=True, related_name="bronze"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "content_hash"], name="bronze_unique_content")
        ]


class SourceRecord(models.Model):
    """Silver layer: one normalized feature from one source."""

    source = models.CharField(max_length=40)
    source_id = models.CharField(max_length=100)
    bronze = models.ForeignKey(BronzeRecord, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=3, db_index=True)
    subtype = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=255, blank=True)
    norm_name = models.CharField(max_length=255, blank=True)
    key_tokens = ArrayField(models.CharField(max_length=60), default=list, blank=True)
    official_ids = models.JSONField(default=dict, blank=True)
    attributes = models.JSONField(default=dict, blank=True)
    geom = models.GeometryField(srid=4326, null=True, blank=True)
    location_precision = models.CharField(max_length=12, choices=Precision.choices, blank=True)
    village = models.ForeignKey(
        Village, on_delete=models.SET_NULL, null=True, blank=True, related_name="source_records"
    )
    source_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "source_id"], name="source_record_unique_id")
        ]

    def __str__(self):
        return f"{self.source}:{self.source_id} {self.name}"
