# -*- coding: utf-8 -*-
# -*- mode: python -*-
from django.urls import re_path

from decide_host import views

urlpatterns = [
    re_path(r"^$", views.api_root, name="index"),
    re_path(r"^api/$", views.api_root, name="index"),
    re_path(r"^api/info/$", views.api_info, name="api-info"),
    re_path(r"^api/events/$", views.EventList.as_view(), name="event-list"),
    re_path(r"^api/trials/$", views.TrialList.as_view(), name="trial-list"),
    re_path(
        r"^api/controllers/$", views.ControllerList.as_view(), name="controller-list"
    ),
    re_path(
        r"^api/controllers/(?P<name>[\w-]+)/$",
        views.ControllerDetail.as_view(),
        name="controller-detail",
    ),
    re_path(
        r"^api/controllers/(?P<addr>[\w-]+)/events/$",
        views.ControllerEventList.as_view(),
        name="controller-event-list",
    ),
    re_path(r"^api/subjects/$", views.SubjectList.as_view(), name="subject-list"),
    re_path(
        r"^api/subjects/(?P<name>[\w-]+)/$",
        views.SubjectDetail.as_view(),
        name="subject-detail",
    ),
    re_path(
        r"^api/subjects/(?P<subject>[\w-]+)/trials/$",
        views.SubjectTrialList.as_view(),
        name="subject-trial-list",
    ),
    # fallthrough to 404
    re_path(r"^.*/$", views.notfound, name="notfound"),
]
