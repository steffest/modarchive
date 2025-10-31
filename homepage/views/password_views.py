from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView, PasswordResetConfirmView, PasswordResetView, PasswordResetCompleteView
from django.shortcuts import render
from django.urls import reverse_lazy

from homepage.forms import ChangePasswordForm, ForgotPasswordForm, ResetPasswordForm
from homepage.views.homepage_views import RedirectAuthenticatedUserMixin

class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'account_management/change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('profile')
    login_url='login'

class PasswordResetView(RedirectAuthenticatedUserMixin, PasswordResetView):
    template_name = 'password_reset/forgot_password.html'
    form_class = ForgotPasswordForm
    email_template_name = 'password_reset/password_reset_email.html'
    subject_template_name = 'password_reset/password_reset_email_subject.txt'
    from_email = 'donotreply@modarchive.org'

class PasswordResetConfirmView(RedirectAuthenticatedUserMixin, PasswordResetConfirmView):
    template_name = 'password_reset/reset_password.html'
    form_class=ResetPasswordForm

class PasswordResetCompleteView(RedirectAuthenticatedUserMixin, PasswordResetCompleteView):
    template_name='password_reset/password_reset_complete.html'

def password_reset_done(request):
    return render(request, 'password_reset/password_reset_done.html')