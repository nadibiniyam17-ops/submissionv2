from django.db import migrations, models


def fill_blank_required_fields(apps, schema_editor):
    Submission = apps.get_model('submissions', 'Submission')
    Submission.objects.filter(doi__isnull=True).update(doi='')
    Submission.objects.filter(source_of_funding__isnull=True).update(source_of_funding='')


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0006_scale_indexes_unique_pdf'),
    ]

    operations = [
        migrations.RunPython(fill_blank_required_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='submission',
            name='tracking_code',
        ),
        migrations.AlterField(
            model_name='submission',
            name='doi',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='submission',
            name='source_of_funding',
            field=models.CharField(max_length=255),
        ),
    ]
