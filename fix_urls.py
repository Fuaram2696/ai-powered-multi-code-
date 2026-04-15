import sqlite3
import os
import re

DATABASE_PATH = "code_converter.db"

def extract_playlist_id(url):
    # Regex for Playlist ID
    match = re.search(r'[?&]list=([^#\&\?]+)', url)
    if match:
        return match.group(1)
    return None

def extract_video_id(url):
    # Regex for Video ID
    match = re.search(r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})', url)
    if match:
        return match.group(1)
    return None

def convert_to_embed_url(url):
    playlist_id = extract_playlist_id(url)
    video_id = extract_video_id(url)

    if playlist_id:
        return f"https://www.youtube.com/embed/videoseries?list={playlist_id}"
    elif video_id:
        return f"https://www.youtube.com/embed/{video_id}"
    else:
        return url

def update_db_with_fixes():
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # User provided URLs from backend.py
    user_updates = [
        ("Python", "https://www.youtube.com/watch?v=t2_Q2BRzeEE&list=PL0--sAWljl5LEzNyN5Z4zlorThiIUYEV_"),
        ("Java", "https://www.youtube.com/watch?v=yRpLlJmRo2w&list=PLfqMhTWNBTe3LtFWcvwpqTkUSlB32kJop"),
        ("JavaScript", "https://www.youtube.com/playlist?list=PLGjplNEQ1it_oTvuLRNqXfz_v_0pq6unW"),
        ("C++", "https://www.youtube.com/watch?v=VTLCoHnyACE&list=PLfqMhTWNBTe137I_EPQd34TsgV6IO55pt"),
        ("Rust", "https://www.youtube.com/watch?v=unRhxbFULII&list=PLinedj3B30sA_M0oxCRgFzPzEMX3CSfT5"),
    ]

    print("Fixing and Updating Video URLs...")
    
    for language, raw_url in user_updates:
        embed_url = convert_to_embed_url(raw_url)
        print(f"[{language}] Raw: {raw_url}")
        print(f"[{language}] Embed: {embed_url}")
        
        cursor.execute("""
            UPDATE video_tutorials 
            SET video_url = ? 
            WHERE language = ?
        """, (embed_url, language))
        
        if cursor.rowcount > 0:
            print(f"  -> Database Updated")
        else:
            print(f"  -> No record found")

    conn.commit()
    conn.close()
    print("Update Complete.")

if __name__ == "__main__":
    update_db_with_fixes()
