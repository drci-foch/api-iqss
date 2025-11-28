"""
Générateur Excel pour les indicateurs de Lettres de Liaison
Version 1.0 - Adapté du générateur PowerPoint
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime
from typing import Dict, List, Optional

# --------------------------------------------------------------------
#  CONSTANTES GLOBALES
# --------------------------------------------------------------------

# Couleurs Hôpital Foch (palette officielle)
FOCH_BLUE = "005293"
FOCH_GREEN = "6AA84F"
FOCH_LIGHT_BLUE = "9BC2E6"
FOCH_DARK_BLUE = "003366"
FOCH_GRAY = "595959"

# Couleurs indicateurs
COLOR_GREEN = "92D050"
COLOR_YELLOW = "FFC000"
COLOR_ORANGE = "FF7F27"
COLOR_RED = "FF0000"
COLOR_GRAY = "D9D9D9"
COLOR_WHITE = "FFFFFF"
COLOR_BLACK = "000000"


# --------------------------------------------------------------------
#  FONCTIONS UTILITAIRES DE STYLE
# --------------------------------------------------------------------


def get_color_by_threshold(value: float, excellent=95, good=85, medium=70) -> str:
    """Obtenir la couleur selon les seuils"""
    if pd.isna(value):
        return COLOR_GRAY
    if value >= excellent:
        return COLOR_GREEN
    elif value >= good:
        return COLOR_YELLOW
    elif value >= medium:
        return COLOR_ORANGE
    else:
        return COLOR_RED


def apply_cell_style(
    cell,
    font_size=11,
    bold=False,
    font_color=COLOR_BLACK,
    bg_color=None,
    alignment_h="center",
    alignment_v="center",
    border=True,
):
    """Appliquer un style à une cellule"""
    cell.font = Font(name="Calibri", size=font_size, bold=bold, color=font_color)
    cell.alignment = Alignment(
        horizontal=alignment_h, vertical=alignment_v, wrap_text=True
    )

    if bg_color:
        cell.fill = PatternFill(
            start_color=bg_color, end_color=bg_color, fill_type="solid"
        )

    if border:
        thin_border = Border(
            left=Side(style="thin", color=FOCH_GRAY),
            right=Side(style="thin", color=FOCH_GRAY),
            top=Side(style="thin", color=FOCH_GRAY),
            bottom=Side(style="thin", color=FOCH_GRAY),
        )
        cell.border = thin_border


def set_column_widths(ws, widths):
    """Définir les largeurs de colonnes"""
    for col_idx, width in enumerate(widths, start=1):
        ws.column_dimensions[chr(64 + col_idx)].width = width


# --------------------------------------------------------------------
#  FEUILLES EXCEL
# --------------------------------------------------------------------


def create_sheet_resume(
    wb: Workbook, stats_validation: Dict, stats_diffusion: Dict, period: str
):
    """Feuille 1 : Résumé global"""
    ws = wb.create_sheet("Résumé Global", 0)

    # En-tête
    ws.merge_cells("A1:D1")
    cell = ws["A1"]
    cell.value = f"RÉSUMÉ GLOBAL - {period}"
    apply_cell_style(
        cell, font_size=16, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_BLUE
    )

    # Sous-titre
    ws.merge_cells("A2:D2")
    cell = ws["A2"]
    cell.value = "Indicateurs prioritaires : délai de validation et diffusion des lettres de liaison"
    apply_cell_style(cell, font_size=12, bold=True, bg_color=FOCH_LIGHT_BLUE)

    # Espace
    ws.row_dimensions[3].height = 5

    # En-têtes du tableau
    headers = ["Indicateur", "Valeur", "Objectif", "Statut"]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        apply_cell_style(
            cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE
        )

    # Données
    data_rows = [
        (
            "Nombre total de séjours",
            f"{stats_validation['total_sejours_all']:,}".replace(",", " "),
            "-",
            "📊",
            None,
        ),
        (
            "Taux de validation",
            f"{stats_validation['pct_sejours_validees_all']:.1f}%",
            "≥ 95%",
            "✅"
            if stats_validation["pct_sejours_validees_all"] >= 95
            else "⚠️"
            if stats_validation["pct_sejours_validees_all"] >= 85
            else "❌",
            get_color_by_threshold(
                stats_validation["pct_sejours_validees_all"], 95, 85, 70
            ),
        ),
        (
            "Taux validation J0",
            f"{stats_validation['taux_validation_j0_over_sejours_all']:.1f}%",
            "≥ 90%",
            "✅"
            if stats_validation["taux_validation_j0_over_sejours_all"] >= 90
            else "⚠️"
            if stats_validation["taux_validation_j0_over_sejours_all"] >= 80
            else "❌",
            get_color_by_threshold(
                stats_validation["taux_validation_j0_over_sejours_all"], 90, 80, 70
            ),
        ),
        (
            "Taux diffusion / validation",
            f"{stats_diffusion['pct_ll_diffusees_over_validees_all']:.1f}%",
            "≥ 90%",
            "✅"
            if stats_diffusion["pct_ll_diffusees_over_validees_all"] >= 90
            else "⚠️"
            if stats_diffusion["pct_ll_diffusees_over_validees_all"] >= 80
            else "❌",
            get_color_by_threshold(
                stats_diffusion["pct_ll_diffusees_over_validees_all"], 90, 80, 70
            ),
        ),
    ]

    for row_idx, (indicator, value, objective, status, color) in enumerate(
        data_rows, start=5
    ):
        # Indicateur
        cell = ws.cell(row=row_idx, column=1, value=indicator)
        apply_cell_style(cell, bold=True, alignment_h="left")

        # Valeur
        cell = ws.cell(row=row_idx, column=2, value=value)
        apply_cell_style(cell, bg_color=color if color else None)

        # Objectif
        cell = ws.cell(row=row_idx, column=3, value=objective)
        apply_cell_style(cell)

        # Statut
        cell = ws.cell(row=row_idx, column=4, value=status)
        apply_cell_style(cell, font_size=14)

    # Largeurs de colonnes
    set_column_widths(ws, [35, 15, 15, 10])

    # Ajuster les hauteurs
    for row in range(1, 10):
        ws.row_dimensions[row].height = 25


def create_sheet_validation_detail(
    wb: Workbook, stats_validation: Dict, stats_diffusion: Dict, period: str
):
    """Feuille 2 : Tableau détaillé par spécialité"""
    ws = wb.create_sheet("Détail par Spécialité")

    # En-tête
    ws.merge_cells("A1:K1")
    cell = ws["A1"]
    cell.value = f"Taux de validation et diffusion des LL - SÉJOURS > 24H - {period}"
    apply_cell_style(
        cell, font_size=14, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_BLUE
    )

    # En-têtes du tableau
    headers = [
        "SPÉCIALITÉS",
        "Nb total de séjours",
        "Nb LL validées",
        "% LL validées",
        "Taux de validation à J0 / séjours",
        "Délai validation moyenne)",
        "Nb LL diffusées",
        "% des validées",
        "% des séjours",
        "Taux de diffusion à J0 de la validation",
        "Délai diffusions / validation",
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=header)
        apply_cell_style(
            cell, bold=True, font_color=FOCH_DARK_BLUE, bg_color=FOCH_LIGHT_BLUE
        )

    # Données par spécialité
    specialites_validation = stats_validation.get("par_specialite_all", [])
    specialites_diffusion = stats_diffusion.get("par_specialite", [])
    diffusion_dict = {spe["specialite"]: spe for spe in specialites_diffusion}

    for row_idx, spe in enumerate(specialites_validation, start=3):
        spe_diff = diffusion_dict.get(spe["specialite"], {})

        # Couleur de ligne alternée
        bg_color = COLOR_WHITE if row_idx % 2 == 1 else "F2F2F2"

        # Spécialité
        cell = ws.cell(row=row_idx, column=1, value=spe["specialite"])
        apply_cell_style(
            cell,
            bold=True,
            alignment_h="left",
            bg_color=bg_color,
            font_color=FOCH_DARK_BLUE,
        )

        # Nb total
        cell = ws.cell(row=row_idx, column=2, value=spe["total_sejours"])
        apply_cell_style(cell, bg_color=bg_color)

        # LL valid.
        cell = ws.cell(row=row_idx, column=3, value=spe["nb_sejours_valides"])
        apply_cell_style(cell, bg_color=bg_color)

        # % val.
        pct_val = spe["pct_sejours_validees"]
        cell = ws.cell(row=row_idx, column=4, value=f"{pct_val:.1f}%")
        color_val = get_color_by_threshold(pct_val, 95, 85, 70)
        apply_cell_style(cell, bg_color=color_val)

        # % J0
        pct_j0 = spe["taux_validation_j0_over_sejours"]
        cell = ws.cell(row=row_idx, column=5, value=f"{pct_j0:.1f}%")
        color_j0 = get_color_by_threshold(pct_j0, 90, 80, 70)
        apply_cell_style(cell, bg_color=color_j0)

        # Délai val.
        delai_val = spe.get("delai_moyen_validation", 0)
        if delai_val is None or (isinstance(delai_val, float) and pd.isna(delai_val)):
            delai_val = 0
        cell = ws.cell(row=row_idx, column=6, value=f"{delai_val:.1f}")
        apply_cell_style(cell, bg_color=bg_color)

        # LL diff.
        nb_diff = spe_diff.get("nb_ll_diffusees", 0)
        cell = ws.cell(row=row_idx, column=7, value=nb_diff)
        apply_cell_style(cell, bg_color=bg_color)

        # % diff.
        pct_diff = spe_diff["pct_ll_diffusees_over_validees"]
        cell = ws.cell(row=row_idx, column=8, value=f"{pct_diff:.1f}%")
        color_diff = get_color_by_threshold(pct_diff, 90, 75, 60)
        apply_cell_style(cell, bg_color=color_diff)

        # % des séjours
        pct_diff_sejours = spe_diff["pct_ll_diffusees_over_sejours"]
        cell = ws.cell(row=row_idx, column=9, value=f"{pct_diff_sejours:.1f}%")
        color_diff_global = get_color_by_threshold(pct_diff_sejours, 90, 75, 60)
        apply_cell_style(cell, bold=True, bg_color=color_diff_global)

        # Taux de diffusion à J0 de la validation
        pct_diff_validation = spe_diff["taux_diffusion_J0_validation"]
        cell = ws.cell(row=row_idx, column=10, value=f"{pct_diff_validation:.1f}%")
        color_diff_global = get_color_by_threshold(pct_diff_validation, 90, 75, 60)
        apply_cell_style(cell, bold=True, bg_color=color_diff_global)

        # Délai diff. / validation
        delai_diff_validation = spe_diff["delai_diffusion_validation"]
        if delai_diff_validation is None or (
            isinstance(delai_diff_validation, float) and pd.isna(delai_diff_validation)
        ):
            delai_diff_validation = 0
        cell = ws.cell(row=row_idx, column=11, value=f"{delai_diff_validation:.1f}")
        apply_cell_style(
            cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE
        )

    # Ligne TOTAL FOCH
    total_row = len(specialites_validation) + 3

    cell = ws.cell(row=total_row, column=1, value="TOTAL FOCH")
    apply_cell_style(
        cell,
        bold=True,
        font_color=COLOR_WHITE,
        bg_color=FOCH_DARK_BLUE,
        alignment_h="left",
    )

    # Nb total de séjours
    cell = ws.cell(
        row=total_row,
        column=2,
        value=f"{stats_validation['total_sejours_all']:,}".replace(",", " "),
    )
    apply_cell_style(cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE)

    # Nb LL validées
    cell = ws.cell(
        row=total_row,
        column=3,
        value=f"{stats_validation['nb_sejours_valides_all']:,}".replace(",", " "),
    )
    apply_cell_style(cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE)

    # % LL validées
    pct_global = stats_validation["pct_sejours_validees_all"]
    cell = ws.cell(row=total_row, column=4, value=f"{pct_global:.1f}%")
    color_global = get_color_by_threshold(pct_global, 95, 85, 70)
    apply_cell_style(cell, bold=True, bg_color=color_global)

    # Taux validation à J0 / séjours
    pct_j0_global = stats_validation["taux_validation_j0_over_sejours_all"]
    cell = ws.cell(row=total_row, column=5, value=f"{pct_j0_global:.1f}%")
    color_j0_global = get_color_by_threshold(pct_j0_global, 90, 80, 70)
    apply_cell_style(cell, bold=True, bg_color=color_j0_global)

    # Délai val. moyenne
    delai_global = stats_validation.get("delai_moyen_validation_all", 0)
    if delai_global is None or (
        isinstance(delai_global, float) and pd.isna(delai_global)
    ):
        delai_global = 0
    cell = ws.cell(row=total_row, column=6, value=f"{delai_global:.1f}")
    apply_cell_style(cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE)

    # Nb LL diffusées
    total_diff = stats_diffusion.get("nb_ll_diffusees_all", 0)
    cell = ws.cell(row=total_row, column=7, value=f"{total_diff:,}".replace(",", " "))
    apply_cell_style(cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE)

    # % des validées
    pct_diff_global = stats_diffusion.get("pct_ll_diffusees_over_validees_all", 0)
    cell = ws.cell(row=total_row, column=8, value=f"{pct_diff_global:.1f}%")
    color_diff_global = get_color_by_threshold(pct_diff_global, 90, 75, 60)
    apply_cell_style(cell, bold=True, bg_color=color_diff_global)

    # % des séjours
    pct_diff_global = stats_diffusion.get("pct_ll_diffusees_over_sejours_all", 0)
    cell = ws.cell(row=total_row, column=9, value=f"{pct_diff_global:.1f}%")
    color_diff_global = get_color_by_threshold(pct_diff_global, 90, 75, 60)
    apply_cell_style(cell, bold=True, bg_color=color_diff_global)

    # Taux de diffusion à J0 de la validation
    pct_diff_global = stats_diffusion.get("taux_diffusion_J0_validation_all", 0)
    cell = ws.cell(row=total_row, column=10, value=f"{pct_diff_global:.1f}%")
    color_diff_global = get_color_by_threshold(pct_diff_global, 90, 75, 60)
    apply_cell_style(cell, bold=True, bg_color=color_diff_global)

    # Délai diff. / validation
    delai_diff_global = stats_diffusion.get("delai_diffusion_validation_all", 0)
    if delai_diff_global is None or (
        isinstance(delai_diff_global, float) and pd.isna(delai_diff_global)
    ):
        delai_diff_global = 0
    cell = ws.cell(row=total_row, column=11, value=f"{delai_diff_global:.1f}")
    apply_cell_style(cell, bold=True, font_color=COLOR_WHITE, bg_color=FOCH_DARK_BLUE)

    # Largeurs de colonnes
    set_column_widths(ws, [25, 10, 10, 10, 10, 12, 10, 10, 10, 10, 12])

    # Hauteur des lignes
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 35


# --------------------------------------------------------------------
#  GENERATION DE L'EXCEL
# --------------------------------------------------------------------


def generate_excel(
    stats_validation: Dict,
    stats_diffusion: Dict,
    output_path: str,
    period: str,
) -> None:
    """Générer le fichier Excel avec toutes les feuilles"""

    wb = Workbook()

    # Supprimer la feuille par défaut
    if "Sheet" in wb.sheetnames:
        wb.remove(wb["Sheet"])

    # Créer les feuilles
    create_sheet_resume(wb, stats_validation, stats_diffusion, period)
    create_sheet_validation_detail(wb, stats_validation, stats_diffusion, period)
    # create_sheet_methodologie(wb)
    # create_sheet_instructions(wb)

    # Sauvegarder
    wb.save(output_path)
    print(f"✅ Excel généré : {output_path}")
    print(f"   {len(wb.sheetnames)} feuilles | Formatage harmonisé")


if __name__ == "__main__":
    # Exemple de test
    test_stats_validation = {
        "total_sejours_all": 1769,
        "nb_sejours_valides_all": 1603,
        "pct_sejours_validees_all": 90.6,
        "taux_validation_j0_over_sejours_all": 70.7,
        "delai_moyen_validation_all": 0.8,
        "par_specialite_all": [
            {
                "specialite": "VASCULAIRE",
                "total_sejours": 128,
                "nb_sejours_valides": 117,
                "pct_sejours_validees": 91.4,
                "taux_validation_j0_over_sejours": 72.6,
                "delai_moyen_validation": 0.8,
            },
            {
                "specialite": "NEUROCHIRURGIE",
                "total_sejours": 145,
                "nb_sejours_valides": 140,
                "pct_sejours_validees": 96.5,
                "taux_validation_j0_over_sejours": 85.0,
                "delai_moyen_validation": 0.5,
            },
            {
                "specialite": "CARDIOLOGIE",
                "total_sejours": 197,
                "nb_sejours_valides": 180,
                "pct_sejours_validees": 91.4,
                "taux_validation_j0_over_sejours": 75.5,
                "delai_moyen_validation": 0.7,
            },
        ],
    }

    test_stats_diffusion = {
        "nb_ll_diffusees_all": 1603,
        "pct_ll_diffusees_over_validees_all": 100.0,
        "delai_diffusion_validation_all": 0.8,
        "par_specialite": [
            {
                "specialite": "VASCULAIRE",
                "nb_ll_diffusees": 117,
                "pct_ll_diffusees_over_validees": 100.0,
                "delai_diffusion_validation": 0.8,
            },
            {
                "specialite": "NEUROCHIRURGIE",
                "nb_ll_diffusees": 140,
                "pct_ll_diffusees_over_validees": 100.0,
                "delai_diffusion_validation": 0.5,
            },
            {
                "specialite": "CARDIOLOGIE",
                "nb_ll_diffusees": 180,
                "pct_ll_diffusees_over_validees": 100.0,
                "delai_diffusion_validation": 0.7,
            },
        ],
    }

    generate_excel(
        test_stats_validation,
        test_stats_diffusion,
        "indicateurs_lettres_liaison.xlsx",
        "01/01 au 31/07/2025 (TEST)",
    )
    print("\n✅ Test terminé !")
