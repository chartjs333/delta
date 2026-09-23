import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useLanguage } from "../../i18n";
import { slideFromSearch, slides } from "./slides";
import "./guide.css";

const labels = {
  en: { title: "How DeltaReduce works", eyebrow: "THE IDEA, STEP BY STEP", previous: "Previous", next: "Next", slide: "Slide", of: "of", jump: "Choose a slide", full: "Full screen", exit: "Exit full screen", original: "Open original image", notes: "Technical notes", corrections: "Corrections to this illustration", language: "Original illustrations: English. Captions and controls follow your selected language.", keys: "Use ← / → to navigate · Home / End for first / last", boundary: "Conceptual guide · See Live execution for measured runs and verified receipts.", failed: "The slide image could not be loaded.", retry: "Retry image", unavailable: "Full screen is unavailable in this browser. You can still use the slide controls." },
  ru: { title: "Как работает DeltaReduce", eyebrow: "ИДЕЯ, ШАГ ЗА ШАГОМ", previous: "Назад", next: "Далее", slide: "Слайд", of: "из", jump: "Выбрать слайд", full: "На весь экран", exit: "Выйти из полного экрана", original: "Открыть исходное изображение", notes: "Технические пояснения", corrections: "Исправления к иллюстрации", language: "Исходные иллюстрации — на английском. Подписи и управление используют выбранный язык.", keys: "Листайте стрелками ← / → · Home / End — первый / последний", boundary: "Объяснение идеи · Измеренные запуски и проверенные receipts — в разделе «Выполнение».", failed: "Не удалось загрузить изображение слайда.", retry: "Загрузить снова", unavailable: "Полный экран недоступен в этом браузере. Кнопки переключения слайдов продолжают работать." },
};

export function GuidePage() {
  const language = useLanguage();
  const copy = labels[language];
  const [index, setIndex] = useState(() => slideFromSearch(window.location.search));
  const [failed, setFailed] = useState(false);
  const [retry, setRetry] = useState(0);
  const [full, setFull] = useState(false);
  const [fullFailed, setFullFailed] = useState(false);
  const root = useRef<HTMLElement>(null);
  const slide = slides[index];
  const text = slide[language];
  function move(next: number) {
    const bounded = Math.max(0, Math.min(slides.length - 1, next));
    setIndex(bounded); setFailed(false);
    const url = new URL(window.location.href);
    url.searchParams.set("slide", String(bounded + 1));
    window.history.replaceState(null, "", url);
  }
  useEffect(() => {
    root.current?.focus({ preventScroll: true });
    const changed = () => setFull(document.fullscreenElement === root.current);
    document.addEventListener("fullscreenchange", changed);
    return () => document.removeEventListener("fullscreenchange", changed);
  }, []);
  async function toggleFullscreen() {
    setFullFailed(false);
    try {
      if (document.fullscreenElement === root.current) await document.exitFullscreen();
      else if (root.current?.requestFullscreen) await root.current.requestFullscreen();
      else setFullFailed(true);
    } catch { setFullFailed(true); }
  }
  function keyboard(event: KeyboardEvent<HTMLElement>) {
    const target = event.target as HTMLElement;
    if (event.altKey || event.ctrlKey || event.metaKey || target.isContentEditable || target.closest("input,select,textarea")) return;
    const next = event.key === "ArrowRight" ? index + 1 : event.key === "ArrowLeft" ? index - 1 : event.key === "Home" ? 0 : event.key === "End" ? slides.length - 1 : null;
    if (next !== null) { event.preventDefault(); move(next); event.currentTarget.focus({ preventScroll: true }); }
  }
  return <article ref={root} className="guide-page" onKeyDown={keyboard} aria-labelledby="guide-title" tabIndex={-1}>
    <header className="guide-heading"><div><p className="eyebrow">{copy.eyebrow}</p><h1 id="guide-title">{copy.title}</h1></div>
      <button type="button" onClick={() => void toggleFullscreen()}>{full ? copy.exit : copy.full} ⛶</button></header>
    <section className="guide-viewer" role="region" aria-roledescription={language === "ru" ? "слайд-шоу" : "slideshow"} aria-label={copy.title} tabIndex={0}>
      <div className="guide-slide-heading"><p role="status" aria-live="polite">{copy.slide} <strong>{index + 1}</strong> {copy.of} {slides.length}<span> · {text.title}</span></p>
        <a href={slide.image} target="_blank" rel="noopener noreferrer">{copy.original} ↗</a></div>
      <div className="guide-image-stage">
        {failed ? <div role="alert"><p>{copy.failed}</p><button onClick={() => { setRetry(retry + 1); setFailed(false); }}>{copy.retry}</button></div>
          : <img key={`${index}-${retry}`} src={slide.image} alt={`${copy.slide} ${index + 1}: ${text.title}. ${text.summary}`} decoding="async" onError={() => setFailed(true)} />}
      </div>
      <div className="guide-controls"><button type="button" disabled={index === 0} onClick={() => move(index - 1)}>← {copy.previous}</button>
        <nav aria-label={copy.jump}>{slides.map((item, itemIndex) => <button type="button" key={item.image} aria-label={`${copy.slide} ${itemIndex + 1}: ${item[language].title}`} aria-current={itemIndex === index ? "step" : undefined} onClick={() => move(itemIndex)}>{itemIndex + 1}</button>)}</nav>
        <button type="button" className="primary" disabled={index === slides.length - 1} onClick={() => move(index + 1)}>{copy.next} →</button></div>
    </section>
    <div className="guide-details"><p className="guide-summary">{text.summary}</p>
      {"correction" in text ? <aside className="guide-correction"><strong>{copy.corrections}</strong><p>{text.note}</p></aside>
        : <details key={index}><summary>{copy.notes}</summary><p>{text.note}</p></details>}
      <p className="guide-help">{copy.keys}<br />{copy.language}</p>
      <a className="guide-boundary" href="#/live-execution">{copy.boundary}</a>
    </div>
    {fullFailed ? <p role="status">{copy.unavailable}</p> : null}
  </article>;
}
