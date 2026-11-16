from django.contrib import admin

from .models import InboundEmail


@admin.register(InboundEmail)
class InboundEmailAdmin(admin.ModelAdmin):
    list_display = ("email_id", "status", "attempts", "error_code", "updated_at")
    list_filter = ("status",)
    search_fields = ("email_id", "forwarded_id")
    readonly_fields = tuple(field.name for field in InboundEmail._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
