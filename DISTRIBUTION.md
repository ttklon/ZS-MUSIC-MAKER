# Дистрибуция треков v7

Готовый релиз-пакет в `output/releases/track_<id>/`:

## Spotify / Yandex Music / Apple Music
- Загружай `master.wav` (24-bit) или `master.flac`.
- `metadata.json` содержит все нужные поля.
- ID3-теги в MP3/FLAC уже прописаны (artist_name из user_profile).

## TikTok
- `tiktok.mp4` — 15-30 сек вертикально с обложкой. Готово к загрузке.

## YouTube Shorts / Reels
- `reels.mp4` — вертикальный формат.

## Для клубов и авто
- `car_master.wav` — с бустом саба (30-80 Hz).
- `club_master.wav` — жирный саб + громкость.
- `streaming_master.wav` — нейтральный.

## Юридически
- `manifest.json` — лицензии всех сэмплов. Только CC0/CC-BY/Royalty-Free.
- Если использовался CC-BY сэмпл — автору полагается упоминание, добавь его в описание релиза.
