from flask import Flask, jsonify
import mysql.connector
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# === CONNECT TO YOUR MYSQL DATABASE ===
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Lisa650101",
        database="UberAPP",
    )

@app.route("/recommendations/<int:user_id>", methods=["GET"])
def recommend_restaurants(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Step 1: Get user's past restaurant orders
    cursor.execute("""
        SELECT r.id, r.name, r.tags
        FROM orders o
        JOIN restaurants r ON o.restaurant_id = r.id
        WHERE o.user_id = %s
    """, (user_id,))
    user_orders = cursor.fetchall()

    if not user_orders:
        return jsonify({"error": "No orders found for this user"}), 404

    user_tags = " ".join([r["tags"] for r in user_orders])
    ordered_ids = [r["id"] for r in user_orders]

    # Step 2: Get all other restaurants
    format_strings = ','.join(['%s'] * len(ordered_ids))
    cursor.execute(f"""
        SELECT id, name, tags FROM restaurants
        WHERE id NOT IN ({format_strings})
    """, tuple(ordered_ids))
    other_restaurants = cursor.fetchall()

    conn.close()

    if not other_restaurants:
        return jsonify([])

    # Step 3: Calculate similarity
    all_tags = [user_tags] + [r["tags"] for r in other_restaurants]
    all_names = ["User"] + [r["name"] for r in other_restaurants]
    all_ids = [None] + [r["id"] for r in other_restaurants]

    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(all_tags)
    similarities = cosine_similarity(X[0:1], X[1:]).flatten()

    results = list(zip(all_ids[1:], all_names[1:], similarities))
    results.sort(key=lambda x: x[2], reverse=True)

    recommendations = [{"id": r[0], "name": r[1], "score": round(r[2], 2)} for r in results]

    return jsonify(recommendations)

if __name__ == "__main__":
    app.run(debug=True)
