"""
Module d'envoi d'emails avec pièces jointes
"""

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from config import settings
import os
from datetime import datetime


async def send_email(
    subject: str,
    body: str,
    to_emails: List[str],
    cc_emails: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
) -> bool:
    """
    Envoyer un email avec pièces jointes

    Args:
        subject: Sujet de l'email
        body: Corps de l'email (HTML)
        to_emails: Liste des destinataires
        cc_emails: Liste des destinataires en copie
        attachments: Liste des chemins de fichiers à attacher

    Returns:
        True si envoi réussi, False sinon
    """
    try:
        # Créer le message
        msg = MIMEMultipart()
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = ", ".join(to_emails)
        if cc_emails:
            msg["Cc"] = ", ".join(cc_emails)
        msg["Subject"] = subject

        # Ajouter le corps de l'email
        msg.attach(MIMEText(body, "html"))

        # Ajouter les pièces jointes
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(file_path)}",
                        )
                        msg.attach(part)

        # Envoyer l'email
        all_recipients = to_emails + (cc_emails if cc_emails else [])

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )

        return True

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email: {e}")
        return False


def generate_monthly_report_email(period: str, stats: dict) -> str:
    """
    Générer le contenu HTML de l'email mensuel

    Args:
        period: Période du rapport
        stats: Statistiques du rapport

    Returns:
        Contenu HTML de l'email
    """
    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                color: #333;
            }}
            .header {{
                background-color: #00529B;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                padding: 20px;
            }}
            .stats-box {{
                background-color: #f0f0f0;
                border-left: 4px solid #00529B;
                padding: 15px;
                margin: 20px 0;
            }}
            .stats-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            .stats-table th {{
                background-color: #00529B;
                color: white;
                padding: 10px;
                text-align: left;
            }}
            .stats-table td {{
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }}
            .highlight {{
                font-size: 24px;
                font-weight: bold;
                color: #00529B;
            }}
            .footer {{
                margin-top: 30px;
                padding: 20px;
                background-color: #f9f9f9;
                border-top: 2px solid #00529B;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Rapport Mensuel - Indicateurs Lettres de Liaison</h1>
            <p>Période: {period}</p>
        </div>
        
        <div class="content">
            <h2>Résumé Exécutif</h2>
            
            <div class="stats-box">
                <h3>Indicateurs Clés</h3>
                <table class="stats-table">
                    <tr>
                        <td><strong>Total des séjours analysés:</strong></td>
                        <td class="highlight">{stats.get("total_sejours", 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Séjours avec LL validée:</strong></td>
                        <td class="highlight">{stats.get("sejours_valides", 0)}</td>
                    </tr>
                    <tr>
                        <td><strong>Taux de validation:</strong></td>
                        <td class="highlight">{stats.get("taux_validation", 0)}%</td>
                    </tr>
                    <tr>
                        <td><strong>Taux de validation à J0:</strong></td>
                        <td class="highlight">{stats.get("taux_validation_j0", 0)}%</td>
                    </tr>
                    <tr>
                        <td><strong>Délai moyen de validation:</strong></td>
                        <td class="highlight">{stats.get("delai_moyen_validation", 0)} jour(s)</td>
                    </tr>
                </table>
            </div>
            
            <h3>Performance par Spécialité</h3>
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Spécialité</th>
                        <th>Nb Séjours</th>
                        <th>Taux Validation</th>
                        <th>Taux Validation J0</th>
                        <th>Délai Moyen</th>
                    </tr>
                </thead>
                <tbody>
"""

    # Ajouter les statistiques par spécialité
    for spe in stats.get("par_specialite", [])[:10]:  # Top 10
        html += f"""
                    <tr>
                        <td>{spe["specialite"]}</td>
                        <td>{spe["nb_total"]}</td>
                        <td>{spe["taux_validation"]}%</td>
                        <td>{spe["taux_validation_j0"]}%</td>
                        <td>{spe["delai_moyen"]}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
            
            <div class="footer">
                <p><strong>Documents joints:</strong></p>
                <ul>
                    <li>Présentation PowerPoint complète avec tableaux détaillés</li>
                    <li>Fichier Excel avec les données brutes (requête Bernard)</li>
                </ul>
                
                <p style="margin-top: 20px;">
                    <em>Ce rapport est généré automatiquement le premier jour de chaque mois.</em><br>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


async def send_monthly_report(
    period: str, stats_validation: dict, pptx_path: str, excel_path: str
) -> bool:
    """
    Envoyer le rapport mensuel automatique

    Args:
        period: Période du rapport
        stats_validation: Statistiques de validation
        pptx_path: Chemin du fichier PowerPoint
        excel_path: Chemin du fichier Excel

    Returns:
        True si envoi réussi, False sinon
    """
    subject = f"Rapport Mensuel - Indicateurs Lettres de Liaison - {period}"
    body = generate_monthly_report_email(period, stats_validation)

    to_emails = [settings.EMAIL_TO]
    cc_emails = [settings.EMAIL_CC] if settings.EMAIL_CC else []

    attachments = [pptx_path]
    if excel_path and os.path.exists(excel_path):
        attachments.append(excel_path)

    return await send_email(
        subject=subject,
        body=body,
        to_emails=to_emails,
        cc_emails=cc_emails,
        attachments=attachments,
    )


async def send_test_email() -> bool:
    """
    Envoyer un email de test

    Returns:
        True si envoi réussi, False sinon
    """
    subject = "Test - Système de Reporting Lettres de Liaison"
    body = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #00529B;">Test du Système de Reporting</h2>
        <p>Cet email confirme que le système de reporting automatique des indicateurs 
        de lettres de liaison est correctement configuré.</p>
        
        <p><strong>Prochaines étapes:</strong></p>
        <ul>
            <li>Configurer les connexions aux bases de données GAM et ESL</li>
            <li>Vérifier le fichier de mapping UF/Spécialités</li>
            <li>Planifier l'envoi automatique mensuel</li>
        </ul>
        
        <p style="margin-top: 30px; color: #666;">
            <em>Système généré automatiquement</em>
        </p>
    </body>
    </html>
    """

    return await send_email(
        subject=subject,
        body=body,
        to_emails=["s.ben-yahia@hopital-foch.com"],
        cc_emails=None,
        attachments=None,
    )
