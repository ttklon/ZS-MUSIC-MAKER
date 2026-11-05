# -*- coding: utf-8 -*-
"""
app/core/ai — AI-слой пайплайна (локальные модели: MusicGen, XTTS, RVC, CLAP).

    context       состояние запуска, передаваемое стадиям
    render        рендер-хелперы над загруженной моделью
    stages_meta   железо, досье, текст, метаданные
    stages_music  бит и стерео-текстура
    stages_vocal  вокал, RVC, микс
    stages_final  мастеринг, обложка, теги
"""
