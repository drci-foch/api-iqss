"""
Script pour l'envoi automatique mensuel des rapports
À exécuter en tant que tâche planifiée (cron ou Windows Task Scheduler)
"""

import asyncio
from datetime import datetime, timedelta
from calendar import monthrange
import sys
import os

# Ajouter le répertoire parent au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processing import generate_report_data
from pptx_generator import generate_powerpoint
from email_sender import send_monthly_report


async def send_monthly_report_task():
    """
    Générer et envoyer le rapport mensuel automatique
    """
    try:
        # Calculer la période du mois précédent
        today = datetime.now()

        # Premier jour du mois dernier
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)

        # Dernier jour du mois dernier
        last_day = monthrange(start_date.year, start_date.month)[1]
        end_date = datetime(start_date.year, start_date.month, last_day)

        print(
            f"Génération du rapport mensuel pour la période: {start_date.date()} au {end_date.date()}"
        )

        # Générer les données
        data, stats_validation, stats_diffusion = generate_report_data(
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        print(f"Données générées: {len(data)} séjours traités")
        print(f"Taux de validation: {stats_validation['taux_validation']}%")

        # Créer les noms de fichiers
        period_str = f"{start_date.strftime('%B_%Y')}".lower()
        timestamp = datetime.now().strftime("%Y%m%d")

        output_dir = "outputs/monthly"
        os.makedirs(output_dir, exist_ok=True)

        pptx_path = f"{output_dir}/LL_Rapport_Mensuel_{period_str}_{timestamp}.pptx"
        excel_path = f"{output_dir}/LL_Donnees_Mensuelles_{period_str}_{timestamp}.xlsx"

        # Générer le PowerPoint
        print("Génération du PowerPoint...")
        generate_powerpoint(
            stats_validation,
            stats_diffusion,
            pptx_path,
            f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}",
        )

        # Exporter les données en Excel
        print("Export des données Excel...")
        data.to_excel(excel_path, index=False)

        # Envoyer l'email
        print("Envoi de l'email...")
        success = await send_monthly_report(
            f"{start_date.strftime('%B %Y')}", stats_validation, pptx_path, excel_path
        )

        if success:
            print("✅ Rapport mensuel envoyé avec succès!")
            return True
        else:
            print("❌ Échec de l'envoi du rapport mensuel")
            return False

    except Exception as e:
        print(f"❌ Erreur lors de la génération du rapport mensuel: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("GÉNÉRATION ET ENVOI DU RAPPORT MENSUEL")
    print("=" * 60)
    print(f"Date d'exécution: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()

    # Exécuter la tâche asynchrone
    result = asyncio.run(send_monthly_report_task())

    print()
    print("=" * 60)
    if result:
        print("SUCCÈS: Rapport mensuel généré et envoyé")
    else:
        print("ÉCHEC: Problème lors de la génération ou de l'envoi")
    print("=" * 60)

    return 0 if result else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
