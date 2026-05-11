import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread
from uuid import uuid4

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .forms import DriveLinkForm
from .services.drive_scraper import AuthRequiredError, save_transcript, scrape_transcript


JOBS = {}
JOBS_LOCK = Lock()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def set_job(job_id, **updates):
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.update(updates)
        job["updated_at"] = now_iso()
        return dict(job)


def extract_transcript_data(url, progress_callback=None):
    result = scrape_transcript(url, progress_callback=progress_callback)

    return {
        "title": result.title or "sin titulo",
        "transcript": result.transcript,
        "segment_count": result.segment_count,
    }


def extract_and_save(url):
    result = scrape_transcript(url)
    output_path = save_transcript(result, settings.TRANSCRIPCIONES_OUTPUT_DIR)
    data = {
        "title": result.title or "sin titulo",
        "transcript": result.transcript,
        "segment_count": result.segment_count,
        "filename": output_path.name,
        "download_url": f"/descargar/{output_path.name}/",
    }
    return data


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


def health(request):
    return JsonResponse({"status": "ok"})


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
        data = extract_transcript_data(form.cleaned_data["url"])
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=500)

    return JsonResponse(data)


def run_transcript_job(job_id, url):
    def progress(status, message):
        set_job(job_id, status=status, message=message)

    try:
        data = extract_transcript_data(url, progress_callback=progress)
    except AuthRequiredError as error:
        set_job(
            job_id,
            status="auth_required",
            message=str(error),
            error=str(error),
        )
    except Exception as error:
        set_job(job_id, status="failed", message=str(error), error=str(error))
    else:
        set_job(job_id, status="done", message="Transcripcion lista", result=data)


@csrf_exempt
@require_POST
def create_transcript_job(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON invalido."}, status=400)

    url = payload.get("url", "").strip()
    form = DriveLinkForm({"url": url})

    if not form.is_valid():
        return JsonResponse({"error": "URL invalida."}, status=400)

    job_id = uuid4().hex
    with JOBS_LOCK:
        JOBS[job_id] = {
            "id": job_id,
            "status": "queued",
            "message": "En cola",
            "result": None,
            "error": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

    thread = Thread(
        target=run_transcript_job,
        args=(job_id, form.cleaned_data["url"]),
        daemon=True,
    )
    thread.start()

    return JsonResponse({"job_id": job_id, "status": "queued", "message": "En cola"})


@require_GET
def transcript_job_status(request, job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)

    if not job:
        return JsonResponse({"error": "Trabajo no encontrado."}, status=404)

    return JsonResponse(job)


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
