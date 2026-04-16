"""
Gestion de la base de données d'authentification (SQLite)
"""

import sqlite3
import os
from datetime import datetime
import bcrypt
from config import settings


def get_db_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialise la base SQLite et crée la table users si elle n'existe pas."""
    os.makedirs(os.path.dirname(settings.DB_PATH), exist_ok=True)
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT,
            role TEXT NOT NULL DEFAULT 'normal',
            auth_type TEXT NOT NULL DEFAULT 'local',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()

    # Seed admin si aucun admin n'existe
    admin = conn.execute(
        "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    if admin is None:
        create_user(
            username=settings.ADMIN_SEED_USERNAME,
            password=settings.ADMIN_SEED_PASSWORD,
            role="admin",
            auth_type="local",
            conn=conn,
        )
        print(f"[AUTH] Admin seed créé : {settings.ADMIN_SEED_USERNAME}")

    conn.close()


def create_user(username: str, password: str | None, role: str, auth_type: str, conn=None):
    """Crée un utilisateur. Retourne l'id ou None si le username existe déjà."""
    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8") if password else None
    try:
        conn.execute(
            "INSERT INTO users (username, password, role, auth_type, created_at) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, role, auth_type, datetime.now().isoformat()),
        )
        conn.commit()
        user_id = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()["id"]
    except sqlite3.IntegrityError:
        if close_conn:
            conn.close()
        return None

    if close_conn:
        conn.close()
    return user_id


def get_user(username: str):
    """Retourne un utilisateur par username, ou None."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(user) if user else None


def get_user_by_id(user_id: int):
    """Retourne un utilisateur par id, ou None."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None


def list_users():
    """Retourne la liste de tous les utilisateurs (sans les passwords)."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT id, username, role, auth_type, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_user_role(user_id: int, role: str) -> bool:
    """Met à jour le rôle d'un utilisateur. Retourne True si trouvé."""
    conn = get_db_connection()
    cursor = conn.execute(
        "UPDATE users SET role = ? WHERE id = ?", (role, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def update_user_password(user_id: int, password: str) -> bool:
    """Met à jour le mot de passe d'un utilisateur."""
    conn = get_db_connection()
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    cursor = conn.execute(
        "UPDATE users SET password = ? WHERE id = ?", (hashed, user_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_user(user_id: int) -> bool:
    """Supprime un utilisateur. Retourne True si trouvé."""
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie un mot de passe contre son hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
