from flask import Blueprint, request, jsonify
from datetime import datetime
from db import get_db   # 🔴 чи өөрийн db connection helper-тэй бол тэрийг ашигла

confirm_order_bp = Blueprint("confirm_order", __name__, url_prefix="/api/orders")


@confirm_order_bp.route("/confirm", methods=["POST"])
def confirm_order():
    data = request.get_json()

    if not data or "order_id" not in data:
        return jsonify({
            "success": False,
            "message": "order_id is required"
        }), 400

    order_id = data["order_id"]
    db = get_db()
    cursor = db.cursor()

    # 1️⃣ Order шалгах
    cursor.execute(
        "SELECT id, status FROM orders WHERE id = %s",
        (order_id,)
    )
    order = cursor.fetchone()

    if not order:
        return jsonify({
            "success": False,
            "message": "Order not found"
        }), 404

    if order[1] == "CONFIRMED":
        return jsonify({
            "success": False,
            "message": "Order already confirmed"
        }), 400

    # 2️⃣ Order баталгаажуулах
    cursor.execute(
        """
        UPDATE orders
        SET status = %s,
            confirmed_at = %s
        WHERE id = %s
        """,
        ("CONFIRMED", datetime.now(), order_id)
    )

    db.commit()

    return jsonify({
        "success": True,
        "message": "Order confirmed successfully",
        "order_id": order_id
    }), 200
