"""
Module de traitement et d'analyse des données
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import unicodedata
from database import get_sejours_data, get_documents_data
from config import settings


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
        "ll",
    ]

    for pattern in patterns_to_remove:
        key = key.replace(pattern, "")

    key = key.strip()
    return key


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


def calculate_validation_stats(df: pd.DataFrame, matrice_path: str = None) -> Dict:
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

    # Utiliser le chemin depuis settings si non fourni
    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH

    print(f"📂 Utilisation matrice: {matrice_path}")

    # Classifier les séjours
    df = classify_sejours_iql(df, matrice_path)

    # Statistiques globales
    total_sejours_all = len(df)

    # =================TABLEAU GAELLE SUR VALIDATION==================
    nb_ll_validees_all = df["doc_val"].notna().sum()
    pct_ll_validees_all = df["doc_val"].notna().mean() * 100
    taux_validation_J0_over_sejours_all = float((df["sej_classe"] == "0j").mean() * 100)
    delai_validation_moyenne_all = df["del_sorval"].mean()

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe_final"].dropna().unique():
        df_spe = df[df["sej_spe_final"] == spe]
        total_sejours = len(df_spe)

        # =================TABLEAU GAELLE SUR VALIDATION==================
        nb_ll_validees = df_spe["doc_val"].notna().sum()
        pct_ll_validees = df_spe["doc_val"].notna().mean() * 100
        taux_validation_J0_over_sejours = float(
            (df_spe["sej_classe"] == "0j").mean() * 100
        )
        delai_validation_moyenne = df_spe["del_sorval"].mean()
        # ==================================================================

        stats_par_spe.append(
            {
                "specialite": str(spe),
                "total_sejours": int(total_sejours),
                "nb_sejours_valides": int(nb_ll_validees),
                "pct_sejours_validees": float(
                    pct_ll_validees
                ),  # ✅ Convertir en float natif
                "taux_validation_j0_over_sejours": float(
                    taux_validation_J0_over_sejours
                ),  # ✅ Convertir en float natif
                "delai_moyen_validation": float(delai_validation_moyenne)
                if not pd.isna(delai_validation_moyenne)
                else 0.0,  # ✅ Gérer NaN
                # ❌ SUPPRIMÉ : "par_specialite": stats_par_spe,
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    return {
        "total_sejours_all": int(total_sejours_all),
        "nb_sejours_valides_all": int(nb_ll_validees_all),
        "pct_sejours_validees_all": float(
            pct_ll_validees_all
        ),  # ✅ Convertir en float natif
        "taux_validation_j0_over_sejours_all": float(
            taux_validation_J0_over_sejours_all
        ),  # ✅ Convertir en float natif
        "delai_moyen_validation_all": float(delai_validation_moyenne_all)
        if not pd.isna(delai_validation_moyenne_all)
        else 0.0,  # ✅ Gérer NaN
        "par_specialite_all": stats_par_spe,
    }


def calculate_diffusion_stats(df: pd.DataFrame, matrice_path: str = None) -> Dict:
    """
    Calcule les statistiques de diffusion selon la méthodologie IQL

    Indicateurs HAS:
    1. % séjours avec LL retrouvée (classes "0j" + "1j+")
    2. % séjours avec LL datée du jour de la sortie (classe "0j")

    Args:
        df: DataFrame contenant les séjours et documents
        matrice_path: Chemin vers la matrice de spécialité

    Returns:
        Dictionnaire contenant les statistiques globales et par spécialité
    """
    # Utiliser le chemin depuis settings si non fourni
    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH

    print(f"📂 Utilisation matrice: {matrice_path}")

    # Classifier les séjours
    df = classify_sejours_iql(df, matrice_path)

    # Statistiques globales
    total_sejours_all = len(df)

    # =================TABLEAU GAELLE SUR DIFFUSION==================
    nb_ll_validees_all = df["doc_val"].notna().sum()

    nb_LL_diffuses_all = df["date_diffusion"].notna().sum()
    pct_diffuses_sur_validees_all = nb_LL_diffuses_all / nb_ll_validees_all * 100
    pct_diffuses_sur_sejours_all = nb_LL_diffuses_all / total_sejours_all * 100

    tx_diffusion_a_J0_validation_all = float(
        ((df["date_diffusion"] - df["doc_val"]).dt.days == 0).mean() * 100
    )
    delai_diffusion_validation_all = (
        df["date_diffusion"] - df["doc_val"]
    ).dt.days.mean()

    # ==================================================================

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe_final"].dropna().unique():
        df_spe = df[df["sej_spe_final"] == spe]
        total_sejours = len(df_spe)

        # =================TABLEAU GAELLE SUR DIFFUSION==================

        nb_LL_diffuses = df_spe["date_diffusion"].notna().sum()
        nb_ll_validees = df_spe["doc_val"].notna().sum()
        pct_diffuses_sur_validees = (
            nb_LL_diffuses / nb_ll_validees * 100 if nb_ll_validees > 0 else 0.0
        )
        pct_diffuses_sur_sejours = nb_LL_diffuses / total_sejours * 100

        tx_diffusion_a_J0_validation = float(
            ((df_spe["date_diffusion"] - df_spe["doc_val"]).dt.days == 0).mean() * 100
        )
        delai_diffusion_validation = (
            df_spe["date_diffusion"] - df_spe["doc_val"]
        ).dt.days.mean()

        stats_par_spe.append(
            {
                "specialite": str(spe),
                "total_sejours": int(total_sejours),
                "nb_ll_diffusees": int(nb_LL_diffuses),
                "pct_ll_diffusees_over_validees": float(
                    pct_diffuses_sur_validees
                ),  # ✅ Convertir en float natif
                "pct_ll_diffusees_over_sejours": float(
                    pct_diffuses_sur_sejours
                ),  # ✅ Convertir en float natif
                "taux_diffusion_J0_validation": float(
                    tx_diffusion_a_J0_validation
                ),  # ✅ Convertir en float natif
                "delai_diffusion_validation": float(delai_diffusion_validation)
                if not pd.isna(delai_diffusion_validation)
                else 0.0,  # ✅ CORRIGÉ : utiliser la bonne variable
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    return {
        "nb_ll_diffusees_all": int(nb_LL_diffuses_all),
        "pct_ll_diffusees_over_validees_all": float(
            pct_diffuses_sur_validees_all
        ),  # ✅ Convertir en float natif
        "pct_ll_diffusees_over_sejours_all": float(
            pct_diffuses_sur_sejours_all
        ),  # ✅ Convertir en float natif
        "taux_diffusion_J0_validation_all": float(
            tx_diffusion_a_J0_validation_all
        ),  # ✅ Convertir en float natif
        "delai_diffusion_validation_all": float(delai_diffusion_validation_all)
        if not pd.isna(delai_diffusion_validation_all)
        else 0.0,  # ✅ CORRIGÉ : utiliser la bonne variable
        "par_specialite": stats_par_spe,
    }


def merge_sejours_documents(
    sejours: pd.DataFrame, documents: pd.DataFrame
) -> pd.DataFrame:
    """
    Fusionne les données de séjours et documents selon la méthodologie IQL

    Critères IQL:
    1. Documents de type Lettre de liaison
    2. Produits à partir d'une "fiche mère" antérieure à la fin du séjour
    3. Validés entre -3j et +30j de la sortie
    4. Si plusieurs LL pour un séjour: garder la DERNIÈRE validée

    Args:
        sejours: DataFrame des séjours (GAM)
        documents: DataFrame des documents (EASILY)

    Returns:
        DataFrame avec UN séjour par ligne et sa dernière LL validée
    """
    sejours = sejours.copy()
    documents = documents.copy()

    # Préparer les clés de jointure
    sejours["pat_ipp"] = sejours["pat_ipp"].astype(str)
    documents["pat_ipp"] = documents["pat_ipp"].astype(str)

    # Créer les clés de documents si nécessaire
    if "doc_key" not in documents.columns:
        documents["doc_key"] = documents["doc_libelle"].apply(create_doc_key)

    # Fusionner sur l'IPP
    data = sejours.merge(documents, on="pat_ipp", how="left", suffixes=("", "_doc"))

    # Convertir les dates
    data["sej_sor"] = pd.to_datetime(data["sej_sor"])
    data["sej_ent"] = pd.to_datetime(data["sej_ent"])
    data["doc_val"] = pd.to_datetime(data["doc_val"])

    if "doc_creamere" in data.columns:
        data["doc_creamere"] = pd.to_datetime(data["doc_creamere"])

    # Calculer les délais
    data["del_sorval"] = (data["doc_val"] - data["sej_sor"]).dt.days

    # Appliquer les filtres IQL
    mask_valide = pd.Series([True] * len(data), index=data.index)

    # Filtre 1: Documents validés (doc_val non null)
    has_doc_val = data["doc_val"].notna()

    # Filtre 2: Fiche mère créée avant la sortie (si disponible)
    if "doc_creamere" in data.columns:
        fiche_mere_avant_sortie = (
            data["doc_creamere"].isna()  # Pas de fiche mère (on garde)
            | (data["doc_creamere"] < data["sej_sor"])  # Fiche mère avant sortie
        )
        mask_valide &= fiche_mere_avant_sortie

    # Filtre 3: Validation entre -3j et +30j de la sortie
    validation_dans_fenetre = data["del_sorval"].isna() | (
        (data["del_sorval"] >= -3) & (data["del_sorval"] <= 30)
    )
    mask_valide &= validation_dans_fenetre

    # Appliquer les filtres
    data_filtered = data[mask_valide].copy()

    # Séparer séjours avec et sans LL
    sejours_avec_ll = data_filtered[data_filtered["doc_val"].notna()].copy()
    sejours_sans_ll = data_filtered[data_filtered["doc_val"].isna()].copy()

    # Pour les séjours avec LL: garder la DERNIÈRE validée (date la plus récente)
    if len(sejours_avec_ll) > 0:
        # Trier par sej_id et doc_val décroissant
        sejours_avec_ll = sejours_avec_ll.sort_values(
            ["sej_id", "doc_val"], ascending=[True, False]
        )

        # Garder la première (= plus récente) pour chaque séjour
        sejours_avec_ll = sejours_avec_ll.drop_duplicates(
            subset=["sej_id"], keep="first"
        )

        print(
            f"   📝 {len(sejours_avec_ll)} séjours avec LL (dernière validation gardée)"
        )

    # Pour les séjours sans LL: une seule ligne par séjour
    if len(sejours_sans_ll) > 0:
        sejours_sans_ll = sejours_sans_ll.drop_duplicates(
            subset=["sej_id"], keep="first"
        )
        print(f"   ❌ {len(sejours_sans_ll)} séjours sans LL")

    # Recombiner
    data_final = pd.concat([sejours_avec_ll, sejours_sans_ll], ignore_index=True)

    # Vérifications
    nb_sejours_initial = len(sejours)
    nb_sejours_final = len(data_final)

    print(f"   ✅ Résultat: {nb_sejours_initial} séjours → {nb_sejours_final} lignes")

    if nb_sejours_initial != nb_sejours_final:
        diff = nb_sejours_initial - nb_sejours_final
        print(
            f"   ⚠️ {diff} séjours non retrouvés (probablement sans LL valide dans la fenêtre)"
        )

    # Statistiques
    nb_avec_ll = data_final["doc_val"].notna().sum()
    print(
        f"   📊 Avec LL validée: {nb_avec_ll} ({nb_avec_ll / nb_sejours_final * 100:.1f}%)"
    )

    return data_final
