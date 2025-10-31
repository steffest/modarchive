from django.views.generic import ListView

class PageNavigationListView(ListView):
    paginate_by = 25
    context_object_name = 'songs'

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        paginator = context_data.get('paginator')
        page = context_data.get('page_obj')
        if paginator and page:
            context_data['page_range'] = paginator.get_elided_page_range(number=page.number, on_ends=1)
            context_data['full_page_range'] = paginator.page_range
        return context_data
