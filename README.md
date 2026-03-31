# ATmega32U4 Configurator

GUI konfigurator za mikrokontroler **ATmega32U4** (TQFP-44) koji generira inicijalizacijski C kod kompatibilan s **Atmel Studio / AVR-GCC**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?logo=qt)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Mogućnosti

| Periferal | Opis |
|-----------|------|
| **GPIO** | Konfiguracija smjera i stanja pinova (DDRx, PORTx) |
| **Timeri** | T0 (8-bit), T1/T3 (16-bit), T4 (10-bit HS) — Normal, CTC, Fast PWM, Phase Correct |
| **Timer 4 PLL** | 96 MHz PLL clock (48/64/96 MHz za Timer 4, 48 MHz za USB) |
| **ADC** | Multi-channel (ADC0–ADC13), diferencijalni kanali s pojačanjem (1×/10×/200×), helper funkcije |
| **UART** | USART1 — baud rate (2400–115200), format (5–9 bit, paritet, stop), U2X, ISR |
| **SPI** | Master / Slave, SPI Mode 0–3, prescaler, data order |
| **I2C (TWI)** | Master (100/400 kHz) / Slave (7-bit adresa, General Call) |
| **Prekidi** | Vanjski (INT0–INT6), Pin Change (PCINT0–7), Timer OVF/CTC, UART/SPI/TWI interrupts |
| **F_CPU** | Konfigurabilan (1–20 MHz + UART-optimizirane frekvencije) |

## Značajke

- Vizualni prikaz TQFP-44 chipa s klikabilnim pinovima
- Automatska konfiguracija DDR registara za OC/Timer/SPI/UART pinove
- Automatsko generiranje `sei()` i ISR stubova kad su prekidi aktivni
- `#define F_CPU` na vrhu generiranog koda
- Syntax highlighting za generirani C kod (VS Code Dark+ tema)
- ADC helper funkcije (`adc_read()`, `adc_select_*()`)
- Copy to clipboard

## Pokretanje

### Preduvjeti

- Python 3.10+
- PyQt6

### Instalacija

```bash
pip install PyQt6
```

### Pokretanje

```bash
cd ATmega32U4_Configurator
python main.py
```

Aplikacija se otvara u fullscreen modu.

## Struktura projekta

```
ATmega32U4_Configurator/
├── main.py                 # Ulazna točka
├── main_window.py          # Glavni prozor i integracija
├── code_gen.py             # Generiranje C koda
├── code_highlighter.py     # Syntax highlighting
│
├── pins.py                 # TQFP-44 pin definicije
├── chip_widget.py          # Vizualni prikaz chipa
├── pin_panel.py            # GPIO konfiguracija
│
├── timers.py               # Timer definicije (T0/T1/T3/T4)
├── timer_panel.py          # Timer UI panel
│
├── adc.py                  # ADC definicije
├── adc_panel.py            # ADC UI panel
│
├── uart.py                 # USART1 definicije
├── uart_panel.py           # UART UI panel
│
├── spi.py                  # SPI definicije
├── spi_panel.py            # SPI UI panel
│
├── twi.py                  # TWI/I2C definicije
├── twi_panel.py            # I2C UI panel
│
├── interrupts.py           # Interrupt definicije
├── interrupt_panel.py      # Interrupt UI panel
│
└── vub_logo.svg            # VUB logotip
```

## Primjer generiranog koda

```c
#define F_CPU 16000000UL
#include <avr/io.h>
#include <avr/interrupt.h>

void init(void)
{
    /* ---- GPIO ---- */
    /* Port B: PB0=Out/LOW, PB1=Out/HIGH */
    DDRB  |= (1 << PB0) | (1 << PB1);
    PORTB |= (1 << PB1);

    /* ---- Timer 0 ---- */
    /* CTC (TOP = OCR0A) | clk / 64 | 1.000 kHz */
    TCCR0A = (1<<WGM01);
    TCCR0B = (1<<CS00) | (1<<CS01);
    OCR0A  = 249;
    TIMSK0 |= (1<<OCIE0A);

    /* ---- USART1 ---- */
    /* 9600 baud, 8N1 */
    UBRR1H = 0;
    UBRR1L = 103;
    UCSR1B = (1<<RXEN1) | (1<<TXEN1) | (1<<RXCIE1);
    UCSR1C = (1<<UCSZ11) | (1<<UCSZ10);

    sei();
}

ISR(TIMER0_COMPA_vect)
{
    /* Timer 0 Compare Match A (CTC) */
}

ISR(USART1_RX_vect)
{
    /* USART1 RX Complete */
    uint8_t data = UDR1;
}
```

## Autor

**Zoran Vrhovski**
Veleučilište u Bjelovaru

## Licenca

MIT License
