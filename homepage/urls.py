from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from homepage.views import password_views, registration_views
from homepage.views.bulk_upload_view import BulkUploadView
from homepage.views.homepage_views import LoginView, HomePageView
from homepage.views.legacy_redirect_view import LegacyUrlRedirectionView
from homepage.views.profile_views import ProfileView, UpdateProfileView, ProfileFavoritesView, ProfileCommentsView, AccountSettingsView

urlpatterns = [
    # Basic homepage
    path('', HomePageView.as_view(), {}, 'home'),

    # Basic auth functionality
    path('login/', LoginView.as_view(), name='login', kwargs={'next': '/'}),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('change_password/', password_views.PasswordChangeView.as_view(), name='change_password'),

    # Account registration
    path('register/', registration_views.register, {}, 'register'),
    path('register_done/', TemplateView.as_view(template_name='registration/register_done.html'), {}, 'register_done'),
    path('register_fail/', TemplateView.as_view(template_name='registration/register_fail.html'), {}, 'register_fail'),
    path('activate_account/<uidb64>/<token>', registration_views.activate, name='activate_account'),
    path('account_activation_complete/', registration_views.AccountActivationCompleteView.as_view(), {}, 'account_activation_complete'),
    path('activation_error/', TemplateView.as_view(template_name='registration/account_activation_error.html'), {}, 'activation_error'),

    # Password reset
    path('forgot_password/', password_views.PasswordResetView.as_view(), {}, 'forgot_password'),
    path('password_reset_done/', password_views.password_reset_done, {}, 'password_reset_done'),
    path('password_reset/<uidb64>/<token>/', password_views.PasswordResetConfirmView.as_view(), name='password_reset'),
    path('password_reset_complete/', password_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Legacy URL redirects
    re_path('(?P<php_file>[a-zA-Z]+).php/', LegacyUrlRedirectionView.as_view(), name='login_php'),

    # Bulk uploader tool
    path('bulk_upload/', BulkUploadView.as_view(), {}, 'bulk_upload'),

    # Profiles
    path('profiles/<int:pk>/', ProfileView.as_view(), {}, 'view_profile'),
    path('profiles/<int:pk>/comments', ProfileCommentsView.as_view(), {}, 'view_profile_comments'),
    path('profiles/<int:pk>/favorites', ProfileFavoritesView.as_view(), {}, 'view_profile_favorites'),
    path('profiles/update/', UpdateProfileView.as_view(), {}, 'update_profile'),
    path('account_settings', AccountSettingsView.as_view(), {}, 'account_settings'),
]

handler404 = 'homepage.views.homepage_views.page_not_found_view'
