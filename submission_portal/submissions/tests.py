import tempfile
from datetime import date
from io import BytesIO
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from submissions.forms import value_or_other
from submissions.models import Submission


PDF_BYTES = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n'


def csrf_token_from(response):
    html = response.content.decode()
    marker = 'name="csrfmiddlewaretoken" value="'
    start = html.find(marker)
    if start < 0:
        return ''
    start += len(marker)
    end = html.find('"', start)
    return html[start:end]


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


def create_submission(**overrides):
    values = {
        'title': 'A study of sample papers',
        'article_type': 'Review article',
        'author_names': 'Ada Lovelace',
        'publication_date': date(2026, 1, 15),
        'doi': '10.1234/example',
        'indexed_on': 'Scopus',
        'source_of_funding': 'Grant',
        'affiliations': 'Example University',
        'pdf': make_pdf(),
    }
    values.update(overrides)
    return Submission.objects.create(**values)


class HelperTests(TestCase):
    def test_value_or_other(self):
        self.assertEqual(value_or_other(None, 'ignored'), None)
        self.assertEqual(value_or_other('Other', '  custom  '), 'custom')
        self.assertEqual(value_or_other('Other', '   '), 'Other')
        self.assertEqual(value_or_other('Scopus', 'custom'), 'Scopus')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SubmitTests(TestCase):
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
        self.assertTrue(submission.pdf.name.startswith('submissions_pdfs/'))
        self.assertTrue(submission.pdf.name.endswith('.pdf'))
        self.assertNotIn('paper.pdf', submission.pdf.name)

    def test_success_page_uses_session_not_public_id(self):
        self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(), 'pdf': make_pdf()},
        )
        submission = Submission.objects.get()
        success = self.client.get(reverse('submit_success'))
        self.assertContains(success, submission.title)
        self.assertEqual(self.client.get(f'/submitted/{submission.pk}/').status_code, 404)

    def test_success_page_without_session_does_not_leak_title(self):
        create_submission(title='Secret paper', pdf=make_pdf('secret.pdf'))
        other = self.client.get(reverse('submit_success'))
        self.assertContains(other, 'Submitted successfully')
        self.assertNotContains(other, 'Secret paper')

    def test_required_fields_are_rejected_when_blank(self):
        response = self.client.post(
            reverse('submit_paper'),
            data={**submission_payload(doi='', source_of_funding=''), 'pdf': make_pdf()},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertContains(response, 'Please correct the errors below.')

    def test_form_fields_are_numbered_and_required(self):
        html = self.client.get(reverse('submit_paper')).content.decode()
        self.assertIn('1. Title of the Paper', html)
        self.assertIn('7. Indexed On', html)
        self.assertIn('8. Source of Funding', html)
        self.assertIn('9. Affiliation', html)
        self.assertIn('10. Upload PDF', html)
        self.assertEqual(html.count('class="required"'), 10)
        self.assertNotIn('check the status', html.lower())

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
        submission = create_submission(title='Private PDF', pdf=make_pdf('private.pdf'))
        self.assertEqual(self.client.get(f'/media/{submission.pdf.name}').status_code, 404)
        pdf = self.client.get(reverse('download_pdf', args=[submission.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertContains(pdf, 'Admin login')

    def test_status_page_is_gone(self):
        self.assertEqual(self.client.get('/status/').status_code, 404)
        self.assertEqual(self.client.get('/status').status_code, 404)


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser('firstadmin', '', 'StrongPass123')

    def test_setup_stays_usable_when_admin_exists(self):
        response = self.client.get(reverse('setup_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Setup is closed')
        self.assertNotIn(response.status_code, {303, 403})
        slashless = self.client.get('/setup')
        self.assertEqual(slashless.status_code, 200)
        self.assertNotIn(slashless.status_code, {301, 303, 403})

    def test_anonymous_dashboard_shows_login(self):
        response = self.client.get(reverse('submission_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin login')
        self.assertNotIn(response.status_code, {303, 403})

    def test_non_staff_user_cannot_open_dashboard(self):
        user = User.objects.create_user('viewer', password='StrongPass123')
        self.client.force_login(user)
        response = self.client.get(reverse('submission_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This account cannot access the review dashboard.')
        self.assertNotIn(response.status_code, {303, 403})

    def test_second_admin_cannot_create_admins(self):
        reviewer = User.objects.create_user('reviewer', password='StrongPass123', is_staff=True)
        self.client.force_login(reviewer)
        response = self.client.get(reverse('create_admin'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Not allowed')
        self.assertNotIn(response.status_code, {303, 403})

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
        self.submission = create_submission(title='Audit paper', pdf=make_pdf('audit.pdf'))

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
        html = response.content.decode()
        submitted = html.find('Submitted:')
        pdf = html.find('View/Download the PDF')
        status = html.find('class="statusform"')
        self.assertLess(submitted, pdf)
        self.assertLess(pdf, status)
        self.assertNotContains(response, 'Tracking code')

    def test_staff_can_download_pdf(self):
        response = self.client.get(reverse('download_pdf', args=[self.submission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_list_shows_latest_first_with_overview_columns(self):
        create_submission(title='Older paper', pdf=make_pdf('older.pdf'))
        newer = create_submission(title='Newer paper', pdf=make_pdf('newer.pdf'))
        response = self.client.get(reverse('submission_list'))
        html = response.content.decode()
        self.assertLess(html.find('Newer paper'), html.find('Older paper'))
        self.assertContains(response, 'Article type')
        self.assertContains(response, 'Number of authors')
        self.assertContains(response, 'Publication date')
        self.assertContains(response, 'DOI')
        self.assertContains(response, 'Indexed source')
        self.assertContains(response, 'Source of funding')
        self.assertContains(response, 'Download all PDFs')
        self.assertNotContains(response, 'Tracking code')
        self.assertEqual(newer.pk, Submission.objects.latest('pk').pk)

    def test_staff_can_download_all_pdfs(self):
        create_submission(title='Second paper', pdf=make_pdf('second.pdf'))
        response = self.client.get(reverse('download_all_pdfs'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        with ZipFile(BytesIO(response.content)) as archive:
            names = archive.namelist()
        self.assertEqual(len(names), 2)
        self.assertTrue(all(name.endswith('.pdf') for name in names))

    def test_anonymous_cannot_download_all_pdfs(self):
        self.client.logout()
        response = self.client.get(reverse('download_all_pdfs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin login')


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class StressAndCsrfTests(TestCase):
    def setUp(self):
        cache.clear()
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_repeated_submits_then_setup_is_not_an_error(self):
        for index in range(5):
            page = self.csrf_client.get(reverse('submit_paper'))
            token = csrf_token_from(page)
            self.assertTrue(token)
            response = self.csrf_client.post(
                reverse('submit_paper'),
                data={
                    **submission_payload(title=f'Stress paper {index}'),
                    'csrfmiddlewaretoken': token,
                    'pdf': make_pdf(f'stress-{index}.pdf'),
                },
            )
            self.assertEqual(response.status_code, 302)
            follow = self.csrf_client.get(response['Location'])
            self.assertEqual(follow.status_code, 200)

        setup = self.csrf_client.get(reverse('setup_admin'))
        self.assertEqual(setup.status_code, 200)
        self.assertContains(setup, 'Admin setup')

        created = self.csrf_client.post(reverse('setup_admin'), {
            'username': 'setupadmin',
            'password': 'StrongPass123',
            'csrfmiddlewaretoken': csrf_token_from(setup),
        })
        self.assertEqual(created.status_code, 302)
        self.assertTrue(User.objects.filter(username='setupadmin').exists())

        locked = self.csrf_client.get(reverse('setup_admin'))
        self.assertEqual(locked.status_code, 200)
        self.assertContains(locked, 'Setup is closed')

    def test_csrf_failure_is_a_usable_page(self):
        self.csrf_client.get(reverse('submit_paper'))
        response = self.csrf_client.post(
            reverse('submit_paper'),
            {
                **submission_payload(),
                'csrfmiddlewaretoken': 'not-a-real-token',
                'pdf': make_pdf(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sorry, please try again')
        self.assertContains(response, 'error-x')
        self.assertNotContains(response, 'CSRF verification failed')
        self.assertNotContains(response, 'Check status')
        self.assertNotIn(response.status_code, {303, 403})

    def test_form_pages_are_not_cached(self):
        response = self.client.get(reverse('submit_paper'))
        self.assertIn('no-store', response['Cache-Control'])
        setup = self.client.get(reverse('setup_admin'))
        self.assertIn('no-store', setup['Cache-Control'])

    def test_csrf_endpoint_issues_a_usable_token(self):
        page = self.csrf_client.get(reverse('submit_paper'))
        self.assertTrue(csrf_token_from(page))
        issued = self.csrf_client.get(reverse('csrf_token'))
        self.assertEqual(issued.status_code, 200)
        token = issued.json()['csrfToken']
        self.assertTrue(token)
        response = self.csrf_client.post(
            reverse('submit_paper'),
            data={
                **submission_payload(title='Token refresh paper'),
                'csrfmiddlewaretoken': token,
                'pdf': make_pdf('token-refresh.pdf'),
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_login_does_not_break_later_posts_when_token_is_refreshed(self):
        User.objects.create_superuser('firstadmin', '', 'StrongPass123')
        stale_page = self.csrf_client.get(reverse('submit_paper'))
        stale_token = csrf_token_from(stale_page)
        login_page = self.csrf_client.get(reverse('admin_login'))
        login_response = self.csrf_client.post(reverse('admin_login'), {
            'username': 'firstadmin',
            'password': 'StrongPass123',
            'csrfmiddlewaretoken': csrf_token_from(login_page),
        })
        self.assertEqual(login_response.status_code, 302)

        stale_post = self.csrf_client.post(reverse('submit_paper'), {
            **submission_payload(title='Stale token paper'),
            'csrfmiddlewaretoken': stale_token,
            'pdf': make_pdf('stale.pdf'),
        })
        self.assertEqual(stale_post.status_code, 200)
        self.assertContains(stale_post, 'Sorry, please try again')

        fresh = self.csrf_client.get(reverse('csrf_token')).json()['csrfToken']
        ok_post = self.csrf_client.post(reverse('submit_paper'), {
            **submission_payload(title='Fresh token paper'),
            'csrfmiddlewaretoken': fresh,
            'pdf': make_pdf('fresh.pdf'),
        })
        self.assertEqual(ok_post.status_code, 302)
