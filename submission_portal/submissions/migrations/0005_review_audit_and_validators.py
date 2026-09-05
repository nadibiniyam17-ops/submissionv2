import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('submissions', '0004_submission_tracking_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='reviewed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='submission',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_submissions',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='submission',
            name='author_number',
            field=models.IntegerField(
                default=1,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AlterField(
            model_name='submission',
            name='pdf',
            field=models.FileField(
                upload_to='submissions_pdfs/',
                validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])],
            ),
        ),
    ]
