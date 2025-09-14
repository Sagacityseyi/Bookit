import  logging


logging.basicConfig(
    level =logging.INFO,
    format= "%(filename)s - %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
)

def get_logger(filename: str) -> logging.Logger:
    return logging.getLogger(filename)