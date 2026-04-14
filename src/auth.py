"""
Authentification : JWT, LDAP, et dépendances FastAPI
"""

from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from config import settings
from auth_db import get_user, verify_password

security = HTTPBearer()


def authenticate_ldap(username: str, password: str) -> bool:
    """Tente une authentification LDAP. Retourne True si succès."""
    if not settings.LDAP_SERVER:
        return False
    try:
        import ldap3

        server = ldap3.Server(settings.LDAP_SERVER, get_info=ldap3.NONE)
        # Construire le DN utilisateur — adapter selon la structure LDAP de l'entreprise
        user_dn = f"{username}@{settings.LDAP_BASE_DN}"
        conn = ldap3.Connection(server, user=user_dn, password=password)
        result = conn.bind()
        conn.unbind()
        return result
    except Exception as e:
        print(f"[AUTH] Erreur LDAP : {e}")
        return False


def authenticate_user(username: str, password: str) -> dict | None:
    """
    Authentifie un utilisateur.
    - En production : tente LDAP d'abord, puis vérifie que l'user existe dans la DB locale
    - Sinon : authentification locale uniquement
    """
    user = get_user(username)

    if settings.APP_ENV == "production":
        # Tenter LDAP
        if authenticate_ldap(username, password):
            if user is None:
                # L'utilisateur LDAP n'a pas encore de compte local
                # → il doit être créé par un admin d'abord
                return None
            return user

        # Fallback : auth locale (pour les comptes admin/seed)
        if user and user["password"] and user["auth_type"] == "local":
            if verify_password(password, user["password"]):
                return user
        return None
    else:
        # Environnement non-production : auth locale uniquement
        if user is None:
            return None
        if user["password"] is None:
            return None
        if verify_password(password, user["password"]):
            return user
        return None


def create_access_token(username: str, role: str) -> str:
    """Crée un JWT signé."""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Décode et valide un JWT. Lève une exception si invalide."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide",
            )
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dependency FastAPI : extrait l'utilisateur courant du JWT."""
    return decode_token(credentials.credentials)


def require_role(*allowed_roles: str):
    """
    Retourne une dependency FastAPI qui vérifie que l'utilisateur a un rôle autorisé.
    Usage : Depends(require_role("admin"))
    """

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès non autorisé pour ce rôle",
            )
        return current_user

    return role_checker
