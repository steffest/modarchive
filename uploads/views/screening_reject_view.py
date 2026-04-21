import os
import re
from typing import Any
from datetime import date

from django.conf import settings
from django.db import transaction, Error
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.views.generic import FormView
from django.shortcuts import render, redirect
from django.contrib import messages
from django.forms import CharField, HiddenInput
from django.urls import reverse_lazy
from django.utils import timezone

from uploads import forms, constants
from uploads.models import NewSong, RejectedSong

class ScreeningRejectView(PermissionRequiredMixin, FormView):
    template_name="screening_reject.html"
    permission_required = 'uploads.can_approve_songs'
    form_class = forms.RejectionForm
    success_url = reverse_lazy('screening_index')

    def form_valid(self, form):
        song_ids = self.extra_context.get('song_ids', [])

        for song_id in song_ids:
            self.finalize_rejection(song_id, form)

        return super().form_valid(form)

    @transaction.atomic
    def finalize_rejection(self, song_id, form):
        new_song = NewSong.objects.get(pk=song_id)

        previous_dir = os.path.join(settings.NEW_FILE_DIR, f'{new_song.filename}.zip')
        new_dir = os.path.join(settings.REJECTED_FILE_DIR, f'{date.today().strftime("%Y%m%d")}-{new_song.filename}.zip')
        try:
            os.rename(previous_dir, new_dir)
        except OSError:
            return

        try:
            RejectedSong.objects.create(
                reason=form.cleaned_data['rejection_reason'],
                message=form.cleaned_data['message'],
                is_temporary=form.cleaned_data['is_temporary'],
                rejected_by=self.request.user.profile,
                rejected_date=timezone.now(),
                filename=new_song.filename,
                filename_unzipped=new_song.filename_unzipped,
                title=new_song.title,
                format=new_song.format,
                file_size=new_song.file_size,
                channels=new_song.channels,
                instrument_text=new_song.instrument_text,
                comment_text=new_song.comment_text,
                hash=new_song.hash,
                pattern_hash=new_song.pattern_hash,
                artist_from_file=new_song.artist_from_file,
                uploader_profile=new_song.uploader_profile,
                uploader_ip_address=new_song.uploader_ip_address,
                is_by_uploader=new_song.is_by_uploader,
            )

            new_song.delete()
        except Error:
            os.rename(new_dir, previous_dir)
            transaction.set_rollback(True)

    def validate_song_ids(self, raw_song_ids, request):
        if not (raw_song_ids and re.match(r'^(\d+,)*\d+$', raw_song_ids)):
            messages.error(request, constants.REJECTION_REQUIRES_IDS)
            return False

        song_ids = [id.strip() for id in raw_song_ids.split(',') if id.strip()]
        new_song_queryset = NewSong.objects.filter(id__in=song_ids)

        # All songs in queryset must be claimed by the current user
        if new_song_queryset.exclude(claimed_by=request.user.profile).exists():
            messages.error(request, constants.REJECTION_ALL_SONGS_MUST_BE_CLAIMED)
            return False

        claimed_queryset = new_song_queryset.filter(claimed_by=request.user.profile)

        if len(claimed_queryset) == 0:
            messages.error(request, constants.REJECTION_REQUIRES_IDS)
            return False

        return claimed_queryset

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        raw_song_ids = form.data.get('song_ids', '')

        claimed_queryset = self.validate_song_ids(raw_song_ids, request)
        if claimed_queryset is False:
            return redirect('screening_index')

        self.extra_context = {'song_ids': claimed_queryset.values_list('id', flat=True)}
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        raw_song_ids = request.GET.get('song_ids', '')

        claimed_queryset = self.validate_song_ids(raw_song_ids, request)
        if claimed_queryset is False:
            return redirect('screening_index')

        # Add a hidden field to the form with the list of song_ids
        claimed_queryset_values = claimed_queryset.values_list('id', flat=True)
        hidden_field = CharField(widget=HiddenInput(), initial=','.join(map(str, claimed_queryset_values)))
        self.form_class.base_fields['song_ids'] = hidden_field

        context = self.get_context_data()
        context['songs'] = claimed_queryset

        return render(request, self.template_name, context)
