import os
import requests
from dotenv import load_dotenv

load_dotenv()
client_id = os.getenv("JDOODLE_CLIENT_ID")
client_secret = os.getenv("JDOODLE_CLIENT_SECRET")

# JDoodle language names to test
languages = [
    "python3", "java", "nodejs", "cpp17", "csharp", "c", "go", "rust", "swift", 
    "kotlin", "ruby", "php", "dart", "scala", "r", "perl", "haskell", "lua",
    "bash", "sql", "objc", "vbn", "fsharp", "elixir", "clojure", "groovy",
    "nasm", "powershell", "octave", "julia"
]

results = []
for lang in languages:
    payload = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "script": "print(1)",
        "language": lang,
        "versionIndex": "0" 
    }
    r = requests.post("https://api.jdoodle.com/v1/execute", json=payload)
    if r.status_code == 200:
        results.append(f"{lang}: OK")
    else:
        results.append(f"{lang}: FAIL - {r.text}")

print("\n".join(results))
