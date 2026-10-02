import csv
import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from accounts.models import Profile
from attendance.models import AttendanceRecord
from contracts.models import Contract
from employees.models import Employee, Workshop
from payroll.models import PayrollElement


@login_required
def reports_home(request):
    return render(request, 'reports/home.html', {'active_menu': 'reports'})


@login_required
def daily_report(request):
    date_str = request.GET.get('date')
    try:
        selected_date = datetime.date.fromisoformat(date_str) if date_str else datetime.date.today()
    except ValueError:
        selected_date = datetime.date.today()

    records = AttendanceRecord.objects.filter(date=selected_date).select_related('employee', 'workshop')
    late = records.filter(status=AttendanceRecord.STATUS_LATE)
    unjustified = records.filter(status=AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED)

    if request.GET.get('export') == 'csv':
        return _export_csv(f"rapport_journalier_{selected_date}.csv", ['Employé', 'Atelier', 'Statut', 'Minutes de retard', 'Remarque'],
                            [[r.employee, r.workshop, r.get_status_display(), r.minutes_late, r.note] for r in records])

    context = {
        'selected_date': selected_date,
        'records': records,
        'late': late,
        'unjustified': unjustified,
        'active_menu': 'reports',
    }
    return render(request, 'reports/daily.html', context)


@login_required
def weekly_report(request):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=today.weekday())
    end = start + datetime.timedelta(days=6)

    records = AttendanceRecord.objects.filter(date__range=(start, end))

    top_absent = (
        records.filter(status__in=[AttendanceRecord.STATUS_ABSENT_JUSTIFIED, AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED])
        .values('employee__first_name', 'employee__last_name')
        .annotate(total=Count('id')).order_by('-total')[:10]
    )
    top_late = (
        records.filter(status=AttendanceRecord.STATUS_LATE)
        .values('employee__first_name', 'employee__last_name')
        .annotate(total=Count('id')).order_by('-total')[:10]
    )
    by_workshop = (
        records.values('workshop__name')
        .annotate(
            present=Count('id', filter=Q(status=AttendanceRecord.STATUS_PRESENT)),
            absent=Count('id', filter=Q(status__in=[AttendanceRecord.STATUS_ABSENT_JUSTIFIED, AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED])),
            late=Count('id', filter=Q(status=AttendanceRecord.STATUS_LATE)),
        )
    )

    context = {
        'start': start, 'end': end,
        'top_absent': top_absent, 'top_late': top_late, 'by_workshop': by_workshop,
        'active_menu': 'reports',
    }
    return render(request, 'reports/weekly.html', context)


@role_required(Profile.ROLE_RH, Profile.ROLE_COMPTABLE)
def monthly_report(request):
    month = int(request.GET.get('month', datetime.date.today().month))
    year = int(request.GET.get('year', datetime.date.today().year))

    payroll_elements = PayrollElement.objects.filter(month=month, year=year).select_related('employee')
    contracts_ending = Contract.objects.filter(
        status=Contract.STATUS_ACTIVE, end_date__year=year, end_date__month=month
    ).select_related('employee')

    active_employees = Employee.objects.filter(status=Employee.STATUS_ACTIVE).count()
    stopped_employees = Employee.objects.filter(status=Employee.STATUS_INACTIVE).count()

    if request.GET.get('export') == 'csv':
        return _export_csv(
            f"rapport_mensuel_{year}_{month}.csv",
            ['Employé', 'Jours travaillés', 'Absences', 'Primes', 'Retenues', 'Net à payer'],
            [[p.employee, p.work_days, p.absence_days, p.total_bonuses, p.total_deductions, p.net_pay]
             for p in payroll_elements]
        )

    context = {
        'month': month, 'year': year,
        'payroll_elements': payroll_elements,
        'contracts_ending': contracts_ending,
        'active_employees': active_employees,
        'stopped_employees': stopped_employees,
        'active_menu': 'reports',
    }
    return render(request, 'reports/monthly.html', context)


@role_required(Profile.ROLE_RH, Profile.ROLE_COMPTABLE)
def employee_report(request, pk):
    from employees.models import Employee as EmployeeModel
    employee = EmployeeModel.objects.get(pk=pk)
    records = employee.attendance_records.order_by('-date')[:60]
    contracts = employee.contracts.order_by('-start_date')
    payrolls = employee.payroll_elements.order_by('-year', '-month')[:12]
    context = {
        'employee': employee, 'records': records, 'contracts': contracts,
        'payrolls': payrolls, 'active_menu': 'reports',
    }
    return render(request, 'reports/employee_report.html', context)


def _export_csv(filename, header, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response
