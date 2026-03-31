"""
ADC definitions and runtime config for ATmega32U4.

Single-ended: ADC0-ADC13, 1.1V bandgap, GND
Differential: various pairs with 1x/10x/200x gain
Registers:    ADMUX, ADCSRA, ADCSRB
"""

from dataclasses import dataclass, field
from typing import Optional

F_CPU_DEFAULT = 16_000_000  # 16 MHz


# ── Channel definition ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ADCChannelDef:
    idx: int            # unique index in ALL_ADC_CHANNELS
    mux: int            # MUX[4:0] value (lower 5 bits)
    mux5: int           # MUX5 bit (in ADCSRB)
    label: str          # display label
    pin_name: str       # e.g. 'PF0' or '—' for internal
    pin_num: int        # physical TQFP-44 pin, 0 if N/A
    is_diff: bool       # True for differential channels
    gain: Optional[int] # 1, 10, 200 or None for single-ended


# ── Single-ended channels ─────────────────────────────────────────────────────

_se = [
    (0x00, 0, "ADC0",  "PF0", 40),
    (0x01, 0, "ADC1",  "PF1", 39),
    (0x04, 0, "ADC4",  "PF4", 38),
    (0x05, 0, "ADC5",  "PF5", 37),
    (0x06, 0, "ADC6",  "PF6", 36),
    (0x07, 0, "ADC7",  "PF7", 35),
    (0x00, 1, "ADC8",  "PD4", 24),
    (0x01, 1, "ADC9",  "PD6", 25),
    (0x02, 1, "ADC10", "PD7", 26),
    (0x03, 1, "ADC11", "PB4", 27),
    (0x04, 1, "ADC12", "PB5", 28),
    (0x05, 1, "ADC13", "PB6", 29),
    (0x1E, 0, "1.1V Bandgap", "\u2014", 0),
    (0x1F, 0, "GND",          "\u2014", 0),
]

SE_CHANNELS = tuple(
    ADCChannelDef(idx=i, mux=m, mux5=m5, label=l, pin_name=p,
                  pin_num=pn, is_diff=False, gain=None)
    for i, (m, m5, l, p, pn) in enumerate(_se)
)

_SE_COUNT = len(SE_CHANNELS)

# ── Differential channels (ATmega32U4 datasheet Table 24-4) ───────────────────

_diff = [
    # mux, mux5, label, pin_name, pin_num, gain
    (0x08, 0, "ADC0\u2013ADC0 10\u00d7",   "PF0",       40, 10),
    (0x09, 0, "ADC1\u2013ADC0 10\u00d7",   "PF0\u2013PF1", 0, 10),
    (0x0A, 0, "ADC0\u2013ADC0 200\u00d7",  "PF0",       40, 200),
    (0x0B, 0, "ADC1\u2013ADC0 200\u00d7",  "PF0\u2013PF1", 0, 200),
    (0x10, 0, "ADC0\u2013ADC1 1\u00d7",    "PF0\u2013PF1", 0, 1),
    (0x11, 0, "ADC1\u2013ADC1 1\u00d7",    "PF1",       39, 1),
    (0x14, 0, "ADC4\u2013ADC1 1\u00d7",    "PF4\u2013PF1", 0, 1),
    (0x15, 0, "ADC5\u2013ADC1 1\u00d7",    "PF5\u2013PF1", 0, 1),
    (0x16, 0, "ADC6\u2013ADC1 1\u00d7",    "PF6\u2013PF1", 0, 1),
    (0x17, 0, "ADC7\u2013ADC1 1\u00d7",    "PF7\u2013PF1", 0, 1),
    # MUX5 = 1 differential pairs
    (0x08, 1, "ADC8\u2013ADC0 10\u00d7",   "PD4\u2013PF0", 0, 10),
    (0x09, 1, "ADC9\u2013ADC0 10\u00d7",   "PD6\u2013PF0", 0, 10),
    (0x0A, 1, "ADC8\u2013ADC0 200\u00d7",  "PD4\u2013PF0", 0, 200),
    (0x0B, 1, "ADC9\u2013ADC0 200\u00d7",  "PD6\u2013PF0", 0, 200),
    (0x10, 1, "ADC8\u2013ADC1 1\u00d7",    "PD4\u2013PF1", 0, 1),
    (0x11, 1, "ADC9\u2013ADC1 1\u00d7",    "PD6\u2013PF1", 0, 1),
    (0x12, 1, "ADC10\u2013ADC1 1\u00d7",   "PD7\u2013PF1", 0, 1),
    (0x13, 1, "ADC11\u2013ADC1 1\u00d7",   "PB4\u2013PF1", 0, 1),
    (0x14, 1, "ADC12\u2013ADC1 1\u00d7",   "PB5\u2013PF1", 0, 1),
    (0x15, 1, "ADC13\u2013ADC1 1\u00d7",   "PB6\u2013PF1", 0, 1),
]

DIFF_CHANNELS = tuple(
    ADCChannelDef(idx=_SE_COUNT + i, mux=m, mux5=m5, label=l,
                  pin_name=p, pin_num=pn, is_diff=True, gain=g)
    for i, (m, m5, l, p, pn, g) in enumerate(_diff)
)

ALL_ADC_CHANNELS = SE_CHANNELS + DIFF_CHANNELS


# ── Voltage reference options (REFS[1:0] in ADMUX) ───────────────────────────

@dataclass(frozen=True)
class ADCRefOption:
    refs: int       # REFS[1:0] value
    label: str

ADC_REFS = (
    ADCRefOption(0b00, "AREF (external)"),
    ADCRefOption(0b01, "AVCC (s kapacitetom na AREF)"),
    ADCRefOption(0b11, "Internal 2.56V (s kapacitetom na AREF)"),
)


# ── Prescaler options (ADPS[2:0] in ADCSRA) ──────────────────────────────────

@dataclass(frozen=True)
class ADCPrescalerOption:
    adps: int       # ADPS[2:0] value
    div: int        # prescaler divisor
    label: str

ADC_PRESCALERS = (
    ADCPrescalerOption(0b001,   2, "/2   (8 MHz)"),
    ADCPrescalerOption(0b010,   4, "/4   (4 MHz)"),
    ADCPrescalerOption(0b011,   8, "/8   (2 MHz)"),
    ADCPrescalerOption(0b100,  16, "/16  (1 MHz)"),
    ADCPrescalerOption(0b101,  32, "/32  (500 kHz)"),
    ADCPrescalerOption(0b110,  64, "/64  (250 kHz)"),
    ADCPrescalerOption(0b111, 128, "/128 (125 kHz)  \u2014 preporu\u010deno"),
)

DEFAULT_PRESCALER_IDX = 6   # /128


# ── Helpers ───────────────────────────────────────────────────────────────────

def adc_clock_hz(prescaler_idx: int, f_cpu: int = F_CPU_DEFAULT) -> int:
    return f_cpu // ADC_PRESCALERS[prescaler_idx].div


def conversion_time_us(prescaler_idx: int, f_cpu: int = F_CPU_DEFAULT) -> float:
    """Single conversion takes 13 ADC clock cycles (first: 25)."""
    return 13 / adc_clock_hz(prescaler_idx, f_cpu) * 1_000_000


def fmt_adc_clock(prescaler_idx: int, f_cpu: int = F_CPU_DEFAULT) -> str:
    hz = adc_clock_hz(prescaler_idx, f_cpu)
    if hz >= 1_000_000:
        return f"{hz / 1_000_000:.1f} MHz"
    return f"{hz / 1_000:.0f} kHz"


# ── Runtime config ────────────────────────────────────────────────────────────

@dataclass
class ADCConfig:
    enabled: bool = False
    enabled_channels: set = field(default_factory=set)  # set of ADCChannelDef.idx
    ref_idx: int = 1                                    # default: AVCC
    prescaler_idx: int = DEFAULT_PRESCALER_IDX          # default: /128


def make_adc_config() -> ADCConfig:
    return ADCConfig()
