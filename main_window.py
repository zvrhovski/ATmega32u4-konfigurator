import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QTextEdit, QLabel, QPushButton, QComboBox,
    QFrame, QApplication, QMenuBar, QMessageBox, QDialog,
    QDialogButtonBox,
)
from PyQt6.QtCore    import Qt, QTimer, QSize
from PyQt6.QtGui     import QFont, QAction, QPixmap, QPainter, QIcon
from PyQt6.QtSvg     import QSvgRenderer

_HERE     = os.path.dirname(os.path.abspath(__file__))
_LOGO_SVG = os.path.join(_HERE, "vub_logo.svg")


def _svg_pixmap(svg_path: str, height: int) -> QPixmap:
    """Render an SVG file to a QPixmap at the given height (aspect-ratio preserved)."""
    renderer = QSvgRenderer(svg_path)
    if not renderer.isValid():
        return QPixmap()
    default = renderer.defaultSize()
    w = int(default.width() * height / default.height())
    pixmap = QPixmap(QSize(w, height))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap

APP_NAME    = "ATmega32U4 Configurator"
APP_VERSION = "1.0"
APP_AUTHOR  = "Zoran Vrhovski"

from pins             import ALL_PINS, PIN_MAP, PinConfig, GpioMode, PinType
from timers           import make_timer_configs
from interrupts       import make_interrupt_config
from adc              import make_adc_config
from uart             import make_uart_config
from spi              import make_spi_config
from twi              import make_twi_config
from chip_widget      import ChipWidget
from pin_panel        import PinPanel
from timer_panel      import TimerPanel
from interrupt_panel  import InterruptPanel
from adc_panel        import ADCPanel
from uart_panel       import USARTPanel
from spi_panel        import SPIPanel
from twi_panel        import TWIPanel
from code_gen         import generate_code
from code_highlighter import CHighlighter


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        # size set by showMaximized() in _build_ui()
        if os.path.exists(_LOGO_SVG):
            self.setWindowIcon(QIcon(_svg_pixmap(_LOGO_SVG, 64)))

        # ── F_CPU options ─────────────────────────────────────────────────────
        self.F_CPU_OPTIONS = [
            (1_000_000,    "1 MHz (internal RC)"),
            (2_000_000,    "2 MHz"),
            (4_000_000,    "4 MHz"),
            (7_372_800,    "7.3728 MHz (UART)"),
            (8_000_000,    "8 MHz"),
            (11_059_200,   "11.0592 MHz (UART)"),
            (12_000_000,   "12 MHz"),
            (14_745_600,   "14.7456 MHz (UART)"),
            (16_000_000,   "16 MHz (default)"),
            (18_432_000,   "18.432 MHz (UART)"),
            (20_000_000,   "20 MHz"),
        ]
        self._f_cpu = 16_000_000
        self._f_cpu_idx = 8   # 16 MHz default

        # ── Shared state ──────────────────────────────────────────────────────
        self.pin_configs = {
            p.number: PinConfig()
            for p in ALL_PINS if p.pin_type == PinType.GPIO
        }
        self.timer_configs = make_timer_configs()
        self.irq_config    = make_interrupt_config()
        self.adc_config    = make_adc_config()
        self.uart_config   = make_uart_config()
        self.spi_config    = make_spi_config()
        self.twi_config    = make_twi_config()

        self._build_ui()
        self._build_menu()
        self._build_statusbar()
        self._refresh_code()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Left: code editor (2/3 width) ────────────────────────────────────
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(6, 6, 6, 6)
        lv.setSpacing(4)

        # F_CPU selector row
        fcpu_row = QHBoxLayout()
        fcpu_row.addWidget(QLabel("F_CPU:"))
        self._cmb_fcpu = QComboBox()
        self._cmb_fcpu.setFont(QFont("Consolas", 12))
        for _val, _label in self.F_CPU_OPTIONS:
            self._cmb_fcpu.addItem(_label)
        self._cmb_fcpu.setCurrentIndex(self._f_cpu_idx)
        self._cmb_fcpu.currentIndexChanged.connect(self._on_fcpu_changed)
        fcpu_row.addWidget(self._cmb_fcpu)
        fcpu_row.addStretch()
        lv.addLayout(fcpu_row)

        lv.addWidget(QLabel("Generated C code  (Atmel Studio / AVR-GCC):"))

        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setFont(QFont("Consolas", 12))
        self.code_edit.setStyleSheet(
            "QTextEdit { background:#1E1E1E; color:#D4D4D4; border:none; }"
        )
        self._highlighter = CHighlighter(self.code_edit.document())
        lv.addWidget(self.code_edit, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_copy = QPushButton("Copy to clipboard")
        self.btn_copy.setFont(QFont("Segoe UI", 8))
        self.btn_copy.clicked.connect(self._copy_code)
        btn_row.addWidget(self.btn_copy)
        lv.addLayout(btn_row)

        # ── Right: config tabs (top 2/3) + chip (bottom 1/3) ─────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        right_tabs = QTabWidget()
        right_tabs.setFont(QFont("Segoe UI", 10))

        # Tab 1 — Pin config + Chip
        pin_tab = QWidget()
        pin_vbox = QVBoxLayout(pin_tab)
        pin_vbox.setContentsMargins(0, 0, 0, 0)
        pin_vbox.setSpacing(0)

        self.pin_panel = PinPanel()
        self.pin_panel.set_pin_configs(self.pin_configs)
        self.pin_panel.config_changed.connect(self._on_pin_config_changed)
        pin_vbox.addWidget(self.pin_panel, stretch=1)

        self.chip = ChipWidget(self.pin_configs)
        self.chip.pin_selected.connect(self._on_pin_selected)
        pin_vbox.addWidget(self.chip, stretch=1)

        right_tabs.addTab(pin_tab, "📌 Pin")

        # Tab 2 — Timers
        self.timer_panel = TimerPanel(self.timer_configs)
        self.timer_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.timer_panel, "⏱ Timers")

        # Tab 3 — ADC
        self.adc_panel = ADCPanel(self.adc_config)
        self.adc_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.adc_panel, "📊 ADC")

        # Tab 4 — UART
        self.uart_panel = USARTPanel(self.uart_config)
        self.uart_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.uart_panel, "📡 UART")

        # Tab 5 — SPI
        self.spi_panel = SPIPanel(self.spi_config)
        self.spi_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.spi_panel, "🔌 SPI")

        # Tab 6 — I2C
        self.twi_panel = TWIPanel(self.twi_config)
        self.twi_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.twi_panel, "🔗 I2C")

        # Tab 7 — Interrupts
        self.irq_panel = InterruptPanel(self.irq_config)
        self.irq_panel.config_changed.connect(self._refresh_code)
        right_tabs.addTab(self.irq_panel, "🔔 IRQ")

        rv.addWidget(right_tabs, stretch=1)

        right.setMinimumWidth(480)
        right.setMaximumWidth(700)

        root.addWidget(left, stretch=2)
        root.addWidget(sep)
        root.addWidget(right, stretch=1)

        # fullscreen is handled in main.py via showMaximized()

    # ── Menu bar ──────────────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = self.menuBar()

        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_statusbar(self):
        sb = self.statusBar()
        sb.setFont(QFont("Segoe UI", 8))
        sb.showMessage(f"{APP_NAME}  v{APP_VERSION}  |  © {APP_AUTHOR}  —  Veleučilište u Bjelovaru")

    def _show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"About  {APP_NAME}")
        dlg.setMinimumWidth(400)

        vbox = QVBoxLayout(dlg)
        vbox.setSpacing(12)
        vbox.setContentsMargins(24, 20, 24, 16)

        # Logo
        if os.path.exists(_LOGO_SVG):
            logo_lbl = QLabel()
            logo_lbl.setPixmap(_svg_pixmap(_LOGO_SVG, 90))
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            vbox.addWidget(logo_lbl)

        # Naziv aplikacije
        title_lbl = QLabel(APP_NAME)
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title_lbl)

        # Info tekst
        info_lbl = QLabel(
            f"<p style='text-align:center;'>"
            f"Verzija {APP_VERSION}<br><br>"
            f"AVR konfigurator za mikrokontroler ATmega32U4.<br>"
            f"Generira Atmel Studio / AVR-GCC kompatibilan<br>"
            f"<code>init()</code> kod za GPIO, tajmere i prekide."
            f"</p>"
            f"<p style='text-align:center;'>"
            f"<b>Autor:</b> {APP_AUTHOR}<br>"
            f"<b>Ustanova:</b> Veleučilište u Bjelovaru"
            f"</p>"
        )
        info_lbl.setFont(QFont("Segoe UI", 9))
        info_lbl.setWordWrap(True)
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(info_lbl)

        # OK button
        btn = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn.accepted.connect(dlg.accept)
        vbox.addWidget(btn)

        dlg.exec()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_pin_selected(self, pin_num: int):
        self.pin_panel.show_pin(PIN_MAP[pin_num])

    def _on_pin_config_changed(self, pin_num: int, mode: GpioMode):
        self.pin_configs[pin_num].mode = mode
        self.chip.update()
        self._refresh_code()

    def _on_fcpu_changed(self, idx: int):
        self._f_cpu = self.F_CPU_OPTIONS[idx][0]
        self._f_cpu_idx = idx
        # Propagate to all panels
        self.timer_panel.set_f_cpu(self._f_cpu)
        self.adc_panel.set_f_cpu(self._f_cpu)
        self.uart_panel.set_f_cpu(self._f_cpu)
        self.spi_panel.set_f_cpu(self._f_cpu)
        self.twi_panel.set_f_cpu(self._f_cpu)
        self._refresh_code()

    def _refresh_code(self):
        code = generate_code(self.pin_configs, self.timer_configs,
                             self.irq_config, self.adc_config,
                             self.uart_config, self.spi_config,
                             self.twi_config, self._f_cpu)
        self.code_edit.setPlainText(code)

    def _copy_code(self):
        QApplication.clipboard().setText(self.code_edit.toPlainText())
        orig = self.btn_copy.text()
        self.btn_copy.setText("Copied!")
        QTimer.singleShot(1500, lambda: self.btn_copy.setText(orig))
