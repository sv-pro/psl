import uvicorn
from dotenv import load_dotenv
from psl.api import app

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("psl.api:app", host="0.0.0.0", port=8000, reload=True)
