from flask import Blueprint, request, jsonify, session
from database.db import execute_query, fetch_query
import sqlite3
import uuid
#from datetime import datetime, timedelta
user_bp = Blueprint('user', __name__)

#FR-UM-001
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'status': 'fail', 'message': 'Username or password is required'}), 400

    try:
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            (username, password, 0)
        )
        return jsonify({'status': 'success', 'message': 'Registration successful'}), 200
    except sqlite3.IntegrityError:
        return jsonify({'status': 'fail', 'message': 'Username already exists'}), 409
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal server error'}), 500


#FR-UM-002
@user_bp.route('/login', methods=['POST'])
def login():
    #print('login')
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    try:
        user = fetch_query("SELECT * FROM Users WHERE username = ? and password = ?", (username, password))
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({'message': 'Server is wrong'}), 500
    if user:
        #save login status
        user_info = user[0]
        session_id = str(uuid.uuid4())
        #expires_at = datetime.utcnow() + timedelta(hours=2)
        try:
            # delete old session before login
            execute_query("DELETE FROM Sessions WHERE username = ?", (username,))
            execute_query("INSERT INTO Sessions (session_id, username, is_admin) VALUES (?, ?, ?)",
                      (session_id, user_info['username'], user_info['is_admin']))
            return jsonify({
                'status': 'success',
                'message': 'Login successful',
                'session_id': session_id
            })
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
    else:
        return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

