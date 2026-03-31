"""
Interrupt configuration UI panel.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QCheckBox, QComboBox, QLabel,
    QFrame, QScrollArea, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from interrupts import (
    InterruptConfig, ExtIntDef, PCIntPinDef,
    EXT_INTS, PCINT_PINS, SENSE_OPTIONS,
)

MONO   = QFont("Consolas", 12)
MONO_B = QFont("Consolas", 12, QFont.Weight.Bold)


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class InterruptPanel(QScrollArea):
    config_changed = pyqtSignal()

    def __init__(self, cfg: InterruptConfig, parent=None):
        super().__init__(parent)
        self.cfg = cfg

        inner = QWidget()
        self.setWidget(inner)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(8)

        # ── External interrupts INTx ──────────────────────────────────────────
        ext_box = QGroupBox("External Interrupts  (INTx)")
        ext_box.setFont(MONO_B)
        ext_grid = QGridLayout(ext_box)
        ext_grid.setSpacing(4)

        ext_grid.addWidget(QLabel("Interrupt"), 0, 0)
        ext_grid.addWidget(QLabel("Pin"),       0, 1)
        ext_grid.addWidget(QLabel("Trigger"),   0, 2)

        self._ext_checks: dict[int, QCheckBox] = {}
        self._ext_sense:  dict[int, QComboBox] = {}

        for row, edef in enumerate(EXT_INTS, start=1):
            ch = QCheckBox(f"INT{edef.n}")
            ch.setFont(MONO)
            ch.setChecked(cfg.ext[edef.n].enabled)
            ch.toggled.connect(lambda checked, n=edef.n: self._on_ext_enable(n, checked))
            self._ext_checks[edef.n] = ch

            pin_lbl = QLabel(f"{edef.pin_name}  (pin {edef.pin_num})")
            pin_lbl.setFont(MONO)

            sense = QComboBox()
            sense.setFont(MONO)
            for _, label in SENSE_OPTIONS:
                sense.addItem(label)
            # find current index
            cur = cfg.ext[edef.n].sense
            sense.setCurrentIndex(next(i for i, (v, _) in enumerate(SENSE_OPTIONS) if v == cur))
            sense.setEnabled(cfg.ext[edef.n].enabled)
            sense.currentIndexChanged.connect(
                lambda idx, n=edef.n: self._on_ext_sense(n, idx))
            self._ext_sense[edef.n] = sense

            ext_grid.addWidget(ch,      row, 0)
            ext_grid.addWidget(pin_lbl, row, 1)
            ext_grid.addWidget(sense,   row, 2)

        vbox.addWidget(ext_box)

        # ── Pin Change Interrupts PCINT0-7 ───────────────────────────────────
        pc_box = QGroupBox("Pin Change Interrupts  (PCINT0-7  →  Port B)")
        pc_box.setFont(MONO_B)
        pc_vbox = QVBoxLayout(pc_box)
        pc_vbox.setSpacing(4)

        self._pcie0_cb = QCheckBox("Enable PCIE0  (Port B group)")
        self._pcie0_cb.setFont(MONO)
        self._pcie0_cb.setChecked(cfg.pcint.group_enabled)
        self._pcie0_cb.toggled.connect(self._on_pcie0)
        pc_vbox.addWidget(self._pcie0_cb)

        pc_vbox.addWidget(_sep())

        pc_grid = QGridLayout()
        pc_grid.setSpacing(4)
        pc_vbox.addLayout(pc_grid)

        self._pcint_checks: dict[int, QCheckBox] = {}
        for i, pdef in enumerate(PCINT_PINS):
            cb = QCheckBox(f"PCINT{pdef.pcint_n}  ({pdef.pin_name}, pin {pdef.pin_num})")
            cb.setFont(MONO)
            cb.setChecked(cfg.pcint.pins.get(pdef.pcint_n, False))
            cb.setEnabled(cfg.pcint.group_enabled)
            cb.toggled.connect(
                lambda checked, n=pdef.pcint_n: self._on_pcint_pin(n, checked))
            self._pcint_checks[pdef.pcint_n] = cb
            pc_grid.addWidget(cb, i // 2, i % 2)

        vbox.addWidget(pc_box)

        # ── Global interrupt enable ───────────────────────────────────────────
        vbox.addWidget(_sep())

        self._sei_cb = QCheckBox("Enable global interrupts  — sei()")
        self._sei_cb.setFont(MONO_B)
        self._sei_cb.setChecked(cfg.sei)
        self._sei_cb.toggled.connect(self._on_sei)
        vbox.addWidget(self._sei_cb)

        sei_note = QLabel(
            "Adds sei() at the end of init().\n"
            "Without sei() no interrupts will fire."
        )
        sei_note.setFont(QFont("Segoe UI", 7))
        sei_note.setStyleSheet("color:#666;")
        vbox.addWidget(sei_note)

        vbox.addStretch()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_ext_enable(self, n: int, checked: bool):
        self.cfg.ext[n].enabled = checked
        self._ext_sense[n].setEnabled(checked)
        self.config_changed.emit()

    def _on_ext_sense(self, n: int, idx: int):
        self.cfg.ext[n].sense = SENSE_OPTIONS[idx][0]
        self.config_changed.emit()

    def _on_pcie0(self, checked: bool):
        self.cfg.pcint.group_enabled = checked
        for cb in self._pcint_checks.values():
            cb.setEnabled(checked)
        self.config_changed.emit()

    def _on_pcint_pin(self, n: int, checked: bool):
        self.cfg.pcint.pins[n] = checked
        self.config_changed.emit()

    def _on_sei(self, checked: bool):
        self.cfg.sei = checked
        self.config_changed.emit()
