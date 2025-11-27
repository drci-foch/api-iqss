"""
Script de test pour générer un PowerPoint et envoyer un email
SANS interroger les bases de données

Ce script utilise des données fictives pour tester :
1. La génération du PowerPoint
2. L'export Excel
3. L'envoi d'email

Usage: python test/test_ppt_email.py (depuis la racine du projet)
"""

import sys
import os

# Ajouter le dossier parent (racine du projet) au path Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

import pandas as pd
import asyncio
from datetime import datetime, timedelta

# Maintenant on peut importer nos modules
try:
    from src.pptx_generator import generate_powerpoint
    from src.email_sender import send_monthly_report
except ImportError:
    # Si dans src/ n'existe pas, essayer import direct
    try:
        from pptx_generator import generate_powerpoint
        from email_sender import send_monthly_report
    except ImportError as e:
        print(f"❌ Erreur d'import : {e}")
        print()
        print("Assurez-vous que les fichiers suivants existent :")
        print("  - src/pptx_generator_v2.py (ou pptx_generator_v2.py à la racine)")
        print("  - src/email_sender.py (ou email_sender.py à la racine)")
        sys.exit(1)

# ============================================================================
# DONNÉES FICTIVES - À REMPLACER PAR VOS VRAIES DONNÉES
# ============================================================================


def create_fake_data():
    """
    Créer des données fictives qui simulent le résultat des requêtes

    Vous pouvez remplacer ces données par vos vraies données en :
    1. Exportant le résultat de la requête de Bernard en CSV
    2. Le chargeant ici avec pd.read_csv()
    """

    # Données de séjours fictifs
    data = []

    specialites = [
        "VASCULAIRE",
        "NEUROCHIRURGIE",
        "CARDIOLOGIE",
        "OBSTETRIQUE",
        "GÉRIATRIE",
        "REANIMATION",
        "THORACIQUE",
        "GYNECOLOGIE",
        "ONCOLOGIE",
        "DIGESTIF",
        "UHCD",
        "UROLOGIE",
        "MIP",
        "PSYCHIATRIE",
        "PNEUMOLOGIE",
        "MEDECINE INTERNE",
        "NEPHROLOGIE",
    ]

    sejour_id = 10000000

    for spe in specialites:
        # Nombre de séjours par spécialité (aléatoire)
        nb_sejours = 50 + (hash(spe) % 100)

        for i in range(nb_sejours):
            sejour_id += 1

            # Dates fictives
            sej_sor = datetime(2025, 7, 15) - timedelta(days=i % 60)
            sej_ent = sej_sor - timedelta(days=2)

            # Simuler validation
            has_ll = (hash(f"{spe}{i}") % 100) > 8  # 92% ont une LL

            if has_ll:
                # Délai de validation (0, 1, 2 ou 3 jours après sortie)
                delai = hash(f"{spe}{i}validation") % 10
                if delai > 2:
                    delai = 0  # 70% validés à J0
                elif delai > 1:
                    delai = 1  # 20% à J1
                else:
                    delai = 2  # 10% à J2+

                doc_val = sej_sor + timedelta(days=delai)
                del_val = float(delai)
            else:
                doc_val = None
                del_val = None

            data.append(
                {
                    "pat_ipp": f"12345{sejour_id % 10000:04d}",
                    "sej_id": sejour_id,
                    "sej_ent": sej_ent,
                    "sej_sor": sej_sor,
                    "sej_uf": f"{hash(spe) % 900 + 100:03d}",
                    "sej_spe": spe,
                    "doc_id": sejour_id + 50000 if has_ll else None,
                    "doc_val": doc_val,
                    "del_val": del_val,
                    "sej_classe": "0j"
                    if del_val == 0
                    else ("1j+" if del_val and del_val > 0 else "sansLL"),
                }
            )

    return pd.DataFrame(data)


def calculate_stats_from_data(df):
    """
    Calculer les statistiques à partir des données
    (comme le ferait data_processing.py)
    """

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

        # Stats de diffusion (simplifiées pour le test)
        spe_diffuses = spe_valides
        spe_pct_diffuses = (spe_diffuses / spe_valides * 100) if spe_valides > 0 else 0

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

    return stats


def calculate_diffusion_stats(df):
    """
    Calculer les statistiques de diffusion
    (comme le ferait data_processing.py)
    """

    diffusion_data = df[df["del_val"].notna()].copy()

    stats = {}

    # Total des documents diffusés
    total_diffuses = len(diffusion_data)
    stats["total_diffuses"] = total_diffuses

    # Pourcentage par rapport aux validés
    total_valides = df["del_val"].notna().sum()
    pct_diffuses = (total_diffuses / total_valides * 100) if total_valides > 0 else 0
    stats["pct_diffuses"] = round(pct_diffuses, 1)

    # Taux de diffusion à J0 de la validation
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

    # Par spécialité (déjà inclus dans stats_validation)
    stats["par_specialite"] = []

    return stats


# ============================================================================
# FONCTION PRINCIPALE DE TEST
# ============================================================================


async def test_generation():
    """
    Fonction principale de test
    """

    print("=" * 80)
    print("🧪 TEST DE GÉNÉRATION POWERPOINT ET ENVOI EMAIL")
    print("=" * 80)
    print()

    # ========================================================================
    # OPTION 1 : Utiliser des données fictives
    # ========================================================================
    print("📊 Génération de données fictives...")
    df = create_fake_data()
    print(f"   ✅ {len(df)} séjours générés")
    print()

    # ========================================================================
    # OPTION 2 : Charger vos vraies données depuis un CSV
    # ========================================================================
    # Décommentez les lignes suivantes si vous avez un fichier CSV avec vos données
    # print("📊 Chargement des données depuis le CSV...")
    # df = pd.read_csv('mes_donnees.csv')
    # print(f"   ✅ {len(df)} séjours chargés")
    # print()

    # Calculer les statistiques
    print("📈 Calcul des statistiques...")
    stats_validation = calculate_stats_from_data(df)
    stats_diffusion = calculate_diffusion_stats(df)
    print(f"   ✅ Stats calculées")
    print(f"   - Total séjours : {stats_validation['total_sejours']}")
    print(f"   - Séjours validés : {stats_validation['sejours_valides']}")
    print(f"   - Taux validation : {stats_validation['taux_validation']}%")
    print(f"   - Taux validation J0 : {stats_validation['taux_validation_j0']}%")
    print()

    # Créer les dossiers de sortie
    output_dir = "outputs/test"
    os.makedirs(output_dir, exist_ok=True)

    # Générer le PowerPoint
    print("📊 Génération du PowerPoint...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pptx_path = f"{output_dir}/TEST_Rapport_LL_{timestamp}.pptx"

    try:
        generate_powerpoint(
            stats_validation,
            stats_diffusion,
            pptx_path,
            "01/01/2025 au 31/07/2025 (TEST)",
        )
        print(f"   ✅ PowerPoint généré : {pptx_path}")
    except Exception as e:
        print(f"   ❌ Erreur PowerPoint : {e}")
        import traceback

        traceback.print_exc()
        return False

    print()

    # Exporter les données en Excel
    print("📈 Export des données en Excel...")
    excel_path = f"{output_dir}/TEST_Donnees_LL_{timestamp}.xlsx"

    try:
        df.to_excel(excel_path, index=False)
        print(f"   ✅ Excel généré : {excel_path}")
    except Exception as e:
        print(f"   ❌ Erreur Excel : {e}")
        return False

    print()

    # Demander si on veut envoyer l'email
    print("📧 Envoi de l'email de test...")
    print()
    print("⚠️  Voulez-vous envoyer l'email de test ? (o/n)")
    reponse = input("   Réponse : ").strip().lower()

    if reponse in ["o", "oui", "y", "yes"]:
        print()
        print("   📤 Envoi en cours...")

        try:
            success = await send_monthly_report(
                "Janvier à Juillet 2025 (TEST)", stats_validation, pptx_path, excel_path
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
    print("✅ TEST TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    print()
    print("📁 Fichiers générés dans :", output_dir)
    print(f"   - {os.path.basename(pptx_path)}")
    print(f"   - {os.path.basename(excel_path)}")
    print()

    return True


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================


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
        "║           🧪 TEST - GÉNÉRATION POWERPOINT & ENVOI EMAIL 🧪                 ║"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "║  Ce script teste la génération du PowerPoint et l'envoi d'email           ║"
    )
    print(
        "║  SANS interroger les bases de données (utilise des données fictives)      ║"
    )
    print(
        "║                                                                            ║"
    )
    print(
        "╚════════════════════════════════════════════════════════════════════════════╝"
    )
    print()

    # Vérifier que les modules nécessaires sont importés
    try:
        # Essayer d'importer config pour vérifier .env
        try:
            from src.config import settings
        except ImportError:
            from config import settings
        print("✅ Configuration chargée")
    except Exception as e:
        print(f"⚠️  Configuration non chargée : {e}")
        print()
        print("💡 Le fichier .env n'est pas nécessaire pour générer le PowerPoint")
        print("   Il est seulement nécessaire pour l'envoi d'email")

    print()

    # Exécuter le test
    try:
        result = asyncio.run(test_generation())

        if result:
            print("🎉 Tous les tests sont passés !")
            return 0
        else:
            print("❌ Des erreurs ont été rencontrées")
            return 1
    except KeyboardInterrupt:
        print()
        print("❌ Test interrompu par l'utilisateur")
        return 1


if __name__ == "__main__":
    sys.exit(main())
