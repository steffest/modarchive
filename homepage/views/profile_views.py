from django.db.models import Prefetch
from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from homepage.forms import UpdateProfileForm, AccountSettingsForm
from homepage.views.common_views import PageNavigationListView

from homepage.models import Profile, Message
from songs.models import Song
from interactions import models as i_models

class ProfileView(DetailView):
    model = Profile
    template_name = 'profile/profile_overview.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        
        if profile and profile.enable_shoutwall:
            most_recent_messages = profile.profile_messages.order_by('-create_date')[:10]
            context['most_recent_messages'] = most_recent_messages
    
        context['profile'] = profile
        context['artist'] = getattr(profile, 'artist', None)
        return context

class ProfileSongsView(PageNavigationListView):
    model = Song
    template_name = "profile/profile_songs.html"

    def get(self, request, *args, **kwargs):
        # Retrieve the profile first
        self.profile = Profile.objects.get(pk=self.kwargs["pk"])

        # If the profile has no artist, redirect to its profile page
        if not hasattr(self.profile, "artist") or self.profile.artist is None:
            return redirect(reverse("view_profile", args=[self.profile.pk]))

        # Otherwise continue with normal processing
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        self.artist = self.profile.artist
        return self.artist.songs.all().order_by('-create_date')
    
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["profile"] = self.profile
        if hasattr(self.profile, 'artist'):
            context_data['artist'] = self.profile.artist
        return context_data

class ProfileCommentsView(PageNavigationListView):
    model = i_models.Comment
    template_name = 'profile/profile_comments.html'
    paginate_by = 40
    context_object_name = 'comments'

    def get(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.profile.comment_set.all().order_by('-create_date')

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['profile'] = self.profile
        return context_data

class ProfileFavoritesView(PageNavigationListView):
    model = i_models.Favorite
    template_name = 'profile/profile_favorites.html'
    paginate_by = 50
    context_object_name = 'favorites'

    def get(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        return super().get(request, *args, **kwargs)

    def get_queryset(self, **kwargs):
        return self.profile.favorite_set.all().order_by('-create_date')

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['profile'] = self.profile
        return context_data

class ProfileMessagesView(PageNavigationListView):
    model = Message
    template_name = "profile/profile_messages.html"
    paginate_by = 20
    context_object_name = 'messages'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # If shoutwall is disabled, redirect to their main profile page
        if (self.profile.enable_shoutwall == False):
            return redirect('view_profile', self.profile.pk)

        return response

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['profile'] = self.profile
        return context_data

    def get_queryset(self):
        # Get the artist object first
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])

        # Handle artists that might not have a profile
        if self.profile is None:
            return Message.objects.none()

        # Fetch top-level messages for that profile
        top_level_messages = (
            Message.objects.filter(profile=self.profile, thread_starter__isnull=True)
            .select_related('sender', 'profile')
            .prefetch_related(
                Prefetch(
                    'all_replies',  # default reverse name for thread_starter unless you set related_name
                    queryset=Message.objects.select_related('sender').order_by('create_date'),
                    to_attr='thread_replies'  # attach replies as .thread_replies on each top-level message
                )
            )
            .order_by('-create_date')
        )

        return top_level_messages

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
