from pins       import PinConfig, GpioMode, PIN_MAP, PinType
from timers     import (TimerDef, TimerConfig, ALL_TIMERS, TIMER_MAP,
                        calc_freq, calc_duty, fmt_freq, fmt_period,
                        calc_overflow_time, effective_top, F_CPU_DEFAULT,
                        PLL_TM_OPTIONS)
from interrupts import InterruptConfig, EXT_INTS, PCINT_PINS, SENSE_OPTIONS
from adc        import ADCConfig, ALL_ADC_CHANNELS, ADC_REFS, ADC_PRESCALERS
from uart       import (USARTConfig, BAUD_RATES, DATA_BITS_OPTIONS,
                        PARITY_OPTIONS, STOP_BITS_OPTIONS, calc_baud_error)
from spi        import SPIConfig, SPI_MODES, SPI_PRESCALERS
from twi        import (TWIConfig, TWI_SPEEDS, TWI_PRESCALERS,
                        calc_twbr, calc_actual_scl)

PORTS = ['B', 'C', 'D', 'E', 'F']


# ══════════════════════════════════════════════════════════════════════════════
#  GPIO
# ══════════════════════════════════════════════════════════════════════════════

def _gpio_section(pin_configs: dict[int, PinConfig]) -> list[str]:
    out_bits:  dict[str, list[int]] = {p: [] for p in PORTS}
    high_bits: dict[str, list[int]] = {p: [] for p in PORTS}
    notes:     dict[str, list[str]] = {p: [] for p in PORTS}
    configured: set[str] = set()

    for pin_num, cfg in pin_configs.items():
        pin = PIN_MAP[pin_num]
        if pin.pin_type != PinType.GPIO or cfg.mode == GpioMode.UNCONFIGURED:
            continue
        port, bit, name = pin.port, pin.bit, f"P{pin.port}{pin.bit}"
        configured.add(port)

        if cfg.mode == GpioMode.OUTPUT_LOW:
            out_bits[port].append(bit);  notes[port].append(f"{name}=Out/LOW")
        elif cfg.mode == GpioMode.OUTPUT_HIGH:
            out_bits[port].append(bit);  high_bits[port].append(bit)
            notes[port].append(f"{name}=Out/HIGH")
        elif cfg.mode == GpioMode.INPUT:
            notes[port].append(f"{name}=In")
        elif cfg.mode == GpioMode.INPUT_PULLUP:
            high_bits[port].append(bit); notes[port].append(f"{name}=In/PU")

    if not configured:
        return []

    lines = ["    /* ---- GPIO ---- */"]
    for port in PORTS:
        if port not in configured:
            continue
        lines.append(f"    /* Port {port}: {', '.join(notes[port])} */")
        if out_bits[port]:
            lines.append(f"    DDR{port}  |= {_bits(port, sorted(out_bits[port]))};")
        if high_bits[port]:
            lines.append(f"    PORT{port} |= {_bits(port, sorted(high_bits[port]))};")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _bits(port: str, bits: list[int]) -> str:
    return " | ".join(f"(1 << P{port}{b})" for b in bits)


# ══════════════════════════════════════════════════════════════════════════════
#  TIMERS
# ══════════════════════════════════════════════════════════════════════════════

def _timer_section(timer_configs: dict[int, TimerConfig], f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    lines = []
    for tdef in ALL_TIMERS:
        cfg = timer_configs.get(tdef.n)
        if not cfg or not cfg.enabled:
            continue
        lines += [""]
        lines += _timer_regs(tdef, cfg, f_cpu)
    return lines


def _timer_regs(tdef: TimerDef, cfg: TimerConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    mode = tdef.modes[cfg.mode_idx]
    cs   = tdef.prescalers[cfg.prescaler_idx]
    top  = effective_top(tdef, cfg)
    if top is None:
        top = cfg.top

    # Effective clock: PLL for Timer 4, or F_CPU
    eff_clk = f_cpu
    if tdef.n == 4 and cfg.pll_enabled:
        pll_opt = PLL_TM_OPTIONS[cfg.pll_tm_idx]
        if pll_opt.clock_hz > 0:
            eff_clk = pll_opt.clock_hz

    hz   = calc_freq(tdef, cfg, eff_clk)
    freq_str = fmt_freq(hz)

    lines = [f"    /* ---- Timer {tdef.n} ({tdef.label})  |  {mode.name}  |  {cs.label}  |  {freq_str} ---- */"]

    # PLL setup for Timer 4
    if tdef.n == 4 and cfg.pll_enabled:
        lines += _t4_pll_regs(cfg, f_cpu)

    if tdef.n == 0:
        lines += _t0_regs(mode, cfg, top, cs)
    elif tdef.n in (1, 3):
        lines += _t13_regs(tdef.n, mode, cfg, top, cs)
    elif tdef.n == 4:
        lines += _t4_regs(mode, cfg, top, cs)

    lines += _normal_mode_extras(tdef, mode, cfg, f_cpu)
    lines += _ctc_mode_extras(tdef, mode, cfg)

    # Configure OC pins as output (DDRx) for any enabled channel with COM != 0
    for ch_def in tdef.channels:
        ch = cfg.ch(ch_def.letter)
        if ch.enabled and ch.com > 0:
            port = ch_def.pin_name[1]   # e.g. 'PB7' → 'B'
            bit  = ch_def.pin_name[2]   # e.g. 'PB7' → '7'
            lines.append(
                f"    DDR{port}  |= (1<<P{port}{bit});"
                f"  /* OC{tdef.n}{ch_def.letter} ({ch_def.pin_name}, pin {ch_def.pin_num}) output */"
            )

    # External clock (counter mode) — Tn pin as input
    # T0=PD7 (pin 26), T1=PD6 (pin 25)
    EXT_CLK_PINS = {0: ("D", "7", "PD7", 26), 1: ("D", "6", "PD6", 25)}
    if cs.cs in (6, 7) and tdef.n in EXT_CLK_PINS:
        port, bit, pname, pnum = EXT_CLK_PINS[tdef.n]
        edge = "silazni brid" if cs.cs == 6 else "uzlazni brid"
        lines.append(
            f"    DDR{port}  &= ~(1<<P{port}{bit});"
            f"  /* T{tdef.n} ({pname}, pin {pnum}) input \u2014 {edge} */"
        )

    return lines


def _t4_pll_regs(cfg: TimerConfig, f_cpu: int) -> list[str]:
    """Generate PLLCSR and PLLFRQ registers for Timer 4 PLL clock."""
    pll_opt = PLL_TM_OPTIONS[cfg.pll_tm_idx]
    lines = []

    # PLLCSR: PINDIV + PLLE
    # PINDIV=1 divides 16 MHz → 8 MHz PLL reference input
    pllcsr_bits = ["(1<<PLLE)"]
    if f_cpu > 8_000_000:
        pllcsr_bits.append("(1<<PINDIV)")
        lines.append(f"    PLLCSR = {_join(pllcsr_bits)};  /* PLL enable, \u00f72 \u2192 8 MHz ulaz */")
    else:
        lines.append(f"    PLLCSR = {_join(pllcsr_bits)};  /* PLL enable, 8 MHz ulaz */")

    # Wait for PLL lock
    lines.append(f"    while (!(PLLCSR & (1<<PLOCK)));  /* \u010dekaj PLL lock */")

    # PLLFRQ: PDIV=1010 (96 MHz = 8 MHz × 12), PLLTM, PLLUSB
    # PDIV3:0 = 1010 → bits PDIV3 + PDIV1
    pllfrq_bits = ["(1<<PDIV3)", "(1<<PDIV1)"]  # PDIV=1010 → 96 MHz

    # PLLUSB: 96 MHz / 2 = 48 MHz za USB
    pllfrq_bits.append("(1<<PLLUSB)")

    # PLLTM: Timer 4 clock postscaler
    plltm = pll_opt.plltm
    if plltm & 0x02:
        pllfrq_bits.append("(1<<PLLTM1)")
    if plltm & 0x01:
        pllfrq_bits.append("(1<<PLLTM0)")

    lines.append(f"    PLLFRQ = {_join(pllfrq_bits)};  /* 96 MHz PLL, USB=48 MHz, T4: {pll_opt.label} */")

    return lines


def _normal_mode_extras(tdef: TimerDef, mode, cfg: TimerConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    """TCNTn preload and TIMSKn for Normal mode."""
    if mode.wgm != 0:          # only Normal mode
        return []
    lines = []
    n = tdef.n
    t = calc_overflow_time(tdef, cfg, f_cpu)
    period_str = fmt_period(t) if t else "\u2014"

    if cfg.tcnt > 0:
        lines.append(f"    TCNT{n}  = {cfg.tcnt};  /* overflow in {period_str} */")
    if cfg.toie:
        lines.append(f"    TIMSK{n} |= (1<<TOIE{n});  /* overflow interrupt */")
    return lines


def _ctc_mode_extras(tdef: TimerDef, mode, cfg: TimerConfig) -> list[str]:
    """OCIEnA for CTC mode."""
    if "CTC" not in mode.name:
        return []
    if not cfg.ocie:
        return []
    n = tdef.n
    return [f"    TIMSK{n} |= (1<<OCIE{n}A);  /* compare match interrupt */"]


# ── Timer 0 ───────────────────────────────────────────────────────────────────

def _t0_regs(mode, cfg, top, cs) -> list[str]:
    wgm   = mode.wgm
    # TCCR0A = COM0A[7:6] | COM0B[3:2] | WGM0[1:0]
    # TCCR0B = WGM0[2]<<3 | CS0[2:0]
    tccr0a_bits = []
    tccr0b_bits = []

    if wgm & 0x01: tccr0a_bits.append("(1<<WGM00)")
    if wgm & 0x02: tccr0a_bits.append("(1<<WGM01)")
    if wgm & 0x04: tccr0b_bits.append("(1<<WGM02)")

    lines = []
    ch_a = cfg.ch('A')
    ch_b = cfg.ch('B')

    if ch_a.enabled:
        tccr0a_bits += _com_bits("COM0A", ch_a.com, mode.is_pwm)
    if ch_b.enabled:
        tccr0a_bits += _com_bits("COM0B", ch_b.com, mode.is_pwm)

    cs_bits = _cs_bits("CS0", cs.cs, 3)
    tccr0b_bits += cs_bits

    lines.append(f"    TCCR0A = {_join(tccr0a_bits, '0x00')};")
    lines.append(f"    TCCR0B = {_join(tccr0b_bits, '0x00')};")

    if mode.top == "OCRA":
        lines.append(f"    OCR0A  = {top};  /* TOP */")
    if ch_a.enabled and not (mode.top == "OCRA"):
        lines.append(f"    OCR0A  = {ch_a.ocr};  /* {calc_duty(ch_a.ocr, top):.1f}% duty */")
    if ch_b.enabled:
        lines.append(f"    OCR0B  = {ch_b.ocr};  /* {calc_duty(ch_b.ocr, top):.1f}% duty */")

    return lines


# ── Timer 1 / Timer 3 ─────────────────────────────────────────────────────────

def _t13_regs(n, mode, cfg, top, cs) -> list[str]:
    wgm = mode.wgm
    # TCCR1A = COM1A[7:6]|COM1B[5:4]|COM1C[3:2]|WGM1[1:0]
    # TCCR1B = ICNC|ICES|–|WGM1[3:2]|CS1[2:0]

    tccr_a = []
    tccr_b = []

    if wgm & 0x01: tccr_a.append(f"(1<<WGM{n}0)")
    if wgm & 0x02: tccr_a.append(f"(1<<WGM{n}1)")
    if wgm & 0x04: tccr_b.append(f"(1<<WGM{n}2)")
    if wgm & 0x08: tccr_b.append(f"(1<<WGM{n}3)")

    lines = []
    for ch_def in TIMER_MAP[n].channels:
        ch = cfg.ch(ch_def.letter)
        if ch.enabled:
            tccr_a += _com_bits(f"COM{n}{ch_def.letter}", ch.com, mode.is_pwm)

    tccr_b += _cs_bits(f"CS{n}", cs.cs, 3)

    lines.append(f"    TCCR{n}A = {_join(tccr_a, '0x00')};")
    lines.append(f"    TCCR{n}B = {_join(tccr_b, '0x00')};")

    # TOP register
    if mode.top == "ICR":
        lines.append(f"    ICR{n}   = {top};  /* TOP */")
    elif mode.top == "OCRA":
        lines.append(f"    OCR{n}A  = {top};  /* TOP */")

    # Channel OCR values
    for ch_def in TIMER_MAP[n].channels:
        ch = cfg.ch(ch_def.letter)
        # Skip OCR1A if it's used as TOP
        if ch_def.letter == 'A' and mode.top == "OCRA":
            continue
        if ch.enabled:
            lines.append(f"    OCR{n}{ch_def.letter}  = {ch.ocr};  /* {calc_duty(ch.ocr, top):.1f}% duty */")

    return lines


# ── Timer 4 ───────────────────────────────────────────────────────────────────

def _t4_regs(mode, cfg, top, cs) -> list[str]:
    wgm  = mode.wgm
    tccr4a = []
    tccr4b = []
    tccr4c = []
    tccr4d = []

    if wgm & 0x01: tccr4d.append("(1<<WGM40)")
    if wgm & 0x02: tccr4d.append("(1<<WGM41)")

    # CS bits in TCCR4B are 4-bit wide
    tccr4b += _cs_bits("CS4", cs.cs, 4)

    ch_a = cfg.ch('A')
    ch_b = cfg.ch('B')
    ch_d = cfg.ch('D')

    lines = []

    if ch_a.enabled:
        tccr4a.append("(1<<PWM4A)")
        tccr4a += _com_bits("COM4A", ch_a.com, mode.is_pwm)
    if ch_b.enabled:
        tccr4a.append("(1<<PWM4B)")
        tccr4a += _com_bits("COM4B", ch_b.com, mode.is_pwm)
    if ch_d.enabled:
        tccr4c.append("(1<<PWM4D)")
        tccr4c += _com_bits("COM4D", ch_d.com, mode.is_pwm)

    lines.append(f"    TCCR4A = {_join(tccr4a, '0x00')};")
    lines.append(f"    TCCR4B = {_join(tccr4b, '0x00')};")
    if tccr4c:
        lines.append(f"    TCCR4C = {_join(tccr4c, '0x00')};")
    lines.append(f"    TCCR4D = {_join(tccr4d, '0x00')};")

    if mode.top == "OCRC":
        lines.append(f"    OCR4C  = {top};  /* TOP */")
    if ch_a.enabled:
        lines.append(f"    OCR4A  = {ch_a.ocr};  /* {calc_duty(ch_a.ocr, top):.1f}% duty */")
    if ch_b.enabled:
        lines.append(f"    OCR4B  = {ch_b.ocr};  /* {calc_duty(ch_b.ocr, top):.1f}% duty */")
    if ch_d.enabled:
        lines.append(f"    OCR4D  = {ch_d.ocr};  /* {calc_duty(ch_d.ocr, top):.1f}% duty */")

    return lines


# ── Register bit helpers ───────────────────────────────────────────────────────

def _com_bits(prefix: str, com: int, is_pwm: bool) -> list[str]:
    """Return list of (1<<COMxy) strings for given COM value."""
    bits = []
    if com & 0x02: bits.append(f"(1<<{prefix}1)")
    if com & 0x01: bits.append(f"(1<<{prefix}0)")
    return bits


def _cs_bits(prefix: str, cs_val: int, width: int) -> list[str]:
    bits = []
    for i in range(width):
        if cs_val & (1 << i):
            bits.append(f"(1<<{prefix}{i})")
    return bits


def _join(bits: list[str], zero: str = "0x00") -> str:
    return " | ".join(bits) if bits else zero


# ══════════════════════════════════════════════════════════════════════════════
#  ADC
# ══════════════════════════════════════════════════════════════════════════════

def _adc_section(cfg: ADCConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    if not cfg.enabled or not cfg.enabled_channels:
        return []

    ref = ADC_REFS[cfg.ref_idx]
    ps  = ADC_PRESCALERS[cfg.prescaler_idx]

    channels = [ALL_ADC_CHANNELS[i] for i in sorted(cfg.enabled_channels)]

    lines = [
        "",
        "    /* ---- ADC ---- */",
        f"    // Referenca: {ref.label}",
        f"    // Prescaler: {ps.label}",
    ]

    # ADCSRA = (1<<ADEN) | ADPS[2:0]  — set once
    adcsra_parts = ["(1<<ADEN)"]
    for i in range(3):
        if ps.adps & (1 << i):
            adcsra_parts.append(f"(1<<ADPS{i})")
    lines.append(f"    ADCSRA = {_join(adcsra_parts)};")

    if len(channels) == 1:
        # Single channel: set ADMUX directly in init
        ch = channels[0]
        ch_desc = ch.label
        if ch.pin_num:
            ch_desc += f" ({ch.pin_name}, pin {ch.pin_num})"

        admux_parts = []
        if ref.refs & 0x02:
            admux_parts.append("(1<<REFS1)")
        if ref.refs & 0x01:
            admux_parts.append("(1<<REFS0)")
        for i in range(5):
            if ch.mux & (1 << i):
                admux_parts.append(f"(1<<MUX{i})")

        lines.append(f"    ADMUX  = {_join(admux_parts, '0x00')};  /* {ch_desc} */")
        if ch.mux5:
            lines.append(f"    ADCSRB = (1<<MUX5);")
        else:
            lines.append(f"    ADCSRB = 0x00;")
    else:
        # Multiple channels: only set reference, channel via helper functions
        ref_parts = []
        if ref.refs & 0x02:
            ref_parts.append("(1<<REFS1)")
        if ref.refs & 0x01:
            ref_parts.append("(1<<REFS0)")
        if ref_parts:
            lines.append(f"    ADMUX  = {_join(ref_parts)};  /* samo referenca */")
        lines.append(f"    // Kanal odaberi pomo\u0107u adc_select_*() funkcija")

    return lines


def _adc_channel_helpers(cfg: ADCConfig) -> list[str]:
    """Generate adc_read() + adc_select_*() helpers."""
    if not cfg.enabled or not cfg.enabled_channels:
        return []

    ref = ADC_REFS[cfg.ref_idx]
    channels = [ALL_ADC_CHANNELS[i] for i in sorted(cfg.enabled_channels)]

    lines = ["", ""]
    lines.append("/* ── ADC helper funkcije ───────────────────────────────────────── */")
    lines.append("")
    lines.append("uint16_t adc_read(void)")
    lines.append("{")
    lines.append("    ADCSRA |= (1<<ADSC);            /* pokreni konverziju */")
    lines.append("    while (ADCSRA & (1<<ADSC));      /* \u010dekaj zavr\u0161etak */")
    lines.append("    return ADC;")
    lines.append("}")
    if len(channels) < 2:
        # Single channel — only adc_read(), no select helpers
        if lines and lines[-1] == "":
            lines.pop()
        return lines

    lines.append("")

    for ch in channels:
        ch_desc = ch.label
        if ch.is_diff:
            ch_desc += f" (diff, {ch.gain}\u00d7)"
        elif ch.pin_num:
            ch_desc += f" ({ch.pin_name}, pin {ch.pin_num})"

        # Function name
        fname = ch.label.replace("\u2013", "_").replace(" ", "_").replace("\u00d7", "x").lower()

        admux_parts = []
        if ref.refs & 0x02:
            admux_parts.append("(1<<REFS1)")
        if ref.refs & 0x01:
            admux_parts.append("(1<<REFS0)")
        for i in range(5):
            if ch.mux & (1 << i):
                admux_parts.append(f"(1<<MUX{i})")

        lines.append(f"void adc_select_{fname}(void)")
        lines.append("{")
        lines.append(f"    ADMUX  = {_join(admux_parts, '0x00')};")
        if ch.mux5:
            lines.append(f"    ADCSRB |= (1<<MUX5);")
        else:
            lines.append(f"    ADCSRB &= ~(1<<MUX5);")
        lines.append("}")
        lines.append("")

    # Remove trailing blank
    if lines and lines[-1] == "":
        lines.pop()

    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  USART1
# ══════════════════════════════════════════════════════════════════════════════

def _uart_section(cfg: USARTConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    if not cfg.enabled:
        return []

    baud = cfg.baud
    ubrr = cfg.ubrr(f_cpu)
    fmt  = cfg.format_str
    error = calc_baud_error(baud, cfg.u2x, f_cpu)

    db  = DATA_BITS_OPTIONS[cfg.databits_idx]
    par = PARITY_OPTIONS[cfg.parity_idx]
    sb  = STOP_BITS_OPTIONS[cfg.stopbits_idx]

    lines = [
        "",
        "    /* ---- USART1 ---- */",
        f"    // {baud} baud, {fmt} (UBRR={ubrr}, gre\u0161ka {error:+.1f}%)",
        f"    // RXD1=PD2 (pin 19), TXD1=PD3 (pin 20)",
    ]

    # UBRR1
    lines.append(f"    UBRR1H = {(ubrr >> 8) & 0xFF};")
    lines.append(f"    UBRR1L = {ubrr & 0xFF};")

    # UCSR1A — only if U2X enabled
    if cfg.u2x:
        lines.append(f"    UCSR1A = (1<<U2X1);")

    # UCSR1B = RXEN | TXEN | interrupt bits
    ucsr1b_bits = []
    if cfg.rx_en:   ucsr1b_bits.append("(1<<RXEN1)")
    if cfg.tx_en:   ucsr1b_bits.append("(1<<TXEN1)")
    if cfg.rxcie:   ucsr1b_bits.append("(1<<RXCIE1)")
    if cfg.txcie:   ucsr1b_bits.append("(1<<TXCIE1)")
    if cfg.udrie:   ucsr1b_bits.append("(1<<UDRIE1)")
    # 9-bit mode: UCSZ12 bit is in UCSR1B
    if db.ucsz & 0x04:
        ucsr1b_bits.append("(1<<UCSZ12)")

    lines.append(f"    UCSR1B = {_join(ucsr1b_bits, '0x00')};")

    # UCSR1C = UPM | USBS | UCSZ[1:0]
    ucsr1c_bits = []
    # Parity
    if par.upm & 0x02: ucsr1c_bits.append("(1<<UPM11)")
    if par.upm & 0x01: ucsr1c_bits.append("(1<<UPM10)")
    # Stop bits
    if sb.usbs:         ucsr1c_bits.append("(1<<USBS1)")
    # Data bits (lower 2 bits of UCSZ)
    if db.ucsz & 0x02: ucsr1c_bits.append("(1<<UCSZ11)")
    if db.ucsz & 0x01: ucsr1c_bits.append("(1<<UCSZ10)")

    # Build comment
    parts = []
    parts.append(f"{db.bits}-bit")
    if par.upm == 0:
        parts.append("no parity")
    else:
        parts.append(f"{par.label.lower()} parity")
    parts.append(sb.label)
    comment = ", ".join(parts)

    lines.append(f"    UCSR1C = {_join(ucsr1c_bits, '0x00')};  /* {comment} */")

    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  SPI
# ══════════════════════════════════════════════════════════════════════════════

def _spi_section(cfg: SPIConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    if not cfg.enabled:
        return []

    mode = SPI_MODES[cfg.mode_idx]
    ps   = SPI_PRESCALERS[cfg.prescaler_idx]

    lines = ["", "    /* ---- SPI ---- */"]

    if cfg.is_master:
        clk = f_cpu // ps.div
        if clk >= 1_000_000:
            clk_str = f"{clk / 1_000_000:.1f} MHz"
        else:
            clk_str = f"{clk / 1_000:.0f} kHz"
        lines.append(f"    // Master, {mode.label}, {ps.label} ({clk_str})")
    else:
        lines.append(f"    // Slave, {mode.label}")

    lines.append(f"    // SS=PB0 (pin 7), SCK=PB1 (pin 8), MOSI=PB2 (pin 9), MISO=PB3 (pin 10)")

    # SPCR
    spcr_bits = ["(1<<SPE)"]
    if cfg.is_master:
        spcr_bits.append("(1<<MSTR)")
    if cfg.spi_int:
        spcr_bits.append("(1<<SPIE)")
    if cfg.lsb_first:
        spcr_bits.append("(1<<DORD)")
    if mode.cpol:
        spcr_bits.append("(1<<CPOL)")
    if mode.cpha:
        spcr_bits.append("(1<<CPHA)")
    if cfg.is_master:
        if ps.spr & 0x01:
            spcr_bits.append("(1<<SPR0)")
        if ps.spr & 0x02:
            spcr_bits.append("(1<<SPR1)")

    lines.append(f"    SPCR = {_join(spcr_bits)};")

    # SPSR (SPI2X for double speed)
    if cfg.is_master and ps.spi2x:
        lines.append(f"    SPSR = (1<<SPI2X);")

    # DDR configuration
    if cfg.is_master:
        lines.append(f"    DDRB |= (1<<PB1) | (1<<PB2);   /* SCK, MOSI output */")
        lines.append(f"    DDRB &= ~(1<<PB3);              /* MISO input */")
        lines.append(f"    DDRB |= (1<<PB0);               /* SS output */")
    else:
        lines.append(f"    DDRB |= (1<<PB3);               /* MISO output (Slave) */")
        lines.append(f"    DDRB &= ~((1<<PB0) | (1<<PB1) | (1<<PB2));  /* SS, SCK, MOSI input */")

    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  TWI (I2C)
# ══════════════════════════════════════════════════════════════════════════════

def _twi_section(cfg: TWIConfig, f_cpu: int = F_CPU_DEFAULT) -> list[str]:
    if not cfg.enabled:
        return []

    lines = ["", "    /* ---- TWI (I2C) ---- */"]
    lines.append(f"    // SCL=PD0 (pin 17), SDA=PD1 (pin 18)")

    if cfg.is_master:
        scl_freq = TWI_SPEEDS[cfg.speed_idx][0]
        scl_label = TWI_SPEEDS[cfg.speed_idx][1]
        ps = TWI_PRESCALERS[cfg.prescaler_idx]
        twbr = calc_twbr(scl_freq, cfg.prescaler_idx, f_cpu)
        actual = calc_actual_scl(twbr, cfg.prescaler_idx, f_cpu)

        lines.append(f"    // Master, {scl_label} (TWBR={twbr}, prescaler={ps.div})")

        # TWSR — prescaler bits
        twsr_bits = []
        if ps.twps & 0x01:
            twsr_bits.append("(1<<TWPS0)")
        if ps.twps & 0x02:
            twsr_bits.append("(1<<TWPS1)")
        lines.append(f"    TWSR = {_join(twsr_bits, '0x00')};  /* prescaler = {ps.div} */")

        # TWBR
        lines.append(f"    TWBR = {twbr};")

        # TWCR
        twcr_bits = ["(1<<TWEN)"]
        if cfg.twi_int:
            twcr_bits.append("(1<<TWIE)")
        lines.append(f"    TWCR = {_join(twcr_bits)};")

    else:
        # Slave mode
        addr = cfg.slave_addr
        lines.append(f"    // Slave, adresa 0x{addr:02X}")

        # TWAR
        twar_bits = [f"(0x{addr:02X}<<1)"]
        if cfg.general_call:
            twar_bits.append("(1<<TWGCE)")
        lines.append(f"    TWAR = {_join(twar_bits)};  /* 7-bit adresa */")

        # TWCR
        twcr_bits = ["(1<<TWEN)", "(1<<TWEA)"]
        if cfg.twi_int:
            twcr_bits.append("(1<<TWIE)")
        lines.append(f"    TWCR = {_join(twcr_bits)};")

    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  INTERRUPTS
# ══════════════════════════════════════════════════════════════════════════════

def _interrupt_section(cfg: InterruptConfig) -> list[str]:
    active_ext   = [e for e in EXT_INTS if cfg.ext[e.n].enabled]
    active_pcint = [p for p in PCINT_PINS if cfg.pcint.pins.get(p.pcint_n)]
    has_pcint    = cfg.pcint.group_enabled and active_pcint

    if not active_ext and not has_pcint:
        return []

    lines = ["", "    /* ---- Interrupts ---- */"]

    # ── INTx ─────────────────────────────────────────────────────────────────
    if active_ext:
        eicra_bits: list[str] = []
        eicrb_bits: list[str] = []
        eimsk_bits: list[str] = []

        for edef in active_ext:
            sense = cfg.ext[edef.n].sense
            label = next(l for v, l in SENSE_OPTIONS if v == sense)
            lines.append(f"    /* INT{edef.n} ({edef.pin_name}): {label} */")

            # ISC bits
            if sense & 0x01:
                bit_name = f"ISC{edef.n}0"
                if edef.eicr_reg == 'EICRA':
                    eicra_bits.append(f"(1<<{bit_name})")
                else:
                    eicrb_bits.append(f"(1<<{bit_name})")
            if sense & 0x02:
                bit_name = f"ISC{edef.n}1"
                if edef.eicr_reg == 'EICRA':
                    eicra_bits.append(f"(1<<{bit_name})")
                else:
                    eicrb_bits.append(f"(1<<{bit_name})")

            eimsk_bits.append(f"(1<<INT{edef.n})")

        if eicra_bits:
            lines.append(f"    EICRA  = {_join(eicra_bits)};")
        if eicrb_bits:
            lines.append(f"    EICRB  = {_join(eicrb_bits)};")
        lines.append(f"    EIMSK  = {_join(eimsk_bits)};")

    # ── PCINTx ────────────────────────────────────────────────────────────────
    if has_pcint:
        pin_names = ", ".join(p.pin_name for p in active_pcint)
        lines.append(f"    /* PCINT0 group: {pin_names} */")
        lines.append("    PCICR  = (1<<PCIE0);")
        mask_bits = [f"(1<<PCINT{p.pcint_n})" for p in active_pcint]
        lines.append(f"    PCMSK0 = {_join(mask_bits)};")

    # sei() is NOT added here — handled centrally in generate_code()
    return lines


def _needs_sei(irq_config: InterruptConfig | None,
               timer_configs: dict[int, TimerConfig] | None,
               uart_config: USARTConfig | None = None,
               spi_config: SPIConfig | None = None,
               twi_config: TWIConfig | None = None) -> bool:
    """
    sei() must be generated when:
      • the sei checkbox is explicitly checked, OR
      • any external / pin-change interrupt is enabled, OR
      • any timer overflow interrupt (TOIE) is enabled, OR
      • any USART interrupt is enabled.
    """
    if irq_config:
        if irq_config.sei:
            return True
        if any(cfg.enabled for cfg in irq_config.ext.values()):
            return True
        if irq_config.pcint.group_enabled and any(irq_config.pcint.pins.values()):
            return True
    if timer_configs:
        if any(cfg.toie or cfg.ocie for cfg in timer_configs.values()):
            return True
    if uart_config and uart_config.enabled and uart_config.has_interrupts():
        return True
    if spi_config and spi_config.enabled and spi_config.has_interrupts():
        return True
    if twi_config and twi_config.enabled and twi_config.has_interrupts():
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  ISR templates
# ══════════════════════════════════════════════════════════════════════════════

def _isr_section(irq_config:    InterruptConfig         | None,
                 timer_configs: dict[int, TimerConfig]  | None,
                 uart_config:   USARTConfig              | None = None,
                 spi_config:    SPIConfig                | None = None,
                 twi_config:    TWIConfig                | None = None) -> list[str]:
    """Generate ISR(...) stub functions for every enabled interrupt source."""
    isrs: list[tuple[str, list[str]]] = []   # (vector_name, body_lines)

    # ── External INTx ─────────────────────────────────────────────────────────
    if irq_config:
        for edef in EXT_INTS:
            if irq_config.ext[edef.n].enabled:
                sense = irq_config.ext[edef.n].sense
                label = next(l for v, l in SENSE_OPTIONS if v == sense)
                isrs.append((
                    f"INT{edef.n}_vect",
                    [f"    /* INT{edef.n} ({edef.pin_name}) \u2014 {label} */"]
                ))

        # ── PCINT0 ────────────────────────────────────────────────────────────
        if irq_config.pcint.group_enabled and any(irq_config.pcint.pins.values()):
            active = [p for p in PCINT_PINS if irq_config.pcint.pins.get(p.pcint_n)]
            pins_str = ", ".join(p.pin_name for p in active)
            isrs.append((
                "PCINT0_vect",
                [f"    /* Pin change on: {pins_str} */"]
            ))

    # ── Timer overflow (TOIE) ─────────────────────────────────────────────────
    if timer_configs:
        for tdef in ALL_TIMERS:
            cfg = timer_configs.get(tdef.n)
            if not cfg or not cfg.enabled:
                continue
            if cfg.toie:
                body = [f"    /* Timer {tdef.n} overflow */"]
                if cfg.tcnt > 0:
                    body.append(f"    TCNT{tdef.n} = {cfg.tcnt};  /* reload preload */")
                isrs.append((f"TIMER{tdef.n}_OVF_vect", body))
            if cfg.ocie:
                mode = tdef.modes[cfg.mode_idx]
                if "CTC" in mode.name:
                    isrs.append((
                        f"TIMER{tdef.n}_COMPA_vect",
                        [f"    /* Timer {tdef.n} Compare Match A (CTC) */"]
                    ))

    # ── USART1 interrupts ─────────────────────────────────────────────────────
    if uart_config and uart_config.enabled:
        if uart_config.rxcie:
            isrs.append((
                "USART1_RX_vect",
                ["    /* USART1 RX Complete */",
                 "    uint8_t data = UDR1;"]
            ))
        if uart_config.txcie:
            isrs.append((
                "USART1_TX_vect",
                ["    /* USART1 TX Complete */"]
            ))
        if uart_config.udrie:
            isrs.append((
                "USART1_UDRE_vect",
                ["    /* USART1 Data Register Empty */"]
            ))

    # ── SPI interrupt ─────────────────────────────────────────────────────────
    if spi_config and spi_config.enabled and spi_config.spi_int:
        isrs.append((
            "SPI_STC_vect",
            ["    /* SPI Transfer Complete */",
             "    uint8_t data = SPDR;"]
        ))

    # ── TWI interrupt ─────────────────────────────────────────────────────────
    if twi_config and twi_config.enabled and twi_config.twi_int:
        isrs.append((
            "TWI_vect",
            ["    /* TWI/I2C */",
             "    uint8_t status = TWSR & 0xF8;"]
        ))

    if not isrs:
        return []

    lines = ["", ""]
    lines.append("/* ── Interrupt Service Routines ─────────────────────────────────── */")
    for vect, body in isrs:
        lines.append("")
        lines.append(f"ISR({vect})")
        lines.append("{")
        lines += body
        lines.append("}")

    return lines


# ══════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════════════

def generate_code(pin_configs:   dict[int, PinConfig],
                  timer_configs: dict[int, TimerConfig]  | None = None,
                  irq_config:    InterruptConfig         | None = None,
                  adc_config:    ADCConfig               | None = None,
                  uart_config:   USARTConfig              | None = None,
                  spi_config:    SPIConfig                | None = None,
                  twi_config:    TWIConfig                | None = None,
                  f_cpu:         int                      = F_CPU_DEFAULT) -> str:

    gpio_lines  = _gpio_section(pin_configs)
    timer_lines = _timer_section(timer_configs, f_cpu) if timer_configs else []
    adc_lines   = _adc_section(adc_config, f_cpu) if adc_config else []
    uart_lines  = _uart_section(uart_config, f_cpu) if uart_config else []
    spi_lines   = _spi_section(spi_config, f_cpu) if spi_config else []
    twi_lines   = _twi_section(twi_config, f_cpu) if twi_config else []
    irq_lines   = _interrupt_section(irq_config) if irq_config else []
    isr_lines   = _isr_section(irq_config, timer_configs, uart_config, spi_config, twi_config)
    sei_needed  = _needs_sei(irq_config, timer_configs, uart_config, spi_config, twi_config)

    has_content = any([gpio_lines, timer_lines, adc_lines, uart_lines,
                       spi_lines, twi_lines, irq_lines, sei_needed])

    includes = ["#include <avr/io.h>"]
    if sei_needed or isr_lines:
        includes.append("#include <avr/interrupt.h>")

    # F_CPU define
    f_mhz = f_cpu / 1_000_000
    if f_mhz == int(f_mhz):
        f_str = f"{int(f_mhz)}000000UL"
    else:
        f_str = f"{int(f_cpu)}UL"
    f_define = f"#define F_CPU {f_str}"

    if not has_content:
        return (
            f"{f_define}\n"
            "#include <avr/io.h>\n\n"
            "void init(void)\n{\n"
            "    /* Nothing configured yet */\n"
            "}\n"
        )

    lines = [f_define] + includes + ["", "void init(void)", "{"]
    lines += gpio_lines
    lines += timer_lines
    lines += adc_lines
    lines += uart_lines
    lines += spi_lines
    lines += twi_lines
    lines += irq_lines
    if sei_needed:
        lines.append("")
        lines.append("    sei();  /* enable global interrupts */")
    lines.append("}")
    lines += isr_lines
    lines += _adc_channel_helpers(adc_config) if adc_config else []
    return "\n".join(lines) + "\n"
