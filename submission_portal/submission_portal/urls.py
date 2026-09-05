"""
URL configuration for submission_portal project.

PDFs are not served from /media/. Admins download them through download_pdf.
The built-in Django admin site is not mounted, so user creation stays on /setup/
and the first-admin rule.
"""
from django.urls import include, path

urlpatterns = [
    path('', include('submissions.urls')),
]
