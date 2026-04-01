# Upute za korištenje — ATmega32U4 Configurator

*Upute napisao Claude Code uz nadzor Zorana Vrhovskog*

---

## 1. Pokretanje aplikacije

### Iz izvornog koda
```bash
pip install PyQt6
cd ATmega32U4_Configurator
python main.py
```

### Iz .exe datoteke
Preuzmi `ATmega32U4_Configurator.exe` s GitHub Releases stranice i pokreni. Ne treba instalacija.

Aplikacija se otvara u fullscreen modu.

---

## 2. Raspored sučelja

Aplikacija je podijeljena u dva dijela:

| Dio | Sadržaj |
|-----|---------|
| **Lijevo (2/3)** | F_CPU odabir, generirani C kod, Copy to clipboard |
| **Desno (1/3)** | Tabovi za konfiguraciju: Pin, Timers, ADC, UART, SPI, I2C, IRQ |

Na **Pin** tabu se dodatno nalazi vizualni prikaz TQFP-44 chipa s klikabilnim pinovima.

---

## 3. F_CPU — odabir frekvencije takta

Na vrhu lijevog dijela nalazi se padajući izbornik **F_CPU** s ponuđenim frekvencijama:

- 1 MHz (internal RC), 2 MHz, 4 MHz
- 7.3728 / 11.0592 / 14.7456 / 18.432 MHz — optimizirane za UART (0% greška na standardnim baud rateovima)
- 8 MHz, 12 MHz, **16 MHz (default)**, 20 MHz

Promjena F_CPU automatski preračunava sve ovisne vrijednosti: UBRR za UART, TWBR za I2C, prescaler frekvencije za timere i ADC.

Generirani kod uvijek sadrži `#define F_CPU` na vrhu.

---

## 4. Tab: Pin (GPIO konfiguracija)

### Vizualni chip
U donjem dijelu taba prikazan je ATmega32U4 u TQFP-44 kućištu. Pinovi su obojani prema tipu:

- **Plava** — GPIO pinovi (konfigurabilni)
- **Siva** — napajanje (VCC, GND, AVCC)
- **Ljubičasta** — USB pinovi (D+, D-, UCAP, VBUS)
- **Narančasta** — XTAL pinovi (kristal)
- **Crvena** — RESET
- **Zelena** — AREF

### Odabir pina
Klikni na pin za prikaz informacija u gornjem dijelu taba:
- Broj pina i naziv (npr. "38 — PF4")
- Tip pina (GPIO, POWER, USB...)
- **Alternativne primjene** (npr. ADC4, TCK)

### Konfiguracija GPIO moda
Za GPIO pinove dostupni su sljedeći modovi:
- **Unconfigured** — ne generira kod
- **Input** — DDR = 0, PORT = 0
- **Input + Pull-up** — DDR = 0, PORT = 1
- **Output LOW** — DDR = 1, PORT = 0
- **Output HIGH** — DDR = 1, PORT = 1

### Tooltip
Prelaskom miša preko pina prikazuje se tooltip s brojem pina, nazivom i alternativnim funkcijama.

---

## 5. Tab: Timers

ATmega32U4 ima 4 timera: **T0** (8-bit), **T1** i **T3** (16-bit), **T4** (10-bit High Speed).

### Osnovna konfiguracija
1. Označi **Enable Timer X**
2. Odaberi **Mode**: Normal, CTC, Fast PWM, Phase Correct...
3. Odaberi **Prescaler**: clk/1, clk/8, clk/64... ili Ext T0/T1 za brojački mod
4. Postavi **TOP** vrijednost (ako mod dopušta)

### Prikaz frekvencije
Ispod prescalera prikazuju se izračunate vrijednosti:
- **Frequency** i **Period** — frekvencija compare matcha / overflow-a
- **OC Toggle** i **OC Period** (samo CTC) — frekvencija pravokutnog vala na OC pinu

### Normal mod
- Prikazuje **Overflow / TCNT Preload** grupu
- Slider i spinbox za podešavanje TCNT preload vrijednosti
- **Enable overflow interrupt (TOIE)** checkbox

### CTC mod
- **Enable Compare Match Interrupt (OCIE)** checkbox
- OC kanali prikazuju samo Output mode (Toggle/Clear/Set), bez OCR i Duty

### PWM modovi
- OC kanali prikazuju: Output mode (Non-inverted/Inverted PWM), OCR vrijednost, Duty %
- Automatski se generira DDR za OC pin kao output

### Timer 4 — PLL
Timer 4 ima dodatnu **PLL Clock** grupu:
- **Enable PLL** checkbox
- Odabir clock izvora: 96 MHz (PLL/1), 64 MHz (PLL/1.5), 48 MHz (PLL/2)
- Generirani kod uključuje PLLCSR, PLLFRQ registre i čekanje PLL locka

### Brojački mod (Ext T0/T1)
Kad se odabere prescaler "Ext T0" ili "Ext T1", automatski se generira DDR za T0 (PD7) ili T1 (PD6) pin kao input.

---

## 6. Tab: ADC

### Enable i opće postavke
1. Označi **Enable ADC (ADEN)**
2. Odaberi **Referentni napon**: AREF, AVCC (default), Internal 2.56V
3. Odaberi **Prescaler**: /2 do /128 (preporučeno /128 za 125 kHz ADC clock)

### Odabir kanala
**Single-ended kanali:**
- ADC0–ADC13 — svaki s checkboxom, prikazuje pin i fizički broj
- 1.1V Bandgap i GND — interni izvori

**Diferencijalni kanali:**
- Parovi s pojačanjem 1x, 10x ili 200x
- Npr. ADC1–ADC0 10x, ADC8–ADC0 200x...

### Generirani kod
- **1 kanal**: ADMUX se postavlja direktno u init()
- **Više kanala**: init() postavlja samo referencu, generirane su **helper funkcije**:
  - `adc_read()` — pokreće konverziju i vraća 10-bit rezultat
  - `adc_select_adc0()`, `adc_select_adc4()`... — prebacivanje kanala

Primjer korištenja:
```c
adc_select_adc4();
uint16_t val = adc_read();
```

---

## 7. Tab: UART

### Osnovna konfiguracija
1. Označi **Enable USART1**
2. Odaberi **Baud rate** (2400–115200)
3. Opcionalno uključi **U2X (double speed)** za bolju preciznost na višim baud rateovima

### Format okvira
- **Data bits**: 5, 6, 7, 8, 9
- **Paritet**: None, Even, Odd
- **Stop bits**: 1, 2

### TX / RX
- **TX Enable (TXEN1)** — TXD1 = PD3, pin 20
- **RX Enable (RXEN1)** — RXD1 = PD2, pin 19

### Prekidi
- **RX Complete (RXCIE1)** — generira ISR(USART1_RX_vect) s `uint8_t data = UDR1;`
- **TX Complete (TXCIE1)** — generira ISR(USART1_TX_vect)
- **Data Register Empty (UDRIE1)** — generira ISR(USART1_UDRE_vect)

### Info prikaz
- UBRR vrijednost i stvarni baud rate s postotkom greške
- Upozorenje ako je greška > 2%
- Sažetak formata (npr. "8N1 @ 9600 baud")

---

## 8. Tab: SPI

### Mod
- **Master** — kontrolira clock, šalje podatke
- **Slave** — prima clock, odgovara na zahtjeve

### SPI Mode (CPOL/CPHA)
| Mode | CPOL | CPHA | Opis |
|------|------|------|------|
| 0 | 0 | 0 | Clock idle LOW, sample na rising edge |
| 1 | 0 | 1 | Clock idle LOW, sample na falling edge |
| 2 | 1 | 0 | Clock idle HIGH, sample na falling edge |
| 3 | 1 | 1 | Clock idle HIGH, sample na rising edge |

### Prescaler (samo Master)
/2, /4, /8, /16, /32, /64, /128 — prikazuje rezultantnu SPI clock frekvenciju.

### Data order
- **MSB first** (default) ili **LSB first** (DORD bit)

### SPI Interrupt (SPIE)
Generira ISR(SPI_STC_vect) s `uint8_t data = SPDR;`

### Pinovi (automatski konfigurirani)
| Pin | Master | Slave |
|-----|--------|-------|
| PB0 (SS) | Output | Input |
| PB1 (SCK) | Output | Input |
| PB2 (MOSI) | Output | Input |
| PB3 (MISO) | Input | Output |

---

## 9. Tab: I2C (TWI)

### Mod
- **Master** — inicira komunikaciju
- **Slave** — odgovara na adresu

### Master postavke
- **SCL brzina**: 100 kHz (Standard) ili 400 kHz (Fast)
- **Prescaler**: 1, 4, 16, 64
- Prikazuje TWBR vrijednost, stvarnu SCL frekvenciju i grešku
- Upozorenje ako TWBR > 255

### Slave postavke
- **Adresa (7-bit)**: 0x01–0x7F (prikazuje hex)
- **General Call Enable (TWGCE)** — odgovara i na adresu 0x00

### TWI Interrupt (TWIE)
Generira ISR(TWI_vect) s `uint8_t status = TWSR & 0xF8;`

### Pinovi
- SCL = PD0 (pin 17)
- SDA = PD1 (pin 18)

---

## 10. Tab: IRQ (Vanjski prekidi)

### Vanjski prekidi (INT0–INT6)
Za svaki prekid:
- **Enable** checkbox
- **Sense** combo: Low level, Any change, Falling edge, Rising edge

Dostupni prekidi na ATmega32U4:
| Prekid | Pin | Fizički pin |
|--------|-----|-------------|
| INT0 | PD0 | 17 |
| INT1 | PD1 | 18 |
| INT2 | PD2 | 19 |
| INT3 | PD3 | 20 |
| INT6 | PE6 | 1 |

### Pin Change Interrupts (PCINT0–7)
- **PCIE0** master checkbox (Port B grupa)
- Individualni checkboxovi: PCINT0 (PB0) do PCINT7 (PB7)

### Enable global interrupts (sei)
- Checkbox za ručno uključivanje `sei()`
- `sei()` se **automatski generira** kad je bilo koji prekid aktivan (timer, UART, SPI, TWI, INTx, PCINT)

---

## 11. Generirani kod

### Struktura
```c
#define F_CPU 16000000UL
#include <avr/io.h>
#include <avr/interrupt.h>    // samo ako su prekidi aktivni

void init(void)
{
    /* ---- GPIO ---- */
    /* ---- Timer X ---- */
    /* ---- ADC ---- */
    /* ---- USART1 ---- */
    /* ---- SPI ---- */
    /* ---- TWI (I2C) ---- */
    /* ---- Interrupts ---- */
    sei();                    // samo ako je potreban
}

/* ISR stubovi */
ISR(vector_name) { ... }

/* ADC helper funkcije */
uint16_t adc_read(void) { ... }
void adc_select_adcX(void) { ... }
```

### Redoslijed sekcija
GPIO > Timeri > ADC > UART > SPI > I2C > Prekidi > sei() > ISR stubovi > ADC helperi

### Copy to clipboard
Gumb **Copy to clipboard** u donjem desnom kutu kopira cijeli generirani kod.

---

## 12. Savjeti

- Započni s odabirom **F_CPU** — sve ostalo ovisi o njemu
- Za UART bez greške koristi frekvencije označene s "(UART)": 7.3728, 11.0592, 14.7456 MHz
- ADC prescaler /128 daje 125 kHz ADC clock pri 16 MHz — idealno za 10-bit preciznost
- Timer 4 s PLL-om na 96 MHz daje PWM frekvencije do 375 kHz
- SPI Slave mod automatski postavlja MISO kao output, ostale pinove kao input
- ISR stubovi se automatski generiraju — samo dodaj svoju logiku unutar `{ }`

---

*ATmega32U4 Configurator v1.0*
*Autor: Zoran Vrhovski, Veleučilište u Bjelovaru*
