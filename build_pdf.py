"""Generate PDF documentation for ATmega32U4 Configurator."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

OUT = os.path.join(os.path.dirname(__file__),
                   "ATmega32U4_Configurator_Upute.pdf")

# ── Register Windows fonts (support Croatian characters) ─────────────────────
WINFONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")

pdfmetrics.registerFont(TTFont("Calibri",      os.path.join(WINFONTS, "calibri.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Bold",  os.path.join(WINFONTS, "calibrib.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Italic", os.path.join(WINFONTS, "calibrii.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-BoldItalic", os.path.join(WINFONTS, "calibriz.ttf")))
pdfmetrics.registerFont(TTFont("Consolas",      os.path.join(WINFONTS, "consola.ttf")))
pdfmetrics.registerFont(TTFont("Consolas-Bold", os.path.join(WINFONTS, "consolab.ttf")))

from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily("Calibri",
                   normal="Calibri", bold="Calibri-Bold",
                   italic="Calibri-Italic", boldItalic="Calibri-BoldItalic")

FONT_BODY = "Calibri"
FONT_CODE = "Consolas"

# ── Colours ───────────────────────────────────────────────────────────────────
DARK   = HexColor("#1A252F")
ACCENT = HexColor("#2980B9")
LIGHT  = HexColor("#ECF0F1")
CODE_BG = HexColor("#F4F4F4")
TBL_HEAD = HexColor("#2C3E50")

# ── Styles ────────────────────────────────────────────────────────────────────
styles = getSampleStyleSheet()

sTitle = ParagraphStyle("DocTitle", parent=styles["Title"],
                        fontName=FONT_BODY, fontSize=22, leading=28,
                        textColor=DARK, spaceAfter=6, alignment=TA_CENTER)

sSubtitle = ParagraphStyle("Subtitle", parent=styles["Normal"],
                           fontName=FONT_BODY, fontSize=11, leading=14,
                           textColor=HexColor("#555"),
                           alignment=TA_CENTER, spaceAfter=20)

sH1 = ParagraphStyle("H1", parent=styles["Heading1"],
                      fontName="Calibri-Bold", fontSize=16, leading=20,
                      textColor=ACCENT, spaceBefore=18, spaceAfter=8,
                      borderWidth=0, borderPadding=0)

sH2 = ParagraphStyle("H2", parent=styles["Heading2"],
                      fontName="Calibri-Bold", fontSize=13, leading=16,
                      textColor=DARK, spaceBefore=12, spaceAfter=6)

sH3 = ParagraphStyle("H3", parent=styles["Heading3"],
                      fontName="Calibri-Bold", fontSize=11, leading=14,
                      textColor=DARK, spaceBefore=8, spaceAfter=4)

sBody = ParagraphStyle("Body", parent=styles["Normal"],
                       fontName=FONT_BODY, fontSize=10, leading=14,
                       alignment=TA_JUSTIFY, spaceAfter=6)

sBullet = ParagraphStyle("Bullet", parent=sBody,
                         bulletIndent=10, leftIndent=22,
                         spaceAfter=3)

sCode = ParagraphStyle("Code", parent=styles["Code"],
                       fontName=FONT_CODE, fontSize=8.5, leading=11,
                       backColor=CODE_BG,
                       borderWidth=0.5, borderColor=HexColor("#DDD"),
                       borderPadding=6, leftIndent=12,
                       spaceAfter=8, spaceBefore=4)

sNote = ParagraphStyle("Note", parent=sBody,
                       fontSize=9.5, leading=13,
                       textColor=HexColor("#666"), leftIndent=12)


def hr():
    return HRFlowable(width="100%", thickness=0.5, color=HexColor("#CCC"),
                      spaceBefore=6, spaceAfter=6)

def sp(h=6):
    return Spacer(1, h)

def tbl(data, col_widths=None):
    """Create a styled table."""
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TBL_HEAD),
        ("TEXTCOLOR",  (0, 0), (-1, 0), white),
        ("FONTNAME",   (0, 0), (-1, 0), "Calibri-Bold"),
        ("FONTNAME",   (0, 1), (-1, -1), FONT_BODY),
        ("FONTSIZE",   (0, 0), (-1, 0), 9),
        ("FONTSIZE",   (0, 1), (-1, -1), 9),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",       (0, 0), (-1, -1), 0.4, HexColor("#CCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F9F9F9")]),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t

def code(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(text.replace("\n", "<br/>"), sCode)


# ── Content ───────────────────────────────────────────────────────────────────

def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="ATmega32U4 Configurator — Upute za korištenje",
        author="Zoran Vrhovski",
    )

    story = []

    # ── Title page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 60))
    story.append(Paragraph("ATmega32U4 Configurator", sTitle))
    story.append(Paragraph("Upute za korištenje", ParagraphStyle(
        "Sub2", parent=sTitle, fontSize=16, textColor=HexColor("#555"))))
    story.append(sp(12))
    story.append(Paragraph("Verzija 1.0", sSubtitle))
    story.append(sp(30))
    story.append(Paragraph(
        "Autor aplikacije: <b>Zoran Vrhovski</b><br/>"
        "Veleu\u010dili\u0161te u Bjelovaru", sSubtitle))
    story.append(sp(12))
    story.append(Paragraph(
        "<i>Upute napisao Claude Code uz nadzor Zorana Vrhovskog</i>", sSubtitle))
    story.append(PageBreak())

    # ── 1. Pokretanje ─────────────────────────────────────────────────────────
    story.append(Paragraph("1. Pokretanje aplikacije", sH1))
    story.append(Paragraph("<b>Iz izvornog koda:</b>", sBody))
    story.append(code("pip install PyQt6\ncd ATmega32U4_Configurator\npython main.py"))
    story.append(Paragraph(
        "<b>Iz .exe datoteke:</b> Preuzmi <font color='#2980B9'>ATmega32U4_Configurator.exe</font> "
        "s GitHub Releases stranice i pokreni. Ne treba instalacija.", sBody))
    story.append(Paragraph("Aplikacija se otvara u fullscreen modu.", sNote))

    # ── 2. Raspored sučelja ───────────────────────────────────────────────────
    story.append(Paragraph("2. Raspored su\u010delja", sH1))
    story.append(tbl([
        ["Dio", "Sadr\u017eaj"],
        ["Lijevo (2/3)", "F_CPU odabir, generirani C kod, Copy to clipboard"],
        ["Desno (1/3)", "Tabovi: Pin, Timers, ADC, UART, SPI, I2C, IRQ"],
    ], col_widths=[120, 350]))
    story.append(sp())
    story.append(Paragraph(
        "Na <b>Pin</b> tabu se dodatno nalazi vizualni prikaz TQFP-44 chipa "
        "s klikabilnim pinovima.", sBody))

    # ── 3. F_CPU ──────────────────────────────────────────────────────────────
    story.append(Paragraph("3. F_CPU \u2014 odabir frekvencije takta", sH1))
    story.append(Paragraph(
        "Na vrhu lijevog dijela nalazi se padaju\u0107i izbornik F_CPU. "
        "Promjena automatski prera\u010dunava UBRR (UART), TWBR (I2C), "
        "timer frekvencije i ADC clock.", sBody))
    story.append(tbl([
        ["Frekvencija", "Napomena"],
        ["1 MHz", "Internal RC oscilator"],
        ["7.3728 / 11.0592 / 14.7456 / 18.432 MHz", "UART-optimizirane (0% gre\u0161ka)"],
        ["8 / 12 / 16 (default) / 20 MHz", "Standardne frekvencije"],
    ], col_widths=[220, 250]))

    # ── 4. Pin ────────────────────────────────────────────────────────────────
    story.append(Paragraph("4. Tab: Pin (GPIO konfiguracija)", sH1))

    story.append(Paragraph("Vizualni chip", sH2))
    story.append(Paragraph(
        "U donjem dijelu Pin taba prikazan je ATmega32U4 u TQFP-44 ku\u0107i\u0161tu. "
        "Pinovi su obojani prema tipu:", sBody))
    story.append(tbl([
        ["Boja", "Tip"],
        ["Plava", "GPIO (konfigurabilni)"],
        ["Siva", "Napajanje (VCC, GND, AVCC)"],
        ["Ljubi\u010dasta", "USB (D+, D-, UCAP, VBUS)"],
        ["Naran\u010dasta", "XTAL (kristal)"],
        ["Crvena", "RESET"],
        ["Zelena", "AREF"],
    ], col_widths=[100, 370]))

    story.append(Paragraph("GPIO modovi", sH2))
    story.append(tbl([
        ["Mod", "DDR", "PORT", "Opis"],
        ["Unconfigured", "\u2014", "\u2014", "Ne generira kod"],
        ["Input", "0", "0", "Ulaz bez pull-up"],
        ["Input + Pull-up", "0", "1", "Ulaz s pull-up otpornikom"],
        ["Output LOW", "1", "0", "Izlaz, po\u010detno stanje LOW"],
        ["Output HIGH", "1", "1", "Izlaz, po\u010detno stanje HIGH"],
    ], col_widths=[110, 40, 45, 275]))

    story.append(Paragraph("Tooltip", sH2))
    story.append(Paragraph(
        "Prelaskom mi\u0161a preko pina prikazuje se tooltip s brojem pina, "
        "nazivom i alternativnim funkcijama.", sBody))

    # ── 5. Timers ─────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("5. Tab: Timers", sH1))
    story.append(Paragraph(
        "ATmega32U4 ima 4 timera:", sBody))
    story.append(tbl([
        ["Timer", "Rezolucija", "Napomena"],
        ["T0", "8-bit", ""],
        ["T1", "16-bit", ""],
        ["T3", "16-bit", ""],
        ["T4", "10-bit", "High Speed, PLL podr\u0161ka"],
    ], col_widths=[60, 90, 320]))

    story.append(Paragraph("Osnovna konfiguracija", sH2))
    story.append(Paragraph(
        "1. Ozna\u010di <b>Enable Timer X</b><br/>"
        "2. Odaberi <b>Mode</b>: Normal, CTC, Fast PWM, Phase Correct...<br/>"
        "3. Odaberi <b>Prescaler</b>: clk/1, clk/8, clk/64... ili Ext T0/T1 za broja\u010dki mod<br/>"
        "4. Postavi <b>TOP</b> vrijednost (ako mod dopu\u0161ta)", sBody))

    story.append(Paragraph("Normal mod", sH2))
    story.append(Paragraph(
        "Prikazuje <b>Overflow / TCNT Preload</b> grupu sa sliderom i spinboxom "
        "za pode\u0161avanje TCNT preload vrijednosti. "
        "Checkbox <b>Enable overflow interrupt (TOIE)</b> generira TIMSK registar i ISR stub.", sBody))

    story.append(Paragraph("CTC mod", sH2))
    story.append(Paragraph(
        "Prikazuje <b>Frequency</b> (compare match) i <b>OC Toggle</b> (pravokutni val na OC pinu). "
        "Compare match interrupt se okida svaki put kad TCNT dostigne TOP \u2014 "
        "OC toggle je upola sporiji jer treba 2 matcha za puni period.<br/>"
        "Checkbox <b>Enable Compare Match Interrupt (OCIE)</b> generira ISR stub.", sBody))

    story.append(Paragraph("PWM modovi", sH2))
    story.append(Paragraph(
        "OC kanali prikazuju: Output mode (Non-inverted/Inverted PWM), OCR vrijednost i Duty %. "
        "Automatski se generira DDR za OC pin kao output.", sBody))

    story.append(Paragraph("Timer 4 \u2014 PLL", sH2))
    story.append(Paragraph(
        "Timer 4 ima dodatnu <b>PLL Clock</b> grupu. PLL generira 96 MHz "
        "(8 MHz \u00d7 12) iz kojeg Timer 4 mo\u017ee koristiti:", sBody))
    story.append(tbl([
        ["PLLTM", "Timer 4 clock"],
        ["PLL / 1", "96 MHz"],
        ["PLL / 1.5", "64 MHz"],
        ["PLL / 2", "48 MHz"],
    ], col_widths=[100, 370]))
    story.append(Paragraph(
        "Generirani kod uklju\u010duje PLLCSR, PLLFRQ registre, "
        "PLLUSB bit (48 MHz za USB) i \u010dekanje PLL locka.", sNote))

    story.append(Paragraph("Broja\u010dki mod (Ext T0/T1)", sH2))
    story.append(Paragraph(
        "Kad se odabere prescaler \"Ext T0\" ili \"Ext T1\", automatski se generira "
        "DDR za T0 (PD7, pin 26) ili T1 (PD6, pin 25) pin kao input.", sBody))

    # ── 6. ADC ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. Tab: ADC", sH1))

    story.append(Paragraph("Opće postavke", sH2))
    story.append(Paragraph(
        "1. Ozna\u010di <b>Enable ADC (ADEN)</b><br/>"
        "2. Odaberi <b>Referentni napon</b>: AREF, AVCC (default), Internal 2.56V<br/>"
        "3. Odaberi <b>Prescaler</b>: /2 do /128 (preporu\u010deno /128 za 125 kHz ADC clock)", sBody))

    story.append(Paragraph("Odabir kanala", sH2))
    story.append(Paragraph(
        "<b>Single-ended:</b> ADC0\u2013ADC13 (svaki s checkboxom), 1.1V Bandgap, GND<br/>"
        "<b>Diferencijalni:</b> parovi s poja\u010danjem 1\u00d7, 10\u00d7 ili 200\u00d7", sBody))

    story.append(Paragraph("Generirani kod", sH2))
    story.append(Paragraph(
        "<b>1 kanal:</b> ADMUX se postavlja direktno u init()<br/>"
        "<b>Vi\u0161e kanala:</b> init() postavlja samo referencu, generirane su helper funkcije:", sBody))
    story.append(code(
        "// Primjer korištenja:\n"
        "adc_select_adc4();\n"
        "uint16_t val = adc_read();"))
    story.append(Paragraph(
        "<b>adc_read()</b> \u2014 pokre\u0107e konverziju i vra\u0107a 10-bit rezultat<br/>"
        "<b>adc_select_adcX()</b> \u2014 prebacivanje kanala", sBody))

    # ── 7. UART ───────────────────────────────────────────────────────────────
    story.append(Paragraph("7. Tab: UART", sH1))
    story.append(Paragraph(
        "1. Ozna\u010di <b>Enable USART1</b><br/>"
        "2. Odaberi <b>Baud rate</b> (2400\u2013115200)<br/>"
        "3. Opcionalno uklju\u010di <b>U2X (double speed)</b> za bolju preciznost", sBody))

    story.append(Paragraph("Format okvira", sH2))
    story.append(tbl([
        ["Parametar", "Opcije"],
        ["Data bits", "5, 6, 7, 8, 9"],
        ["Paritet", "None, Even, Odd"],
        ["Stop bits", "1, 2"],
    ], col_widths=[120, 350]))

    story.append(Paragraph("TX / RX pinovi", sH2))
    story.append(Paragraph(
        "<b>TX Enable (TXEN1)</b> \u2014 TXD1 = PD3, pin 20<br/>"
        "<b>RX Enable (RXEN1)</b> \u2014 RXD1 = PD2, pin 19", sBody))

    story.append(Paragraph("Prekidi", sH2))
    story.append(tbl([
        ["Prekid", "ISR vektor", "Komentar"],
        ["RX Complete (RXCIE1)", "USART1_RX_vect", "uint8_t data = UDR1;"],
        ["TX Complete (TXCIE1)", "USART1_TX_vect", ""],
        ["Data Reg Empty (UDRIE1)", "USART1_UDRE_vect", ""],
    ], col_widths=[150, 140, 180]))

    # ── 8. SPI ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("8. Tab: SPI", sH1))
    story.append(Paragraph(
        "Podr\u017eava <b>Master</b> i <b>Slave</b> mod.", sBody))

    story.append(Paragraph("SPI Mode (CPOL/CPHA)", sH2))
    story.append(tbl([
        ["Mode", "CPOL", "CPHA", "Opis"],
        ["0", "0", "0", "Clock idle LOW, sample rising"],
        ["1", "0", "1", "Clock idle LOW, sample falling"],
        ["2", "1", "0", "Clock idle HIGH, sample falling"],
        ["3", "1", "1", "Clock idle HIGH, sample rising"],
    ], col_widths=[50, 50, 50, 320]))

    story.append(Paragraph("Prescaler (samo Master)", sH2))
    story.append(Paragraph(
        "/2, /4, /8, /16, /32, /64, /128 \u2014 prikazuje SPI clock frekvenciju.", sBody))

    story.append(Paragraph("Pin konfiguracija (automatska)", sH2))
    story.append(tbl([
        ["Pin", "Master", "Slave"],
        ["PB0 (SS)", "Output", "Input"],
        ["PB1 (SCK)", "Output", "Input"],
        ["PB2 (MOSI)", "Output", "Input"],
        ["PB3 (MISO)", "Input", "Output"],
    ], col_widths=[120, 175, 175]))

    # ── 9. I2C ────────────────────────────────────────────────────────────────
    story.append(Paragraph("9. Tab: I2C (TWI)", sH1))

    story.append(Paragraph("Master postavke", sH2))
    story.append(Paragraph(
        "<b>SCL brzina:</b> 100 kHz (Standard) ili 400 kHz (Fast)<br/>"
        "<b>Prescaler:</b> 1, 4, 16, 64<br/>"
        "Prikazuje TWBR vrijednost, stvarnu SCL frekvenciju i gre\u0161ku. "
        "Upozorenje ako TWBR &gt; 255.", sBody))

    story.append(Paragraph("Slave postavke", sH2))
    story.append(Paragraph(
        "<b>Adresa (7-bit):</b> 0x01\u20130x7F<br/>"
        "<b>General Call Enable (TWGCE)</b> \u2014 odgovara i na adresu 0x00", sBody))

    story.append(Paragraph("Pinovi", sH2))
    story.append(Paragraph(
        "SCL = PD0 (pin 17), SDA = PD1 (pin 18)", sBody))

    # ── 10. IRQ ───────────────────────────────────────────────────────────────
    story.append(Paragraph("10. Tab: IRQ (Vanjski prekidi)", sH1))

    story.append(Paragraph("Vanjski prekidi (INT0\u2013INT6)", sH2))
    story.append(tbl([
        ["Prekid", "Pin", "Fizi\u010dki pin"],
        ["INT0", "PD0", "17"],
        ["INT1", "PD1", "18"],
        ["INT2", "PD2", "19"],
        ["INT3", "PD3", "20"],
        ["INT6", "PE6", "1"],
    ], col_widths=[80, 80, 310]))
    story.append(Paragraph(
        "Za svaki prekid: Enable checkbox + Sense (Low level, Any change, "
        "Falling edge, Rising edge).", sBody))

    story.append(Paragraph("Pin Change Interrupts (PCINT0\u20137)", sH2))
    story.append(Paragraph(
        "PCIE0 master checkbox (Port B grupa) + individualni checkboxovi "
        "PCINT0 (PB0) do PCINT7 (PB7).", sBody))

    story.append(Paragraph("sei() \u2014 automatsko generiranje", sH2))
    story.append(Paragraph(
        "<font color='#C0392B'><b>Va\u017eno:</b></font> "
        "<b>sei()</b> se automatski generira kad je bilo koji prekid aktivan "
        "(timer, UART, SPI, TWI, INTx, PCINT). "
        "Mo\u017ee se i ru\u010dno uklju\u010diti checkboxom.", sBody))

    # ── 11. Generirani kod ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("11. Generirani kod", sH1))

    story.append(Paragraph("Struktura", sH2))
    story.append(code(
        "#define F_CPU 16000000UL\n"
        "#include &lt;avr/io.h&gt;\n"
        "#include &lt;avr/interrupt.h&gt;\n"
        "\n"
        "void init(void)\n"
        "{\n"
        "    /* GPIO */\n"
        "    /* Timeri */\n"
        "    /* ADC */\n"
        "    /* USART1 */\n"
        "    /* SPI */\n"
        "    /* TWI (I2C) */\n"
        "    /* Interrupts */\n"
        "    sei();\n"
        "}\n"
        "\n"
        "ISR(vector) { ... }\n"
        "uint16_t adc_read(void) { ... }\n"
        "void adc_select_adcX(void) { ... }"))

    story.append(Paragraph("Redoslijed sekcija", sH2))
    story.append(Paragraph(
        "GPIO &rarr; Timeri &rarr; ADC &rarr; UART &rarr; SPI &rarr; I2C &rarr; "
        "Prekidi &rarr; sei() &rarr; ISR stubovi &rarr; ADC helperi", sBody))

    story.append(Paragraph("Copy to clipboard", sH2))
    story.append(Paragraph(
        "Gumb <b>Copy to clipboard</b> u donjem desnom kutu kopira cijeli generirani kod.", sBody))

    # ── 12. Savjeti ───────────────────────────────────────────────────────────
    story.append(Paragraph("12. Savjeti", sH1))
    tips = [
        "Zapo\u010dni s odabirom <b>F_CPU</b> \u2014 sve ostalo ovisi o njemu.",
        "Za UART bez gre\u0161ke koristi frekvencije ozna\u010dene s \"(UART)\": "
        "7.3728, 11.0592, 14.7456 MHz.",
        "ADC prescaler /128 daje 125 kHz ADC clock pri 16 MHz \u2014 "
        "idealno za 10-bit preciznost.",
        "Timer 4 s PLL-om na 96 MHz daje PWM frekvencije do 375 kHz.",
        "SPI Slave mod automatski postavlja MISO kao output, ostale pinove kao input.",
        "ISR stubovi se automatski generiraju \u2014 samo dodaj svoju logiku unutar { }.",
        "Za broja\u010dki mod timera odaberi \"Ext T0\" ili \"Ext T1\" kao prescaler.",
    ]
    for tip in tips:
        story.append(Paragraph(f"\u2022 {tip}", sBullet))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(sp(30))
    story.append(hr())
    story.append(Paragraph(
        "<i>ATmega32U4 Configurator v1.0</i><br/>"
        "<i>Autor: Zoran Vrhovski, Veleu\u010dili\u0161te u Bjelovaru</i><br/>"
        "<i>Upute napisao Claude Code uz nadzor Zorana Vrhovskog</i>",
        ParagraphStyle("Footer", parent=sBody, alignment=TA_CENTER,
                       fontSize=9, textColor=HexColor("#999"))))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"PDF saved: {OUT}")


if __name__ == "__main__":
    build()
