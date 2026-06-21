# Prayer Time Rounding System — Design Document

## Terms (English → Aam Bhasha)

| English | Matlab |
|---------|--------|
| **Offset** (faasla) | "Kitni der baad" — jaise namaz shuru hone ke 30 min BAAD azan dena |
| **Azan Offset** | Namaz ka waqt shuru hua, uske kitni der BAAD azan di jaaye |
| **Jamaat Offset** | Azan ke kitni der BAAD jamaat khadi ki jaaye |
| **Rounding** (gol karna) | Beech wale number ko nazdeeki pura number pe le jaana. Jaise 4:14 ko 4:15 banana |
| **Rounding Interval** (gol karne ka hisab) | Kitne-kitne minute ke pura number chahiye: 15 min = 4:00, 4:15, 4:30, 4:45 |
| **Fixed Mode** (jamya hua) | Admin ne seedha time likh diya, koi calculation nahi |
| **Dynamic Mode** (khudkaar) | Computer raw time + offset se calculate kare |

---

## Azan Offset kya hai — Example se samjho

```
Fajr ka waqt SHURU hota hai 3:44 AM pe (ye UME calculate karta hai)

Lekin masjid mein 3:44 pe AZAN nahi dete!
Kyun? Kyunki log abhi so rahe hain. Thoda waqt chahiye tayyari ka.

Imam sahab bolte hain: "Fajr shuru hone ke 30 minute BAAD azan do"

Ye 30 minute = AZAN OFFSET

  Fajr Start = 3:44 AM
  Azan Offset = 30 min
  Azan = 3:44 + 30 = 4:14 AM ← Is waqt azan hogi

Ab Jamaat ka hisab:
  Jamaat Offset = 15 min (azan ke 15 min baad)
  Jamaat = 4:14 + 15 = 4:29 AM ← Is waqt jamaat khadi hogi
```

> [!NOTE]
> **Azan Offset** = Namaz SHURU hone se → AZAN tak ka faasla
> **Jamaat Offset** = AZAN se → JAMAAT tak ka faasla

---

## Rounding (Gol Karna) kya hai

```
Computer ne nikala: Azan = 4:14 AM

4:14 koi masjid nahi likhti! Ye beech ka number hai.
Imam sahab chahte hain: 4:00, 4:15, 4:30, 4:45 (15-15 ke pura number)

4:14 sabse nazdeek kiske hai?
  4:14 se 4:00 = 14 min door
  4:14 se 4:15 = 1 min door  ← YE NAZDEEK HAI!
  
Rounding karega: 4:14 → 4:15 ✅

Board pe likhdo: AZAN 4:15 AM
```

**Rounding Interval ke options:**

| Interval | Pura numbers | Kab use karein |
|----------|-------------|----------------|
| OFF (band) | 7:10, 7:11, 7:12... (jaise hai waise) | Maghrib — exact chahiye |
| 5 min | 7:00, 7:05, 7:10, 7:15... | Chhota rounding |
| 10 min | 7:00, 7:10, 7:20, 7:30... | Darmiyana |
| 15 min | 7:00, 7:15, 7:30, 7:45... | **Zyada masjidein ye use karti hain** |
| 30 min | 7:00, 7:30, 8:00, 8:30... | Bada rounding — bahut kam badle |

---

## Admin Panel — Paancho Namaz

```
┌──────────────────────────────────────────────────────────┐
│                    FAJR                                  │
│  Mode: ● Dynamic (khudkaar)   ○ Fixed (jamya hua)       │
│                                                          │
│  Azan Offset (faasla):          [30 min]                 │
│     ↑ "Fajr shuru hone ke 30 min baad azan"              │
│                                                          │
│  Jamaat Offset (faasla):        [15 min]                 │
│     ↑ "Azan ke 15 min baad jamaat"                       │
│                                                          │
│  Rounding (gol karna):          [15 min]                 │
│     ↑ "4:00, 4:15, 4:30, 4:45 mein se nazdeek wala"     │
├──────────────────────────────────────────────────────────┤
│                    DHUHR — FIXED (jamya hua)             │
│  Mode: ○ Dynamic   ● Fixed                              │
│                                                          │
│  Azan:   [1:00 PM]                                       │
│  Jamaat: [1:30 PM]                                       │
│                                                          │
│  ⚠️ Fixed mein Offset aur Rounding DISABLE hain          │
│     Admin ne jo likha wahi dikhega, koi calculation nahi  │
├──────────────────────────────────────────────────────────┤
│                    ASR                                    │
│  Mode: ● Dynamic   ○ Fixed                              │
│                                                          │
│  Azan Offset:  [30 min]   "Asr shuru ke 30 min baad"     │
│  Jamaat:       [15 min]   "Azan ke 15 min baad"          │
│  Rounding:     [15 min]   "5:00, 5:15, 5:30, 5:45..."   │
├──────────────────────────────────────────────────────────┤
│                    MAGHRIB                                │
│  Mode: ● Dynamic   ○ Fixed                              │
│                                                          │
│  Azan Offset:  [3 min]    "Suraj dube ke 3 min baad"     │
│  Jamaat:       [5 min]    "Azan ke 5 min baad"           │
│  Rounding:     [OFF]      "Exact timing, gol nahi karna" │
│                                                          │
│  ℹ️ Maghrib mein Imam exact rakhte hain isliye OFF        │
├──────────────────────────────────────────────────────────┤
│                    ISHA                                   │
│  Mode: ● Dynamic   ○ Fixed                              │
│                                                          │
│  Azan Offset:  [45 min]   "Isha shuru ke 45 min baad"    │
│  Jamaat:       [20 min]   "Azan ke 20 min baad"          │
│  Rounding:     [15 min]   "9:00, 9:15, 9:30, 9:45..."   │
└──────────────────────────────────────────────────────────┘
```

---

## 7 Din ka Example — Paancho Namaz

Raw times (UME se aaye — garmi mein roz thoda late ho raha):

| Din | Fajr Start | Asr Start | Maghrib Start | Isha Start |
|-----|-----------|-----------|---------------|------------|
| 1 | 3:44 AM | 5:01 PM | 7:07 PM | 8:39 PM |
| 2 | 3:44 AM | 5:02 PM | 7:08 PM | 8:40 PM |
| 3 | 3:45 AM | 5:03 PM | 7:09 PM | 8:42 PM |
| 4 | 3:46 AM | 5:04 PM | 7:10 PM | 8:44 PM |
| 5 | 3:47 AM | 5:06 PM | 7:11 PM | 8:46 PM |
| 6 | 3:48 AM | 5:07 PM | 7:12 PM | 8:48 PM |
| 7 | 3:50 AM | 5:08 PM | 7:13 PM | 8:50 PM |

---

### FAJR — Dynamic, Azan Offset=30, Jamaat Offset=15, Rounding=15

```
Din 1: Start 3:44 + 30min = 4:14 → Rounding (gol karna) → 4:15 AM
       AZAN = 4:15 AM    JAMAAT = 4:15 + 15 = 4:30 AM

Din 2: 3:44 + 30 = 4:14 → gol → 4:15    SAME ✅
Din 3: 3:45 + 30 = 4:15 → gol → 4:15    SAME ✅
Din 4: 3:46 + 30 = 4:16 → gol → 4:15    SAME ✅
Din 5: 3:47 + 30 = 4:17 → gol → 4:15    SAME ✅
Din 6: 3:48 + 30 = 4:18 → gol → 4:15    SAME ✅
Din 7: 3:50 + 30 = 4:20 → gol → 4:15    SAME ✅
       (4:20 se 4:15=5min door, 4:30=10min door. 5<10 isliye 4:15)

BOARD PE 7 DIN: AZAN 4:15 AM | JAMAAT 4:30 AM (kabhi nahi badla!) ✅
```

### DHUHR — FIXED (koi calculation nahi)

```
Din 1-7: AZAN = 1:00 PM | JAMAAT = 1:30 PM

Admin ne 1:00/1:30 likha. Bas wahi dikhega.
Jab ADMIN khud badle, tab badle. Computer kuch nahi karega.
```

### ASR — Dynamic, Azan Offset=30, Jamaat Offset=15, Rounding=15

```
Din 1: 5:01 + 30 = 5:31 → gol → 5:30    AZAN=5:30 PM  JAMAAT=5:45 PM
Din 2: 5:02 + 30 = 5:32 → gol → 5:30    SAME ✅
Din 3: 5:03 + 30 = 5:33 → gol → 5:30    SAME ✅
Din 4: 5:04 + 30 = 5:34 → gol → 5:30    SAME ✅
Din 5: 5:06 + 30 = 5:36 → gol → 5:30    SAME ✅
Din 6: 5:07 + 30 = 5:37 → gol → 5:30    SAME ✅
Din 7: 5:08 + 30 = 5:38 → gol → 5:45    BADLA!
       (5:38 se 5:30=8min, 5:45=7min. 7<8 isliye 5:45 pe gaya)

       AZAN = 5:45 PM  JAMAAT = 5:45 + 15 = 6:00 PM ✅
```

### MAGHRIB — Dynamic, Azan Offset=3, Jamaat Offset=5, Rounding=OFF

```
Din 1: 7:07 + 3 = 7:10    AZAN=7:10 PM  JAMAAT=7:15 PM
Din 2: 7:08 + 3 = 7:11    AZAN=7:11 PM  JAMAAT=7:16 PM
Din 3: 7:09 + 3 = 7:12    AZAN=7:12 PM  JAMAAT=7:17 PM
Din 4: 7:10 + 3 = 7:13    AZAN=7:13 PM  JAMAAT=7:18 PM
Din 5: 7:11 + 3 = 7:14    AZAN=7:14 PM  JAMAAT=7:19 PM
Din 6: 7:12 + 3 = 7:15    AZAN=7:15 PM  JAMAAT=7:20 PM
Din 7: 7:13 + 3 = 7:16    AZAN=7:16 PM  JAMAAT=7:21 PM

Rounding OFF hai — har din exact timing. Imam suraj ke hisab se exact rakhte hain.
```

### ISHA — Dynamic, Azan Offset=45, Jamaat Offset=20, Rounding=15

```
Din 1: 8:39 + 45 = 9:24 → gol → 9:30    AZAN=9:30 PM  JAMAAT=9:50 PM
Din 2: 8:40 + 45 = 9:25 → gol → 9:30    SAME ✅
Din 3: 8:42 + 45 = 9:27 → gol → 9:30    SAME ✅
Din 4: 8:44 + 45 = 9:29 → gol → 9:30    SAME ✅
Din 5: 8:46 + 45 = 9:31 → gol → 9:30    SAME ✅
Din 6: 8:48 + 45 = 9:33 → gol → 9:30    SAME ✅
Din 7: 8:50 + 45 = 9:35 → gol → 9:30    SAME ✅

BOARD PE 7 DIN: AZAN 9:30 PM | JAMAAT 9:50 PM ✅
```

---

## Tomorrow (kal ka hisab) — Schedule mein

Schedule mein har din ke saath KAL ki bhi timing aati hai:

```
┌──────────────────────────────────────────────────┐
│ AAJ (Din 6):                                     │
│                                                  │
│ Fajr:    Azan 4:15 AM  | Jamaat 4:30 AM         │
│ Dhuhr:   Azan 1:00 PM  | Jamaat 1:30 PM (Fixed) │
│ Asr:     Azan 5:30 PM  | Jamaat 5:45 PM         │
│ Maghrib: Azan 7:15 PM  | Jamaat 7:20 PM         │
│ Isha:    Azan 9:30 PM  | Jamaat 9:50 PM         │
│                                                  │
│ KAL (Din 7):                                     │
│ Fajr:    Azan 4:15 AM  | Jamaat 4:30 AM         │
│ Dhuhr:   Azan 1:00 PM  | Jamaat 1:30 PM (Fixed) │
│ Asr:     Azan 5:45 PM  | Jamaat 6:00 PM ← BADLA │
│ Maghrib: Azan 7:16 PM  | Jamaat 7:21 PM         │
│ Isha:    Azan 9:30 PM  | Jamaat 9:50 PM         │
└──────────────────────────────────────────────────┘
```

Kal ka hisab bhi WAHI formula: kal ka raw time → offset → rounding.
schedule_service.py mein ye pehle se hota hai. **Koi badlav nahi.**

---

## Current Namaz (abhi kya chal raha) — koi badlav nahi

```
Agar abhi 6:30 PM hai:

  Abhi: ASR chal raha hai
  Shuru: 5:01 PM (raw start time)
  Khatam: 7:07 PM (Maghrib raw start)
  
  Azan: 5:30 PM (jo board pe hai)
  Jamaat: 5:45 PM
  
  Agla: MAGHRIB
  Azan: 7:10 PM
  Jamaat: 7:15 PM
```

Ye raw times se dekhta hai. **Rounding se isme KUCH NAHI BADLEGA.**

---

## Pichle sab sujhav jo yaad rakhne the:

| # | Sujhav | Detail |
|---|--------|--------|
| 1 | **Admin ko live preview** | Jab admin setting kare, dikha do: "Aaj Fajr 3:45 pe hai, apki azan 4:15 pe dikhegi" — Frontend ka kaam, backend raw times dega |
| 2 | **Fiqah Profile (ehtiyat) ki info** | "Barelvi profile ne Fajr mein +1 min ehtiyat already laga di hai" — Admin ko pata chale ki double ehtiyat na lagaye |
| 3 | **Fixed time pe warning** | Jab fixed azan time namaz ke start time ke paas pahunche: "Apka fixed time 4:00 agle hafte start time se pehle aa jayega, update karo" |
| 4 | **Admin ko notification** | Push notification bhejo: "Asr ka timing update karo" |
| 5 | **Maghrib special** | Rounding OFF rakhna default mein — suraj ke saath exact |
| 6 | **Paancho namaz mein** | Har namaz ka apna alag rounding — global nahi |
| 7 | **Fixed + Dynamic dono option** | Admin jo chahe wo chune — Fixed mein offset/rounding disable |

---

## Code mein kya badlega:

| File | Kya | Kitna |
|------|-----|-------|
| [timing_calculator.py](file:///home/ubuntu/Masjid/app/services/prayer_time/timing_calculator.py) | Purana threshold hatao, Rounding dalo | ~20 line |
| [constants.py](file:///home/ubuntu/Masjid/app/core/constants.py) | Rounding field name add karo | 5 line |
| MasjidSettings model | `fajr_rounding=15` jaise fields | DB migration |
| schedule_service.py | **KUCH NAHI** | Zero |
| prayer_time_service.py | **KUCH NAHI** | Zero |
| UME engine | **KUCH NAHI** | Zero |

> [!IMPORTANT]
> Purana threshold ka DB chaining problem — **KHATAM!**
> Rounding stateless (bi-yaad-dasht) hai — na pichle din ki zaroorat, na DB ki.
> Har din ka hisab apne aap mein mukammal hai.
