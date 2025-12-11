import pandas as pd
from config import settings
from typing import Dict, List, Optional, Tuple

from database import get_sejours_data, get_documents_data
from data_processing import (
    merge_sejours_documents,
    calculate_validation_stats,
    calculate_diffusion_stats,
)


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
