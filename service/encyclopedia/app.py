from flask import Flask, jsonify, request
from db import get_conn

app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/health/db")
def health_db():
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return jsonify({"db": "ok"}), 200
    except Exception as e:
        return jsonify({"db": "error", "detail": str(e)}), 503

@app.get("/info/<name>")
def info(name):
    q = name.strip()
    sql = """
      SELECT *
      FROM snakes
      WHERE name_en = %s OR name_th = %s OR short_name = %s OR scientific_name = %s
      LIMIT 1
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (q, q, q, q))
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "NOT_FOUND", "message": f"Snake '{name}' not found"}), 404
    return jsonify(row), 200

@app.get("/search")
def search():
    q = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)
    if not q:
        return jsonify({"items": [], "total": 0, "query": ""}), 200

    like = f"%{q}%"
    sql = """
      SELECT id, name_en, name_th, short_name, scientific_name, `group`, venom_type, image_path
      FROM snakes
      WHERE name_en LIKE %s OR name_th LIKE %s OR short_name LIKE %s OR scientific_name LIKE %s
      LIMIT %s
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (like, like, like, like, limit))
            rows = cur.fetchall()
    finally:
        conn.close()

    return jsonify({"items": rows, "total": len(rows), "query": q}), 200

@app.get("/suggest")
def suggest():
    q = request.args.get("q", "").strip()
    limit = min(int(request.args.get("limit", 5)), 10)
    
    if not q or len(q) < 1:
        return jsonify({"suggestions": []}), 200
    
    prefix = f"{q}%"
    sql = """
      SELECT DISTINCT name_th, scientific_name
      FROM snakes
      WHERE name_th LIKE %s OR scientific_name LIKE %s
      LIMIT %s
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (prefix, prefix, limit))
            rows = cur.fetchall()
    finally:
        conn.close()

    suggestions = [row.get("name_th") or row.get("scientific_name") for row in rows if row.get("name_th") or row.get("scientific_name")]
    return jsonify({"suggestions": suggestions, "query": q}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)