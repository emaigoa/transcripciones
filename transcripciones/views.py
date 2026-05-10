import json
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import DriveLinkForm
from .services.drive_scraper import save_transcript, scrape_transcript


def extract_and_save(url):
    result = scrape_transcript(url)
    output_path = save_transcript(result, settings.TRANSCRIPCIONES_OUTPUT_DIR)

    return {
        "title": result.title or "sin titulo",
        "transcript": result.transcript,
        "segment_count": result.segment_count,
        "filename": output_path.name,
    }


def index(request):
    context = {"form": DriveLinkForm()}

    if request.method == "POST":
        form = DriveLinkForm(request.POST)
        context["form"] = form

        if form.is_valid():
            try:
                context.update(extract_and_save(form.cleaned_data["url"]))
            except Exception as error:
                context["error"] = str(error)

    return render(request, "transcripciones/index.html", context)


@csrf_exempt
@require_POST
def create_transcript(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON invalido."}, status=400)

    url = payload.get("url", "").strip()
    form = DriveLinkForm({"url": url})

    if not form.is_valid():
        return JsonResponse({"error": "URL invalida."}, status=400)

    try:
        data = extract_and_save(form.cleaned_data["url"])
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)

    return JsonResponse(data)


def download_transcript(request, filename):
    output_dir = Path(settings.TRANSCRIPCIONES_OUTPUT_DIR).resolve()
    file_path = (output_dir / filename).resolve()

    if output_dir not in file_path.parents or not file_path.exists():
        raise Http404("Archivo no encontrado")

    return FileResponse(
        file_path.open("rb"),
        as_attachment=True,
        filename=file_path.name,
    )
