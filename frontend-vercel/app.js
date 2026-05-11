const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const progressBar = document.getElementById("progress-bar");
const errorBox = document.getElementById("error");
const authRequired = document.getElementById("auth-required");
const result = document.getElementById("result");
const title = document.getElementById("title");
const segmentCount = document.getElementById("segment-count");
const transcript = document.getElementById("transcript");
const copy = document.getElementById("copy");

const progressByStatus = {
    queued: 8,
    starting: 16,
    opening: 30,
    playing: 45,
    transcript_panel: 60,
    waiting_segments: 74,
    extracting: 88,
    finished: 96,
    done: 100,
    auth_required: 100,
    failed: 100
};

const terminalStatuses = new Set(["done", "failed", "auth_required"]);

function setLoading(isLoading) {
    loading.hidden = !isLoading;

    if (!isLoading) {
        progressBar.style.width = "0%";
        return;
    }
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
}

function clearError() {
    errorBox.textContent = "";
    errorBox.hidden = true;
    authRequired.hidden = true;
}

function updateProgress(status, message) {
    loadingText.textContent = message || "Procesando";
    progressBar.style.width = `${progressByStatus[status] || 12}%`;
}

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

async function startTranscriptJob(url) {
    const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/api/transcripciones/jobs/`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url })
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "No se pudo iniciar la transcripcion.");
    }

    return data.job_id;
}

async function waitForTranscriptJob(jobId) {
    while (true) {
        const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/api/transcripciones/jobs/${jobId}/`);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "No se pudo consultar el progreso.");
        }

        updateProgress(data.status, data.message);

        if (terminalStatuses.has(data.status)) {
            return data;
        }

        await sleep(1500);
    }
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    result.hidden = true;
    setLoading(true);
    updateProgress("queued", "En cola");

    try {
        const jobId = await startTranscriptJob(urlInput.value.trim());
        const job = await waitForTranscriptJob(jobId);

        if (job.status === "auth_required") {
            authRequired.hidden = false;
            throw new Error(job.error || "El archivo requiere iniciar sesion.");
        }

        if (job.status === "failed") {
            throw new Error(job.error || "No se pudo extraer la transcripcion.");
        }

        const data = job.result;
        title.textContent = data.title;
        segmentCount.textContent = `${data.segment_count} segmentos extraidos`;
        transcript.value = data.transcript;
        result.hidden = false;
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
});

copy.addEventListener("click", async () => {
    await navigator.clipboard.writeText(transcript.value);
    copy.textContent = "Copiado";
    setTimeout(() => {
        copy.textContent = "Copiar texto";
    }, 1400);
});
