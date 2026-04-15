import requests

url = "https://onecompiler.com/api/v1/run"
headers = {
    "X-API-Key": "oc_44hfavwkj_44hfavwm3_f778fb366d108c1cdfeba8efb018f94e8d0876898a48c9bd",
    "Content-Type": "application/json"
}

langs = [
    "python", "java", "nodejs", "cpp", "csharp", "c", "go", "rust", "swift",
    "kotlin", "ruby", "php", "dart", "scala", "r", "octave", "julia", "perl",
    "haskell", "lua", "objectivec", "vb", "fsharp", "elixir", "clojure", "groovy",
    "assembly", "bash", "powershell", "mysql"
]

for l in langs:
    payload = {
        "language": l,
        "stdin": "",
        "files": [{"name": "main", "content": "print(1)"}]
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 200:
        print(f"{l}: OK")
    else:
        print(f"{l}: FAIL {r.status_code} - {r.text[:50]}")
