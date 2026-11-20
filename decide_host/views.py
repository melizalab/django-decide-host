# -*- mode: python -*-

import ipaddress
import json
import logging
import math

from django.conf import settings
from django.db.models import Q
from django.db.models.fields.json import KeyTransform
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from drf_link_header_pagination import LinkHeaderPagination
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings

from decide_host import __version__, api_version, models, renderers, serializers

logger = logging.getLogger(__name__)


class LinkHeaderPaginationByTimestamp(LinkHeaderPagination):
    ordering = "-time"
    page_size_query_param = "page_size"
    max_page_size = 10000


@api_view(["HEAD", "GET"])
def api_root(request, format=None):
    urls = {
        "info": reverse("decide:api-info", request=request, format=format),
        "events": reverse("decide:event-list", request=request, format=format),
        "trials": reverse("decide:trial-list", request=request, format=format),
        "controllers": reverse(
            "decide:controller-list", request=request, format=format
        ),
        "subjects": reverse("decide:subject-list", request=request, format=format),
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


_NOT_SCALAR = object()


def parse_json_scalar(value: str):
    """Parse a query string value as a JSON boolean, number, or null.

    Python-style True and False are also accepted. Returns _NOT_SCALAR for any
    other value.

    """
    if value in ("True", "False"):
        return value == "True"
    try:
        parsed = json.loads(value)
    except ValueError:
        return _NOT_SCALAR
    if parsed is None or isinstance(parsed, bool | int):
        return parsed
    if isinstance(parsed, float) and math.isfinite(parsed):
        return parsed
    return _NOT_SCALAR


class DataFieldFilterMixin:
    """Provides filtering based on components of the data JSONField.

    Query string values are always strings, so for exact matches, values that
    parse as booleans, numbers, or null also match the corresponding JSON
    values. For example, `data__correct=true` matches `{"correct": true}`, and
    `data__stim=123` matches both `{"stim": 123}` and `{"stim": "123"}`.

    """

    key_lookups = frozenset(KeyTransform.get_lookups())

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # this could be a little dangerous b/c we're letting the user design queries
        for key, value in self.request.GET.items():
            if not key.startswith("data__"):
                continue
            q = Q(**{key: value})
            lookup = key.rsplit("__", 1)[-1]
            if lookup == "exact" or lookup not in self.key_lookups:
                parsed = parse_json_scalar(value)
                if parsed is not _NOT_SCALAR:
                    q |= Q(**{key: parsed})
            qs = qs.filter(q)
        return qs


class StreamingNDJSONMixin:
    """Streams all results as newline-delimited JSON, without pagination, if
    the client requests `application/x-ndjson` in the Accept header (or uses
    `?format=ndjson`). Otherwise, responses are paginated as usual.

    """

    renderer_classes = (
        *api_settings.DEFAULT_RENDERER_CLASSES,
        renderers.NDJSONRenderer,
    )
    stream_chunk_size = 2000

    def list(self, request, *args, **kwargs):
        if not isinstance(request.accepted_renderer, renderers.NDJSONRenderer):
            return super().list(request, *args, **kwargs)
        queryset = self.filter_queryset(self.get_queryset())
        return StreamingHttpResponse(
            self.stream_ndjson(queryset),
            content_type=renderers.NDJSONRenderer.media_type,
        )

    def stream_ndjson(self, queryset):
        """Yield records as lines of JSON, batched to reduce write calls"""
        serializer = self.get_serializer()
        lines = []
        for record in serializer.iter_representations(
            queryset, chunk_size=self.stream_chunk_size
        ):
            lines.append(renderers.dumps(record))
            if len(lines) >= self.stream_chunk_size:
                yield "\n".join(lines) + "\n"
                lines = []
        if lines:
            yield "\n".join(lines) + "\n"


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


class EventList(StreamingNDJSONMixin, DataFieldFilterMixin, generics.ListCreateAPIView):
    queryset = models.Event.objects.with_names()
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = EventFilter
    pagination_class = LinkHeaderPaginationByTimestamp
    permission_classes = (IsAuthorizedSubnetOrReadOnly,)


class TrialList(StreamingNDJSONMixin, DataFieldFilterMixin, generics.ListCreateAPIView):
    """Records of trials and trial-related comments.

    This endpoint returns a list of records from the database of trial records.
    Use query parameters to restrict the number of items to a reasonable subset.

    Basic filters: `name` (of the procedure), `addr` (of the controller), and
    `subject`.

    Date-based filters: `time__date` for a specific date, `date_before` and
    `date_after` to specify a range. range is inclusive. Format dates as `YYYY-MM-DD`.

    Exclude comments with the query `nocomment=true`.

    You can filter on other fields of the record, but these need to be prefaced
    by `data__` due to the way they're stored in the database. For example, to
    restrict returned records to ones in which `correct` was `True`, add the
    query `data__correct=True`. Values that look like booleans, numbers, or
    `null` also match the corresponding JSON values.

    Multiple queries produce a more restrictive filter.

    Results are paginated. Use `page_size` to set the number of records per page
    (maximum 10000). Links to other pages are in the `Link` response header.

    To retrieve all matching records in a single response, request
    `Accept: application/x-ndjson` (or add `format=ndjson` to the query). The
    records are streamed as newline-delimited JSON, without pagination.

    Example: "?subject=P24&date_after=2022-02-01&date_before=2022-02-28"

    """

    queryset = models.Trial.objects.with_names()
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TrialFilter
    pagination_class = LinkHeaderPaginationByTimestamp
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
        uri = reverse(
            "decide:controller-event-list", args=[kwargs["name"]], request=request
        )
        response["Link"] = f'<{uri}>; rel="events"'
        return response


class ControllerEventList(
    StreamingNDJSONMixin, DataFieldFilterMixin, generics.ListAPIView
):
    serializer_class = serializers.EventSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = LinkHeaderPaginationByTimestamp
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
        uri = reverse(
            "decide:subject-trial-list", args=[kwargs["name"]], request=request
        )
        response["Link"] = f'<{uri}>; rel="trials"'
        return response


class SubjectTrialList(
    StreamingNDJSONMixin, DataFieldFilterMixin, generics.ListAPIView
):
    serializer_class = serializers.TrialSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    pagination_class = LinkHeaderPaginationByTimestamp
    filterset_class = TrialFilter

    def get_object(self):
        return get_object_or_404(models.Subject, name=self.kwargs["subject"])

    def get_queryset(self):
        subj = self.get_object()
        return subj.trial_set.with_names()
