"""
Module de traitement et d'analyse des données
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import unicodedata
from database import get_sejours_data, get_documents_data


def load_ufum_mapping() -> pd.DataFrame:
    """
    Charger la correspondance UF -> Spécialité
    À adapter selon le fichier de référence
    """
    # À remplacer par le chargement du fichier CSV réel
    # Pour l'instant, retourne un DataFrame vide avec la structure attendue
    return pd.DataFrame(columns=["sej_uf", "doc_key", "sej_spe"])


# def merge_sejours_documents(
#     sejours: pd.DataFrame, documents: pd.DataFrame, ufum: pd.DataFrame
# ) -> pd.DataFrame:
#     """
#     Fusionner les séjours avec les documents et calculer les délais

#     Args:
#         sejours: DataFrame des séjours
#         documents: DataFrame des documents
#         ufum: DataFrame de mapping UF -> Spécialité

#     Returns:
#         DataFrame fusionné avec les délais calculés
#     """
#     # Jointure sur pat_ipp
#     merged = sejours.merge(documents, on="pat_ipp", how="left")

#     # Jointure sur sej_uf pour obtenir sej_spe
#     merged = merged.merge(ufum, on="sej_uf", how="left")

#     # Conversion des dates en datetime si nécessaire
#     merged["sej_sor"] = pd.to_datetime(merged["sej_sor"])
#     merged["sej_ent"] = pd.to_datetime(merged["sej_ent"])
#     merged["doc_val"] = pd.to_datetime(merged["doc_val"])
#     merged["doc_cre"] = pd.to_datetime(merged["doc_cre"])
#     merged["doc_creamere"] = pd.to_datetime(merged["doc_creamere"])

#     # Calcul du délai sortie-validation
#     def calculate_delay(row):
#         """Calcule le délai selon les règles métier"""
#         if pd.isna(row["doc_val"]):
#             return np.nan

#         # Vérification des conditions
#         condition1 = row["doc_val"] >= row["sej_ent"]
#         condition2 = row["doc_val"] >= (row["sej_sor"] - timedelta(days=3))

#         # Condition sur doc_creamere
#         condition3 = pd.isna(row["doc_creamere"]) or (
#             row["doc_creamere"] <= row["sej_sor"]
#         )

#         # Condition sur doc_cre
#         condition4 = row["doc_cre"] >= row["sej_ent"]

#         if condition1 and condition2 and condition3 and condition4:
#             return (row["doc_val"] - row["sej_sor"]).days

#         return np.nan

#     merged["del_sorval"] = merged.apply(calculate_delay, axis=1)

#     # Tri et sélection du meilleur document par séjour
#     merged["spe_na"] = merged["sej_spe"].isna()
#     merged = merged.sort_values(["sej_id", "spe_na", "del_sorval"])
#     merged["del_row"] = merged.groupby("sej_id").cumcount() + 1

#     # Garder seulement le premier document par séjour
#     result = merged[merged["del_row"] == 1].copy()

#     # Calcul du délai ajusté (>=0)
#     def adjust_delay(row):
#         if (
#             pd.isna(row["del_sorval"])
#             or np.isinf(row["del_sorval"])
#             or pd.isna(row["sej_spe"])
#         ):
#             return np.nan
#         return max(0, row["del_sorval"])

#     result["del_val"] = result.apply(adjust_delay, axis=1)

#     # Classification des séjours
#     def classify_sejour(delay):
#         if pd.isna(delay):
#             return "sansLL"
#         elif delay == 0:
#             return "0j"
#         else:
#             return "1j+"

#     result["sej_classe"] = result["del_val"].apply(classify_sejour)

#     return result


def normalize_text(text):
    """Normalise le texte: majuscules, sans accents"""
    if pd.isna(text):
        return None
    text = str(text).upper().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )
    return text


def load_matrice_specialite(
    matrice_path: str = "data/db/iqss_ll_ufum3.csv",
) -> pd.DataFrame:
    """Charge et prépare la matrice de spécialité"""
    matrice = pd.read_csv(matrice_path, sep=";", dtype={"sej_uf": str})
    matrice["doc_key_norm"] = matrice["doc_key"].apply(normalize_text)
    # Supprimer les doublons (garder la première occurrence)
    matrice = matrice.drop_duplicates(subset=["sej_uf", "doc_key_norm"], keep="first")
    return matrice


def create_doc_key(libelle: str) -> str:
    """
    Créer une clé de document à partir du libellé
    Simplifie et normalise le libellé du document
    """
    if pd.isna(libelle):
        return ""

    # Normaliser
    key = str(libelle).lower().strip()

    # Supprimer les patterns inutiles
    patterns_to_remove = [
        "cr lettre de liaison",
        "lettre de liaison",
        "cr",
        "foch",
        "hdj",
        "cs",
        "\.",
    ]

    for pattern in patterns_to_remove:
        key = key.replace(pattern, "")

    key = key.strip()
    return key


def calculate_validation_stats(
    df: pd.DataFrame, matrice_path: str = "data/db/iqss_ll_ufum3.csv"
) -> Dict:
    """
    Calcule les statistiques de validation selon la méthodologie IQL

    Indicateurs HAS:
    1. % séjours avec LL retrouvée (classes "0j" + "1j+")
    2. % séjours avec LL datée du jour de la sortie (classe "0j")

    Args:
        df: DataFrame contenant les séjours et documents
        matrice_path: Chemin vers la matrice de spécialité

    Returns:
        Dictionnaire contenant les statistiques globales et par spécialité
    """
    # Classifier les séjours
    df = classify_sejours_iql(df, matrice_path)

    # Statistiques globales
    total_sejours = len(df)
    sejours_avec_ll = len(df[df["sej_classe"].isin(["0j", "1j+"])])
    sejours_j0 = len(df[df["sej_classe"] == "0j"])
    sejours_j1plus = len(df[df["sej_classe"] == "1j+"])
    sejours_sans_ll = len(df[df["sej_classe"] == "sansLL"])

    # Taux
    taux_ll_retrouvee = (
        (sejours_avec_ll / total_sejours * 100) if total_sejours > 0 else 0
    )
    taux_ll_j0 = (sejours_j0 / total_sejours * 100) if total_sejours > 0 else 0

    # Délais (uniquement pour séjours avec LL)
    df_avec_ll = df[df["sej_classe"].isin(["0j", "1j+"])]
    delai_moyen = df_avec_ll["del_sorval"].mean() if len(df_avec_ll) > 0 else 0

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe_final"].dropna().unique():
        df_spe = df[df["sej_spe_final"] == spe]

        nb_total = len(df_spe)
        nb_avec_ll = len(df_spe[df_spe["sej_classe"].isin(["0j", "1j+"])])
        nb_j0 = len(df_spe[df_spe["sej_classe"] == "0j"])

        taux_ll = (nb_avec_ll / nb_total * 100) if nb_total > 0 else 0
        taux_j0_spe = (nb_j0 / nb_total * 100) if nb_total > 0 else 0

        df_spe_ll = df_spe[df_spe["sej_classe"].isin(["0j", "1j+"])]
        delai_spe = df_spe_ll["del_sorval"].mean() if len(df_spe_ll) > 0 else 0

        # Statistiques de diffusion (à adapter selon vos critères)
        nb_diffuses = nb_avec_ll
        pct_diffuses = 100.0 if nb_avec_ll > 0 else 0

        stats_par_spe.append(
            {
                "specialite": str(spe),
                "nb_total": int(nb_total),
                "nb_valides": int(nb_avec_ll),
                "taux_validation": round(taux_ll, 1),
                "taux_validation_j0": round(taux_j0_spe, 1),
                "delai_moyen": round(delai_spe, 1),
                "nb_diffuses": int(nb_diffuses),
                "pct_diffuses": round(pct_diffuses, 1),
                "delai_diffusion": round(delai_spe, 1),
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(stats_par_spe, key=lambda x: x["nb_total"], reverse=True)

    return {
        "total_sejours": int(total_sejours),
        "sejours_valides": int(sejours_avec_ll),
        "taux_validation": round(taux_ll_retrouvee, 1),
        "taux_validation_j0": round(taux_ll_j0, 1),
        "delai_moyen_validation": round(delai_moyen, 1),
        "total_diffuses": int(sejours_avec_ll),
        "pct_diffuses": round(taux_ll_retrouvee, 1),
        "delai_moyen_diffusion": round(delai_moyen, 1),
        "par_specialite": stats_par_spe,
    }


def calculate_statistics(data: pd.DataFrame) -> Dict:
    """
    Calculer les statistiques pour le rapport

    Args:
        data: DataFrame avec les données fusionnées

    Returns:
        Dictionnaire avec les statistiques
    """
    stats = {}

    # Total des séjours
    total_sejours = len(data)
    stats["total_sejours"] = total_sejours

    # Séjours avec LL validée
    sejours_valides = data["del_val"].notna().sum()
    stats["sejours_valides"] = sejours_valides

    # Taux de validation
    taux_validation = (
        (sejours_valides / total_sejours * 100) if total_sejours > 0 else 0
    )
    stats["taux_validation"] = round(taux_validation, 1)

    # Taux de validation le jour de la sortie (J0)
    sejours_j0 = (data["del_val"] == 0).sum()
    taux_j0 = (sejours_j0 / sejours_valides * 100) if sejours_valides > 0 else 0
    stats["taux_validation_j0"] = round(taux_j0, 1)

    # Délai moyen de validation
    delai_moyen = data["del_val"].mean()
    stats["delai_moyen_validation"] = (
        round(delai_moyen, 1) if not pd.isna(delai_moyen) else 0
    )

    # Statistiques par spécialité
    stats_spe = []

    for spe in data["sej_spe"].dropna().unique():
        spe_data = data[data["sej_spe"] == spe]

        spe_total = len(spe_data)
        spe_valides = spe_data["del_val"].notna().sum()
        spe_taux_val = (spe_valides / spe_total * 100) if spe_total > 0 else 0

        spe_j0 = (spe_data["del_val"] == 0).sum()
        spe_taux_j0 = (spe_j0 / spe_valides * 100) if spe_valides > 0 else 0

        spe_delai = spe_data["del_val"].mean()

        stats_spe.append(
            {
                "specialite": spe,
                "nb_total": spe_total,
                "nb_valides": spe_valides,
                "taux_validation": round(spe_taux_val, 1),
                "taux_validation_j0": round(spe_taux_j0, 1),
                "delai_moyen": round(spe_delai, 1) if not pd.isna(spe_delai) else 0,
            }
        )

    stats["par_specialite"] = sorted(stats_spe, key=lambda x: x["specialite"])

    return stats


def prepare_diffusion_stats(data: pd.DataFrame) -> Dict:
    """
    Préparer les statistiques de diffusion (envoi)

    Args:
        data: DataFrame avec les données fusionnées

    Returns:
        Dictionnaire avec les statistiques de diffusion
    """
    # Filtrer les données pour la diffusion
    # Exclure les validations les weekends et jours fériés
    # (À implémenter avec un calendrier des jours fériés)

    diffusion_data = data[data["del_val"].notna()].copy()

    # Pour simplifier, on considère tous les jours pour l'instant
    # Dans une version complète, il faudrait filtrer les weekends

    stats = {}

    # Total des documents diffusés
    total_diffuses = len(diffusion_data)
    stats["total_diffuses"] = total_diffuses

    # Pourcentage par rapport aux validés
    total_valides = data["del_val"].notna().sum()
    pct_diffuses = (total_diffuses / total_valides * 100) if total_valides > 0 else 0
    stats["pct_diffuses"] = round(pct_diffuses, 1)

    # Taux de diffusion à J0 de la validation
    # (Dans le cas simplifié, c'est la même chose que validation J0)
    diffuses_j0 = (diffusion_data["del_val"] == 0).sum()
    taux_diffusion_j0 = (
        (diffuses_j0 / total_diffuses * 100) if total_diffuses > 0 else 0
    )
    stats["taux_diffusion_j0"] = round(taux_diffusion_j0, 1)

    # Délai moyen de diffusion
    delai_diffusion = diffusion_data["del_val"].mean()
    stats["delai_moyen_diffusion"] = (
        round(delai_diffusion, 1) if not pd.isna(delai_diffusion) else 0
    )

    # Statistiques par spécialité
    stats_spe = []

    for spe in diffusion_data["sej_spe"].dropna().unique():
        spe_data = diffusion_data[diffusion_data["sej_spe"] == spe]

        spe_total = len(spe_data)
        spe_j0 = (spe_data["del_val"] == 0).sum()
        spe_taux_j0 = (spe_j0 / spe_total * 100) if spe_total > 0 else 0
        spe_delai = spe_data["del_val"].mean()

        # Pourcentage de séjours
        total_spe_valides = data[data["sej_spe"] == spe]["del_val"].notna().sum()
        pct_sej = (spe_total / total_spe_valides * 100) if total_spe_valides > 0 else 0

        stats_spe.append(
            {
                "specialite": spe,
                "nb_diffuses": spe_total,
                "pct_valides": round(pct_sej, 1),
                "taux_diffusion_j0": round(spe_taux_j0, 1),
                "delai_moyen": round(spe_delai, 1) if not pd.isna(spe_delai) else 0,
            }
        )

    stats["par_specialite"] = sorted(stats_spe, key=lambda x: x["specialite"])

    return stats


def convert_numpy_types(obj):
    """Convertit les types numpy en types Python natifs pour la sérialisation JSON"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


def classify_sejours_iql(
    df: pd.DataFrame, matrice_path: str = "data/db/iqss_ll_ufum3.csv"
) -> pd.DataFrame:
    """
    Classifie les séjours selon la méthodologie IQL

    Règles de classification:
    - "0j" : LL validée au plus tard le jour de la sortie (del_sorval <= 0)
    - "1j+" : LL validée après la sortie (del_sorval > 0)
    - "sansLL" : Aucune LL validée OU pas de spécialité associée

    Args:
        df: DataFrame contenant les séjours et documents
        matrice_path: Chemin vers la matrice de spécialité

    Returns:
        DataFrame avec colonnes 'sej_spe_final' et 'sej_classe' ajoutées
    """
    df = df.copy()

    # Charger la matrice de spécialité
    try:
        matrice = load_matrice_specialite(matrice_path)
    except Exception as e:
        print(f"⚠️ Erreur chargement matrice: {e}")
        # Fallback: utiliser doc_spe comme spécialité
        df["sej_spe_final"] = df.get("doc_spe")
        df["sej_classe"] = "sansLL"
        return df

    # Préparer les données pour le matching
    df["sej_uf"] = df["sej_uf"].astype(str)

    # Créer doc_key normalisée si nécessaire
    if "doc_key" not in df.columns:
        df["doc_key"] = df["doc_libelle"].apply(create_doc_key)

    df["doc_key_norm"] = df["doc_key"].apply(normalize_text)

    # Joindre avec la matrice de spécialité
    df = df.merge(
        matrice[["sej_uf", "doc_key_norm", "sej_spe"]],
        on=["sej_uf", "doc_key_norm"],
        how="left",
        suffixes=("_old", "_matrice"),
    )

    # Déterminer la spécialité finale
    if "sej_spe_matrice" in df.columns:
        df["sej_spe_final"] = df["sej_spe_matrice"]
    elif "sej_spe" in df.columns:
        df["sej_spe_final"] = df["sej_spe"]
    else:
        df["sej_spe_final"] = None

    # Classification IQL
    df["sej_classe"] = "sansLL"

    # Conditions d'éligibilité
    has_ll = df["doc_val"].notna()
    has_spe = df["sej_spe_final"].notna()
    has_delay = df["del_sorval"].notna()
    eligible = has_ll & has_spe & has_delay

    # Classification selon del_sorval
    df.loc[eligible & (df["del_sorval"] <= 0), "sej_classe"] = "0j"
    df.loc[eligible & (df["del_sorval"] > 0), "sej_classe"] = "1j+"

    return df


def merge_sejours_documents(
    sejours: pd.DataFrame, documents: pd.DataFrame
) -> pd.DataFrame:
    """
    Fusionne les données de séjours et documents

    Args:
        sejours: DataFrame des séjours (GAM)
        documents: DataFrame des documents (EASILY)

    Returns:
        DataFrame fusionné avec les séjours et leurs documents associés
    """
    # Nettoyer et préparer les clés
    sejours = sejours.copy()
    documents = documents.copy()

    # S'assurer que les IPP sont au bon format
    sejours["pat_ipp"] = sejours["pat_ipp"].astype(str)
    documents["pat_ipp"] = documents["pat_ipp"].astype(str)

    # Créer les clés de documents si pas déjà présentes
    if "doc_key" not in documents.columns:
        documents["doc_key"] = documents["doc_libelle"].apply(create_doc_key)

    # Fusionner séjours et documents sur l'IPP
    data = sejours.merge(documents, on="pat_ipp", how="left", suffixes=("", "_doc"))

    # Filtrer les documents validés dans une fenêtre raisonnable autour de la sortie
    # Documents validés entre 3 jours avant et 30 jours après la sortie
    if "doc_val" in data.columns and "sej_sor" in data.columns:
        data["sej_sor"] = pd.to_datetime(data["sej_sor"])
        data["doc_val"] = pd.to_datetime(data["doc_val"])

        # Calculer le délai entre sortie et validation
        data["del_sorval"] = (data["doc_val"] - data["sej_sor"]).dt.days

        # Filtrer: garder les docs validés entre -3j et +30j de la sortie
        data = data[
            (data["del_sorval"].isna())
            | ((data["del_sorval"] >= -3) & (data["del_sorval"] <= 30))
        ]

    return data


def calculate_diffusion_stats(df: pd.DataFrame) -> Dict:
    """
    Calcule les statistiques de diffusion

    Note: À adapter selon vos critères de diffusion
    Pour l'instant, utilise les mêmes critères que la validation

    Args:
        df: DataFrame avec séjours classifiés

    Returns:
        Dictionnaire contenant les statistiques de diffusion
    """
    # Pour simplifier, on considère que tous les séjours avec LL validée sont diffusés
    # Vous pouvez affiner cette logique selon vos besoins

    return calculate_validation_stats(df)


def generate_report_data(
    start_date: str,
    end_date: str,
    sejour_list: Optional[List[str]] = None,
    matrice_path: str = "data/db/iqss_ll_ufum3.csv",
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

    # 1. Récupérer les données des séjours (GAM)
    print("📥 Récupération des séjours...")
    sejours = get_sejours_data(start_date, end_date, sejour_list)
    print(f"   ✅ {len(sejours)} séjours récupérés")

    # 2. Récupérer les données des documents (EASILY)
    print("📥 Récupération des documents...")
    documents = get_documents_data(start_date, end_date)
    print(f"   ✅ {len(documents)} documents récupérés")

    # 3. Fusionner les données
    print("🔗 Fusion des données...")
    data = merge_sejours_documents(sejours, documents)
    print(f"   ✅ {len(data)} lignes après fusion")

    # 4. Classifier les séjours selon IQL
    print("🏷️  Classification IQL...")
    data = classify_sejours_iql(data, matrice_path)

    # Afficher la répartition des classes
    class_counts = data["sej_classe"].value_counts()
    print(f"   ✅ Classification:")
    for classe, count in class_counts.items():
        print(f"      - {classe}: {count} ({count / len(data) * 100:.1f}%)")

    # 5. Calculer les statistiques de validation
    print("📈 Calcul des statistiques de validation...")
    stats_validation = calculate_validation_stats(data)
    print(f"   ✅ Taux LL retrouvée: {stats_validation['taux_validation']:.1f}%")
    print(f"   ✅ Taux LL J0: {stats_validation['taux_validation_j0']:.1f}%")

    # 6. Calculer les statistiques de diffusion
    print("📈 Calcul des statistiques de diffusion...")
    stats_diffusion = calculate_diffusion_stats(data)
    print(f"   ✅ {stats_diffusion['total_diffuses']} documents diffusés")

    print("✅ Génération du rapport terminée\n")

    return data, stats_validation, stats_diffusion
