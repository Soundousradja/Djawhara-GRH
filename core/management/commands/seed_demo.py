import datetime
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile
from employees.models import Workshop, Employee
from contracts.models import Contract
from attendance.models import AttendanceRecord
from payroll.models import PayrollElement


class Command(BaseCommand):
    help = "Crée des données de démonstration pour Djawhara GRH (ateliers, employés, utilisateurs, pointages)."

    def handle(self, *args, **options):
        self.stdout.write("Création des ateliers...")
        workshops = {}
        for name in ["Bonbons", "Confiseries", "Emballage", "Administration"]:
            w, _ = Workshop.objects.get_or_create(name=name)
            workshops[name] = w

        self.stdout.write("Création des utilisateurs de démonstration...")
        demo_users = [
            ('directeur', 'Directeur', 'Général', Profile.ROLE_DG, None),
            ('rh', 'Responsable', 'RH', Profile.ROLE_RH, None),
            ('chef_bonbons', 'Chef', 'Bonbons', Profile.ROLE_CHEF, workshops['Bonbons']),
            ('comptable', 'Comptable', 'Finance', Profile.ROLE_COMPTABLE, None),
        ]
        for username, first, last, role, workshop in demo_users:
            user, created = User.objects.get_or_create(
                username=username, defaults={'first_name': first, 'last_name': last}
            )
            if created:
                user.set_password('djawhara2026')
                user.save()
            user.profile.role = role
            user.profile.workshop = workshop
            user.profile.save()

        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser('admin', 'admin@djawhara.local', 'djawhara2026')
            self.stdout.write(self.style.SUCCESS("Superutilisateur 'admin' créé (mot de passe: djawhara2026)"))

        self.stdout.write("Création d'employés de démonstration...")
        first_names = ["Karim", "Amina", "Yacine", "Sara", "Mounir", "Nadia", "Riad", "Lina", "Farid", "Hana"]
        last_names = ["Bensalem", "Cherif", "Meziane", "Boudiaf", "Haddad", "Zerrouki", "Aissani", "Guerroudj"]
        positions = ["Ouvrier de production", "Emballeuse", "Opérateur machine", "Chef d'équipe", "Agent qualité"]

        employees = []
        for i in range(20):
            fn, ln = random.choice(first_names), random.choice(last_names)
            emp, created = Employee.objects.get_or_create(
                first_name=fn, last_name=f"{ln}{i}",
                defaults=dict(
                    workshop=random.choice(list(workshops.values())),
                    position=random.choice(positions),
                    hire_date=datetime.date.today() - datetime.timedelta(days=random.randint(60, 1500)),
                    status=Employee.STATUS_ACTIVE,
                    phone=f"055512{1000+i}",
                )
            )
            employees.append(emp)
            if created:
                Contract.objects.get_or_create(
                    employee=emp, contract_type=random.choice([Contract.TYPE_CDI, Contract.TYPE_CDD]),
                    defaults=dict(
                        start_date=emp.hire_date,
                        end_date=None if random.random() > 0.3 else datetime.date.today() + datetime.timedelta(days=random.randint(5, 60)),
                        base_salary=random.choice([30000, 35000, 40000, 45000]),
                        status=Contract.STATUS_ACTIVE,
                    )
                )

        self.stdout.write("Génération des pointages des 14 derniers jours...")
        for i in range(14):
            day = datetime.date.today() - datetime.timedelta(days=i)
            for emp in employees:
                r = random.random()
                if r < 0.8:
                    status = AttendanceRecord.STATUS_PRESENT
                elif r < 0.88:
                    status = AttendanceRecord.STATUS_LATE
                elif r < 0.94:
                    status = AttendanceRecord.STATUS_ABSENT_JUSTIFIED
                else:
                    status = AttendanceRecord.STATUS_ABSENT_UNJUSTIFIED
                AttendanceRecord.objects.get_or_create(
                    employee=emp, date=day,
                    defaults=dict(
                        status=status, workshop=emp.workshop,
                        minutes_late=random.randint(5, 30) if status == AttendanceRecord.STATUS_LATE else 0,
                    )
                )

        self.stdout.write(self.style.SUCCESS("Données de démonstration créées avec succès."))
        self.stdout.write("Comptes de démonstration (mot de passe: djawhara2026) :")
        for username, *_ in demo_users:
            self.stdout.write(f"  - {username}")
        self.stdout.write("  - admin (superutilisateur / accès Django admin)")
