import os

from api.main import app


__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
