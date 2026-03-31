"""
External interrupt definitions and config for ATmega32U4.

INT0-INT3, INT6  →  EICRA / EICRB / EIMSK
PCINT0-7         →  PCICR / PCMSK0
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Sense control options (ISCx1:ISCx0) ──────────────────────────────────────

SENSE_OPTIONS = [
    (0b00, "Low level"),
    (0b01, "Any change"),
    (0b10, "Falling edge"),
    (0b11, "Rising edge"),
]


# ── Static descriptor ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExtIntDef:
    n: int           # interrupt number: 0,1,2,3,6
    pin_name: str    # e.g. 'PD0'
    pin_num: int     # physical TQFP-44 pin
    eicr_reg: str    # 'EICRA' or 'EICRB'
    isc_bit: int     # LSB position of ISCn0 in the register (ISCn1 = isc_bit+1)
    eimsk_bit: int   # bit position in EIMSK


EXT_INTS = (
    ExtIntDef(0, 'PD0', 17, 'EICRA', 0, 0),
    ExtIntDef(1, 'PD1', 18, 'EICRA', 2, 1),
    ExtIntDef(2, 'PD2', 19, 'EICRA', 4, 2),
    ExtIntDef(3, 'PD3', 20, 'EICRA', 6, 3),
    ExtIntDef(6, 'PE6',  1, 'EICRB', 4, 6),
)

EXT_INT_MAP = {e.n: e for e in EXT_INTS}


# ── PCINT group (Port B only on ATmega32U4) ───────────────────────────────────

@dataclass(frozen=True)
class PCIntPinDef:
    pcint_n: int     # PCINT0-7
    pin_name: str
    pin_num: int


PCINT_PINS = (
    PCIntPinDef(0, 'PB0',  7),
    PCIntPinDef(1, 'PB1',  8),
    PCIntPinDef(2, 'PB2',  9),
    PCIntPinDef(3, 'PB3', 10),
    PCIntPinDef(4, 'PB4', 27),
    PCIntPinDef(5, 'PB5', 28),
    PCIntPinDef(6, 'PB6', 29),
    PCIntPinDef(7, 'PB7', 11),
)


# ── Runtime config ────────────────────────────────────────────────────────────

@dataclass
class ExtIntConfig:
    enabled: bool = False
    sense: int = 0b10          # default: falling edge


@dataclass
class PCIntConfig:
    group_enabled: bool = False
    pins: dict = field(default_factory=lambda: {p.pcint_n: False for p in PCINT_PINS})


@dataclass
class InterruptConfig:
    ext: dict = field(default_factory=lambda: {e.n: ExtIntConfig() for e in EXT_INTS})
    pcint: PCIntConfig = field(default_factory=PCIntConfig)
    sei: bool = False          # add sei() at end of init


def make_interrupt_config() -> InterruptConfig:
    return InterruptConfig()
