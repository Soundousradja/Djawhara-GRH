from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """Profil étendu de l'utilisateur avec son rôle dans le système GRH."""

    ROLE_DG = 'DG'
    ROLE_GERANT = 'GERANT'
    ROLE_RH = 'RH'
    ROLE_CHEF = 'CHEF'
    ROLE_COMPTABLE = 'COMPTABLE'
    ROLE_LIMITE = 'LIMITE'

    ROLE_CHOICES = [
        (ROLE_DG, 'Directeur Général'),
        (ROLE_GERANT, 'Gérant'),
        (ROLE_RH, 'Responsable Ressources Humaines'),
        (ROLE_CHEF, "Chef d'atelier"),
        (ROLE_COMPTABLE, 'Comptable / Responsable Finance'),
        (ROLE_LIMITE, 'Utilisateur limité'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_RH)
    workshop = models.ForeignKey(
        'employees.Workshop', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='chefs',
        help_text="Atelier géré (uniquement pour un chef d'atelier)"
    )
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def is_manager(self):
        return self.role != self.ROLE_LIMITE or self.user.is_superuser

    @property
    def is_dg(self):
        return self.role == self.ROLE_DG or self.user.is_superuser

    @property
    def is_gerant(self):
        return self.role == self.ROLE_GERANT

    @property
    def is_rh(self):
        return self.role == self.ROLE_RH

    @property
    def is_chef(self):
        return self.role == self.ROLE_CHEF

    @property
    def is_comptable(self):
        return self.role == self.ROLE_COMPTABLE

    @property
    def can_manage_employees(self):
        return self.is_manager

    @property
    def can_manage_contracts(self):
        return self.is_manager

    @property
    def can_view_payroll(self):
        return self.is_manager

    @property
    def can_edit_payroll(self):
        return self.is_manager


class AuditLog(models.Model):
    """Journal de traçabilité: qui a fait quoi et quand."""

    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Création'),
        (ACTION_UPDATE, 'Modification'),
        (ACTION_DELETE, 'Suppression'),
    ]

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} - {self.user} - {self.get_action_display()} - {self.model_name}"


def log_action(user, action, instance, details=''):
    AuditLog.objects.create(
        user=user if (user and user.is_authenticated) else None,
        action=action,
        model_name=instance.__class__.__name__,
        object_repr=str(instance)[:255],
        details=details,
    )
