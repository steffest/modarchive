from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic.base import TemplateView

from homepage.forms import EmailAddressInUseError, RegisterUserForm
from homepage.functions import is_recaptcha_success
from homepage.tokens import account_activation_token
from homepage.views.homepage_views import RedirectAuthenticatedUserMixin

class AccountActivationCompleteView(RedirectAuthenticatedUserMixin, TemplateView):
    template_name = 'registration/account_activation_complete.html'

def register(request):
    # Logged-in users should not be able to view the registration page or submit a request.
    if (request.user.is_authenticated):
        return redirect("home")

    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            if not is_recaptcha_success(request.POST.get('g-recaptcha-response')):
                return redirect("register_fail")

            try:
                user = form.save()
                subject = "Active your ModArchive account"

                message = render_to_string('registration/account_activation_email.html', {
                    'user': user,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'domain': get_current_site(request).domain
                })

                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")

            except EmailAddressInUseError:
                user = User.objects.get(email = form.cleaned_data['email'])
                subject = "ModArchive security warning"
                message = "A user attempted to register a ModArchive account with your email address."
                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")
            
        else:
            return render(request=request, template_name='registration/register.html', context={"form":form})

    form = RegisterUserForm
    return render(request, 'registration/register.html', context={'form': form, 'recaptcha_site_key': settings.GOOGLE_RECAPTCHA_SITE_KEY})

@transaction.atomic
def activate(request, uidb64, token):
    if (request.user.is_authenticated):
        return redirect("home")

    User = get_user_model()
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None:
        return redirect('activation_error')
    elif user.is_active:
        # Take no action if user is already active
        return redirect('home')
    
    user.is_active = True
    user.save()
    return redirect('account_activation_complete')