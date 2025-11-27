"""
Script pour configurer la tâche planifiée mensuelle
"""

import platform
import subprocess
import os
from pathlib import Path


def setup_cron_linux():
    """
    Configurer une tâche cron sur Linux
    À exécuter le 1er de chaque mois à 8h00
    """
    script_dir = Path(__file__).parent.absolute()
    python_path = subprocess.check_output(["which", "python3"]).decode().strip()

    cron_command = f"0 8 1 * * {python_path} {script_dir}/monthly_report.py >> {script_dir}/logs/monthly_report.log 2>&1"

    print("Pour configurer la tâche planifiée sur Linux:")
    print("\n1. Ouvrez crontab:")
    print("   crontab -e")
    print("\n2. Ajoutez cette ligne:")
    print(f"   {cron_command}")
    print("\n3. Sauvegardez et quittez")
    print("\nLa tâche s'exécutera le 1er de chaque mois à 8h00")


def setup_task_windows():
    """
    Configurer une tâche planifiée sur Windows
    """
    script_dir = Path(__file__).parent.absolute()
    python_path = (
        subprocess.check_output(["where", "python"]).decode().split("\n")[0].strip()
    )

    task_name = "HopitalFoch_LL_MensuelReport"

    # Commande pour créer la tâche planifiée
    xml_config = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T08:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth>
          <Day>1</Day>
        </DaysOfMonth>
        <Months>
          <January />
          <February />
          <March />
          <April />
          <May />
          <June />
          <July />
          <August />
          <September />
          <October />
          <November />
          <December />
        </Months>
      </ScheduleByMonth>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>{script_dir}\\monthly_report.py</Arguments>
      <WorkingDirectory>{script_dir}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    xml_path = script_dir / "task_schedule.xml"
    with open(xml_path, "w", encoding="utf-16") as f:
        f.write(xml_config)

    print("Pour configurer la tâche planifiée sur Windows:")
    print("\n1. Exécutez cette commande en tant qu'administrateur:")
    print(f'   schtasks /create /tn "{task_name}" /xml "{xml_path}"')
    print("\n2. Ou utilisez le Planificateur de tâches Windows:")
    print("   - Ouvrez 'Planificateur de tâches'")
    print("   - Créez une nouvelle tâche")
    print("   - Déclencheur: Le 1er de chaque mois à 8h00")
    print(f"   - Action: Démarrer le programme '{python_path}'")
    print(f"   - Arguments: '{script_dir}\\monthly_report.py'")
    print("\nLa tâche s'exécutera le 1er de chaque mois à 8h00")


def main():
    """Configuration principale"""
    print("=" * 70)
    print("CONFIGURATION DE LA TÂCHE PLANIFIÉE MENSUELLE")
    print("=" * 70)
    print()

    # Créer le dossier de logs
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    system = platform.system()

    if system == "Linux" or system == "Darwin":  # Darwin = macOS
        setup_cron_linux()
    elif system == "Windows":
        setup_task_windows()
    else:
        print(f"Système d'exploitation non supporté: {system}")

    print()
    print("=" * 70)
    print("NOTES IMPORTANTES:")
    print("=" * 70)
    print("1. Assurez-vous que les connexions aux bases de données sont configurées")
    print("2. Vérifiez que les paramètres SMTP sont corrects dans le fichier .env")
    print("3. Testez manuellement le script avant de planifier:")
    print(f"   python monthly_report.py")
    print()


if __name__ == "__main__":
    main()
