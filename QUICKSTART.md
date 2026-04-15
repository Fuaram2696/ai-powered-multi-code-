# Quick Start Guide

## Step 1: Get Groq API Key
1. Visit [https://console.groq.com/](https://console.groq.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key and copy it

## Step 2: Configure Environment
Create a `.env` file in the project root:
```bash
GROQ_API_KEY=your_api_key_here
```

## Step 3: Start the Application

### Windows:
```bash
start.bat
```

### Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

### Manual Start:

**Backend:**
```bash
pip install -r requirements.txt
python backend.py
```

**Frontend (in a new terminal):**
```bash
cd frontend
npm install
npm run dev
```

## Step 4: Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## First Time Setup
1. Open http://localhost:3000 in your browser
2. Click "Sign Up" to create an account
3. Fill in your email and password
4. Log in with your credentials
5. Start converting code!

## Troubleshooting

## Common Issues

- **Backend won't start**: Check Python version (3.8+)
- **Frontend won't start**: Check Node.js version (16+)
- **Conversion fails**: 
  - Verify your Groq API key is valid
  - Check your internet connection
  - Make sure you have API credits on Groq

## Need Help?
Check the full README.md for detailed documentation.
