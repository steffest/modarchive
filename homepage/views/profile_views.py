from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from homepage.forms import UpdateProfileForm, AccountSettingsForm

from homepage.models import Profile

class ProfileView(DetailView):
    model = Profile
    template_name = 'profile.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if (hasattr(self.object, 'artist')):
            return redirect('view_artist', self.object.artist.id)

        return response

class ProfileCommentsView(DetailView):
    model = Profile
    template_name = 'profile_comments.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if (hasattr(self.object, 'artist')):
            return redirect('view_artist_comments', self.object.artist.id)

        return response

class ProfileFavoritesView(DetailView):
    model = Profile
    template_name = 'profile_favorites.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if (hasattr(self.object, 'artist')):
            return redirect('view_artist_favorites', self.object.artist.id)

        return response

class UpdateProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = request.user.profile
            form = UpdateProfileForm(instance=profile)
            return render(request, 'update_profile.html', {'form': form, 'profile': profile})
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")

    def post(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
        
        form = UpdateProfileForm(request.POST, instance=profile)
        
        if form.is_valid():
            form.save()
            return redirect(reverse('view_profile', kwargs = {'pk': profile.id}))
        else:
            return render(request, 'update_profile.html', {'form': form, 'profile': profile})
        
class AccountSettingsView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = request.user.profile
            form = AccountSettingsForm(instance=profile, user=request.user)
            return render(request, 'account_settings.html', {'form': form, 'profile': profile})
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
    
    def post(self, request):
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
    
        form = AccountSettingsForm(request.POST, instance=profile, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Your settings have been updated.")
            return redirect(reverse('account_settings'))
        else:
            return render(request, 'account_settings.html', {'form': form, 'profile': profile})
