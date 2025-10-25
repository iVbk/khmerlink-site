from flask import Flask, request, jsonify, redirect, render_template
import psycopg2
import psycopg2.extras
import os
import json
from urllib.parse import quote_plus

app = Flask(__name__)


def get_db_conn():
    """Create a new database connection using the DATABASE_URL env var"""
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    return conn

# Initialize the database table if it doesn't exist
def init_db():
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS links (
                slug TEXT PRIMARY KEY,
                target TEXT NOT NULL
            );
            """
        )
        conn.commit()


init_db()


@app.route("/api/shortener", methods=["POST"])
def api_shortener():
    data = request.get_json()
    url = data.get("url")
    slug = data.get("slug")
    if not url or not slug:
        return jsonify({"error": "url and slug required"}), 400
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO links (slug, target) VALUES (%s, %s) ON CONFLICT (slug) DO UPDATE SET target = EXCLUDED.target;",
            (slug, url),
        )
        conn.commit()
    return jsonify({"slug": slug})


@app.route("/api/address", methods=["POST"])
def api_address():
    data = request.get_json()
    address = data.get("address")
    slug = data.get("slug")
    if not address or not slug:
        return jsonify({"error": "address and slug required"}), 400
    # Encode address for Google Maps search
    encoded = quote_plus(address)
    google_url = f"https://www.google.com/maps/search/?api=1&query={encoded}"
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO links (slug, target) VALUES (%s, %s) ON CONFLICT (slug) DO UPDATE SET target = EXCLUDED.target;",
            (slug, google_url),
        )
        conn.commit()
    return jsonify({"slug": slug})


@app.route("/api/profile", methods=["POST"])
def api_profile():
    data = request.get_json()
    slug = data.get("slug")
    profile = data.get("profile", {})
    if not slug:
        return jsonify({"error": "slug required"}), 400
    # Store the profile as JSON string
    profile_json = json.dumps(profile, ensure_ascii=False)
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO links (slug, target) VALUES (%s, %s) ON CONFLICT (slug) DO UPDATE SET target = EXCLUDED.target;",
            (slug, profile_json),
        )
        conn.commit()
    return jsonify({"slug": slug})


@app.route("/<slug>")
def redirect_slug(slug):
    with get_db_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT target FROM links WHERE slug = %s;", (slug,))
        row = cur.fetchone()
    if not row:
        return "Not found", 404
    target = row[0]
    # Try to load JSON to see if it's a profile; otherwise treat as URL
    try:
        data = json.loads(target)
        # Return profile as JSON or simple page; here we just return JSON
        return jsonify(data)
    except json.JSONDecodeError:
        return redirect(target)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
