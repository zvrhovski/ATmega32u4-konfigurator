from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class PinType(Enum):
    GPIO  = "gpio"
    POWER = "power"
    USB   = "usb"
    CLOCK = "clock"
    RESET = "reset"
    REF   = "reference"


class GpioMode(Enum):
    UNCONFIGURED = "Unconfigured"
    INPUT        = "Input"
    INPUT_PULLUP = "Input + Pull-up"
    OUTPUT_LOW   = "Output LOW"
    OUTPUT_HIGH  = "Output HIGH"


@dataclass
class PinDef:
    number: int
    name: str
    port: Optional[str]       # 'B','C','D','E','F' or None
    bit: Optional[int]        # 0-7 or None
    alt_functions: List[str]
    pin_type: PinType

    @property
    def side(self) -> str:
        if   1  <= self.number <= 11: return 'left'
        elif 12 <= self.number <= 22: return 'bottom'
        elif 23 <= self.number <= 33: return 'right'
        else:                          return 'top'

    @property
    def side_index(self) -> int:
        """Physical position index 0-10 along the side."""
        if self.side == 'left':   return self.number - 1        # 0=top,   10=bottom
        if self.side == 'bottom': return self.number - 12       # 0=left,  10=right
        if self.side == 'right':  return self.number - 23       # 0=bottom,10=top
        return                           self.number - 34       # 0=right, 10=left (top)


@dataclass
class PinConfig:
    mode: GpioMode = GpioMode.UNCONFIGURED


def _p(num, name, port, bit, alts, ptype):
    return PinDef(num, name, port, bit, alts, ptype)

G   = PinType.GPIO
P   = PinType.POWER
U   = PinType.USB
C   = PinType.CLOCK
R   = PinType.RESET
REF = PinType.REF

# ATmega32U4 TQFP-44 pinout
# Counter-clockwise from top-left:
# Left 1-11 (top→bottom), Bottom 12-22 (left→right),
# Right 23-33 (bottom→top), Top 34-44 (right→left)
ALL_PINS: List[PinDef] = [
    # ── Left side (1-11) ──────────────────────────────────────────────────────
    _p(1,  "PE6",   'E', 6, ["INT6", "AIN0"],                        G),
    _p(2,  "UVCC",  None,None,[],                                      P),
    _p(3,  "D-",    None,None,[],                                      U),
    _p(4,  "D+",    None,None,[],                                      U),
    _p(5,  "UCAP",  None,None,[],                                      U),
    _p(6,  "VBUS",  None,None,[],                                      U),
    _p(7,  "PB0",   'B', 0, ["SS",   "PCINT0"],                       G),
    _p(8,  "PB1",   'B', 1, ["SCK",  "PCINT1"],                       G),
    _p(9,  "PB2",   'B', 2, ["PDI",  "MOSI", "PCINT2"],               G),
    _p(10, "PB3",   'B', 3, ["PDO",  "MISO", "PCINT3"],               G),
    _p(11, "PB7",   'B', 7, ["OC0A", "OC1C", "PCINT7", "RTS"],        G),
    # ── Bottom side (12-22) ────────────────────────────────────────────────────
    _p(12, "/RESET",None,None,[],                                      R),
    _p(13, "VCC",   None,None,[],                                      P),
    _p(14, "GND",   None,None,[],                                      P),
    _p(15, "XTAL2", None,None,[],                                      C),
    _p(16, "XTAL1", None,None,[],                                      C),
    _p(17, "PD0",   'D', 0, ["OC0B", "SCL",  "INT0"],                 G),
    _p(18, "PD1",   'D', 1, ["SDA",  "INT1"],                         G),
    _p(19, "PD2",   'D', 2, ["RXD1", "INT2"],                         G),
    _p(20, "PD3",   'D', 3, ["TXD1", "INT3"],                         G),
    _p(21, "PD5",   'D', 5, ["XCK1", "CTS"],                          G),
    _p(22, "GND",   None,None,[],                                      P),
    # ── Right side (23-33, physical bottom→top) ────────────────────────────────
    _p(23, "AVCC",  None,None,[],                                      P),
    _p(24, "PD4",   'D', 4, ["ICP1", "ADC8"],                         G),
    _p(25, "PD6",   'D', 6, ["T1",   "OC4D", "ADC9"],                 G),
    _p(26, "PD7",   'D', 7, ["T0",   "OC4D", "ADC10"],                G),
    _p(27, "PB4",   'B', 4, ["PCINT4","ADC11"],                       G),
    _p(28, "PB5",   'B', 5, ["PCINT5","OC1A","OC4B","ADC12"],         G),
    _p(29, "PB6",   'B', 6, ["PCINT6","OC1B","OC4B","ADC13"],         G),
    _p(30, "PC6",   'C', 6, ["OC3A", "UVcon"],                        G),
    _p(31, "PC7",   'C', 7, ["ICP3", "CLK0", "OC4A"],                 G),
    _p(32, "PE2",   'E', 2, ["HWB"],                                   G),
    _p(33, "VCC",   None,None,[],                                      P),
    # ── Top side (34-44, physical right→left) ──────────────────────────────────
    _p(34, "GND",   None,None,[],                                      P),
    _p(35, "PF7",   'F', 7, ["ADC7", "TDI"],                          G),
    _p(36, "PF6",   'F', 6, ["ADC6", "TDO"],                          G),
    _p(37, "PF5",   'F', 5, ["ADC5", "TMS"],                          G),
    _p(38, "PF4",   'F', 4, ["ADC4", "TCK"],                          G),
    _p(39, "PF1",   'F', 1, ["ADC1"],                                  G),
    _p(40, "PF0",   'F', 0, ["ADC0"],                                  G),
    _p(41, "AREF",  None,None,[],                                      REF),
    _p(42, "GND",   None,None,[],                                      P),
    _p(43, "AVCC",  None,None,[],                                      P),
    _p(44, "VCC",   None,None,[],                                      P),
]

PIN_MAP: dict[int, PinDef] = {p.number: p for p in ALL_PINS}
