import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

DEFAULT_XLSX  = Path(__file__).with_name("Liste emballages ref Trigo.xlsx")
DEFAULT_SHEET = "Feuil3"
REF_COL       = "Reference"
UC_COL        = "UC"


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
    base = Path(__file__).parent / "box_images"
    exact = base / f"{uc}.jpg"
    if exact.exists():
        return exact
    uc_norm = normalize(uc)
    for img in base.glob("*.jpg"):
        if normalize(img.stem) == uc_norm:
            return img
    return None
