"""
Module de connexion aux bases de données GAM et ESL
"""

import pandas as pd
from typing import Optional, List
from config import settings
import re
import pytds
import oracledb


class DatabaseConnector:
    """Classe pour gérer les connexions aux bases de données"""

    def __init__(self):
        self._conn_gam = None
        self._conn_esl = None

    @property
    def connect_gam(self):
        """Connexion à Oracle (GAM) avec lazy loading"""
        if self._conn_gam is None:
            try:
                dsn = oracledb.makedsn(
                    settings.GAM_HOST,
                    settings.GAM_PORT,
                    service_name=settings.GAM_SERVICE,
                )
                self._conn_gam = oracledb.connect(
                    user=settings.GAM_USER, password=settings.GAM_PASSWORD, dsn=dsn
                )

            except Exception as e:
                print(f"❌ Erreur connexion GAM: {e}")
                raise
        return self._conn_gam

    @property
    def connect_esl(self):
        """Connexion à SQL Server (EASILY) avec lazy loading"""
        if self._conn_esl is None:
            try:
                self._conn_esl = pytds.connect(
                    server=settings.ESL_HOST,
                    database=settings.ESL_DATABASE,
                    user=settings.ESL_USER,
                    password=settings.ESL_PASSWORD,
                    autocommit=True,
                )
                print("✅ Connexion EASILY (SQL Server) réussie")
            except Exception as e:
                print(f"❌ Erreur connexion EASILY: {e}")
                raise
        return self._conn_esl

    def disconnect_all(self):
        """Fermer toutes les connexions"""
        if self._conn_gam:
            self._conn_gam.close()
            self._conn_gam = None
        if self._conn_esl:
            self._conn_esl.close()
            self._conn_esl = None


def get_sejours_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sejour_list: Optional[list] = None,
) -> pd.DataFrame:
    """
    Récupérer les données des séjours depuis GAM

    Args:
        start_date: Date de début (format YYYY-MM-DD)
        end_date: Date de fin (format YYYY-MM-DD)
        sejour_list: Liste optionnelle de numéros de séjours

    Returns:
        DataFrame avec les données des séjours
    """
    db = DatabaseConnector()
    try:
        conn = db.connect_gam  # Sans parenthèses
        cursor = conn.cursor()

        # Construction de la requête SQL de base
        base_query = """
        SELECT 
            HO_MANUMDOS as pat_ipp, 
            ho_num as sej_id, 
            ho_ddeb as sej_ent, 
            ho_dfin as sej_sor,
            mha.mh_ufcode as uf_sortie
        FROM drci.hospitalisation 
        LEFT JOIN drci.mouv_hospi mha ON ho_num = mh_honum  
        LEFT JOIN drci.serveur_identite ON HO_MANUMDOS = SI_NUMDOS 
        LEFT JOIN drci.uf ON mha.mh_ufcode = uf_code 
        WHERE 1=1
            AND mh_der = 'X'
            AND ho_recode = 'HC'
            AND ho_dfin IS NOT NULL
            AND (ho_dfin - ho_ddeb) >= 1
            AND uf_hjour IS NULL
            AND mha.mh_ufcode NOT IN ('TEST99','392A','348U','537U','553A','294U','294E','350B','393A','393B','393C','549B','394B','675B')
            AND (Si_DATEDEC IS NULL OR TRUNC(Si_DATEDEC) != TRUNC(ho_dfin))
        """

        # Initialiser les filtres
        filters = []

        # Filtre par dates
        if start_date and end_date:
            filters.append(
                f"ho_dfin BETWEEN TO_DATE('{start_date}', 'YYYY-MM-DD') AND TO_DATE('{end_date}', 'YYYY-MM-DD')"
            )
        elif not sejour_list:
            # Par défaut uniquement si aucune date ET aucune liste de séjours
            filters.append(
                "ho_dfin BETWEEN TRUNC(SYSDATE, 'YYYY') AND LAST_DAY(ADD_MONTHS(SYSDATE, -3))"
            )

        # Filtre par liste de séjours (peut se combiner avec les dates)
        if sejour_list:
            # Nettoyer la liste des séjours
            sejour_list_clean = [str(s).strip() for s in sejour_list if str(s).strip()]

            if sejour_list_clean:
                sejour_str = "','".join(sejour_list_clean)
                filters.append(f"ho_num IN ('{sejour_str}')")

        # Appliquer les filtres
        if filters:
            base_query += " AND " + " AND ".join(filters)

        print("📊 Requête SQL séjours:")
        print(base_query)
        print()

        cursor.execute(base_query)

        # Récupération des noms de colonnes
        columns = [
            desc[0].lower() for desc in cursor.description
        ]  # ✅ Conversion en minuscules
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)

        print(f"✅ Séjours récupérés : {len(df)} lignes")

        # Vérification que les colonnes existent avant de les manipuler
        if "pat_ipp" in df.columns:
            df["pat_ipp"] = df["pat_ipp"].apply(clean_ipp)
        else:
            print(
                f"⚠️ Colonne 'pat_ipp' introuvable. Colonnes disponibles: {df.columns.tolist()}"
            )
            raise KeyError(
                "La colonne 'pat_ipp' n'a pas été trouvée dans les résultats de la requête"
            )

        # Extraction du code UF (3 premiers caractères)
        if "uf_sortie" in df.columns:
            df["sej_uf"] = df["uf_sortie"].str[:3]
        else:
            print(f"⚠️ Colonne 'uf_sortie' introuvable")

        return df

    except Exception as e:
        print(f"❌ Erreur dans get_sejours_data: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.disconnect_all()


def get_documents_data(
    start_date: Optional[str] = None, end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Récupérer les données des documents depuis ESL
    """
    db = DatabaseConnector()

    try:
        conn = db.connect_esl  # Sans parenthèses

        # Construction de la requête SQL
        query = """
        SELECT DISTINCT
            fic.fiche_id as doc_id,
            pat.pat_ipp as pat_ipp,
            dos.dos_libelle_court as doc_spe,
            fsl.fos_libelle as doc_libelle,
            fic.fic_date_creation as doc_cre,
            fhs.fic_date_statut_validation as doc_val,
            df2.fic_date_creation as doc_creamere,
            dest.dest_diffusion_date as date_diffusion
        FROM NOYAU.patient.patient pat
            LEFT JOIN DOMINHO.dominho.FICHE fic ON pat.pat_id = fic.patient_id AND fic.fic_suppr = 0
            LEFT JOIN DOMINHO.dominho.FICHE_HISTORIQUE_STATUT fhs ON fhs.fiche_id = fic.fiche_id AND fhs.fic_statut_validation_id = 3
            INNER JOIN DOMINHO.dominho.FORMULAIRE_SELECTION fsl ON fic.formulaire_selection_id = fsl.formulaire_selection_id 
                AND fsl.fos_libelle NOT LIKE '%extraction%'
                AND fsl.fos_libelle NOT LIKE '%CR Lettre de Liaison SSPI Foch%'
            INNER JOIN dominho.dominho.FORMULAIRE frm ON fsl.formulaire_id = frm.formulaire_id 
                AND frm.type_document_code IN ('00209','00082')
                AND for_courrier = 1
            LEFT JOIN DOMINHO.dominho.DOSSIER_SPECIALITE dos ON dos.dossier_specialite_id = fic.dossier_specialite_id
            LEFT JOIN dominho.dominho.FICHE df2 ON (df2.fiche_id = fic.fiche_mere_id AND df2.fic_suppr != 1)
            LEFT JOIN BOITE_ENVOI.BOITE_ENVOI.DOCUMENT doc ON doc.document_id = fic.document_id
            LEFT JOIN BOITE_ENVOI.BOITE_ENVOI.DESTINATAIRE dest on dest.doc_id = doc.doc_id 
        WHERE 1=1
            AND fsl.fos_libelle NOT LIKE '%Word Direct%'
        """

        # Ajout des conditions de date
        if start_date and end_date:
            query += f" AND fhs.fic_date_statut_validation BETWEEN '{start_date}' AND '{end_date}'"
        else:
            pass

        # ✅ SOLUTION : Utiliser pandas directement avec pyodbc
        df = pd.read_sql(query, conn)

        # Conversion des dates
        if "doc_cre" in df.columns:
            df["doc_cre"] = pd.to_datetime(df["doc_cre"]).dt.date
        if "doc_val" in df.columns:
            df["doc_val"] = pd.to_datetime(df["doc_val"]).dt.date
        if "doc_creamere" in df.columns:
            df["doc_creamere"] = pd.to_datetime(df["doc_creamere"]).dt.date

        # Nettoyage des IPP
        if "pat_ipp" in df.columns:
            df["pat_ipp"] = df["pat_ipp"].apply(clean_ipp)

        # Construction de la clé doc_key à partir du libellé
        if "doc_libelle" in df.columns:
            df["doc_key"] = df["doc_libelle"].apply(create_doc_key)

        return df

    except Exception as e:
        print(f"❌ Erreur dans get_documents_data: {e}")
        import traceback

        traceback.print_exc()
        raise
    finally:
        db.disconnect_all()


def clean_ipp(ipp) -> Optional[str]:
    """
    Nettoyer et valider un IPP

    Args:
        ipp: Numéro IPP à nettoyer

    Returns:
        IPP nettoyé ou None si invalide
    """
    if pd.isna(ipp):
        return None

    ipp_str = str(int(float(str(ipp).strip()))).strip()

    if re.match(r"^\d{9}$", ipp_str):
        return ipp_str

    return None


def create_doc_key(libelle: str) -> str:
    """
    Créer une clé de document à partir du libellé

    Args:
        libelle: Libellé du document

    Returns:
        Clé simplifiée du document
    """
    if pd.isna(libelle):
        return ""

    # Suppression des patterns inutiles (similaire à masac en R)
    key = re.sub(
        r"foch|CR Lettre de Liaison|CR|HDJ|\.", "", libelle, flags=re.IGNORECASE
    )
    key = key.strip().lower()

    return key
