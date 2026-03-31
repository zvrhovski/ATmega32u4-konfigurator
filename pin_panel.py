from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QButtonGroup, QRadioButton, QFrame, QGroupBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from pins import PinDef, PinType, GpioMode, PinConfig

TYPE_LABELS = {
    PinType.GPIO:  ("GPIO",   "#4A90D9"),
    PinType.POWER: ("POWER",  "#888888"),
    PinType.USB:   ("USB",    "#9B59B6"),
    PinType.CLOCK: ("CLOCK",  "#E67E22"),
    PinType.RESET: ("RESET",  "#E74C3C"),
    PinType.REF:   ("ANALOG", "#1ABC9C"),
}

MODE_ORDER = [
    GpioMode.UNCONFIGURED,
    GpioMode.INPUT,
    GpioMode.INPUT_PULLUP,
    GpioMode.OUTPUT_LOW,
    GpioMode.OUTPUT_HIGH,
]

FONT_MAIN  = QFont("Consolas", 12)
FONT_BOLD  = QFont("Consolas", 12, QFont.Weight.Bold)
FONT_BIG   = QFont("Consolas", 20, QFont.Weight.Bold)
FONT_MED   = QFont("Consolas", 14)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class PinPanel(QWidget):
    """Right-side panel: shows selected pin info and mode selector."""

    config_changed = pyqtSignal(int, GpioMode)   # pin_num, new_mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_pin: PinDef | None = None
        self._pin_configs: dict[int, PinConfig] = {}
        self._building = False
        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll area so content is never clipped
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # ── Header ────────────────────────────────────────────────────────────
        self._lbl_num = QLabel("—")
        self._lbl_num.setFont(FONT_BIG)
        self._lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_name = QLabel("Select a pin")
        self._lbl_name.setFont(FONT_MED)
        self._lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_type = QLabel("")
        self._lbl_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_type.setFont(FONT_BOLD)

        root.addWidget(self._lbl_num)
        root.addWidget(self._lbl_name)
        root.addWidget(self._lbl_type)
        root.addWidget(_hline())

        # ── Alt functions ─────────────────────────────────────────────────────
        alt_box = QGroupBox("Alternativne primjene")
        alt_box.setFont(FONT_BOLD)
        alt_layout = QVBoxLayout(alt_box)
        alt_layout.setContentsMargins(8, 6, 8, 8)
        alt_layout.setSpacing(3)

        self._lbl_alts = QLabel("—")
        self._lbl_alts.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self._lbl_alts.setWordWrap(True)
        self._lbl_alts.setStyleSheet(
            "color: #F0C040; background: transparent;"
        )
        self._lbl_alts.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl_alts.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        alt_layout.addWidget(self._lbl_alts)

        root.addWidget(alt_box)
        root.addWidget(_hline())

        # ── GPIO mode selector ────────────────────────────────────────────────
        self._mode_box = QGroupBox("Pin mode")
        self._mode_box.setFont(FONT_BOLD)
        mode_layout = QVBoxLayout(self._mode_box)
        mode_layout.setContentsMargins(8, 6, 8, 8)
        mode_layout.setSpacing(4)

        self._btn_group = QButtonGroup(self)
        self._radio: dict[GpioMode, QRadioButton] = {}
        for mode in MODE_ORDER:
            rb = QRadioButton(mode.value)
            rb.setFont(FONT_MAIN)
            self._radio[mode] = rb
            self._btn_group.addButton(rb)
            mode_layout.addWidget(rb)

        self._btn_group.buttonClicked.connect(self._on_mode_clicked)
        root.addWidget(self._mode_box)

        # ── Non-GPIO info ─────────────────────────────────────────────────────
        self._lbl_info = QLabel("")
        self._lbl_info.setFont(FONT_MAIN)
        self._lbl_info.setWordWrap(True)
        self._lbl_info.setStyleSheet("color: #555;")
        root.addWidget(self._lbl_info)

        root.addStretch()

        # Initial state — nothing selected
        self._mode_box.setVisible(False)
        self._lbl_info.setVisible(False)

    # ── Public API ────────────────────────────────────────────────────────────

    def set_pin_configs(self, configs: dict[int, PinConfig]):
        self._pin_configs = configs

    def show_pin(self, pin: PinDef):
        self._current_pin = pin
        self._building = True

        # Header
        self._lbl_num.setText(str(pin.number))
        self._lbl_name.setText(pin.name)

        label, color = TYPE_LABELS.get(pin.pin_type, ("?", "#000"))
        self._lbl_type.setText(f"[ {label} ]")
        self._lbl_type.setStyleSheet(f"color: {color}; font-weight: bold;")

        # Alt functions — always shown
        if pin.alt_functions:
            # Each function on its own line for readability
            self._lbl_alts.setText("\n".join(f"• {fn}" for fn in pin.alt_functions))
        else:
            self._lbl_alts.setText("(nema)")

        # Mode controls
        if pin.pin_type == PinType.GPIO:
            cfg = self._pin_configs.get(pin.number, PinConfig())
            self._radio[cfg.mode].setChecked(True)
            self._mode_box.setVisible(True)
            self._lbl_info.setVisible(False)
        else:
            self._mode_box.setVisible(False)
            info = {
                PinType.POWER: "Naponski pin — nije konfigurabilno.",
                PinType.USB:   "USB pin — nije konfigurabilno.",
                PinType.CLOCK: "Kristalni oscilator — nije konfigurabilno.",
                PinType.RESET: "Reset (active-low) — nije konfigurabilno.",
                PinType.REF:   "ADC referentni napon — nije konfigurabilno.",
            }
            self._lbl_info.setText(info.get(pin.pin_type, ""))
            self._lbl_info.setVisible(True)

        self._building = False

    def clear(self):
        self._current_pin = None
        self._lbl_num.setText("—")
        self._lbl_name.setText("Select a pin")
        self._lbl_type.setText("")
        self._lbl_alts.setText("—")
        self._lbl_info.setText("")
        self._mode_box.setVisible(False)
        self._lbl_info.setVisible(False)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _on_mode_clicked(self, button: QRadioButton):
        if self._building or self._current_pin is None:
            return
        for mode, rb in self._radio.items():
            if rb is button:
                self.config_changed.emit(self._current_pin.number, mode)
                break
