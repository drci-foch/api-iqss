"""
Module de traitement et d'analyse des données
Version R v7 - Décembre 2025
"""

import pandas as pd
import numpy as np
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
        print(f"   ✅ Matrice chargée : {len(matrice)} mappings UF/spécialité")
        return matrice
    except FileNotFoundError:
        print(f"   ⚠️ Fichier matrice non trouvé : {matrice_path}")
        print(f"   ⚠️ Tentative avec ancien format CSV...")
        # Fallback vers CSV si Excel non trouvé
        csv_path = matrice_path.replace(".xlsx", ".csv")
        try:
            matrice = pd.read_csv(csv_path, dtype={"sej_uf": str})
            matrice["doc_key_norm"] = matrice["doc_key"].apply(normalize_text)
            matrice = matrice.drop_duplicates(
                subset=["sej_uf", "doc_key_norm"], keep="first"
            )
            print(f"   ✅ Matrice CSV chargée : {len(matrice)} mappings")
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
    sejours: pd.DataFrame, documents: pd.DataFrame
) -> pd.DataFrame:
    """
    Fusionne les données de séjours et documents selon la méthodologie IQL R v7

    Nouveaux critères de rattachement (v7) :
    1. sdt_docven : Numéro de venue correspond
    2. sdt_docval : Doc validé après entrée ET ≥ (sortie - 3j)
    3. sdt_smere : Fiche mère créée/modifiée AVANT la sortie
    4. sdt_doccre : Doc créé après entrée - 5j
    5. sdt_doccref : Doc créé DURANT le séjour (critère préférentiel)
    6. sdt_emere : Fiche mère créée/modifiée après entrée - 5j

    Critère minimal : (sdt_docval + sdt_smere + sdt_doccre) > 2

    Priorisation (ordre de tri) :
    1. Présence de spécialité (sej_spe)
    2. Venue correspondante (sdt_docven)
    3. Fiche mère valide (sdt_emere)
    4. Critères minimaux OK (sdt_status)
    5. Doc créé durant séjour (sdt_doccref)
    6. Délai de validation (del_sorval)

    Args:
        sejours: DataFrame des séjours (GAM)
        documents: DataFrame des documents (EASILY)

    Returns:
        DataFrame avec UN séjour par ligne et son document optimal
    """
    sejours = sejours.copy()
    documents = documents.copy()

    print("\n🔗 Fusion séjours × documents (méthodologie R v7)...")

    # Préparer les clés de jointure
    sejours["pat_ipp"] = sejours["pat_ipp"].astype(str)
    documents["pat_ipp"] = documents["pat_ipp"].astype(str)

    # Créer les clés de documents si nécessaire
    if "doc_key" not in documents.columns:
        documents["doc_key"] = documents["doc_libelle"].apply(create_doc_key)

    print(f"   📊 {len(sejours)} séjours × {len(documents)} documents")

    # Fusionner sur l'IPP
    data = sejours.merge(documents, on="pat_ipp", how="left", suffixes=("", "_doc"))

    print(f"   ✅ Jointure IPP : {len(data)} lignes")

    # Convertir les dates
    data["sej_sor"] = pd.to_datetime(data["sej_sor"])
    data["sej_ent"] = pd.to_datetime(data["sej_ent"])
    data["doc_val"] = pd.to_datetime(data["doc_val"])
    data["doc_cre"] = pd.to_datetime(data["doc_cre"])

    if "doc_creamere" in data.columns:
        data["doc_creamere"] = pd.to_datetime(data["doc_creamere"])
    if "doc_modmere" in data.columns:
        data["doc_modmere"] = pd.to_datetime(data["doc_modmere"])

    print("\n🔍 Application des critères de rattachement R v7...")

    # ========================================
    # NOUVEAUX CRITÈRES BOOLÉENS (R v7)
    # ========================================

    # 1. sdt_docven : Le numéro de venue du doc est-il celui du séjour ?
    if "doc_venue" in data.columns:
        data["sdt_docven"] = data["sej_id"] == data["doc_venue"].astype(str)
        print(f"   ✅ sdt_docven : {data['sdt_docven'].sum()} correspondances venue")
    else:
        data["sdt_docven"] = False
        print(f"   ⚠️ sdt_docven : colonne doc_venue absente, critère désactivé")

    # 2. sdt_docval : Doc validé après entrée ET ≥ (sortie - 3 jours)
    data["sdt_docval"] = (data["doc_val"] >= data["sej_ent"]) & (
        data["doc_val"] >= (data["sej_sor"] - pd.Timedelta(days=3))
    )
    print(f"   ✅ sdt_docval : {data['sdt_docval'].sum()} docs dans fenêtre temporelle")

    # 3. sdt_smere : Fiche mère créée OU modifiée AVANT la sortie
    if "doc_creamere" in data.columns and "doc_modmere" in data.columns:
        data["sdt_smere"] = (
            data["doc_creamere"].isna()
            | (data["doc_creamere"] <= data["sej_sor"])
            | (data["doc_modmere"] <= data["sej_sor"])
        )
        print(f"   ✅ sdt_smere : {data['sdt_smere'].sum()} fiches mères avant sortie")
    else:
        data["sdt_smere"] = True  # Par défaut si pas de fiche mère
        print(f"   ⚠️ sdt_smere : colonnes fiche mère absentes, critère désactivé")

    # 4. sdt_doccre : Doc créé après entrée - 5 jours
    data["sdt_doccre"] = data["doc_cre"] >= (data["sej_ent"] - pd.Timedelta(days=5))
    print(f"   ✅ sdt_doccre : {data['sdt_doccre'].sum()} docs créés après entrée-5j")

    # 5. sdt_doccref : Doc créé DURANT le séjour (critère préférentiel)
    data["sdt_doccref"] = (data["doc_cre"] >= data["sej_ent"]) & (
        data["doc_cre"] <= data["sej_sor"]
    )
    print(f"   ✅ sdt_doccref : {data['sdt_doccref'].sum()} docs créés durant séjour")

    # 6. sdt_emere : Fiche mère créée/modifiée après entrée - 5j
    if "doc_creamere" in data.columns and "doc_modmere" in data.columns:
        data["sdt_emere"] = (
            data["doc_creamere"].isna()
            | (data["doc_creamere"] >= (data["sej_ent"] - pd.Timedelta(days=5)))
            | (data["doc_modmere"] >= (data["sej_ent"] - pd.Timedelta(days=5)))
        )
        print(
            f"   ✅ sdt_emere : {data['sdt_emere'].sum()} fiches mères après entrée-5j"
        )
    else:
        data["sdt_emere"] = True
        print(f"   ⚠️ sdt_emere : colonnes fiche mère absentes, critère désactivé")

    # ========================================
    # CRITÈRE MINIMAL DE RATTACHEMENT
    # ========================================
    # Il faut au moins 3 critères vrais parmi : docval, smere, doccre
    data["sdt_status"] = (
        data["sdt_docval"].astype(int)
        + data["sdt_smere"].astype(int)
        + data["sdt_doccre"].astype(int)
    ) > 2

    print(
        f"   ✅ sdt_status : {data['sdt_status'].sum()} lignes avec critères minimaux OK"
    )

    # Calculer del_sorval seulement si critères minimaux OK
    data["del_sorval"] = np.where(
        data["sdt_status"], (data["doc_val"] - data["sej_sor"]).dt.days, np.nan
    )

    nb_with_delay = data["del_sorval"].notna().sum()
    print(f"   ✅ del_sorval calculé pour {nb_with_delay} lignes")

    # ========================================
    # JOINTURE AVEC MATRICE DE SPÉCIALITÉ
    # ========================================
    # (pour pouvoir trier par sej_spe)

    print("\n🏥 Jointure avec matrice de spécialité...")

    try:
        matrice = load_matrice_specialite(settings.MATRICE_PATH)

        # Créer doc_key_norm si nécessaire
        if "doc_key_norm" not in data.columns:
            data["doc_key_norm"] = data["doc_key"].apply(normalize_text)

        # Jointure
        data = data.merge(
            matrice[["sej_uf", "doc_key_norm", "sej_spe"]],
            on=["sej_uf", "doc_key_norm"],
            how="left",
            suffixes=("", "_matrice"),
        )

        nb_with_spe = data["sej_spe"].notna().sum()
        print(
            f"   ✅ Spécialité trouvée pour {nb_with_spe} lignes ({nb_with_spe / len(data) * 100:.1f}%)"
        )

    except Exception as e:
        print(f"   ⚠️ Impossible de charger la matrice : {e}")
        print(f"   ⚠️ Le tri par spécialité sera désactivé")
        data["sej_spe"] = None

    # ========================================
    # PRIORISATION DES DOCUMENTS (R v7)
    # ========================================
    # Trier selon l'ordre de préférence R

    print("\n📊 Priorisation des documents (tri multi-critères)...")

    # Créer une colonne booléenne : True si sej_spe existe, False sinon
    data["has_spe"] = data["sej_spe"].notna()

    # Pour chaque séjour, trier les documents candidats
    data_sorted = data.sort_values(
        by=[
            "sej_id",
            "has_spe",  # 1. Prioriser ceux avec spécialité
            "sdt_docven",  # 2. Prioriser si venue correspond
            "sdt_emere",  # 3. Prioriser si fiche mère après entrée
            "sdt_status",  # 4. Prioriser si critères minimaux OK
            "sdt_doccref",  # 5. Prioriser si doc créé durant séjour
            "del_sorval",  # 6. Puis trier par délai (croissant)
        ],
        ascending=[True, False, False, False, False, False, True],
        na_position="last",
    )

    # Garder le meilleur document pour chaque séjour
    data_best = data_sorted.groupby("sej_id", as_index=False).first()

    print(f"   ✅ Meilleur document sélectionné pour {len(data_best)} séjours")

    # ========================================
    # GESTION DES DOCUMENTS MULTI-SÉJOURS
    # ========================================
    # Si un document est associé à plusieurs séjours, ne garder que le plus proche

    print("\n🔄 Gestion des documents multi-séjours...")

    # Pour chaque doc_id, compter combien de séjours l'utilisent
    doc_counts = data_best[data_best["doc_id"].notna()].groupby("doc_id").size()
    multi_sejour_docs = doc_counts[doc_counts > 1].index

    if len(multi_sejour_docs) > 0:
        print(f"   ⚠️ {len(multi_sejour_docs)} documents associés à plusieurs séjours")

        # Pour ces documents, marquer comme "libre" seulement le séjour le plus proche
        for doc_id in multi_sejour_docs:
            mask = data_best["doc_id"] == doc_id
            doc_sejours = data_best[mask].copy()

            # Trier par del_sorval (le plus proche)
            doc_sejours_sorted = doc_sejours.sort_values("del_sorval")

            # Seul le premier garde le document
            closest_sej = doc_sejours_sorted.iloc[0]["sej_id"]

            # Mettre del_sorval à NaN pour les autres
            data_best.loc[mask & (data_best["sej_id"] != closest_sej), "del_sorval"] = (
                np.nan
            )

        print(f"   ✅ Documents multi-séjours traités")
    else:
        print(f"   ✅ Aucun document multi-séjours")

    # ========================================
    # AJOUT DES SÉJOURS SANS DOCUMENT
    # ========================================
    sejours_sans_doc = sejours[~sejours["sej_id"].isin(data_best["sej_id"])].copy()

    if len(sejours_sans_doc) > 0:
        print(f"   ℹ️ {len(sejours_sans_doc)} séjours sans aucun document rattaché")
        # Ajouter les colonnes manquantes avec NaN
        for col in data_best.columns:
            if col not in sejours_sans_doc.columns:
                sejours_sans_doc[col] = np.nan

        data_final = pd.concat([data_best, sejours_sans_doc], ignore_index=True)
    else:
        data_final = data_best

    # Vérifications finales
    nb_sejours_initial = len(sejours)
    nb_sejours_final = len(data_final)

    print(
        f"\n✅ Fusion terminée : {nb_sejours_initial} séjours → {nb_sejours_final} lignes"
    )

    nb_avec_ll = data_final["doc_val"].notna().sum()
    print(
        f"📊 Avec LL validée : {nb_avec_ll} ({nb_avec_ll / nb_sejours_final * 100:.1f}%)"
    )

    return data_final


def classify_sejours_iql(df: pd.DataFrame, matrice_path: str = None) -> pd.DataFrame:
    """
    Classifie les séjours selon la méthodologie IQL R v7

    Changements v7 :
    - Utilise del_val (≥ 0) au lieu de del_sorval
    - del_val = max(0, del_sorval) si spécialité associée
    - Si la jointure avec la matrice a déjà été faite dans merge_sejours_documents,
      on ne la refait pas

    Règles de classification:
    - "0j" : LL validée au plus tard le jour de la sortie (del_val == 0)
    - "1j+" : LL validée après la sortie (del_val > 0)
    - "sansLL" : Aucune LL validée OU pas de spécialité associée

    Args:
        df: DataFrame contenant les séjours et documents
        matrice_path: Chemin vers la matrice de spécialité (optionnel)

    Returns:
        DataFrame avec colonnes 'sej_spe_final' et 'sej_classe' ajoutées
    """
    df = df.copy()

    print("\n🏷️ Classification des séjours (IQL R v7)...")

    # ========================================
    # VÉRIFIER SI LA JOINTURE A DÉJÀ ÉTÉ FAITE
    # ========================================
    if "sej_spe" in df.columns and df["sej_spe"].notna().sum() > 0:
        print("   ℹ️ Spécialités déjà jointes dans merge_sejours_documents()")
        df["sej_spe_final"] = df["sej_spe"]
    else:
        print("   ℹ️ Jointure avec matrice de spécialité nécessaire")

        # Utiliser le chemin depuis settings si non fourni
        if matrice_path is None:
            matrice_path = settings.MATRICE_PATH

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

    # ========================================
    # CALCULER del_val (R v7)
    # ========================================
    # del_val = max(0, del_sorval) si spécialité associée
    # Sinon NA

    print("\n📏 Calcul de del_val (délai réajusté ≥ 0)...")

    df["del_val"] = df.apply(
        lambda row: max(0, row["del_sorval"])
        if pd.notna(row["del_sorval"])
        and not np.isinf(row["del_sorval"])
        and pd.notna(row["sej_spe_final"])
        else np.nan,
        axis=1,
    )

    nb_with_delval = df["del_val"].notna().sum()
    print(f"   ✅ del_val calculé pour {nb_with_delval} séjours")

    # ========================================
    # Classification selon del_val (pas del_sorval)
    # ========================================
    df["sej_classe"] = "sansLL"

    has_del_val = df["del_val"].notna()

    # Classification
    df.loc[has_del_val & (df["del_val"] == 0), "sej_classe"] = "0j"
    df.loc[has_del_val & (df["del_val"] > 0), "sej_classe"] = "1j+"

    print(f"\n📊 Classification finale :")
    for classe in ["0j", "1j+", "sansLL"]:
        count = (df["sej_classe"] == classe).sum()
        pct = count / len(df) * 100 if len(df) > 0 else 0
        print(f"   - {classe}: {count} ({pct:.1f}%)")

    return df


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

    print(f"\n📊 Calcul des statistiques de VALIDATION...")

    # Classifier les séjours
    df = classify_sejours_iql(df, matrice_path)

    # Statistiques globales
    total_sejours_all = len(df)

    # =================TABLEAU GAELLE SUR VALIDATION==================
    nb_ll_validees_all = df["doc_val"].notna().sum()
    pct_ll_validees_all = df["doc_val"].notna().mean() * 100
    taux_validation_J0_over_sejours_all = float((df["sej_classe"] == "0j").mean() * 100)
    delai_validation_moyenne_all = df["del_sorval"].mean()

    print(f"\n   📈 Statistiques globales :")
    print(f"      Total séjours : {total_sejours_all}")
    print(f"      LL validées : {nb_ll_validees_all} ({pct_ll_validees_all:.1f}%)")
    print(f"      Validées à J0 : {taux_validation_J0_over_sejours_all:.1f}%")
    print(f"      Délai moyen : {delai_validation_moyenne_all:.2f}j")

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
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    print(f"\n   ✅ Statistiques calculées pour {len(stats_par_spe)} spécialités")

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

    print(f"\n📊 Calcul des statistiques de DIFFUSION...")

    # Classifier les séjours
    df = classify_sejours_iql(df, matrice_path)

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

    print(f"\n   📈 Statistiques globales diffusion :")
    print(
        f"      LL diffusées : {nb_LL_diffuses_all} ({pct_diffuses_sur_validees_all:.1f}% des validées)"
    )
    print(f"      Diffusées à J0 validation : {tx_diffusion_a_J0_validation_all:.1f}%")

    # ==================================================================

    # Statistiques par spécialité
    stats_par_spe = []

    for spe in df["sej_spe_final"].dropna().unique():
        df_spe = df[df["sej_spe_final"] == spe]
        df_spe_dates = df_with_dates[df_with_dates["sej_spe_final"] == spe]
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
                else 0.0,
            }
        )

    # Trier par nombre total décroissant
    stats_par_spe = sorted(
        stats_par_spe, key=lambda x: x["total_sejours"], reverse=True
    )

    print(
        f"\n   ✅ Statistiques diffusion calculées pour {len(stats_par_spe)} spécialités"
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
        else 0.0,
        "par_specialite": stats_par_spe,
    }
