"""
SPI configuration panel for ATmega32U4 Configurator.
Master + Slave modes.
"""

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from spi import (
    SPIConfig, SPI_MODES, SPI_PRESCALERS, F_CPU_DEFAULT,
    fmt_spi_clock,
)

FONT      = QFont("Consolas", 12)
FONT_BOLD = QFont("Consolas", 12, QFont.Weight.Bold)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class SPIPanel(QWidget):
    config_changed = pyqtSignal()

    def __init__(self, spi_config: SPIConfig, parent=None):
        super().__init__(parent)
        self.cfg = spi_config
        self._f_cpu = F_CPU_DEFAULT
        self._building = False
        self._build_ui()
        self._sync_from_config()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        container = QWidget()
        container.setFont(FONT)
        scroll.setWidget(container)

        root = QVBoxLayout(container)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # Enable
        self._chk_enable = QCheckBox("Enable SPI")
        self._chk_enable.setFont(FONT_BOLD)
        self._chk_enable.stateChanged.connect(self._on_enable)
        root.addWidget(self._chk_enable)
        root.addWidget(_hline())

        # Master / Slave
        ms_box = QGroupBox("Mod")
        ms_box.setFont(FONT_BOLD)
        ms_lay = QVBoxLayout(ms_box)
        ms_lay.setContentsMargins(8, 6, 8, 8)

        self._cmb_ms = QComboBox()
        self._cmb_ms.setFont(FONT)
        self._cmb_ms.addItems(["Master", "Slave"])
        self._cmb_ms.currentIndexChanged.connect(self._on_ms)
        ms_lay.addWidget(self._cmb_ms)
        root.addWidget(ms_box)

        # SPI Mode
        mode_box = QGroupBox("SPI Mode (CPOL/CPHA)")
        mode_box.setFont(FONT_BOLD)
        mode_lay = QVBoxLayout(mode_box)
        mode_lay.setContentsMargins(8, 6, 8, 8)

        self._cmb_mode = QComboBox()
        self._cmb_mode.setFont(FONT)
        for m in SPI_MODES:
            self._cmb_mode.addItem(m.label)
        self._cmb_mode.currentIndexChanged.connect(self._on_mode)
        mode_lay.addWidget(self._cmb_mode)
        root.addWidget(mode_box)

        # Prescaler (Master only)
        ps_box = QGroupBox("Prescaler (Master)")
        ps_box.setFont(FONT_BOLD)
        ps_lay = QVBoxLayout(ps_box)
        ps_lay.setContentsMargins(8, 6, 8, 8)
        ps_lay.setSpacing(6)

        self._cmb_prescaler = QComboBox()
        self._cmb_prescaler.setFont(FONT)
        for p in SPI_PRESCALERS:
            self._cmb_prescaler.addItem(p.label)
        self._cmb_prescaler.currentIndexChanged.connect(self._on_prescaler)
        ps_lay.addWidget(self._cmb_prescaler)

        self._lbl_clock = QLabel("")
        self._lbl_clock.setFont(FONT)
        self._lbl_clock.setStyleSheet("color: #F0C040;")
        ps_lay.addWidget(self._lbl_clock)

        self._ps_box = ps_box
        root.addWidget(ps_box)

        # Data order
        self._chk_lsb = QCheckBox("LSB first  (DORD)")
        self._chk_lsb.setFont(FONT)
        self._chk_lsb.stateChanged.connect(self._on_lsb)
        root.addWidget(self._chk_lsb)

        root.addWidget(_hline())

        # SPI Interrupt
        self._chk_spie = QCheckBox("SPI Interrupt  (SPIE)")
        self._chk_spie.setFont(FONT)
        self._chk_spie.stateChanged.connect(self._on_spie)
        root.addWidget(self._chk_spie)

        root.addWidget(_hline())

        # Pin info
        self._lbl_pins = QLabel("")
        self._lbl_pins.setFont(FONT)
        self._lbl_pins.setWordWrap(True)
        self._lbl_pins.setStyleSheet("color: #AAAAAA;")
        root.addWidget(self._lbl_pins)

        root.addStretch()

    def _sync_from_config(self):
        self._building = True
        self._chk_enable.setChecked(self.cfg.enabled)
        self._cmb_ms.setCurrentIndex(0 if self.cfg.is_master else 1)
        self._cmb_mode.setCurrentIndex(self.cfg.mode_idx)
        self._cmb_prescaler.setCurrentIndex(self.cfg.prescaler_idx)
        self._chk_lsb.setChecked(self.cfg.lsb_first)
        self._chk_spie.setChecked(self.cfg.spi_int)
        self._building = False
        self._update_ui()

    # Slots
    def _on_enable(self, state):
        if self._building: return
        self.cfg.enabled = bool(state)
        self._update_ui()
        self.config_changed.emit()

    def _on_ms(self, idx):
        if self._building: return
        self.cfg.is_master = (idx == 0)
        self._update_ui()
        self.config_changed.emit()

    def _on_mode(self, idx):
        if self._building: return
        self.cfg.mode_idx = idx
        self.config_changed.emit()

    def _on_prescaler(self, idx):
        if self._building: return
        self.cfg.prescaler_idx = idx
        self._update_clock()
        self.config_changed.emit()

    def _on_lsb(self, state):
        if self._building: return
        self.cfg.lsb_first = bool(state)
        self.config_changed.emit()

    def _on_spie(self, state):
        if self._building: return
        self.cfg.spi_int = bool(state)
        self.config_changed.emit()

    # UI updates
    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._update_clock()

    def _update_ui(self):
        en = self.cfg.enabled
        self._cmb_ms.setEnabled(en)
        self._cmb_mode.setEnabled(en)
        self._cmb_prescaler.setEnabled(en and self.cfg.is_master)
        self._chk_lsb.setEnabled(en)
        self._chk_spie.setEnabled(en)
        self._ps_box.setVisible(self.cfg.is_master)
        self._update_clock()
        self._update_pins()

    def _update_clock(self):
        if self.cfg.is_master:
            clk = fmt_spi_clock(self.cfg.prescaler_idx, self._f_cpu)
            self._lbl_clock.setText(f"SPI clock: {clk}")
        else:
            self._lbl_clock.setText("")

    def _update_pins(self):
        if self.cfg.is_master:
            self._lbl_pins.setText(
                "SS=PB0 (pin 7) output\n"
                "SCK=PB1 (pin 8) output\n"
                "MOSI=PB2 (pin 9) output\n"
                "MISO=PB3 (pin 10) input"
            )
        else:
            self._lbl_pins.setText(
                "SS=PB0 (pin 7) input\n"
                "SCK=PB1 (pin 8) input\n"
                "MOSI=PB2 (pin 9) input\n"
                "MISO=PB3 (pin 10) output"
            )
