"""Display-only adaptation of the existing MNIST demo; no training/protocol changes."""

# Localized display copy intentionally uses Cyrillic.
import re
from pathlib import Path

PREFIX = "/node-training"
GET_ROUTES = {PREFIX + "/", PREFIX + "/api/status", PREFIX + "/api/catalog"}
RUN_ROUTE = PREFIX + "/api/run"


def adapt_page(page: str, language: str) -> str:
    """Preserve nonce/script and API payloads; mount links and apply the app palette."""
    language = "en" if language == "en" else "ru"
    labels = (
        (
            "Presentation",
            "Admin UI",
            "How it works",
            "Node training example",
            "Separate MNIST example · LOCAL_DEMO_ONLY · not a Feature010 qualification",
        )
        if language == "en"
        else (
            "Презентация",
            "Администрирование",
            "Как это работает",
            "Обучение узлов",
            "Отдельный пример MNIST · LOCAL_DEMO_ONLY · не квалификация Feature010",
        )
    )
    navigation = (
        '<div class="delta-app-bar"><a class="delta-app-brand" href="/?lang='
        + language
        + '">Δ <strong>DeltaReduce</strong></a><nav aria-label="'
        + labels[3]
        + '">'
        + f'<a href="/?lang={language}">{labels[0]}</a>'
        + f'<a href="/admin/?lang={language}#/live-execution">{labels[1]}</a>'
        + f'<a href="/admin/?lang={language}#/guide">{labels[2]}</a>'
        + f'<span aria-current="page">{labels[3]}</span></nav></div>'
        + f'<div class="delta-example-scope">{labels[4]}</div>'
    )
    style = Path(__file__).with_name("node-training.css").read_text(encoding="utf-8")
    note = (
        "The pinned MNIST dataset is already prepared on this host. "
        "Run the example, then compare all four nodes with failure and recovery."
        if language == "en"
        else "Закреплённый набор MNIST уже подготовлен на этом компьютере. "
        "Запустите пример, затем сравните работу четырёх узлов и восстановление после сбоя."
    )
    page = re.sub(
        r'<p class="hero-note">.*?</p>', f'<p class="hero-note">{note}</p>', page, flags=re.DOTALL
    )
    return (
        page.replace("fetch('/api/", "fetch('/node-training/api/")
        .replace("</head>", f"<style>{style}</style></head>")
        .replace("<body>", "<body>" + navigation)
    )
