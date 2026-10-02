from django.db import models
from django.urls import reverse


class Workshop(models.Model):
    """Atelier / Service (ex: Bonbons, Confiseries, Emballage, Administration)."""

    name = models.CharField("Nom de l'atelier", max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Atelier"
        verbose_name_plural = "Ateliers"

    def __str__(self):
        return self.name

    @property
    def active_employee_count(self):
        return self.employees.filter(status=Employee.STATUS_ACTIVE).count()


class Employee(models.Model):
    """Fiche employé: informations personnelles et professionnelles."""

    STATUS_ACTIVE = 'ACTIF'
    STATUS_INACTIVE = 'INACTIF'
    STATUS_SUSPENDED = 'SUSPENDU'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Actif'),
        (STATUS_INACTIVE, 'Arrêté / Sorti'),
        (STATUS_SUSPENDED, 'Suspendu'),
    ]

    FAMILY_SINGLE = 'CELIBATAIRE'
    FAMILY_MARRIED = 'MARIE'
    FAMILY_DIVORCED = 'DIVORCE'
    FAMILY_WIDOWED = 'VEUF'
    FAMILY_CHOICES = [
        (FAMILY_SINGLE, 'Célibataire'),
        (FAMILY_MARRIED, 'Marié(e)'),
        (FAMILY_DIVORCED, 'Divorcé(e)'),
        (FAMILY_WIDOWED, 'Veuf(ve)'),
    ]

    SEX_MALE = 'M'
    SEX_FEMALE = 'F'
    SEX_CHOICES = [
        (SEX_MALE, 'Homme'),
        (SEX_FEMALE, 'Femme'),
    ]

    # Informations personnelles
    first_name = models.CharField('Prénom', max_length=100)
    last_name = models.CharField('Nom', max_length=100)
    birth_date = models.DateField('Date de naissance', null=True, blank=True)
    birth_place = models.CharField('Lieu de naissance', max_length=150, blank=True)
    national_id = models.CharField("N° carte d'identité", max_length=50, blank=True)
    address = models.CharField('Adresse', max_length=255, blank=True)
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    family_status = models.CharField('Situation familiale', max_length=20,
                                      choices=FAMILY_CHOICES, blank=True)
    cnas_number = models.CharField('N° CNAS', max_length=50, blank=True)
    # Identifiant fourni par le terminal; aucun gabarit d'empreinte n'est stocke ici.
    biometric_id = models.CharField(
        'Identifiant biometrique', max_length=100, unique=True, null=True, blank=True
    )
    photo = models.ImageField('Photo', upload_to='photos/', null=True, blank=True)

    sex = models.CharField('Sexe', max_length=1, choices=SEX_CHOICES, blank=True)

    # Informations professionnelles
    matricule = models.CharField(
        'Matricule', max_length=20, unique=True, blank=True, editable=False
    )
    hire_date = models.DateField("Date d'embauche", null=True, blank=True)
    position = models.CharField('Poste', max_length=150, blank=True)
    workshop = models.ForeignKey(Workshop, verbose_name='Atelier / Service',
                                  related_name='employees', on_delete=models.SET_NULL,
                                  null=True, blank=True)
    responsible = models.CharField('Responsable direct', max_length=150, blank=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES,
                               default=STATUS_ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'

    def save(self, *args, **kwargs):
        if not self.matricule and self.pk is None:
            super().save(*args, **kwargs)
            self.matricule = f'DJ{self.pk:06d}'
            type(self).objects.filter(pk=self.pk).update(matricule=self.matricule)
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_absolute_url(self):
        return reverse('employee_detail', args=[self.pk])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def active_contract(self):
        return self.contracts.order_by('-start_date').first()

    @property
    def missing_documents(self):
        required = dict(EmployeeDocument.DOC_TYPE_CHOICES)
        existing = set(self.documents.values_list('doc_type', flat=True))
        return [label for code, label in required.items() if code not in existing]


class EmployeeDocument(models.Model):
    """Documents administratifs joints au dossier de l'employé."""

    DOC_ID_CARD = 'CIN'
    DOC_BIRTH_CERT = 'NAISSANCE'
    DOC_RESIDENCE = 'RESIDENCE'
    DOC_PHOTO = 'PHOTO'
    DOC_CONTRACT = 'CONTRAT'
    DOC_CNAS = 'CNAS'
    DOC_DIPLOMA = 'DIPLOME'
    DOC_OTHER = 'AUTRE'
    DOC_TYPE_CHOICES = [
        (DOC_ID_CARD, "Carte d'identité"),
        (DOC_BIRTH_CERT, 'Acte de naissance'),
        (DOC_RESIDENCE, 'Certificat de résidence'),
        (DOC_PHOTO, "Photo d'identité"),
        (DOC_CONTRACT, 'Copie du contrat'),
        (DOC_CNAS, 'Document CNAS'),
        (DOC_DIPLOMA, 'Diplôme / Attestation de formation'),
        (DOC_OTHER, 'Autre document'),
    ]

    employee = models.ForeignKey(Employee, related_name='documents', on_delete=models.CASCADE)
    doc_type = models.CharField('Type de document', max_length=20, choices=DOC_TYPE_CHOICES)
    file = models.FileField('Fichier', upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document employé'
        verbose_name_plural = 'Documents employés'

    def __str__(self):
        return f"{self.get_doc_type_display()} - {self.employee}"
