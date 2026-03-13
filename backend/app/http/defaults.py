from fastapi.responses import JSONResponse


class InternalServerErrorResponse(JSONResponse):
    def __init__(self, detail: str = "Internal server error"):
        super().__init__(
            status_code=500,
            content={"detail": detail},
        )


class NotFoundErrorResponse(JSONResponse):
    def __init__(self, detail: str = "Not found"):
        super().__init__(
            status_code=404,
            content={"detail": detail},
        )