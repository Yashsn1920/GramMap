from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Block, District, State, Village


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("name",)


@admin.register(District)
class DistrictAdmin(GISModelAdmin):
    list_display = ("code", "name", "state")
    list_filter = ("state",)
    search_fields = ("name",)


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "district")
    list_filter = ("district",)
    search_fields = ("name",)


@admin.register(Village)
class VillageAdmin(GISModelAdmin):
    list_display = ("lgd_code", "name", "census_code", "block", "is_pilot", "gap_score")
    list_filter = ("is_pilot", "boundary_precision", "block__district")
    search_fields = ("name", "norm_name", "lgd_code", "census_code")
