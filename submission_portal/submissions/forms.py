from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Submission


ARTICLE_TYPE_CHOICES = [
    ('Full length research paper', 'Full length research paper'),
    ('Review article', 'Review article'),
    ('Short communication', 'Short communication'),
    ('Case study', 'Case study'),
    ('Other', 'Other'),
]

INDEXED_ON_CHOICES = [
    ('Scopus', 'Scopus'),
    ('Web of Science', 'Web of Science'),
    ('Nationally accredited', 'Nationally accredited'),
    ('PubMed', 'PubMed'),
    ('Other', 'Other'),
]

def validate_pdf_file(upload):
    name = (getattr(upload, 'name', '') or '').lower()
    if not name.endswith('.pdf'):
        raise ValidationError('Upload a PDF file.')
    content_type = getattr(upload, 'content_type', '') or ''
    if content_type and content_type not in {'application/pdf', 'application/x-pdf'}:
        raise ValidationError('Upload a PDF file.')
    size = getattr(upload, 'size', 0) or 0
    if size > settings.MAX_PDF_BYTES:
        raise ValidationError('PDF must be 20 MB or smaller.')
    pointer = upload.tell()
    header = upload.read(5)
    upload.seek(pointer)
    if header != b'%PDF-':
        raise ValidationError('That file is not a valid PDF.')


def value_or_other(posted, custom):
    if posted == 'Other':
        custom = (custom or '').strip()
        return custom if custom else 'Other'
    return posted


class SubmissionForm(forms.ModelForm):
    article_type = forms.ChoiceField(choices=ARTICLE_TYPE_CHOICES)
    indexed_on = forms.ChoiceField(choices=INDEXED_ON_CHOICES)
    article_type_other = forms.CharField(required=False, max_length=100)
    indexed_on_other = forms.CharField(required=False, max_length=100)
    doi = forms.CharField(max_length=255)
    source_of_funding = forms.CharField(max_length=255)

    class Meta:
        model = Submission
        fields = [
            'title',
            'article_type',
            'author_number',
            'author_names',
            'publication_date',
            'doi',
            'indexed_on',
            'source_of_funding',
            'affiliations',
            'pdf',
        ]

    def clean_title(self):
        title = (self.cleaned_data.get('title') or '').strip()
        if not title:
            raise ValidationError('Enter the title of your paper.')
        return title

    def clean_author_names(self):
        names = (self.cleaned_data.get('author_names') or '').strip()
        if not names:
            raise ValidationError('Enter the author names.')
        return names

    def clean_doi(self):
        doi = (self.cleaned_data.get('doi') or '').strip()
        if not doi:
            raise ValidationError('Enter a DOI.')
        return doi

    def clean_source_of_funding(self):
        funding = (self.cleaned_data.get('source_of_funding') or '').strip()
        if not funding:
            raise ValidationError('Enter a source of funding.')
        return funding

    def clean_affiliations(self):
        affiliations = (self.cleaned_data.get('affiliations') or '').strip()
        if not affiliations:
            raise ValidationError('Enter an affiliation.')
        return affiliations

    def clean_pdf(self):
        pdf = self.cleaned_data.get('pdf')
        if not pdf:
            raise ValidationError('Upload a PDF file.')
        validate_pdf_file(pdf)
        return pdf

    def clean(self):
        cleaned = super().clean()
        article_type = cleaned.get('article_type')
        if article_type == 'Other':
            custom = (cleaned.get('article_type_other') or '').strip()
            if not custom:
                self.add_error('article_type_other', 'Enter your article type.')
            else:
                cleaned['article_type'] = custom
        indexed_on = cleaned.get('indexed_on')
        if indexed_on == 'Other':
            custom = (cleaned.get('indexed_on_other') or '').strip()
            if not custom:
                self.add_error('indexed_on_other', 'Enter your indexing source.')
            else:
                cleaned['indexed_on'] = custom
        return cleaned

    def save(self, commit=True):
        submission = super().save(commit=False)
        submission.status = 'pending'
        if commit:
            submission.save()
        return submission


class SubmissionStatusForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['status']
