"""
Module de traitement et d'analyse des données
Version R v7 - Décembre 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import unicodedata
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
    matrice_path: str = None,
) -> pd.DataFrame:
    """
    Charge et prépare la matrice de spécialité v7

    Args:
        matrice_path: Chemin vers le fichier Excel de mapping

    Returns:
        DataFrame avec les mappings UF/doc_key -> spécialité
    """
    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH

    try:
        # Lire le fichier Excel (v7 utilise .xlsx au lieu de .csv)
        matrice = pd.read_excel(matrice_path, dtype={"sej_uf": str})
        matrice["doc_key_norm"] = matrice["doc_key"].apply(normalize_text)
        # Supprimer les doublons (garder la première occurrence)
        matrice = matrice.drop_duplicates(
            subset=["sej_uf", "doc_key_norm"], keep="first"
        )
        return matrice
    except FileNotFoundError:
        print(f"Fichier matrice non trouvé : {matrice_path}")
        print("Tentative avec ancien format CSV...")
        # Fallback vers CSV si Excel non trouvé
        csv_path = matrice_path.replace(".xlsx", ".csv")
        try:
            matrice = pd.read_csv(csv_path, dtype={"sej_uf": str})
            matrice["doc_key_norm"] = matrice["doc_key"].apply(normalize_text)
            matrice = matrice.drop_duplicates(
                subset=["sej_uf", "doc_key_norm"], keep="first"
            )

            return matrice
        except Exception as e:
            raise FileNotFoundError(
                f"Impossible de charger la matrice (Excel ou CSV) : {e}"
            )
    except Exception as e:
        raise Exception(f"Erreur lors du chargement de la matrice : {e}")


def create_doc_key(libelle: str) -> str:
    """
    Créer une clé de document à partir du libellé
    Simplifie et normalise le libellé du document

    Args:
        libelle: Libellé du document depuis EASILY

    Returns:
        Clé simplifiée du document
    """
    if pd.isna(libelle):
        return ""

    # Normaliser
    key = str(libelle).lower().strip()

    # Supprimer les patterns inutiles (même logique que le code R)
    patterns_to_remove = [
        "cr lettre de liaison",
        "lettre de liaison",
        "cr",
        "foch",
        "hdj",
        "cs",
        "\\.",
        "ll",
    ]

    for pattern in patterns_to_remove:
        key = key.replace(pattern, "")

    key = key.strip()
    return key


def merge_sejours_documents(
    sejours: pd.DataFrame, documents: pd.DataFrame, matrice_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Fusionne les données de séjours et documents selon la méthodologie IQL R v7

    ORDRE DES OPÉRATIONS (conforme au code R lignes 177-248):
    1. Jointure séjours × documents sur pat_ipp (R ligne 181)
    2. Jointure avec matrice de spécialité (ufum) sur sej_uf + doc_key (R ligne 184)
    3. Calcul des critères booléens sdt_* (R lignes 188-213)
    4. Calcul de del_sorval si sdt_status=TRUE (R lignes 211-213)
    5. PREMIER TRI : is.na(sej_spe), del_sorval → pref_sorval (R ligne 220-221)
    6. DEUXIÈME TRI : is.na(sej_spe), desc(sdt_docven), desc(sdt_emere),
                      desc(sdt_status), desc(sdt_doccref), del_sorval → pref_ficmere (R ligne 224-225)
    7. Sélection du meilleur document : pref_ficmere == min(pref_ficmere) (R ligne 230)
    8. Gestion des documents multi-séjours : del_sorval=NA si doc_sejn > 1 (R lignes 232-237)
    9. Calcul de del_val APRÈS gestion multi-séjours (R ligne 241)
    10. Classification sej_classe (R lignes 243-247)

    Args:
        sejours: DataFrame des séjours (GAM)
        documents: DataFrame des documents (EASILY)
        matrice_path: Chemin vers la matrice de spécialité (optionnel)

    Returns:
        DataFrame avec UN séjour par ligne et son document optimal
    """
    # Import settings ici pour éviter les imports circulaires
    from config import settings

    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH

    sejours = sejours.copy()
    documents = documents.copy()

    # ========================================
    # ÉTAPE 1 : PRÉPARATION DES DONNÉES
    # ========================================

    sejours["pat_ipp"] = sejours["pat_ipp"].astype(str)
    documents["pat_ipp"] = documents["pat_ipp"].astype(str)
    sejours["sej_uf"] = sejours["sej_uf"].astype(str)

    if "doc_key" not in documents.columns:
        documents["doc_key"] = documents["doc_libelle"].apply(create_doc_key)

    documents["doc_key_norm"] = documents["doc_key"].apply(normalize_text)

    # ========================================
    # ÉTAPE 2 : JOINTURE SÉJOURS × DOCUMENTS SUR IPP (R ligne 181)
    # ========================================

    data = sejours.merge(documents, on="pat_ipp", how="left", suffixes=("", "_doc"))

    # ========================================
    # ÉTAPE 3 : JOINTURE AVEC MATRICE DE SPÉCIALITÉ (R ligne 184)
    # ========================================

    try:
        matrice = load_matrice_specialite(matrice_path)

        data = data.merge(
            matrice[["sej_uf", "doc_key_norm", "sej_spe"]],
            on=["sej_uf", "doc_key_norm"],
            how="left",
        )

    except Exception as e:
        print(f"Impossible de charger la matrice : {e}")
        data["sej_spe"] = None

    # ========================================
    # ÉTAPE 4 : CONVERSION DES DATES
    # ========================================

    data["sej_sor"] = pd.to_datetime(data["sej_sor"])
    data["sej_ent"] = pd.to_datetime(data["sej_ent"])
    data["doc_val"] = pd.to_datetime(data["doc_val"])
    data["doc_cre"] = pd.to_datetime(data["doc_cre"])

    if "doc_creamere" in data.columns:
        data["doc_creamere"] = pd.to_datetime(data["doc_creamere"])
    if "doc_modmere" in data.columns:
        data["doc_modmere"] = pd.to_datetime(data["doc_modmere"])

    # ========================================
    # ÉTAPE 5 : CALCUL DES CRITÈRES BOOLÉENS (R lignes 188-213)
    # ========================================

    # 1. sdt_docven (R ligne 190-191)
    if "doc_venue" in data.columns:
        data["doc_venue"] = pd.to_numeric(data["doc_venue"], errors="coerce")
        data["sej_id_num"] = pd.to_numeric(data["sej_id"], errors="coerce")
        data["sdt_docven"] = data["sej_id_num"] == data["doc_venue"]
        data.drop(columns=["sej_id_num"], inplace=True)

    else:
        data["sdt_docven"] = False

    # 2. sdt_docval (R ligne 193-194)
    data["sdt_docval"] = (data["doc_val"] >= data["sej_ent"]) & (
        data["doc_val"] >= (data["sej_sor"] - pd.Timedelta(days=3))
    )

    # 3. sdt_smere (R ligne 196-197)
    if "doc_creamere" in data.columns and "doc_modmere" in data.columns:
        data["sdt_smere"] = (
            data["doc_creamere"].isna()
            | (data["doc_creamere"] <= data["sej_sor"])
            | (data["doc_modmere"] <= data["sej_sor"])
        )

    else:
        data["sdt_smere"] = True

    # 4. sdt_doccre (R ligne 199-200)
    data["sdt_doccre"] = data["doc_cre"] >= (data["sej_ent"] - pd.Timedelta(days=5))

    # 5. sdt_doccref (R ligne 202-203)
    data["sdt_doccref"] = (data["doc_cre"] >= data["sej_ent"]) & (
        data["doc_cre"] <= data["sej_sor"]
    )

    # 6. sdt_emere (R ligne 205-207)
    if "doc_creamere" in data.columns and "doc_modmere" in data.columns:
        data["sdt_emere"] = (
            data["doc_creamere"].isna()
            | (data["doc_creamere"] >= (data["sej_ent"] - pd.Timedelta(days=5)))
            | (data["doc_modmere"] >= (data["sej_ent"] - pd.Timedelta(days=5)))
        )

    else:
        data["sdt_emere"] = True

    # 7. sdt_status (R ligne 210)
    data["sdt_status"] = (
        data["sdt_docval"].astype(int)
        + data["sdt_smere"].astype(int)
        + data["sdt_doccre"].astype(int)
    ) > 2

    # 8. del_sorval (R lignes 211-213)
    # R: del_sorval=case_when(sdt_status == TRUE ~ as.numeric(difftime(doc_val,sej_sor,units = "days")), TRUE ~ NA_real_)
    data["del_sorval"] = np.where(
        data["sdt_status"], (data["doc_val"] - data["sej_sor"]).dt.days, np.nan
    )

    # ========================================
    # ÉTAPE 6 : PREMIER TRI - pref_sorval (R lignes 220-221)
    # ========================================
    # R: arrange(is.na(sej_spe), del_sorval) |> mutate(pref_sorval=row_number())

    # Créer colonne pour le tri (True si sej_spe est NA → à mettre en dernier)
    data["spe_is_na"] = data["sej_spe"].isna()

    # Trier par sej_id, puis is.na(sej_spe) ASC, puis del_sorval ASC
    data = data.sort_values(
        by=["sej_id", "spe_is_na", "del_sorval"],
        ascending=[True, True, True],
        na_position="last",
    )

    # Calculer pref_sorval par groupe sej_id
    data["pref_sorval"] = data.groupby("sej_id").cumcount() + 1

    # ========================================
    # ÉTAPE 7 : DEUXIÈME TRI - pref_ficmere (R lignes 224-225)
    # ========================================
    # R: arrange(is.na(sej_spe), desc(sdt_docven), desc(sdt_emere), desc(sdt_status), desc(sdt_doccref), del_sorval)
    #    mutate(pref_ficmere=row_number())

    data = data.sort_values(
        by=[
            "sej_id",
            "spe_is_na",  # is.na(sej_spe) ASC → ceux AVEC spe en premier
            "sdt_docven",  # desc(sdt_docven) → True en premier
            "sdt_emere",  # desc(sdt_emere) → True en premier
            "sdt_status",  # desc(sdt_status) → True en premier
            "sdt_doccref",  # desc(sdt_doccref) → True en premier
            "del_sorval",  # del_sorval ASC → plus petit en premier
        ],
        ascending=[True, True, False, False, False, False, True],
        na_position="last",
    )

    # Calculer pref_ficmere par groupe sej_id
    data["pref_ficmere"] = data.groupby("sej_id").cumcount() + 1

    # ========================================
    # ÉTAPE 8 : SÉLECTION DU MEILLEUR DOCUMENT (R ligne 230)
    # ========================================
    # R: filter(.by=c(pat_ipp,sej_id), pref_ficmere==min(pref_ficmere))

    data_best = data[data["pref_ficmere"] == 1].copy()

    # ========================================
    # ÉTAPE 9 : GESTION DES DOCUMENTS MULTI-SÉJOURS (R lignes 232-237)
    # ========================================
    # R:
    # group_by(doc_id) |>
    # arrange(del_sorval) |>
    # mutate(doc_sejn=row_number()) |>
    # mutate(del_sorval=ifelse(doc_sejn==1,del_sorval,NA_real_),
    #        sdt_doclibre=ifelse(doc_sejn==1,TRUE,FALSE))

    # Initialiser sdt_doclibre à True par défaut
    data_best["sdt_doclibre"] = True
    data_best["doc_sejn"] = 1

    # Identifier les docs utilisés par plusieurs séjours
    doc_counts = data_best[data_best["doc_id"].notna()].groupby("doc_id").size()
    multi_sejour_docs = doc_counts[doc_counts > 1].index.tolist()

    if len(multi_sejour_docs) > 0:
        for doc_id in multi_sejour_docs:
            mask = data_best["doc_id"] == doc_id

            # Trier par del_sorval (comme R: arrange(del_sorval))
            # Récupérer les indices triés
            doc_sejours = data_best.loc[mask].sort_values(
                "del_sorval", na_position="last"
            )

            # Appliquer doc_sejn
            for i, (idx, _) in enumerate(doc_sejours.iterrows()):
                data_best.loc[idx, "doc_sejn"] = i + 1

                if i == 0:
                    # Premier séjour (le plus proche) : garde del_sorval et sdt_doclibre=True
                    data_best.loc[idx, "sdt_doclibre"] = True
                else:
                    # Autres séjours : del_sorval=NA et sdt_doclibre=False
                    data_best.loc[idx, "del_sorval"] = np.nan
                    data_best.loc[idx, "sdt_doclibre"] = False

    else:
        print("Aucun document multi-séjours")

    # ========================================
    # ÉTAPE 10 : CALCUL DE del_val APRÈS multi-séjours (R ligne 241)
    # ========================================
    # R: del_val=case_when(is.na(del_sorval)|is.infinite(del_sorval)|is.na(sej_spe) ~ NA,
    #                      TRUE ~ max(0,del_sorval))

    data_best["del_val"] = data_best.apply(
        lambda row: np.nan
        if (
            pd.isna(row["del_sorval"]) or np.isinf(row["del_sorval"])
            if pd.notna(row["del_sorval"])
            else True
        )
        or pd.isna(row["sej_spe"])
        else max(0, row["del_sorval"]),
        axis=1,
    )

    # ========================================
    # ÉTAPE 11 : CLASSIFICATION sej_classe (R lignes 243-247)
    # ========================================
    # R: sej_classe=factor(case_when(del_val==0 ~ 0, del_val>0 ~ 1, TRUE ~ 2),
    #                      levels = c(0, 1, 2), labels = status_libelle)

    def classify_sejour(del_val):
        if pd.isna(del_val):
            return "sansLL"
        elif del_val == 0:
            return "0j"
        else:  # del_val > 0
            return "1j+"

    data_best["sej_classe"] = data_best["del_val"].apply(classify_sejour)

    # ========================================
    # ÉTAPE 12 : AJOUT DES SÉJOURS SANS DOCUMENT
    # ========================================

    sejours_sans_doc = sejours[~sejours["sej_id"].isin(data_best["sej_id"])].copy()

    if len(sejours_sans_doc) > 0:
        # Ajouter les colonnes manquantes
        for col in data_best.columns:
            if col not in sejours_sans_doc.columns:
                sejours_sans_doc[col] = np.nan

        # Ces séjours sont classés sansLL
        sejours_sans_doc["sej_classe"] = "sansLL"
        sejours_sans_doc["sdt_doclibre"] = True

        data_final = pd.concat([data_best, sejours_sans_doc], ignore_index=True)
    else:
        data_final = data_best

    # ========================================
    # VÉRIFICATIONS FINALES
    # ========================================

    # Nettoyer les colonnes temporaires
    cols_to_drop = ["spe_is_na", "pref_sorval", "pref_ficmere", "doc_sejn"]
    for col in cols_to_drop:
        if col in data_final.columns:
            data_final.drop(columns=[col], inplace=True)

    return data_final


def calculate_validation_stats(df: pd.DataFrame, matrice_path: str = None) -> Dict:
    """
    Calcule les statistiques de validation selon la méthodologie IQL R v7

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

    # Statistiques globales
    total_sejours_all = len(df)

    # =================TABLEAU GAELLE SUR VALIDATION==================
    nb_ll_validees_all = df["doc_val"].notna().sum()
    pct_ll_validees_all = df["doc_val"].notna().mean() * 100
    taux_validation_J0_over_sejours_all = float((df["sej_classe"] == "0j").mean() * 100)
    delai_validation_moyenne_all = df["del_sorval"].mean()

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe"].dropna().unique():
        df_spe = df[df["sej_spe"] == spe]
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
                "pct_sejours_validees": float(pct_ll_validees),
                "taux_validation_j0_over_sejours": float(
                    taux_validation_J0_over_sejours
                ),
                "delai_moyen_validation": float(delai_validation_moyenne)
                if not pd.isna(delai_validation_moyenne)
                else 0.0,  #  Gérer NaN
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    return {
        "total_sejours_all": int(total_sejours_all),
        "nb_sejours_valides_all": int(nb_ll_validees_all),
        "pct_sejours_validees_all": float(pct_ll_validees_all),
        "taux_validation_j0_over_sejours_all": float(
            taux_validation_J0_over_sejours_all
        ),
        "delai_moyen_validation_all": float(delai_validation_moyenne_all)
        if not pd.isna(delai_validation_moyenne_all)
        else 0.0,  #  Gérer NaN
        "par_specialite_all": stats_par_spe,
    }


def calculate_diffusion_stats(df: pd.DataFrame, matrice_path: str = None) -> Dict:
    """
    Calcule les statistiques de diffusion selon la méthodologie IQL R v7

    Indicateurs HAS:
    1. % séjours avec LL diffusée
    2. % séjours avec LL diffusée le jour de la validation

    Args:
        df: DataFrame contenant les séjours et documents
        matrice_path: Chemin vers la matrice de spécialité

    Returns:
        Dictionnaire contenant les statistiques globales et par spécialité
    """
    # Utiliser le chemin depuis settings si non fourni
    if matrice_path is None:
        matrice_path = settings.MATRICE_PATH

    # Classifier les séjours
    # df = classify_sejours_iql(df, matrice_path)

    # Statistiques globales
    total_sejours_all = len(df)

    # =================TABLEAU GAELLE SUR DIFFUSION==================
    nb_ll_validees_all = df["doc_val"].notna().sum()

    nb_LL_diffuses_all = df["date_diffusion"].notna().sum()
    pct_diffuses_sur_validees_all = (
        nb_LL_diffuses_all / nb_ll_validees_all * 100 if nb_ll_validees_all > 0 else 0.0
    )
    pct_diffuses_sur_sejours_all = nb_LL_diffuses_all / total_sejours_all * 100

    # Convertir les dates pour calcul
    df_with_dates = df.copy()
    df_with_dates["date_diffusion"] = pd.to_datetime(df_with_dates["date_diffusion"])
    df_with_dates["doc_val"] = pd.to_datetime(df_with_dates["doc_val"])

    tx_diffusion_a_J0_validation_all = float(
        (
            (df_with_dates["date_diffusion"] - df_with_dates["doc_val"]).dt.days == 0
        ).mean()
        * 100
    )
    delai_diffusion_validation_all = (
        df_with_dates["date_diffusion"] - df_with_dates["doc_val"]
    ).dt.days.mean()

    # ==================================================================

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe"].dropna().unique():
        df_spe = df[df["sej_spe"] == spe]
        df_spe_dates = df_with_dates[df_with_dates["sej_spe"] == spe]
        total_sejours = len(df_spe)

        # =================TABLEAU GAELLE SUR DIFFUSION==================

        nb_LL_diffuses = df_spe["date_diffusion"].notna().sum()
        nb_ll_validees = df_spe["doc_val"].notna().sum()
        pct_diffuses_sur_validees = (
            nb_LL_diffuses / nb_ll_validees * 100 if nb_ll_validees > 0 else 0.0
        )
        pct_diffuses_sur_sejours = nb_LL_diffuses / total_sejours * 100

        tx_diffusion_a_J0_validation = float(
            (
                (df_spe_dates["date_diffusion"] - df_spe_dates["doc_val"]).dt.days == 0
            ).mean()
            * 100
        )
        delai_diffusion_validation = (
            df_spe_dates["date_diffusion"] - df_spe_dates["doc_val"]
        ).dt.days.mean()

        stats_par_spe.append(
            {
                "specialite": str(spe),
                "total_sejours": int(total_sejours),
                "nb_ll_diffusees": int(nb_LL_diffuses),
                "pct_ll_diffusees_over_validees": float(pct_diffuses_sur_validees),
                "pct_ll_diffusees_over_sejours": float(pct_diffuses_sur_sejours),
                "taux_diffusion_J0_validation": float(tx_diffusion_a_J0_validation),
                "delai_diffusion_validation": float(delai_diffusion_validation)
                if not pd.isna(delai_diffusion_validation)
                else 0.0,
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    return {
        "nb_ll_diffusees_all": int(nb_LL_diffuses_all),
        "pct_ll_diffusees_over_validees_all": float(pct_diffuses_sur_validees_all),
        "pct_ll_diffusees_over_sejours_all": float(pct_diffuses_sur_sejours_all),
        "taux_diffusion_J0_validation_all": float(tx_diffusion_a_J0_validation_all),
        "delai_diffusion_validation_all": float(delai_diffusion_validation_all)
        if not pd.isna(delai_diffusion_validation_all)
        else 0.0,
        "par_specialite": stats_par_spe,
    }
