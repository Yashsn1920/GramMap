from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import ExpectedAmenity, GapFlag, RoadEdge, Settlement, SettlementAccess, WaterBody


@admin.register(Settlement)
class SettlementAdmin(GISModelAdmin):
    list_display = ("id", "village", "building_count", "population_est")
    raw_id_fields = ("village",)


@admin.register(RoadEdge)
class RoadEdgeAdmin(GISModelAdmin):
    list_display = ("id", "source", "target", "highway", "length_m", "is_blocked")
    list_filter = ("highway", "is_blocked")


@admin.register(SettlementAccess)
class SettlementAccessAdmin(admin.ModelAdmin):
    list_display = ("settlement", "category", "mode", "distance_m", "time_min")
    list_filter = ("category", "mode")
    raw_id_fields = ("settlement", "nearest_asset")


@admin.register(ExpectedAmenity)
class ExpectedAmenityAdmin(admin.ModelAdmin):
    list_display = ("village", "category", "source", "expected_count", "source_year")
    list_filter = ("category", "source")
    raw_id_fields = ("village",)


@admin.register(GapFlag)
class GapFlagAdmin(GISModelAdmin):
    list_display = ("id", "village", "kind", "category", "status", "created_at")
    list_filter = ("kind", "category", "status")
    raw_id_fields = ("village",)


@admin.register(WaterBody)
class WaterBodyAdmin(GISModelAdmin):
    list_display = ("id", "label", "permanence", "trend_slope")
    list_filter = ("label",)
