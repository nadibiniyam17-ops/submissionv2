import importlib.util
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.apps import apps
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from submissions.forms import value_or_other


def load_fill_tracking_codes():
    path = Path(__file__).resolve().parent / 'migrations' / '0004_submission_tracking_code.py'
    spec = importlib.util.spec_from_file_location('tracking_code_migration', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fill_tracking_codes
from submissions.models import (
    TRACKING_CODE_ALPHABET,
    Submission,
    generate_tracking_code,
    normalize_tracking_code,
)


PDF_BYTES = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'


def make_pdf(name='paper.pdf', content=PDF_BYTES, content_type='application/pdf'):
    return SimpleUploadedFile(name, content, content_type=content_type)


def submission_payload(**overrides):
    data = {
        'title': 'A study of sample papers',
        'article_type': 'Review article',
        'author_number': '1',
        'author_names': 'Ada Lovelace',
        'publication_date': '2026-01-15',
        'doi': '10.1234/example',
        'indexed_on': 'Scopus',
        'source_of_funding': 'Grant',
        'affiliations': 'Example University',
    }
    data.update(overrides)
    return data


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TrackingCodeTests(TestCase):
    def test_generate_tracking_code_format(self):
        code = generate_tracking_code()
        self.assertTrue(code.startswith('RS-'))
        self.assertEqual(len(code), 9)
        self.assertTrue(all(char in TRACKING_CODE_ALPHABET for char in code[3:]))

    def test_normalize_tracking_code(self):
        self.assertEqual(normalize_tracking_code(' rs 8f3k2p '), 'RS-8F3K2P')
        self.assertEqual(normalize_tracking_code('RS-8F3K2P'), 'RS-8F3K2P')
        self.assertEqual(normalize_tracking_code(''), '')

    def test_save_assigns_unique_code(self):
        first = Submission.objects.create(
            title='One',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('one.pdf'),
        )
        second = Submission.objects.create(
            title='Two',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('two.pdf'),
        )
        self.assertTrue(first.tracking_code.startswith('RS-'))
        self.assertTrue(second.tracking_code.startswith('RS-'))
        self.assertNotEqual(first.tracking_code, second.tracking_code)

    def test_save_retries_on_integrity_error(self):
        existing = Submission.objects.create(
            title='Existing',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('existing.pdf'),
        )
        codes = [existing.tracking_code, existing.tracking_code, 'RS-NEWID1']
        with patch('submissions.models.generate_tracking_code', side_effect=codes):
            created = Submission.objects.create(
                title='Retry',
                article_type='Review article',
                author_names='Ada',
                publication_date=date(2026, 1, 1),
                indexed_on='Scopus',
                affiliations='Uni',
                pdf=make_pdf('retry.pdf'),
            )
        self.assertEqual(created.tracking_code, 'RS-NEWID1')

    def test_fill_tracking_codes_backfills_empty_values(self):
        submission = Submission.objects.create(
            title='Backfill',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('backfill.pdf'),
        )
        Submission.objects.filter(pk=submission.pk).update(tracking_code='')
        load_fill_tracking_codes()(apps, None)
        submission.refresh_from_db()
        self.assertTrue(submission.tracking_code.startswith('RS-'))
        self.assertEqual(len(submission.tracking_code), 9)


class HelperTests(TestCase):
    def test_value_or_other(self):
        self.assertEqual(value_or_other(None, 'ignored'), None)
        self.assertEqual(value_or_other('Other', '  custom  '), 'custom')
        self.assertEqual(value_or_other('Other', '   '), 'Other')
        self.assertEqual(value_or_other('Scopus', 'custom'), 'Scopus')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SubmitAndStatusTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_submit_creates_pending_submission(self):
        response = self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(), 'pdf': make_pdf()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('submit_success'))
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.get()
        self.assertEqual(submission.status, 'pending')
        self.assertTrue(submission.tracking_code.startswith('RS-'))

    def test_success_page_uses_session_not_public_id(self):
        self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(), 'pdf': make_pdf()},
        )
        submission = Submission.objects.get()
        success = self.client.get(reverse('submit_success'))
        self.assertContains(success, submission.tracking_code)
        self.assertEqual(self.client.get(f'/submitted/{submission.pk}/').status_code, 404)

    def test_success_page_without_session_does_not_leak_code(self):
        Submission.objects.create(
            title='Secret paper',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('secret.pdf'),
        )
        other = self.client.get(reverse('submit_success'))
        self.assertContains(other, 'Confirmation unavailable')
        self.assertNotContains(other, 'Secret paper')

    def test_status_lookup(self):
        submission = Submission.objects.create(
            title='Lookup paper',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('lookup.pdf'),
        )
        missing = self.client.post(reverse('check_status'), {'tracking_code': 'RS-XXXXXX'})
        self.assertContains(missing, 'No submission found for that code.')
        found = self.client.post(reverse('check_status'), {'tracking_code': submission.tracking_code})
        self.assertContains(found, 'Lookup paper')
        self.assertContains(found, 'Pending')

    def test_status_page_rate_limit(self):
        for _ in range(10):
            response = self.client.post(reverse('check_status'), {'tracking_code': 'RS-XXXXXX'})
            self.assertEqual(response.status_code, 200)
        limited = self.client.post(reverse('check_status'), {'tracking_code': 'RS-XXXXXX'})
        self.assertEqual(limited.status_code, 429)
        self.assertContains(limited, 'Too many attempts', status_code=429)

    def test_status_page_has_no_submit_link(self):
        response = self.client.get(reverse('check_status'))
        self.assertNotContains(response, 'Submit a paper')
        self.assertNotContains(response, 'page-nav')

    def test_invalid_date_does_not_500(self):
        response = self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(publication_date='not-a-date'), 'pdf': make_pdf()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertContains(response, 'Please correct the errors below.')

    def test_non_pdf_upload_is_rejected(self):
        fake = make_pdf(name='payload.pdf', content=b'MZ executable', content_type='application/pdf')
        response = self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(), 'pdf': fake},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertContains(response, 'not a valid PDF')

    def test_media_url_is_not_public(self):
        submission = Submission.objects.create(
            title='Private PDF',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('private.pdf'),
        )
        self.assertEqual(self.client.get(f'/media/{submission.pdf.name}').status_code, 404)
        self.assertEqual(self.client.get(reverse('download_pdf', args=[submission.pk])).status_code, 302)

    def test_status_url_follows_request_host(self):
        response = self.client.get(reverse('submit_paper'), HTTP_HOST='127.0.0.1:8000')
        self.assertContains(response, 'http://127.0.0.1:8000/status/')

    def test_status_url_sits_outside_form_card(self):
        html = self.client.get(reverse('submit_paper')).content.decode()
        form_end = html.find('</form>')
        card_end = html.find('</div>', form_end)
        note = html.find('class="status-note"')
        self.assertGreater(form_end, 0)
        self.assertGreater(note, card_end)
        self.assertNotContains(self.client.get(reverse('submit_paper')), 'Submit a paper')


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser('firstadmin', '', 'StrongPass123')

    def test_setup_returns_403_when_admin_exists(self):
        response = self.client.get(reverse('setup_admin'))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_dashboard_redirects_to_login(self):
        response = self.client.get(reverse('submission_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('admin_login'), response['Location'])

    def test_non_staff_user_cannot_open_dashboard(self):
        user = User.objects.create_user('viewer', password='StrongPass123')
        self.client.force_login(user)
        response = self.client.get(reverse('submission_list'))
        self.assertEqual(response.status_code, 403)

    def test_second_admin_cannot_create_admins(self):
        reviewer = User.objects.create_user('reviewer', password='StrongPass123', is_staff=True)
        self.client.force_login(reviewer)
        response = self.client.get(reverse('create_admin'))
        self.assertEqual(response.status_code, 403)

    def test_login_honors_safe_next(self):
        response = self.client.post(
            reverse('admin_login') + '?next=/dashboard/admins/create/',
            {'username': 'firstadmin', 'password': 'StrongPass123', 'next': '/dashboard/admins/create/'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/dashboard/admins/create/')

    def test_logout_rejects_get(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('admin_logout')).status_code, 405)
        response = self.client.post(reverse('admin_logout'))
        self.assertEqual(response.status_code, 302)

    def test_login_rate_limit(self):
        for _ in range(5):
            self.client.post(reverse('admin_login'), {'username': 'nope', 'password': 'nope'})
        limited = self.client.post(reverse('admin_login'), {'username': 'nope', 'password': 'nope'})
        self.assertEqual(limited.status_code, 429)

    def test_password_similarity_uses_username(self):
        User.objects.all().delete()
        response = self.client.post(reverse('setup_admin'), {
            'username': 'nadim',
            'password': 'nadim123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.exists())
        self.assertContains(response, 'too similar')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReviewAuditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('firstadmin', '', 'StrongPass123')
        self.client.force_login(self.admin)
        self.submission = Submission.objects.create(
            title='Audit paper',
            article_type='Review article',
            author_names='Ada',
            publication_date=date(2026, 1, 1),
            indexed_on='Scopus',
            affiliations='Uni',
            pdf=make_pdf('audit.pdf'),
        )

    def test_status_change_records_reviewer(self):
        response = self.client.post(
            reverse('submission_detail', args=[self.submission.pk]),
            {'status': 'reviewed'},
        )
        self.assertEqual(response.status_code, 302)
        self.submission.refresh_from_db()
        self.assertEqual(self.submission.status, 'reviewed')
        self.assertEqual(self.submission.reviewed_by, self.admin)
        self.assertIsNotNone(self.submission.reviewed_at)

    def test_detail_shows_created_at(self):
        response = self.client.get(reverse('submission_detail', args=[self.submission.pk]))
        self.assertContains(response, 'Submitted:')

    def test_staff_can_download_pdf(self):
        response = self.client.get(reverse('download_pdf', args=[self.submission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
