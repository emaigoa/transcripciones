const form = document.getElementById("form");
const urlInput = document.getElementById("url");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const errorBox = document.getElementById("error");
const result = document.getElementById("result");
const title = document.getElementById("title");
const segmentCount = document.getElementById("segment-count");
const transcript = document.getElementById("transcript");
const copy = document.getElementById("copy");

const frames = ["Cargando ..", "Cargando ...."];
let loadingInterval = null;

function setLoading(isLoading) {
    loading.hidden = !isLoading;

    if (!isLoading) {
        clearInterval(loadingInterval);
        loadingInterval = null;
        return;
    }

    let frame = 0;
    loadingText.textContent = frames[frame];
    loadingInterval = setInterval(() => {
        frame += 1;
        loadingText.textContent = frames[frame % frames.length];
    }, 500);
}

function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
}

function clearError() {
    errorBox.textContent = "";
    errorBox.hidden = true;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    result.hidden = true;
    setLoading(true);

    try {
        const response = await fetch(`${window.APP_CONFIG.API_BASE_URL}/api/transcripciones/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: urlInput.value.trim() })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "No se pudo extraer la transcripcion.");
        }

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
