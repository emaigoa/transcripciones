from django.urls import path

from . import views


app_name = "transcripciones"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/health/", views.health, name="api-health"),
    path("api/transcripciones/", views.create_transcript, name="api-create"),
    path("api/transcripciones/jobs/", views.create_transcript_job, name="api-job-create"),
    path(
        "api/transcripciones/jobs/<str:job_id>/",
        views.transcript_job_status,
        name="api-job-status",
    ),
    path("descargar/<path:filename>/", views.download_transcript, name="download"),
]
