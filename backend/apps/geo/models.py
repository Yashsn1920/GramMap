"""Administrative backbone (PRD Section 9). Codes are stored as text to keep leading zeros."""

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex


class Precision(models.TextChoices):
    """How a location was obtained; drives marker style and analysis filters (PRD 7.4, 11.1)."""

    EXACT = "exact"
    MATCHED = "matched"
    APPROXIMATE = "approximate"


class State(models.Model):
    code = models.CharField(primary_key=True, max_length=4)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class District(models.Model):
    code = models.CharField(primary_key=True, max_length=6)
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="districts")
    name = models.CharField(max_length=100)
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)

    def __str__(self):
        return self.name


class Block(models.Model):
    code = models.CharField(primary_key=True, max_length=8)
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="blocks")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Village(models.Model):
    lgd_code = models.CharField(primary_key=True, max_length=10)
    census_code = models.CharField(max_length=10, blank=True, db_index=True)
    gp_lgd_code = models.CharField(max_length=10, blank=True, db_index=True)
    block = models.ForeignKey(Block, on_delete=models.PROTECT, related_name="villages")
    name = models.CharField(max_length=150)
    norm_name = models.CharField(max_length=150)
    name_variants = ArrayField(models.CharField(max_length=150), default=list, blank=True)
    boundary = models.MultiPolygonField(srid=4326, null=True, blank=True)
    boundary_precision = models.CharField(max_length=12, choices=Precision.choices, blank=True)
    population_census = models.PositiveIntegerField(null=True, blank=True)
    population_est = models.PositiveIntegerField(null=True, blank=True)
    completeness_score = models.FloatField(null=True, blank=True)
    gap_score = models.FloatField(null=True, blank=True)
    is_pilot = models.BooleanField(default=False, db_index=True)
    last_processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            GinIndex(
                name="village_norm_name_trgm", fields=["norm_name"], opclasses=["gin_trgm_ops"]
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.lgd_code})"
