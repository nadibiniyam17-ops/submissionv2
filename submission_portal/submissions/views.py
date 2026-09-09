import io
import os
import zipfile
from functools import wraps

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .forms import SubmissionForm, SubmissionStatusForm
from .models import Submission
from .ratelimit import rate_limit


SESSION_LAST_TITLE = 'last_submission_title'


def first_superuser():
    return User.objects.filter(is_superuser=True).order_by('pk').first()


def user_is_first_admin(user):
    first = first_superuser()
    return bool(user.is_authenticated and first and user.pk == first.pk)


def staff_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, 'submissions/login.html', {
                'next': request.get_full_path(),
            })
        if not request.user.is_staff:
            return render(request, 'submissions/login.html', {
                'error': 'This account cannot access the review dashboard.',
                'next': request.get_full_path(),
            })
        return view(request, *args, **kwargs)
    return wrapped


def safe_next_url(request):
    candidate = request.POST.get('next') or request.GET.get('next')
    if candidate and url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return None


def remember_submission_title(request, title):
    request.session[SESSION_LAST_TITLE] = title
    request.session.modified = True


def field_value(form, name, default=''):
    if name in form.data:
        return form.data.get(name, default)
    value = form[name].value()
    return default if value is None else value


def zip_pdf_name(submission, used):
    slug = slugify(submission.title) or 'submission'
    name = f'{submission.pk}-{slug}.pdf'
    index = 2
    while name in used:
        name = f'{submission.pk}-{slug}-{index}.pdf'
        index += 1
    used.add(name)
    return name


@never_cache
@ensure_csrf_cookie
def submit_paper(request):
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save()
            remember_submission_title(request, submission.title)
            return redirect('submit_success')
    else:
        form = SubmissionForm()

    return render(request, 'submissions/submit.html', {
        'form': form,
        'title_value': field_value(form, 'title'),
        'article_type_value': field_value(form, 'article_type'),
        'article_type_other_value': field_value(form, 'article_type_other'),
        'author_number_value': field_value(form, 'author_number', 1),
        'author_names_value': field_value(form, 'author_names'),
        'publication_date_value': field_value(form, 'publication_date'),
        'doi_value': field_value(form, 'doi'),
        'indexed_on_value': field_value(form, 'indexed_on'),
        'indexed_on_other_value': field_value(form, 'indexed_on_other'),
        'source_of_funding_value': field_value(form, 'source_of_funding'),
        'affiliations_value': field_value(form, 'affiliations'),
    })


@never_cache
def submit_success(request):
    title = request.session.get(SESSION_LAST_TITLE)
    return render(request, 'submissions/submitted.html', {
        'title': title,
    })


@never_cache
@ensure_csrf_cookie
def setup_admin(request):
    if User.objects.filter(is_superuser=True).exists():
        return render(request, 'submissions/setup.html', {
            'setup_locked': True,
        })

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            validate_password(password, user=User(username=username))
        except ValidationError as exc:
            return render(request, 'submissions/setup.html', {
                'error': ' '.join(exc.messages),
            })
        User.objects.create_superuser(username=username, email='', password=password)
        return redirect('admin_login')

    return render(request, 'submissions/setup.html')


@never_cache
@ensure_csrf_cookie
@rate_limit('login', settings.LOGIN_RATE_LIMIT, settings.LOGIN_RATE_WINDOW)
def admin_login(request):
    next_url = safe_next_url(request)
    rate_limited = getattr(request, 'rate_limited', False)

    if request.method == 'POST':
        if rate_limited:
            return render(request, 'submissions/login.html', {
                'error': 'Too many attempts. Wait a minute and try again.',
                'next': next_url or '',
            }, status=429)
        user = request.POST.get('username')
        pwd = request.POST.get('password')
        account = authenticate(request, username=user, password=pwd)
        if account is not None and account.is_staff:
            login(request, account)
            return redirect(next_url or 'submission_list')
        return render(request, 'submissions/login.html', {
            'error': 'Invalid credentials',
            'next': next_url or '',
        })

    return render(request, 'submissions/login.html', {
        'next': request.GET.get('next', ''),
    })


@require_POST
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@staff_required
@never_cache
@ensure_csrf_cookie
def create_admin(request):
    if not user_is_first_admin(request.user):
        return render(request, 'submissions/create_admin.html', {
            'create_forbidden': True,
        })

    error = None
    success = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm', '')

        if not username or not password:
            error = 'Username and password are required.'
        elif password != confirm:
            error = 'Passwords do not match.'
        elif User.objects.filter(username=username).exists():
            error = 'That username is already taken.'
        else:
            try:
                validate_password(password, user=User(username=username))
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            else:
                reviewer = User.objects.create_user(
                    username=username,
                    email='',
                    password=password,
                )
                reviewer.is_staff = True
                reviewer.save(update_fields=['is_staff'])
                success = f'Admin "{username}" was created.'

    return render(request, 'submissions/create_admin.html', {
        'error': error,
        'success': success,
    })


@staff_required
@never_cache
@ensure_csrf_cookie
def submission_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    submissions = Submission.objects.all().order_by('-created_at', '-pk')
    if q:
        submissions = submissions.filter(
            Q(title__icontains=q) |
            Q(author_names__icontains=q) |
            Q(doi__icontains=q)
        )
    if status in Submission.STATUS_VALUES:
        submissions = submissions.filter(status=status)

    page_obj = Paginator(submissions, settings.DASHBOARD_PAGE_SIZE).get_page(
        request.GET.get('page')
    )

    stats = Submission.objects.aggregate(
        total_count=Count('pk'),
        pending_count=Count('pk', filter=Q(status='pending')),
        under_review_count=Count('pk', filter=Q(status='under_review')),
        reviewed_count=Count('pk', filter=Q(status='reviewed')),
    )
    context = {
        'submissions': page_obj,
        'page_obj': page_obj,
        'q': q,
        'status': status,
        'can_create_admin': user_is_first_admin(request.user),
        'status_choices': Submission.STATUS_CHOICES,
        **stats,
    }
    return render(request, 'submissions/list.html', context)


@staff_required
@never_cache
@ensure_csrf_cookie
def submission_detail(request, pk):
    submission = get_object_or_404(
        Submission.objects.select_related('reviewed_by'),
        pk=pk,
    )
    if request.method == 'POST':
        form = SubmissionStatusForm(request.POST, instance=submission)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.reviewed_by = request.user
            updated.reviewed_at = timezone.now()
            updated.save()
            return redirect('submission_detail', pk=pk)

    return render(request, 'submissions/detail.html', {
        'submission': submission,
        'status_choices': Submission.STATUS_CHOICES,
    })


@staff_required
def download_pdf(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    if not submission.pdf:
        raise Http404('No PDF for this submission.')
    return FileResponse(
        submission.pdf.open('rb'),
        as_attachment=False,
        filename=os.path.basename(submission.pdf.name),
        content_type='application/pdf',
    )


@staff_required
def download_all_pdfs(request):
    buffer = io.BytesIO()
    used_names = set()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for submission in Submission.objects.exclude(pdf='').order_by('-created_at', '-pk'):
            if not submission.pdf:
                continue
            try:
                with submission.pdf.open('rb') as pdf_file:
                    content = pdf_file.read()
            except (FileNotFoundError, OSError, ValueError):
                continue
            archive.writestr(zip_pdf_name(submission, used_names), content)
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="all-submissions-pdfs.zip"'
    return response


@never_cache
@require_GET
def csrf_token_json(request):
    return JsonResponse({'csrfToken': get_token(request)})


def csrf_failure(request, reason='', exception=None):
    return render(request, 'submissions/csrf_failure.html')
