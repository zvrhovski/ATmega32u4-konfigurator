import os
from PyQt6.QtWidgets import QWidget, QToolTip
from PyQt6.QtCore    import Qt, QRect, QRectF, QPoint, pyqtSignal, QSize
from PyQt6.QtGui     import QPainter, QColor, QPen, QFont, QBrush, QFontMetrics
from PyQt6.QtSvg     import QSvgRenderer

from pins import ALL_PINS, PinDef, PinType, GpioMode, PinConfig

_HERE     = os.path.dirname(os.path.abspath(__file__))
_LOGO_SVG = os.path.join(_HERE, "vub_logo.svg")
_logo_renderer: QSvgRenderer | None = None

def _get_logo() -> QSvgRenderer | None:
    global _logo_renderer
    if _logo_renderer is None and os.path.exists(_LOGO_SVG):
        _logo_renderer = QSvgRenderer(_LOGO_SVG)
    return _logo_renderer

# ── Colour palette ────────────────────────────────────────────────────────────
TYPE_COLORS: dict[PinType, QColor] = {
    PinType.GPIO:  QColor("#4A90D9"),
    PinType.POWER: QColor("#888888"),
    PinType.USB:   QColor("#9B59B6"),
    PinType.CLOCK: QColor("#E67E22"),
    PinType.RESET: QColor("#E74C3C"),
    PinType.REF:   QColor("#1ABC9C"),
}

MODE_COLORS: dict[GpioMode, QColor] = {
    GpioMode.UNCONFIGURED: QColor("#4A90D9"),
    GpioMode.INPUT:        QColor("#27AE60"),
    GpioMode.INPUT_PULLUP: QColor("#2ECC71"),
    GpioMode.OUTPUT_LOW:   QColor("#C0392B"),
    GpioMode.OUTPUT_HIGH:  QColor("#E74C3C"),
}

CHIP_BODY   = QColor("#2C3E50")
CHIP_BORDER = QColor("#1A252F")
CHIP_TEXT   = QColor("#ECF0F1")
SEL_COLOR   = QColor("#F1C40F")
HOV_LIGHTEN = 140   # % for lighter()

PIN_LEN = 29   # stub length (px)  — 20% smaller
PIN_W   = 9    # stub width  (px)
N       = 11   # pins per side
MARGIN  = 100  # px reserved outside chip for stubs + labels


class ChipWidget(QWidget):
    pin_selected = pyqtSignal(int)   # emits pin number

    def __init__(self, pin_configs: dict[int, PinConfig], parent=None):
        super().__init__(parent)
        self.pin_configs  = pin_configs
        self.selected_pin: int | None = None
        self.hovered_pin:  int | None = None
        self._pin_rects:   dict[int, QRect] = {}   # hit-test rects

        self.setMinimumSize(280, 220)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

    # ── Geometry helpers ──────────────────────────────────────────────────────

    def _chip_rect(self) -> tuple[int, int, int, int]:
        """Return (cx, cy, cw, ch) — chip body top-left and size."""
        w, h = self.width(), self.height()
        side = min(w, h) - 2 * MARGIN
        cx = (w - side) // 2
        cy = (h - side) // 2
        return cx, cy, side, side

    def _stub_rect(self, pin: PinDef,
                   cx: int, cy: int, cw: int, ch: int) -> QRect:
        """Return the QRect of this pin's stub line."""
        idx = pin.side_index
        if pin.side == 'left':
            y = cy + int((idx + 0.5) * ch / N)
            return QRect(cx - PIN_LEN, y - PIN_W // 2, PIN_LEN, PIN_W)
        if pin.side == 'bottom':
            x = cx + int((idx + 0.5) * cw / N)
            return QRect(x - PIN_W // 2, cy + ch, PIN_W, PIN_LEN)
        if pin.side == 'right':
            # side_index 0 = physical bottom (pin 23), 10 = physical top (pin 33)
            y = cy + ch - int((idx + 0.5) * ch / N)
            return QRect(cx + cw, y - PIN_W // 2, PIN_LEN, PIN_W)
        # top: side_index 0 = physical right (pin 34), 10 = physical left (pin 44)
        x = cx + cw - int((idx + 0.5) * cw / N)
        return QRect(x - PIN_W // 2, cy - PIN_LEN, PIN_W, PIN_LEN)

    # ── Paint ─────────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy, cw, ch = self._chip_rect()
        self._pin_rects.clear()

        # Chip body
        painter.setPen(QPen(CHIP_BORDER, 2))
        painter.setBrush(QBrush(CHIP_BODY))
        painter.drawRect(cx, cy, cw, ch)

        # Chip label + VUB logo
        font = QFont("Consolas", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(CHIP_TEXT)

        logo     = _get_logo()
        LOGO_H   = min(78, ch * 26 // 100)   # logo height: ~30 % larger than original min(60, ch//5)
        GAP      = 8                   # gap between text and logo
        fm       = QFontMetrics(font)
        text_h   = fm.height()
        block_h  = text_h + GAP + LOGO_H
        text_y   = cy + (ch - block_h) // 2

        # Draw "ATmega32U4" centred horizontally, at text_y
        painter.drawText(QRect(cx, text_y, cw, text_h),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                         "ATmega32U4")

        # Draw VUB logo below the text, centred
        if logo and logo.isValid():
            default = logo.defaultSize()
            logo_w  = int(default.width() * LOGO_H / default.height())
            logo_x  = cx + (cw - logo_w) // 2
            logo_y  = text_y + text_h + GAP
            painter.setOpacity(0.85)
            logo.render(painter, QRectF(logo_x, logo_y, logo_w, LOGO_H))
            painter.setOpacity(1.0)

        # Pins
        for pin in ALL_PINS:
            self._draw_pin(painter, pin, cx, cy, cw, ch)

        painter.end()

    def _pin_color(self, pin: PinDef) -> QColor:
        if pin.pin_type == PinType.GPIO:
            cfg = self.pin_configs.get(pin.number)
            mode = cfg.mode if cfg else GpioMode.UNCONFIGURED
            return MODE_COLORS[mode]
        return TYPE_COLORS[pin.pin_type]

    def _draw_pin(self, painter: QPainter, pin: PinDef,
                  cx: int, cy: int, cw: int, ch: int):
        stub = self._stub_rect(pin, cx, cy, cw, ch)
        hit  = stub.adjusted(-4, -4, 4, 4)
        self._pin_rects[pin.number] = hit

        color     = self._pin_color(pin)
        selected  = pin.number == self.selected_pin
        hovered   = pin.number == self.hovered_pin

        if selected:
            pen_color  = SEL_COLOR
            fill_color = SEL_COLOR
        elif hovered:
            pen_color  = color.lighter(HOV_LIGHTEN)
            fill_color = color.lighter(HOV_LIGHTEN)
        else:
            pen_color  = color.darker(130)
            fill_color = color

        painter.setPen(QPen(pen_color, 1))
        painter.setBrush(QBrush(fill_color))
        painter.drawRect(stub)

        self._draw_label(painter, pin, stub)

    def _draw_label(self, painter: QPainter, pin: PinDef, stub: QRect):
        font = QFont("Consolas", 9)
        painter.setFont(font)
        painter.setPen(QColor("#FFFFFF"))

        label = f"{pin.number}:{pin.name}"
        fm    = QFontMetrics(font)
        lw    = fm.horizontalAdvance(label)
        lh    = fm.height()
        GAP   = 4

        if pin.side == 'left':
            x = stub.left() - lw - GAP
            y = stub.center().y() - lh // 2
            painter.drawText(x, y, lw, lh,
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             label)

        elif pin.side == 'right':
            x = stub.right() + GAP
            y = stub.center().y() - lh // 2
            painter.drawText(x, y, lw, lh,
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             label)

        elif pin.side == 'bottom':
            painter.save()
            painter.translate(stub.center().x(), stub.bottom() + GAP)
            painter.rotate(90)
            painter.drawText(0, -lh // 2, lw, lh,
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             label)
            painter.restore()

        else:  # top
            # After rotate(-90°) in Qt, +x points UPWARD on screen.
            # Draw at positive x so text goes away from the chip (upward).
            painter.save()
            painter.translate(stub.center().x(), stub.top() - GAP)
            painter.rotate(-90)
            painter.drawText(2, -lh // 2, lw, lh,
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             label)
            painter.restore()

    # ── Mouse events ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pin_num = self._pin_at(event.position().toPoint())
            if pin_num is not None:
                self.selected_pin = pin_num
                self.pin_selected.emit(pin_num)
                self.update()

    def mouseMoveEvent(self, event):
        pin_num = self._pin_at(event.position().toPoint())
        if pin_num != self.hovered_pin:
            self.hovered_pin = pin_num
            self.update()
            if pin_num is not None:
                pin = ALL_PINS[pin_num - 1]
                alts = ", ".join(pin.alt_functions) if pin.alt_functions else "—"
                QToolTip.showText(
                    event.globalPosition().toPoint(),
                    f"<div style='background:#2C3E50; color:#F0C040; padding:6px; "
                    f"font-family:Consolas; font-size:10pt;'>"
                    f"<b style='color:#ECF0F1;'>Pin {pin.number}: {pin.name}</b><br>"
                    f"<b>Alt:</b> {alts}</div>",
                    self
                )
            else:
                QToolTip.hideText()

    def _pin_at(self, pos: QPoint) -> int | None:
        for num, rect in self._pin_rects.items():
            if rect.contains(pos):
                return num
        return None
