"""
SPI definitions and runtime config for ATmega32U4.

Master + Slave modes. Pins: PB0=SS, PB1=SCK, PB2=MOSI, PB3=MISO.
Registers: SPCR, SPSR.
"""

from dataclasses import dataclass

F_CPU_DEFAULT = 16_000_000


# ── SPI Mode (CPOL, CPHA) ────────────────────────────────────────────────────

@dataclass(frozen=True)
class SPIModeOption:
    mode: int       # 0-3
    cpol: int       # clock polarity
    cpha: int       # clock phase
    label: str

SPI_MODES = (
    SPIModeOption(0, 0, 0, "Mode 0  (CPOL=0, CPHA=0)"),
    SPIModeOption(1, 0, 1, "Mode 1  (CPOL=0, CPHA=1)"),
    SPIModeOption(2, 1, 0, "Mode 2  (CPOL=1, CPHA=0)"),
    SPIModeOption(3, 1, 1, "Mode 3  (CPOL=1, CPHA=1)"),
)


# ── SPI Prescaler (SPR[1:0] + SPI2X) ─────────────────────────────────────────

@dataclass(frozen=True)
class SPIPrescalerOption:
    spr: int        # SPR[1:0] value
    spi2x: int      # SPI2X bit
    div: int        # prescaler divisor
    label: str

SPI_PRESCALERS = (
    SPIPrescalerOption(0b00, 1,   2, "/2"),
    SPIPrescalerOption(0b00, 0,   4, "/4"),
    SPIPrescalerOption(0b01, 1,   8, "/8"),
    SPIPrescalerOption(0b01, 0,  16, "/16"),
    SPIPrescalerOption(0b10, 1,  32, "/32"),
    SPIPrescalerOption(0b10, 0,  64, "/64"),
    SPIPrescalerOption(0b11, 0, 128, "/128"),
)

DEFAULT_PRESCALER_IDX = 3   # /16


# ── Helpers ───────────────────────────────────────────────────────────────────

def spi_clock_hz(prescaler_idx: int, f_cpu: int = F_CPU_DEFAULT) -> int:
    return f_cpu // SPI_PRESCALERS[prescaler_idx].div


def fmt_spi_clock(prescaler_idx: int, f_cpu: int = F_CPU_DEFAULT) -> str:
    hz = spi_clock_hz(prescaler_idx, f_cpu)
    if hz >= 1_000_000:
        return f"{hz / 1_000_000:.1f} MHz"
    return f"{hz / 1_000:.0f} kHz"


# ── Runtime config ────────────────────────────────────────────────────────────

@dataclass
class SPIConfig:
    enabled: bool = False
    is_master: bool = True
    mode_idx: int = 0               # SPI Mode 0
    prescaler_idx: int = DEFAULT_PRESCALER_IDX
    lsb_first: bool = False         # DORD: False=MSB, True=LSB
    spi_int: bool = False           # SPIE

    def has_interrupts(self) -> bool:
        return self.spi_int


def make_spi_config() -> SPIConfig:
    return SPIConfig()
