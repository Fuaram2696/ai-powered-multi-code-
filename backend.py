from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import sqlite3
import hashlib
import secrets
import json
import os
import httpx
from dotenv import load_dotenv
import tempfile
import subprocess

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Code Converter API")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Database Configuration
DATABASE_PATH = "code_converter.db"

# Groq Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"  # You can change this to other Groq models

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ConversionRequest(BaseModel):
    source_code: str
    source_language: str
    target_language: str
    include_video: bool = False

class ConversionHistory(BaseModel):
    id: Optional[int] = None
    user_id: int
    source_code: str
    converted_code: str
    source_language: str
    target_language: str
    status: str
    created_at: Optional[str] = None

class CodeExecutionRequest(BaseModel):
    code: str
    language: str
    stdin: Optional[str] = ""

# Database Functions
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Conversion history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversion_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source_code TEXT NOT NULL,
            converted_code TEXT NOT NULL,
            source_language TEXT NOT NULL,
            target_language TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            execution_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # User preferences table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            default_source_lang TEXT DEFAULT 'Python',
            default_target_lang TEXT DEFAULT 'JavaScript',
            include_video_default BOOLEAN DEFAULT 1,
            theme TEXT DEFAULT 'dark',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    # Video tutorials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_tutorials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            video_url TEXT,
            thumbnail_url TEXT,
            duration INTEGER,
            views INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

# Utility Functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify authentication token"""
    token = credentials.credentials
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.user_id, u.email, u.full_name
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > ?
    """, (token, datetime.now()))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "user_id": result[0],
        "email": result[1],
        "full_name": result[2]
    }



# API Endpoints

@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    init_db()
    seed_video_tutorials()

@app.get("/")
async def root():
    return {"message": "AI Code Converter API", "status": "active"}

@app.post("/api/auth/register")
async def register(user: UserRegister):
    """Register new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        password_hash = hash_password(user.password)
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name)
            VALUES (?, ?, ?)
        """, (user.email, password_hash, user.full_name))
        
        user_id = cursor.lastrowid
        
        # Create default preferences
        cursor.execute("""
            INSERT INTO user_preferences (user_id)
            VALUES (?)
        """, (user_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user_id": user_id
        }
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    finally:
        conn.close()

@app.post("/api/auth/login")
async def login(user: UserLogin):
    """User login"""
    conn = get_db()
    cursor = conn.cursor()
    
    password_hash = hash_password(user.password)
    cursor.execute("""
        SELECT id, email, full_name
        FROM users
        WHERE email = ? AND password_hash = ?
    """, (user.email, password_hash))
    
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    user_id = result[0]
    
    # Create session token
    token = generate_token()
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute("""
        INSERT INTO sessions (user_id, token, expires_at)
        VALUES (?, ?, ?)
    """, (user_id, token, expires_at))
    
    # Update last login
    cursor.execute("""
        UPDATE users SET last_login = ? WHERE id = ?
    """, (datetime.now(), user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user_id,
            "email": result[1],
            "full_name": result[2]
        }
    }

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(verify_token)):
    """User logout"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM sessions WHERE user_id = ?
    """, (current_user["user_id"],))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Logged out successfully"}

@app.get("/api/auth/verify")
async def verify(current_user: dict = Depends(verify_token)):
    """Verify token and get user info"""
    return {
        "success": True,
        "user": current_user
    }

@app.post("/api/convert")
async def convert_code(
    request: ConversionRequest,
    current_user: dict = Depends(verify_token)
):
    """Convert code using Groq AI"""
    start_time = datetime.now()
    
    try:
        # Check if API key is configured
        if not GROQ_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Groq API key not configured. Please set GROQ_API_KEY in .env file"
            )
        
        # Simple language validation using keywords (no API call needed for basic check)
        code_lower = request.source_code.lower()
        language_keywords = {
            "java": ["public class", "private", "void", "static", "import java"],
            "python": ["def ", "import ", "class ", "self", "print("],
            "javascript": ["function", "const ", "let ", "var ", "console.log"],
            "c++": ["#include", "std::", "cout", "cin", "namespace"],
            "c#": ["using System", "namespace", "public class", "private"],
            "go": ["func ", "package ", "import ", "fmt."],
            "rust": ["fn ", "let mut", "impl ", "pub "],
            "php": ["<?php", "function", "$", "echo"],
            "ruby": ["def ", "end", "puts", "require"],
            "swift": ["func ", "var ", "let ", "import "],
        }
        
        # Check if selected source language keywords are present
        selected_lang_lower = request.source_language.lower()
        if selected_lang_lower in language_keywords:
            keywords = language_keywords[selected_lang_lower]
            has_keywords = any(keyword in code_lower for keyword in keywords)
            
            # If no keywords found, check if it matches another language
            if not has_keywords and len(request.source_code) > 50:
                for lang, kw_list in language_keywords.items():
                    if lang != selected_lang_lower and any(kw in code_lower for kw in kw_list):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"⚠️ Source language mismatch! The code appears to be {lang.title()}, not {request.source_language}. Please select the correct source language."
                        )
        
        # Create prompt for code conversion
        # Create prompt for code conversion with strict validation
        prompt = f"""You are an expert programmer. Convert the following source code from {request.source_language} to {request.target_language}.

        IMPORTANT: First, validate if the provided code is actually written in {request.source_language}.
        - If the code clearly matches {request.source_language}, proceed with the conversion.
        - If the code clearly does NOT match {request.source_language} (e.g., user selected Python but provided C++ code), return a JSON object with this exact structure:
          {{ "error": "Language Mismatch", "message": "You selected {request.source_language}, but the code appears to be [Detected Language]. Please select the correct source language." }}
        
        If the code is valid {request.source_language}:
        1. Preserve the logic and functionality.
        2. Follow {request.target_language} best practices. Note: JavaScript/TypeScript must be written for Node.js (browser APIs like prompt/window are polyfilled but best avoided).
        3. Add comments explaining complex parts. Note: JavaScript/TypeScript must be written for Node.js. For user input, ALWAYS use the globally polyfilled `prompt(message)` function. DO NOT import or require any modules for input (e.g., NEVER use `require('prompt')`, `require('prompt-sync')`, or `readline`).
        4. Return ONLY the code, no markdown backticks, no explanations outside the code.

        Source Code ({request.source_language}):
        ```
        {request.source_code}
        ```
        """

        # Calculate token limit based on input code size
        # Groq's llama-3.3-70b-versatile supports up to 32,768 tokens context
        estimated_output_tokens = int(len(request.source_code) * 1.5 * 0.4)  # 0.4 tokens per char
        max_tokens = min(max(1000, estimated_output_tokens + 200), 8000)  # Cap at 8000 for safety
        
        print(f"🔍 Using {max_tokens} max tokens for conversion")
        
        # Call Groq API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code != 200:
                error_detail = response.json().get("error", {}).get("message", "Unknown error")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Groq API error: {error_detail}"
                )
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Check for validation error in response
            if content.strip().startswith('{') and '"error": "Language Mismatch"' in content:
                import json
                try:
                    error_data = json.loads(content)
                    raise HTTPException(status_code=400, detail=error_data["message"])
                except json.JSONDecodeError:
                    pass # Fallback if not valid JSON

            converted_code = content.strip()
            # Automatically remove first and last line if they are markdown formatting (e.g. ```python ... ```)
            if converted_code.startswith("```") and converted_code.endswith("```"):
                lines = converted_code.split("\n")
                if len(lines) >= 2:
                    converted_code = "\n".join(lines[1:-1]).strip()
                else:
                    converted_code = converted_code.replace("```", "").strip()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversion_history 
            (user_id, source_code, converted_code, source_language, target_language, status, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user["user_id"],
            request.source_code,
            converted_code,
            request.source_language,
            request.target_language,
            "success",
            execution_time
        ))
        
        conversion_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "converted_code": converted_code,
            "conversion_id": conversion_id,
            "execution_time": execution_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error to database
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversion_history 
            (user_id, source_code, converted_code, source_language, target_language, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            current_user["user_id"],
            request.source_code,
            "",
            request.source_language,
            request.target_language,
            "error",
            str(e)
        ))
        
        conn.commit()
        conn.close()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversion failed: {str(e)}"
        )

@app.post("/api/run")
async def run_code(
    request: CodeExecutionRequest,
    current_user: dict = Depends(verify_token)
):
    """Execute code using JDoodle API"""
    try:
        req_lang = request.language.lower()
        
        # Local GCC Execution for C and C++
        if req_lang in ["c", "c++"]:
            ext = ".c" if req_lang == "c" else ".cpp"
            compiler = "gcc" if req_lang == "c" else "g++"
            
            with tempfile.TemporaryDirectory() as temp_dir:
                source_path = os.path.join(temp_dir, f"main{ext}")
                executable_path = os.path.join(temp_dir, "main.exe" if os.name == "nt" else "main")
                
                with open(source_path, "w", encoding="utf-8") as f:
                    f.write(request.code)
                    
                # Compile
                try:
                    compile_process = subprocess.run(
                        [compiler, source_path, "-o", executable_path],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                except FileNotFoundError:
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": f"Error: '{compiler}' compiler not found. Please install GCC.",
                        "output": f"Error: '{compiler}' compiler not found. Please install GCC.",
                        "code": 1
                    }
                    
                if compile_process.returncode != 0:
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": compile_process.stderr,
                        "output": f"Compilation Error:\n{compile_process.stderr}",
                        "code": compile_process.returncode
                    }
                    
                # Execute
                try:
                    run_process = subprocess.run(
                        [executable_path],
                        input=request.stdin or "",
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    return {
                        "success": True,
                        "stdout": run_process.stdout,
                        "stderr": run_process.stderr,
                        "output": run_process.stdout + ("\n" + run_process.stderr if run_process.stderr else ""),
                        "code": run_process.returncode
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "success": True,
                        "stdout": "",
                        "stderr": "Execution Timeout",
                        "output": "Execution Output timeout after 5 seconds",
                        "code": 124
                    }

        # JDoodle Execution for other languages
        raw_client_ids = os.getenv("JDOODLE_CLIENT_ID", "")
        raw_client_secrets = os.getenv("JDOODLE_CLIENT_SECRET", "")
        
        jdoodle_client_ids = [k.strip() for k in raw_client_ids.split(",") if k.strip()]
        jdoodle_client_secrets = [k.strip() for k in raw_client_secrets.split(",") if k.strip()]
        
        if not jdoodle_client_ids or not jdoodle_client_secrets:
            return {
                "success": True,
                "stdout": "",
                "stderr": "",
                "output": "⚠️ Missing JDoodle API Keys in .env file.",
                "code": 0
            }

        jdoodle_url = "https://api.jdoodle.com/v1/execute"
        
        jdoodle_language_map = {
            "python": ("python3", "4"),
            "java": ("java", "4"),
            "javascript": ("nodejs", "4"),
            "typescript": ("nodejs", "4"), 
            "c#": ("csharp", "4"),
            "go": ("go", "4"),
            "rust": ("rust", "4"),
            "swift": ("swift", "4"),
            "kotlin": ("kotlin", "3"),
            "ruby": ("ruby", "4"),
            "php": ("php", "4"),
            "dart": ("dart", "4"),
            "scala": ("scala", "4"),
            "r": ("r", "4"),
            "perl": ("perl", "4"),
            "haskell": ("haskell", "4"),
            "lua": ("lua", "4"),
            "shell": ("bash", "4"),
            "sql": ("sql", "4"),
            "objective-c": ("objc", "0"),
            "visual basic": ("vbn", "0"),
            "f#": ("fsharp", "0"),
            "elixir": ("elixir", "0"),
            "clojure": ("clojure", "0"),
            "groovy": ("groovy", "0"),
            "assembly": ("nasm", "0")
        }

        if req_lang not in jdoodle_language_map:
            raise HTTPException(
                status_code=400,
                detail=f"⚠️ Execution for '{request.language}' is not currently supported."
            )
            
        jdoodle_lang, version_index = jdoodle_language_map[req_lang]
        
        script_code = request.code
        
        # Polyfill for Node.js
        if req_lang in ["javascript", "typescript"]:
            polyfill = """// Node.js Polyfill
try {
    const fs = require('fs');
    let __stdin_buffer = "";
    try { __stdin_buffer = fs.readFileSync(0, 'utf-8'); } catch(e) {}
    
    // Split and aggressively remove any trailing empty lines that come from JDoodle wrappers
    let __stdin_lines = __stdin_buffer.split(/\\r?\\n/);
    while (__stdin_lines.length > 0 && __stdin_lines[__stdin_lines.length - 1] === "") {
        __stdin_lines.pop();
    }
    
    let __stdin_line_idx = 0;
    global.prompt = function(msg) {
        if (msg) process.stdout.write(String(msg) + " ");
        if (__stdin_line_idx >= __stdin_lines.length) {
            process.exit(0); // Pause exactly here and exit cleanly
        }
        return __stdin_lines[__stdin_line_idx++];
    };
    
    // Intercept requires for terminal prompt libraries
    const Module = require('module');
    const originalRequire = Module.prototype.require;
    Module.prototype.require = function(mod) {
        if (mod === 'prompt' || mod === 'prompt-sync') {
            const f = function(msg) { return global.prompt(msg || ""); };
            f.start = function() {};
            f.get = function(props, cb) { if (cb) cb(null, { result: global.prompt(props[0] || "") }); };
            return mod === 'prompt-sync' ? function() { return f; } : f;
        }
        if (mod === 'readline-sync') {
            return { question: function(msg) { return global.prompt(msg || ""); } };
        }
        return originalRequire.apply(this, arguments);
    };

    global.alert = function(msg) { if (msg !== undefined) console.log(msg); };
    global.window = global;
} catch(e) {}
"""
            script_code = polyfill + script_code
            
        if req_lang == "python":
            python_polyfill = """import builtins
import sys
_orig_input = builtins.input
def _mock_input(prompt_text=""):
    try:
        if prompt_text:
            print(prompt_text, end='', flush=True)
        return _orig_input()
    except EOFError:
        sys.exit(0)
builtins.input = _mock_input
"""
            script_code = python_polyfill + script_code

        last_error = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for client_id, client_secret in zip(jdoodle_client_ids, jdoodle_client_secrets):
                payload = {
                    "clientId": client_id,
                    "clientSecret": client_secret,
                    "script": script_code,
                    "language": jdoodle_lang,
                    "versionIndex": version_index,
                    "stdin": request.stdin or ""
                }
                
                response = await client.post(jdoodle_url, json=payload)
                
                # Status 401/429 indicate key exhaustion or invalid key
                if response.status_code == 401 or response.status_code == 429:
                    last_error = f"API Key error: {response.status_code}"
                    continue # Try next key
                    
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to execute code via JDoodle service."
                    )
                    
                data = response.json()
                
                # Wait: JDoodle HTTP 200 might contain error property for limit issues
                if data.get("error") == "Daily limit reached" or data.get("error") == "Unauthorized" or data.get("statusCode") == 401:
                    last_error = f"JDoodle Error: {data.get('error', 'Unauthorized')}"
                    continue # Try next key

                output = data.get("output") or ""
                error = data.get("error") or ""
                
                return {
                    "success": True,
                    "stdout": output if not error else "",
                    "stderr": error if error else "",
                    "output": str(output) + ("\n" + str(error) if error else ""),
                    "code": 0 if not error else 1
                }
                
        # If we break out of the loop, all keys failed
        return {
            "success": True,
            "stdout": "",
            "stderr": str(last_error) if last_error else "All JDoodle API keys failed or exhausted limit.",
            "output": f"⚠️ Execution Failed: {last_error or 'All JDoodle API keys exhausted their daily limits.'}",
            "code": 1
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Execution failed: {str(e)}"
        )

@app.get("/api/history")
async def get_history(
    limit: int = 10,
    current_user: dict = Depends(verify_token)
):
    """Get user's conversion history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, source_language, target_language, status, created_at, execution_time
        FROM conversion_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (current_user["user_id"], limit))
    
    history = []
    for row in cursor.fetchall():
        history.append({
            "id": row[0],
            "from": row[1],
            "to": row[2],
            "status": row[3].capitalize(),
            "created_at": row[4],
            "execution_time": row[5]
        })
    
    conn.close()
    return {"success": True, "history": history}

@app.delete("/api/history")
async def clear_history(current_user: dict = Depends(verify_token)):
    """Clear user's conversion history"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM conversion_history
        WHERE user_id = ?
    """, (current_user["user_id"],))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "History cleared successfully"}

@app.get("/api/history/{conversion_id}")
async def get_conversion_detail(
    conversion_id: int,
    current_user: dict = Depends(verify_token)
):
    """Get specific conversion details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT source_code, converted_code, source_language, target_language, status, created_at
        FROM conversion_history
        WHERE id = ? AND user_id = ?
    """, (conversion_id, current_user["user_id"]))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversion not found"
        )
    
    return {
        "success": True,
        "conversion": {
            "source_code": result[0],
            "converted_code": result[1],
            "source_language": result[2],
            "target_language": result[3],
            "status": result[4],
            "created_at": result[5]
        }
    }

@app.get("/api/videos")
async def get_videos(language: Optional[str] = None):
    """Get video tutorials"""
    conn = get_db()
    cursor = conn.cursor()
    
    if language:
        cursor.execute("""
            SELECT id, language, title, description, video_url, thumbnail_url, duration, views
            FROM video_tutorials
            WHERE language = ?
            ORDER BY views DESC
        """, (language,))
    else:
        cursor.execute("""
            SELECT id, language, title, description, video_url, thumbnail_url, duration, views
            FROM video_tutorials
            ORDER BY views DESC
        """)
    
    videos = []
    for row in cursor.fetchall():
        videos.append({
            "id": row[0],
            "language": row[1],
            "title": row[2],
            "description": row[3],
            "video_url": row[4],
            "thumbnail_url": row[5],
            "duration": row[6],
            "views": row[7]
        })
    
    conn.close()
    return {"success": True, "videos": videos}

class VideoUpdate(BaseModel):
    video_url: str

@app.put("/api/videos/{video_id}")
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    current_user: dict = Depends(verify_token)
):
    """Update video URL"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE video_tutorials
        SET video_url = ?
        WHERE id = ?
    """, (video_update.video_url, video_id))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video tutorial not found"
        )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Video URL updated successfully"}

@app.get("/api/stats")
async def get_stats(current_user: dict = Depends(verify_token)):
    """Get user statistics"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total conversions
    cursor.execute("""
        SELECT COUNT(*) FROM conversion_history WHERE user_id = ?
    """, (current_user["user_id"],))
    total_conversions = cursor.fetchone()[0]
    
    # Successful conversions
    cursor.execute("""
        SELECT COUNT(*) FROM conversion_history WHERE user_id = ? AND status = 'success'
    """, (current_user["user_id"],))
    successful_conversions = cursor.fetchone()[0]
    
    # Most used source language
    cursor.execute("""
        SELECT source_language, COUNT(*) as count
        FROM conversion_history
        WHERE user_id = ?
        GROUP BY source_language
        ORDER BY count DESC
        LIMIT 1
    """, (current_user["user_id"],))
    most_used_source = cursor.fetchone()
    
    # Most used target language
    cursor.execute("""
        SELECT target_language, COUNT(*) as count
        FROM conversion_history
        WHERE user_id = ?
        GROUP BY target_language
        ORDER BY count DESC
        LIMIT 1
    """, (current_user["user_id"],))
    most_used_target = cursor.fetchone()
    
    conn.close()
    
    return {
        "success": True,
        "stats": {
            "total_conversions": total_conversions,
            "successful_conversions": successful_conversions,
            "success_rate": (successful_conversions / total_conversions * 100) if total_conversions > 0 else 0,
            "most_used_source": most_used_source[0] if most_used_source else None,
            "most_used_target": most_used_target[0] if most_used_target else None
        }
    }

@app.get("/api/preferences")
async def get_preferences(current_user: dict = Depends(verify_token)):
    """Get user preferences"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT default_source_lang, default_target_lang, include_video_default, theme
        FROM user_preferences
        WHERE user_id = ?
    """, (current_user["user_id"],))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return {
            "success": True,
            "preferences": {
                "default_source_lang": "Python",
                "default_target_lang": "JavaScript",
                "include_video_default": True,
                "theme": "dark"
            }
        }
    
    return {
        "success": True,
        "preferences": {
            "default_source_lang": result[0],
            "default_target_lang": result[1],
            "include_video_default": bool(result[2]),
            "theme": result[3]
        }
    }

@app.put("/api/preferences")
async def update_preferences(
    preferences: dict,
    current_user: dict = Depends(verify_token)
):
    """Update user preferences"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE user_preferences
        SET default_source_lang = ?,
            default_target_lang = ?,
            include_video_default = ?,
            theme = ?
        WHERE user_id = ?
    """, (
        preferences.get("default_source_lang", "Python"),
        preferences.get("default_target_lang", "JavaScript"),
        preferences.get("include_video_default", True),
        preferences.get("theme", "dark"),
        current_user["user_id"]
    ))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Preferences updated"}

def seed_video_tutorials():
    """Seed initial video tutorials"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if tutorials already exist
    cursor.execute("SELECT COUNT(*) FROM video_tutorials")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    tutorials = [
        ("Python", "Complete Python Bootcamp Tutorial", "Learn Python from basics to advanced", "https://www.youtube.com/embed/videoseries?list=PL0--sAWljl5LEzNyN5Z4zlorThiIUYEV_", None, 3600, 15000),
        ("Java", "Modern Java Development", "Master Java programming", "https://www.youtube.com/embed/videoseries?list=PLfqMhTWNBTe3LtFWcvwpqTkUSlB32kJop", None, 4200, 12000),
        ("JavaScript", "JavaScript UI/UX Explained", "Build interactive web apps", "https://www.youtube.com/embed/videoseries?list=PLGjplNEQ1it_oTvuLRNqXfz_v_0pq6unW", None, 2800, 18000),
        ("C++", "Deep Dive Development with C++", "Advanced C++ concepts", "https://www.youtube.com/embed/videoseries?list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt", None, 5400, 9000),
        ("Rust", "Rust Programming", "Systems programming with Rust", "https://www.youtube.com/embed/videoseries?list=PLinedj3B30sA_M0oxCRgFzPzEMX3CSfT5", None, 4800, 7000),
        ("C", "C Programming", "Start with your C journey", "https://www.youtube.com/embed/irqbmMNs2Bo", None, 4800, 7000),
        ("TypeScript", "TypeScript Programming", "TypeScript is a programming Language", "https://www.youtube.com/embed/videoseries?list=PLu71SKxNbfoBkkr8lblqtsJvxrw3j1tWC", None, 4800, 7000),
        ("Go", "Go (Golang) Programming", "Learn Go for efficient backend dev", "https://www.youtube.com/embed/YS4e4q9oBaU", None, 18000, 5000),
        ("Swift", "Swift for Beginners", "iOS App Development with Swift", "https://www.youtube.com/embed/videoseries?list=PLMRqhzcHGw1TYJJb95Yc61d5T_4M66-Hk", None, 3600, 8000),
        ("Kotlin", "Kotlin for Android", "Modern Android Development", "https://www.youtube.com/embed/F9UC9DY-vIU", None, 28000, 9000),
        ("Ruby", "Ruby Programming", "Elegant and productive language", "https://www.youtube.com/embed/t_ispmWmdjY", None, 14400, 4000),
        ("PHP", "PHP for Beginners", "Server-side scripting mastered", "https://www.youtube.com/embed/OK_JCtrrv-c", None, 23000, 10000),
        ("Dart", "Dart Programming", "Client-optimized language for fast apps", "https://www.youtube.com/embed/videoseries?list=PLCC34OHNcOsqf40M-q4d8_7EfdWopF9E_", None, 5000, 6000),
        ("Scala", "Scala Programming", "Scalable language for JVM", "https://www.youtube.com/embed/videoseries?list=PL0-84-yl1fUmaW9tJ_uMjk_Y_Y7_aJ8b-", None, 7200, 3000),
        ("R", "R Programming", "Statistical computing and graphics", "https://www.youtube.com/embed/videoseries?list=PLc2za7Fk30wjuH525s0Zp566u4f7x5c-r", None, 6000, 5000),
        ("MATLAB", "MATLAB Essentials", "Programming for engineers and scientists", "https://www.youtube.com/embed/T_ekAD7U-wU", None, 4000, 4000),
        ("Julia", "Julia Programming", "High-performance dynamic language", "https://www.youtube.com/embed/GEyIq5a6s0I", None, 14400, 2000),
        ("Perl", "Perl Programming", "Scripting and text processing", "https://www.youtube.com/embed/WEghIQFhD2U", None, 3600, 2000),
        ("Haskell", "Haskell Programming", "Purely functional programming", "https://www.youtube.com/embed/videoseries?list=PLu0W_9lII9agp6kLA6fVqX_A30y1h_G9F", None, 5400, 3000),
        ("Lua", "Lua Scripting", "Lightweight scripting language", "https://www.youtube.com/embed/1srFmjt1Ib0", None, 3000, 4000),
        ("Objective-C", "Objective-C Guide", "Primary language for Apple dev", "https://www.youtube.com/embed/videoseries?list=PLMRqhzcHGw1YfS92iytSJCjt01FxPF9rr", None, 3600, 1500),
        ("Visual Basic", "Visual Basic .NET", "Easy to learn .NET language", "https://www.youtube.com/embed/3s-bgPg7IWc", None, 5000, 3000),
        ("F#", "F# Functional", "Functional programming on .NET", "https://www.youtube.com/embed/videoseries?list=PLdo4fOcmZ0oUFghYOp89baYFBTGxUkC7Z", None, 4500, 2000),
        ("Elixir", "Elixir Programming", "Dynamic, functional language", "https://www.youtube.com/embed/4Y7D1B7z878", None, 3600, 2500),
        ("Clojure", "Clojure Essentials", "Lisp on the JVM", "https://www.youtube.com/embed/rC_I2n_K0hQ", None, 4000, 2000),
        ("Groovy", "Groovy Fundamentals", "Agile dynamic language for Java", "https://www.youtube.com/embed/GfTzUuM4SCA", None, 3000, 2000),
        ("Assembly", "Assembly Language", "Low-level programming", "https://www.youtube.com/embed/faZ_N8g0B00", None, 7200, 5000),
        ("Shell", "Shell Scripting", "Command line automation", "https://www.youtube.com/embed/e7BufAVwDiM", None, 4000, 8000),
        ("PowerShell", "PowerShell Automation", "Task automation and config", "https://www.youtube.com/embed/qR4M_fGqNws", None, 5000, 9000),
        ("SQL", "SQL Database", "Managing relational databases", "https://www.youtube.com/embed/HXV3zeQKqGY", None, 14400, 20000),
    ]
    
    cursor.executemany("""
        INSERT INTO video_tutorials (language, title, description, video_url, thumbnail_url, duration, views)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, tutorials)
    
    conn.commit()
    conn.close()

# Serve frontend static files in production
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    @app.exception_handler(404)
    async def custom_404_handler(request, __):
        if request.url.path.startswith("/api"):
            return None
        return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
