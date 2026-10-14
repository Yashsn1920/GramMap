"""Gold layer: conflated assets, their links to source records, and review / feedback."""

from django.conf import settings
from django.contrib.gis.db import models

from apps.geo.models import Precision, Village
from apps.sources.models import SourceRecord


class Asset(models.Model):
    class ReviewStatus(models.TextChoices):
        AUTO = "auto"
        CONFIRMED = "confirmed"
        REJECTED = "rejected"

    category = models.CharField(max_length=3, db_index=True)
    subtype = models.CharField(max_length=40, blank=True)
    name = models.CharField(max_length=255, blank=True)
    geom = models.GeometryField(srid=4326)
    village = models.ForeignKey(
        Village, on_delete=models.SET_NULL, null=True, blank=True, related_name="assets"
    )
    attributes = models.JSONField(default=dict, blank=True)
    attribute_provenance = models.JSONField(default=dict, blank=True)
    confidence = models.DecimalField(max_digits=3, decimal_places=2)
    location_precision = models.CharField(max_length=12, choices=Precision.choices)
    source_count = models.PositiveSmallIntegerField(default=1)
    first_seen = models.DateField(null=True, blank=True)
    last_confirmed = models.DateField(null=True, blank=True)
    review_status = models.CharField(
        max_length=10, choices=ReviewStatus.choices, default=ReviewStatus.AUTO
    )
    source_records = models.ManyToManyField(SourceRecord, through="AssetSourceLink")

    def __str__(self):
        return f"{self.category} {self.name or '(unnamed)'}"


class AssetSourceLink(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    source_record = models.ForeignKey(SourceRecord, on_delete=models.CASCADE)
    match_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["asset", "source_record"], name="asset_source_unique")
        ]


class MatchReview(models.Model):
    class Decision(models.TextChoices):
        MATCH = "match"
        NOT_MATCH = "not_match"

    record_a = models.ForeignKey(SourceRecord, on_delete=models.CASCADE, related_name="+")
    record_b = models.ForeignKey(SourceRecord, on_delete=models.CASCADE, related_name="+")
    score = models.DecimalField(max_digits=4, decimal_places=3)
    decision = models.CharField(max_length=10, choices=Decision.choices, blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["record_a", "record_b"], name="match_review_unique_pair"
            )
        ]


class CorrectionFlag(models.Model):
    class Status(models.TextChoices):
        OPEN = "open"
        ACCEPTED = "accepted"
        REJECTED = "rejected"

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="correction_flags")
    suggested_geom = models.PointField(srid=4326, null=True, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
