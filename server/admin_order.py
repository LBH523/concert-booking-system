from flask import Blueprint, request, jsonify, session
from database.db import execute_query, fetch_query, get_user_id
admin_order_bp = Blueprint("admin_order", __name__)

# FR-OM-001
@admin_order_bp.route('/show_orders', methods=['get'])
def show_orders():
    #check is_admin
    session_id = request.headers.get('Session-ID')
    session_info = fetch_query("SELECT username, is_admin FROM Sessions WHERE session_id = ?", (session_id,))
    if not session_info:
        return jsonify({'status': 'fail', 'message': 'Invalid or expired session'}), 401
    username = session_info[0]['username']
    is_admin = session_info[0]['is_admin']
    user_id = get_user_id(username)

    status = request.args.get("status") #0-only status == 0  1-only status == 1  2-ignore status and return all
    if status is None:
        return jsonify({'status': 'fail', 'message': 'Need a status'}), 400

    try:
        # only show the user's own orders
        if is_admin == 0:
            if status == '2':
                order_info = fetch_query(f"""
                    SELECT e.name, o.total_price, o.created_at, u.username, o.id
                    FROM Events e
                    JOIN Orders o ON e.id = o.event_id
                    JOIN Users u ON u.user_id = o.user_id
                    WHERE o.user_id = ?
                """, (user_id,))
            else:
                order_info = fetch_query(f"""
                    SELECT e.name, o.total_price, o.created_at, u.username, o.id
                    FROM Events e
                    JOIN Orders o ON e.id = o.event_id
                    JOIN Users u ON u.user_id = o.user_id
                    WHERE o.user_id = ? and o.status = ?
                """, (user_id, status))
        # show all users' orders
        else:
            if status == '2':
                order_info = fetch_query(f"""
                    SELECT e.name, o.total_price, o.created_at, u.username, o.id
                    FROM Events e
                    JOIN Orders o ON e.id = o.event_id
                    JOIN Users u ON u.user_id = o.user_id
                """)
            else:
                order_info = fetch_query(f"""
                    SELECT e.name, o.total_price, o.created_at, u.username, o.id
                    FROM Events e
                    JOIN Orders o ON e.id = o.event_id
                    JOIN Users u ON u.user_id = o.user_id
                    WHERE o.status = ?
                """, (status,))
    except Exception as e:
        # 捕获异常并返回错误信息
        return jsonify({'status': 'fail', 'message': str(e)}), 500
    if order_info:
        dict_order_info = [dict(row) for row in order_info]
        return jsonify({'status': 'success', 'data': dict_order_info})
    else:
        return jsonify({'status': 'success', 'data': []})

# FR-OM-002
@admin_order_bp.route('/cancel_order', methods=['post'])
def cancel_order():
    id = request.args.get("id")
    print(id)
    try:
        execute_query('UPDATE Orders SET status = 0 WHERE id = ?', (id,))
        return jsonify({'status': 'success', 'message': 'Order has been canceled'}), 200
    except Exception as e:
        # 捕获异常并返回错误信息
        return jsonify({'status': 'fail', 'message': str(e)}), 500



