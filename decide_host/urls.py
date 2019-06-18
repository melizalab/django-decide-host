# -*- coding: utf-8 -*-
# -*- mode: python -*-
from django.conf.urls import url

from decide_host import views

urlpatterns = [
    url(r'^$', views.api_root, name='index'),
    url(r'^api/$', views.api_root, name='index'),
    url(r'^api/info/$', views.api_info, name='api-info'),
    url(r"^api/events/$", views.EventList.as_view(), name="event-list"),
    url(r"^api/trials/$", views.TrialList.as_view(), name="trial-list"),
    url(r"^api/controllers/$", views.ControllerList.as_view(), name="controller-list"),
    url(r"^api/controllers/(?P<name>[\w-]+)/$",
        views.ControllerDetail.as_view(), name="controller-detail"),
    url(r"^api/controllers/(?P<addr>[\w-]+)/events/$",
        views.ControllerEventList.as_view(), name="controller-event-list"),
    url(r"^api/subjects/$", views.SubjectList.as_view(), name="subject-list"),
    url(r"^api/subjects/(?P<name>[\w-]+)/$",
        views.SubjectDetail.as_view(), name="subject-detail"),
    url(r"^api/subjects/(?P<subject>[\w-]+)/trials/$",
        views.SubjectTrialList.as_view(), name="subject-trial-list"),
    # fallthrough to 404
    url(r"^.*/$", views.notfound, name='notfound')
]
