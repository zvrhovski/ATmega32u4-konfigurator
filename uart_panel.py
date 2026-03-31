"""
USART1 configuration panel for ATmega32U4 Configurator.
"""

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QComboBox, QFrame, QGroupBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from uart import (
    USARTConfig, BAUD_RATES, DATA_BITS_OPTIONS, PARITY_OPTIONS,
    STOP_BITS_OPTIONS, F_CPU_DEFAULT,
    fmt_baud_info, calc_baud_error,
)

FONT      = QFont("Consolas", 12)
FONT_BOLD = QFont("Consolas", 12, QFont.Weight.Bold)


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class USARTPanel(QWidget):
    """USART1 configuration panel."""

    config_changed = pyqtSignal()

    def __init__(self, uart_config: USARTConfig, parent=None):
        super().__init__(parent)
        self.cfg = uart_config
        self._f_cpu = F_CPU_DEFAULT
        self._building = False
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

        # ── Enable ────────────────────────────────────────────────────────────
        self._chk_enable = QCheckBox("Enable USART1")
        self._chk_enable.setFont(FONT_BOLD)
        self._chk_enable.stateChanged.connect(self._on_enable)
        root.addWidget(self._chk_enable)

        root.addWidget(_hline())

        # ── Baud rate ─────────────────────────────────────────────────────────
        baud_box = QGroupBox("Baud rate")
        baud_box.setFont(FONT_BOLD)
        baud_lay = QVBoxLayout(baud_box)
        baud_lay.setContentsMargins(8, 6, 8, 8)
        baud_lay.setSpacing(6)

        self._cmb_baud = QComboBox()
        self._cmb_baud.setFont(FONT)
        for b in BAUD_RATES:
            self._cmb_baud.addItem(f"{b}")
        self._cmb_baud.currentIndexChanged.connect(self._on_baud)
        baud_lay.addWidget(self._cmb_baud)

        self._chk_u2x = QCheckBox("U2X  (double speed)")
        self._chk_u2x.setFont(FONT)
        self._chk_u2x.stateChanged.connect(self._on_u2x)
        baud_lay.addWidget(self._chk_u2x)

        self._lbl_baud_info = QLabel("")
        self._lbl_baud_info.setFont(FONT)
        self._lbl_baud_info.setWordWrap(True)
        self._lbl_baud_info.setStyleSheet("color: #F0C040;")
        baud_lay.addWidget(self._lbl_baud_info)

        root.addWidget(baud_box)

        # ── Frame format ──────────────────────────────────────────────────────
        fmt_box = QGroupBox("Format okvira")
        fmt_box.setFont(FONT_BOLD)
        fmt_lay = QVBoxLayout(fmt_box)
        fmt_lay.setContentsMargins(8, 6, 8, 8)
        fmt_lay.setSpacing(6)

        # Data bits
        row_db = QHBoxLayout()
        row_db.addWidget(QLabel("Data bits:"))
        self._cmb_databits = QComboBox()
        self._cmb_databits.setFont(FONT)
        for d in DATA_BITS_OPTIONS:
            self._cmb_databits.addItem(d.label)
        self._cmb_databits.currentIndexChanged.connect(self._on_databits)
        row_db.addWidget(self._cmb_databits)
        fmt_lay.addLayout(row_db)

        # Parity
        row_par = QHBoxLayout()
        row_par.addWidget(QLabel("Paritet:"))
        self._cmb_parity = QComboBox()
        self._cmb_parity.setFont(FONT)
        for p in PARITY_OPTIONS:
            self._cmb_parity.addItem(p.label)
        self._cmb_parity.currentIndexChanged.connect(self._on_parity)
        row_par.addWidget(self._cmb_parity)
        fmt_lay.addLayout(row_par)

        # Stop bits
        row_sb = QHBoxLayout()
        row_sb.addWidget(QLabel("Stop bits:"))
        self._cmb_stopbits = QComboBox()
        self._cmb_stopbits.setFont(FONT)
        for s in STOP_BITS_OPTIONS:
            self._cmb_stopbits.addItem(s.label)
        self._cmb_stopbits.currentIndexChanged.connect(self._on_stopbits)
        row_sb.addWidget(self._cmb_stopbits)
        fmt_lay.addLayout(row_sb)

        root.addWidget(fmt_box)

        # ── TX / RX enable ────────────────────────────────────────────────────
        txrx_box = QGroupBox("TX / RX")
        txrx_box.setFont(FONT_BOLD)
        txrx_lay = QVBoxLayout(txrx_box)
        txrx_lay.setContentsMargins(8, 6, 8, 8)
        txrx_lay.setSpacing(4)

        self._chk_tx = QCheckBox("TX Enable  (TXEN1)  \u2014  TXD1 = PD3, pin 20")
        self._chk_tx.setFont(FONT)
        self._chk_tx.stateChanged.connect(self._on_tx)
        txrx_lay.addWidget(self._chk_tx)

        self._chk_rx = QCheckBox("RX Enable  (RXEN1)  \u2014  RXD1 = PD2, pin 19")
        self._chk_rx.setFont(FONT)
        self._chk_rx.stateChanged.connect(self._on_rx)
        txrx_lay.addWidget(self._chk_rx)

        root.addWidget(txrx_box)

        # ── Interrupts ────────────────────────────────────────────────────────
        irq_box = QGroupBox("Prekidi (Interrupts)")
        irq_box.setFont(FONT_BOLD)
        irq_lay = QVBoxLayout(irq_box)
        irq_lay.setContentsMargins(8, 6, 8, 8)
        irq_lay.setSpacing(4)

        self._chk_rxcie = QCheckBox("RX Complete  (RXCIE1)")
        self._chk_rxcie.setFont(FONT)
        self._chk_rxcie.stateChanged.connect(self._on_irq)
        irq_lay.addWidget(self._chk_rxcie)

        self._chk_txcie = QCheckBox("TX Complete  (TXCIE1)")
        self._chk_txcie.setFont(FONT)
        self._chk_txcie.stateChanged.connect(self._on_irq)
        irq_lay.addWidget(self._chk_txcie)

        self._chk_udrie = QCheckBox("Data Register Empty  (UDRIE1)")
        self._chk_udrie.setFont(FONT)
        self._chk_udrie.stateChanged.connect(self._on_irq)
        irq_lay.addWidget(self._chk_udrie)

        root.addWidget(irq_box)

        # ── Summary ───────────────────────────────────────────────────────────
        root.addWidget(_hline())

        self._lbl_summary = QLabel("")
        self._lbl_summary.setFont(FONT)
        self._lbl_summary.setWordWrap(True)
        self._lbl_summary.setStyleSheet("color: #AAAAAA;")
        root.addWidget(self._lbl_summary)

        root.addStretch()

    # ── Sync from config ──────────────────────────────────────────────────────

    def _sync_from_config(self):
        self._building = True

        self._chk_enable.setChecked(self.cfg.enabled)
        self._cmb_baud.setCurrentIndex(self.cfg.baud_idx)
        self._chk_u2x.setChecked(self.cfg.u2x)
        self._cmb_databits.setCurrentIndex(self.cfg.databits_idx)
        self._cmb_parity.setCurrentIndex(self.cfg.parity_idx)
        self._cmb_stopbits.setCurrentIndex(self.cfg.stopbits_idx)
        self._chk_tx.setChecked(self.cfg.tx_en)
        self._chk_rx.setChecked(self.cfg.rx_en)
        self._chk_rxcie.setChecked(self.cfg.rxcie)
        self._chk_txcie.setChecked(self.cfg.txcie)
        self._chk_udrie.setChecked(self.cfg.udrie)

        self._building = False
        self._update_ui_state()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_enable(self, state):
        if self._building: return
        self.cfg.enabled = bool(state)
        self._update_ui_state()
        self.config_changed.emit()

    def _on_baud(self, idx):
        if self._building: return
        self.cfg.baud_idx = idx
        self._update_baud_info()
        self.config_changed.emit()

    def _on_u2x(self, state):
        if self._building: return
        self.cfg.u2x = bool(state)
        self._update_baud_info()
        self.config_changed.emit()

    def _on_databits(self, idx):
        if self._building: return
        self.cfg.databits_idx = idx
        self._update_summary()
        self.config_changed.emit()

    def _on_parity(self, idx):
        if self._building: return
        self.cfg.parity_idx = idx
        self._update_summary()
        self.config_changed.emit()

    def _on_stopbits(self, idx):
        if self._building: return
        self.cfg.stopbits_idx = idx
        self._update_summary()
        self.config_changed.emit()

    def _on_tx(self, state):
        if self._building: return
        self.cfg.tx_en = bool(state)
        self.config_changed.emit()

    def _on_rx(self, state):
        if self._building: return
        self.cfg.rx_en = bool(state)
        self.config_changed.emit()

    def _on_irq(self, _state):
        if self._building: return
        self.cfg.rxcie = self._chk_rxcie.isChecked()
        self.cfg.txcie = self._chk_txcie.isChecked()
        self.cfg.udrie = self._chk_udrie.isChecked()
        self.config_changed.emit()

    # ── UI updates ────────────────────────────────────────────────────────────

    def _update_ui_state(self):
        en = self.cfg.enabled
        self._cmb_baud.setEnabled(en)
        self._chk_u2x.setEnabled(en)
        self._cmb_databits.setEnabled(en)
        self._cmb_parity.setEnabled(en)
        self._cmb_stopbits.setEnabled(en)
        self._chk_tx.setEnabled(en)
        self._chk_rx.setEnabled(en)
        self._chk_rxcie.setEnabled(en)
        self._chk_txcie.setEnabled(en)
        self._chk_udrie.setEnabled(en)
        self._update_baud_info()
        self._update_summary()

    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._update_baud_info()
        self._update_summary()

    def _update_baud_info(self):
        if not self.cfg.enabled:
            self._lbl_baud_info.setText("")
            return
        info = fmt_baud_info(self.cfg.baud, self.cfg.u2x, self._f_cpu)
        error = abs(calc_baud_error(self.cfg.baud, self.cfg.u2x, self._f_cpu))
        if error > 2.0:
            info += "\n\u26a0 Velika gre\u0161ka! Preporu\u010da se U2X."
        self._lbl_baud_info.setText(info)

    def _update_summary(self):
        if not self.cfg.enabled:
            self._lbl_summary.setText("USART1 isklju\u010den.")
            return

        fmt = self.cfg.format_str
        baud = self.cfg.baud
        ubrr = self.cfg.ubrr(self._f_cpu)

        parts = []
        if self.cfg.tx_en: parts.append("TX")
        if self.cfg.rx_en: parts.append("RX")
        txrx = "+".join(parts) if parts else "ni TX ni RX"

        irq_parts = []
        if self.cfg.rxcie: irq_parts.append("RXCIE")
        if self.cfg.txcie: irq_parts.append("TXCIE")
        if self.cfg.udrie: irq_parts.append("UDRIE")
        irq_str = ", ".join(irq_parts) if irq_parts else "nema"

        self._lbl_summary.setText(
            f"{fmt} @ {baud} baud  (UBRR={ubrr})\n"
            f"{txrx}\n"
            f"Prekidi: {irq_str}"
        )
