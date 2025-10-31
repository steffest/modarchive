from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm, UsernameField, UserCreationForm
from django.contrib.auth.models import User
from django.forms.widgets import EmailInput
# from sceneid.forms import UserCreationForm as BaseUserCreationForm

from homepage.models import Profile, BlacklistedDomain
from homepage.fields import BlacklistProtectedEmailField

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control', 'placeholder': 'Password'}))
    remember_me = forms.BooleanField(required=False, widget=forms.CheckboxInput())

class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control', 'placeholder': 'Current Password'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New Password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Repeat New Password'}))

class RegisterUserForm(UserCreationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))
    email = BlacklistProtectedEmailField(widget=EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'Repeat Password'}))

    def save(self, commit=False):
        user = super().save(commit=commit)

        # Test to see if a user already exists with that email address. If so, raise an error
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise EmailAddressInUseError("Email address is already in use.")

        user.is_active = False
        user.email = self.cleaned_data['email']

        user.save()
        return user

class ForgotPasswordForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class': 'form-control', 'placeholder': 'Email Address'}))

class ResetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New password'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control', 'placeholder': 'New password confirmation'}))

class EmailAddressInUseError(Exception):
    pass

class CsvUploadForm(forms.Form):
    csv_file = forms.FileField()

class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("website", "blurb",)

class AccountSettingsForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Account email")

    class Meta:
        model = Profile
        fields = ("email", "enable_notifications", "enable_shoutwall", "enable_shoutwall_notifications")
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Prepopulate the email field from the user model
        if self.user:
            self.fields["email"].initial = self.user.email
    
    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()

        # Must not be blank
        if not email:
            raise forms.ValidationError("Email address cannot be blank.")

        # Must be unique among users (excluding current user)
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already in use.")

        # Must not be from a blacklisted domain
        domain = email.split("@")[-1]
        if BlacklistedDomain.objects.filter(domain__iexact=domain).exists():
            raise forms.ValidationError("Email addresses from this domain are not allowed.")

        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()

        # Update user email if changed
        email = self.cleaned_data.get("email")
        if self.user and email and self.user.email != email:
            self.user.email = email
            self.user.save(update_fields=["email"])

        return profile

# class SceneIDUserCreationForm(BaseUserCreationForm):
#     username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control', 'placeholder': 'Username'}))