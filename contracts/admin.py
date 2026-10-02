from django.contrib import admin
from .models import Contract


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('employee', 'contract_type', 'start_date', 'end_date', 'status', 'base_salary')
    list_filter = ('contract_type', 'status', 'payment_method')
    search_fields = ('employee__first_name', 'employee__last_name')
