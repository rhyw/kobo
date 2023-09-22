# -*- coding: utf-8 -*-

import warnings
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.generic.edit import ProcessFormView, FormMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

class UsersAclMixin:
    def _check_acl_permission(self, request):
        permission_type = getattr(settings, "USERS_ACL_PERMISSION", "")

        if permission_type == "authenticated" and not request.user.is_authenticated:
            return "authenticated"
        elif permission_type == "staff" and not request.user.is_staff:
            return "staff"
        return ""

    def dispatch(self, request, *args, **kwargs):
        permission_type = self._check_acl_permission(request)

        if permission_type in ["authenticated", "staff"]:
            if permission_type == "authenticated":
                message = "Permission denied: you must login to access."
            else:
                message = "Permission denied: only staff users can access."
            template = get_template("base.html")
            context = {
                "error_message": message
            }
            return HttpResponse(
                template.render(context, request=request),
                status=403
            )

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset=get_user_model().objects.order_by("username"),
        permission_type = self._check_acl_permission(self.request)
        if permission_type in ["authenticated", "staff"]:
            if permission_type == "authenticated" and not self.request.user.is_authenticated:
                return queryset.none()
            elif permission_type == "staff" and not self.request.user.is_staff:
                return queryset.none()
        return queryset  # Return all objects if user is staff

class ExtraListView(UsersAclMixin, ListView):
    paginate_by = getattr(settings, "PAGINATE_BY", None)
    extra_context = None
    title = None

    def get_context_data(self, **kwargs):
        context = super(ExtraListView, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            context.update(self.extra_context)
        if self.title is not None:
            context['title'] = self.title
        return context


class ExtraDetailView(DetailView):
    extra_context = None
    title = None

    def get_context_data(self, **kwargs):
        context = super(ExtraDetailView, self).get_context_data(**kwargs)
        if self.extra_context is not None:
            context.update(self.extra_context)
        if self.title is not None:
            context['title'] = self.title
        return context

class SearchView(FormMixin, ProcessFormView, ExtraListView):
    """
    Appends GET variables to the context. Used for paginated searches.
    In settings.py you can set optional parameter PAGINATE_BY which will be
    used as a default value.

    Useful fields:
        form_class - form_class is expected that it implements get_query(request)
                     method which returns queryset for displaying in list. It
                     also can return just query (Q()) which is then applied
                     to base queryset/model of class
    """

    object_list = []

    # ProcessFormView needs redefine get to use form data
    def get(self,  request,  *args,  **kwargs):
        return self.post(request,  *args,  **kwargs)

    # same goes for FormMixin
    def get_form_kwargs(self):
        kwargs = {'initial': self.get_initial()}
        if self.request.method == 'GET':
            kwargs['data'] = self.request.GET
        return kwargs

    def form_invalid(self, form):
        self.queryset = []
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form):
        query = form.get_query(self.request)
        if isinstance(query, QuerySet):
            self.queryset = query
        else:
            self.queryset = self.get_queryset().filter(query)
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        kwargs['object_list'] = self.get_queryset()
        context = super(SearchView, self).get_context_data(**kwargs)

        get_vars = self.request.GET.copy()
        if "page" in get_vars:
            del get_vars["page"]
        if len(get_vars) > 0:
            get_vars = "&%s" % get_vars.urlencode()
        else:
            get_vars = ""
        context['get_vars'] = get_vars
        return context

def object_list(request, **kwargs):
    warnings.warn('object_list is deprecated, please use ExtraListView or SearchView in future.')
    if 'form' in kwargs:
        return SearchView.as_view(**kwargs)(request)
    else:
        return ExtraListView.as_view(**kwargs)(request)
