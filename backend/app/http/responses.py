from starlette.responses import JSONResponse

from app.core.settings import settings


class TokenPairJSONResponse(JSONResponse):
    def __init__(self, access_token: str, refresh_token: str, content: dict):
        super().__init__(content=content)

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.content = content

        self.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=settings.app_settings.APP_SECURE_COOKIES,
            max_age=settings.auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        self.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="lax",
            secure=settings.app_settings.APP_SECURE_COOKIES,
            max_age=settings.auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )