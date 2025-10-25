from flask import Flask, request, jsonify, redirect, render_template
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# create table if not exists
def init_db():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS links (
                slug TEXT PRIMARY KEY,
                url TEXT NOT NULL
            );""")
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/shortener", methods=["POST"])
def shortener():
    data = request.get_json()
    url = data.get("url")
    slug = data.get("slug")
    if not url or not slug:
        return jsonify({"error": "missing url or slug"}), 400
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO links (slug, url) VALUES (%s, %s) ON CONFLICT (slug) DO UPDATE SET url = EXCLUDED.url", (slug, url))
    conn.close()
    short_link = request.host_url + slug
    return jsonify({"short_link": short_link})

@app.route("/<slug>")
def redirect_slug(slug):
    conn = get_db_connection()
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("SELECT url FROM links WHERE slug = %s", (slug,))
            row = cur.fetchone()
            if row:
                return redirect(row["url"])
    return "Not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
