# import jwt
# from jwt import PyJWKClient

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False, description="Mot de passe partagé temporaire (v0).")


async def require_access(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> None:
    password = request.app.state.settings.API_PASSWORD
    if password is None or not password.get_secret_value():
        raise HTTPException(503, "Accès API non configuré")
    if credentials is None or not compare_digest(
        credentials.credentials.encode(), password.get_secret_value().encode()
    ):
        raise HTTPException(401, "Identifiants invalides", headers={"WWW-Authenticate": "Bearer"})


## For Keycloak SSO

# oauth2_scheme = OAuth2PasswordBearer(
# tokenUrl=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/token"
# )
#
# jwks_client = PyJWKClient(
#     f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}/protocol/openid-connect/certs"
# )
#
# async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Token SSO invalide ou expiré",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         signing_key = jwks_client.get_signing_key_from_jwt(token)
#         payload = jwt.decode(
#             token,
#             signing_key.key,
#             algorithms=["RS256"],
#             audience=settings.KEYCLOAK_CLIENT_ID,
#             issuer=f"{settings.KEYCLOAK_URL}/realms/{settings.KEYCLOAK_REALM}",
#         )
#         return payload
#     except Exception:
#         raise credentials_exception from None
