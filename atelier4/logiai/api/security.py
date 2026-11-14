"""Authentification par clé d'API : qui êtes-vous ? et avez-vous le droit ?"""
import secrets

from fastapi import Depends, Header, HTTPException

from logiai import config


def _egal(a: str | None, b: str | None) -> bool:
    """Comparaison en temps constant. Une clé non configurée n'est jamais valide."""
    if not a or not b:
        return False
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def verify_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """Authentification : renvoie le rôle ('user' ou 'admin') ou lève une 401.

    À VOUS :
    1. si l'en-tête X-API-Key est absent : HTTPException 401 (message clair) ;
    2. si la clé égale config.ADMIN_KEY : renvoyer "admin" ;
    3. si la clé égale config.API_KEY : renvoyer "user" ;
    4. sinon : HTTPException 401 "Clé API invalide".
    Utilisez _egal(...) pour comparer, jamais ==.
    Ajoutez headers={"WWW-Authenticate": "ApiKey"} aux 401.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Clé API absente : en-tête X-API-Key requis.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    # l'admin d'abord : les deux clés sont distinctes, mais l'ordre rend le rôle explicite
    if _egal(x_api_key, config.ADMIN_KEY):
        return "admin"
    if _egal(x_api_key, config.API_KEY):
        return "user"
    raise HTTPException(
        status_code=401,
        detail="Clé API invalide.",
        headers={"WWW-Authenticate": "ApiKey"},
    )


def require_admin(role: str = Depends(verify_api_key)) -> str:
    """Autorisation : réservé aux administrateurs.

    À VOUS : si role n'est pas "admin", lever HTTPException 403 ; sinon renvoyer role.
    """
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Accès réservé à l'administrateur.",
        )
    return role
