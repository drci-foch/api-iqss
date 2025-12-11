"""
Application FastAPI pour la génération de rapports sur les lettres de liaison
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from io import BytesIO
import traceback
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import pandas as pd
import os
from pathlib import Path
import numpy as np
from config import settings
from generate_files import generate_report_data
from excel_generator import generate_excel


# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API pour générer des rapports sur les indicateurs de lettres de liaison",
)


# Modèles Pydantic
class ReportByDateRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD


class ReportBySejoursRequest(BaseModel):
    sejour_ids: List[str]


class ReportRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    sejour_list: Optional[List[str]] = None


@app.get("/", response_class=HTMLResponse)
async def ui():
    with open(
        "./src/static/index.html",
        encoding="utf-8",
    ) as f:
        return f.read()


@app.post("/api/report/by-date")
async def generate_report_by_date(request: ReportRequest):
    """
    Génère un rapport d'indicateurs de lettres de liaison pour une période donnée
    """
    try:
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

        # Génération du rapport (données)
        data, stats_validation, stats_diffusion = generate_report_data(
            start_date=request.start_date,
            end_date=request.end_date,
            sejour_list=request.sejour_list,
        )

        # Création du nom de fichier (pour le téléchargement uniquement)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_formatted = start.strftime("%d-%m-%Y")
        end_formatted = end.strftime("%d-%m-%Y")
        excel_filename = (
            f"LL_Rapport_{start_formatted}_au_{end_formatted}_{timestamp}.xlsx"
        )

        # Formater la période pour l'affichage dans le fichier
        period = f"{start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"

        # Génération du fichier Excel en mémoire
        try:
            excel_bytes = generate_excel(
                stats_validation,
                stats_diffusion,
                period,
                df_analysis=data,  # Ajouter le DataFrame
            )

        except Exception as excel_error:
            print(f"Erreur génération Excel : {excel_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération du fichier Excel: {str(excel_error)}",
            )

        # Retour de la réponse sous forme de téléchargement
        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{excel_filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


@app.post("/api/report/by-sejours")
async def generate_report_by_sejours(request: ReportBySejoursRequest):
    """
    Générer un rapport pour une liste de séjours spécifiques
    """
    try:
        if not request.sejour_ids:
            raise HTTPException(
                status_code=400,
                detail="Aucun numéro de séjour fourni. Veuillez fournir au moins un numéro de séjour.",
            )

        data, stats_validation, stats_diffusion = generate_report_data(
            start_date=None,
            end_date=None,
            sejour_list=request.sejour_ids,
        )

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour les {len(request.sejour_ids)} séjours demandés",
            )

        # Nom de fichier pour le téléchargement
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nb_sejours = len(request.sejour_ids)
        excel_filename = f"LL_Rapport_{nb_sejours}_sejours_{timestamp}.xlsx"

        # Génération du fichier Excel en mémoire
        try:
            excel_bytes = generate_excel(
                stats_validation=stats_validation,
                stats_diffusion=stats_diffusion,
                period=f"{nb_sejours} séjours sélectionnés",
                df_analysis=data,
            )
            print("✅ Excel généré en mémoire")
        except Exception as excel_error:
            print(f"❌ Erreur génération Excel : {excel_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la génération du fichier Excel: {str(excel_error)}",
            )

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{excel_filename}"'},
        )

    except HTTPException:
        raise
    except Exception as e:
        print("ERREUR dans generate_report_by_sejours:")
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la génération du rapport: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
