# Cline's Memory Bank - 7DaysToBackup

Bu proje **7 Days to Die Save Yedekleme Aracı**'dır. Aşağıdaki Memory Bank dosyaları projenin tüm bağlamını içerir.

## Proje Özeti
7 Days to Die oyunu için save dosyalarını yönetmeye yarayan cross-platform bir masaüstü uygulaması. PySide6 (Qt6) ile geliştirilmiş, koyu temalı ve çoklu dil destekli bir GUI sunuyor.

## Memory Bank Structure

Memory Bank `memory-bank/` klasöründe bulunur ve şu dosyalardan oluşur:

```
memory-bank/
├── projectbrief.md      # Proje temelleri ve gereksinimler
├── productContext.md    # Ürün vizyonu ve UX hedefleri
├── techContext.md       # Teknik detaylar ve kurulum
├── systemPatterns.md    # Mimari ve tasarım desenleri
├── activeContext.md     # Mevcut çalışma durumu
└── progress.md          # İlerleme ve yapılacaklar
```

flowchart TD
    PB[projectbrief.md] --> PC[productContext.md]
    PB --> SP[systemPatterns.md]
    PB --> TC[techContext.md]

    PC --> AC[activeContext.md]
    SP --> AC
    TC --> AC

    AC --> P[progress.md]

### Core Files (Required)
1. `projectbrief.md`
   - Foundation document that shapes all other files
   - Created at project start if it doesn't exist
   - Defines core requirements and goals
   - Source of truth for project scope

2. `productContext.md`
   - Why this project exists
   - Problems it solves
   - How it should work
   - User experience goals

3. `activeContext.md`
   - Current work focus
   - Recent changes
   - Next steps
   - Active decisions and considerations
   - Important patterns and preferences
   - Learnings and project insights

4. `systemPatterns.md`
   - System architecture
   - Key technical decisions
   - Design patterns in use
   - Component relationships
   - Critical implementation paths

5. `techContext.md`
   - Technologies used
   - Development setup
   - Technical constraints
   - Dependencies
   - Tool usage patterns

6. `progress.md`
   - What works
   - What's left to build
   - Current status
   - Known issues
   - Evolution of project decisions

### Additional Context
Create additional files/folders within memory-bank/ when they help organize:
- Complex feature documentation
- Integration specifications
- API documentation
- Testing strategies
- Deployment procedures

## Core Workflows

### Plan Mode
flowchart TD
    Start[Start] --> ReadFiles[Read Memory Bank]
    ReadFiles --> CheckFiles{Files Complete?}

    CheckFiles -->|No| Plan[Create Plan]
    Plan --> Document[Document in Chat]

    CheckFiles -->|Yes| Verify[Verify Context]
    Verify --> Strategy[Develop Strategy]
    Strategy --> Present[Present Approach]

### Act Mode
flowchart TD
    Start[Start] --> Context[Check Memory Bank]
    Context --> Update[Update Documentation]
    Update --> Execute[Execute Task]
    Execute --> Document[Document Changes]

## Documentation Updates

Memory Bank updates occur when:
1. Discovering new project patterns
2. After implementing significant changes
3. When user requests with **update memory bank** (MUST review ALL files)
4. When context needs clarification

flowchart TD
    Start[Update Process]

    subgraph Process
        P1[Review ALL Files]
        P2[Document Current State]
        P3[Clarify Next Steps]
        P4[Document Insights & Patterns]

        P1 --> P2 --> P3 --> P4
    end

    Start --> Process

---

## Proje Yapılacaklar Listesi

### 🔴 Yüksek Öncelik
- [ ] **Kod Refaktörü** - Ana dosyanın okunurluk için bölünmesi
  - [ ] `ui.py` - Arayüz bileşenleri ve tema
  - [ ] `utils.py` - Yardımcı fonksiyonlar (OS tespiti, yol belirleme)
  - [ ] `file_ops.py` - Dosya işlemleri (yedekleme, silme, zip)
- [ ] Unit test coverage ekleme

### 🟡 Orta Öncelik
- [ ] Ayarlar penceresi
- [ ] Özel save yolu belirleme (kullanıcı tanımlı)
- [ ] Yedek geçmişi görüntüleme
- [ ] Birden fazla save seçimi desteği

### 🟢 Düşük Öncelik
- [ ] Otomatik yedekleme (zamanlayıcı)
- [ ] Steam entegrasyonu
- [ ] Cloud backup desteği
- [ ] Ek dil desteği (Almanca, Fransızca vb.)

## Dosya Bölme Planı

Mevcut `7DaysToBackup.py` dosyası 329 satır. Okunurluk için şu şekilde bölünebilir:

```
src/
├── __init__.py
├── main.py           # Entry point, sadece main() fonksiyonu
├── ui/
│   ├── __init__.py
│   ├── window.py     # SaveManagerWindow sınıfı
│   └── theme.py      # create_dark_palette() ve tema ayarları
├── core/
│   ├── __init__.py
│   ├── platform.py   # get_os_type(), get_saves_path(), get_desktop_path()
│   └── file_ops.py   # Dosya işlemleri (backup, delete, export, import)
└── i18n/
    ├── __init__.py
    └── languages.py  # LANGUAGES dictionary
```

---

REMEMBER: After every memory reset, I begin completely fresh. The Memory Bank is my only link to previous work. It must be maintained with precision and clarity, as my effectiveness depends entirely on its accuracy.