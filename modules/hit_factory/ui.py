# -*- coding: utf-8 -*-
"""
modules.hit_factory.ui — Gradio вкладка для HIT FACTORY.

Добавляет в Gradio fallback UI секцию "HIT FACTORY" с кнопками:
  - Сгенерить 1 хит / батч
  - Бенчмарк / KPI
  - Плеер последнего мастера

Подключение: из app/gui или python -m modules.hit_factory.ui
"""
from __future__ import annotations

def build_hit_factory_blocks():
    try:
        import gradio as gr
    except Exception:
        return None

    from pathlib import Path
    from modules.hit_factory.generator import HitFactory
    from modules.hit_factory.kpi import build_kpi
    from modules.hit_factory.config import TOP_GENRES_FOR_HELP

    def _make_one(genre, theme, seed, duration, min_score, evolve):
        genre = genre.strip() or None
        theme = theme.strip() or None
        seed_v = int(seed) if str(seed).strip() else None
        dur = int(duration) if str(duration).strip() else None
        ms = float(min_score) if str(min_score).strip() else 68.0
        factory = HitFactory(min_score=ms, evolve=bool(evolve), verbose=False)
        hit = factory.make_one(genre=genre, theme=theme, seed=seed_v, duration_sec=dur)
        # ищем аудио для плеера
        audio = hit.get("master_path") or ""
        txt = f"project {hit.get('project_id')}  score {hit.get('hit_score')} {hit.get('verdict')}\nmaster {audio}\ncover {Path(hit.get('out_root','')) / 'cover.png'}"
        return txt, audio

    def _make_batch(count, genre, duration):
        genre = genre.strip() or None
        dur = int(duration) if str(duration).strip() else None
        factory = HitFactory(verbose=False)
        batch = factory.make_batch(count=int(count or 2), genre=genre, duration_sec=dur)
        txt = "\n".join([f"{b.get('project_id')} {b.get('hit_score')} {b.get('verdict')} {b.get('master_path')}" for b in batch])
        # последний лучший
        best = max(batch, key=lambda x: float(x.get("hit_score") or 0)) if batch else {}
        audio = best.get("master_path") or ""
        return txt, audio

    def _kpi():
        kpi = build_kpi(save=True)
        md = Path("output/hits/hits_kpi.md").read_text(encoding="utf-8") if Path("output/hits/hits_kpi.md").exists() else "нет хитов"
        return md

    with gr.Blocks(title="HIT FACTORY") as demo:
        gr.Markdown("# HIT FACTORY — автономная фабрика хитов (бесплатно)\nОдна кнопка → трек + tiktok-куски + обложка + hit_score")
        with gr.Tab("Один хит"):
            with gr.Row():
                genre = gr.Dropdown(choices=[""]+TOP_GENRES_FOR_HELP, value="", label="Жанр (пусто=рандом)")
                theme = gr.Textbox(value="", label="Тема (пусто=авто)")
            with gr.Row():
                seed = gr.Number(value=None, label="Seed", precision=0)
                duration = gr.Number(value=90, label="Длительность сек")
                min_score = gr.Number(value=68, label="Порог для эволюции")
                evolve = gr.Checkbox(value=True, label="Эволюция")
            btn1 = gr.Button("Сгенерить хит", variant="primary")
            out_txt1 = gr.Textbox(lines=6, label="Результат")
            audio1 = gr.Audio(label="Мастер", type="filepath")
            btn1.click(_make_one, [genre, theme, seed, duration, min_score, evolve], [out_txt1, audio1])

        with gr.Tab("Батч"):
            with gr.Row():
                count = gr.Number(value=3, label="Количество", precision=0)
                genre2 = gr.Dropdown(choices=[""]+TOP_GENRES_FOR_HELP, value="", label="Жанр")
                duration2 = gr.Number(value=90, label="Длительность")
            btn2 = gr.Button("Запустить батч")
            out_txt2 = gr.Textbox(lines=10, label="Батч")
            audio2 = gr.Audio(label="Лучший мастер", type="filepath")
            btn2.click(_make_batch, [count, genre2, duration2], [out_txt2, audio2])

        with gr.Tab("KPI"):
            btn3 = gr.Button("Обновить KPI")
            md = gr.Markdown("нажми Обновить")
            btn3.click(_kpi, [], md)

    return demo

if __name__ == "__main__":
    demo = build_hit_factory_blocks()
    if demo is None:
        print("gradio not installed")
    else:
        demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
