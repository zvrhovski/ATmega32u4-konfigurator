"""
Timer definitions and runtime config for ATmega32U4.
Covers Timer0 (8-bit), Timer1 (16-bit), Timer3 (16-bit), Timer4 (10-bit HS).
"""

from dataclasses import dataclass, field
from typing import Optional

F_CPU_DEFAULT = 16_000_000  # Hz


# ── Static descriptors (frozen) ───────────────────────────────────────────────

@dataclass(frozen=True)
class WGMMode:
    name: str
    wgm: int               # WGM field value
    top: str               # "MAX8","MAX10","MAX16","OCRA","ICR","OCRC"
    top_fixed: Optional[int]  # None → user sets TOP; int → fixed
    is_pwm: bool
    is_phase: bool = False  # phase-correct or phase+freq-correct


@dataclass(frozen=True)
class CSOption:
    label: str
    cs: int
    div: int               # 0 = timer stopped


@dataclass(frozen=True)
class OCChannel:
    letter: str            # 'A','B','C','D'
    pin_name: str          # e.g. 'PB7'
    pin_num: int           # physical TQFP-44 pin


@dataclass(frozen=True)
class TimerDef:
    n: int
    bits: int
    label: str             # display name
    modes: tuple
    prescalers: tuple
    channels: tuple


# ── Timer 0 (8-bit) ───────────────────────────────────────────────────────────

T0_MODES = (
    WGMMode("Normal",                         0, "MAX8",  0xFF,  False),
    WGMMode("CTC  (TOP = OCR0A)",             2, "OCRA",  None,  False),
    WGMMode("Fast PWM  (TOP = 0xFF)",         3, "MAX8",  0xFF,  True),
    WGMMode("Fast PWM  (TOP = OCR0A)",        7, "OCRA",  None,  True),
    WGMMode("Phase Correct  (TOP = 0xFF)",    1, "MAX8",  0xFF,  True,  True),
    WGMMode("Phase Correct  (TOP = OCR0A)",   5, "OCRA",  None,  True,  True),
)

T0_CS = (
    CSOption("Stopped",      0,  0),
    CSOption("clk / 1",      1,  1),
    CSOption("clk / 8",      2,  8),
    CSOption("clk / 64",     3,  64),
    CSOption("clk / 256",    4,  256),
    CSOption("clk / 1024",   5,  1024),
    CSOption("Ext T0 ↓",     6,  0),
    CSOption("Ext T0 ↑",     7,  0),
)

TIMER0 = TimerDef(
    n=0, bits=8, label="Timer 0  (8-bit)",
    modes=T0_MODES, prescalers=T0_CS,
    channels=(
        OCChannel('A', 'PB7', 11),
        OCChannel('B', 'PD0', 17),
    ),
)

# ── Timer 1 (16-bit) ──────────────────────────────────────────────────────────

T13_MODES = (
    WGMMode("Normal",                              0,  "MAX16", 0xFFFF, False),
    WGMMode("CTC  (TOP = OCR1A)",                  4,  "OCRA",  None,   False),
    WGMMode("CTC  (TOP = ICR1)",                   12, "ICR",   None,   False),
    WGMMode("Fast PWM  8-bit  (TOP = 0x00FF)",     5,  "MAX8",  0xFF,   True),
    WGMMode("Fast PWM  9-bit  (TOP = 0x01FF)",     6,  "MAX9",  0x1FF,  True),
    WGMMode("Fast PWM  10-bit  (TOP = 0x03FF)",    7,  "MAX10", 0x3FF,  True),
    WGMMode("Fast PWM  (TOP = ICR1)",              14, "ICR",   None,   True),
    WGMMode("Fast PWM  (TOP = OCR1A)",             15, "OCRA",  None,   True),
    WGMMode("Phase Correct  (TOP = ICR1)",         10, "ICR",   None,   True,  True),
    WGMMode("Phase Correct  (TOP = OCR1A)",        11, "OCRA",  None,   True,  True),
    WGMMode("Phase+Freq Correct  (TOP = ICR1)",    8,  "ICR",   None,   True,  True),
    WGMMode("Phase+Freq Correct  (TOP = OCR1A)",   9,  "OCRA",  None,   True,  True),
)

T13_CS = (
    CSOption("Stopped",      0,  0),
    CSOption("clk / 1",      1,  1),
    CSOption("clk / 8",      2,  8),
    CSOption("clk / 64",     3,  64),
    CSOption("clk / 256",    4,  256),
    CSOption("clk / 1024",   5,  1024),
    CSOption("Ext T1 ↓",     6,  0),
    CSOption("Ext T1 ↑",     7,  0),
)

TIMER1 = TimerDef(
    n=1, bits=16, label="Timer 1  (16-bit)",
    modes=T13_MODES, prescalers=T13_CS,
    channels=(
        OCChannel('A', 'PB5', 28),
        OCChannel('B', 'PB6', 29),
        OCChannel('C', 'PB7', 11),
    ),
)

# ── Timer 3 (16-bit, same structure as Timer1) ────────────────────────────────

TIMER3 = TimerDef(
    n=3, bits=16, label="Timer 3  (16-bit)",
    modes=T13_MODES, prescalers=T13_CS,
    channels=(
        OCChannel('A', 'PC6', 30),
    ),
)

# ── Timer 4 (10-bit high-speed) ───────────────────────────────────────────────

T4_MODES = (
    WGMMode("Normal",                  0, "MAX10", 0x3FF, False),
    WGMMode("CTC  (TOP = OCR4C)",      1, "OCRC",  None,  False),
    WGMMode("Fast PWM  (TOP = OCR4C)", 2, "OCRC",  None,  True),
    WGMMode("Phase+Freq Correct",      3, "OCRC",  None,  True,  True),
)

T4_CS = (
    CSOption("Stopped",       0,   0),
    CSOption("clk / 1",       1,   1),
    CSOption("clk / 2",       2,   2),
    CSOption("clk / 4",       3,   4),
    CSOption("clk / 8",       4,   8),
    CSOption("clk / 16",      5,   16),
    CSOption("clk / 32",      6,   32),
    CSOption("clk / 64",      7,   64),
    CSOption("clk / 128",     8,   128),
    CSOption("clk / 256",     9,   256),
    CSOption("clk / 512",     10,  512),
    CSOption("clk / 1024",    11,  1024),
    CSOption("clk / 2048",    12,  2048),
    CSOption("clk / 4096",    13,  4096),
    CSOption("clk / 8192",    14,  8192),
    CSOption("clk / 16384",   15,  16384),
)

TIMER4 = TimerDef(
    n=4, bits=10, label="Timer 4  (10-bit HS)",
    modes=T4_MODES, prescalers=T4_CS,
    channels=(
        OCChannel('A', 'PC6', 30),
        OCChannel('B', 'PB6', 29),
        OCChannel('D', 'PD7', 26),
    ),
)

ALL_TIMERS = (TIMER0, TIMER1, TIMER3, TIMER4)
TIMER_MAP  = {t.n: t for t in ALL_TIMERS}


# ── PLL for Timer 4 ──────────────────────────────────────────────────────────

PLL_FREQ = 96_000_000   # PLL output: 96 MHz (8 MHz × 12, PDIV=1010)

@dataclass(frozen=True)
class PLLTMOption:
    plltm: int          # PLLTM[1:0] value
    label: str
    clock_hz: int       # Timer 4 clock frequency (0 = disabled)

PLL_TM_OPTIONS = (
    PLLTMOption(0b00, "PLL off (koristi F_CPU)",    0),
    PLLTMOption(0b01, "96 MHz  (PLL / 1)",          96_000_000),
    PLLTMOption(0b10, "64 MHz  (PLL / 1.5)",        64_000_000),
    PLLTMOption(0b11, "48 MHz  (PLL / 2)",          48_000_000),
)


# ── Runtime configuration ─────────────────────────────────────────────────────

@dataclass
class ChannelConfig:
    enabled: bool = False
    ocr: int = 0
    com: int = 0   # 0=disconnected, 1=toggle, 2=non-inv/clear, 3=inv/set


@dataclass
class TimerConfig:
    enabled: bool = False
    mode_idx: int = 0
    prescaler_idx: int = 0
    top: int = 255
    # Normal mode extras
    tcnt: int = 0       # initial counter value (preload)
    toie: bool = False  # overflow interrupt enable
    # CTC mode extras
    ocie: bool = False  # output compare interrupt enable (OCIEnA)
    # PLL (Timer 4 only)
    pll_enabled: bool = False
    pll_tm_idx: int = 1    # default: 48 MHz (index into PLL_TM_OPTIONS)

    _channels: dict = field(default_factory=dict, repr=False)

    def ch(self, letter: str) -> ChannelConfig:
        if letter not in self._channels:
            self._channels[letter] = ChannelConfig()
        return self._channels[letter]


def make_timer_configs() -> dict[int, TimerConfig]:
    return {t.n: TimerConfig() for t in ALL_TIMERS}


# ── Frequency / duty helpers ──────────────────────────────────────────────────

def effective_top(tdef: TimerDef, cfg: TimerConfig) -> Optional[int]:
    mode = tdef.modes[cfg.mode_idx]
    return mode.top_fixed if mode.top_fixed is not None else cfg.top


def calc_freq(tdef: TimerDef, cfg: TimerConfig,
              f_cpu: int = F_CPU_DEFAULT) -> Optional[float]:
    """Return timer base frequency (PWM/OVF) in Hz, or None if stopped."""
    cs  = tdef.prescalers[cfg.prescaler_idx]
    if cs.div == 0:
        return None
    mode = tdef.modes[cfg.mode_idx]
    top  = effective_top(tdef, cfg)
    if top is None or top == 0:
        return None
    N = cs.div
    if not mode.is_pwm:
        if mode.wgm == 0:          # Normal — overflow frequency
            return f_cpu / (N * (top + 1))
        return f_cpu / (N * (top + 1))        # CTC — compare match frequency
    if mode.is_phase:
        return f_cpu / (N * 2 * top)
    return f_cpu / (N * (top + 1))


def calc_overflow_time(tdef: TimerDef, cfg: TimerConfig,
                       f_cpu: int = F_CPU_DEFAULT) -> Optional[float]:
    """Return Normal-mode overflow period in seconds given TCNTn preload."""
    cs = tdef.prescalers[cfg.prescaler_idx]
    if cs.div == 0:
        return None
    max_val = (1 << tdef.bits) - 1       # 255 / 65535 / 1023
    counts  = max_val - cfg.tcnt + 1     # ticks until overflow
    return counts * cs.div / f_cpu


def fmt_period(sec: Optional[float]) -> str:
    """Format a period in seconds to a human-readable string."""
    if sec is None:
        return "— (stopped)"
    if sec >= 1.0:
        return f"{sec:.4f} s"
    if sec >= 1e-3:
        return f"{sec*1e3:.3f} ms"
    if sec >= 1e-6:
        return f"{sec*1e6:.2f} µs"
    return f"{sec*1e9:.1f} ns"


def calc_duty(ocr: int, top: int) -> float:
    if top == 0:
        return 0.0
    return min(ocr / top * 100.0, 100.0)


def fmt_freq(hz: Optional[float]) -> str:
    if hz is None:
        return "— (stopped)"
    if hz >= 1_000_000:
        return f"{hz/1_000_000:.3f} MHz"
    if hz >= 1_000:
        return f"{hz/1_000:.3f} kHz"
    return f"{hz:.2f} Hz"
