import os
import sqlite3
import sys
from pathlib import Path

# 新增：将项目根目录添加到系统路径（关键修复）
BASE_DIR = Path(__file__).parent.parent  # 项目根目录（server_optimized）
sys.path.append(str(BASE_DIR))

# 现在可以直接导入根目录的 cache 模块
from seat_cache import update_seat_cache  # <-- 修正为绝对导入

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # database/ 目录
DB_PATH = os.path.join(BASE_DIR, "concert.db")  # 指向 database/app.db


def connect_db():
    return sqlite3.connect(DB_PATH)


def execute_query(query, params=()):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id


#execute select query and return the results
def fetch_query(query, params=()):
    conn = connect_db()
    #return sqlite3.Row
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results


#from username get user_id
def get_user_id(username):
    result = fetch_query("SELECT * FROM Users WHERE username = ?", (username,))
    return result[0]['user_id']


# FR-TK-003
def reserve_seats(event_id, seat_ids, username, user_id):
    """
    Handle seat reservation with transaction locking to ensure data consistency
    """
    conn = connect_db()
    try:
        cur = conn.cursor()
        # Start transaction with immediate lock to avoid race conditions
        cur.execute("BEGIN IMMEDIATE")

        # fetch seat info for validation
        placeholders = ",".join("?" for _ in seat_ids)
        cur.execute(f"""
            SELECT s.id, s.is_reserved, s.type, st.price
            FROM Seats s
            JOIN SeatTypes st 
              ON st.event_id = s.event_id AND st.type = s.type
            WHERE s.event_id=? AND s.id IN ({placeholders})
        """, [event_id] + seat_ids)
        rows = cur.fetchall()

        # check seat existence and availability
        if len(rows) != len(seat_ids):
            conn.rollback()
            return {"status": "fail", "message": "Invalid seat selection: some seats not found"}
        if any(r[1] == 1 for r in rows):
            conn.rollback()
            return {"status": "fail", "message": "Reservation failed: one or more seats already taken"}

        # calculate total price
        total_price = 0
        for seat_id, is_reserved, seat_type, price in rows:
            #print(seat_id, seat_type, price)
            total_price += price

        # create order record
        cur.execute(
            "INSERT INTO Orders (event_id, user_id, created_at, total_price) VALUES (?, ?, datetime('now'), ?)",
            (event_id, user_id, total_price)
        )
        order_id = cur.lastrowid

        # insert order items and update seat/stock
        for seat_id, _, seat_type, price in rows:
            # Add order item with price lookup
            cur.execute("""
                INSERT INTO OrderDetails (order_id, seat_id, seat_type, price) 
                VALUES (?, ?, ?, ?)
            """, (order_id, seat_id, seat_type, price))
            # Mark seat as reserved
            cur.execute("UPDATE Seats SET is_reserved=1 WHERE id=?", (seat_id,))
            # Reduce stock for the seat type
            cur.execute("UPDATE SeatTypes SET stock = stock - 1 WHERE event_id=? AND type=?", (event_id, seat_type))

        # Step 5: commit transaction
        conn.commit()

        # 新增：更新缓存中已预订的座位状态（使用调整后的导入）
        for seat_id in seat_ids:  # <-- 新增
            update_seat_cache(event_id, seat_id, 1)  # <-- 新增

        return {"status": "success", "order_id": order_id, 'total_price': total_price}
    except Exception as e:
        conn.rollback()
        print("Error in reserve_seats:", e)  # 打印具体错误
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}
    finally:
        conn.close()
