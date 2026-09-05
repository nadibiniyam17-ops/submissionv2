import secrets

from django.db import migrations, models


TRACKING_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def fill_tracking_codes(apps, schema_editor):
    Submission = apps.get_model('submissions', 'Submission')
    used = set(
        Submission.objects.exclude(tracking_code__isnull=True)
        .exclude(tracking_code='')
        .values_list('tracking_code', flat=True)
    )
    for submission in Submission.objects.all():
        if submission.tracking_code:
            continue
        while True:
            body = ''.join(secrets.choice(TRACKING_CODE_ALPHABET) for _ in range(6))
            code = f'RS-{body}'
            if code not in used:
                used.add(code)
                submission.tracking_code = code
                submission.save(update_fields=['tracking_code'])
                break


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0003_status_pending_under_review_reviewed'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='tracking_code',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.RunPython(fill_tracking_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='submission',
            name='tracking_code',
            field=models.CharField(max_length=16, unique=True),
        ),
    ]
