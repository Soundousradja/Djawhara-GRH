import datetime
from django.conf import settings
from django.db import models
from employees.models import Employee


class Contract(models.Model):
    TYPE_CDI = 'CDI'
    TYPE_CDD = 'CDD'
    TYPE_TRIAL = 'ESSAI'
    TYPE_TEMP = 'TEMPORAIRE'
    TYPE_CHOICES = [
        (TYPE_CDI, 'CDI - Contrat à durée indéterminée'),
        (TYPE_CDD, 'CDD - Contrat à durée déterminée'),
        (TYPE_TRIAL, "Période d'essai"),
        (TYPE_TEMP, 'Travailleur temporaire / journalier'),
    ]

    PAY_MONTHLY = 'MENSUEL'
    PAY_DAILY = 'JOURNALIER'
    PAY_CHOICES = [
        (PAY_MONTHLY, 'Salaire mensuel'),
        (PAY_DAILY, 'Salaire journalier'),
    ]

    STATUS_ACTIVE = 'ACTIF'
    STATUS_ENDED = 'TERMINE'
    STATUS_CANCELLED = 'ANNULE'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Actif'),
        (STATUS_ENDED, 'Terminé'),
        (STATUS_CANCELLED, 'Annulé'),
    ]

    employee = models.ForeignKey(Employee, related_name='contracts', on_delete=models.CASCADE)
    contract_type = models.CharField('Type de contrat', max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField('Date de début')
    end_date = models.DateField('Date de fin', null=True, blank=True,
                                 help_text='Laisser vide pour un CDI')
    payment_method = models.CharField('Mode de paiement', max_length=15,
                                       choices=PAY_CHOICES, default=PAY_MONTHLY)
    base_salary = models.DecimalField('Salaire de base', max_digits=12, decimal_places=2,
                                       default=0)
    status = models.CharField('Statut', max_length=15, choices=STATUS_CHOICES,
                               default=STATUS_ACTIVE)
    document = models.FileField('Copie du contrat (PDF/scan)', upload_to='documents/contracts/',
                                 null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Contrat'
        verbose_name_plural = 'Contrats'

    def __str__(self):
        return f"{self.employee} - {self.get_contract_type_display()} ({self.start_date})"

    @property
    def days_before_end(self):
        if not self.end_date:
            return None
        return (self.end_date - datetime.date.today()).days

    @property
    def is_ending_soon(self):
        alert_days = getattr(settings, 'CONTRACT_ALERT_DAYS', 30)
        days = self.days_before_end
        return days is not None and 0 <= days <= alert_days

    @property
    def is_expired(self):
        days = self.days_before_end
        return days is not None and days < 0
