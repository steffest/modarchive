from datetime import timedelta
from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models.query import QuerySet
from django.utils import timezone

from homepage.views.common_views import PageNavigationListView
from uploads.forms import ScreeningQueueFilterForm
from uploads.models import NewSong
from uploads import constants

class ScreeningIndexView(PermissionRequiredMixin, PageNavigationListView):
    model = NewSong
    template_name="screening_index.html"
    permission_required = 'uploads.can_approve_songs'
    context_object_name = 'new_songs'
    paginate_by = 25
    filter_options = {
        constants.HIGH_PRIORITY_FILTER: constants.HIGH_PRIORITY_FILTER_DESCRIPTION,
        constants.LOW_PRIORITY_FILTER: constants.LOW_PRIORITY_FILTER_DESCRIPTION,
        constants.BY_UPLOADER_FILTER: constants.BY_UPLOADER_FILTER_DESCRIPTION,
        constants.MY_SCREENING_FILTER: constants.MY_SCREENING_FILTER_DESCRIPTION,
        constants.OTHERS_SCREENING_FILTER: constants.OTHERS_SCREENING_FILTER_DESCRIPTION,
        constants.PRE_SCREENED_FILTER: constants.PRE_SCREENED_FILTER_DESCRIPTION,
        constants.PRE_SCREENED_AND_RECOMMENDED_FILTER: constants.PRE_SCREENED_AND_RECOMMENDED_FILTER_DESCRIPTION,
        constants.NEEDS_SECOND_OPINION_FILTER: constants.NEEDS_SECOND_OPINION_FILTER_DESCRIPTION,
        constants.POSSIBLE_DUPLICATE_FILTER: constants.POSSIBLE_DUPLICATE_FILTER_DESCRIPTION,
        constants.UNDER_INVESTIGATION_FILTER: constants.UNDER_INVESTIGATION_FILTER_DESCRIPTION
    }

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['filter_options'] = self.filter_options
        context['filter'] = self.request.GET.get('filter', constants.HIGH_PRIORITY_FILTER)

        if context['filter'] in [
            constants.HIGH_PRIORITY_FILTER,
            constants.LOW_PRIORITY_FILTER,
            constants.BY_UPLOADER_FILTER,
            constants.NEEDS_SECOND_OPINION_FILTER,
            constants.POSSIBLE_DUPLICATE_FILTER,
            constants.UNDER_INVESTIGATION_FILTER
        ]:
            context['actions'] = [
                constants.CLAIM_ACTION
            ]
        elif context['filter'] == constants.MY_SCREENING_FILTER:
            context['actions'] = [
                constants.PRE_SCREEN_ACTION,
                constants.PRE_SCREEN_AND_RECOMMEND_ACTION,
                constants.NEEDS_SECOND_OPINION_ACTION,
                constants.POSSIBLE_DUPLICATE_ACTION,
                constants.UNDER_INVESTIGATION_ACTION,
                constants.REJECT_ACTION,
                constants.UNCLAIM_ACTION,
                constants.CLEAR_FLAG_ACTION
            ]
        elif context['filter'] == constants.OTHERS_SCREENING_FILTER:
            context['actions'] = []
        elif context['filter'] == constants.PRE_SCREENED_FILTER:
            context['actions'] = [constants.APPROVE_ACTION, constants.APPROVE_AND_FEATURE_ACTION, constants.REJECT_ACTION, constants.CLEAR_FLAG_ACTION]
        elif context['filter'] == constants.PRE_SCREENED_AND_RECOMMENDED_FILTER:
            context['actions'] = [constants.APPROVE_ACTION, constants.APPROVE_AND_FEATURE_ACTION, constants.REJECT_ACTION, constants.CLEAR_FLAG_ACTION]

        context['form'] = ScreeningQueueFilterForm(initial={'filter': context['filter']})

        return context

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()

        # Get filter option from request
        filter_option = self.request.GET.get('filter', constants.HIGH_PRIORITY_FILTER)

        if filter_option not in self.filter_options:
            filter_option = constants.HIGH_PRIORITY_FILTER

        # Before doing anything, clear any song claims that are older than 48 hours
        NewSong.objects.filter(claim_date__lte=timezone.now() - timedelta(hours=48)).update(claimed_by=None, claim_date=None)

        # High priority is defined as any song where it's not uploaded by the placeholder account (id of 1)
        match filter_option:
            case constants.HIGH_PRIORITY_FILTER:
                queryset = queryset.filter(uploader_profile__user_id__isnull=False).filter(claimed_by=None).filter(flag=None)
            case constants.LOW_PRIORITY_FILTER:
                queryset = queryset.filter(uploader_profile__user_id=None).filter(claimed_by=None).filter(flag=None)
            case constants.BY_UPLOADER_FILTER:
                queryset = queryset.filter(is_by_uploader=True).filter(claimed_by=None).filter(flag=None)
            case constants.MY_SCREENING_FILTER:
                queryset = queryset.filter(claimed_by=self.request.user.profile)
            case constants.OTHERS_SCREENING_FILTER:
                queryset = queryset.exclude(claimed_by=None).exclude(claimed_by=self.request.user.profile)
            case constants.PRE_SCREENED_FILTER:
                queryset = queryset.filter(flag=NewSong.Flags.PRE_SCREENED)
            case constants.PRE_SCREENED_AND_RECOMMENDED_FILTER:
                queryset = queryset.filter(flag=NewSong.Flags.PRE_SCREENED_PLUS)
            case constants.NEEDS_SECOND_OPINION_FILTER:
                queryset = queryset.filter(flag=NewSong.Flags.NEEDS_SECOND_OPINION)
            case constants.POSSIBLE_DUPLICATE_FILTER:
                queryset = queryset.filter(flag=NewSong.Flags.POSSIBLE_DUPLICATE)
            case constants.UNDER_INVESTIGATION_FILTER:
                queryset = queryset.filter(flag=NewSong.Flags.UNDER_INVESTIGATION)

        return queryset.order_by('-create_date')
