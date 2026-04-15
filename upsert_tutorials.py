import sqlite3
import os

DATABASE_PATH = "code_converter.db"

def upsert_videos():
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Verified list with correct IDs
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

    print("Upserting video tutorials with verified IDs...")
    for video in tutorials:
        lang, title, desc, url, thumb, dur, views = video
        
        # Check if exists
        cursor.execute("SELECT id FROM video_tutorials WHERE language = ?", (lang,))
        row = cursor.fetchone()
        
        if row:
            # Update with new verified URL
            cursor.execute("""
                UPDATE video_tutorials 
                SET title = ?, description = ?, video_url = ?
                WHERE language = ?
            """, (title, desc, url, lang))
            print(f"Updated {lang}")
        else:
            # Insert
            cursor.execute("""
                INSERT INTO video_tutorials (language, title, description, video_url, thumbnail_url, duration, views)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (lang, title, desc, url, thumb, dur, views))
            print(f"Inserted {lang}")
            
    conn.commit()
    conn.close()
    print("Database sync complete.")

if __name__ == "__main__":
    upsert_videos()
