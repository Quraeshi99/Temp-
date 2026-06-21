# 📋 Masjid App — Smart Quran Module — MASTER TASK LIST

> **Rule**: Har task ko order mein karna hai. Pehle wala complete ho tab agle pe jaana.
> **Project**: `/home/ubuntu/Masjid`
> **Branch**: `feature/quran-module` (new branch banayenge)

---

## PHASE 0: Setup & Preparation
> Koi code nahi likhna — sirf tayyaari

- [ ] **0.1** — Git branch banao `feature/quran-module`
  - Command: `git checkout -b feature/quran-module`
  - Verify: `git branch` mein naya branch dikhna chahiye

- [ ] **0.2** — `httpx` ko `requirements.txt` mein explicitly add karo
  - File: [requirements.txt](file:///home/ubuntu/Masjid/requirements.txt)
  - Kya karna hai: `httpx>=0.27.0` add karo (abhi implicit dependency hai)
  - Verify: `pip install -r requirements.txt` error-free chale

- [ ] **0.3** — Feature flags add karo
  - File: [feature_flags.py](file:///home/ubuntu/Masjid/app/core/feature_flags.py)
  - Kya karna hai: 6 new flags add karo:
    ```python
    QURAN_MODULE: bool        # Master switch for Quran
    QURAN_AUDIO: bool         # Audio playback
    QURAN_HIFZ: bool          # Hifz engine
    QURAN_USTAAD: bool        # Teacher-student mode
    QURAN_WORD_BY_WORD: bool  # Word-by-word breakdown
    QURAN_TAFSIR: bool        # Tafsir feature
    ```
  - Verify: App start ho without error

- [ ] **0.4** — Quran config params add karo
  - File: [config.py](file:///home/ubuntu/Masjid/app/core/config.py)
  - Kya karna hai: Add Quran.com API settings:
    ```python
    QURAN_API_BASE_URL: str = "https://api.quran.com/api/v4"
    QURAN_API_RATE_LIMIT: int = 2          # requests per second
    QURAN_DEFAULT_SCRIPT: str = "indopak"  # uthmani/indopak/imlaei
    QURAN_DEFAULT_TRANSLATIONS: str = "131,85"  # resource IDs
    QURAN_IMPORT_BATCH_SIZE: int = 50
    ```
  - Verify: `from app.core.config import settings` — no error

- [ ] **0.5** — Constants add karo
  - File: [constants.py](file:///home/ubuntu/Masjid/app/core/constants.py)
  - Kya karna hai: Quran-related constants:
    ```python
    TOTAL_SURAHS = 114
    TOTAL_AYAHS = 6236
    TOTAL_PAGES = 604
    TOTAL_JUZ = 30
    TOTAL_HIZB = 60
    TOTAL_MANZIL = 7
    TOTAL_RUKU = 556
    
    HIFZ_STATUS_NEW = "new"
    HIFZ_STATUS_LEARNING = "learning"
    HIFZ_STATUS_REVIEWING = "reviewing"
    HIFZ_STATUS_MEMORIZED = "memorized"
    
    ASSIGNMENT_STATUS_PENDING = "pending"
    ASSIGNMENT_STATUS_SUBMITTED = "submitted"
    ASSIGNMENT_STATUS_GRADED = "graded"
    ```
  - Verify: Import karo, no error

---

## PHASE 1: Database Models (Foundation)
> Sab se pehle — bina models ke kuch nahi hoga

- [ ] **1.1** — Quran models file banao
  - File: 🆕 [quran.py](file:///home/ubuntu/Masjid/app/models/quran.py)
  - Kya karna hai: 16 SQLAlchemy models likhna hai (sab ek file mein):
    1. `QuranSurah` — 114 surahs ka metadata
    2. `QuranAyah` — 6,236 ayahs with 3 scripts
    3. `QuranWord` — Word-by-word data (~77K rows)
    4. `QuranJuz` — 30 juz/para metadata
    5. `QuranReciter` — Reciter registry
    6. `QuranTranslation` — Translation cache (hybrid)
    7. `QuranTafsirEntry` — Tafsir cache (hybrid)
    8. `QuranAudioFile` — Audio URL cache
    9. `QuranBookmark` — User bookmarks
    10. `QuranReadingHistory` — Reading tracker
    11. `QuranUserSettings` — Per-user Quran preferences
    12. `HifzProgress` — Per ayah memorization state (FSRS)
    13. `HifzSession` — Practice session log
    14. `HifzDailyTarget` — User's daily Hifz settings
    15. `HifzAssignment` — Teacher → Student task
    16. `HifzSubmission` — Student submission + grading
  - Rules:
    - Sab IDs `BigInteger`
    - Sab mein `version` column (delta sync)
    - Sab mein `created_at`, `updated_at`
    - Proper ForeignKeys + relationships
    - Indexes on frequently queried columns
  - Verify: `python -c "from app.models.quran import *"` — no error

- [ ] **1.2** — Models ko `__init__.py` mein register karo
  - File: [__init__.py](file:///home/ubuntu/Masjid/app/models/__init__.py)
  - Kya karna hai: Sab 16 new models import karo + `__all__` mein add karo
  - Verify: `python -c "from app.models import QuranSurah, QuranAyah, HifzProgress"` — no error

- [ ] **1.3** — `db/base.py` update karo
  - File: [base.py](file:///home/ubuntu/Masjid/app/db/base.py)
  - Kya karna hai: `import app.models.quran` add karo (Alembic ke liye zaroori)
  - Verify: Alembic ko naye models dikhne chahiye

- [ ] **1.4** — Alembic migration generate karo
  - Command: `alembic revision --autogenerate -m "add_quran_module_16_tables"`
  - Verify: New migration file generate ho
  - Check: Migration mein sab 16 tables ka `create_table` dikhna chahiye

- [ ] **1.5** — Migration run karo
  - Command: `alembic upgrade head`
  - Verify: `\dt` in psql — 16 new tables dikhni chahiye
  - Verify: Sab indexes create hue

---

## PHASE 2: Quran.com API Client + Data Import
> API se baat karne ka engine + data lana

- [ ] **2.1** — Quran.com API Client banao
  - File: 🆕 [api_client.py](file:///home/ubuntu/Masjid/app/services/quran/api_client.py)
  - Package init: 🆕 [__init__.py](file:///home/ubuntu/Masjid/app/services/quran/__init__.py)
  - Kya karna hai:
    ```
    QuranAPIClient class:
    ├── __init__(rate_limit=2)     # 2 req/sec throttle
    ├── _throttle()                # asyncio.sleep for rate limit
    ├── get_chapters()             # GET /chapters
    ├── get_chapter(id)            # GET /chapters/{id}
    ├── get_verses_by_chapter(n)   # GET /verses/by_chapter/{n}?words=true
    ├── get_verses_by_page(n)      # GET /verses/by_page/{n}
    ├── get_verses_by_juz(n)       # GET /verses/by_juz/{n}
    ├── get_translations_list()    # GET /resources/translations
    ├── get_translation(id, params)# GET /quran/translations/{id}
    ├── get_tafsirs_list()         # GET /resources/tafsirs
    ├── get_tafsir(id, key)        # GET /tafsirs/{id}/by_ayah/{key}
    ├── get_reciters()             # GET /resources/recitations
    ├── get_recitation(id, chapter)# GET /recitations/{id}/by_chapter/{n}
    ├── search(query, lang, size)  # GET /search
    └── _get(url, params)          # Base httpx.AsyncClient GET
    ```
  - Rules:
    - `httpx.AsyncClient` with timeout=15s
    - Rate limiting (asyncio.Semaphore + sleep)
    - Retry 3 times with exponential backoff
    - structlog logging har request pe
    - Error handling (HTTPStatusError, TimeoutError)
  - Verify: Script likhke test karo — `/chapters` call karke 114 surahs aane chahiye

- [ ] **2.2** — Celery import tasks banao
  - File: 🆕 [quran_import.py](file:///home/ubuntu/Masjid/app/tasks/quran_import.py)
  - Kya karna hai:
    ```
    Tasks (all on "slow" queue):
    ├── import_all_surahs()
    │   → /chapters API → QuranSurah table (114 rows)
    │
    ├── import_ayahs_for_surah(surah_number)
    │   → /verses/by_chapter API (words=true)
    │   → QuranAyah + QuranWord tables
    │   → Also fetch uthmani + imlaei scripts
    │
    ├── import_full_quran()
    │   → Orchestrator: calls import_all_surahs()
    │   → Then loops 1-114 calling import_ayahs_for_surah(n)
    │   → Then calls import_juz_metadata()
    │   → Progress tracked in Redis key "quran:import:progress"
    │
    ├── import_juz_metadata()
    │   → Compute from ayah data → QuranJuz (30 rows)
    │
    ├── import_translations(resource_ids: list)
    │   → /quran/translations/{id} → QuranTranslation table
    │
    ├── import_reciters()
    │   → /resources/recitations → QuranReciter table
    │
    ├── import_audio_urls(reciter_id, surah_number)
    │   → /recitations/{id}/by_chapter/{n} → QuranAudioFile
    │
    └── sync_quran_data()
        → Nightly check: any new translations/tafsirs?
        → Update existing data if changed
    ```
  - Rules:
    - Idempotent — re-run karo toh duplicate na bane (upsert by verse_key)
    - Progress tracking in Redis
    - Error handling + retry (max 3)
    - Batched API calls (50 ayahs per request)
  - Verify: Celery task manually trigger karo, DB mein data aana chahiye

- [ ] **2.3** — Import management endpoint banao
  - File: Admin endpoint mein add karo
  - Kya karna hai: Super Admin ke liye import trigger endpoint:
    ```
    POST /api/super-admin/quran/import          → Start full import
    GET  /api/super-admin/quran/import/status    → Check progress
    POST /api/super-admin/quran/import/translations → Import specific translations
    ```
  - Verify: Super admin call kare, task start ho, progress dikhe

---

## PHASE 3: Quran Reading APIs (Core)
> User Quran padh sake — basic reading experience

- [ ] **3.1** — Quran schemas banao
  - File: 🆕 [quran.py](file:///home/ubuntu/Masjid/app/schemas/quran.py)
  - Kya karna hai: Sab Pydantic schemas likhna hai:
    ```
    # Surah schemas
    SurahListItem, SurahDetail, SurahInfo
    
    # Ayah schemas
    AyahDisplay, AyahBrief, WordDisplay
    
    # Page/Juz schemas
    QuranPageView, JuzListItem, JuzDetail
    
    # Translation schemas
    TranslationResource, TranslationDisplay
    
    # Tafsir schemas
    TafsirResource, TafsirDisplay
    
    # Audio schemas
    ReciterDisplay, AudioFileDisplay
    
    # Bookmark schemas
    BookmarkCreate, BookmarkDisplay
    
    # Reading schemas
    ReadingLogCreate, ReadingStats, KhatamProgress
    
    # Hifz schemas
    HifzDashboard, HifzDueToday, HifzGradeRequest
    HifzStats, HifzHeatmap, HifzSettingsUpdate
    SabaqStart, ReviewGrade, TestPrompt
    
    # Ustaad schemas
    AssignmentCreate, AssignmentDisplay
    SubmissionCreate, SubmissionGrade
    StudentProgress, TeacherDashboard
    
    # Search schemas
    SearchRequest, SearchResult
    ```
  - Verify: `python -c "from app.schemas.quran import *"` — no error

- [ ] **3.2** — Surah service banao
  - File: 🆕 [surah_service.py](file:///home/ubuntu/Masjid/app/services/quran/surah_service.py)
  - Kya karna hai:
    ```
    SurahService:
    ├── get_all_surahs(db)           → List of 114 surahs
    ├── get_surah(db, number)        → Single surah detail
    └── get_surah_info(db, number)   → Detailed background info
    ```
  - Data: DB se read karo (Phase 2 mein import ho chuka hoga)
  - Verify: Unit test likhke verify karo

- [ ] **3.3** — Ayah service banao
  - File: 🆕 [ayah_service.py](file:///home/ubuntu/Masjid/app/services/quran/ayah_service.py)
  - Kya karna hai:
    ```
    AyahService:
    ├── get_by_surah(db, surah_num, page, per_page, script, words)
    ├── get_by_page(db, page_number, script, words)
    ├── get_by_juz(db, juz_number, page, per_page, script)
    ├── get_by_hizb(db, hizb_number, ...)
    ├── get_by_ruku(db, ruku_number, ...)
    ├── get_by_manzil(db, manzil_number, ...)
    ├── get_by_key(db, verse_key, script, words)
    └── get_random(db)
    ```
  - Rules:
    - Pagination support (per_page, page)
    - Script selection (uthmani/indopak/imlaei)
    - Optional word-by-word include
    - `selectinload` for relationships (N+1 avoid)
  - Verify: Unit tests for each method

- [ ] **3.4** — Surah + Ayah API endpoints banao
  - Files:
    - 🆕 [quran/__init__.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/__init__.py) — Router registry
    - 🆕 [quran/surahs.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/surahs.py)
    - 🆕 [quran/ayahs.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/ayahs.py)
  - Endpoints:
    ```
    GET /api/quran/surahs                     → 114 surahs list
    GET /api/quran/surahs/{number}            → Surah detail
    GET /api/quran/surahs/{number}/info       → Surah background

    GET /api/quran/ayahs/by-surah/{n}         → Ayahs of surah
    GET /api/quran/ayahs/by-page/{n}          → Ayahs on page
    GET /api/quran/ayahs/by-juz/{n}           → Ayahs of juz
    GET /api/quran/ayahs/by-hizb/{n}          → Ayahs of hizb
    GET /api/quran/ayahs/by-ruku/{n}          → Ayahs of ruku
    GET /api/quran/ayahs/by-manzil/{n}        → Ayahs of manzil
    GET /api/quran/ayahs/{verse_key}          → Single ayah "2:255"
    GET /api/quran/ayahs/random               → Random ayah
    ```
  - Auth: No auth required (public read)
  - Verify: `curl` se test karo, sahi JSON aana chahiye

- [ ] **3.5** — Old quran endpoint ko replace karo
  - Delete: Purana [quran.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran.py) single file
  - Modify: [api.py](file:///home/ubuntu/Masjid/app/api/v1/api.py) — old router hatao, new quran package register karo
  - Modify: [prayer.py](file:///home/ubuntu/Masjid/app/schemas/prayer.py) — old `QuranVerse`, `QuranPageDisplay` remove karo
  - Verify: Purana `/api/quran/page/{n}` ab bhi kaam kare (backward compat endpoint rakho)

---

## PHASE 4: Translation + Tafsir
> Tarjuma aur Tafsir system

- [ ] **4.1** — Translation service banao (HYBRID CACHE)
  - File: 🆕 [translation_service.py](file:///home/ubuntu/Masjid/app/services/quran/translation_service.py)
  - Kya karna hai:
    ```
    TranslationService:
    ├── get_available_translations(db)
    │   → DB check → if empty, fetch from API & cache
    │
    ├── get_translation_for_surah(db, resource_id, surah_num)
    │   → DB check → hit? return
    │   → miss? fetch from API → save to DB → return
    │   → Track demand in quran_cache_stats
    │
    └── get_translation_for_ayah(db, resource_id, verse_key)
        → Same hybrid pattern
    ```
  - Ye hai HYBRID cache pattern — pehle DB dekho, na mile toh API call karo, save karo
  - Verify: Pehli baar API call hoga, doosri baar DB se milega

- [ ] **4.2** — Tafsir service banao (HYBRID CACHE)
  - File: 🆕 [tafsir_service.py](file:///home/ubuntu/Masjid/app/services/quran/tafsir_service.py)
  - Same pattern as translation service
  - Verify: Test with Ibn Kathir tafsir

- [ ] **4.3** — Translation + Tafsir API endpoints
  - Files:
    - 🆕 [quran/translations.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/translations.py)
    - 🆕 [quran/tafsirs.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/tafsirs.py)
  - Endpoints:
    ```
    GET /api/quran/translations/resources      → Available translations list
    GET /api/quran/translations/{id}/by-surah/{n}  → Translation for surah
    GET /api/quran/translations/{id}/by-ayah/{key} → Translation for ayah

    GET /api/quran/tafsirs/resources            → Available tafsirs list
    GET /api/quran/tafsirs/{id}/by-ayah/{key}   → Tafsir for ayah
    ```
  - Auth: No auth (public read)
  - Verify: Urdu + English translations test karo

---

## PHASE 5: Audio System
> Tilawat sunne ka system

- [ ] **5.1** — Audio service banao
  - File: 🆕 [audio_service.py](file:///home/ubuntu/Masjid/app/services/quran/audio_service.py)
  - Kya karna hai:
    ```
    AudioService:
    ├── get_reciters(db)             → All reciters from DB
    ├── get_reciter(db, id)          → Single reciter detail
    ├── get_audio_by_ayah(db, verse_key, reciter_id)
    │   → DB check → miss? fetch API → cache → return URL
    ├── get_audio_by_surah(db, surah_num, reciter_id)
    │   → All ayah audio URLs for a surah
    ├── get_audio_by_page(db, page_num, reciter_id)
    └── get_chapter_audio(db, surah_num, reciter_id)
        → Full chapter audio (single file URL)
    ```
  - Rule: SIRF URLs store karo — audio files QuranicAudio.com se stream honge
  - Verify: Audio URL kaam kare browser mein

- [ ] **5.2** — Audio API endpoints
  - File: 🆕 [quran/audio.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/audio.py)
  - Endpoints:
    ```
    GET /api/quran/audio/reciters              → Reciters list
    GET /api/quran/audio/reciters/{id}         → Reciter detail
    GET /api/quran/audio/by-ayah/{key}?reciter={id}   → Ayah audio
    GET /api/quran/audio/by-surah/{n}?reciter={id}    → Surah audio URLs
    GET /api/quran/audio/by-page/{n}?reciter={id}     → Page audio URLs
    GET /api/quran/audio/chapter/{n}?reciter={id}     → Full chapter audio
    ```
  - Verify: Audio URLs valid hain, browser mein play ho

---

## PHASE 6: Search + Bookmarks + Reading History
> User engagement features

- [ ] **6.1** — Search service banao
  - File: 🆕 [search_service.py](file:///home/ubuntu/Masjid/app/services/quran/search_service.py)
  - Kya karna hai:
    ```
    SearchService:
    ├── search_quran(db, query, language, page, size)
    │   → Arabic search: PostgreSQL tsvector on text_uthmani
    │   → Translation search: tsvector on QuranTranslation.text
    │   → Verse key search: direct lookup "2:255"
    │   → Fallback: Quran.com Search API
    └── get_suggestions(db, query)
        → Autocomplete from surah names + ayah text
    ```
  - DB Setup: GIN index chahiye text columns pe
  - Verify: Arabic + English search test karo

- [ ] **6.2** — Bookmark service banao
  - File: 🆕 [bookmark_service.py](file:///home/ubuntu/Masjid/app/services/quran/bookmark_service.py)
  - Kya karna hai:
    ```
    BookmarkService:
    ├── get_bookmarks(db, user_id, folder)    → User's bookmarks
    ├── add_bookmark(db, user_id, ayah_id, folder, note)
    ├── remove_bookmark(db, user_id, bookmark_id)
    ├── get_last_read(db, user_id)            → Last read position
    └── update_last_read(db, user_id, ayah_id, page)
    ```
  - Verify: CRUD operations test karo

- [ ] **6.3** — Reading history service banao
  - File: 🆕 [reading_service.py](file:///home/ubuntu/Masjid/app/services/quran/reading_service.py)
  - Kya karna hai:
    ```
    ReadingService:
    ├── log_reading(db, user_id, ayah_id, duration_secs)
    ├── get_stats(db, user_id, period)   → Daily/weekly/monthly stats
    ├── get_streak(db, user_id)          → Current reading streak
    └── get_khatam_progress(db, user_id) → % completion of full Quran
    ```
  - Verify: Stats calculation test karo

- [ ] **6.4** — Search + Bookmark + Reading endpoints
  - Files:
    - 🆕 [quran/search.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/search.py)
    - 🆕 [quran/bookmarks.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/bookmarks.py)
    - 🆕 [quran/reading.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/reading.py)
  - Endpoints:
    ```
    # Search (public)
    GET  /api/quran/search?q=...&language=...&page=1&size=20
    GET  /api/quran/search/suggestions?q=...

    # Bookmarks (auth required)
    GET    /api/quran/bookmarks?folder=...
    POST   /api/quran/bookmarks
    DELETE /api/quran/bookmarks/{id}
    GET    /api/quran/bookmarks/last-read
    PUT    /api/quran/bookmarks/last-read

    # Reading (auth required)
    POST /api/quran/reading/log
    GET  /api/quran/reading/stats?period=weekly
    GET  /api/quran/reading/streak
    GET  /api/quran/reading/khatam-progress
    ```
  - Verify: Auth check, CRUD test

---

## PHASE 7: Hifz Engine 🧠 (Sabse Important!)
> Hafiz ke liye memorization system — FSRS + Sabaq/Sabqi/Manzil

- [ ] **7.1** — FSRS Algorithm implement karo
  - File: 🆕 [hifz_service.py](file:///home/ubuntu/Masjid/app/services/quran/hifz_service.py)
  - Kya karna hai — **FSRS (Free Spaced Repetition Scheduler)**:
    ```
    HifzEngine:
    ├── calculate_next_review(progress, quality_rating)
    │   Input:  HifzProgress record + grade (again/hard/good/easy)
    │   Output: (new_interval, new_ease_factor, next_review_date)
    │   
    │   Algorithm:
    │   - "again" (1): interval=1, ease×0.8, restart
    │   - "hard"  (2): interval×1.2, ease×0.85
    │   - "good"  (3): interval×ease, ease unchanged
    │   - "easy"  (4): interval×ease×1.3, ease×1.05
    │   - Minimum interval = 1 day
    │   - Minimum ease = 1.3
    │
    ├── get_dashboard(db, user_id)
    │   → Today's Sabaq + Sabqi + Manzil + stats
    │
    ├── get_due_today(db, user_id)
    │   → SELECT * FROM hifz_progress
    │     WHERE user_id=X AND next_review_date <= today
    │     ORDER BY next_review_date ASC
    │
    ├── start_sabaq(db, user_id, start_key, end_key)
    │   → Create HifzProgress records for new ayahs
    │   → status = "learning"
    │
    ├── grade_ayah(db, user_id, ayah_id, quality)
    │   → Call calculate_next_review()
    │   → Update HifzProgress record
    │   → Update streak
    │
    ├── get_review_queue(db, user_id)
    │   → Sabqi: Due items from last 7 days
    │   → Manzil: Rotating juz review
    │   → Combine + sort by priority
    │
    ├── log_session(db, user_id, session_data)
    │   → Create HifzSession record
    │
    ├── get_stats(db, user_id)
    │   → Total memorized/learning/new counts
    │   → Per surah/juz breakdown
    │
    ├── get_heatmap(db, user_id)
    │   → Surah × strength matrix
    │   → Each surah: % memorized, avg strength
    │
    ├── get_streak(db, user_id)
    │   → Consecutive days with at least 1 review
    │
    └── get_self_test_prompt(db, user_id, mode, verse_key)
        → mode="hidden": Return ayah number only
        → mode="first_letter": Return first letter of each word
        → mode="fill_gap": Hide random words
        → mode="next_ayah": Show one ayah, ask for next
    ```
  - **CRITICAL**: FSRS algorithm sahi hona chahiye — ye core feature hai!
  - Verify: Unit tests with different grade sequences

- [ ] **7.2** — Hifz API endpoints banao
  - File: 🆕 [quran/hifz.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/hifz.py)
  - Endpoints (ALL auth required):
    ```
    # Dashboard
    GET  /api/quran/hifz/dashboard           → Today's overview
    GET  /api/quran/hifz/due-today           → Ayahs due for review
    GET  /api/quran/hifz/stats               → Overall analytics
    GET  /api/quran/hifz/heatmap             → Visual heatmap data
    GET  /api/quran/hifz/streak              → Current streak

    # Sabaq (New Lesson)
    POST /api/quran/hifz/sabaq/start         → {start_key:"2:1", end_key:"2:5"}
    GET  /api/quran/hifz/sabaq/current       → Current new lesson

    # Review
    GET  /api/quran/hifz/review/queue        → Today's review queue
    POST /api/quran/hifz/review/grade        → {ayah_id:X, grade:"good"}
    POST /api/quran/hifz/review/session      → Log complete session

    # Self-Test
    GET  /api/quran/hifz/test/prompt?mode=hidden&verse_key=2:5
    
    # Progress
    GET  /api/quran/hifz/progress/by-surah   → Per surah progress
    GET  /api/quran/hifz/progress/by-juz     → Per juz progress
    PUT  /api/quran/hifz/progress/mark-memorized → Bulk mark

    # Settings
    GET  /api/quran/hifz/settings            → User's hifz preferences
    PUT  /api/quran/hifz/settings            → Update preferences
    ```
  - Feature Flag: `QURAN_HIFZ` se controlled
  - Verify: Full flow test — start sabaq → practice → grade → check dashboard

---

## PHASE 8: Teaching Partner (AI Prep)
> On-device AI ke liye backend support

- [ ] **8.1** — AI model info endpoint banao
  - File: Hifz endpoint file mein add karo
  - Kya karna hai:
    ```
    GET /api/quran/hifz/ai-model-info
    Response:
    {
      "model_name": "whisper-tiny-ar-quran",
      "model_url": "https://huggingface.co/tarteel-ai/whisper-tiny-ar-quran",
      "model_size_mb": 75,
      "quantized": true,
      "download_url": "https://..../model.bin",  ← CDN link
      "version": "1.0.0",
      "min_ram_gb": 4,
      "supported_platforms": ["android", "ios"]
    }
    ```
  - Ye endpoint mobile app ko batayega kaunsa model download karna hai
  - Verify: Response valid JSON ho

- [ ] **8.2** — Verse matching engine banao (server-side backup)
  - File: 🆕 [verse_matcher.py](file:///home/ubuntu/Masjid/app/services/quran/verse_matcher.py)
  - Kya karna hai:
    ```
    VerseMatcher:
    ├── match_text_to_ayah(db, recognized_text)
    │   → Fuzzy string matching against quran_ayah table
    │   → Return top 3 matches with confidence score
    │   → Uses: SequenceMatcher or rapidfuzz library
    │
    └── check_recitation(db, recognized_words, verse_key)
        → Compare word-by-word against known ayah
        → Return: {correct: [], missed: [], extra: []}
    ```
  - Ye sirf BACKUP hai — primary matching mobile pe hoga
  - Verify: Test with correct + incorrect recitation text

---

## PHASE 9: Ustaad Mode 👨‍🏫 (Teacher-Student)
> Real insaan teacher ke liye system

- [ ] **9.1** — Ustaad service banao
  - File: 🆕 [ustaad_service.py](file:///home/ubuntu/Masjid/app/services/quran/ustaad_service.py)
  - Kya karna hai:
    ```
    UstaadService:
    # Teacher functions
    ├── get_students(db, teacher_id)          → List enrolled students
    ├── invite_student(db, teacher_id, email/code)
    ├── create_assignment(db, teacher_id, student_id, data)
    │   → Create HifzAssignment record
    │   → Send notification to student
    ├── get_pending_submissions(db, teacher_id)
    ├── grade_submission(db, teacher_id, submission_id, grade_data)
    │   → Update HifzSubmission with grade + feedback
    │   → Send notification to student
    ├── get_student_progress(db, teacher_id, student_id)
    └── get_student_heatmap(db, teacher_id, student_id)

    # Student functions
    ├── get_my_assignments(db, student_id, status)
    ├── get_assignment_detail(db, student_id, assignment_id)
    ├── submit_assignment(db, student_id, assignment_id, data)
    │   → Create HifzSubmission
    │   → Send notification to teacher
    ├── get_my_teachers(db, student_id)
    └── get_my_grades(db, student_id)
    ```
  - Notifications: Existing FCM notification system use karo
  - Verify: Full flow — assign → submit → grade

- [ ] **9.2** — Ustaad API endpoints
  - File: 🆕 [quran/ustaad.py](file:///home/ubuntu/Masjid/app/api/v1/endpoints/user/quran/ustaad.py)
  - Endpoints (ALL auth required):
    ```
    # Teacher endpoints
    GET  /api/quran/ustaad/students
    POST /api/quran/ustaad/students/invite
    POST /api/quran/ustaad/assignments
    GET  /api/quran/ustaad/assignments
    GET  /api/quran/ustaad/submissions/pending
    PUT  /api/quran/ustaad/submissions/{id}/grade
    GET  /api/quran/ustaad/students/{id}/progress
    GET  /api/quran/ustaad/students/{id}/heatmap

    # Student endpoints
    GET  /api/quran/ustaad/my-assignments
    GET  /api/quran/ustaad/my-assignments/{id}
    POST /api/quran/ustaad/my-assignments/{id}/submit
    GET  /api/quran/ustaad/my-teachers
    GET  /api/quran/ustaad/my-grades
    ```
  - Feature Flag: `QURAN_USTAAD` se controlled
  - Verify: 2 user accounts se test — 1 teacher, 1 student

---

## PHASE 10: Testing + Polish + Verify
> Sab kuch test karo, sab kuch check karo

- [ ] **10.1** — Unit tests likhho (services)
  - File: 🆕 `tests/services/quran/` folder
    ```
    tests/services/quran/
    ├── test_surah_service.py
    ├── test_ayah_service.py
    ├── test_translation_service.py
    ├── test_audio_service.py
    ├── test_search_service.py
    ├── test_bookmark_service.py
    ├── test_reading_service.py
    ├── test_hifz_engine.py       ← CRITICAL: FSRS tests
    └── test_ustaad_service.py
    ```
  - Verify: `pytest tests/services/quran/ -v` — all pass

- [ ] **10.2** — API endpoint tests likhho
  - File: 🆕 `tests/api/test_quran.py`
  - Cover: Sab endpoints ka happy path + error cases
  - Verify: `pytest tests/api/test_quran.py -v` — all pass

- [ ] **10.3** — Ruff linting check karo
  - Command: `ruff check app/models/quran.py app/services/quran/ app/api/v1/endpoints/user/quran/`
  - Verify: No F821, no F401, clean code

- [ ] **10.4** — Data import full test
  - Command: Celery task trigger karo `import_full_quran()`
  - Verify:
    - 114 surahs in `quran_surah`
    - 6,236 ayahs in `quran_ayah`
    - ~77,000 words in `quran_word`
    - 30 juz in `quran_juz`
    - Reciters in `quran_reciter`

- [ ] **10.5** — Full flow integration test
  - Scenario:
    1. Import full Quran ✓
    2. Browse surahs → open surah → read ayahs ✓
    3. Get translation (Urdu) → hybrid cache works ✓
    4. Play audio → URL valid ✓
    5. Search "رحمن" → results aayein ✓
    6. Add bookmark → retrieve → delete ✓
    7. Start Hifz sabaq → practice → grade → check dashboard ✓
    8. Teacher assign → student submit → teacher grade ✓
  - Verify: End-to-end flow without errors

- [ ] **10.6** — Performance check
  - Check: Surah listing < 50ms
  - Check: Ayah by page < 100ms
  - Check: Search < 200ms
  - Check: Hifz dashboard < 100ms
  - Tool: `time curl` ya app logs se check karo

- [ ] **10.7** — Purani quran_service.py cleanup
  - Delete: `app/services/quran_service.py` (replaced by package)
  - Verify: No import errors anywhere

- [ ] **10.8** — Documentation update
  - File: Update README.md with Quran module info
  - File: Update GEMINI.md — Task 19 complete mark karo
  - Verify: Docs accurate hain

- [ ] **10.9** — Git commit + merge prep
  - Commands:
    ```bash
    git add -A
    git commit -m "feat: Add Smart Quran Module with Hifz Engine & Ustaad Mode"
    ```
  - Verify: Clean commit, no secrets exposed

---

## 📊 SUMMARY TABLE

| Phase | Tasks | New Files | Priority |
|-------|-------|-----------|----------|
| **0. Setup** | 5 | 0 | 🔴 Do First |
| **1. DB Models** | 5 | 1 (quran.py) + 1 migration | 🔴 Do First |
| **2. API Client + Import** | 3 | 2 (api_client, quran_import) | 🔴 Do First |
| **3. Reading APIs** | 5 | 5 (schemas, services, endpoints) | 🟡 Core |
| **4. Translation + Tafsir** | 3 | 4 (services + endpoints) | 🟡 Core |
| **5. Audio** | 2 | 2 (service + endpoint) | 🟡 Core |
| **6. Search + Bookmarks** | 4 | 6 (services + endpoints) | 🟢 Important |
| **7. Hifz Engine** | 2 | 2 (service + endpoint) | 🔴 Critical! |
| **8. Teaching Partner** | 2 | 2 (endpoint + matcher) | 🟢 Important |
| **9. Ustaad Mode** | 2 | 2 (service + endpoint) | 🟢 Important |
| **10. Testing** | 9 | 3 (test files) | 🔴 Must Do |
| **TOTAL** | **42 tasks** | **~28 new files** | |

---

## ⏱️ Estimated Time

| Phase | Estimated Time |
|-------|---------------|
| Phase 0-1 (Setup + Models) | ~2-3 hours |
| Phase 2 (API Client + Import) | ~3-4 hours |
| Phase 3 (Reading APIs) | ~3-4 hours |
| Phase 4 (Translation + Tafsir) | ~2-3 hours |
| Phase 5 (Audio) | ~1-2 hours |
| Phase 6 (Search + Bookmarks) | ~2-3 hours |
| Phase 7 (Hifz Engine) | ~4-5 hours |
| Phase 8 (Teaching Partner) | ~1-2 hours |
| Phase 9 (Ustaad Mode) | ~3-4 hours |
| Phase 10 (Testing) | ~3-4 hours |
| **TOTAL** | **~24-34 hours** |

> [!TIP]
> **Suggestion**: Phase 0-3 ek din mein karo (basic Quran reading). Phase 4-6 doosre din. Phase 7-9 teesre din. Phase 10 chauthe din. **~4 din mein complete ho sakta hai!**
