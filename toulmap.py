#!/usr/bin/env python3
"""
Mappa Argomentativa di Toulmin
Applicazione per costruire, visualizzare ed esportare mappe argomentative
secondo il modello di Stephen Toulmin.
"""

import sys
import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QPushButton, QGroupBox, QScrollArea,
    QFileDialog, QMessageBox, QSplitter, QFrame, QSizePolicy,
    QStatusBar, QAction, QMenuBar, QToolBar, QTabWidget
)
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF, QTimer
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QPainterPath, QImage, QPixmap, QPalette
)

# ─── Modello dati ────────────────────────────────────────────────────────────

@dataclass
class ToulminArgument:
    title: str = "Mappa Argomentativa di Toulmin"
    claim: str = ""
    data: str = ""
    warrant: str = ""
    backing: str = ""
    qualifier: str = ""
    rebuttal: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        # compatibilità con file salvati senza il campo title
        d.setdefault("title", "Mappa Argomentativa di Toulmin")
        return cls(**d)

    def is_empty(self):
        return not any([self.claim, self.data, self.warrant,
                        self.backing, self.qualifier, self.rebuttal])


# ─── Palette cromatica ───────────────────────────────────────────────────────

COLORS = {
    "claim":    {"bg": "#2C5F8A", "fg": "#FFFFFF", "border": "#1A3D5C"},
    "data":     {"bg": "#2E7D52", "fg": "#FFFFFF", "border": "#1A5435"},
    "warrant":  {"bg": "#7B4F8A", "fg": "#FFFFFF", "border": "#52305C"},
    "backing":  {"bg": "#9C5A2E", "fg": "#FFFFFF", "border": "#6B3D1A"},
    "qualifier":{"bg": "#5A7A3A", "fg": "#FFFFFF", "border": "#3A5220"},
    "rebuttal": {"bg": "#8A3A3A", "fg": "#FFFFFF", "border": "#5C1A1A"},
    "bg":       "#F5F3EE",
    "arrow":    "#555555",
    "grid":     "#E8E4DC",
}

LABELS = {
    "claim":     "Tesi (Claim)",
    "data":      "Dati (Data/Grounds)",
    "warrant":   "Garanzia (Warrant)",
    "backing":   "Sostegno (Backing)",
    "qualifier": "Qualificatore (Qualifier)",
    "rebuttal":  "Confutazione (Rebuttal)",
}

DESCRIPTIONS = {
    "claim":     "L'affermazione che si vuole sostenere, la conclusione dell'argomento.",
    "data":      "I fatti, le prove o le evidenze su cui si basa l'argomentazione.",
    "warrant":   "Il principio generale che collega i dati alla tesi.",
    "backing":   "Le ragioni che supportano e legittimano la garanzia.",
    "qualifier": "Il grado di certezza o forza della tesi (es. «probabilmente», «di norma»).",
    "rebuttal":  "Le eccezioni o condizioni in cui la tesi non vale.",
}

# ─── Widget di disegno ───────────────────────────────────────────────────────

class MapCanvas(QWidget):
    """Canvas di disegno per la mappa di Toulmin."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.argument = ToulminArgument()
        self.setMinimumSize(900, 620)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: #F5F3EE;")

    def update_argument(self, arg: ToulminArgument):
        self.argument = arg
        self.update()

    # ── geometria nodi ──────────────────────────────────────────────────────
    def _layout(self, w, h, font_scale=1.0, extra_margin=0):
        """Restituisce le posizioni (cx, cy, bw, bh) di ogni nodo.
        cy e' il centro del livello principale (data/claim). Viene calcolato
        in modo che tutti i nodi rientrino nel canvas con 12px di margine."""
        MARGIN = 12 + extra_margin
        bw = min(int(200 * font_scale), w // 4 - 20)
        bh = int(80 * font_scale)
        cx = w / 2

        # bordo superiore del nodo piu' alto (rebuttal): cy - bh*1.7 - bh/2
        # bordo inferiore del nodo piu' basso (backing):  cy + bh*3.2 + bh/2
        top_offset    = bh * 1.7 + bh / 2
        bottom_offset = bh * 3.2 + bh / 2

        cy_min = MARGIN + top_offset
        cy_max = h - MARGIN - bottom_offset

        if cy_min > cy_max:
            cy = (cy_min + cy_max) / 2
        else:
            cy = max(cy_min, min(h * 0.40, cy_max))

        return {
            "data":      (cx - bw * 1.6, cy,             bw,      bh),
            "warrant":   (cx,            cy + bh * 1.7,  bw,      bh),
            "claim":     (cx + bw * 1.6, cy,             bw + 20, bh),
            "qualifier": (cx + bw * 0.6, cy - bh * 1.4, bw - 10, bh - 10),
            "backing":   (cx,            cy + bh * 3.2,  bw,      bh),
            "rebuttal":  (cx + bw * 1.6, cy - bh * 1.7, bw,      bh),
        }

    def _draw_scene(self, painter, w, h, font_scale=1.0, extra_margin=0):
        """Disegna l'intera mappa su un painter già configurato."""
        layout = self._layout(w, h, font_scale, extra_margin=extra_margin)
        painter.fillRect(0, 0, w, h, QColor(COLORS["bg"]))
        self._draw_grid(painter, w, h)
        self._draw_arrow(painter, layout["data"],      layout["claim"],   "→ supporta →",   font_scale=font_scale)
        self._draw_arrow(painter, layout["warrant"],   layout["claim"],   "→ garantisce →", font_scale=font_scale)
        self._draw_arrow(painter, layout["backing"],   layout["warrant"], "→ sostiene →",   font_scale=font_scale)
        self._draw_arrow(painter, layout["qualifier"], layout["claim"],   "qualifica",       dashed=True, font_scale=font_scale)
        self._draw_arrow(painter, layout["rebuttal"],  layout["claim"],   "a meno che",      dashed=True, color="#8A3A3A", font_scale=font_scale)
        for key, pos in layout.items():
            text = getattr(self.argument, key)
            self._draw_node(painter, key, pos, text, font_scale=font_scale)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        self._draw_scene(painter, self.width(), self.height(), font_scale=1.0)
        painter.end()

    def render_to_image(self, scale=2, font_scale=1.0, extra_margin=0):
        """Restituisce un QImage ad alta risoluzione."""
        w, h = self.width(), self.height()
        img = QImage(w * scale, h * scale, QImage.Format_ARGB32)
        img.fill(Qt.white)
        painter = QPainter(img)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.scale(scale, scale)
        self._draw_scene(painter, w, h, font_scale=font_scale, extra_margin=extra_margin)
        painter.end()
        return img

    def _draw_grid(self, painter, w, h):
        pen = QPen(QColor(COLORS["grid"]), 1, Qt.DotLine)
        painter.setPen(pen)
        step = 40
        for x in range(0, w, step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, step):
            painter.drawLine(0, y, w, y)

    def _draw_node(self, painter, key, pos, text, font_scale=1.0):
        cx, cy, bw, bh = pos
        x, y = cx - bw / 2, cy - bh / 2
        col = COLORS[key]

        fs = font_scale  # abbreviazione locale

        # ombra
        shadow_rect = QRectF(x + 3, y + 3, bw, bh)
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 40))

        # sfondo nodo
        rect = QRectF(x, y, bw, bh)
        grad = QLinearGradient(x, y, x, y + bh)
        base = QColor(col["bg"])
        lighter = base.lighter(120)
        grad.setColorAt(0, lighter)
        grad.setColorAt(1, base)
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.fillPath(path, QBrush(grad))

        # bordo
        painter.setPen(QPen(QColor(col["border"]), 2))
        painter.drawPath(path)

        # etichetta tipo (piccola, in alto)
        label_sz = max(7, int(7 * fs))
        label_font = QFont("Helvetica", label_sz, QFont.Bold)
        painter.setFont(label_font)
        painter.setPen(QColor(col["fg"]))
        lh = label_sz * 2.2  # altezza riga etichetta
        label_rect = QRectF(x + 6, y + 4, bw - 12, lh)
        painter.drawText(label_rect, Qt.AlignLeft | Qt.AlignVCenter,
                         LABELS[key].upper())

        # testo principale
        content_sz = max(9, int(9 * fs))
        content_font = QFont("Helvetica", content_sz)
        painter.setFont(content_font)
        display = text if text else "—"
        top_offset = lh + 6
        content_rect = QRectF(x + 8, y + top_offset, bw - 16, bh - top_offset - 6)
        painter.drawText(content_rect,
                         Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
                         display)

    def _node_edge(self, frm, to):
        """Calcola i punti di ingresso/uscita tra due nodi."""
        fx, fy = frm[0], frm[1]
        tx, ty = to[0], to[1]
        fbw, fbh = frm[2], frm[3]
        tbw, tbh = to[2], to[3]

        dx, dy = tx - fx, ty - fy
        angle = math.atan2(dy, dx)

        # punto sul bordo del nodo sorgente
        sx = fx + math.cos(angle) * fbw / 2
        sy = fy + math.sin(angle) * fbh / 2
        # punto sul bordo del nodo destinazione
        ex = tx - math.cos(angle) * tbw / 2
        ey = ty - math.sin(angle) * tbh / 2
        return (sx, sy), (ex, ey)

    def _draw_arrow(self, painter, frm, to, label="", dashed=False, color=None, font_scale=1.0):
        col = color or COLORS["arrow"]
        pen = QPen(QColor(col), 2)
        if dashed:
            pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        (sx, sy), (ex, ey) = self._node_edge(frm, to)

        # curva di Bézier leggera
        cx1 = sx + (ex - sx) * 0.4
        cy1 = sy
        cx2 = sx + (ex - sx) * 0.6
        cy2 = ey

        path = QPainterPath()
        path.moveTo(sx, sy)
        path.cubicTo(cx1, cy1, cx2, cy2, ex, ey)
        painter.drawPath(path)

        # punta freccia
        angle = math.atan2(ey - cy2, ex - cx2)
        al, aw = 12, 6
        p1 = QPointF(ex - al * math.cos(angle - 0.4),
                     ey - al * math.sin(angle - 0.4))
        p2 = QPointF(ex - al * math.cos(angle + 0.4),
                     ey - al * math.sin(angle + 0.4))
        arrow = QPainterPath()
        arrow.moveTo(ex, ey)
        arrow.lineTo(p1)
        arrow.lineTo(p2)
        arrow.closeSubpath()
        painter.fillPath(arrow, QBrush(QColor(col)))

        # etichetta freccia
        if label:
            mid_x = (sx + ex) / 2 + 4
            mid_y = (sy + ey) / 2 - 8
            arrow_lbl_sz = max(7, int(7 * font_scale))
            lf = QFont("Helvetica", arrow_lbl_sz, QFont.StyleItalic)
            painter.setFont(lf)
            painter.setPen(QColor("#666666"))
            lbl_w = max(100, int(100 * font_scale))
            lbl_h = max(20, int(20 * font_scale))
            painter.drawText(QRectF(mid_x - lbl_w/2, mid_y - lbl_h/2, lbl_w, lbl_h),
                             Qt.AlignCenter, label)



# ─── Pannello di input ───────────────────────────────────────────────────────

class FieldWidget(QWidget):
    """Singolo campo di input con colore e descrizione."""

    def __init__(self, key: str, parent=None):
        super().__init__(parent)
        self.key = key
        col = COLORS[key]
        self._build_ui(col)

    def _build_ui(self, col):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(2)

        # intestazione colorata
        header = QLabel(LABELS[self.key])
        header.setStyleSheet(f"""
            background-color: {col['bg']};
            color: {col['fg']};
            font-weight: bold;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 4px 4px 0 0;
        """)
        layout.addWidget(header)

        # descrizione
        desc = QLabel(DESCRIPTIONS[self.key])
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 9px; padding: 2px 4px;")
        layout.addWidget(desc)

        # area di testo
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(65)
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid {col['border']};
                border-top: none;
                border-radius: 0 0 4px 4px;
                padding: 4px;
                font-size: 11px;
                background: #FAFAFA;
            }}
            QTextEdit:focus {{
                border: 2px solid {col['bg']};
                border-top: none;
                background: white;
            }}
        """)
        layout.addWidget(self.text_edit)

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def set_text(self, text: str):
        self.text_edit.setPlainText(text)

    def clear(self):
        self.text_edit.clear()


# ─── Finestra principale ─────────────────────────────────────────────────────

class ToulminApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.current_file: Optional[str] = None
        self.argument = ToulminArgument()
        self._build_ui()
        self._build_menu()
        self._update_map()

    # ── costruzione UI ───────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("Mappa Argomentativa di Toulmin")
        self.setMinimumSize(1100, 680)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # splitter orizzontale
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ── pannello sinistro: campi input ──────────────────────────────────
        left_panel = QWidget()
        left_panel.setMaximumWidth(340)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        title_label = QLabel("Inserisci i componenti dell'argomento")
        title_label.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #333;
            padding: 6px 0;
        """)
        left_layout.addWidget(title_label)

        # campo titolo mappa
        map_title_label = QLabel("Titolo della mappa")
        map_title_label.setStyleSheet("font-size: 11px; color: #555; margin-top: 4px;")
        left_layout.addWidget(map_title_label)
        from PyQt5.QtWidgets import QLineEdit
        self.map_title_edit = QLineEdit("Mappa Argomentativa di Toulmin")
        self.map_title_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #BBBBBB;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                font-weight: bold;
                color: #2C5F8A;
                background: white;
            }
            QLineEdit:focus {
                border: 2px solid #2C5F8A;
            }
        """)
        self.map_title_edit.textChanged.connect(self._on_text_changed)
        left_layout.addWidget(self.map_title_edit)

        # scroll area per i campi
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(4, 4, 4, 4)

        self.fields = {}
        for key in ["claim", "data", "warrant", "backing", "qualifier", "rebuttal"]:
            fw = FieldWidget(key)
            fw.text_edit.textChanged.connect(self._on_text_changed)
            self.fields[key] = fw
            scroll_layout.addWidget(fw)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        left_layout.addWidget(scroll)

        # bottoni azione
        btn_row = QHBoxLayout()
        self.btn_clear = QPushButton("🗑 Cancella tutto")
        self.btn_clear.setStyleSheet(self._btn_style("#888"))
        self.btn_clear.clicked.connect(self._clear_all)
        btn_row.addWidget(self.btn_clear)

        self.btn_example = QPushButton("💡 Esempio")
        self.btn_example.setStyleSheet(self._btn_style("#5A7A3A"))
        self.btn_example.clicked.connect(self._load_example)
        btn_row.addWidget(self.btn_example)

        left_layout.addLayout(btn_row)

        # ── pannello destro: canvas + pulsanti esportazione ─────────────────
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        canvas_label = QLabel("Mappa argomentativa")
        canvas_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #333; padding: 6px 0;")
        right_layout.addWidget(canvas_label)

        self.canvas = MapCanvas()
        right_layout.addWidget(self.canvas, 1)

        # barra esportazione
        export_bar = QHBoxLayout()
        export_bar.setSpacing(6)

        lbl = QLabel("Esporta:")
        lbl.setStyleSheet("font-size: 11px; color: #555;")
        export_bar.addWidget(lbl)

        for label, icon, handler, color in [
            ("PNG",  "🖼",  self._export_png,  "#2C5F8A"),
            ("HTML", "🌐",  self._export_html, "#2E7D52"),
            ("PDF",  "📄",  self._export_pdf,  "#7B4F8A"),
            ("JSON", "💾",  self._save_file,   "#9C5A2E"),
        ]:
            btn = QPushButton(f"{icon} {label}")
            btn.setStyleSheet(self._btn_style(color))
            btn.clicked.connect(handler)
            export_bar.addWidget(btn)

        export_bar.addStretch()
        right_layout.addLayout(export_bar)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 3)

        # status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Pronto. Inserisci i componenti dell'argomento.")

    def _btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.85;
                background-color: {color}CC;
            }}
            QPushButton:pressed {{
                background-color: {color}99;
            }}
        """

    def _build_menu(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("File")
        actions = [
            ("Nuovo",    "Ctrl+N", self._new_file),
            ("Apri…",   "Ctrl+O", self._open_file),
            ("Salva",   "Ctrl+S", self._save_file),
            ("Salva con nome…", "Ctrl+Shift+S", self._save_as),
            (None, None, None),
            ("Esporta PNG…",  None, self._export_png),
            ("Esporta HTML…", None, self._export_html),
            ("Esporta PDF…",  None, self._export_pdf),
            (None, None, None),
            ("Esci", "Ctrl+Q", self.close),
        ]
        for label, shortcut, handler in actions:
            if label is None:
                file_menu.addSeparator()
            else:
                act = QAction(label, self)
                if shortcut:
                    act.setShortcut(shortcut)
                act.triggered.connect(handler)
                file_menu.addAction(act)

        # Aiuto
        help_menu = mb.addMenu("Aiuto")
        about_act = QAction("Il modello di Toulmin", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)
        help_menu.addSeparator()
        info_act = QAction("Informazioni su ToulMap…", self)
        info_act.triggered.connect(self._show_info)
        help_menu.addAction(info_act)

    # ── logica aggiornamento ─────────────────────────────────────────────────
    def _on_text_changed(self):
        self._update_map()

    def _update_map(self):
        self.argument = ToulminArgument(
            title=self.map_title_edit.text().strip() or "Mappa Argomentativa di Toulmin",
            claim=self.fields["claim"].get_text(),
            data=self.fields["data"].get_text(),
            warrant=self.fields["warrant"].get_text(),
            backing=self.fields["backing"].get_text(),
            qualifier=self.fields["qualifier"].get_text(),
            rebuttal=self.fields["rebuttal"].get_text(),
        )
        self.canvas.update_argument(self.argument)

    # ── azioni ───────────────────────────────────────────────────────────────
    def _clear_all(self):
        for fw in self.fields.values():
            fw.clear()
        self.map_title_edit.setText("Mappa Argomentativa di Toulmin")
        self.current_file = None
        self.setWindowTitle("Mappa Argomentativa di Toulmin")
        self.status.showMessage("Mappa cancellata.")

    def _load_example(self):
        example = ToulminArgument(
            claim="Harry è un cittadino britannico.",
            data="Harry è nato nelle Bermuda.",
            warrant="Chi nasce nelle Bermuda è generalmente cittadino britannico.",
            backing="La legge sulla cittadinanza britannica del 1948 stabilisce questo principio.",
            qualifier="Presumibilmente / con buona probabilità",
            rebuttal="A meno che i genitori di Harry siano stranieri, o che abbia rinunciato alla cittadinanza.",
        )
        for key, fw in self.fields.items():
            fw.set_text(getattr(example, key))
        self.status.showMessage("Esempio caricato (argomento classico di Toulmin).")

    def _new_file(self):
        reply = QMessageBox.question(
            self, "Nuovo file",
            "Creare una nuova mappa? I dati non salvati andranno persi.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._clear_all()

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri mappa", "", "File JSON (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                arg = ToulminArgument.from_dict(data)
                self.map_title_edit.setText(arg.title)
                for key, fw in self.fields.items():
                    fw.set_text(getattr(arg, key))
                self.current_file = path
                self.setWindowTitle(f"Toulmin — {os.path.basename(path)}")
                self.status.showMessage(f"Aperto: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Errore", f"Impossibile aprire il file:\n{e}")

    def _save_file(self):
        if self.current_file:
            self._write_json(self.current_file)
        else:
            self._save_as()

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Salva mappa", "mappa_toulmin.json", "File JSON (*.json)"
        )
        if path:
            self.current_file = path
            self._write_json(path)

    def _write_json(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.argument.to_dict(), f, ensure_ascii=False, indent=2)
            self.setWindowTitle(f"Toulmin — {os.path.basename(path)}")
            self.status.showMessage(f"Salvato: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile salvare:\n{e}")

    # ── rendering condiviso: PNG in memoria ─────────────────────────────────
    def _render_png_bytes(self, w=1800, h=1000, font_scale=1.8, extra_margin=60) -> bytes:
        """Renderizza la mappa su un canvas virtuale e restituisce i byte PNG."""
        tmp = MapCanvas()
        tmp.resize(w, h)
        tmp.update_argument(self.argument)
        img = tmp.render_to_image(scale=1, font_scale=font_scale, extra_margin=extra_margin)
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name
        img.save(tmp_path, "PNG")
        with open(tmp_path, "rb") as f:
            data = f.read()
        os.unlink(tmp_path)
        return data

    # ── esportazione PNG ─────────────────────────────────────────────────────
    def _export_png(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta come PNG", "mappa_toulmin.png", "Immagini PNG (*.png)"
        )
        if path:
            img = self.canvas.render_to_image(scale=2)
            if img.save(path, "PNG"):
                self.status.showMessage(f"PNG salvato: {path}")
            else:
                QMessageBox.critical(self, "Errore", "Impossibile salvare il PNG.")

    # ── esportazione HTML ────────────────────────────────────────────────────
    def _export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta come HTML", "mappa_toulmin.html", "File HTML (*.html)"
        )
        if not path:
            return
        try:
            import base64
            png_bytes = self._render_png_bytes(w=1800, h=1000)
            b64 = base64.b64encode(png_bytes).decode("ascii")
            map_title = self.argument.title
            html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{map_title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Helvetica, sans-serif;
         background: #F5F3EE; color: #222;
         padding: 2rem; display: flex; flex-direction: column;
         align-items: center; }}
  h1 {{ font-size: 1.5rem; color: #2C5F8A; margin-bottom: 1.2rem; }}
  .map-wrap {{ width: 100%; max-width: 1100px; border-radius: 10px;
               overflow: hidden; box-shadow: 0 4px 18px rgba(0,0,0,.15); }}
  .map-wrap img {{ width: 100%; display: block; }}
  .legend {{ width: 100%; max-width: 1100px; margin-top: 1.5rem; padding: 1rem;
             background: white; border-radius: 8px; border: 1px solid #ddd; }}
  .legend h2 {{ font-size: .95rem; margin-bottom: .6rem; color: #555; }}
  .legend dl {{ display: grid; grid-template-columns: 1fr 1fr; gap: .35rem .8rem; }}
  .legend dt {{ font-weight: bold; font-size: .82rem; }}
  .legend dd {{ font-size: .82rem; color: #555; margin: 0; }}
  footer {{ margin-top: 1.5rem; font-size: .72rem; color: #aaa; }}
</style>
</head>
<body>
<h1>{map_title}</h1>
<div class="map-wrap">
  <img src="data:image/png;base64,{b64}" alt="Mappa di Toulmin">
</div>
<div class="legend">
  <h2>Legenda del modello di Toulmin</h2>
  <dl>
    {"".join(f"<dt>{LABELS[k]}</dt><dd>{DESCRIPTIONS[k]}</dd>" for k in LABELS)}
  </dl>
</div>
<footer>Generato con ToulMap · <a href="https://antonio-vigilante.github.io/toulmap" style="color:#2C5F8A;">antonio-vigilante.github.io/toulmap</a></footer>
</body>
</html>"""
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            self.status.showMessage(f"HTML salvato: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore HTML", str(e))

    # ── esportazione PDF ─────────────────────────────────────────────────────
    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta come PDF", "mappa_toulmin.pdf", "File PDF (*.pdf)"
        )
        if not path:
            return
        try:
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import cm, mm
            from reportlab.platypus import (SimpleDocTemplate, Spacer,
                                            HRFlowable, Paragraph, Image as RLImage)
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            import tempfile, os

            page_w, page_h = landscape(A4)
            margin = 1.5 * cm

            doc = SimpleDocTemplate(path, pagesize=landscape(A4),
                                    leftMargin=margin, rightMargin=margin,
                                    topMargin=margin, bottomMargin=margin)
            story = []

            # titolo
            title_style = ParagraphStyle("title", fontSize=16, alignment=TA_CENTER,
                                         textColor=colors.HexColor("#2C5F8A"),
                                         spaceAfter=10, fontName="Helvetica-Bold")
            story.append(Paragraph(self.argument.title, title_style))
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=colors.HexColor("#2C5F8A"), spaceAfter=8))

            # immagine della mappa
            avail_w = page_w - 2 * margin
            avail_h = page_h - 2 * margin - 60  # spazio per titolo e legenda

            # render ad alta risoluzione proporzionato alla pagina
            render_w = int(avail_w / mm * 3.78 * 2)   # ~2× risoluzione schermo
            render_h = int(avail_h / mm * 3.78 * 2)

            png_bytes = self._render_png_bytes(w=render_w, h=render_h)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(png_bytes)
                tmp_img_path = f.name

            story.append(RLImage(tmp_img_path, width=avail_w, height=avail_h))
            story.append(Spacer(1, 6))

            # legenda compatta
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=colors.HexColor("#AAAAAA"), spaceAfter=4))
            leg_style = ParagraphStyle("leg", fontSize=7, leading=10,
                                       textColor=colors.HexColor("#555555"),
                                       fontName="Helvetica")
            leg_text = "  ·  ".join(
                f"<b>{LABELS[k]}</b>: {DESCRIPTIONS[k]}" for k in LABELS
            )
            story.append(Paragraph(leg_text, leg_style))

            doc.build(story)
            os.unlink(tmp_img_path)
            self.status.showMessage(f"PDF salvato: {path}")
        except ImportError:
            QMessageBox.critical(self, "Libreria mancante",
                                 "reportlab non è installato.\n"
                                 "Esegui: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Errore PDF", str(e))

    # ── finestra informazioni ────────────────────────────────────────────────
    def _show_about(self):
        text = """<h2 style="color:#2C5F8A;">Il modello argomentativo di Toulmin</h2>
<p>Stephen Toulmin (1922–2009) propose in <em>The Uses of Argument</em> (1958)
un modello per analizzare la struttura logica degli argomenti, alternativo
alla sillogistica classica e più vicino al ragionamento ordinario.</p>
<h3 style="margin-top:12px;">I sei componenti</h3>
<ul>
<li><b>Tesi (Claim)</b>: l'affermazione da dimostrare.</li>
<li><b>Dati (Data/Grounds)</b>: i fatti su cui si basa l'argomento.</li>
<li><b>Garanzia (Warrant)</b>: il principio generale che connette dati e tesi.</li>
<li><b>Sostegno (Backing)</b>: le ragioni che legittimano la garanzia.</li>
<li><b>Qualificatore (Qualifier)</b>: il grado di certezza della tesi.</li>
<li><b>Confutazione (Rebuttal)</b>: le eccezioni o condizioni di inapplicabilità.</li>
</ul>"""
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Il modello di Toulmin")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(text)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()


    def _show_info(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
        from PyQt5.QtCore import QUrl
        from PyQt5.QtGui import QDesktopServices
        text = (
            "<h2 style='color:#2C5F8A;margin-bottom:8px;'>ToulMap</h2>"
            "<p style='margin-bottom:8px;'>"
            "Applicazione per la costruzione di mappe argomentative "
            "secondo il modello di Stephen Toulmin.</p>"
            "<p style='margin-bottom:8px;'>"
            "Creata da <b>Antonio Vigilante</b>.</p>"
            "<p style='margin-bottom:8px;'>"
            "Rilasciata con licenza libera "
            "<b>GNU GPL v3</b>.</p>"
            "<p>"
            "Repository e documentazione:<br>"
            "<a href='https://antonio-vigilante.github.io/toulmap' "
            "style='color:#2C5F8A;'>"
            "antonio-vigilante.github.io/toulmap</a></p>"
        )
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Informazioni su ToulMap")
        dlg.setTextFormat(Qt.RichText)
        dlg.setText(text)
        dlg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        dlg.setStandardButtons(QMessageBox.Ok)
        dlg.exec_()


# ─── Avvio ───────────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Mappa Argomentativa di Toulmin")
    app.setStyle("Fusion")

    # palette chiara
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#F5F3EE"))
    palette.setColor(QPalette.WindowText, QColor("#222222"))
    palette.setColor(QPalette.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.AlternateBase, QColor("#EAE7DF"))
    app.setPalette(palette)

    window = ToulminApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
