from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import BronzeRecord, PipelineRun, SourceRecord


@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "status", "started_at", "finished_at")
    list_filter = ("kind", "status")


@admin.register(BronzeRecord)
class BronzeRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "source", "fetched_at", "content_hash", "run")
    list_filter = ("source",)


@admin.register(SourceRecord)
class SourceRecordAdmin(GISModelAdmin):
    list_display = ("id", "source", "source_id", "category", "name", "location_precision")
    list_filter = ("source", "category", "location_precision", "is_active")
    search_fields = ("name", "source_id")
    raw_id_fields = ("bronze", "village")
