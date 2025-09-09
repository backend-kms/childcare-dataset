# Standard Libraries
import os

# Third-party Libraries
from dotenv import load_dotenv

load_dotenv()

DATA_SECRET_KEY = os.environ["DATA_SECRET_KEY"]
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")