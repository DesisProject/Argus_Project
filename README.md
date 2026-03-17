
# App design

This is a code bundle for App design. The original project is available at https://www.figma.com/design/LvBrVgKLx6b82jpYRNVmrT/App-design.

# Running the project

## Backend (Python)
cd startup_financial_engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --port 8000

## Frontend (TypeScript/Vite)
npm install
npm run dev