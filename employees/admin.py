from django.contrib import admin
from .models import Workshop, Employee, EmployeeDocument


@admin.register(Workshop)
class WorkshopAdmin(admin.ModelAdmin):
    list_display = ('name', 'active_employee_count')
    search_fields = ('name',)


class EmployeeDocumentInline(admin.TabularInline):
    model = EmployeeDocument
    extra = 0


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'last_name', 'first_name', 'biometric_id', 'workshop', 'position', 'status', 'hire_date')
    list_filter = ('workshop', 'status', 'family_status')
    search_fields = ('matricule', 'first_name', 'last_name', 'national_id', 'cnas_number', 'biometric_id')
    inlines = [EmployeeDocumentInline]


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'doc_type', 'uploaded_at')
    list_filter = ('doc_type',)
