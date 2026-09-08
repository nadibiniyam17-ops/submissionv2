import secrets
import uuid
from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import IntegrityError, models, transaction


TRACKING_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generate_tracking_code():
    body = ''.join(secrets.choice(TRACKING_CODE_ALPHABET) for _ in range(6))
    return f'RS-{body}'


def normalize_tracking_code(raw):
    code = (raw or '').strip().upper().replace(' ', '')
    if code.startswith('RS') and not code.startswith('RS-') and len(code) > 2:
        code = 'RS-' + code[2:]
    return code


def pdf_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    if suffix != '.pdf':
        suffix = '.pdf'
    return f'submissions_pdfs/{uuid.uuid4().hex}{suffix}'


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under review'),
        ('reviewed', 'Reviewed'),
    ]
    STATUS_VALUES = [value for value, _label in STATUS_CHOICES]

    title = models.CharField(max_length=255)
    article_type = models.CharField(max_length=100)
    author_number = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    author_names = models.TextField()
    publication_date = models.DateField()
    doi = models.CharField(max_length=255, blank=True, null=True)
    pdf = models.FileField(
        upload_to=pdf_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    indexed_on = models.CharField(max_length=100)
    source_of_funding = models.CharField(max_length=255, blank=True, null=True)
    affiliations = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_code = models.CharField(max_length=16, unique=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reviewed_submissions',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='submission_status_idx'),
            models.Index(fields=['created_at'], name='submission_created_idx'),
        ]

    def save(self, *args, **kwargs):
        if self.tracking_code:
            return super().save(*args, **kwargs)

        last_error = None
        for _ in range(20):
            self.tracking_code = generate_tracking_code()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                last_error = exc
                self.tracking_code = ''
        raise RuntimeError('Could not generate a unique tracking code.') from last_error

    def __str__(self):
        return self.title
