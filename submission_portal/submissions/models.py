from django.db import models

# Create your models here.
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
