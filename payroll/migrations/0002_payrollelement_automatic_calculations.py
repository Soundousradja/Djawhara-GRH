from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payrollelement',
            name='late_deduction',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Retenue pour retard'),
        ),
        migrations.AddField(
            model_name='payrollelement',
            name='late_minutes',
            field=models.PositiveIntegerField(default=0, verbose_name='Minutes de retard'),
        ),
        migrations.AddField(
            model_name='payrollelement',
            name='overtime_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Montant des heures supplementaires'),
        ),
    ]
