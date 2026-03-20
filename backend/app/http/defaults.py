from fastapi.responses import JSONResponse


class InternalServerErrorResponse(JSONResponse):
    """JSON 500 response with a ``detail`` string."""

    def __init__(self, detail: str = "Internal server error"):
        """Builds a 500 response body.

        Args:
            detail: Error message for clients.

        """
        super().__init__(
            status_code=500,
            content={"detail": detail},
        )


class NotFoundErrorResponse(JSONResponse):
    """JSON 404 response with a ``detail`` string."""

    def __init__(self, detail: str = "Not found"):
        """Builds a 404 response body.

        Args:
            detail: Error message for clients.

        """
        super().__init__(
            status_code=404,
            content={"detail": detail},
        )
