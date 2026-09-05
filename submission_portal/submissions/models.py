import secrets

from django.db import models

TRACKING_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def generate_tracking_code():
    body = ''.join(secrets.choice(TRACKING_CODE_ALPHABET) for _ in range(6))
    return f'RS-{body}'


def normalize_tracking_code(raw):
    code = (raw or '').strip().upper().replace(' ', '')
    if code.startswith('RS') and not code.startswith('RS-') and len(code) > 2:
        code = 'RS-' + code[2:]
    return code


class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under review'),
        ('reviewed', 'Reviewed'),
    ]

    title = models.CharField(max_length=255)
    article_type = models.CharField(max_length=100)
    author_number = models.IntegerField(default=1)
    author_names = models.TextField()
    publication_date = models.DateField()
    doi = models.CharField(max_length=255, blank=True, null=True)
    pdf = models.FileField(upload_to='submissions_pdfs/')
    indexed_on = models.CharField(max_length=100)
    source_of_funding = models.CharField(max_length=255, blank=True, null=True)
    affiliations = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_code = models.CharField(max_length=16, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.tracking_code:
            for _ in range(20):
                code = generate_tracking_code()
                if not Submission.objects.filter(tracking_code=code).exists():
                    self.tracking_code = code
                    break
            else:
                raise RuntimeError('Could not generate a unique tracking code.')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
