import calendar
import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from employees.models import Employee


MONTH_CHOICES = [
    (1, 'Janvier'),
    (2, 'Février'),
    (3, 'Mars'),
    (4, 'Avril'),
    (5, 'Mai'),
    (6, 'Juin'),
    (7, 'Juillet'),
    (8, 'Août'),
    (9, 'Septembre'),
    (10, 'Octobre'),
    (11, 'Novembre'),
    (12, 'Décembre'),
]


class PayrollElement(models.Model):
    """
    Préparation des éléments de la paie mensuelle d'un employé.

    Règles de calcul :
    - 26 jours de travail par mois
    - 8 heures par jour
    - 100 DA par heure normale
    - 150 DA par heure de retard
    - 150 DA par heure supplémentaire
    """

    # ==========================================================
    # STATUTS
    # ==========================================================

    STATUS_DRAFT = 'BROUILLON'
    STATUS_VALIDATED = 'VALIDE'
    STATUS_PAID = 'PAYE'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Brouillon'),
        (STATUS_VALIDATED, 'Validé'),
        (STATUS_PAID, 'Payé'),
    ]

    # ==========================================================
    # CONSTANTES DE PAIE
    # ==========================================================

    WORKING_DAYS_PER_MONTH = Decimal('26')
    HOURS_PER_DAY = Decimal('8')

    # Salaire normal : 100 DA / heure
    HOURLY_RATE = Decimal('100')

    # Retard et heure supplémentaire : 150 DA / heure
    PREMIUM_HOURLY_RATE = Decimal('150')
    SENIORITY_BONUS_PER_YEAR = Decimal('1000')

    # ==========================================================
    # INFORMATIONS GÉNÉRALES
    # ==========================================================

    employee = models.ForeignKey(
        Employee,
        related_name='payroll_elements',
        on_delete=models.CASCADE
    )

    month = models.PositiveSmallIntegerField(
        'Mois',
        choices=MONTH_CHOICES
    )

    year = models.PositiveSmallIntegerField(
        'Année'
    )

    # ==========================================================
    # ÉLÉMENTS DE SALAIRE
    # ==========================================================

    base_salary = models.DecimalField(
        'Salaire de base',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    work_days = models.DecimalField(
        'Jours de travail effectifs',
        max_digits=5,
        decimal_places=1,
        default=0
    )

    absence_days = models.DecimalField(
        "Jours d'absence",
        max_digits=5,
        decimal_places=1,
        default=0
    )

    overtime_hours = models.DecimalField(
        'Heures supplémentaires',
        max_digits=6,
        decimal_places=1,
        default=0
    )

    # ==========================================================
    # RETARDS
    # ==========================================================

    late_minutes = models.PositiveIntegerField(
        'Minutes de retard',
        default=0
    )

    late_deduction = models.DecimalField(
        'Retenue pour retard',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================================================
    # HEURES SUPPLÉMENTAIRES
    # ==========================================================

    overtime_amount = models.DecimalField(
        'Montant des heures supplémentaires',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================================================
    # PRIMES ET RETENUES
    # ==========================================================

    total_bonuses = models.DecimalField(
        'Total des primes',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    seniority_bonus = models.DecimalField(
        "Prime d'ancienneté",
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_deductions = models.DecimalField(
        'Total des retenues',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================================================
    # AVANCE
    # ==========================================================

    advance = models.DecimalField(
        'Avance / Acompte',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================================================
    # NET
    # ==========================================================

    net_pay = models.DecimalField(
        'Net à payer',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # ==========================================================
    # AUTRES INFORMATIONS
    # ==========================================================

    status = models.CharField(
        'Statut',
        max_length=15,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==========================================================
    # META
    # ==========================================================

    class Meta:
        unique_together = (
            'employee',
            'month',
            'year'
        )

        ordering = [
            '-year',
            '-month'
        ]

        verbose_name = 'Élément de paie'
        verbose_name_plural = 'Éléments de paie'

    # ==========================================================
    # AFFICHAGE
    # ==========================================================

    def __str__(self):
        return f"{self.employee} - {self.month}/{self.year}"

    # ==========================================================
    # CALCUL AUTOMATIQUE DE LA PAIE
    # ==========================================================

    def recalculate(self):
        """
        Calcule automatiquement la paie à partir
        des pointages du mois.
        """

        from attendance.models import AttendanceRecord

        # ======================================================
        # RÉCUPÉRER LES POINTAGES DU MOIS
        # ======================================================

        records = AttendanceRecord.objects.filter(
            employee=self.employee,
            date__year=self.year,
            date__month=self.month,
        )

        # ======================================================
        # 1. CALCUL DES JOURS TRAVAILLÉS
        # ======================================================

        worked_statuses = (
            AttendanceRecord.STATUS_PRESENT,
            AttendanceRecord.STATUS_LATE,
            AttendanceRecord.STATUS_EARLY_LEAVE,
        )

        worked_days = sum(
            1
            for record in records
            if record.status in worked_statuses
        )

        # Maximum 26 jours travaillés
        self.work_days = min(
            Decimal(worked_days),
            self.WORKING_DAYS_PER_MONTH
        )

        # ======================================================
        # 2. CALCUL DES ABSENCES
        # ======================================================

        self.absence_days = max(
            self.WORKING_DAYS_PER_MONTH - self.work_days,
            Decimal('0')
        )

        # ======================================================
        # 3. SALAIRE DE BASE
        # ======================================================

        # 26 jours × 8 heures × 100 DA
        #
        # 26 × 8 = 208 heures
        # 208 × 100 = 20 800 DA

        self.base_salary = (
            self.WORKING_DAYS_PER_MONTH
            * self.HOURS_PER_DAY
            * self.HOURLY_RATE
        )

        # ======================================================
        # 4. CALCUL DES RETARDS
        # ======================================================

        self.late_minutes = sum(
            record.minutes_late or 0
            for record in records
        )

        # 150 DA par heure de retard
        #
        # Exemple :
        # 30 minutes = 0.5 × 150 = 75 DA
        # 60 minutes = 1 × 150 = 150 DA

        self.late_deduction = (
            Decimal(self.late_minutes)
            / Decimal('60')
            * self.PREMIUM_HOURLY_RATE
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # ======================================================
        # 5. CALCUL DES HEURES SUPPLÉMENTAIRES
        # ======================================================

        overtime_minutes = 0

        for record in records:

            # Il faut avoir une entrée et une sortie
            if record.check_in_at and record.check_out_at:

                worked_minutes = max(
                    int(
                        (
                            record.check_out_at
                            - record.check_in_at
                        ).total_seconds() // 60
                    ),
                    0
                )

                # 8 heures normales = 480 minutes
                normal_minutes = int(
                    self.HOURS_PER_DAY * 60
                )

                # Tout ce qui dépasse 8 heures
                # est considéré comme heure supplémentaire
                overtime_minutes += max(
                    worked_minutes - normal_minutes,
                    0
                )

        # Conversion minutes → heures
        self.overtime_hours = (
            Decimal(overtime_minutes)
            / Decimal('60')
        ).quantize(
            Decimal('0.1'),
            rounding=ROUND_HALF_UP
        )

        # 150 DA par heure supplémentaire
        self.overtime_amount = (
            Decimal(overtime_minutes)
            / Decimal('60')
            * self.PREMIUM_HOURLY_RATE
        ).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # ======================================================
        # 6. RETENUE DES ABSENCES
        # ======================================================

        # 1 jour = 8 heures × 100 DA
        #
        # 1 jour d'absence = 800 DA
        #
        # 2 jours = 1600 DA

        daily_salary = (
            self.HOURS_PER_DAY
            * self.HOURLY_RATE
        )

        absence_deduction = (
            self.absence_days
            * daily_salary
        )

        # 1 000 DA par année complète d'ancienneté au dernier jour du mois.
        self.seniority_bonus = self.calculate_seniority_bonus()

        # ======================================================
        # 7. PRIMES MANUELLES
        # ======================================================

        manual_bonuses = sum(
            (
                bonus.amount
                for bonus in self.bonuses.all()
            ),
            start=Decimal('0')
        )

        # Total primes =
        # primes manuelles + heures supplémentaires

        self.total_bonuses = (
            manual_bonuses
            + self.seniority_bonus
            + self.overtime_amount
        )

        # ======================================================
        # 8. RETENUES MANUELLES
        # ======================================================

        manual_deductions = sum(
            (
                deduction.amount
                for deduction in self.deductions.all()
            ),
            start=Decimal('0')
        )

        # Total retenues =
        # retenues manuelles
        # + absences
        # + retards

        self.total_deductions = (
            manual_deductions
            + absence_deduction
            + self.late_deduction
        )

        # ======================================================
        # 9. CALCUL FINAL DU NET
        # ======================================================

        self.compute_net()

    def calculate_seniority_bonus(self):
        """Return the seniority bonus earned by the employee for this payroll month."""
        hire_date = self.employee.hire_date
        if not hire_date:
            return Decimal('0')

        month_end = datetime.date(
            self.year,
            self.month,
            calendar.monthrange(self.year, self.month)[1],
        )
        completed_years = month_end.year - hire_date.year
        if (month_end.month, month_end.day) < (hire_date.month, hire_date.day):
            completed_years -= 1

        return max(Decimal(completed_years), Decimal('0')) * self.SENIORITY_BONUS_PER_YEAR

    # ==========================================================
    # CALCUL DU NET
    # ==========================================================

    def compute_net(self):
        """
        Calcule le salaire net à payer.

        Net =
        Salaire de base
        + Primes
        - Retenues
        - Avance
        """

        self.net_pay = (
            (self.base_salary or Decimal('0'))
            + (self.total_bonuses or Decimal('0'))
            - (self.total_deductions or Decimal('0'))
            - (self.advance or Decimal('0'))
        )

        return self.net_pay


# ==============================================================
# PRIME
# ==============================================================

class Bonus(models.Model):

    LABEL_RESPONSIBILITY = 'RESPONSABILITE'
    LABEL_TRANSPORT = 'TRANSPORT'
    LABEL_PRODUCTIVITY = 'PRODUCTION'
    LABEL_OTHER = 'AUTRE'

    LABEL_CHOICES = [
        (
            LABEL_RESPONSIBILITY,
            'Prime de responsabilité'
        ),
        (
            LABEL_TRANSPORT,
            'Prime de transport'
        ),
        (
            LABEL_PRODUCTIVITY,
            'Prime de production/rendement'
        ),
        (
            LABEL_OTHER,
            'Autre prime'
        ),
    ]

    payroll = models.ForeignKey(
        PayrollElement,
        related_name='bonuses',
        on_delete=models.CASCADE
    )

    label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES,
        default=LABEL_OTHER
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.get_label_display()}: {self.amount}"


# ==============================================================
# RETENUE
# ==============================================================

class Deduction(models.Model):

    LABEL_ABSENCE = 'ABSENCE'
    LABEL_LATE = 'RETARD'
    LABEL_ADVANCE = 'AVANCE'
    LABEL_PENALTY = 'SANCTION'
    LABEL_OTHER = 'AUTRE'

    LABEL_CHOICES = [
        (
            LABEL_ABSENCE,
            "Retenue d'absence"
        ),
        (
            LABEL_LATE,
            'Retenue de retard'
        ),
        (
            LABEL_ADVANCE,
            'Avance sur salaire'
        ),
        (
            LABEL_PENALTY,
            'Sanction financière'
        ),
        (
            LABEL_OTHER,
            'Autre retenue'
        ),
    ]

    payroll = models.ForeignKey(
        PayrollElement,
        related_name='deductions',
        on_delete=models.CASCADE
    )

    label = models.CharField(
        max_length=20,
        choices=LABEL_CHOICES,
        default=LABEL_OTHER
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    def __str__(self):
        return f"{self.get_label_display()}: {self.amount}"