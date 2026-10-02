import datetime
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from employees.models import Employee, Workshop
from attendance.models import AttendanceRecord
from contracts.models import Contract
from payroll.models import PayrollElement


@login_required
def dashboard(request):

    today = datetime.date.today()

    # ==========================================================
    # 1. EMPLOYES
    # ==========================================================

    active_employees = Employee.objects.filter(
        status=Employee.STATUS_ACTIVE
    )

    total_employees = active_employees.count()

    inactive_employees = Employee.objects.filter(
        status=Employee.STATUS_INACTIVE
    ).count()

    suspended_employees = Employee.objects.filter(
        status=Employee.STATUS_SUSPENDED
    ).count()

    # ==========================================================
    # 2. ATELIERS
    # ==========================================================

    total_workshops = Workshop.objects.count()

    workshop_stats = []

    for workshop in Workshop.objects.all():

        count = active_employees.filter(
            workshop=workshop
        ).count()

        workshop_stats.append({
            'name': workshop.name,
            'count': count,
        })

    workshop_stats.sort(
        key=lambda x: x['count'],
        reverse=True
    )

    # ==========================================================
    # 3. CONTRATS
    # ==========================================================

    active_contracts = Contract.objects.filter(
        status=Contract.STATUS_ACTIVE
    ).count()

    contract_stats = {

        'cdi': Contract.objects.filter(
            contract_type=Contract.TYPE_CDI,
            status=Contract.STATUS_ACTIVE
        ).count(),

        'cdd': Contract.objects.filter(
            contract_type=Contract.TYPE_CDD,
            status=Contract.STATUS_ACTIVE
        ).count(),

        'probation': Contract.objects.filter(
            contract_type=Contract.TYPE_TRIAL,
            status=Contract.STATUS_ACTIVE
        ).count(),

        'temporary': Contract.objects.filter(
            contract_type=Contract.TYPE_TEMP,
            status=Contract.STATUS_ACTIVE
        ).count(),

    }

    # ----------------------------------------------------------
    # Contrats bientôt expirés
    # ----------------------------------------------------------

    alert_days = getattr(
        settings,
        'CONTRACT_ALERT_DAYS',
        30
    )

    contracts_ending_soon = Contract.objects.filter(
        status=Contract.STATUS_ACTIVE,
        end_date__isnull=False,
        end_date__gte=today,
        end_date__lte=today + datetime.timedelta(
            days=alert_days
        )
    ).select_related(
        'employee'
    )

    contracts_ending_soon = list(
        contracts_ending_soon
    )

    contracts_ending_soon.sort(
        key=lambda x: x.days_before_end
    )

    # ==========================================================
    # 4. POINTAGE AUJOURD'HUI
    # ==========================================================

    today_records = AttendanceRecord.objects.filter(
        date=today,
        employee__status=Employee.STATUS_ACTIVE
    )

    present_count = today_records.filter(
        status=AttendanceRecord.STATUS_PRESENT
    ).count()

    absent_count = today_records.filter(
        status__in=[
            AttendanceRecord.STATUS_ABSENT_JUSTIFIED,
            AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
        ]
    ).count()

    unjustified_absent_count = today_records.filter(
        status=AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
    ).count()

    late_count = today_records.filter(
        status=AttendanceRecord.STATUS_LATE
    ).count()

    leave_count = today_records.filter(
        status__in=[
            AttendanceRecord.STATUS_ANNUAL_LEAVE,
            AttendanceRecord.STATUS_SICK_LEAVE
        ]
    ).count()

    rest_count = today_records.filter(
        status=AttendanceRecord.STATUS_REST_DAY
    ).count()

    recorded = today_records.count()

    not_recorded_count = max(
        total_employees - recorded,
        0
    )

    today_counts = {

        'present': present_count,

        'absent': absent_count,

        'unjustified_absent':
            unjustified_absent_count,

        'late': late_count,

        'leave': leave_count,

        'rest': rest_count,

        'not_recorded':
            not_recorded_count,
    }

    # ==========================================================
    # 4 BIS. TAUX DE PRESENCE
    # ==========================================================

    if total_employees:

        attendance_rate = round(
            (
                present_count /
                total_employees
            ) * 100
        )

    else:

        attendance_rate = 0

    # ==========================================================
    # 5. PRESENCE DES 7 DERNIERS JOURS
    # ==========================================================

    week_chart_data = []

    for i in range(6, -1, -1):

        day = today - datetime.timedelta(
            days=i
        )

        records = AttendanceRecord.objects.filter(
            date=day,
            employee__status=Employee.STATUS_ACTIVE
        )

        present = records.filter(
            status=AttendanceRecord.STATUS_PRESENT
        ).count()

        absent = records.filter(
            status__in=[
                AttendanceRecord.STATUS_ABSENT_JUSTIFIED,
                AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
            ]
        ).count()

        late = records.filter(
            status=AttendanceRecord.STATUS_LATE
        ).count()

        week_chart_data.append({

            'label':
                day.strftime('%d/%m'),

            'present':
                present,

            'absent':
                absent,

            'late':
                late,

        })

    # ==========================================================
    # 6. DOSSIERS INCOMPLETS
    # ==========================================================

    incomplete_files = []

    employees_with_documents = (
        Employee.objects
        .filter(
            status=Employee.STATUS_ACTIVE
        )
        .prefetch_related(
            'documents',
            'workshop'
        )
    )

    for employee in employees_with_documents:

        try:
            missing = employee.missing_documents
        except Exception:
            missing = []

        if missing:

            incomplete_files.append({

                'employee':
                    employee,

                'missing_count':
                    len(missing),

                'missing_documents':
                    missing,

            })

    incomplete_files.sort(
        key=lambda x: x['missing_count'],
        reverse=True
    )

    # ==========================================================
    # 7. PROBLEMES D'ASSIDUITE
    # ==========================================================

    thirty_days_ago = (
        today -
        datetime.timedelta(days=30)
    )

    problem_records = (
        AttendanceRecord.objects
        .filter(
            date__gte=thirty_days_ago,
            employee__status=Employee.STATUS_ACTIVE,
            status__in=[
                AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED,
                AttendanceRecord.STATUS_ABSENT_JUSTIFIED,
                AttendanceRecord.STATUS_LATE,
            ]
        )
        .values(
            'employee',
            'employee__first_name',
            'employee__last_name',
            'employee__workshop__name',
            'status'
        )
        .annotate(
            total=Count('id')
        )
    )

    problem_employees_dict = {}

    for row in problem_records:

        employee_id = row['employee']

        if employee_id not in problem_employees_dict:

            problem_employees_dict[employee_id] = {

                'employee_id':
                    employee_id,

                'name':
                    (
                        f"{row['employee__first_name']} "
                        f"{row['employee__last_name']}"
                    ),

                'workshop':
                    (
                        row['employee__workshop__name']
                        or 'Sans atelier'
                    ),

                'absences':
                    0,

                'unjustified':
                    0,

                'late':
                    0,
            }

        item = problem_employees_dict[
            employee_id
        ]

        if (
            row['status']
            ==
            AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
        ):

            item['unjustified'] += row['total']

            item['absences'] += row['total']

        elif (
            row['status']
            ==
            AttendanceRecord.STATUS_ABSENT_JUSTIFIED
        ):

            item['absences'] += row['total']

        elif (
            row['status']
            ==
            AttendanceRecord.STATUS_LATE
        ):

            item['late'] += row['total']

    problem_employees = sorted(

        problem_employees_dict.values(),

        key=lambda x: (
            x['unjustified'],
            x['late'],
            x['absences']
        ),

        reverse=True
    )

    # ==========================================================
    # 7 BIS. ATTENDANCE ISSUES
    # ==========================================================

    attendance_issues = []

    for employee in problem_employees:

        attendance_issues.append({

            'employee':
                employee['name'],

            'workshop':
                employee['workshop'],

            'absences':
                employee['absences'],

            'lates':
                employee['late'],

        })

    attendance_issues = attendance_issues[:6]

    # ==========================================================
    # 7 TER. PRESENCE PAR ATELIER
    # ==========================================================

    workshop_attendance = []

    for workshop in Workshop.objects.all():

        workshop_employees = active_employees.filter(
            workshop=workshop
        )

        workshop_total = workshop_employees.count()

        if workshop_total == 0:

            rate = 0

        else:

            workshop_present = today_records.filter(
                employee__workshop=workshop,
                status=AttendanceRecord.STATUS_PRESENT
            ).count()

            rate = round(
                (
                    workshop_present /
                    workshop_total
                ) * 100
            )

        workshop_attendance.append({

            'name':
                workshop.name,

            'rate':
                rate,

            'count':
                workshop_total,

        })

    workshop_attendance.sort(
        key=lambda x: x['rate'],
        reverse=True
    )

    # ==========================================================
    # 8. EMPLOYES RECENTS
    # ==========================================================

    try:

        recent_employees = (
            Employee.objects
            .select_related('workshop')
            .order_by('-date_joined')[:6]
        )

    except Exception:

        try:

            recent_employees = (
                Employee.objects
                .select_related('workshop')
                .order_by('-id')[:6]
            )

        except Exception:

            recent_employees = []

    # ==========================================================
    # 9. ACTIVITE RECENTE
    # ==========================================================

    recent_activity = []

    try:

        from accounts.models import AuditLog

        recent_activity = (
            AuditLog.objects
            .select_related('user')
            .order_by('-timestamp')[:8]
        )

    except Exception:

        pass

    # ==========================================================
    # 10. ALERTES
    # ==========================================================

    alerts = []

    if contracts_ending_soon:

        alerts.append({

            'type':
                'danger',

            'title':
                'Contrats bientôt expirés',

            'message':
                (
                    f"{len(contracts_ending_soon)} "
                    "contrat(s) bientôt expiré(s)."
                ),

            'count':
                len(contracts_ending_soon),

        })

    if late_count:

        alerts.append({

            'type':
                'warning',

            'title':
                'Employés en retard',

            'message':
                (
                    f"{late_count} "
                    "employé(s) en retard."
                ),

            'count':
                late_count,

        })

    if unjustified_absent_count:

        alerts.append({

            'type':
                'danger',

            'title':
                'Absences non justifiées',

            'message':
                (
                    f"{unjustified_absent_count} "
                    "absence(s) non justifiée(s)."
                ),

            'count':
                unjustified_absent_count,

        })

    if incomplete_files:

        alerts.append({

            'type':
                'info',

            'title':
                'Dossiers incomplets',

            'message':
                (
                    f"{len(incomplete_files)} "
                    "dossier(s) incomplet(s)."
                ),

            'count':
                len(incomplete_files),

        })

    

    # ==========================================================
    # 12. JSON
    # ==========================================================

    week_chart_json = json.dumps(
        week_chart_data
    )

    today_counts_json = json.dumps(
        today_counts
    )

    # ==========================================================
    # 13. CONTEXT
    # ==========================================================

    context = {

        'today':
            today,

        'active_menu':
            'dashboard',

        # KPI

        'total_employees':
            total_employees,

        'total_workshops':
            total_workshops,

        'active_contracts':
            active_contracts,

        'inactive_employees':
            inactive_employees,

        'suspended_employees':
            suspended_employees,

        # Attendance

        'today_counts':
            today_counts,

        'today_counts_json':
            today_counts_json,

        'attendance_rate':
            attendance_rate,

        # Graphique

        'week_chart_json':
            week_chart_json,

        # Ateliers

        'workshop_stats':
            workshop_stats,

        'workshop_attendance':
            workshop_attendance,

        # Problèmes

        'problem_employees':
            problem_employees[:6],

        'attendance_issues':
            attendance_issues,

        # Contrats

        'contracts_ending_soon':
            contracts_ending_soon,

        'contract_stats':
            contract_stats,

        # Documents

        'incomplete_files':
            incomplete_files[:6],

        # Employés récents

        'recent_employees':
            recent_employees,

        

       

        # Activité

        'recent_activity':
            recent_activity,

        # Alertes

        'alerts':
            alerts,
    }

    # ==========================================================
    # 14. RENDER
    # ==========================================================

    return render(
        request,
        'dashboard.html',
        context
    )