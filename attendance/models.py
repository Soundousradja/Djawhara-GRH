from django.db import models
from django.contrib.auth.models import User
from employees.models import Employee, Workshop


class AttendanceRecord(models.Model):
    """Enregistrement quotidien de présence/absence d'un employé."""

    STATUS_PRESENT = 'PRESENT'
    STATUS_ABSENT_JUSTIFIED = 'ABSENT_JUSTIFIE'
    STATUS_ABSENT_UNJUSTIFIED = 'ABSENT_INJUSTIFIE'
    STATUS_LATE = 'RETARD'
    STATUS_EARLY_LEAVE = 'SORTIE_ANTICIPEE'
    STATUS_ANNUAL_LEAVE = 'CONGE_ANNUEL'
    STATUS_SICK_LEAVE = 'CONGE_MALADIE'
    STATUS_REST_DAY = 'REPOS'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Présent'),
        (STATUS_ABSENT_JUSTIFIED, 'Absence justifiée'),
        (STATUS_ABSENT_UNJUSTIFIED, 'Absence injustifiée'),
        (STATUS_LATE, 'Retard'),
        (STATUS_EARLY_LEAVE, 'Sortie anticipée'),
        (STATUS_ANNUAL_LEAVE, 'Congé annuel'),
        (STATUS_SICK_LEAVE, 'Congé maladie'),
        (STATUS_REST_DAY, 'Jour de repos'),
    ]

    SOURCE_MANUAL = 'MANUAL'
    SOURCE_BIOMETRIC = 'BIOMETRIQUE'
    SOURCE_CHOICES = [
        (SOURCE_MANUAL, 'Saisie manuelle'),
        (SOURCE_BIOMETRIC, 'Empreinte digitale'),
    ]

    employee = models.ForeignKey(Employee, related_name='attendance_records', on_delete=models.CASCADE)
    workshop = models.ForeignKey(Workshop, null=True, on_delete=models.SET_NULL)
    date = models.DateField('Date')
    status = models.CharField('Statut', max_length=25, choices=STATUS_CHOICES, default=STATUS_PRESENT)
    minutes_late = models.PositiveIntegerField('Minutes de retard', default=0)
    note = models.CharField('Remarque du chef d\'atelier', max_length=255, blank=True)
    source = models.CharField('Source', max_length=15, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    check_in_at = models.DateTimeField("Heure d'entree", null=True, blank=True)
    check_out_at = models.DateTimeField('Heure de sortie', null=True, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']
        verbose_name = 'Pointage'
        verbose_name_plural = 'Pointages'

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.get_status_display()}"

    @property
    def is_problem(self):
        return self.status in (
            self.STATUS_ABSENT_UNJUSTIFIED, self.STATUS_ABSENT_JUSTIFIED, self.STATUS_LATE
        )


class DisciplinaryAction(models.Model):
    """Suivi disciplinaire lié aux problèmes de ponctualité/assiduité."""

    TYPE_NOTE = 'NOTE'
    TYPE_SUMMON = 'CONVOCATION'
    TYPE_WARNING = 'AVERTISSEMENT'
    TYPE_FOLLOWUP = 'SUIVI'
    TYPE_CHOICES = [
        (TYPE_NOTE, 'Simple observation'),
        (TYPE_SUMMON, 'Convocation'),
        (TYPE_WARNING, 'Avertissement'),
        (TYPE_FOLLOWUP, 'Mise sous suivi'),
    ]

    employee = models.ForeignKey(Employee, related_name='disciplinary_actions', on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_NOTE)
    reason = models.TextField('Motif')
    date = models.DateField('Date')
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Action disciplinaire'
        verbose_name_plural = 'Actions disciplinaires'

    def __str__(self):
        return f"{self.employee} - {self.get_action_type_display()} - {self.date}"
