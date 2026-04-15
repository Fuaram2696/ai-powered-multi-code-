import sqlite3
import os

DATABASE_PATH = "code_converter.db"

def update_videos():
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Real YouTube Embed URLs
    updates = [
        ("Python", "https://www.youtube.com/embed/_uQrJ0TkZlc"),      # Python for Beginners
        ("Java", "https://www.youtube.com/embed/eIrMbAQSU34"),        # Java Tutorial
        ("JavaScript", "https://www.youtube.com/embed/W6NZfCO5SIk"),  # JavaScript Tutorial
        ("C++", "https://www.youtube.com/embed/vLnPwxZdW4Y"),         # C++ Tutorial
        ("Go", "https://www.youtube.com/embed/un6ZyFkqFKo"),          # Go Tutorial
        ("Rust", "https://www.youtube.com/embed/BpPEoZW5IiY"),        # Rust Tutorial
    ]

    print("Updating video URLs...")
    for language, url in updates:
        cursor.execute("""
            UPDATE video_tutorials 
            SET video_url = ? 
            WHERE language = ?
        """, (url, language))
        if cursor.rowcount > 0:
            print(f"Updated {language} -> {url}")
        else:
            print(f"No record found for {language}")

    conn.commit()
    conn.close()
    print("Database update complete.")

if __name__ == "__main__":
    update_videos()
