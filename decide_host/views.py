# -*- coding: utf-8 -*-
# -*- mode: python -*-

import ipaddress
import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from drf_link_header_pagination import LinkHeaderCursorPagination
from django_filters import rest_framework as filters

from decide_host import __version__, api_version
from decide_host import models
from decide_host import serializers

logger = logging.getLogger(__name__)


class LinkHeaderCursorPaginationByTimestamp(LinkHeaderCursorPagination):
    ordering = "-time"


@api_view(["HEAD", "GET"])
def api_root(request, format=None):
    urls = {
        "info": reverse("api-info", request=request, format=format),
        "events": reverse("event-list", request=request, format=format),
        "trials": reverse("trial-list", request=request, format=format),
        "controllers": reverse("controller-list", request=request, format=format),
        "subjects": reverse("subject-list", request=request, format=format),
    }
    headers = {
        "Link": ", ".join(f'<{uri}>; rel="{name}"' for name, uri in urls.items())
    }
    return Response(urls, headers=headers)


@api_view(["GET"])
def api_info(request, format=None):
    return Response(
        {
            "host": "django-decide-host",
            "host_version": __version__,
            "api_version": api_version,
        }
    )


@api_view(["GET"])
def notfound(request, format=None):
    return Response({"detail": "not found"}, status=status.HTTP_404_NOT_FOUND)


class IsAuthorizedSubnetOrReadOnly(permissions.BasePermission):
    message = "read-only access"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            ip_addr = request.META["REMOTE_ADDR"]
            for subnet in settings.DECIDE_HOST.get("READWRITE_SUBNETS", []):
                if ipaddress.ip_address(ip_addr) in ipaddress.ip_network(subnet):
                    return True
            return False


class DataFieldFilterMixin(object):
    """Provides filtering based on components of the data JSONField"""

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # this could be a little dangerous b/c we're letting the user design queries
        mq = {k: v for k, v in self.request.GET.items() if k.startswith("data__")}
        return qs.filter(**mq)


class EventFilter(filters.FilterSet):
    addr = filters.CharFilter(
        field_name="addr__name", label="addr", lookup_expr="iexact"
    )
    name = filters.CharFilter(
        field_name="name__name", label="name", lookup_expr="iexact"
    )
    date = filters.DateFromToRangeFilter(field_name="time")

    class Meta:
        model = models.Event
        fields = {"time": ["exact", "date"]}


class TrialFilter(filters.FilterSet):
    addr = filters.CharFilter(
        field_name="addr__name", label="addr", lookup_expr="iexact"
    )
    name = filters.CharFilter(
        field_name="name__name", label="name", lookup_expr="iexact"
    )
    subject = filters.CharFilter(
        field_name="subject__name", label="subject", lookup_expr="iexact"
    )
    nocomment = filters.BooleanFilter(
        field_name="data__comment", label="nocomment", lookup_expr="isnull"
    )
    date = filters.DateFromToRangeFilter(field_name="time")

    class Meta:
        model = models.Trial
        fields = {"time": ["exact", "date"]}


class EventList(DataFieldFilterMixin, generics.ListCreateAPIView):
    queryset = models.Event.objects.with_names()
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EventFilter
    pagination_class = LinkHeaderCursorPaginationByTimestamp
    permission_classes = (IsAuthorizedSubnetOrReadOnly,)


class TrialList(DataFieldFilterMixin, generics.ListCreateAPIView):
    """Records of trials and trial-related comments.

    This endpoint returns a list of records from the database of trial records.
    Use query parameters to restrict the number of items to a reasonable subset.

    Basic filters: `name` (of the procedure), `addr` (of the controller), and
    `subject`.

    Date-based filters: `time__date` for a specific date, `date_before` and
    `date_after` to specify a range. Ranges are exclusive. Format dates as `YYYY-MM-DD`.

    Exclude comments with the query `nocomment=true`.

    You can filter on other fields of the record, but these need to be prefaced
    by `data__` due to the way they're stored in the database. For example, to
    restrict returned records to ones in which `correct` was `True`, add the
    query `data__correct=True`.

    Multiple queries produce a more restrictive filter.

    Example: "?subject=P24&date_after=2022-02-01&date_before=2022-02-28"

    """

    queryset = models.Trial.objects.with_names()
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TrialFilter
    pagination_class = LinkHeaderCursorPaginationByTimestamp
    permission_classes = (IsAuthorizedSubnetOrReadOnly,)


class ControllerList(generics.ListAPIView):
    queryset = models.Controller.objects.with_counts().order_by("-last_event_time")
    serializer_class = serializers.ControllerSerializer


class ControllerDetail(generics.RetrieveAPIView):
    lookup_field = "name"
    queryset = models.Controller.objects.with_counts()
    serializer_class = serializers.ControllerSerializer

    def retrieve(self, request, **kwargs):
        response = super().retrieve(request, **kwargs)
        # add link to trials in header
        uri = reverse("controller-event-list", args=[kwargs["name"]], request=request)
        response["Link"] = f'<{uri}>; rel="events"'
        return response


class ControllerEventList(DataFieldFilterMixin, generics.ListAPIView):
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = LinkHeaderCursorPaginationByTimestamp
    filterset_class = EventFilter

    def get_object(self):
        return get_object_or_404(models.Controller, name=self.kwargs["addr"])

    def get_queryset(self):
        addr = self.get_object()
        return addr.event_set.with_names()


class SubjectList(generics.ListAPIView):
    queryset = models.Subject.objects.with_counts().order_by("-last_trial_time")
    serializer_class = serializers.SubjectSerializer


class SubjectDetail(generics.RetrieveAPIView):
    lookup_field = "name"
    queryset = models.Subject.objects.with_counts()
    serializer_class = serializers.SubjectSerializer

    def retrieve(self, request, **kwargs):
        response = super().retrieve(request, **kwargs)
        # add link to trials in header
        uri = reverse("subject-trial-list", args=[kwargs["name"]], request=request)
        response["Link"] = f'<{uri}>; rel="trials"'
        return response


class SubjectTrialList(DataFieldFilterMixin, generics.ListAPIView):
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = LinkHeaderCursorPaginationByTimestamp
    filterset_class = TrialFilter

    def get_object(self):
        return get_object_or_404(models.Subject, name=self.kwargs["subject"])

    def get_queryset(self):
        subj = self.get_object()
        return subj.trial_set.with_names()
