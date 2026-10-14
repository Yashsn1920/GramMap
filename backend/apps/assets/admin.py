from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Asset, AssetSourceLink, CorrectionFlag, MatchReview


class AssetSourceLinkInline(admin.TabularInline):
    model = AssetSourceLink
    raw_id_fields = ("source_record",)
    extra = 0


@admin.register(Asset)
class AssetAdmin(GISModelAdmin):
    list_display = ("id", "category", "name", "village", "confidence", "review_status")
    list_filter = ("category", "location_precision", "review_status")
    search_fields = ("name",)
    raw_id_fields = ("village",)
    inlines = [AssetSourceLinkInline]


@admin.register(MatchReview)
class MatchReviewAdmin(admin.ModelAdmin):
    list_display = ("id", "record_a", "record_b", "score", "decision", "decided_by")
    list_filter = ("decision",)
    raw_id_fields = ("record_a", "record_b")


@admin.register(CorrectionFlag)
class CorrectionFlagAdmin(GISModelAdmin):
    list_display = ("id", "asset", "status", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("asset",)


@admin.register(AssetSourceLink)
class AssetSourceLinkAdmin(admin.ModelAdmin):
    list_display = ("asset", "source_record", "match_score")
    raw_id_fields = ("asset", "source_record")
