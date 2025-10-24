import os
from dotenv import load_dotenv

# Load environment variables from .env file
try:
    load_dotenv()
except:
    pass

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o-mini'
MAX_TURN = 7
MAX_TURN_10 = 10
TERMINATION_WORD = 'stop'