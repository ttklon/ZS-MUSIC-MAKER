# grep-таблицы `app/ai/prompts.py`

## `import` — 1 совпадений
```
    3 | from __future__ import annotations
```

## `def` — 6 совпадений
```
   32 | def build_lyrics_prompt(theme, genre, bpm, n_verses, bilingual,
   57 | def build_dossier_prompt(artist, tracks_text):
   62 | def build_track_dossier_prompt(title, lyrics, features):
   70 | def build_metadata_prompt(theme, style, snippet):
   75 | def build_music_prompt(genre, bpm, key, mood, reference_artist=None,
   91 | def build_cover_prompt(title, artist, genre, mood):
```

## `return` — 6 совпадений
```
   54 |     return "\n".join(parts)
   58 |     return (f"Артист: {artist}\n\nВсе известные тексты:\n=====\n"
   63 |     return (f"Трек: {title}\nBPM: {features.get('bpm', '?')}\n"
   71 |     return (f"Тема: {theme}\nСтиль: {style}\n\nКусок лирики:\n{snippet[:1200]}\n\n"
   88 |     return ", ".join(parts)
   92 |     return (f"Album cover for song '{title}' by {artist}. Genre: {genre}. "
```

## `if` — 7 совпадений
```
   37 |     if user_lines:
   40 |     if artist_dossier:
   47 |     if track_reference:
   78 |     if reference_artist:
   80 |     if reference_track_features:
   82 |         if instr:
   85 |         if atmo:
```
