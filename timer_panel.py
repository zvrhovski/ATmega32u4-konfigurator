"""
Timer configuration UI panel.
Contains one TimerWidget per timer inside a QTabWidget.
"""

from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
    QGridLayout, QGroupBox, QCheckBox, QComboBox, QSpinBox,
    QLabel, QFrame, QSizePolicy, QSlider,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui  import QFont

from timers import (
    TimerDef, TimerConfig, ChannelConfig, WGMMode,
    ALL_TIMERS, calc_freq, calc_duty, fmt_freq, fmt_period,
    calc_overflow_time, effective_top, F_CPU_DEFAULT,
    PLL_TM_OPTIONS,
)

MONO = QFont("Consolas", 12)
MONO_B = QFont("Consolas", 10, QFont.Weight.Bold)
LABEL_FONT = QFont("Segoe UI", 8)

# COM options shown in the combo box per mode type
COM_LABELS_NORMAL = ["Disconnected", "Toggle on match",
                     "Clear on match", "Set on match"]
COM_LABELS_PWM    = ["Disconnected", "Non-inverted PWM", "Inverted PWM"]
# COM_LABELS_PWM index → actual COM bits:  0→0, 1→2, 2→3
COM_PWM_BITS      = [0, 2, 3]


def _sep():
    """Thin horizontal separator."""
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setFrameShadow(QFrame.Shadow.Sunken)
    return f


class ChannelGroup(QGroupBox):
    """Config widget for one OC channel (A/B/C/D)."""

    changed = pyqtSignal()

    def __init__(self, ch_def, cfg: ChannelConfig, timer_n: int, parent=None):
        super().__init__(parent)
        self.ch_def  = ch_def
        self.cfg     = cfg
        self.timer_n = timer_n
        self._building = False

        title = (f"Channel {ch_def.letter}  "
                 f"(OC{timer_n}{ch_def.letter} → {ch_def.pin_name}  pin {ch_def.pin_num})")
        self.setTitle(title)
        self.setFont(MONO_B)
        self.setCheckable(True)
        self.setChecked(cfg.enabled)
        self.toggled.connect(self._on_enable)

        grid = QGridLayout(self)
        grid.setSpacing(4)

        grid.addWidget(QLabel("Output mode:"), 0, 0)
        self.com_combo = QComboBox()
        self.com_combo.setFont(MONO)
        grid.addWidget(self.com_combo, 0, 1)
        self.com_combo.currentIndexChanged.connect(self._on_com)

        self._ocr_label = QLabel(f"OCR{timer_n}{ch_def.letter}:")
        grid.addWidget(self._ocr_label, 1, 0)
        self.ocr_spin = QSpinBox()
        self.ocr_spin.setFont(MONO)
        self.ocr_spin.setRange(0, 65535)
        self.ocr_spin.setValue(cfg.ocr)
        grid.addWidget(self.ocr_spin, 1, 1)
        self.ocr_spin.valueChanged.connect(self._on_ocr)

        self.duty_label = QLabel("Duty: —")
        self.duty_label.setFont(MONO)
        grid.addWidget(self.duty_label, 1, 2)

        self._set_controls_enabled(cfg.enabled)

    def set_mode(self, is_pwm: bool, top: int, is_ctc: bool = False):
        """Called by parent when timer mode or TOP changes."""
        self._building = True
        self._is_ctc = is_ctc
        prev_com = self.cfg.com
        self.com_combo.clear()

        if is_pwm:
            self.com_combo.addItems(COM_LABELS_PWM)
            if prev_com in COM_PWM_BITS:
                self.com_combo.setCurrentIndex(COM_PWM_BITS.index(prev_com))
            else:
                self.com_combo.setCurrentIndex(0)
        else:
            self.com_combo.addItems(COM_LABELS_NORMAL)
            self.com_combo.setCurrentIndex(min(prev_com, 3))

        # Update OCR max
        self.ocr_spin.setMaximum(top if top > 0 else 65535)
        self._building = False

        # CTC: hide OCR row and duty (no duty in CTC, OCR=TOP is set above)
        self._ocr_label.setVisible(not is_ctc)
        self.ocr_spin.setVisible(not is_ctc)
        self.duty_label.setVisible(not is_ctc)

        self._refresh_duty(top)

    def _refresh_duty(self, top: int):
        if getattr(self, '_is_ctc', False):
            self.duty_label.setText("")
            return
        if not self.cfg.enabled or top == 0:
            self.duty_label.setText("Duty: \u2014")
            return
        d = calc_duty(self.cfg.ocr, top)
        self.duty_label.setText(f"Duty: {d:.1f}%")

    def _on_enable(self, checked: bool):
        self.cfg.enabled = checked
        self._set_controls_enabled(checked)
        self.changed.emit()

    def _on_com(self, idx: int):
        if self._building:
            return
        # determine actual COM bits
        if len(self.com_combo) == len(COM_LABELS_PWM):
            self.cfg.com = COM_PWM_BITS[idx]
        else:
            self.cfg.com = idx
        self.changed.emit()

    def _on_ocr(self, val: int):
        if self._building:
            return
        self.cfg.ocr = val
        self.changed.emit()

    def _set_controls_enabled(self, enabled: bool):
        self.com_combo.setEnabled(enabled)
        self.ocr_spin.setEnabled(enabled)
        self.duty_label.setEnabled(enabled)


class OverflowGroup(QGroupBox):
    """TCNTn preload + TOIE — visible only in Normal mode."""

    changed = pyqtSignal()

    def __init__(self, tdef: TimerDef, cfg: TimerConfig, parent=None):
        super().__init__(f"Overflow / TCNT{tdef.n} Preload")
        self.tdef = tdef
        self.cfg  = cfg
        self._max = (1 << tdef.bits) - 1   # 255 / 65535 / 1023
        self._f_cpu = F_CPU_DEFAULT
        self._building = False
        self.setFont(MONO_B)

        vbox = QVBoxLayout(self)
        vbox.setSpacing(6)

        # ── TOIE checkbox ─────────────────────────────────────────────────────
        self.toie_cb = QCheckBox(f"Enable overflow interrupt  (TOIE{tdef.n})")
        self.toie_cb.setFont(MONO)
        self.toie_cb.setChecked(cfg.toie)
        self.toie_cb.toggled.connect(self._on_toie)
        vbox.addWidget(self.toie_cb)

        vbox.addWidget(_sep())

        # ── Range label ───────────────────────────────────────────────────────
        self.range_label = QLabel("")
        self.range_label.setFont(QFont("Consolas", 9))
        self.range_label.setStyleSheet("color:#666;")
        vbox.addWidget(self.range_label)

        # ── Slider (position = MAX - TCNT → right = longer period) ───────────
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, self._max)
        self.slider.setValue(self._max - cfg.tcnt)
        self.slider.setSingleStep(max(1, self._max // 256))
        self.slider.setPageStep(max(1, self._max // 20))
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(max(1, self._max // 10))
        self.slider.valueChanged.connect(self._on_slider)
        vbox.addWidget(self.slider)

        # ── Spinbox row ───────────────────────────────────────────────────────
        spin_row = QHBoxLayout()
        spin_row.addWidget(QLabel(f"TCNT{tdef.n}:"))

        self.tcnt_spin = QSpinBox()
        self.tcnt_spin.setFont(MONO)
        self.tcnt_spin.setRange(0, self._max)
        self.tcnt_spin.setValue(cfg.tcnt)
        self.tcnt_spin.valueChanged.connect(self._on_tcnt)
        spin_row.addWidget(self.tcnt_spin)
        spin_row.addStretch()
        vbox.addLayout(spin_row)

        # ── Result label ──────────────────────────────────────────────────────
        self.result_label = QLabel("—")
        self.result_label.setFont(MONO_B)
        self.result_label.setStyleSheet("color:#4EC9B0;")  # teal accent
        vbox.addWidget(self.result_label)

        self._refresh_labels()

    # ── Public ────────────────────────────────────────────────────────────────

    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._refresh_labels()

    def notify_prescaler_changed(self):
        """Called by TimerWidget when prescaler changes."""
        self._refresh_labels()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_toie(self, checked: bool):
        self.cfg.toie = checked
        self.changed.emit()

    def _on_slider(self, slider_val: int):
        if self._building:
            return
        self._building = True
        tcnt = self._max - slider_val
        self.cfg.tcnt = tcnt
        self.tcnt_spin.setValue(tcnt)
        self._building = False
        self._refresh_labels()
        self.changed.emit()

    def _on_tcnt(self, val: int):
        if self._building:
            return
        self._building = True
        self.cfg.tcnt = val
        self.slider.setValue(self._max - val)
        self._building = False
        self._refresh_labels()
        self.changed.emit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _refresh_labels(self):
        cs = self.tdef.prescalers[self.cfg.prescaler_idx]

        # Range: min (TCNT=MAX-1) … max (TCNT=0)
        if cs.div > 0:
            t_min = 1          * cs.div / self._f_cpu
            t_max = self._max  * cs.div / self._f_cpu
            self.range_label.setText(
                f"Range: {fmt_period(t_min)}  …  {fmt_period(t_max)}"
                f"  (prescaler {cs.label})"
            )
        else:
            self.range_label.setText("Range: — (timer stopped)")

        # Current overflow time
        t = calc_overflow_time(self.tdef, self.cfg, self._f_cpu)
        if t and t > 0:
            hz = 1.0 / t
            self.result_label.setText(
                f"TCNT{self.tdef.n} = {self.cfg.tcnt}"
                f"  →  {fmt_period(t)}  ({fmt_freq(hz)})"
            )
        else:
            self.result_label.setText("—")


class TimerWidget(QScrollArea):
    """Full configuration widget for one timer."""

    changed = pyqtSignal()

    def __init__(self, tdef: TimerDef, cfg: TimerConfig, parent=None):
        super().__init__(parent)
        self.tdef = tdef
        self.cfg  = cfg
        self._ch_groups: list[ChannelGroup] = []
        self._f_cpu = F_CPU_DEFAULT
        self._building = False

        inner = QWidget()
        inner.setFont(MONO)
        self.setWidget(inner)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)

        vbox = QVBoxLayout(inner)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        # ── Enable ────────────────────────────────────────────────────────────
        self.enable_cb = QCheckBox(f"Enable {tdef.label}")
        self.enable_cb.setFont(MONO_B)
        self.enable_cb.setChecked(cfg.enabled)
        self.enable_cb.toggled.connect(self._on_enable)
        vbox.addWidget(self.enable_cb)

        vbox.addWidget(_sep())

        # ── Mode & prescaler ──────────────────────────────────────────────────
        grid = QGridLayout()
        grid.setSpacing(4)

        grid.addWidget(QLabel("Mode:"), 0, 0)
        self.mode_combo = QComboBox()
        self.mode_combo.setFont(MONO)
        for m in tdef.modes:
            self.mode_combo.addItem(m.name)
        self.mode_combo.setCurrentIndex(cfg.mode_idx)
        self.mode_combo.currentIndexChanged.connect(self._on_mode)
        grid.addWidget(self.mode_combo, 0, 1)

        grid.addWidget(QLabel("Prescaler:"), 1, 0)
        self.cs_combo = QComboBox()
        self.cs_combo.setFont(MONO)
        for cs in tdef.prescalers:
            self.cs_combo.addItem(cs.label)
        self.cs_combo.setCurrentIndex(cfg.prescaler_idx)
        self.cs_combo.currentIndexChanged.connect(self._on_prescaler)
        grid.addWidget(self.cs_combo, 1, 1)

        vbox.addLayout(grid)

        # ── PLL (Timer 4 only) ───────────────────────────────────────────────
        self._pll_group = QGroupBox("PLL Clock (Timer 4)")
        self._pll_group.setFont(MONO_B)
        pll_lay = QVBoxLayout(self._pll_group)
        pll_lay.setContentsMargins(8, 6, 8, 8)
        pll_lay.setSpacing(4)

        self._pll_enable = QCheckBox("Enable PLL za Timer 4")
        self._pll_enable.setFont(MONO)
        self._pll_enable.setChecked(cfg.pll_enabled)
        self._pll_enable.toggled.connect(self._on_pll_enable)
        pll_lay.addWidget(self._pll_enable)

        pll_row = QHBoxLayout()
        pll_row.addWidget(QLabel("Timer 4 clock:"))
        self._pll_tm_combo = QComboBox()
        self._pll_tm_combo.setFont(MONO)
        for opt in PLL_TM_OPTIONS:
            self._pll_tm_combo.addItem(opt.label)
        self._pll_tm_combo.setCurrentIndex(cfg.pll_tm_idx)
        self._pll_tm_combo.currentIndexChanged.connect(self._on_pll_tm)
        self._pll_tm_combo.setEnabled(cfg.pll_enabled)
        pll_row.addWidget(self._pll_tm_combo)
        pll_lay.addLayout(pll_row)

        self._pll_group.setVisible(tdef.n == 4)
        vbox.addWidget(self._pll_group)

        # ── TOP value ─────────────────────────────────────────────────────────
        top_row = QHBoxLayout()
        self.top_label = QLabel("TOP:")
        self.top_label.setFont(MONO)
        self.top_spin = QSpinBox()
        self.top_spin.setFont(MONO)
        self.top_spin.setRange(1, (1 << tdef.bits) - 1)
        self.top_spin.setValue(cfg.top)
        self.top_spin.valueChanged.connect(self._on_top)
        top_row.addWidget(self.top_label)
        top_row.addWidget(self.top_spin)
        top_row.addStretch()
        vbox.addLayout(top_row)

        # ── Frequency display ─────────────────────────────────────────────────
        freq_box = QGroupBox("Calculated  (@16 MHz)")
        freq_box.setFont(MONO_B)
        freq_grid = QGridLayout(freq_box)
        freq_grid.setSpacing(2)

        self.freq_label  = QLabel("—")
        self.freq_label.setFont(MONO)
        self.per_label   = QLabel("—")
        self.per_label.setFont(MONO)

        freq_grid.addWidget(QLabel("Frequency:"), 0, 0)
        freq_grid.addWidget(self.freq_label, 0, 1)
        freq_grid.addWidget(QLabel("Period:"),    1, 0)
        freq_grid.addWidget(self.per_label,  1, 1)

        # CTC-only: OC toggle frequency (half of compare match freq)
        self._oc_freq_lbl_title = QLabel("OC Toggle:")
        self._oc_freq_lbl = QLabel("—")
        self._oc_freq_lbl.setFont(MONO)
        self._oc_per_lbl_title = QLabel("OC Period:")
        self._oc_per_lbl = QLabel("—")
        self._oc_per_lbl.setFont(MONO)
        freq_grid.addWidget(self._oc_freq_lbl_title, 2, 0)
        freq_grid.addWidget(self._oc_freq_lbl, 2, 1)
        freq_grid.addWidget(self._oc_per_lbl_title, 3, 0)
        freq_grid.addWidget(self._oc_per_lbl, 3, 1)

        vbox.addWidget(freq_box)
        vbox.addWidget(_sep())

        # ── Normal mode: overflow / TCNT preload ──────────────────────────────
        self._ovf_group = OverflowGroup(tdef, cfg)
        self._ovf_group.changed.connect(self.changed)
        vbox.addWidget(self._ovf_group)

        # ── CTC mode: output compare interrupt ────────────────────────────────
        self._ocie_cb = QCheckBox(f"Enable Compare Match Interrupt  (OCIE{tdef.n}A)")
        self._ocie_cb.setFont(MONO)
        self._ocie_cb.setChecked(cfg.ocie)
        self._ocie_cb.toggled.connect(self._on_ocie)
        vbox.addWidget(self._ocie_cb)

        # ── Channels ──────────────────────────────────────────────────────────
        for ch_def in tdef.channels:
            grp = ChannelGroup(ch_def, cfg.ch(ch_def.letter), tdef.n)
            grp.changed.connect(self._on_ch_changed)
            self._ch_groups.append(grp)
            vbox.addWidget(grp)

        vbox.addStretch()

        self._set_all_enabled(cfg.enabled)
        self._update_top_visibility()
        self._update_ovf_visibility()
        self._sync_channels_to_mode()
        self._update_freq()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_enable(self, checked: bool):
        self.cfg.enabled = checked
        self._set_all_enabled(checked)
        self.changed.emit()

    def _on_mode(self, idx: int):
        if self._building:
            return
        self.cfg.mode_idx = idx
        self._update_top_visibility()
        self._sync_channels_to_mode()
        self._update_freq()
        self._update_ovf_visibility()
        self.changed.emit()

    def _on_prescaler(self, idx: int):
        if self._building:
            return
        self.cfg.prescaler_idx = idx
        self._update_freq()
        self._ovf_group.notify_prescaler_changed()
        self.changed.emit()

    def _on_top(self, val: int):
        if self._building:
            return
        self.cfg.top = val
        self._sync_channels_to_mode()
        self._update_freq()
        self.changed.emit()

    def _on_ocie(self, checked: bool):
        self.cfg.ocie = checked
        self.changed.emit()

    def _on_pll_enable(self, checked: bool):
        if self._building:
            return
        self.cfg.pll_enabled = checked
        self._pll_tm_combo.setEnabled(checked)
        self._update_freq()
        self.changed.emit()

    def _on_pll_tm(self, idx: int):
        if self._building:
            return
        self.cfg.pll_tm_idx = idx
        self._update_freq()
        self.changed.emit()

    def _on_ch_changed(self):
        top = effective_top(self.tdef, self.cfg) or self.cfg.top
        for grp in self._ch_groups:
            mode = self.tdef.modes[self.cfg.mode_idx]
            grp._refresh_duty(top)
        self.changed.emit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _current_mode(self) -> WGMMode:
        return self.tdef.modes[self.cfg.mode_idx]

    def _update_top_visibility(self):
        mode = self._current_mode()
        user_set = mode.top_fixed is None
        self.top_label.setVisible(user_set)
        self.top_spin.setVisible(user_set)
        if not user_set and mode.top_fixed is not None:
            # show fixed TOP value as read-only info
            pass

        # Rename label based on which register holds TOP
        reg = {"OCRA": f"OCR{self.tdef.n}A",
               "ICR":  f"ICR{self.tdef.n}",
               "OCRC": f"OCR{self.tdef.n}C"}.get(mode.top, "TOP")
        self.top_label.setText(f"{reg} (TOP):")

    def _sync_channels_to_mode(self):
        mode = self._current_mode()
        top  = effective_top(self.tdef, self.cfg)
        if top is None:
            top = self.cfg.top
        is_ctc = "CTC" in mode.name
        for grp in self._ch_groups:
            grp.set_mode(mode.is_pwm, top, is_ctc)

    def _effective_clock(self) -> int:
        """Return effective clock for this timer (PLL or F_CPU)."""
        if self.tdef.n == 4 and self.cfg.pll_enabled:
            pll_opt = PLL_TM_OPTIONS[self.cfg.pll_tm_idx]
            if pll_opt.clock_hz > 0:
                return pll_opt.clock_hz
        return self._f_cpu

    def _update_freq(self):
        mode = self._current_mode()
        is_ctc = "CTC" in mode.name
        hz = calc_freq(self.tdef, self.cfg, self._effective_clock())

        # Compare match / overflow frequency
        self.freq_label.setText(fmt_freq(hz))
        if hz and hz > 0:
            self.per_label.setText(fmt_period(1.0 / hz))
        else:
            self.per_label.setText("\u2014")

        # OC toggle frequency (CTC only, = half of compare match)
        if is_ctc and hz and hz > 0:
            oc_hz = hz / 2
            self._oc_freq_lbl.setText(fmt_freq(oc_hz))
            self._oc_per_lbl.setText(fmt_period(1.0 / oc_hz))
        else:
            self._oc_freq_lbl.setText("\u2014")
            self._oc_per_lbl.setText("\u2014")

    def _update_ovf_visibility(self):
        mode = self._current_mode()
        is_normal = mode.wgm == 0
        is_ctc = "CTC" in mode.name
        self._ovf_group.setVisible(is_normal)
        self._ocie_cb.setVisible(is_ctc)
        # OC channels — hide in Normal mode (no compare output)
        for grp in self._ch_groups:
            grp.setVisible(not is_normal)
        # OC toggle freq rows — only in CTC
        for w in (self._oc_freq_lbl_title, self._oc_freq_lbl,
                  self._oc_per_lbl_title, self._oc_per_lbl):
            w.setVisible(is_ctc)

    def set_f_cpu(self, f_cpu: int):
        self._f_cpu = f_cpu
        self._ovf_group.set_f_cpu(f_cpu)
        self._update_freq()

    def _set_all_enabled(self, on: bool):
        for w in (self.mode_combo, self.cs_combo, self.top_spin):
            w.setEnabled(on)
        self._ovf_group.setEnabled(on)
        for grp in self._ch_groups:
            grp.setEnabled(on)


# ── Top-level panel ───────────────────────────────────────────────────────────

class TimerPanel(QTabWidget):
    """QTabWidget holding one TimerWidget per timer."""

    config_changed = pyqtSignal()

    def __init__(self, timer_configs: dict[int, TimerConfig], parent=None):
        super().__init__(parent)
        self.timer_configs = timer_configs
        self._timer_widgets: list[TimerWidget] = []
        self.setFont(QFont("Segoe UI", 8))

        for tdef in ALL_TIMERS:
            w = TimerWidget(tdef, timer_configs[tdef.n])
            w.changed.connect(self.config_changed)
            self._timer_widgets.append(w)
            self.addTab(w, f"T{tdef.n}")

        self.setTabPosition(QTabWidget.TabPosition.North)

    def set_f_cpu(self, f_cpu: int):
        for w in self._timer_widgets:
            w.set_f_cpu(f_cpu)
