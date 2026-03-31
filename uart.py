"""
USART1 definitions and runtime config for ATmega32U4.

Async mode only. Pins: PD2=RXD1 (pin 19), PD3=TXD1 (pin 20).
Registers: UCSR1A, UCSR1B, UCSR1C, UBRR1H, UBRR1L.
"""

from dataclasses import dataclass
from typing import Optional

F_CPU_DEFAULT = 16_000_000  # 16 MHz


# ── Baud rate helpers ─────────────────────────────────────────────────────────

def calc_ubrr(baud: int, u2x: bool = False, f_cpu: int = F_CPU_DEFAULT) -> int:
    """Calculate UBRR value for given baud rate."""
    divisor = 8 if u2x else 16
    return round(f_cpu / (divisor * baud) - 1)


def calc_actual_baud(ubrr: int, u2x: bool = False, f_cpu: int = F_CPU_DEFAULT) -> float:
    """Actual baud rate for a given UBRR value."""
    divisor = 8 if u2x else 16
    return f_cpu / (divisor * (ubrr + 1))


def calc_baud_error(baud: int, u2x: bool = False, f_cpu: int = F_CPU_DEFAULT) -> float:
    """Baud rate error in percent."""
    ubrr = calc_ubrr(baud, u2x, f_cpu)
    actual = calc_actual_baud(ubrr, u2x, f_cpu)
    return (actual / baud - 1) * 100


def fmt_baud_info(baud: int, u2x: bool = False, f_cpu: int = F_CPU_DEFAULT) -> str:
    """Human-readable baud info with UBRR and error."""
    ubrr = calc_ubrr(baud, u2x, f_cpu)
    actual = calc_actual_baud(ubrr, u2x, f_cpu)
    error = calc_baud_error(baud, u2x, f_cpu)
    return f"UBRR = {ubrr}, stvarni baud = {actual:.0f}, gre\u0161ka = {error:+.1f}%"


# ── Standard baud rates ──────────────────────────────────────────────────────

BAUD_RATES = (2400, 4800, 9600, 14400, 19200, 28800, 38400, 57600, 76800, 115200)

DEFAULT_BAUD_IDX = 2   # 9600


# ── Data bits (UCSZ1[2:0]) ──────────────────────────────────────────────────

@dataclass(frozen=True)
class DataBitsOption:
    bits: int       # 5, 6, 7, 8, 9
    ucsz: int       # UCSZ1[2:0] value (0-7)
    label: str

DATA_BITS_OPTIONS = (
    DataBitsOption(5, 0b000, "5-bit"),
    DataBitsOption(6, 0b001, "6-bit"),
    DataBitsOption(7, 0b010, "7-bit"),
    DataBitsOption(8, 0b011, "8-bit"),
    DataBitsOption(9, 0b111, "9-bit"),
)

DEFAULT_DATABITS_IDX = 3   # 8-bit


# ── Parity (UPM1[1:0]) ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class ParityOption:
    upm: int        # UPM1[1:0] value
    label: str
    code: str       # for display: N, E, O

PARITY_OPTIONS = (
    ParityOption(0b00, "Disabled (None)", "N"),
    ParityOption(0b10, "Even",           "E"),
    ParityOption(0b11, "Odd",            "O"),
)

DEFAULT_PARITY_IDX = 0   # None


# ── Stop bits (USBS1) ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StopBitsOption:
    usbs: int       # USBS1 bit value (0 or 1)
    label: str

STOP_BITS_OPTIONS = (
    StopBitsOption(0, "1 stop bit"),
    StopBitsOption(1, "2 stop bits"),
)

DEFAULT_STOPBITS_IDX = 0   # 1 stop


# ── Runtime config ────────────────────────────────────────────────────────────

@dataclass
class USARTConfig:
    enabled: bool = False
    baud_idx: int = DEFAULT_BAUD_IDX
    databits_idx: int = DEFAULT_DATABITS_IDX
    parity_idx: int = DEFAULT_PARITY_IDX
    stopbits_idx: int = DEFAULT_STOPBITS_IDX
    tx_en: bool = True
    rx_en: bool = True
    u2x: bool = False
    # Interrupt enables
    rxcie: bool = False     # RX Complete Interrupt Enable
    txcie: bool = False     # TX Complete Interrupt Enable
    udrie: bool = False     # Data Register Empty Interrupt Enable

    @property
    def baud(self) -> int:
        return BAUD_RATES[self.baud_idx]

    def ubrr(self, f_cpu: int = F_CPU_DEFAULT) -> int:
        return calc_ubrr(self.baud, self.u2x, f_cpu)

    @property
    def format_str(self) -> str:
        """e.g. '8N1' or '7E2'"""
        db = DATA_BITS_OPTIONS[self.databits_idx]
        par = PARITY_OPTIONS[self.parity_idx]
        sb = STOP_BITS_OPTIONS[self.stopbits_idx]
        return f"{db.bits}{par.code}{1 + sb.usbs}"

    def has_interrupts(self) -> bool:
        return self.rxcie or self.txcie or self.udrie


def make_uart_config() -> USARTConfig:
    return USARTConfig()
