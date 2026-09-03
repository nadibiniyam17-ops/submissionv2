from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from .models import Submission
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import ensure_csrf_cookie


def first_superuser():
    return User.objects.filter(is_superuser=True).order_by('pk').first()


def user_is_first_admin(user):
    first = first_superuser()
    return bool(user.is_authenticated and first and user.pk == first.pk)


def value_or_other(posted, custom):
    if posted == 'Other':
        custom = (custom or '').strip()
        return custom if custom else 'Other'
    return posted


@ensure_csrf_cookie
def submit_paper(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        article_type = value_or_other(
            request.POST.get('article_type'),
            request.POST.get('article_type_other'),
        )
        author_number = request.POST.get('author_number', 1)
        author_names = request.POST.get('author_names')
        publication_date = request.POST.get('publication_date')
        doi = request.POST.get('doi', '')
        indexed_on = value_or_other(
            request.POST.get('indexed_on'),
            request.POST.get('indexed_on_other'),
        )
        source_of_funding = request.POST.get('source_of_funding')
        affiliations = request.POST.get('affiliations')
        pdf = request.FILES.get('pdf')

        submission = Submission.objects.create(
            title=title,
            article_type=article_type,
            author_number=author_number,
            author_names=author_names,
            publication_date=publication_date,
            doi=doi,
            indexed_on=indexed_on,
            source_of_funding=source_of_funding,
            affiliations=affiliations,
            pdf=pdf,
            status='pending'
        )
        return redirect('submit_success', pk=submission.pk)

    return render(request, 'submissions/submit.html')


def submit_success(request, pk):
    submission = get_object_or_404(Submission, pk=pk)
    return render(request, 'submissions/submitted.html', {
        'title': submission.title,
    })


@ensure_csrf_cookie
def setup_admin(request):
    if User.objects.filter(is_superuser=True).exists():
        return render(request, 'submissions/setup.html', {
            'setup_locked': True,
        }, status=403)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            validate_password(password)
        except ValidationError as exc:
            return render(request, 'submissions/setup.html', {
                'error': ' '.join(exc.messages),
            })
        User.objects.create_superuser(username=username, email='', password=password)
        return redirect('admin_login')

    return render(request, 'submissions/setup.html')


@ensure_csrf_cookie
def admin_login(request):
    if request.method == 'POST':
        user = request.POST.get('username')
        pwd = request.POST.get('password')
        account = authenticate(request, username=user, password=pwd)
        if account is not None:
            login(request, account)
            return redirect('submission_list')
        return render(request, 'submissions/login.html', {'error': 'Invalid credentials'})

    return render(request, 'submissions/login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required(login_url='/login/')
@ensure_csrf_cookie
def create_admin(request):
    if not user_is_first_admin(request.user):
        return render(request, 'submissions/create_admin.html', {
            'create_forbidden': True,
        }, status=403)

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
                validate_password(password)
            except ValidationError as exc:
                error = ' '.join(exc.messages)
            else:
                User.objects.create_superuser(username=username, email='', password=password)
                success = f'Admin "{username}" was created.'

    return render(request, 'submissions/create_admin.html', {
        'error': error,
        'success': success,
    })


@login_required(login_url='/login/')
@ensure_csrf_cookie
def submission_list(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    # Show oldest submissions first so the list order matches PK order (1,2,3,...).
    submissions = Submission.objects.all().order_by('pk')
    if q:
        submissions = submissions.filter(
            Q(title__icontains=q) |
            Q(author_names__icontains=q) |
            Q(doi__icontains=q)
        )
    if status in ['pending', 'under_review', 'reviewed']:
        submissions = submissions.filter(status=status)

    all_subs = Submission.objects.all()
    context = {
        'submissions': submissions,
        'q': q,
        'status': status,
        'total_count': all_subs.count(),
        'pending_count': all_subs.filter(status='pending').count(),
        'under_review_count': all_subs.filter(status='under_review').count(),
        'reviewed_count': all_subs.filter(status='reviewed').count(),
        'can_create_admin': user_is_first_admin(request.user),
    }
    return render(request, 'submissions/list.html', context)


@login_required(login_url='/login/')
@ensure_csrf_cookie
def submission_detail(request, pk):
    submission = get_object_or_404(Submission, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['pending', 'under_review', 'reviewed']:
            submission.status = new_status
            submission.save()
            return redirect('submission_detail', pk=pk)

    return render(request, 'submissions/detail.html', {'submission': submission})
