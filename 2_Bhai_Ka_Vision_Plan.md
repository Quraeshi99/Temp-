# 2. Bhai Ka Vision Plan — Naya Master Plan

> **Created:** 2026-06-21
> **Purpose:** Purana adha-adhura plan hata kar naya clear plan banaya hai tere **REAL vision** ke hisaab se.
> **Rule:** Jab bhi koi naya session ho, ye doc pehle padhna. Phir code likhna.

---

## 🎯 MERA ASLI MAQSAD (One Line)

> **"Backend ko Quran.com jaisa powerful banao (15-line Mushaf, word-by-word, audio, tarjuma, tafsir). UI baad me. Plus 3 original features: Arabic↔Tarjuma alternate audio, word search, Hifz mode."**

---

## 📋 BUILD ORDER (Strict — Is Order Me Karna Hai)

```
🔴 PHASE 1: TEXT QURAN (backend, Quran.com-jaisa)
   ↓
🔴 PHASE 2: AUDIO MODULE (tap-to-play, play-long, Arabic↔Tarjuma alternate)
   ↓
🔴 PHASE 3: HIFZ MODE (Magic Reveal — advance vision)
   ↓
🔴 PHASE 4: UI (Adhan-jaisa clean — baad me)
```

**Rule:** Phase 1 complete bina Phase 2 shuru mat karo. Phase 2 complete bina Phase 3 mat karo.

---

## 🔴 PHASE 1: TEXT QURAN BACKEND (Quran.com-Jaisa)

### Goal:
Backend ko itna powerful banao ki Quran.com ka **har feature** ham le sake. Same-to-same.

### 1.1 Data Foundation (Sabse Pehle)

**Already Done:**
- ✅ 16 DB tables (`app/models/quran.py`)
- ✅ Migration file (`fa998687c22c_add_quran_module_16_tables.py`)
- ✅ API client (`app/services/quran/api_client.py`)
- ✅ Surahs + Ayahs import (`app/tasks/quran_import.py`)

**Karna Hai (Import):**
- 🔴 **Juz metadata import** (30 rows)
- 🔴 **Reciters import** (top 5-10 reciters)
- 🔴 **Translations import** (Urdu, English, Hindi — text)
- 🔴 **Tafsir import** (Ibn Kathir, Jalalayn — text)
- 🔴 **Word-level fields import** — `code_v1`, `code_v2`, `text_uthmani`, `text_indopak`, `line_number`, `page_number`, `audio_url`, `translation`, `transliteration`

### 1.2 Quran.com-Jaisa Reading APIs

**Endpoints jo banane hain (backend, no UI):**

```
📖 SURAH ENDPOINTS:
GET /api/quran/surahs                    → 114 surahs list
GET /api/quran/surahs/{number}           → Single surah detail
GET /api/quran/surahs/{number}/info      → Surah background info

📖 AYAH ENDPOINTS (Sabse Important!):
GET /api/quran/ayahs/by-surah/{n}        → Ayahs of surah
GET /api/quran/ayahs/by-page/{n}         → Ayahs on a Mushaf page (1-604)
GET /api/quran/ayahs/by-juz/{n}          → Ayahs of a Juz (1-30)
GET /api/quran/ayahs/by-hizb/{n}         → Ayahs of a Hizb (1-60)
GET /api/quran/ayahs/{verse_key}         → Single ayah "2:255"
GET /api/quran/ayahs/random              → Random ayah

📖 TRANSLATION ENDPOINTS:
GET /api/quran/translations/resources    → Available translations list
GET /api/quran/translations/{id}/by-surah/{n}
GET /api/quran/translations/{id}/by-ayah/{key}

📖 TAFSIR ENDPOINTS:
GET /api/quran/tafsirs/resources         → Available tafsirs list
GET /api/quran/tafsirs/{id}/by-ayah/{key}
```

### 1.3 The 15-Line Mushaf System (Bhai Ka Requirement)

Quran.com ki tarah **15-line Mushaf** rendering support:
- Har word ke paas `code_v1` field hai (15-line font glyph code)
- Har word ke paas `line_number` hai (page par kaunsi line)
- Har word ke paas `page_number` hai (1-604)
- Frontend in codes ko use karke **real book jaisi 15-line page** banayega

**API Response Format (Example — Ayah 2:255 word):**
```json
{
  "position": 1,
  "text_uthmani": "ٱللَّهُ",
  "code_v1": "\ufba3",
  "code_v2": "\ufc93",
  "page_number": 42,
  "line_number": 8,
  "audio_url": "wbw/002_255_001.mp3",
  "translation": {"text": "Allah", "language_name": "english"},
  "transliteration": {"text": "al-lahu"}
}
```

### 1.4 Translation Lines System (Bhai Ka Requirement)

> Bhai: *"fir usme translation ka hai in line wala hame yhi lena baki dusra wala nhi"*

- Translation **inline** dikhegi — alag panel nahi
- User select karega kaunsi translation chahiye (Urdu/English/Hindi)
- API response me `translations: [{text, language}]` array aayega
- Max 2-3 translations ek saath (performance)

---

## 🔴 PHASE 2: AUDIO MODULE (Bhai Ka Special Features)

### 2.1 Word-Level Tap-to-Play (Bhai Ka Requirement)

> Bhai: *"word par tap kro to uski audio play ho jati sirf us word ki jis par tap kiya"*

**How it works:**
1. Har word ka apna `audio_url` hai (word-by-word audio)
2. User word par tap karega → sirf wahi word bajega
3. Yeh data Quran.com API se aata hai (`words=true&word_fields=audio_url`)

**Backend:**
- Word audio URLs database me store karo
- Pattern: `https://audio.qurancdn.com/wbw/002_255_001.mp3`

### 2.2 Play-Long Feature (Bhai Ka Requirement)

> Bhai: *"play long is trha ka option ata hai to jis word pr tap kiya tha whan se jo tumhra qari setting me save kiya tha wo uski audio play ho jati whi se aur age chalne lagti hai"*

**How it works:**
1. User word par long-press ya "Play Long" option tap karega
2. Us word se lekar aage ki saari audio bajegi (full ayah, then next ayah, then next...)
3. Qari = user ki settings me saved reciter

**Backend:**
- GET `/api/quran/audio/stream/{verse_key}?reciter={id}`
- Response: ordered list of audio URLs from that point onward

### 2.3 Mid-Playback Tap-to-Jump (Bhai Ka Requirement)

> Bhai: *"agr tum long audio chal rhi hai aur uske bich me tum kahin aur kisi aur word ke text par tap krte ho to wahan se play hoti bich ka sb skip hojata hai"*

**How it works:**
- Audio chal rahi hai → user doosre word par tap karega
- Pehli audio **stop** → naye word se playback **restart**
- Beech ka sab skip

**Implementation:** Frontend job (audio queue reset). Backend sirf URLs deta hai.

### 2.4 Arabic ↔ Tarjuma Alternate Playback (BHAI KA ORIGINAL FEATURE!)

> Bhai: *"agr user ne play with tarjuma chuna hai to fir hamri ek ayat ouri hogi fir uske bad tarjuma fir agli ayat fir tarjuma"*

**How it works (Frontend Queue):**
```
Queue = [arabic_1:1, urdu_1:1, arabic_1:2, urdu_1:2, arabic_1:3, urdu_1:3, ...]
```

**Backend Response (per ayah):**
```json
{
  "verse_key": "1:1",
  "arabic_audio_url": "https://audio.qurancdn.com/Alafasy/001001.mp3",
  "translation_audio_url": "/local/urdu_shamshad_ali_khan_46kbps/001001.mp3"
}
```

**Local Audio (Already Downloaded!):**
- ✅ Urdu tarjuma audio: `~/Downloads/everyayah_urdu_shamshad/001001.mp3` ... `114006.mp3` (6,236 files, 504 MB, VERIFIED)

### 2.5 Word Highlighting During Playback (Bhai Ka Requirement)

> Bhai: *"quran.com me agr audio play ho rhi hai to jo word qari pad rha hai wo highlight hota hai aur pichle wali ayaton ka jitna pad chuka uska color thoda dark ho jata hai"*

**How it works:**
- Quran.com provides **audio segments** (timestamp per word)
- Jaise qari word padhta hai → us word ka highlight hota hai
- Padhe hue words ka color thoda **dark/dim** ho jata hai

**Backend:**
- Audio segments data import karna hoga (`segments` field in verse audio)
- Format: `[[start_ms, end_ms, word_index], ...]`

### 2.6 Settings Page (Bhai Ka Requirement)

> Bhai: *"qari ki setting, apni bhasha, tarjume ki bhasha, ye sb ya baki sbhi setting jo bhi hongi ya jo ane wale smy me banegi wo ham alg setting wale page me denge asan kr ke complex nhi karenge"*

**Settings (Alg Page, Simple):**
```
- Qari (Reciter) selection — dropdown
- Apni bhasha (App language) — Urdu/English/Hindi
- Tarjuma ki bhasha (Translation language) — Urdu/English/Hindi
- Audio mode: Sirf Arabic / Arabic + Tarjuma alternate
- Script: 15-line / 16-line
- Font size
```

**Backend:**
- `GET /api/quran/settings` → user ki settings
- `PUT /api/quran/settings` → update settings
- `QuranUserSettings` table already bani hai ✅

---

## 🔴 PHASE 3: HIFZ MODE (Bhai Ka Advance Vision)

> **Note:** Ye phase baad me aayega. Pehle Phase 1 + 2 complete.

### Bhai Ka Vision (4 Layers):

**Layer 1: Magic Reveal (Page-Level)**
- Hifz icon → page ke saare words **GAYAB**
- User padhta jata → words **visible** hote jate

**Layer 2: Mistake Tracking**
- Galti pe word **RED**
- Tap karke dekhe: "tune kya bola" vs "sahi kya hai"

**Layer 3: Auto-Detect**
- App khud samjhe user kahan tak padh raha hai
- Real-time tracking

**Layer 4: Dedicated Hifz Mode**
- Full hifz session
- Score, streak, heatmap

> **Implementation detailed plan Phase 3 me likhenge — jab Phase 1+2 complete ho.**

---

## 🎯 IMPORTANT RULES (Bhai Ke Hukum)

### Rule 1: Backend Pehle, UI Baad Me
> *"ham hamra backend hame quran.com ke trha krna hai...fir UI to bad ki bat hai"*

### Rule 2: Complex Settings → Alg Page
> *"setting jo bhi hongi ya jo ane wale smy me banegi wo ham alg setting wale page me dnege asan kr ke complex nhi karenge"*

### Rule 3: Translation Lines = Quran.com Style
> *"translation ka hai in line wala hame yhi lena baki dusra wala nhi"*

### Rule 4: Quran.com-Jaisa Feature Parity
> *"hame hamra backend bilkul quran.com jesa banana hai"*

### Rule 5: 3 Original Features (Quran.com me nahi)
1. Arabic ↔ Tarjuma alternate audio playback
2. Pure Quran me word search
3. Hifz Magic Reveal mode

---

## 📦 DATA SOURCES (Verified)

| Data | Source | Status |
|------|--------|--------|
| Arabic text (6,236 ayahs) | Quran.com API v4 | 🔴 Import needed |
| Word-level data (code_v1, line_number) | Quran.com API v4 | 🔴 Import needed |
| Translations text (Urdu/Eng/Hindi) | Quran.com API v4 | 🔴 Import needed |
| Tafsir text (Ibn Kathir) | Quran.com API v4 | 🔴 Import needed |
| Arabic audio URLs | Quran.com / EveryAyah | 🔴 Import needed |
| **Urdu tarjuma audio** | EveryAyah (downloaded) | ✅ **DONE** (6,236 files, verified) |
| Reciter metadata | Quran.com API v4 | 🔴 Import needed |
| Audio segments (word highlight) | Quran.com API v4 | 🔴 Import needed |

---

## ✅ ALREADY HAVE (Purana Kaam)

| Item | File | Status |
|------|------|--------|
| 16 DB tables | `app/models/quran.py` | ✅ Solid |
| Migration | `fa998687c22c_add_quran_module_16_tables.py` | ✅ |
| API client | `app/services/quran/api_client.py` | ✅ Solid |
| Surah + Ayah import | `app/tasks/quran_import.py` | ⚠️ Partial (juz/translation/tafsir missing) |
| Hifz FSRS engine | `app/services/quran/hifz_service.py` | ⚠️ Buggy (Phase 3 me fix) |

---

## 🗑️ CLEANUP NEEDED (Pehle Karna Hai)

1. Delete `app/services/quran_service.py` (zombie file, 2 saal purana)
2. Delete junk files: `=2024.1`, `=4.1.5`, `=6.0.0`
3. Commit `app/api/v1/endpoints/user/hifz.py` (untracked)
4. Git branch banao: `feature/quran-text-phase1`

---

## 📊 WEEKLY ROADMAP

| Week | Focus | Deliverable |
|------|-------|-------------|
| **Week 1** | Phase 1 — Text Foundation | Quran.com-jaisa reading backend, import complete, 15-line Mushaf data |
| **Week 2** | Phase 2 — Audio Module | Tap-to-play, play-long, Arabic↔Tarjuma, highlight, settings |
| **Week 3** | Phase 3 — Hifz Mode | Magic Reveal, red mistake, auto-detect |
| **Week 4** | Phase 4 — UI | Adhan-jaisa clean frontend |

---

## 🔒 DATA INTEGRITY (Critical)

> Bhai ka hukum: *"ek ayat bhi chhuti to kam gad bad ho jayega"*

**Rules:**
- Kanzul Iman (Aala Hazrat) ko "Unverified" mark karo until Admin approves
- `QuranTranslation` me `is_verified: Boolean` column add karo (abhi missing)
- Har text `verse_key` + `resource_id` se lock hoga
- Mismatch impossible hona chahiye

---

**END OF VISION PLAN**

> **Next Action:** Phase 1 start — git cleanup + complete import + reading APIs.
