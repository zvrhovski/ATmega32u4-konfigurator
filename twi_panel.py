"""
TWI (I2C) configuration panel for ATmega32U4 Configurator.
Master + Slave modes.
"""

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QSpinBox, QFrame, QGroupBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from twi import (
    TWIConfig, TWI_SPEEDS, TWI_PRESCALERS, F_CPU_DEFAULT,
    fmt_twi_info, calc_twbr,
)

FONT      = QFont("Consolas", 12)
FONT_BOLD = QFont("Consolas", 12, QFont.Weight.Bold)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class TWIPanel(QWidget):
    config_changed = pyqtSignal()

    def __init__(self, twi_config: TWIConfig, parent=None):
        super().__init__(parent)
        self.cfg = twi_config
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
        self._chk_enable = QCheckBox("Enable TWI (I2C)")
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

        # ── Master settings ───────────────────────────────────────────────────
        self._master_box = QGroupBox("Master postavke")
        self._master_box.setFont(FONT_BOLD)
        m_lay = QVBoxLayout(self._master_box)
        m_lay.setContentsMargins(8, 6, 8, 8)
        m_lay.setSpacing(6)

        # Speed
        sp_row = QHBoxLayout()
        sp_row.addWidget(QLabel("SCL brzina:"))
        self._cmb_speed = QComboBox()
        self._cmb_speed.setFont(FONT)
        for _freq, _label in TWI_SPEEDS:
            self._cmb_speed.addItem(_label)
        self._cmb_speed.currentIndexChanged.connect(self._on_speed)
        sp_row.addWidget(self._cmb_speed)
        m_lay.addLayout(sp_row)

        # Prescaler
        ps_row = QHBoxLayout()
        ps_row.addWidget(QLabel("Prescaler:"))
        self._cmb_prescaler = QComboBox()
        self._cmb_prescaler.setFont(FONT)
        for p in TWI_PRESCALERS:
            self._cmb_prescaler.addItem(p.label)
        self._cmb_prescaler.currentIndexChanged.connect(self._on_prescaler)
        ps_row.addWidget(self._cmb_prescaler)
        m_lay.addLayout(ps_row)

        self._lbl_master_info = QLabel("")
        self._lbl_master_info.setFont(FONT)
        self._lbl_master_info.setWordWrap(True)
        self._lbl_master_info.setStyleSheet("color: #F0C040;")
        m_lay.addWidget(self._lbl_master_info)

        root.addWidget(self._master_box)

        # ── Slave settings ────────────────────────────────────────────────────
        self._slave_box = QGroupBox("Slave postavke")
        self._slave_box.setFont(FONT_BOLD)
        s_lay = QVBoxLayout(self._slave_box)
        s_lay.setContentsMargins(8, 6, 8, 8)
        s_lay.setSpacing(6)

        addr_row = QHBoxLayout()
        addr_row.addWidget(QLabel("Adresa (7-bit):"))
        self._spin_addr = QSpinBox()
        self._spin_addr.setFont(FONT)
        self._spin_addr.setRange(1, 127)
        self._spin_addr.setPrefix("0x")
        self._spin_addr.setDisplayIntegerBase(16)
        self._spin_addr.valueChanged.connect(self._on_addr)
        addr_row.addWidget(self._spin_addr)
        s_lay.addLayout(addr_row)

        self._chk_gcall = QCheckBox("General Call Enable  (TWGCE)")
        self._chk_gcall.setFont(FONT)
        self._chk_gcall.stateChanged.connect(self._on_gcall)
        s_lay.addWidget(self._chk_gcall)

        root.addWidget(self._slave_box)

        root.addWidget(_hline())

        # TWI Interrupt
        self._chk_twie = QCheckBox("TWI Interrupt  (TWIE)")
        self._chk_twie.setFont(FONT)
        self._chk_twie.stateChanged.connect(self._on_twie)
        root.addWidget(self._chk_twie)

        root.addWidget(_hline())

        # Pin info
        self._lbl_pins = QLabel(
            "SCL = PD0 (pin 17)\nSDA = PD1 (pin 18)"
        )
        self._lbl_pins.setFont(FONT)
        self._lbl_pins.setStyleSheet("color: #AAAAAA;")
        root.addWidget(self._lbl_pins)

        root.addStretch()

    def _sync_from_config(self):
        self._building = True
        self._chk_enable.setChecked(self.cfg.enabled)
        self._cmb_ms.setCurrentIndex(0 if self.cfg.is_master else 1)
        self._cmb_speed.setCurrentIndex(self.cfg.speed_idx)
        self._cmb_prescaler.setCurrentIndex(self.cfg.prescaler_idx)
        self._spin_addr.setValue(self.cfg.slave_addr)
        self._chk_gcall.setChecked(self.cfg.general_call)
        self._chk_twie.setChecked(self.cfg.twi_int)
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

    def _on_speed(self, idx):
        if self._building: return
        self.cfg.speed_idx = idx
        self._update_master_info()
        self.config_changed.emit()

    def _on_prescaler(self, idx):
        if self._building: return
        self.cfg.prescaler_idx = idx
        self._update_master_info()
        self.config_changed.emit()

    def _on_addr(self, val):
        if self._building: return
        self.cfg.slave_addr = val
        self.config_changed.emit()

    def _on_gcall(self, state):
        if self._building: return
        self.cfg.general_call = bool(state)
        self.config_changed.emit()

    def _on_twie(self, state):
        if self._building: return
        self.cfg.twi_int = bool(state)
        self.config_changed.emit()

    # UI updates
    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._update_master_info()

    def _update_ui(self):
        en = self.cfg.enabled
        self._cmb_ms.setEnabled(en)
        self._cmb_speed.setEnabled(en)
        self._cmb_prescaler.setEnabled(en)
        self._spin_addr.setEnabled(en)
        self._chk_gcall.setEnabled(en)
        self._chk_twie.setEnabled(en)
        self._master_box.setVisible(self.cfg.is_master)
        self._slave_box.setVisible(not self.cfg.is_master)
        self._update_master_info()

    def _update_master_info(self):
        if not self.cfg.is_master:
            self._lbl_master_info.setText("")
            return
        info = fmt_twi_info(self.cfg.scl_freq, self.cfg.prescaler_idx, self._f_cpu)
        twbr = calc_twbr(self.cfg.scl_freq, self.cfg.prescaler_idx, self._f_cpu)
        if twbr > 255:
            info += "\n\u26a0 TWBR > 255! Pove\u0107aj prescaler."
        self._lbl_master_info.setText(info)
