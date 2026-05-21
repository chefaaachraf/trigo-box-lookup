"""
Box Lookup App — TRIGO v3.0
----------------------------
Scannez une étiquette GALIA (ou saisissez une référence pièce) pour afficher
l'emballage plastique (UC) à utiliser.

Dépendances :  pip install ttkbootstrap pandas openpyxl pillow
"""

import csv
import re
import tkinter as tk
from tkinter import font as tkfont, messagebox, filedialog
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import pandas as pd
from PIL import Image, ImageTk

# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_XLSX  = Path(__file__).with_name("Liste emballages ref Trigo.xlsx")
DEFAULT_SHEET = "Feuil3"
REF_COL       = "Reference"
UC_COL        = "UC"

# ── Palette TRIGO ─────────────────────────────────────────────────────────────
C_NAVY    = "#004983"
C_LIME    = "#A8C855"
C_TEAL    = "#275C7B"
C_SAGE    = "#51806E"
C_GREEN   = "#7DA361"
C_GRAY    = "#717179"
C_RED     = "#D0001B"

C_BG      = "#F0F3F8"
C_TOPBAR  = "#E4E9F2"
C_CARD    = "#FFFFFF"
C_SURFACE = "#F7F9FC"
C_BORDER  = "#C8D0DF"
C_TEXT    = "#1A2236"
C_TEXT_S  = "#4A5568"
C_TEXT_M  = "#8A96A8"

C_SUCCESS    = "#2D7A1F"
C_SUCCESS_BG = "#EBF5E7"
C_ERROR      = C_RED
C_ERROR_BG   = "#FDEDF0"
C_WARN       = "#7A5A00"
C_WARN_BG    = "#FDF6E0"
C_IDLE       = C_GRAY
C_IDLE_BG    = "#F5F7FB"


# ── Data helpers ──────────────────────────────────────────────────────────────

def normalize(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def load_mapping(xlsx_path: Path = DEFAULT_XLSX, sheet_name: str = DEFAULT_SHEET,
                 ref_col: str = REF_COL, uc_col: str = UC_COL):
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {xlsx_path}")
    try:
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name,
                           dtype={ref_col: str, uc_col: str})
    except Exception as exc:
        raise ValueError(f"Impossible de lire le fichier Excel :\n{exc}") from exc

    missing = [c for c in (ref_col, uc_col) if c not in df.columns]
    if missing:
        raise ValueError(
            f"Colonnes introuvables dans « {sheet_name} » : {missing}\n"
            f"Disponibles : {list(df.columns)}"
        )

    df = df.dropna(subset=[ref_col, uc_col])
    df[ref_col] = df[ref_col].astype(str).str.strip()
    df[uc_col]  = df[uc_col].astype(str).str.strip()

    uc_by_ref = defaultdict(list)
    for _, row in df.iterrows():
        uc_by_ref[normalize(row[ref_col])].append(row[uc_col])

    final_map, details_map = {}, {}
    for nref, ucs in uc_by_ref.items():
        counts = Counter(ucs)
        final_map[nref]   = counts.most_common(1)[0][0]
        details_map[nref] = dict(counts)

    emplacement_map = {}
    empl_col = "Emplacement"
    if empl_col in df.columns:
        for _, row in df.iterrows():
            raw_ref  = str(row[ref_col]).strip() if pd.notna(row[ref_col]) else ""
            empl_val = row.get(empl_col)
            empl     = str(empl_val).strip() if (empl_val is not None and pd.notna(empl_val)) else ""
            if raw_ref and empl and empl.lower() != "nan":
                nref = normalize(raw_ref)
                if nref not in emplacement_map:
                    emplacement_map[nref] = empl

    return final_map, list(df[ref_col].astype(str).unique()), details_map, emplacement_map


def extract_reference(scanned: str, known_norm_set: set, known_original: list):
    s_norm = normalize(scanned)
    if s_norm in known_norm_set:
        return s_norm
    matches = [
        (normalize(r), len(normalize(r)))
        for r in known_original
        if normalize(r) and normalize(r) in s_norm
    ]
    return max(matches, key=lambda x: x[1])[0] if matches else None


def find_image(uc: str) -> Path | None:
    """Cherche l'image d'un UC en tolérant les variations de tirets/espaces."""
    base = Path(__file__).parent / "box_images"
    exact = base / f"{uc}.jpg"
    if exact.exists():
        return exact
    uc_norm = normalize(uc)
    for img in base.glob("*.jpg"):
        if normalize(img.stem) == uc_norm:
            return img
    return None


# ── GUI ───────────────────────────────────────────────────────────────────────

class BoxLookupApp(ttk.Window):

    def __init__(self, mapping: dict, original_refs: list, details_map: dict,
                 ref_count: int, xlsx_path: Path, sheet_name: str,
                 ref_col: str, uc_col: str):
        super().__init__(themename="flatly")

        self.mapping       = mapping
        self.details_map   = details_map
        self.original_refs = original_refs
        self.known_norm    = set(mapping.keys())
        self.xlsx_path     = xlsx_path
        self.sheet_name    = sheet_name
        self._ref_col      = ref_col
        self._uc_col       = uc_col
        self._scan_count   = 0
        self._history: list[dict] = []

        self.title("TRIGO — Box Lookup")
        self.resizable(False, False)
        self.geometry("760x840")
        self.configure(bg=C_BG)

        self._build_fonts()
        self._setup_styles()
        self._build_topbar()
        self._build_header(ref_count)
        self._build_notebook()
        self._build_statusbar(ref_count)

        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

        self.entry.focus_set()

    # ── fonts -----------------------------------------------------------------

    def _build_fonts(self):
        fam = "Segoe UI"
        self.f_topbar  = tkfont.Font(family=fam, size=8)
        self.f_brand   = tkfont.Font(family=fam, size=26, weight="bold")
        self.f_brand_s = tkfont.Font(family=fam, size=9,  weight="bold")
        self.f_section = tkfont.Font(family=fam, size=8,  weight="bold")
        self.f_entry   = tkfont.Font(family=fam, size=15)
        self.f_result  = tkfont.Font(family=fam, size=30, weight="bold")
        self.f_detail  = tkfont.Font(family=fam, size=10)
        self.f_hint    = tkfont.Font(family=fam, size=8,  slant="italic")
        self.f_badge   = tkfont.Font(family=fam, size=7,  weight="bold")
        self.f_count   = tkfont.Font(family=fam, size=11, weight="bold")

    # ── ttkbootstrap style overrides -----------------------------------------

    def _setup_styles(self):
        s = self.style

        # ── Notebook: TRIGO-branded tabs
        s.configure("TNotebook",
                    background=C_TOPBAR, tabmargins=[0, 0, 0, 0])
        s.configure("TNotebook.Tab",
                    background=C_TOPBAR, foreground=C_TEXT_M,
                    font=("Segoe UI", 8, "bold"), padding=[18, 8])
        s.map("TNotebook.Tab",
              background=[("selected", C_CARD), ("active", C_BG)],
              foreground=[("selected", C_NAVY), ("active", C_TEXT_S)])

        # ── Treeview: clean table
        s.configure("Treeview",
                    background=C_CARD, fieldbackground=C_CARD,
                    foreground=C_TEXT, rowheight=28,
                    font=("Segoe UI", 9))
        s.configure("Treeview.Heading",
                    background=C_TOPBAR, foreground=C_NAVY,
                    font=("Segoe UI", 8, "bold"), relief="flat")
        s.map("Treeview",
              background=[("selected", C_NAVY)],
              foreground=[("selected", "#FFFFFF")])

        # ── Buttons: override primary to TRIGO navy
        s.configure("primary.TButton",
                    font=("Segoe UI", 8, "bold"))
        s.configure("secondary.Outline.TButton",
                    font=("Segoe UI", 8, "bold"))

    # ── topbar ----------------------------------------------------------------

    def _build_topbar(self):
        bar = tk.Frame(self, bg=C_TOPBAR, height=26)
        bar.pack(fill=X)
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=C_TOPBAR)
        left.pack(side=LEFT, padx=14, fill=Y)
        for crumb, color in [
            ("TRIGO SAS", C_TEXT_S), ("›", C_TEXT_M),
            ("Logistique", C_TEXT_S), ("›", C_TEXT_M),
            ("Box Lookup", C_LIME),
        ]:
            tk.Label(left, text=crumb, font=self.f_topbar,
                     fg=color, bg=C_TOPBAR).pack(side=LEFT, padx=2)

        tk.Label(bar, text="v3.0", font=self.f_topbar,
                 fg=C_TEXT_M, bg=C_TOPBAR).pack(side=RIGHT, padx=14)

    # ── header ----------------------------------------------------------------

    def _build_header(self, ref_count: int):
        header = tk.Frame(self, bg=C_NAVY, height=88)
        header.pack(fill=X)
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=C_NAVY)
        inner.pack(fill=BOTH, expand=YES, padx=28)

        left = tk.Frame(inner, bg=C_NAVY)
        left.pack(side=LEFT, fill=Y)

        logo_row = tk.Frame(left, bg=C_NAVY)
        logo_row.pack(anchor="sw", pady=(16, 0))
        tk.Label(logo_row, text="TRIGO", font=self.f_brand,
                 fg="#FFFFFF", bg=C_NAVY).pack(side=LEFT)
        tk.Label(logo_row, text="●",
                 font=tkfont.Font(family="Segoe UI", size=8),
                 fg=C_LIME, bg=C_NAVY).pack(side=LEFT, anchor=S, pady=(0, 10))

        tk.Label(left, text="BOX LOOKUP  —  Identification emballage UC",
                 font=self.f_brand_s, fg=C_LIME, bg=C_NAVY, anchor=W).pack(anchor=NW)

        right = tk.Frame(inner, bg=C_NAVY)
        right.pack(side=RIGHT, fill=Y, pady=14)

        self.kpi_refs_var = tk.StringVar(value=str(ref_count))
        self._kpi_block(right, "REFS", self.kpi_refs_var, C_LIME)
        tk.Frame(right, bg="#FFFFFF", width=1, height=36).pack(
            side=LEFT, padx=16, pady=8)
        self.kpi_scans_var = tk.StringVar(value="0")
        self._kpi_block(right, "SCANS", self.kpi_scans_var, "#A8C8E8")

        tk.Frame(self, bg=C_LIME, height=3).pack(fill=X)

    def _kpi_block(self, parent, label: str, var: tk.StringVar, color: str):
        blk = tk.Frame(parent, bg=C_NAVY)
        blk.pack(side=LEFT, padx=8)
        tk.Label(blk, textvariable=var, font=self.f_count,
                 fg=color, bg=C_NAVY).pack()
        tk.Label(blk, text=label, font=self.f_badge,
                 fg="#AABBD0", bg=C_NAVY).pack()

    # ── notebook --------------------------------------------------------------

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        for label, builder in [
            ("  SCAN EMBALLAGE  ", self._build_scan_tab),
            ("  HISTORIQUE  ",     self._build_history_tab),
            ("  PARAMÈTRES  ",     self._build_settings_tab),
        ]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=label)
            builder(frame)

    def _on_tab_changed(self, _event=None):
        idx = self.notebook.index(self.notebook.select())
        if idx == 0:
            self.entry.focus_set()
        elif idx == 1:
            self._refresh_history_table()

    # ── SCAN tab --------------------------------------------------------------

    def _build_scan_tab(self, parent: ttk.Frame):
        body = ttk.Frame(parent, padding=(24, 18))
        body.pack(fill=BOTH, expand=YES)

        # ── Section 01 : Identification
        self._section_title(body, "01", "IDENTIFICATION", C_NAVY)

        id_card = tk.Frame(body, bg=C_CARD, relief="flat")
        id_card.pack(fill=X, pady=(0, 14))
        tk.Frame(id_card, bg=C_NAVY, height=3).pack(fill=X)

        id_inner = tk.Frame(id_card, bg=C_CARD, padx=20, pady=16)
        id_inner.pack(fill=BOTH)

        tk.Label(id_inner, text="RÉFÉRENCE / CODE-BARRE GALIA",
                 font=self.f_section, fg=C_NAVY, bg=C_CARD).pack(anchor=W, pady=(0, 8))

        entry_wrap = tk.Frame(id_inner, bg=C_BORDER, padx=1, pady=1)
        entry_wrap.pack(fill=X)
        entry_inner = tk.Frame(entry_wrap, bg=C_SURFACE)
        entry_inner.pack(fill=X)

        tk.Label(entry_inner, text="▐▌",
                 font=tkfont.Font(family="Segoe UI", size=13),
                 fg=C_NAVY, bg=C_SURFACE, padx=10).pack(side=LEFT)

        self.entry = tk.Entry(
            entry_inner, font=self.f_entry,
            fg=C_TEXT, bg=C_SURFACE,
            insertbackground=C_LIME,
            relief="flat", bd=0, highlightthickness=0,
        )
        self.entry.pack(fill=X, side=LEFT, expand=YES, ipady=11, ipadx=6)
        self.entry.bind("<Return>",   self._on_scan)
        self.entry.bind("<FocusIn>",  lambda _: entry_wrap.config(bg=C_LIME))
        self.entry.bind("<FocusOut>", lambda _: entry_wrap.config(bg=C_BORDER))

        tk.Label(id_inner,
                 text="Scannez l'étiquette ou tapez la référence pièce  ↵ Entrée",
                 font=self.f_hint, fg=C_TEXT_M, bg=C_CARD, anchor=W,
                 ).pack(fill=X, pady=(6, 0))

        # ── Section 02 : Résultat
        self._section_title(body, "02", "RÉSULTAT", C_TEAL)

        self.result_card = tk.Frame(body, bg=C_IDLE_BG)
        self.result_card.pack(fill=X, pady=(0, 14))
        self.result_top_bar = tk.Frame(self.result_card, bg=C_IDLE, height=3)
        self.result_top_bar.pack(fill=X)

        result_inner = tk.Frame(self.result_card, bg=C_IDLE_BG, padx=20, pady=16)
        result_inner.pack(fill=BOTH)
        self._result_inner = result_inner

        badge_row = tk.Frame(result_inner, bg=C_IDLE_BG)
        badge_row.pack(fill=X, pady=(0, 8))
        self._badge_row = badge_row

        self.badge_var = tk.StringVar(value="EN ATTENTE")
        self.badge_lbl = tk.Label(badge_row, textvariable=self.badge_var,
                                  font=self.f_badge, fg="#FFFFFF", bg=C_IDLE,
                                  padx=8, pady=3)
        self.badge_lbl.pack(side=LEFT)

        self.ref_badge_var = tk.StringVar(value="")
        self.ref_badge_lbl = tk.Label(badge_row, textvariable=self.ref_badge_var,
                                      font=self.f_badge, fg=C_TEXT_S, bg=C_IDLE_BG,
                                      padx=8, pady=3)
        self.ref_badge_lbl.pack(side=LEFT, padx=(6, 0))

        self.result_var = tk.StringVar(value="En attente de scan…")
        self.result_lbl = tk.Label(result_inner, textvariable=self.result_var,
                                   font=self.f_result, fg=C_IDLE, bg=C_IDLE_BG,
                                   anchor=W)
        self.result_lbl.pack(fill=X)

        self.detail_var = tk.StringVar(value="")
        self.detail_lbl = tk.Label(result_inner, textvariable=self.detail_var,
                                   font=self.f_detail, fg=C_TEXT_S, bg=C_IDLE_BG,
                                   anchor=W)
        self.detail_lbl.pack(fill=X)

        # ── Section 03 : Photo
        self._section_title(body, "03", "PHOTO EMBALLAGE", C_SAGE)

        img_card = tk.Frame(body, bg=C_CARD)
        img_card.pack(fill=X)
        tk.Frame(img_card, bg=C_SAGE, height=3).pack(fill=X)

        self.img_inner = tk.Frame(img_card, bg=C_CARD, padx=20, pady=14)
        self.img_inner.pack(fill=BOTH)

        self.image_placeholder = tk.Label(
            self.img_inner,
            text="Aucune image — scannez une référence pour afficher la photo",
            font=self.f_hint, fg=C_TEXT_M, bg=C_CARD, pady=26,
        )
        self.image_placeholder.pack(fill=X)
        self.image_lbl = tk.Label(self.img_inner, bg=C_CARD)
        self.image_lbl.pack()

    # ── HISTORIQUE tab --------------------------------------------------------

    def _build_history_tab(self, parent: ttk.Frame):
        body = ttk.Frame(parent, padding=(24, 18))
        body.pack(fill=BOTH, expand=YES)

        self._section_title(body, "01", "HISTORIQUE DES SCANS", C_TEAL)

        # Button row with ttkbootstrap buttons
        btn_row = ttk.Frame(body)
        btn_row.pack(fill=X, pady=(0, 12))

        ttk.Button(btn_row, text="Exporter CSV", bootstyle="primary-outline",
                   command=self._export_history_csv).pack(side=LEFT)
        ttk.Button(btn_row, text="Effacer", bootstyle="danger-outline",
                   command=self._clear_history).pack(side=LEFT, padx=(8, 0))

        self.hist_count_var = tk.StringVar(value="0 scan(s)")
        ttk.Label(btn_row, textvariable=self.hist_count_var,
                  bootstyle="secondary", font=self.f_hint).pack(side=RIGHT)

        # Table
        table_wrap = tk.Frame(body, bg=C_TEAL, padx=0, pady=0)
        table_wrap.pack(fill=BOTH, expand=YES)
        tk.Frame(table_wrap, bg=C_TEAL, height=3).pack(fill=X)

        table_frame = tk.Frame(table_wrap, bg=C_CARD)
        table_frame.pack(fill=BOTH, expand=YES)

        cols = ("#", "Heure", "Référence scannée", "UC", "Statut")
        self.hist_tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse",
        )
        for col, width, stretch in [
            ("#",                 42,  False),
            ("Heure",             80,  False),
            ("Référence scannée", 220, True),
            ("UC",                160, False),
            ("Statut",            100, False),
        ]:
            self.hist_tree.heading(col, text=col)
            self.hist_tree.column(col, width=width, anchor=W, stretch=stretch)

        vsb = ttk.Scrollbar(table_frame, orient=VERTICAL,
                            command=self.hist_tree.yview, bootstyle="round")
        self.hist_tree.configure(yscrollcommand=vsb.set)
        self.hist_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        vsb.pack(side=RIGHT, fill=Y)

        self.hist_tree.tag_configure("found", foreground=C_SUCCESS)
        self.hist_tree.tag_configure("error", foreground=C_ERROR)
        self.hist_tree.tag_configure("warn",  foreground=C_WARN)

    def _refresh_history_table(self):
        self.hist_tree.delete(*self.hist_tree.get_children())
        for i, entry in enumerate(reversed(self._history), 1):
            tag = {"TROUVÉ": "found", "ERREUR": "error",
                   "INCOMPLET": "warn"}.get(entry["statut"], "")
            self.hist_tree.insert("", END, values=(
                i, entry["heure"], entry["scan_brut"],
                entry["uc"], entry["statut"],
            ), tags=(tag,))
        self.hist_count_var.set(f"{len(self._history)} scan(s)")

    def _export_history_csv(self):
        if not self._history:
            messagebox.showinfo("Export", "Aucun scan à exporter.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")],
            initialfile=f"historique_{datetime.now():%Y%m%d_%H%M}.csv",
            title="Exporter l'historique",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(
                f, fieldnames=["heure", "scan_brut", "ref_normee", "uc", "statut"]
            )
            writer.writeheader()
            writer.writerows(self._history)
        messagebox.showinfo("Export réussi", f"Fichier enregistré :\n{path}")

    def _clear_history(self):
        if not self._history:
            return
        if messagebox.askyesno("Effacer", "Vider tout l'historique des scans ?"):
            self._history.clear()
            self._refresh_history_table()

    # ── PARAMÈTRES tab --------------------------------------------------------

    def _build_settings_tab(self, parent: ttk.Frame):
        body = ttk.Frame(parent, padding=(24, 18))
        body.pack(fill=BOTH, expand=YES)

        self._section_title(body, "01", "SOURCE DE DONNÉES", C_NAVY)

        card = tk.Frame(body, bg=C_CARD)
        card.pack(fill=X, pady=(0, 16))
        tk.Frame(card, bg=C_NAVY, height=3).pack(fill=X)

        form = ttk.Frame(card, padding=(20, 18))
        form.pack(fill=BOTH)

        self._p_xlsx   = tk.StringVar(value=str(self.xlsx_path))
        self._p_sheet  = tk.StringVar(value=self.sheet_name)
        self._p_refcol = tk.StringVar(value=self._ref_col)
        self._p_uccol  = tk.StringVar(value=self._uc_col)

        self._param_field(form, "Fichier Excel :",      self._p_xlsx,
                          browse=self._browse_xlsx)
        self._param_field(form, "Feuille :",            self._p_sheet)
        self._param_field(form, "Colonne Référence :",  self._p_refcol)
        self._param_field(form, "Colonne UC :",         self._p_uccol)

        btn_row = ttk.Frame(form)
        btn_row.pack(fill=X, pady=(18, 0))

        ttk.Button(btn_row, text="Recharger la base",
                   bootstyle="primary",
                   command=self._reload_data).pack(side=LEFT)

        self._param_status_var = tk.StringVar(value="")
        self._param_status_lbl = ttk.Label(
            form, textvariable=self._param_status_var,
            font=self.f_hint, bootstyle="success",
        )
        self._param_status_lbl.pack(fill=X, pady=(10, 0))

    def _param_field(self, parent: ttk.Frame, label_text: str,
                     var: tk.StringVar, browse=None):
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=5)

        ttk.Label(row, text=label_text, font=self.f_section,
                  width=22, anchor=W).pack(side=LEFT)

        ent = ttk.Entry(row, textvariable=var, font=("Segoe UI", 9),
                        bootstyle="primary")
        ent.pack(side=LEFT, fill=X, expand=YES, ipady=3)

        if browse:
            ttk.Button(row, text="…", bootstyle="secondary-outline",
                       width=3, command=browse).pack(side=LEFT, padx=(6, 0))

    def _browse_xlsx(self):
        path = filedialog.askopenfilename(
            filetypes=[("Excel", "*.xlsx *.xls *.xlsm"), ("Tous", "*.*")],
            title="Choisir le fichier Excel",
        )
        if path:
            self._p_xlsx.set(path)

    def _reload_data(self):
        xlsx    = Path(self._p_xlsx.get().strip())
        sheet   = self._p_sheet.get().strip()
        ref_col = self._p_refcol.get().strip()
        uc_col  = self._p_uccol.get().strip()

        try:
            mapping, original_refs, details_map = load_mapping(
                xlsx, sheet, ref_col, uc_col
            )
        except (FileNotFoundError, ValueError) as exc:
            self._param_status_var.set(f"✗  {exc}")
            self._param_status_lbl.configure(bootstyle="danger")
            return

        self.mapping = mapping
        self.original_refs = original_refs
        self.details_map = details_map
        self.known_norm = set(mapping.keys())
        self.xlsx_path = xlsx
        self.sheet_name = sheet
        self._ref_col = ref_col
        self._uc_col = uc_col

        self.kpi_refs_var.set(str(len(mapping)))
        self._param_status_var.set(
            f"✓  Base rechargée — {len(mapping)} références chargées"
        )
        self._param_status_lbl.configure(bootstyle="success")
        self.status_var.set(f"Base rechargée  —  {len(mapping)} références")

    # ── section header helper -------------------------------------------------

    def _section_title(self, parent, number: str, title: str, color: str):
        row = tk.Frame(parent, bg=C_BG)
        row.pack(fill=X, pady=(0, 8))

        tk.Label(row, text=f" {number} ", font=self.f_badge,
                 fg=C_CARD, bg=color, padx=4, pady=2).pack(side=LEFT)
        tk.Label(row, text=f"  {title}", font=self.f_section,
                 fg=color, bg=C_BG).pack(side=LEFT)
        tk.Frame(row, bg=C_BORDER, height=1).pack(
            side=LEFT, fill=X, expand=YES, padx=(12, 0), pady=6)

    # ── statusbar -------------------------------------------------------------

    def _build_statusbar(self, ref_count: int):
        tk.Frame(self, bg=C_BORDER, height=1).pack(fill=X)

        bar = tk.Frame(self, bg=C_TOPBAR, height=30)
        bar.pack(fill=X, side=BOTTOM)
        bar.pack_propagate(False)

        self.status_var = tk.StringVar(
            value=f"Prêt  —  {ref_count} références chargées"
        )
        tk.Label(bar, textvariable=self.status_var,
                 font=self.f_topbar, fg=C_TEXT_S, bg=C_TOPBAR, anchor=W,
                 ).pack(side=LEFT, padx=14, fill=Y)

        right = tk.Frame(bar, bg=C_TOPBAR)
        right.pack(side=RIGHT, padx=14, fill=Y)
        tk.Label(right, text="●", font=self.f_topbar,
                 fg=C_GREEN, bg=C_TOPBAR).pack(side=LEFT)
        tk.Label(right, text=" TRIGO SAS  |  Qualité & Logistique",
                 font=self.f_topbar, fg=C_TEXT_M, bg=C_TOPBAR).pack(side=LEFT)

    # ── scan logic ------------------------------------------------------------

    def _set_result(self, text: str, badge: str, color: str, bg: str,
                    detail: str = "", ref: str = ""):
        self.result_card.config(bg=bg)
        self.result_top_bar.config(bg=color)
        self._result_inner.config(bg=bg)
        self._badge_row.config(bg=bg)

        self.badge_var.set(badge)
        self.badge_lbl.config(fg="#FFFFFF", bg=color)

        self.ref_badge_var.set(f"  {ref}" if ref else "")
        self.ref_badge_lbl.config(fg=C_TEXT_S, bg=bg)

        self.result_var.set(text)
        self.result_lbl.config(fg=color, bg=bg)
        self.detail_var.set(detail)
        self.detail_lbl.config(fg=C_TEXT_S, bg=bg)

    def _on_scan(self, *_):
        scanned = self.entry.get().strip()
        self.entry.delete(0, END)

        self.image_lbl.config(image="")
        self.image_lbl.image = None
        self.image_placeholder.config(
            text="Aucune image — scannez une référence pour afficher la photo",
            fg=C_TEXT_M,
        )
        self.image_placeholder.pack(fill=X)

        if not scanned:
            return

        self._scan_count += 1
        self.kpi_scans_var.set(str(self._scan_count))

        nref = extract_reference(scanned, self.known_norm, self.original_refs)

        if not nref:
            self._set_result(
                "Référence non reconnue", "ERREUR", C_ERROR, C_ERROR_BG,
                detail="Impossible d'extraire une référence connue du scan.",
            )
            self.status_var.set("  ✗  Référence non reconnue dans la base")
            self._history.append({
                "heure": datetime.now().strftime("%H:%M:%S"),
                "scan_brut": scanned, "ref_normee": "",
                "uc": "", "statut": "ERREUR",
            })
            return

        uc = self.mapping.get(nref)
        if uc:
            self._set_result(
                f"{uc}", "TROUVÉ", C_SUCCESS, C_SUCCESS_BG,
                detail="Emballage UC identifié avec succès",
                ref=f"Réf : {nref}",
            )
            self.status_var.set(f"  ✓  {nref}  →  {uc}")
            self._show_image(uc)
            self._history.append({
                "heure": datetime.now().strftime("%H:%M:%S"),
                "scan_brut": scanned, "ref_normee": nref,
                "uc": uc, "statut": "TROUVÉ",
            })
        else:
            self._set_result(
                "UC non défini", "INCOMPLET", C_WARN, C_WARN_BG,
                detail=f"Référence {nref} présente mais aucun emballage assigné.",
                ref=f"Réf : {nref}",
            )
            self.status_var.set(f"  ⚠  {nref}  →  emballage manquant")
            self._history.append({
                "heure": datetime.now().strftime("%H:%M:%S"),
                "scan_brut": scanned, "ref_normee": nref,
                "uc": "", "statut": "INCOMPLET",
            })

    def _show_image(self, uc: str):
        img_path = find_image(uc)
        if img_path is None:
            self.image_placeholder.config(
                text=f"Aucune photo disponible pour l'emballage :  {uc}",
                fg=C_WARN,
            )
            self.image_placeholder.pack(fill=X)
            return

        self.image_placeholder.pack_forget()
        pil_img = Image.open(img_path)
        pil_img.thumbnail((480, 290), Image.LANCZOS)
        photo = ImageTk.PhotoImage(pil_img)
        self.image_lbl.config(image=photo, bg=C_CARD)
        self.image_lbl.image = photo


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    try:
        mapping, original_refs, details_map, _ = load_mapping()
    except (FileNotFoundError, ValueError) as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("TRIGO — Erreur", str(exc))
        root.destroy()
        return

    BoxLookupApp(
        mapping, original_refs, details_map,
        len(mapping), DEFAULT_XLSX, DEFAULT_SHEET,
        REF_COL, UC_COL,
    ).mainloop()


if __name__ == "__main__":
    main()
