"""Derived layers: settlements, road network, access results, expected amenities, gaps, water."""

from django.contrib.gis.db import models

from apps.assets.models import Asset
from apps.geo.models import Village


class Settlement(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="settlements")
    geom = models.PolygonField(srid=4326)
    centroid = models.PointField(srid=4326)
    building_count = models.PositiveIntegerField(default=0)
    population_est = models.PositiveIntegerField(null=True, blank=True)
    road_node_id = models.BigIntegerField(null=True, blank=True)


class RoadEdge(models.Model):
    """pgRouting edge table: source/target are node IDs, costs are in seconds."""

    source = models.BigIntegerField(db_index=True)
    target = models.BigIntegerField(db_index=True)
    geom = models.LineStringField(srid=4326)
    highway = models.CharField(max_length=30, blank=True)
    surface = models.CharField(max_length=30, blank=True)
    length_m = models.FloatField()
    cost_walk_s = models.FloatField()
    cost_drive_s = models.FloatField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)


class SettlementAccess(models.Model):
    class Mode(models.TextChoices):
        WALK = "walk"
        DRIVE = "drive"

    settlement = models.ForeignKey(Settlement, on_delete=models.CASCADE, related_name="access")
    category = models.CharField(max_length=3)
    mode = models.CharField(max_length=5, choices=Mode.choices)
    distance_m = models.FloatField(null=True, blank=True)
    time_min = models.FloatField(null=True, blank=True)
    nearest_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["settlement", "category", "mode"], name="settlement_access_unique"
            )
        ]


class ExpectedAmenity(models.Model):
    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="expected")
    category = models.CharField(max_length=3)
    source = models.CharField(max_length=40)
    expected_count = models.PositiveIntegerField()
    source_year = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["village", "category", "source"], name="expected_amenity_unique"
            )
        ]


class GapFlag(models.Model):
    class Kind(models.TextChoices):
        MISSING = "missing"
        UNLISTED = "unlisted"
        COUNT_MISMATCH = "count_mismatch"
        UNMAPPED_ROAD = "unmapped_road"

    class Status(models.TextChoices):
        OPEN = "open"
        RESOLVED = "resolved"
        DISMISSED = "dismissed"

    village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name="gap_flags")
    kind = models.CharField(max_length=15, choices=Kind.choices)
    category = models.CharField(max_length=3, blank=True)
    geom = models.GeometryField(srid=4326, null=True, blank=True)
    evidence = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)


class WaterBody(models.Model):
    class Label(models.TextChoices):
        PERMANENT = "permanent"
        SEASONAL = "seasonal"
        DRYING = "drying"

    # MultiPolygon rather than Polygon: OSM water relations often have several parts.
    geom = models.MultiPolygonField(srid=4326)
    permanence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    trend_slope = models.FloatField(null=True, blank=True)
    label = models.CharField(max_length=10, choices=Label.choices, blank=True)
