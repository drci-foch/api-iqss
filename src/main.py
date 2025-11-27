"""
Application FastAPI pour la génération de rapports sur les lettres de liaison
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import traceback
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import pandas as pd
import os
from pathlib import Path
import numpy as np
import pandas as pd

from config import settings
from data_processing import generate_report_data
from pptx_generator import generate_powerpoint
from email_sender import send_monthly_report, send_test_email

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API pour générer des rapports sur les indicateurs de lettres de liaison",
)

# Créer les dossiers nécessaires
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)


# Modèles Pydantic
class ReportByDateRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    send_email: bool = False


class ReportBySejoursRequest(BaseModel):
    sejour_ids: List[str]
    send_email: bool = False


class ReportResponse(BaseModel):
    success: bool
    message: str
    pptx_path: Optional[str] = None
    excel_path: Optional[str] = None
    statistics: Optional[dict] = None


# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Page d'accueil avec interface utilisateur"""
    html_content = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Indicateurs Lettres de Liaison - Hôpital Foch</title>
        <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #f5f7fa;
                min-height: 100vh;
                padding: 0;
            }
            
            /* Header Foch style */
            .top-header {
                background: #00529B;
                color: white;
                padding: 20px 40px;
                box-shadow: 0 2px 10px rgba(0, 82, 155, 0.15);
            }
            .top-header h1 {
                font-size: 24px;
                font-weight: 600;
                margin-bottom: 5px;
                letter-spacing: -0.5px;
            }
            .top-header .subtitle {
                font-size: 14px;
                opacity: 0.9;
                font-weight: 300;
            }
            
            /* Container */
            .container {
                max-width: 1000px;
                margin: 40px auto;
                padding: 0 20px;
            }
            
            /* Intro section */
            .intro-section {
                background: white;
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
                border-left: 4px solid #00529B;
            }
            .intro-section h2 {
                color: #00529B;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .intro-section p {
                color: #555;
                line-height: 1.6;
                font-size: 15px;
            }
            
            /* Form sections */
            .form-section {
                background: white;
                border-radius: 8px;
                padding: 30px;
                margin-bottom: 25px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
                transition: box-shadow 0.3s ease;
            }
            .form-section:hover {
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            .form-section h2 {
                color: #333;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 20px;
                padding-bottom: 12px;
                border-bottom: 2px solid #e8edf2;
            }
            .form-section h2::before {
                content: '';
                display: inline-block;
                width: 4px;
                height: 18px;
                background: #00529B;
                margin-right: 10px;
                vertical-align: middle;
            }
            
            /* Form groups */
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
                font-size: 14px;
            }
            .form-group input, .form-group textarea {
                width: 100%;
                padding: 12px 15px;
                border: 1px solid #d1d9e0;
                border-radius: 4px;
                font-size: 14px;
                font-family: 'Open Sans', sans-serif;
                transition: all 0.3s ease;
                background: #fafbfc;
            }
            .form-group input:focus, .form-group textarea:focus {
                outline: none;
                border-color: #00529B;
                background: white;
                box-shadow: 0 0 0 3px rgba(0, 82, 155, 0.1);
            }
            .form-group textarea {
                min-height: 120px;
                resize: vertical;
                line-height: 1.5;
            }
            
            /* Checkbox */
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 12px;
                background: #f8f9fb;
                border-radius: 4px;
            }
            .checkbox-group input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
                accent-color: #00529B;
            }
            .checkbox-group label {
                margin: 0;
                font-weight: 400;
                cursor: pointer;
            }
            
            /* Buttons */
            .btn {
                background: #00529B;
                color: white;
                border: none;
                padding: 14px 30px;
                border-radius: 4px;
                font-size: 15px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .btn:hover {
                background: #003d73;
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0, 82, 155, 0.25);
            }
            .btn:active {
                transform: translateY(0);
            }
            .btn-secondary {
                background: #28a745;
            }
            .btn-secondary:hover {
                background: #218838;
            }
            
            /* Results */
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 4px;
                display: none;
                border-left: 4px solid;
            }
            .result.success {
                background: #e8f5e9;
                border-color: #28a745;
                color: #155724;
                display: block;
            }
            .result.error {
                background: #ffebee;
                border-color: #dc3545;
                color: #721c24;
                display: block;
            }
            .result h3 {
                margin-bottom: 12px;
                font-size: 16px;
            }
            
            /* Loading */
            .loading {
                text-align: center;
                padding: 40px 20px;
                display: none;
                background: white;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
            }
            .loading.active {
                display: block;
            }
            .spinner {
                border: 3px solid #e8edf2;
                border-top: 3px solid #00529B;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 0.8s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .loading p {
                color: #666;
                font-size: 15px;
            }
            
            /* Download links */
            .download-links {
                margin-top: 15px;
            }
            .download-links a {
                display: inline-block;
                margin: 8px 10px 8px 0;
                padding: 10px 20px;
                background: #00529B;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                transition: all 0.3s ease;
                font-size: 14px;
                font-weight: 600;
            }
            .download-links a:hover {
                background: #003d73;
                transform: translateY(-2px);
                box-shadow: 0 2px 8px rgba(0, 82, 155, 0.3);
            }
            
            /* Footer */
            .footer {
                text-align: center;
                padding: 30px 20px;
                color: #666;
                font-size: 13px;
                margin-top: 40px;
            }
            .footer a {
                color: #00529B;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="top-header">
            <h1>Indicateurs Lettres de Liaison</h1>
            <div class="subtitle">L'expertise à visage humain • Hôpital Foch • 40 rue Worth, 92150 Suresnes</div>
        </div>
        
        <div class="container">
            <div class="intro-section">
                <h2>Génération automatique de rapports</h2>
                <p>Cet outil vous permet de générer des rapports détaillés sur les indicateurs de lettres de liaison pour améliorer la qualité de la prise en charge et la coordination des soins.</p>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Génération du rapport en cours, veuillez patienter...</p>
            </div>

            <div class="form-section">
                <h2>Rapport par Période</h2>
                <form id="dateForm">
                    <div class="form-group">
                        <label for="start_date">Date de début</label>
                        <input type="date" id="start_date" name="start_date" required>
                    </div>
                    <div class="form-group">
                        <label for="end_date">Date de fin</label>
                        <input type="date" id="end_date" name="end_date" required>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" id="send_email_date" name="send_email">
                        <label for="send_email_date">Envoyer le rapport par email</label>
                    </div>
                    <button type="submit" class="btn">Générer le rapport</button>
                </form>
            </div>

            <div class="form-section">
                <h2>Rapport par Numéros de Séjour</h2>
                <form id="sejoursForm">
                    <div class="form-group">
                        <label for="sejour_ids">Numéros de séjour (un par ligne)</label>
                        <textarea id="sejour_ids" name="sejour_ids" placeholder="Exemple:
12345678
87654321
11223344" required></textarea>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" id="send_email_sejours" name="send_email">
                        <label for="send_email_sejours">Envoyer le rapport par email</label>
                    </div>
                    <button type="submit" class="btn">Générer le rapport</button>
                </form>
            </div>

            <div class="form-section">
                <h2>Test de Configuration Email</h2>
                <p style="margin-bottom: 20px; color: #666; line-height: 1.6;">Envoyez un email de test pour vérifier que la configuration de messagerie fonctionne correctement.</p>
                <button onclick="sendTestEmail()" class="btn btn-secondary">Envoyer un email de test</button>
            </div>



            <div class="result" id="result"></div>
        </div>

        <div class="footer">
            <p>Hôpital Foch - 40 rue Worth, 92150 Suresnes | <a href="tel:0146252000">01 46 25 20 00</a></p>
            <p style="margin-top: 5px;">© 2025 Fondation Foch - Tous droits réservés</p>
        </div>

        <script>
            // Définir les dates par défaut (début d'année jusqu'à aujourd'hui)
            window.onload = function() {
                const today = new Date();
                const startOfYear = new Date(today.getFullYear(), 0, 1);
                
                document.getElementById('start_date').valueAsDate = startOfYear;
                document.getElementById('end_date').valueAsDate = today;
            };

            // Formulaire par dates
            document.getElementById('dateForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const startDate = document.getElementById('start_date').value;
                const endDate = document.getElementById('end_date').value;
                const sendEmail = document.getElementById('send_email_date').checked;
                
                await generateReport('/api/report/by-date', {
                    start_date: startDate,
                    end_date: endDate,
                    send_email: sendEmail
                });
            });

            // Formulaire par séjours
            document.getElementById('sejoursForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const sejourIds = document.getElementById('sejour_ids').value
                    .split('\\n')
                    .map(s => s.trim())
                    .filter(s => s.length > 0);
                const sendEmail = document.getElementById('send_email_sejours').checked;
                
                await generateReport('/api/report/by-sejours', {
                    sejour_ids: sejourIds,
                    send_email: sendEmail
                });
            });

            // Fonction générique pour générer un rapport
            async function generateReport(endpoint, data) {
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.classList.add('active');
                result.style.display = 'none';
                
                try {
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(data)
                    });
                    
                    const responseData = await response.json();
                    
                    loading.classList.remove('active');
                    
                    if (responseData.success) {
                        result.className = 'result success';
                        let html = `<h3>✓ ${responseData.message}</h3>`;
                        
                        if (responseData.statistics) {
                            html += `
                                <div style="margin-top: 20px; padding: 15px; background: #f8f9fb; border-radius: 4px;">
                                    <strong style="color: #00529B;">Résumé des indicateurs :</strong>
                                    <ul style="margin-top: 12px; margin-left: 20px; line-height: 1.8;">
                                        <li><strong>Total séjours :</strong> ${responseData.statistics.total_sejours}</li>
                                        <li><strong>Séjours validés :</strong> ${responseData.statistics.sejours_valides}</li>
                                        <li><strong>Taux de validation :</strong> ${responseData.statistics.taux_validation}%</li>
                                        <li><strong>Taux validation J0 :</strong> ${responseData.statistics.taux_validation_j0}%</li>
                                        <li><strong>Délai moyen :</strong> ${responseData.statistics.delai_moyen_validation} jour(s)</li>
                                    </ul>
                                </div>
                            `;
                        }
                        
                        if (responseData.pptx_path || responseData.excel_path) {
                            html += '<div class="download-links"><strong>Télécharger les fichiers :</strong><br>';
                            if (responseData.pptx_path) {
                                html += `<a href="/download/${responseData.pptx_path.split('/').pop()}" download>📊 Présentation PowerPoint</a>`;
                            }
                            if (responseData.excel_path) {
                                html += `<a href="/download/${responseData.excel_path.split('/').pop()}" download>📈 Données Excel</a>`;
                            }
                            html += '</div>';
                        }
                        
                        result.innerHTML = html;
                    } else {
                        result.className = 'result error';
                        result.innerHTML = `<h3>✗ Erreur</h3><p>${responseData.message}</p>`;
                    }
                    
                } catch (error) {
                    loading.classList.remove('active');
                    result.className = 'result error';
                    result.innerHTML = `<h3>✗ Erreur de connexion</h3><p>Impossible de communiquer avec le serveur : ${error.message}</p>`;
                }
            }

            // Test email
            async function sendTestEmail() {
                const loading = document.getElementById('loading');
                const result = document.getElementById('result');
                
                loading.classList.add('active');
                result.style.display = 'none';
                
                try {
                    const response = await fetch('/api/test-email', {
                        method: 'POST'
                    });
                    
                    const data = await response.json();
                    
                    loading.classList.remove('active');
                    
                    if (data.success) {
                        result.className = 'result success';
                        result.innerHTML = `<h3>✓ ${data.message}</h3>`;
                    } else {
                        result.className = 'result error';
                        result.innerHTML = `<h3>✗ Erreur</h3><p>${data.message}</p>`;
                    }
                    
                } catch (error) {
                    loading.classList.remove('active');
                    result.className = 'result error';
                    result.innerHTML = `<h3>✗ Erreur de connexion</h3><p>Impossible d'envoyer l'email de test : ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


def convert_to_json(obj):
    """Convertit numpy/pandas en types JSON"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.replace({np.nan: None}).to_dict(orient="records")
    elif isinstance(obj, dict):
        return {k: convert_to_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json(item) for item in obj]
    return obj


class ReportRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    sejour_list: Optional[List[str]] = None


def convert_to_serializable(obj):
    """
    Convertit les types numpy/pandas en types Python natifs pour JSON
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    elif isinstance(obj, pd.DataFrame):
        return obj.replace({np.nan: None}).to_dict(orient="records")
    elif isinstance(obj, pd.Series):
        return obj.replace({np.nan: None}).to_dict()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif pd.isna(obj):
        return None
    return obj


@app.post("/api/report/by-date")
async def generate_report_by_date(request: ReportRequest):
    """
    Génère un rapport d'indicateurs de lettres de liaison pour une période donnée
    """
    try:
        print(f"📅 Génération du rapport du {request.start_date} au {request.end_date}")

        # Validation des dates
        try:
            start = datetime.strptime(request.start_date, "%Y-%m-%d")
            end = datetime.strptime(request.end_date, "%Y-%m-%d")

            if start > end:
                raise HTTPException(
                    status_code=400,
                    detail="La date de début doit être antérieure à la date de fin",
                )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Format de date invalide. Utilisez YYYY-MM-DD. Erreur: {str(e)}",
            )

        # Génération du rapport
        data, stats_validation, stats_diffusion = generate_report_data(
            start_date=request.start_date,
            end_date=request.end_date,
            sejour_list=request.sejour_list,
        )

        # Génération du PowerPoint
        pptx_path = None
        try:
            # Créer le nom du fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            start_formatted = start.strftime("%d-%m-%Y")
            end_formatted = end.strftime("%d-%m-%Y")
            output_filename = (
                f"LL_Rapport_{start_formatted}_au_{end_formatted}_{timestamp}.pptx"
            )
            output_path = os.path.join("outputs", output_filename)

            # Créer le dossier outputs s'il n'existe pas
            os.makedirs("outputs", exist_ok=True)

            # Formater la période pour l'affichage
            period = f"{start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"

            # Générer le PowerPoint avec les bons arguments
            generate_powerpoint(
                stats_validation=stats_validation,
                stats_diffusion=stats_diffusion,
                output_path=output_path,
                period=period,
                logo_path=None,  # Ajoutez le chemin de votre logo si disponible
            )

            pptx_path = output_path
            print(f"✅ PowerPoint généré : {pptx_path}")

        except Exception as pptx_error:
            print(f"⚠️ Erreur génération PowerPoint : {pptx_error}")
            traceback.print_exc()
            # On continue même si le PowerPoint échoue

        # Conversion des types numpy/pandas pour la sérialisation JSON
        response_data = {
            "status": "success",
            "message": f"Rapport généré avec succès pour la période du {request.start_date} au {request.end_date}",
            "period": {"start_date": request.start_date, "end_date": request.end_date},
            "stats_validation": convert_to_serializable(stats_validation),
            "stats_diffusion": convert_to_serializable(stats_diffusion),
            "pptx_path": pptx_path,
            "generated_at": datetime.now().isoformat(),
        }

        print(f"✅ Réponse API préparée avec succès")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERREUR DÉTAILLÉE dans generate_report_by_date:")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )

    except HTTPException:
        # Re-lever les HTTPException sans les wrapper
        raise
    except Exception as e:
        # Log de l'erreur complète
        print(f"❌ ERREUR DÉTAILLÉE dans generate_report_by_date:")
        print(traceback.format_exc())

        # Retourner une erreur 500 avec le message
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


@app.post("/api/report/by-sejours", response_model=ReportResponse)
async def generate_report_by_sejours(
    request: ReportBySejoursRequest, background_tasks: BackgroundTasks
):
    """Générer un rapport pour une liste de séjours"""
    try:
        if not request.sejour_ids:
            raise HTTPException(status_code=400, detail="Aucun numéro de séjour fourni")

        # Générer les données
        data, stats_validation, stats_diffusion = generate_report_data(
            sejour_list=request.sejour_ids
        )

        # Créer le nom du fichier
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nb_sejours = len(request.sejour_ids)

        pptx_filename = f"LL_Rapport_{nb_sejours}_sejours_{timestamp}.pptx"
        pptx_path = OUTPUT_DIR / pptx_filename

        excel_filename = f"LL_Donnees_{nb_sejours}_sejours_{timestamp}.xlsx"
        excel_path = OUTPUT_DIR / excel_filename

        # Générer le PowerPoint
        generate_powerpoint(
            stats_validation,
            stats_diffusion,
            str(pptx_path),
            f"{nb_sejours} séjours sélectionnés",
        )

        # Exporter les données en Excel
        data.to_excel(str(excel_path), index=False)

        # Envoyer par email si demandé
        if request.send_email:
            background_tasks.add_task(
                send_monthly_report,
                f"{nb_sejours} séjours",
                stats_validation,
                str(pptx_path),
                str(excel_path),
            )

        return ReportResponse(
            success=True,
            message=f"Rapport généré avec succès pour {nb_sejours} séjours",
            pptx_path=str(pptx_path),
            excel_path=str(excel_path),
            statistics=stats_validation,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


@app.post("/api/test-email")
async def test_email():
    """Envoyer un email de test"""
    try:
        success = await send_test_email()

        if success:
            return {
                "success": True,
                "message": f"Email de test envoyé avec succès à {settings.EMAIL_TO}",
            }
        else:
            return {"success": False, "message": "Échec de l'envoi de l'email de test"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}"
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Télécharger un fichier généré"""
    file_path = OUTPUT_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/octet-stream"
    )


@app.get("/api/health")
async def health_check():
    """Vérifier l'état de l'API"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
