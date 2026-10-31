# -*- coding: utf-8 -*-
"""
app/core/stages — реализации стадий пайплайна, по одному модулю на ответственность.

    prep     анализ референсов, грув, план аранжировки
    beat     бит: beat_constructor и процедурный фоллбек
    texture  атмосфера: MusicGen и честный synth-скаффолд
    lyrics   текст песни: структура, LLM, шаблоны
    vocal    вокал: TTS, RVC, вокальные эффекты
    mix      микс бита и вокала + сайдчейн
    master   стенды, anti-neuro полировка, стемы, hit-score
    release  релиз-пакет

Склейка стадий — только в `app.core.orchestrator`.
"""
