# ATmega32U4 Configurator — Upute za razvoj

## Pregled projekta

GUI Python/PyQt6 konfigurator za mikrokontroler ATmega32U4 (TQFP-44).
Vizualno prikazuje chip s klikabilnim pinovima, omogućuje konfiguraciju GPIO, tajmera, ADC-a i vanjskih prekida,
te generira Atmel Studio / AVR-GCC kompatibilan `void init()` C kod.

**Autor:** Zoran Vrhovski, Veleučilište u Bjelovaru

---

## Struktura datoteka

| Datoteka | Opis |
|---|---|
| `main.py` | Ulazna točka (pokreće QApplication + MainWindow) |
| `main_window.py` | Glavni prozor: chip lijevo, tabovi desno, code editor dolje |
| `pins.py` | 44-pin TQFP-44 definicije, PinDef, PinConfig, GpioMode, PinType |
| `chip_widget.py` | QPainter crtanje chipa, hover tooltip, VUB logo na chipu |
| `pin_panel.py` | Desni panel: info o pinu, alt funkcije, GPIO mode radio gumbi |
| `timers.py` | Timer definicije (T0/T1/T3/T4): WGM modovi, prescaleri, kanali |
| `timer_panel.py` | Timer UI: OverflowGroup (slider+TOIE), ChannelGroup (OCR, COM, duty%) |
| `interrupts.py` | INT0-6 + PCINT0-7 definicije, sense opcije, InterruptConfig |
| `interrupt_panel.py` | Interrupt UI: enable + sense combo za INTx, PCINT checkboxovi |
| `adc.py` | ADC definicije: single-ended (ADC0-13) + diferencijalni kanali, REFS, prescaler |
| `adc_panel.py` | ADC UI: multi-channel checkboxovi, referenca, prescaler |
| `code_gen.py` | Generiranje C koda: GPIO + Timers + ADC + Interrupts + ISR stubovi |
| `code_highlighter.py` | QSyntaxHighlighter za C kod (VS Code Dark+ boje) |
| `vub_logo.svg` | VUB logotip (renderira se na chipu i u About dijalogu) |

---

## Arhitektura

### Tok podataka
```
UI Widget promjena → pyqtSignal.emit() → MainWindow slot →
  ažurira state dict → _refresh_code() → generate_code() →
  code_edit.setPlainText()
```

### Obrazac za periferal (svaki periferal slijedi isti obrazac)
1. **Definicijska datoteka** (`timers.py`, `interrupts.py`, `adc.py`) — frozen dataclasses za hardverske opise + mutable dataclass za runtime konfiguraciju
2. **UI panel** (`timer_panel.py`, `interrupt_panel.py`, `adc_panel.py`) — QWidget/QScrollArea, emitira `config_changed` signal
3. **Code gen funkcija** u `code_gen.py` — `_timer_section()`, `_interrupt_section()`, `_adc_section()`
4. **Integracija u MainWindow** — state objekt, tab, signal → `_refresh_code()`

### Registri generiranog koda
- **GPIO**: `DDRx |= (1 << PBn);`, `PORTx |= (1 << PBn);`
- **Timers**: TCCRnA/B, OCRnX, ICRn, TCNTn, TIMSKn
- **ADC**: ADCSRA (ADEN + prescaler), ADMUX (REFS + MUX), ADCSRB (MUX5)
- **Interrupts**: EICRA/B, EIMSK, PCICR, PCMSK0
- **sei()** se automatski generira kad je bilo koji prekid aktivan
- **ISR stubovi** za svaki aktivni prekid

---

## Ključne tehničke napomene

- **PyQt6** — svi fontovi Consolas 10pt, dark mode kompatibilno
- **Boja alt-funkcija**: `#F0C040` (zlatno-žuta) za vidljivost na tamnoj pozadini
- **Tooltip**: tamna pozadina `#2C3E50`, bijeli naziv pina, žute alt funkcije
- **VUB logo na chipu**: `QSvgRenderer` u `paintEvent`, 85% opacity, `LOGO_H = min(78, ch*26//100)`
- **Chip crtanje**: TQFP-44 counter-clockwise numeracija, `PIN_LEN=36`, `PIN_W=11`, `MARGIN=130`
- **`_building` flag** u svim panelima sprečava feedback loop pri programatskim ažuriranjima
- **`_needs_sei()`** provjerava: sei checkbox, ext/pcint interrupts, timer TOIE
- **ADC multi-channel**: ADCSRA se postavlja jednom, prvi kanal nekomentiran, ostali zakomentirani

---

## Pokretanje

```bash
cd ATmega32U4_Configurator
python main.py
```

Zahtijeva: Python 3.10+, PyQt6 (`pip install PyQt6`)

---

## Verzija
- v1.0 — GPIO + Timers (T0/T1/T3/T4) + Interrupts (INTx, PCINT) + ADC (multi-channel, diferencijalni)
