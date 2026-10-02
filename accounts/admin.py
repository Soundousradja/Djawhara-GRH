from django.contrib import admin
from .models import Profile, AuditLog


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'workshop', 'phone')
    list_filter = ('role', 'workshop')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_repr')
    list_filter = ('action', 'model_name')
    search_fields = ('object_repr', 'user__username')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False
