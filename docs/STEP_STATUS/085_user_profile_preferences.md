# PLAN_v39 — ШАГ 085: user creative preferences

`modules/user_profile.py` now persists a `creative_preferences` object containing only generation-relevant fields: favourite genres, lyrics language, text style and a default beat (BPM/key/mood). Setters validate ranges and bound strings; obvious email, URL and phone-like values are rejected. `prompt_preferences()` is deliberately narrower than the complete profile and never exposes `artist_name`, history or voice-training data.

`app/ai/prompts.py` adds a prompt-safe profile context and uses it in lyrics, metadata and music builders. Existing builder call signatures remain compatible because the optional `user_profile` argument is appended. Prompts demonstrably change with genres/language/style/default beat while direct identity fields and history are excluded.

A full-suite run revealed that default prompt composition had created `data/user_profile.json`, making the data inventory fail. The implementation was corrected: no-profile prompt construction now uses immutable defaults and performs no persistence. The generated artifact was removed and the full check rerun. Final acceptance: **197 passed**; `compileall` successfully; AST audit — **0 dead imports**; data inventory — **73 managed, 0 unknown, 0 invalid**.
