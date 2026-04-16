"""
Application FastAPI pour la génération de rapports sur les lettres de liaison
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from io import BytesIO
import traceback
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import time

from config import settings
from generate_files import generate_report_data
from excel_generator import generate_excel
from auth_db import init_db, list_users, create_user, update_user_role, delete_user
from auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_role,
)


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


# Créer l'application FastAPI
app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="API pour générer des rapports sur les indicateurs de lettres de liaison",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────
# Modèles Pydantic
# ──────────────────────────────────────────────

class ReportByDateRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD


class ReportBySejoursRequest(BaseModel):
    sejour_ids: List[str]


class ReportRequest(BaseModel):
    start_date: str  # Format: YYYY-MM-DD
    end_date: str  # Format: YYYY-MM-DD
    sejour_list: Optional[List[str]] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: Optional[str] = None
    role: str = "normal"
    auth_type: str = "local"


class UpdateUserRoleRequest(BaseModel):
    role: str


# ──────────────────────────────────────────────
# Pages HTML
# ──────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    with open("./src/static/login.html", encoding="utf-8") as f:
        return f.read()


@app.get("/", response_class=HTMLResponse)
async def ui():
    with open("./src/static/index.html", encoding="utf-8") as f:
        return f.read()


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with open("./src/static/admin.html", encoding="utf-8") as f:
        return f.read()


# ──────────────────────────────────────────────
# Auth API
# ──────────────────────────────────────────────

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects",
        )
    token = create_access_token(user["username"], user["role"])
    return {"access_token": token, "role": user["role"], "username": user["username"]}


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


# ──────────────────────────────────────────────
# Admin API
# ──────────────────────────────────────────────

@app.get("/api/admin/users")
async def admin_list_users(current_user: dict = Depends(require_role("admin"))):
    return list_users()


@app.post("/api/admin/users")
async def admin_create_user(
    request: CreateUserRequest,
    current_user: dict = Depends(require_role("admin")),
):
    if request.role not in ("admin", "expert", "normal"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    if request.auth_type not in ("local", "ldap"):
        raise HTTPException(status_code=400, detail="Type d'auth invalide")
    if request.auth_type == "local" and not request.password:
        raise HTTPException(
            status_code=400,
            detail="Un mot de passe est requis pour les comptes locaux",
        )

    user_id = create_user(
        username=request.username,
        password=request.password,
        role=request.role,
        auth_type=request.auth_type,
    )
    if user_id is None:
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur existe déjà")
    return {"id": user_id, "message": "Utilisateur créé"}


@app.put("/api/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    request: UpdateUserRoleRequest,
    current_user: dict = Depends(require_role("admin")),
):
    if request.role not in ("admin", "expert", "normal"):
        raise HTTPException(status_code=400, detail="Rôle invalide")
    if not update_user_role(user_id, request.role):
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Rôle mis à jour"}


@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    current_user: dict = Depends(require_role("admin")),
):
    if not delete_user(user_id):
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return {"message": "Utilisateur supprimé"}


# ──────────────────────────────────────────────
# Report API (protégé)
# ──────────────────────────────────────────────

@app.post("/api/report/by-date")
async def generate_report_by_date(
    request: ReportRequest,
    current_user: dict = Depends(get_current_user),
):
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
        t_report_start = time.perf_counter()
        data, stats_validation = generate_report_data(
            start_date=request.start_date,
            end_date=request.end_date,
            sejour_list=request.sejour_list,
        )
        t_report_end = time.perf_counter()
        print(f"[PROFILING] generate_report_data: {t_report_end - t_report_start:.3f}s")

        # Création du nom de fichier (pour le téléchargement uniquement)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_formatted = start.strftime("%d-%m-%Y")
        end_formatted = end.strftime("%d-%m-%Y")
        excel_filename = (
            f"LL_Rapport_{start_formatted}_au_{end_formatted}_{timestamp}.xlsx"
        )

        # Formater la période pour l'affichage dans le fichier
        period = f"{start.strftime('%d/%m/%Y')} au {end.strftime('%d/%m/%Y')}"

        # Les utilisateurs "normal" n'ont pas accès aux données brutes
        include_raw = current_user["role"] in ("admin", "expert")

        # Génération du fichier Excel en mémoire
        try:
            t_excel_start = time.perf_counter()
            excel_bytes = generate_excel(
                stats_validation=stats_validation,
                period=period,
                df_analysis=data,
                include_raw_data=include_raw,
            )
            t_excel_end = time.perf_counter()
            print(f"[PROFILING] generate_excel: {t_excel_end - t_excel_start:.3f}s")
            print(f"[PROFILING] TOTAL /api/report/by-date: {t_excel_end - t_report_start:.3f}s")

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
async def generate_report_by_sejours(
    request: ReportBySejoursRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Générer un rapport pour une liste de séjours spécifiques
    """
    try:
        if not request.sejour_ids:
            raise HTTPException(
                status_code=400,
                detail="Aucun numéro de séjour fourni. Veuillez fournir au moins un numéro de séjour.",
            )

        t_report_start = time.perf_counter()
        data, stats_validation = generate_report_data(
            start_date=None,
            end_date=None,
            sejour_list=request.sejour_ids,
        )
        t_report_end = time.perf_counter()
        print(f"[PROFILING] generate_report_data: {t_report_end - t_report_start:.3f}s")

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour les {len(request.sejour_ids)} séjours demandés",
            )

        # Nom de fichier pour le téléchargement
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nb_sejours = len(request.sejour_ids)
        excel_filename = f"LL_Rapport_{nb_sejours}_sejours_{timestamp}.xlsx"

        # Les utilisateurs "normal" n'ont pas accès aux données brutes
        include_raw = current_user["role"] in ("admin", "expert")

        # Génération du fichier Excel en mémoire
        try:
            t_excel_start = time.perf_counter()
            excel_bytes = generate_excel(
                stats_validation=stats_validation,
                period=f"{nb_sejours} séjours sélectionnés",
                df_analysis=data,
                include_raw_data=include_raw,
            )
            t_excel_end = time.perf_counter()
            print(f"[PROFILING] generate_excel: {t_excel_end - t_excel_start:.3f}s")
            print(f"[PROFILING] TOTAL /api/report/by-sejours: {t_excel_end - t_report_start:.3f}s")
        except Exception as excel_error:
            print(f"Erreur génération Excel : {excel_error}")
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
