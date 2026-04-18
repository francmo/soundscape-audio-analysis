"""Genera una scheda di annotazione PDF editabile (AcroForm) per l'utente.

La scheda e' il gold standard first-hand: il compositore ascolta una propria
registrazione soundscape e compila i campi, producendo un'annotazione che
diventa poi `references/user_feedback/<brano>.md` per validare la skill.

Uso:
    python -m scripts.generate_annotation_sheet [output.pdf]

Output: PDF A4 di 4 pagine (metadati+timeline, tassonomie, drammaturgia,
glossario referenziale). I campi editabili si compilano su Preview.app
oppure su iPad con Apple Pencil/Scribble.

Tipografia: sfondo bianco puro, testo nero, font Unicode (Libre Baskerville
+ Source Sans Pro gia' registrati nella skill). Nessun em dash, accenti
italiani corretti.
"""
from __future__ import annotations

import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"


def _register_fonts() -> tuple[str, str]:
    """Registra i font OFL della skill. Ritorna (serif_name, sans_name)."""
    serif = "LibreBaskerville"
    sans = "SourceSansPro"
    try:
        pdfmetrics.registerFont(
            TTFont(serif, str(FONT_DIR / "LibreBaskerville-Regular.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont(f"{serif}-Bold",
                   str(FONT_DIR / "LibreBaskerville-Bold.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont(sans, str(FONT_DIR / "SourceSansPro-Regular.ttf"))
        )
        pdfmetrics.registerFont(
            TTFont(f"{sans}-Bold",
                   str(FONT_DIR / "SourceSansPro-Semibold.ttf"))
        )
    except Exception:
        # Fallback su Helvetica se i font non sono disponibili
        return ("Helvetica", "Helvetica")
    return (serif, sans)


PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
BLACK = (0, 0, 0)
GRAY = (0.35, 0.35, 0.35)
LIGHT = (0.92, 0.92, 0.92)

# Color objects for acroForm (che non accetta tuple)
FIELD_BORDER = Color(0.7, 0.7, 0.7)
FIELD_BORDER_LIGHT = Color(0.8, 0.8, 0.8)
FIELD_BORDER_DARK = Color(0.4, 0.4, 0.4)
FIELD_FILL = Color(1, 1, 1)


class SheetBuilder:
    def __init__(self, output_path: Path):
        self.c = canvas.Canvas(str(output_path), pagesize=A4)
        self.serif, self.sans = _register_fonts()
        self.c.setTitle("Scheda annotazione soundscape")
        self.c.setAuthor("Soundscape Audio Analysis")
        self.c.setSubject("Gold standard first-hand per validazione skill")
        self.y = PAGE_H - MARGIN
        self._field_counter = 0

    def _next_field_name(self, prefix: str) -> str:
        self._field_counter += 1
        return f"{prefix}_{self._field_counter}"

    # --- primitive ---

    def title(self, text: str, size: int = 18) -> None:
        self.c.setFont(f"{self.serif}-Bold", size)
        self.c.setFillColorRGB(*BLACK)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= size + 6

    def subtitle(self, text: str, size: int = 11) -> None:
        self.c.setFont(self.sans, size)
        self.c.setFillColorRGB(*GRAY)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= size + 10

    def h2(self, text: str, size: int = 13) -> None:
        self.y -= 8
        self.c.setFont(f"{self.serif}-Bold", size)
        self.c.setFillColorRGB(*BLACK)
        self.c.drawString(MARGIN, self.y, text)
        self.y -= size + 5

    def paragraph(self, text: str, size: int = 9,
                  font: str | None = None) -> None:
        font = font or self.sans
        self.c.setFont(font, size)
        self.c.setFillColorRGB(*BLACK)
        for line in text.split("\n"):
            self.c.drawString(MARGIN, self.y, line)
            self.y -= size + 3
        self.y -= 2

    def hint(self, text: str, size: int = 8) -> None:
        """Hint grigio piccolo. Supporta \\n per righe multiple."""
        self.c.setFont(self.sans, size)
        self.c.setFillColorRGB(*GRAY)
        for line in text.split("\n"):
            self.c.drawString(MARGIN, self.y, line)
            self.y -= size + 2
        self.c.setFillColorRGB(*BLACK)
        self.y -= 2

    def label_and_field(self, label: str, field_name: str,
                        field_w_mm: float = 90, field_h_mm: float = 7,
                        size: int = 9) -> None:
        """Etichetta a sinistra, campo testo editabile a destra su stessa riga."""
        self.c.setFont(self.sans, size)
        self.c.setFillColorRGB(*BLACK)
        self.c.drawString(MARGIN, self.y, label)
        # Label ha larghezza fissa di 55mm; campo segue dopo
        self.c.acroForm.textfield(
            name=field_name,
            x=MARGIN + 55 * mm,
            y=self.y - 2,
            width=field_w_mm * mm,
            height=field_h_mm * mm,
            borderColor=FIELD_BORDER,
            fillColor=FIELD_FILL,
            textColor=black,
            fontName="Helvetica",
            fontSize=size,
            borderWidth=0.5,
        )
        self.y -= field_h_mm * mm + 2

    def big_textarea(self, label: str, field_name: str,
                     height_mm: float = 30, size: int = 9) -> None:
        self.c.setFont(self.sans, size)
        self.c.setFillColorRGB(*BLACK)
        self.c.drawString(MARGIN, self.y, label)
        self.y -= size + 3
        self.c.acroForm.textfield(
            name=field_name,
            x=MARGIN,
            y=self.y - height_mm * mm,
            width=PAGE_W - 2 * MARGIN,
            height=height_mm * mm,
            borderColor=FIELD_BORDER,
            fillColor=FIELD_FILL,
            textColor=black,
            fontName="Helvetica",
            fontSize=size,
            borderWidth=0.5,
            fieldFlags="multiline",
        )
        self.y -= height_mm * mm + 4

    def row_table(self, headers: list[str], n_rows: int,
                  col_widths_mm: list[float], field_prefix: str,
                  row_h_mm: float = 8, size: int = 9) -> None:
        """Tabella con N righe editabili. headers stampati sopra."""
        total_w = sum(col_widths_mm)
        # header
        self.c.setFont(f"{self.sans}-Bold", size)
        self.c.setFillColorRGB(*BLACK)
        x = MARGIN
        for h, w_mm in zip(headers, col_widths_mm):
            self.c.drawString(x + 1 * mm, self.y, h)
            x += w_mm * mm
        self.y -= size + 2
        # rows
        for i in range(n_rows):
            x = MARGIN
            for j, w_mm in enumerate(col_widths_mm):
                fname = f"{field_prefix}_r{i+1}_c{j+1}"
                self.c.acroForm.textfield(
                    name=fname,
                    x=x,
                    y=self.y - row_h_mm * mm + 1,
                    width=w_mm * mm - 1 * mm,
                    height=row_h_mm * mm,
                    borderColor=FIELD_BORDER_LIGHT,
                    fillColor=FIELD_FILL,
                    textColor=black,
                    fontName="Helvetica",
                    fontSize=size,
                    borderWidth=0.5,
                )
                x += w_mm * mm
            self.y -= row_h_mm * mm + 1
        self.y -= 4

    def choice_radio(self, label: str, options: list[str], field_name: str,
                     size: int = 9) -> None:
        """Gruppo radio button orizzontale con opzioni."""
        self.c.setFont(self.sans, size)
        self.c.setFillColorRGB(*BLACK)
        self.c.drawString(MARGIN, self.y, label)
        self.y -= size + 3
        x = MARGIN
        for opt in options:
            self.c.acroForm.radio(
                name=field_name,
                value=opt,
                selected=False,
                x=x,
                y=self.y - 1,
                size=3.5 * mm,
                buttonStyle="cross",
                borderColor=FIELD_BORDER_DARK,
                fillColor=FIELD_FILL,
                borderWidth=0.4,
            )
            self.c.drawString(x + 4.5 * mm, self.y, opt)
            # avanzo in base alla lunghezza dell'etichetta
            x += 4.5 * mm + self.c.stringWidth(opt, self.sans, size) + 8
        self.y -= size + 6

    def hline(self) -> None:
        self.c.setStrokeColorRGB(0.8, 0.8, 0.8)
        self.c.setLineWidth(0.3)
        self.c.line(MARGIN, self.y, PAGE_W - MARGIN, self.y)
        self.y -= 4

    def new_page(self) -> None:
        self.c.showPage()
        self.y = PAGE_H - MARGIN

    def footer(self, text: str) -> None:
        self.c.setFont(self.sans, 7)
        self.c.setFillColorRGB(*GRAY)
        self.c.drawCentredString(PAGE_W / 2, 10 * mm, text)

    def save(self) -> None:
        self.c.save()

    # --- pagine ---

    def page_1_metadata_timeline(self) -> None:
        self.title("Scheda di annotazione soundscape")
        self.subtitle(
            "Gold standard first-hand per validazione. Francesco Mariano, "
            "Soundscape Audio Analysis."
        )
        self.paragraph(
            "Compila questa scheda dopo un ascolto attento della registrazione.\n"
            "Le tue annotazioni diventano riferimento per valutare l'analisi\n"
            "automatica della skill. Vedi pagina 4 per il glossario tassonomico.",
            size=9,
        )
        self.hline()

        self.h2("1. Identificazione")
        self.label_and_field("Nome file audio:", "meta_file")
        self.label_and_field("Luogo registrazione:", "meta_luogo")
        self.label_and_field("Data e ora:", "meta_data")
        self.label_and_field("Durata totale (MM:SS):", "meta_durata",
                             field_w_mm=30)
        self.label_and_field("Microfono / dispositivo:", "meta_mic")
        self.label_and_field("Condizioni meteo:", "meta_meteo")
        self.big_textarea(
            "Note ambientali (contesto, postura, intenzione dell'ascolto):",
            "meta_note", height_mm=22,
        )

        self.hline()
        self.h2("2. Timeline sezioni")
        self.hint(
            "Dividi la registrazione in sezioni con timecode, evento principale, note brevi."
        )
        self.row_table(
            headers=["Tempo (MM:SS - MM:SS)", "Evento principale", "Note"],
            n_rows=8,
            col_widths_mm=[36, 58, 80],
            field_prefix="timeline",
            row_h_mm=8,
        )

        self.footer(
            "Scheda annotazione soundscape - pagina 1/4 - metadati + timeline"
        )

    def page_2_taxonomies(self) -> None:
        self.title("Tassonomie di riferimento")
        self.subtitle(
            "Indica la distribuzione percepita e le categorie dominanti. "
            "Vedi glossario a p.4."
        )
        self.hline()

        self.h2("3. Krause (biofonia/antropofonia/geofonia)")
        self.hint(
            "Distribuzione percepita in percentuale approssimativa.\n"
            "Esempi: bio=uccelli/insetti, antro=voci/auto, geo=vento/acqua."
        )
        self.label_and_field("Biofonia %:", "krause_bio",
                             field_w_mm=30)
        self.label_and_field("Antropofonia %:", "krause_antro",
                             field_w_mm=30)
        self.label_and_field("Geofonia %:", "krause_geo",
                             field_w_mm=30)
        self.label_and_field("Dominante:", "krause_dom")

        self.hline()
        self.h2("4. Schafer")
        self.hint(
            "Keynote = sfondo continuo; Signal = figura saliente;\n"
            "Soundmark = suono identitario del luogo.\n"
            "Hi-Fi = suoni separati; Lo-Fi = saturo."
        )
        self.label_and_field("Keynote (sfondo continuo):", "schafer_key")
        self.label_and_field("Signal (figure salienti):", "schafer_sig")
        self.label_and_field("Soundmark (suoni identitari):", "schafer_mark")
        self.choice_radio(
            "Fidelity:",
            ["Hi-Fi", "Lo-Fi", "misto"],
            "schafer_fid",
        )

        self.hline()
        self.h2("5. Schaeffer (type + detail TARTYP)")
        self.hint(
            "Type: morfologia globale. Esempi: impulsivo=colpo; iterativo=passi;\n"
            "tenuto=drone; trama=folla; campione=blocco complesso."
        )
        self.choice_radio(
            "Type dominante:",
            ["impulsivo", "iterativo", "tenuto", "tenuto-evol", "trama",
             "campione"],
            "schaeffer_type",
        )
        self.label_and_field("Detail TARTYP (opz.):", "schaeffer_det")
        self.hint(
            "Detail esempi: morphing, cross-sintesi, tenuto-modulato,\n"
            "evolutivo-graduale, trama-fine, trama-rugosa."
        )

        self.hline()
        self.h2("6. Smalley (motion + growth)")
        self.hint(
            "Motion: comportamento spaziale del suono.\n"
            "Growth: come il materiale si sviluppa nel tempo (opz.)."
        )
        self.label_and_field("Motion dominante:", "smalley_motion")
        self.hint(
            "Opzioni: flow, turbulence, streaming, radiation, oscillation,\n"
            "ascent, descent, rotation, plane, convergence, divergence."
        )
        self.label_and_field("Growth (opz.):", "smalley_growth")
        self.hint(
            "Opzioni: dilation, accumulation, dissipation, exogeny,\n"
            "endogeny, contraction."
        )

        self.hline()
        self.h2("7-9. Chion / Truax / Westerkamp")
        self.choice_radio(
            "Chion modo dominante:",
            ["causale", "semantico", "ridotto", "misto"],
            "chion",
        )
        self.choice_radio(
            "Truax listening mode:",
            ["background", "readiness", "search"],
            "truax",
        )
        self.choice_radio(
            "Westerkamp soundwalk relevance:",
            ["sì", "no", "parziale"],
            "westerkamp",
        )

        self.footer("Scheda annotazione soundscape - pagina 2/4 - tassonomie")

    def page_3_dramaturgy(self) -> None:
        self.title("Lettura drammaturgica")
        self.subtitle(
            "La tua interpretazione compositiva. Serve a valutare la lettura "
            "dell'agente LLM."
        )
        self.hline()

        self.h2("10. Metafora globale")
        self.big_textarea(
            "Una metafora interpretativa dell'arco della registrazione (1-3 frasi):",
            "metafora", height_mm=16,
        )

        self.h2("11. Scene sonore")
        self.hint(
            "Titoli evocativi che raccontano il brano come un viaggio."
        )
        self.row_table(
            headers=["Titolo evocativo", "Tempo", "Prosa descrittiva (1-2 righe)"],
            n_rows=5,
            col_widths_mm=[40, 28, 106],
            field_prefix="scene",
            row_h_mm=11,
        )

        self.h2("12. Binomi concettuali (2-4 coppie)")
        self.hint(
            "Coppie X - Y che organizzano il senso. Es: uomo - ambiente; "
            "quiete - attivita; interno - esterno."
        )
        self.row_table(
            headers=["Binomio (X - Y)", "Motivazione (1 riga)"],
            n_rows=4,
            col_widths_mm=[50, 124],
            field_prefix="binomi",
            row_h_mm=9,
        )

        self.h2("13. Parentele estetiche")
        self.big_textarea(
            "Compositori/scuole che ti vengono in mente (Ferrari, Westerkamp, GRM, WSP, ecc.):",
            "parentele", height_mm=12,
        )

        self.h2("14. Aspettative dall'analisi automatica")
        self.big_textarea(
            "Cosa vuoi che la skill rilevi + cosa ti aspetti sarà invisibile:",
            "aspettative", height_mm=12,
        )

        self.h2("15. Criticità tecniche percepite")
        self.choice_radio(
            "Hum 50/60 Hz percepito?", ["sì", "no", "dubbio"],
            "tech_hum",
        )
        self.choice_radio(
            "Clipping/saturazione?", ["sì", "no"],
            "tech_clip",
        )
        self.choice_radio(
            "Dinamica:", ["ampia", "media", "ristretta"],
            "tech_dyn",
        )
        self.choice_radio(
            "Livello medio:", ["basso", "corretto", "alto"],
            "tech_lvl",
        )

        self.footer("Scheda annotazione soundscape - pagina 3/4 - drammaturgia")

    def page_4_glossary(self) -> None:
        self.title("Note libere + Glossario tassonomico")
        self.subtitle(
            "Sopra: spazio libero per osservazioni. Sotto: glossario di "
            "riferimento per p. 2-3."
        )
        self.hline()

        self.h2("16. Note libere")
        self.big_textarea(
            "Tutto cio' che non rientra nelle sezioni precedenti (contesto, "
            "impressioni, casi limite, suggerimenti per la skill):",
            "note_libere", height_mm=25,
        )

        self.hline()
        self.h2("Glossario tassonomico", size=12)

        gloss = [
            ("Krause (Bernie Krause, 2012)",
             "Biofonia: organismi viventi non-umani (uccelli, insetti, anfibi, mammiferi).\n"
             "Antropofonia: suoni umani (voci, musica, veicoli, macchinari, strumenti).\n"
             "Geofonia: naturali non-biologici (vento, acqua, tuono, fuoco, sismi)."),
            ("Schafer (R.M. Schafer, 'The Soundscape', 1977)",
             "Keynote: suono-chiave di sfondo sempre presente (ronzio elettrico urbano, vento di quota).\n"
             "Signal: figura che attira l'attenzione (campana, sirena, richiamo animale).\n"
             "Soundmark: suono identitario unico del luogo (campane di una specifica chiesa).\n"
             "Hi-Fi: soundscape con buona separazione (campagna isolata, alba).\n"
             "Lo-Fi: soundscape saturo con sovrapposizione e mascheramento (citta trafficata)."),
            ("Schaeffer type ('Traite des objets musicaux', 1966)",
             "Impulsivo: breve con attacco netto (colpo, esplosione, pizzicato).\n"
             "Iterativo: impulsi a ritmo riconoscibile (passi, goccia, motore).\n"
             "Tenuto: sostenuto stabile (drone, sinusoide, bordone).\n"
             "Tenuto-evolutivo: tenuto con variazione interna graduale.\n"
             "Trama: tessitura continua densa (folla, sciame, rumore).\n"
             "Campione: blocco di suono complesso non riducibile."),
            ("Schaeffer detail TARTYP esteso",
             "Morphing: trasformazione continua di un oggetto in un altro.\n"
             "Cross-sintesi: compenetrazione di due materiali eterogenei.\n"
             "Tenuto-modulato: tenuto con oscillazione timbrica regolare.\n"
             "Evolutivo-graduale: cambio lento e continuo.\n"
             "Trama-fine / trama-rugosa: grana percepita della tessitura."),
            ("Smalley motion (Spectromorphology, 1997)",
             "Flow: movimento fluido continuo. Turbulence: agitazione interna.\n"
             "Streaming: flusso direzionato. Radiation: diffusione da un centro.\n"
             "Oscillation: periodico stabile. Ascent/Descent: salita/discesa.\n"
             "Rotation: circolare. Plane: massa piatta omogenea.\n"
             "Convergence/Divergence: verso/da un punto focale."),
            ("Smalley growth",
             "Dilation: espansione (time-stretch). Accumulation: stratificazione.\n"
             "Dissipation: rarefazione verso silenzio. Exogeny: materiale esterno.\n"
             "Endogeny: crescita interna senza intervento. Contraction: compressione."),
            ("Chion ('L'audio-vision', 1990)",
             "Causale: cerchi di identificare la sorgente ('cosa fa questo suono?').\n"
             "Semantico: interpreti il significato ('cosa comunica?').\n"
             "Ridotto: ascolti la forma sonora in se ('come e strutturata?')."),
            ("Truax ('Acoustic Communication', 1984)",
             "Background: ascolto periferico, suono come ambiente.\n"
             "Readiness: ascolto attento ma non focalizzato.\n"
             "Search: ricerca attiva di informazioni specifiche."),
            ("Westerkamp soundwalk",
             "Passeggiata sonora con ascolto intenzionale. Relevance positiva se "
             "il materiale e compatibile con una pratica di soundwalk, cioe field\n"
             "recording documentario di luogo specifico con ascolto narrativo."),
        ]
        for title, body in gloss:
            self.h2(title, size=9)
            self.paragraph(body, size=7)

        self.footer("Scheda annotazione soundscape - pagina 4/4 - glossario")


def build(output_path: Path) -> Path:
    b = SheetBuilder(output_path)
    b.page_1_metadata_timeline()
    b.new_page()
    b.page_2_taxonomies()
    b.new_page()
    b.page_3_dramaturgy()
    b.new_page()
    b.page_4_glossary()
    b.save()
    return output_path


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "~/soundscape-training/annotation_sheet_v1.pdf"
    ).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    built = build(out)
    print(f"Scheda generata: {built}")


if __name__ == "__main__":
    main()
