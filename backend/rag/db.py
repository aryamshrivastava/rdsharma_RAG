import sqlite3
from .config import SQLITE_PATH

def connect():
    con = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)

    con.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      source_pdf TEXT,
      page_start INTEGER,
      page_end INTEGER,
      chunk_type TEXT,
      title TEXT,
      text TEXT
    );
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_chunks_title ON chunks(title);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_chunks_pages ON chunks(page_start, page_end);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(chunk_type);")
    con.commit()
    return con

def insert_chunk(con, source_pdf, page_start, page_end, chunk_type, title, text):
    con.execute(
        """
        INSERT INTO chunks (source_pdf, page_start, page_end, chunk_type, title, text)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source_pdf, page_start, page_end, chunk_type, title, text)
    )

def fetch_chunk(con, chunk_id: int):
    cur = con.execute(
        """
        SELECT id, source_pdf, page_start, page_end, chunk_type, title, text
        FROM chunks WHERE id = ?
        """,
        (chunk_id,)
    )
    row = cur.fetchone()
    if not row:
        return None

    return {
        "id": row[0],
        "source_pdf": row[1],
        "page_start": row[2],
        "page_end": row[3],
        "chunk_type": row[4],
        "title": row[5],
        "text": row[6],
    }
