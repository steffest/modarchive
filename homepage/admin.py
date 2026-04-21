from django.contrib import admin
from django import forms

from . import models

@admin.register(models.Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("pk", "display_name")
    search_fields = ("display_name", )

class MessageAdminForm(forms.ModelForm):
    class Meta:
        model = models.Message
        fields = '__all__'
        help_texts = {
            'profile': 'The profile that the message was sent to',
            'sender': 'The profile that posted the message',
            'reply_to': 'The message that this message is a reply to',
            'reply_recipient': 'The profile that this message is a reply to',
            'thread_starter': 'The top post of the message thread'
        }

@admin.register(models.Message)
class MessageAdmin(admin.ModelAdmin):
    form = MessageAdminForm
    fields = ("profile", "sender", "text", "reply_recipient", "reply_to", "thread_starter")
    autocomplete_fields = ['profile', 'sender', 'reply_recipient', 'reply_to', 'thread_starter']
    search_fields = ['text']

@admin.register(models.News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("profile", "headline")
    exclude = ("profile",)

    def save_model(self, request, obj, form, change):
        obj.profile = request.user.profile
        super().save_model(request, obj, form, change)