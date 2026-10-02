from django.contrib import admin
from .models import PayrollElement, Bonus, Deduction


class BonusInline(admin.TabularInline):
    model = Bonus
    extra = 0


class DeductionInline(admin.TabularInline):
    model = Deduction
    extra = 0


@admin.register(PayrollElement)
class PayrollElementAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'net_pay', 'status')
    list_filter = ('month', 'year', 'status')
    inlines = [BonusInline, DeductionInline]
