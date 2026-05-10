from django.urls import path

from . import views


app_name = "transcripciones"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/transcripciones/", views.create_transcript, name="api-create"),
    path("descargar/<path:filename>/", views.download_transcript, name="download"),
]
