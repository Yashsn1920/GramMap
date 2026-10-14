from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import AuditLog, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (("GramMap", {"fields": ("role",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("GramMap", {"fields": ("email", "role")}),)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("at", "user", "action", "object_type", "object_id")
    list_filter = ("action", "object_type")
    readonly_fields = ("at", "user", "action", "object_type", "object_id", "diff")
