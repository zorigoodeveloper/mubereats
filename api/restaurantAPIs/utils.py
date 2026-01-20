def is_order_belongs_to_restaurant(cursor, order_id, res_id):
    cursor.execute("""
        SELECT 1
        FROM tbl_order o
        JOIN tbl_orderfood of ON o."orderID" = of."orderID"
        JOIN tbl_food f ON f."foodID" = of."foodID"
        WHERE o."orderID" = %s AND f."resID" = %s
        LIMIT 1
    """, [order_id, res_id])
    return cursor.fetchone() is not None