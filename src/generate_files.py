import pandas as pd
from config import settings
from typing import Dict, List, Optional, Tuple

from database import get_sejours_data, get_documents_data
from data_processing import (
    merge_sejours_documents,
    calculate_validation_stats,
    calculate_diffusion_stats,
)


def export_requete_to_excel(
    data: pd.DataFrame, stats_validation: Dict, stats_diffusion: Dict, output_path: str
) -> None:
    """
    Exporte les données et statistiques vers Excel avec plusieurs feuilles

    Args:
        data: DataFrame avec toutes les données des séjours
        stats_validation: Dictionnaire des statistiques de validation
        stats_diffusion: Dictionnaire des statistiques de diffusion
        output_path: Chemin du fichier Excel de sortie
    """
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Feuille 1: Données détaillées
            # Sélectionner les colonnes les plus pertinentes
            cols_to_export = [
                "pat_ipp",
                "sej_id",
                "sej_ent",
                "sej_sor",
                "sej_uf",
                "doc_id",
                "doc_spe",
                "doc_libelle",
                "doc_val",
                "del_sorval",
                "date_diffusion",
                "sej_classe",
            ]

            # Ajouter sej_spe_final si elle existe
            if "sej_spe_final" in data.columns:
                cols_to_export.append("sej_spe_final")

            # Filtrer les colonnes qui existent réellement
            cols_available = [col for col in cols_to_export if col in data.columns]

            data[cols_available].to_excel(writer, sheet_name="Donnees", index=False)

    except Exception as e:
        print(f"Erreur lors de l'export Excel : {e}")
        raise


def generate_report_data(
    start_date: Optional[List[str]] = None,
    end_date: Optional[List[str]] = None,
    sejour_list: Optional[List[str]] = None,
    matrice_path: Optional[str] = None,  # Permettre de passer un chemin personnalisé
) -> Tuple[pd.DataFrame, Dict, Dict]:
    """
    Génère les données complètes du rapport selon la méthodologie IQL

    Args:
        start_date: Date de début (format YYYY-MM-DD)
        end_date: Date de fin (format YYYY-MM-DD)
        sejour_list: Liste optionnelle de numéros de séjour spécifiques
        matrice_path: Chemin vers la matrice de spécialité

    Returns:
        Tuple contenant:
        - DataFrame avec toutes les données classifiées
        - Dict avec statistiques de validation
        - Dict avec statistiques de diffusion
    """

    # Si matrice_path n'est pas fourni, utiliser celui des settings
    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH
    else:
        print(f"Utilisation du chemin fourni: {matrice_path}")

    # 1. Récupérer les données des séjours (GAM)

    sejours = get_sejours_data(start_date, end_date, sejour_list)

    # 2. Récupérer les données des documents (EASILY)
    documents = get_documents_data(start_date, end_date)

    # 3. Fusionner les données

    data = merge_sejours_documents(sejours, documents)

    # 5. Calculer les statistiques de validation

    stats_validation = calculate_validation_stats(data, matrice_path=matrice_path)

    # 6. Calculer les statistiques de diffusion

    stats_diffusion = calculate_diffusion_stats(data, matrice_path=matrice_path)

    return data, stats_validation, stats_diffusion
