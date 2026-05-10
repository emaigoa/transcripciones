from dataclasses import dataclass
from html import unescape
from pathlib import Path
import os
import re
import shutil
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


DEFAULT_OUTPUT_FILE = Path("transcripcion.txt")
TRANSCRIPT_JSNAME = "h7hTqc"
TITLE_JSCONTROLLER = "LxQ0Q"
PLAY_BUTTON_JSNAME = "dW8tsb"
TRANSCRIPT_BUTTON_JSNAME = "QzTKac"
INVALID_FILENAME_CHARS = r'<>:"/\|?*'


@dataclass(frozen=True)
class TranscriptResult:
    title: str
    transcript: str
    segment_count: int


def fix_mojibake(text):
    if "\u00c3" not in text and "\u00c2" not in text:
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except UnicodeError:
        return text


def clean_text(text):
    text = unescape(text)
    text = fix_mojibake(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def sanitize_filename(name):
    name = clean_text(name)

    for char in INVALID_FILENAME_CHARS:
        name = name.replace(char, "-")

    name = re.sub(r"\s+", " ", name).strip(" .")

    if not name:
        return DEFAULT_OUTPUT_FILE.name

    path = Path(name)
    if path.suffix:
        name = path.stem

    return f"{name}.txt"


def available_path(path):
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        return path

    for index in range(1, 1000):
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"No se encontro un nombre disponible para {path.name}")


def create_driver():
    chrome_options = ChromeOptions()
    chrome_binary = os.environ.get("CHROME_BIN") or shutil.which("chromium")
    if chrome_binary:
        chrome_options.binary_location = chrome_binary

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        return webdriver.Chrome(options=chrome_options)
    except Exception:
        edge_options = EdgeOptions()
        edge_options.add_argument("--headless=new")
        edge_options.add_argument("--mute-audio")
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--window-size=1920,1080")
        return webdriver.Edge(options=edge_options)


def click_button(driver, wait, selector, error_message):
    try:
        button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        button.click()
    except TimeoutException as error:
        raise RuntimeError(error_message) from error
    except Exception:
        button = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].click();", button)


def scrape_transcript(url):
    driver = create_driver()
    wait = WebDriverWait(driver, 120)

    try:
        driver.get(url)

        play_selector = f'button[jsname="{PLAY_BUTTON_JSNAME}"]'
        click_button(driver, wait, play_selector, "No se encontro el boton reproducir.")
        time.sleep(2)

        transcript_button_selector = f'button[jsname="{TRANSCRIPT_BUTTON_JSNAME}"]'
        click_button(
            driver,
            wait,
            transcript_button_selector,
            "No se encontro el boton transcripcion.",
        )

        transcript_selector = f'div[jsname="{TRANSCRIPT_JSNAME}"] div.wyBDIb'
        title_selector = f'span[jscontroller="{TITLE_JSCONTROLLER}"]'

        try:
            wait.until(
                lambda browser: browser.find_elements(
                    By.CSS_SELECTOR,
                    transcript_selector,
                )
            )
        except TimeoutException as error:
            raise RuntimeError(
                f"No se encontraron segmentos dentro de div jsname={TRANSCRIPT_JSNAME!r}."
            ) from error

        segments = [
            clean_text(element.text)
            for element in driver.find_elements(By.CSS_SELECTOR, transcript_selector)
        ]
        segments = [segment for segment in segments if segment]

        if not segments:
            raise RuntimeError("La transcripcion se encontro vacia.")

        title_elements = driver.find_elements(By.CSS_SELECTOR, title_selector)
        title = clean_text(title_elements[0].text) if title_elements else ""

        return TranscriptResult(
            title=title,
            transcript="\n".join(segments),
            segment_count=len(segments),
        )
    finally:
        driver.quit()


def save_transcript(result, output_dir):
    filename = sanitize_filename(result.title)
    output_path = available_path(Path(output_dir) / filename)
    output_path.write_text(result.transcript + "\n", encoding="utf-8")
    return output_path
