"""
Application FastAPI pour la génération de rapports sur les lettres de liaison
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import pandas as pd
import os
from pathlib import Path

from config import settings
from data_processing import generate_report_data
from pptx_generator import generate_powerpoint
from email_sender import send_monthly_report, send_test_email

# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API pour générer des rapports sur les indicateurs de lettres de liaison"
)

# Créer les dossiers nécessaires
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)


# Modèles Pydantic
class ReportByDateRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str    # Format: YYYY-MM-DD
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
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                color: #00529B;
                font-size: 28px;
                margin-bottom: 10px;
            }
            .header p {
                color: #666;
                font-size: 16px;
            }
            .form-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 30px;
                margin-bottom: 20px;
            }
            .form-section h2 {
                color: #333;
                font-size: 20px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 2px solid #00529B;
            }
            .form-group {
                margin-bottom: 20px;
            }
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 500;
            }
            .form-group input, .form-group textarea {
                width: 100%;
                padding: 12px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
            }
            .form-group input:focus, .form-group textarea:focus {
                outline: none;
                border-color: #00529B;
            }
            .form-group textarea {
                min-height: 100px;
                resize: vertical;
            }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .checkbox-group input[type="checkbox"] {
                width: auto;
                cursor: pointer;
            }
            .btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                width: 100%;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
            }
            .btn:active {
                transform: translateY(0);
            }
            .btn-secondary {
                background: linear-gradient(135deg, #6aa84f 0%, #38761d 100%);
                margin-top: 10px;
            }
            .result {
                margin-top: 30px;
                padding: 20px;
                border-radius: 10px;
                display: none;
            }
            .result.success {
                background: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
                display: block;
            }
            .result.error {
                background: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
                display: block;
            }
            .loading {
                text-align: center;
                padding: 20px;
                display: none;
            }
            .loading.active {
                display: block;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #00529B;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .download-links {
                margin-top: 15px;
            }
            .download-links a {
                display: inline-block;
                margin: 5px 10px 5px 0;
                padding: 10px 20px;
                background: #00529B;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background 0.3s;
            }
            .download-links a:hover {
                background: #003d73;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏥 Indicateurs Lettres de Liaison</h1>
                <p>Génération automatique de rapports - Hôpital Foch</p>
            </div>

            <div class="form-section">
                <h2>📅 Rapport par Période</h2>
                <form id="dateForm">
                    <div class="form-group">
                        <label for="start_date">Date de début:</label>
                        <input type="date" id="start_date" name="start_date" required>
                    </div>
                    <div class="form-group">
                        <label for="end_date">Date de fin:</label>
                        <input type="date" id="end_date" name="end_date" required>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" id="send_email_date" name="send_email">
                        <label for="send_email_date">Envoyer par email</label>
                    </div>
                    <button type="submit" class="btn">Générer le rapport</button>
                </form>
            </div>

            <div class="form-section">
                <h2>🔢 Rapport par Numéros de Séjour</h2>
                <form id="sejoursForm">
                    <div class="form-group">
                        <label for="sejour_ids">Numéros de séjour (un par ligne):</label>
                        <textarea id="sejour_ids" name="sejour_ids" placeholder="Exemple:
12345678
87654321
11223344" required></textarea>
                    </div>
                    <div class="form-group checkbox-group">
                        <input type="checkbox" id="send_email_sejours" name="send_email">
                        <label for="send_email_sejours">Envoyer par email</label>
                    </div>
                    <button type="submit" class="btn">Générer le rapport</button>
                </form>
            </div>

            <div class="form-section">
                <h2>📧 Test Email</h2>
                <p style="margin-bottom: 15px; color: #666;">Envoyer un email de test pour vérifier la configuration</p>
                <button onclick="sendTestEmail()" class="btn btn-secondary">Envoyer un email de test</button>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Génération du rapport en cours...</p>
            </div>

            <div class="result" id="result"></div>
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
                        let html = `<h3>✅ ${responseData.message}</h3>`;
                        
                        if (responseData.statistics) {
                            html += `
                                <div style="margin-top: 15px;">
                                    <strong>Résumé:</strong>
                                    <ul style="margin-top: 10px; margin-left: 20px;">
                                        <li>Total séjours: ${responseData.statistics.total_sejours}</li>
                                        <li>Séjours validés: ${responseData.statistics.sejours_valides}</li>
                                        <li>Taux de validation: ${responseData.statistics.taux_validation}%</li>
                                        <li>Taux validation J0: ${responseData.statistics.taux_validation_j0}%</li>
                                        <li>Délai moyen: ${responseData.statistics.delai_moyen_validation} jour(s)</li>
                                    </ul>
                                </div>
                            `;
                        }
                        
                        if (responseData.pptx_path || responseData.excel_path) {
                            html += '<div class="download-links"><strong>Télécharger:</strong><br>';
                            if (responseData.pptx_path) {
                                html += `<a href="/download/${responseData.pptx_path.split('/').pop()}" download>📊 PowerPoint</a>`;
                            }
                            if (responseData.excel_path) {
                                html += `<a href="/download/${responseData.excel_path.split('/').pop()}" download>📈 Excel</a>`;
                            }
                            html += '</div>';
                        }
                        
                        result.innerHTML = html;
                    } else {
                        result.className = 'result error';
                        result.innerHTML = `<h3>❌ Erreur</h3><p>${responseData.message}</p>`;
                    }
                    
                } catch (error) {
                    loading.classList.remove('active');
                    result.className = 'result error';
                    result.innerHTML = `<h3>❌ Erreur</h3><p>Erreur de connexion: ${error.message}</p>`;
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
                        result.innerHTML = `<h3>✅ ${data.message}</h3>`;
                    } else {
                        result.className = 'result error';
                        result.innerHTML = `<h3>❌ Erreur</h3><p>${data.message}</p>`;
                    }
                    
                } catch (error) {
                    loading.classList.remove('active');
                    result.className = 'result error';
                    result.innerHTML = `<h3>❌ Erreur</h3><p>Erreur de connexion: ${error.message}</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/api/report/by-date", response_model=ReportResponse)
async def generate_report_by_date(request: ReportByDateRequest, background_tasks: BackgroundTasks):
    """Générer un rapport pour une période donnée"""
    try:
        # Valider les dates
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d")
        
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="La date de fin doit être après la date de début")
        
        # Générer les données
        data, stats_validation, stats_diffusion = generate_report_data(
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Créer le nom du fichier
        period_str = f"{start_date.strftime('%d-%m-%Y')}_au_{end_date.strftime('%d-%m-%Y')}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        pptx_filename = f"LL_Rapport_{period_str}_{timestamp}.pptx"
        pptx_path = OUTPUT_DIR / pptx_filename
        
        excel_filename = f"LL_Donnees_{period_str}_{timestamp}.xlsx"
        excel_path = OUTPUT_DIR / excel_filename
        
        # Générer le PowerPoint
        generate_powerpoint(
            stats_validation,
            stats_diffusion,
            str(pptx_path),
            f"{start_date.strftime('%d/%m/%Y')} au {end_date.strftime('%d/%m/%Y')}"
        )
        
        # Exporter les données en Excel
        data.to_excel(str(excel_path), index=False)
        
        # Envoyer par email si demandé
        if request.send_email:
            background_tasks.add_task(
                send_monthly_report,
                period_str,
                stats_validation,
                str(pptx_path),
                str(excel_path)
            )
        
        return ReportResponse(
            success=True,
            message="Rapport généré avec succès",
            pptx_path=str(pptx_path),
            excel_path=str(excel_path),
            statistics=stats_validation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}")


@app.post("/api/report/by-sejours", response_model=ReportResponse)
async def generate_report_by_sejours(request: ReportBySejoursRequest, background_tasks: BackgroundTasks):
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
            f"{nb_sejours} séjours sélectionnés"
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
                str(excel_path)
            )
        
        return ReportResponse(
            success=True,
            message=f"Rapport généré avec succès pour {nb_sejours} séjours",
            pptx_path=str(pptx_path),
            excel_path=str(excel_path),
            statistics=stats_validation
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}")


@app.post("/api/test-email")
async def test_email():
    """Envoyer un email de test"""
    try:
        success = await send_test_email()
        
        if success:
            return {
                "success": True,
                "message": f"Email de test envoyé avec succès à {settings.EMAIL_TO}"
            }
        else:
            return {
                "success": False,
                "message": "Échec de l'envoi de l'email de test"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'envoi de l'email: {str(e)}")


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Télécharger un fichier généré"""
    file_path = OUTPUT_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Fichier non trouvé")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )


@app.get("/api/health")
async def health_check():
    """Vérifier l'état de l'API"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)