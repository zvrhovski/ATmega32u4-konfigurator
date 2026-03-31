"""
TWI (I2C) definitions and runtime config for ATmega32U4.

Master + Slave modes. Pins: PD0=SCL (pin 17), PD1=SDA (pin 18).
Registers: TWBR, TWSR, TWCR, TWAR.
"""

from dataclasses import dataclass
from typing import Optional

F_CPU_DEFAULT = 16_000_000


# ── Speed presets ─────────────────────────────────────────────────────────────

TWI_SPEEDS = (
    (100_000, "100 kHz (Standard)"),
    (400_000, "400 kHz (Fast)"),
)

DEFAULT_SPEED_IDX = 0   # 100 kHz


# ── Prescaler (TWPS[1:0]) ────────────────────────────────────────────────────

@dataclass(frozen=True)
class TWIPrescalerOption:
    twps: int       # TWPS[1:0] value
    div: int        # prescaler value (1, 4, 16, 64)
    label: str

TWI_PRESCALERS = (
    TWIPrescalerOption(0b00,  1, "1"),
    TWIPrescalerOption(0b01,  4, "4"),
    TWIPrescalerOption(0b10, 16, "16"),
    TWIPrescalerOption(0b11, 64, "64"),
)

DEFAULT_PRESCALER_IDX = 0   # prescaler = 1


# ── Helpers ───────────────────────────────────────────────────────────────────

def calc_twbr(scl_freq: int, prescaler_idx: int = 0,
              f_cpu: int = F_CPU_DEFAULT) -> int:
    """TWBR = (F_CPU / SCL_freq - 16) / (2 * prescaler)"""
    ps = TWI_PRESCALERS[prescaler_idx].div
    val = (f_cpu / scl_freq - 16) / (2 * ps)
    return max(0, round(val))


def calc_actual_scl(twbr: int, prescaler_idx: int = 0,
                    f_cpu: int = F_CPU_DEFAULT) -> float:
    """Actual SCL frequency from TWBR value."""
    ps = TWI_PRESCALERS[prescaler_idx].div
    denom = 16 + 2 * ps * twbr
    if denom == 0:
        return 0
    return f_cpu / denom


def calc_scl_error(scl_freq: int, prescaler_idx: int = 0,
                   f_cpu: int = F_CPU_DEFAULT) -> float:
    """SCL frequency error in percent."""
    twbr = calc_twbr(scl_freq, prescaler_idx, f_cpu)
    actual = calc_actual_scl(twbr, prescaler_idx, f_cpu)
    if scl_freq == 0:
        return 0
    return (actual / scl_freq - 1) * 100


def fmt_twi_info(scl_freq: int, prescaler_idx: int = 0,
                 f_cpu: int = F_CPU_DEFAULT) -> str:
    twbr = calc_twbr(scl_freq, prescaler_idx, f_cpu)
    actual = calc_actual_scl(twbr, prescaler_idx, f_cpu)
    error = calc_scl_error(scl_freq, prescaler_idx, f_cpu)
    return (f"TWBR = {twbr}, stvarni SCL = {actual / 1000:.1f} kHz, "
            f"gre\u0161ka = {error:+.1f}%")


# ── Runtime config ────────────────────────────────────────────────────────────

@dataclass
class TWIConfig:
    enabled: bool = False
    is_master: bool = True
    speed_idx: int = DEFAULT_SPEED_IDX
    prescaler_idx: int = DEFAULT_PRESCALER_IDX
    # Slave
    slave_addr: int = 0x50      # 7-bit address (0-127)
    general_call: bool = False  # TWGCE
    # Interrupt
    twi_int: bool = False       # TWIE

    @property
    def scl_freq(self) -> int:
        return TWI_SPEEDS[self.speed_idx][0]

    def has_interrupts(self) -> bool:
        return self.twi_int


def make_twi_config() -> TWIConfig:
    return TWIConfig()
