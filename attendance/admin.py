from django.contrib import admin
from .models import AttendanceRecord, DisciplinaryAction


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'source', 'check_in_at', 'check_out_at', 'workshop')
    list_filter = ('status', 'source', 'workshop', 'date')
    search_fields = ('employee__first_name', 'employee__last_name')
    date_hierarchy = 'date'


@admin.register(DisciplinaryAction)
class DisciplinaryActionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'action_type', 'date', 'created_by')
    list_filter = ('action_type',)
