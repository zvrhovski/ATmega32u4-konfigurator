"""
ADC configuration panel for ATmega32U4 Configurator.
Allows enabling multiple single-ended and differential channels.
"""

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QFrame, QGroupBox, QGridLayout,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from adc import (
    ADCConfig, ALL_ADC_CHANNELS, SE_CHANNELS, DIFF_CHANNELS,
    ADC_REFS, ADC_PRESCALERS, F_CPU_DEFAULT,
    fmt_adc_clock, conversion_time_us,
)

FONT      = QFont("Consolas", 12)
FONT_BOLD = QFont("Consolas", 12, QFont.Weight.Bold)
FONT_SM   = QFont("Consolas", 11)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class ADCPanel(QWidget):
    """ADC configuration panel — multi-channel selection."""

    config_changed = pyqtSignal()

    def __init__(self, adc_config: ADCConfig, parent=None):
        super().__init__(parent)
        self.cfg = adc_config
        self._f_cpu = F_CPU_DEFAULT
        self._building = False
        self._ch_checks: dict[int, QCheckBox] = {}   # idx → checkbox
        self._build_ui()
        self._sync_from_config()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

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

        # ── Enable ADC ────────────────────────────────────────────────────────
        self._chk_enable = QCheckBox("Enable ADC  (ADEN)")
        self._chk_enable.setFont(FONT_BOLD)
        self._chk_enable.stateChanged.connect(self._on_enable)
        root.addWidget(self._chk_enable)

        root.addWidget(_hline())

        # ── Reference voltage ─────────────────────────────────────────────────
        ref_box = QGroupBox("Referentni napon (REFS)")
        ref_box.setFont(FONT_BOLD)
        ref_lay = QVBoxLayout(ref_box)
        ref_lay.setContentsMargins(8, 6, 8, 8)
        ref_lay.setSpacing(4)

        self._cmb_ref = QComboBox()
        self._cmb_ref.setFont(FONT)
        for r in ADC_REFS:
            self._cmb_ref.addItem(r.label)
        self._cmb_ref.currentIndexChanged.connect(self._on_ref)
        ref_lay.addWidget(self._cmb_ref)
        root.addWidget(ref_box)

        # ── Prescaler ─────────────────────────────────────────────────────────
        ps_box = QGroupBox("Prescaler (ADPS)")
        ps_box.setFont(FONT_BOLD)
        ps_lay = QVBoxLayout(ps_box)
        ps_lay.setContentsMargins(8, 6, 8, 8)
        ps_lay.setSpacing(6)

        self._cmb_prescaler = QComboBox()
        self._cmb_prescaler.setFont(FONT)
        for p in ADC_PRESCALERS:
            self._cmb_prescaler.addItem(p.label)
        self._cmb_prescaler.currentIndexChanged.connect(self._on_prescaler)
        ps_lay.addWidget(self._cmb_prescaler)

        self._lbl_clock = QLabel("")
        self._lbl_clock.setFont(FONT)
        self._lbl_clock.setStyleSheet("color: #F0C040;")
        ps_lay.addWidget(self._lbl_clock)
        root.addWidget(ps_box)

        root.addWidget(_hline())

        # ── Single-ended channels ─────────────────────────────────────────────
        se_box = QGroupBox("Single-ended kanali")
        se_box.setFont(FONT_BOLD)
        se_grid = QGridLayout(se_box)
        se_grid.setContentsMargins(8, 6, 8, 8)
        se_grid.setSpacing(4)

        for i, ch in enumerate(SE_CHANNELS):
            if ch.pin_num:
                text = f"{ch.label}  ({ch.pin_name}, pin {ch.pin_num})"
            else:
                text = ch.label
            cb = QCheckBox(text)
            cb.setFont(FONT_SM)
            cb.stateChanged.connect(self._on_channel_toggled)
            self._ch_checks[ch.idx] = cb
            se_grid.addWidget(cb, i, 0)

        root.addWidget(se_box)

        # ── Differential channels ─────────────────────────────────────────────
        diff_box = QGroupBox("Diferencijalni kanali")
        diff_box.setFont(FONT_BOLD)
        diff_grid = QGridLayout(diff_box)
        diff_grid.setContentsMargins(8, 6, 8, 8)
        diff_grid.setSpacing(4)

        for i, ch in enumerate(DIFF_CHANNELS):
            text = f"{ch.label}  ({ch.pin_name})"
            cb = QCheckBox(text)
            cb.setFont(FONT_SM)
            cb.stateChanged.connect(self._on_channel_toggled)
            self._ch_checks[ch.idx] = cb
            diff_grid.addWidget(cb, i, 0)

        root.addWidget(diff_box)

        # ── Summary ───────────────────────────────────────────────────────────
        root.addWidget(_hline())

        self._lbl_summary = QLabel("")
        self._lbl_summary.setFont(FONT)
        self._lbl_summary.setWordWrap(True)
        self._lbl_summary.setStyleSheet("color: #AAAAAA;")
        root.addWidget(self._lbl_summary)

        root.addStretch()

    # ── Sync UI from config ───────────────────────────────────────────────────

    def _sync_from_config(self):
        self._building = True

        self._chk_enable.setChecked(self.cfg.enabled)
        self._cmb_ref.setCurrentIndex(self.cfg.ref_idx)
        self._cmb_prescaler.setCurrentIndex(self.cfg.prescaler_idx)

        for idx, cb in self._ch_checks.items():
            cb.setChecked(idx in self.cfg.enabled_channels)

        self._building = False
        self._update_ui_state()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_enable(self, state):
        if self._building:
            return
        self.cfg.enabled = bool(state)
        self._update_ui_state()
        self.config_changed.emit()

    def _on_ref(self, idx):
        if self._building:
            return
        self.cfg.ref_idx = idx
        self.config_changed.emit()

    def _on_prescaler(self, idx):
        if self._building:
            return
        if 0 <= idx < len(ADC_PRESCALERS):
            self.cfg.prescaler_idx = idx
        self._update_prescaler_info()
        self.config_changed.emit()

    def _on_channel_toggled(self, _state):
        if self._building:
            return
        # Rebuild enabled set from checkboxes
        self.cfg.enabled_channels = {
            idx for idx, cb in self._ch_checks.items() if cb.isChecked()
        }
        self._update_summary()
        self.config_changed.emit()

    # ── UI updates ────────────────────────────────────────────────────────────

    def _update_ui_state(self):
        en = self.cfg.enabled
        self._cmb_ref.setEnabled(en)
        self._cmb_prescaler.setEnabled(en)
        for cb in self._ch_checks.values():
            cb.setEnabled(en)
        self._update_prescaler_info()
        self._update_summary()

    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._update_prescaler_info()

    def _update_prescaler_info(self):
        idx = self.cfg.prescaler_idx
        clk = fmt_adc_clock(idx, self._f_cpu)
        conv = conversion_time_us(idx, self._f_cpu)
        self._lbl_clock.setText(
            f"ADC clock: {clk}\n"
            f"Konverzija: ~{conv:.0f} \u00b5s (13 ciklusa)"
        )

    def _update_summary(self):
        if not self.cfg.enabled:
            self._lbl_summary.setText("ADC isklju\u010den.")
            return

        n = len(self.cfg.enabled_channels)
        if n == 0:
            self._lbl_summary.setText("Nema odabranih kanala.")
        else:
            names = []
            for idx in sorted(self.cfg.enabled_channels):
                ch = ALL_ADC_CHANNELS[idx]
                names.append(ch.label)
            self._lbl_summary.setText(
                f"Odabrano kanala: {n}\n" + ", ".join(names)
            )
