import uvicorn

from ruralsmartmark.config import settings


def main() -> None:
    uvicorn.run(
        "ruralsmartmark.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
