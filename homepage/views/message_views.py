from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404, redirect
from homepage import models, forms

class CreateMessageView(PermissionRequiredMixin, FormView):
    form_class = forms.MessageForm
    permission_required = 'homepage.add_message'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        self.profile = get_object_or_404(models.Profile, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        sender = self.request.user.profile
        reply_to = form.cleaned_data.get("reply_to")

        if not self.profile.enable_shoutwall:
            messages.error(self.request, "Cannot send message to user with messages disabled")
            return redirect("view_profile", pk=self.profile.pk)

        msg = form.save(commit=False)
        msg.profile = self.profile
        msg.sender = sender

        if reply_to:
            # Invalid if the profile of the reply does not match the profile of the new message
            if reply_to.profile != msg.profile:
                messages.error(self.request, "Message must be posted to the same profile as the message it responds to")
                return redirect("view_profile_messages", pk=self.profile.pk)
            
            # reply_recipient is always the sender of the message you're replying to
            msg.reply_recipient = reply_to.sender
            msg.thread_starter = (
                reply_to.thread_starter if reply_to.thread_starter else reply_to
            )
        else:
            msg.reply_recipient = None
            msg.thread_starter = None

        msg.save()
        return redirect("view_profile_messages", pk=self.profile.pk)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.profile
        return context
