import uvicorn
from loguru import logger
from app.config import config


def main():
    logger.info("start server, docs: http://127.0.0.1:" +
                str(config.listen_port) + "/docs")
    uvicorn.run(
        app="app.asgi:app",
        host=config.listen_host,
        port=config.listen_port,
        reload=config.reload_debug,
        log_level="warning")


if __name__ == "__main__":
    main()
