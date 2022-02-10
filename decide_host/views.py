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
from django_filters import rest_framework as filters
from drf_link_header_pagination import LinkHeaderPagination

from decide_host import __version__, api_version
from decide_host import models
from decide_host import serializers

logger = logging.getLogger(__name__)

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'info': reverse('api-info', request=request, format=format),
        'events': reverse('event-list', request=request, format=format),
        'trials': reverse('trial-list', request=request, format=format),
        'controllers': reverse('controller-list', request=request, format=format),
        'subjects': reverse('subject-list', request=request, format=format),
    })


@api_view(['GET'])
def api_info(request, format=None):
    return Response({
        'host': 'django-decide-host',
        'host_version': __version__,
        'api_version': api_version
    })


@api_view(['GET'])
def notfound(request, format=None):
    return Response({'detail': 'not found'}, status=status.HTTP_404_NOT_FOUND)


class IsAuthorizedSubnetOrReadOnly(permissions.BasePermission):
    message = "read-only access"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        else:
            ip_addr = request.META['REMOTE_ADDR']
            for subnet in settings.DECIDE_HOST.get("READWRITE_SUBNETS", []):
                if ipaddress.ip_address(ip_addr) in ipaddress.ip_network(subnet):
                    return True
            return False


class DataFieldFilterMixin(object):
    """ Provides filtering based on components of the data JSONField """
    def filter_queryset(self, queryset):
        qs = super(DataFieldFilterMixin, self).filter_queryset(queryset)
        # this could be a little dangerous b/c we're letting the user design queries
        mq = {k: v for k, v in self.request.GET.items() if k.startswith("data__")}
        return qs.filter(**mq)


class EventFilter(filters.FilterSet):
    addr = filters.CharFilter(field_name="addr__name", label="addr", lookup_expr="icontains")
    name = filters.CharFilter(field_name="name__name", label="name", lookup_expr="icontains")
    date = filters.DateFromToRangeFilter(field_name="time")
    datetime = filters.DateTimeFromToRangeFilter(field_name="time")

    class Meta:
        model = models.Event
        fields = {
            'time': ['exact', 'date']
        }


class TrialFilter(filters.FilterSet):
    addr = filters.CharFilter(field_name="addr__name", label="addr", lookup_expr="icontains")
    name = filters.CharFilter(field_name="name__name", label="name", lookup_expr="icontains")
    subject = filters.CharFilter(field_name="subject__name", label="subject",
                                 lookup_expr="icontains")
    nocomment = filters.BooleanFilter(field_name="data__comment", label="nocomment",
                                      lookup_expr="isnull")
    date = filters.DateFromToRangeFilter(field_name="time")
    datetime = filters.DateTimeFromToRangeFilter(field_name="time")

    class Meta:
        model = models.Trial
        fields = {
            'time': ['exact', 'date']
        }


class FilterOrLinkHeaderPagination(LinkHeaderPagination):

    def paginate_queryset(self, queryset, request, view=None):
        if 'no_page' in request.query_params:
            return None
        else:
            return super().paginate_queryset(queryset, request, view)


class EventList(DataFieldFilterMixin, generics.ListCreateAPIView):
    queryset = models.Event.objects.all()
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = EventFilter
    pagination_class = LinkHeaderPagination
    permission_classes = (IsAuthorizedSubnetOrReadOnly,)


class TrialList(DataFieldFilterMixin, generics.ListCreateAPIView):
    """Records of trials and trial-related comments.

    This endpoint returns a list of records from the database of trial records.
    Use query parameters to restrict the number of items to a reasonable subset.

    Basic filters: `name` (of the procedure), `addr` (of the controller), and
    `subject`.

    Date-based filters: `time__date` for a specific date, `date_before` and
    `date_after` to specify a range. Ranges are inclusive. Format dates as `YYYY-MM-DD`.

    Time-based filters: `datetime_before` and `datetime_after` to specify a
    range. Format datetimes as `YYYY-MM-DD hh:mm`

    Exclude comments with the query `nocomment=true`.

    You can filter on other fields of the record, but these need to be prefaced
    by `data__` due to the way they're stored in the database. For example, to
    restrict returned records to ones in which `correct` was `True`, add the
    query `data__correct=True`.

    Multiple queries produce a more restrictive filter.

    Example: "?subject=P24&date_after=2022-02-01&date_before=2022-02-28"

    """

    queryset = models.Trial.objects.all()
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TrialFilter
    pagination_class = FilterOrLinkHeaderPagination
    permission_classes = (IsAuthorizedSubnetOrReadOnly,)


class ControllerList(generics.ListAPIView):
    queryset = models.Controller.objects.all()
    serializer_class = serializers.ControllerSerializer


class ControllerDetail(generics.RetrieveAPIView):
    lookup_field = "name"
    queryset = models.Controller.objects.all()
    serializer_class = serializers.ControllerSerializer


class ControllerEventList(DataFieldFilterMixin, generics.ListAPIView):
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = EventFilter
    pagination_class = LinkHeaderPagination

    def get_object(self):
        return get_object_or_404(models.Controller, name=self.kwargs["addr"])

    def get_queryset(self):
        addr = self.get_object()
        return addr.event_set.all()


class SubjectList(generics.ListAPIView):
    queryset = models.Subject.objects.all()
    serializer_class = serializers.SubjectSerializer


class SubjectDetail(generics.RetrieveAPIView):
    lookup_field = "name"
    queryset = models.Subject.objects.all()
    serializer_class = serializers.SubjectSerializer


class SubjectTrialList(DataFieldFilterMixin, generics.ListAPIView):
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TrialFilter
    pagination_class = LinkHeaderPagination

    def get_object(self):
        return get_object_or_404(models.Subject, name=self.kwargs["subject"])

    def get_queryset(self):
        subj = self.get_object()
        return subj.trial_set.all()
