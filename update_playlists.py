import sqlite3
import os

DATABASE_PATH = "code_converter.db"

def update_playlist_videos():
    if not os.path.exists(DATABASE_PATH):
        print(f"Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # YouTube Playlist Embed URLs
    updates = [
        ("Python", "https://www.youtube.com/embed/videoseries?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU"),
        ("Java", "https://www.youtube.com/embed/videoseries?list=PL_c9BZzLwBRKmimQuhLeZLvD8zukV2O12"),
        ("JavaScript", "https://www.youtube.com/embed/videoseries?list=PLillGF-RfqbZ7s3t6ZInY3NjEOOX7hsBv"),
        ("C++", "https://www.youtube.com/embed/videoseries?list=PLlrATfBNZ98dudnM48yfGUldqGD0S4FFb"),
        ("Go", "https://www.youtube.com/embed/videoseries?list=PLRAV69dS1uLGNHJj9k19H0NbMyyT-m-E7"),
        ("Rust", "https://www.youtube.com/embed/videoseries?list=PLai5B987bZ9CoVR-QEIN9foz4QCJ0H2Y8"),
    ]

    print("Updating video URLs to Playlists...")
    for language, url in updates:
        cursor.execute("""
            UPDATE video_tutorials 
            SET video_url = ? 
            WHERE language = ?
        """, (url, language))
        if cursor.rowcount > 0:
            print(f"Updated {language} -> Playlist")
        else:
            print(f"No record found for {language}")

    conn.commit()
    conn.close()
    print("Database playlist update complete.")

if __name__ == "__main__":
    update_playlist_videos()
