"""
Script pour générer PowerPoint et email avec VOS DONNÉES
à partir d'un fichier CSV ou Excel

Usage:
    python test_avec_mes_donnees.py chemin/vers/mes_donnees.csv
    python test_avec_mes_donnees.py chemin/vers/mes_donnees.xlsx
"""

import pandas as pd
import asyncio
from datetime import datetime
import os
import sys
from pptx_generator import generate_powerpoint
from email_sender import send_monthly_report


def load_data_from_file(file_path):
    """
    Charger les données depuis un fichier CSV ou Excel

    Le fichier doit contenir au minimum ces colonnes :
    - sej_spe : Spécialité
    - del_val : Délai de validation (en jours, ou NaN si pas de LL)

    Colonnes optionnelles mais recommandées :
    - pat_ipp : IPP du patient
    - sej_id : Numéro de séjour
    - sej_ent : Date d'entrée
    - sej_sor : Date de sortie
    - doc_val : Date de validation
    """

    print(f"📂 Chargement des données depuis : {file_path}")

    # Détecter le type de fichier
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Format de fichier non supporté. Utilisez .csv ou .xlsx")

    print(f"   ✅ {len(df)} lignes chargées")
    print(f"   ✅ Colonnes : {', '.join(df.columns)}")

    # Vérifier les colonnes minimales
    colonnes_requises = ["sej_spe", "del_val"]
    colonnes_manquantes = [col for col in colonnes_requises if col not in df.columns]

    if colonnes_manquantes:
        raise ValueError(f"Colonnes manquantes : {', '.join(colonnes_manquantes)}")

    return df


def calculate_stats_from_data(df):
    """
    Calculer les statistiques à partir des données
    """

    print()
    print("📈 Calcul des statistiques...")

    stats = {}

    # Total des séjours
    total_sejours = len(df)
    stats["total_sejours"] = total_sejours

    # Séjours avec LL validée
    sejours_valides = df["del_val"].notna().sum()
    stats["sejours_valides"] = sejours_valides

    # Taux de validation
    taux_validation = (
        (sejours_valides / total_sejours * 100) if total_sejours > 0 else 0
    )
    stats["taux_validation"] = round(taux_validation, 1)

    # Taux de validation le jour de la sortie (J0)
    sejours_j0 = (df["del_val"] == 0).sum()
    taux_j0 = (sejours_j0 / sejours_valides * 100) if sejours_valides > 0 else 0
    stats["taux_validation_j0"] = round(taux_j0, 1)

    # Délai moyen de validation
    delai_moyen = df["del_val"].mean()
    stats["delai_moyen_validation"] = (
        round(delai_moyen, 1) if not pd.isna(delai_moyen) else 0
    )

    # Statistiques par spécialité
    stats_spe = []

    for spe in df["sej_spe"].dropna().unique():
        spe_data = df[df["sej_spe"] == spe]

        spe_total = len(spe_data)
        spe_valides = spe_data["del_val"].notna().sum()
        spe_taux_val = (spe_valides / spe_total * 100) if spe_total > 0 else 0

        spe_j0 = (spe_data["del_val"] == 0).sum()
        spe_taux_j0 = (spe_j0 / spe_valides * 100) if spe_valides > 0 else 0

        spe_delai = spe_data["del_val"].mean()

        # Stats de diffusion (simplifiées)
        spe_diffuses = spe_valides
        spe_pct_diffuses = 100.0  # Pour ce test, on considère que tout est diffusé

        stats_spe.append(
            {
                "specialite": spe,
                "nb_total": spe_total,
                "nb_valides": spe_valides,
                "taux_validation": round(spe_taux_val, 1),
                "taux_validation_j0": round(spe_taux_j0, 1),
                "delai_moyen": round(spe_delai, 1) if not pd.isna(spe_delai) else 0,
                "nb_diffuses": spe_diffuses,
                "pct_valides": round(spe_pct_diffuses, 1),
            }
        )

    stats["par_specialite"] = sorted(stats_spe, key=lambda x: x["specialite"])

    print(f"   ✅ Statistiques calculées")
    print(f"   - Total séjours : {stats['total_sejours']}")
    print(
        f"   - Séjours validés : {stats['sejours_valides']} ({stats['taux_validation']}%)"
    )
    print(f"   - Taux validation J0 : {stats['taux_validation_j0']}%")
    print(f"   - Délai moyen : {stats['delai_moyen_validation']} jour(s)")
    print(f"   - Spécialités : {len(stats['par_specialite'])}")

    return stats


def calculate_diffusion_stats(df):
    """
    Calculer les statistiques de diffusion (simplifiées pour le test)
    """

    diffusion_data = df[df["del_val"].notna()].copy()

    stats = {}
    stats["total_diffuses"] = len(diffusion_data)
    stats["pct_diffuses"] = 100.0
    stats["taux_diffusion_j0"] = (
        ((diffusion_data["del_val"] == 0).sum() / len(diffusion_data) * 100)
        if len(diffusion_data) > 0
        else 0
    )
    stats["delai_moyen_diffusion"] = (
        round(diffusion_data["del_val"].mean(), 1)
        if not diffusion_data["del_val"].isna().all()
        else 0
    )
    stats["par_specialite"] = []

    return stats


async def generate_report_from_data(df, period_label="Période personnalisée"):
    """
    Générer le rapport à partir des données
    """

    # Calculer les statistiques
    stats_validation = calculate_stats_from_data(df)
    stats_diffusion = calculate_diffusion_stats(df)

    # Créer les dossiers de sortie
    output_dir = "outputs/test"
    os.makedirs(output_dir, exist_ok=True)

    # Générer le PowerPoint
    print()
    print("📊 Génération du PowerPoint...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pptx_path = f"{output_dir}/Rapport_LL_{timestamp}.pptx"

    try:
        generate_powerpoint(stats_validation, stats_diffusion, pptx_path, period_label)
        print(f"   ✅ PowerPoint généré : {pptx_path}")
    except Exception as e:
        print(f"   ❌ Erreur PowerPoint : {e}")
        import traceback

        traceback.print_exc()
        return False

    # Exporter les données en Excel
    print()
    print("📈 Export des données en Excel...")
    excel_path = f"{output_dir}/Donnees_LL_{timestamp}.xlsx"

    try:
        df.to_excel(excel_path, index=False)
        print(f"   ✅ Excel généré : {excel_path}")
    except Exception as e:
        print(f"   ❌ Erreur Excel : {e}")
        return False

    # Demander si on veut envoyer l'email
    print()
    print("📧 Envoi de l'email...")
    print()
    print("⚠️  Voulez-vous envoyer l'email ? (o/n)")
    reponse = input("   Réponse : ").strip().lower()

    if reponse in ["o", "oui", "y", "yes"]:
        print()
        print("   📤 Envoi en cours...")

        try:
            success = await send_monthly_report(
                period_label, stats_validation, pptx_path, excel_path
            )

            if success:
                print("   ✅ Email envoyé avec succès !")
            else:
                print("   ❌ Échec de l'envoi de l'email")
                return False
        except Exception as e:
            print(f"   ❌ Erreur email : {e}")
            import traceback

            traceback.print_exc()
            return False
    else:
        print("   ⏭️  Envoi d'email ignoré")

    print()
    print("=" * 80)
    print("✅ GÉNÉRATION TERMINÉE AVEC SUCCÈS")
    print("=" * 80)
    print()
    print("📁 Fichiers générés dans :", output_dir)
    print(f"   - {os.path.basename(pptx_path)}")
    print(f"   - {os.path.basename(excel_path)}")
    print()

    return True


def main():
    """Point d'entrée principal"""

    print()
    print(
        "╔════════════════════════════════════════════════════════════════════════════╗"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "║         📊 GÉNÉRATION RAPPORT AVEC VOS DONNÉES 📊                          ║"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "╚════════════════════════════════════════════════════════════════════════════╝"
    )
    print()

    # Vérifier les arguments
    if len(sys.argv) < 2:
        print("❌ Usage : python test_avec_mes_donnees.py chemin/vers/fichier.csv")
        print()
        print("Exemples :")
        print("  python test_avec_mes_donnees.py mes_donnees.csv")
        print("  python test_avec_mes_donnees.py exports/requete_bernard.xlsx")
        print()
        print("Le fichier doit contenir au minimum les colonnes :")
        print("  - sej_spe : Spécialité")
        print("  - del_val : Délai de validation (en jours)")
        print()
        return 1

    file_path = sys.argv[1]

    # Vérifier que le fichier existe
    if not os.path.exists(file_path):
        print(f"❌ Fichier introuvable : {file_path}")
        return 1

    try:
        # Charger les données
        df = load_data_from_file(file_path)

        # Demander la période
        print()
        print("📅 Période du rapport (ex: 01/01/2025 au 31/07/2025) :")
        period = input("   Période : ").strip()

        if not period:
            period = "Période personnalisée"

        # Générer le rapport
        print()
        result = asyncio.run(generate_report_from_data(df, period))

        if result:
            print("🎉 Rapport généré avec succès !")
            return 0
        else:
            print("❌ Des erreurs ont été rencontrées")
            return 1

    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
