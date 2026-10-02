from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='role',
            field=models.CharField(
                choices=[
                    ('DG', 'Directeur Général'),
                    ('GERANT', 'Gérant'),
                    ('RH', 'Responsable Ressources Humaines'),
                    ('CHEF', "Chef d'atelier"),
                    ('COMPTABLE', 'Comptable / Responsable Finance'),
                    ('LIMITE', 'Utilisateur limité'),
                ],
                default='LIMITE',
                max_length=20,
            ),
        ),
    ]
