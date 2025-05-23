from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

print("TOKEN =", os.getenv("TELEGRAM_BOT_TOKEN"))