import pytest
import os
import tempfile
import shutil
from flask import Flask
import sys

# 添加父目录到 Python 路径，以便导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import connect_db, execute_query, fetch_query
from app import app
from user import user_bp
from admin_event import admin_event_bp
from ticket_booking import ticket_booking_bp
from admin_order import admin_order_bp

@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 获取原始数据库路径
    original_db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'concert.db')
    
    # 创建临时数据库文件
    temp_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(temp_dir, 'test_concert.db')
    
    # 复制原始数据库到临时位置
    shutil.copy2(original_db_path, test_db_path)
    
    # 备份原始数据库路径
    import database.db
    original_path = database.db.DB_PATH
    database.db.DB_PATH = test_db_path
    
    # 确保外键约束启用
    conn = database.db.connect_db()
    conn.execute('PRAGMA foreign_keys = ON')
    conn.commit()
    conn.close()
    
    yield test_db_path
    
    # 恢复原始路径
    database.db.DB_PATH = original_path
    # 清理临时文件
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def client(test_db):
    """创建测试客户端"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def admin_session(client):
    """创建管理员会话"""
    # 检查是否已存在管理员用户
    admin_users = fetch_query("SELECT * FROM Users WHERE username = 'admin'")
    
    if not admin_users:
        # 创建管理员用户
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('admin', 'admin', 1)
        )
    
    # 清理可能存在的旧会话
    execute_query("DELETE FROM Sessions WHERE username = 'admin'")
    
    # 登录获取session_id
    response = client.post('/login', json={
        'username': 'admin',
        'password': 'admin'
    })
    
    if response.status_code == 200:
        data = response.get_json()
        if data and 'session_id' in data:
            return data['session_id']
    
    raise Exception("Failed to create admin session")

@pytest.fixture
def user_session(client):
    """创建普通用户会话"""
    # 清理可能存在的旧用户和会话
    execute_query("DELETE FROM Sessions WHERE username = 'testuser'")
    execute_query("DELETE FROM Users WHERE username = 'testuser'")
    
    # 注册一个普通用户
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'user123'
    })
    
    # 登录获取session_id
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'user123'
    })
    
    if response.status_code == 200:
        data = response.get_json()
        if data and 'session_id' in data:
            return data['session_id']
    
    raise Exception("Failed to create user session")

@pytest.fixture
def sample_event(client, admin_session):
    """创建示例活动"""
    # 先尝试查找有座位的活动
    events_with_seats = fetch_query("SELECT DISTINCT event_id FROM Seats LIMIT 1")
    
    if events_with_seats:
        return events_with_seats[0]['event_id']
    
    # 如果没有有座位的活动，返回第一个活动
    existing_events = fetch_query("SELECT * FROM Events LIMIT 1")
    if existing_events:
        return existing_events[0]['id']
    
    # 如果没有任何活动，创建一个测试活动
    response = client.post('/add_event',
        data={
            'name': 'Sample Test Event',
            'event_date': '2025-12-25',
            'start_time': '20:00',
            'price_1': '1000',
            'price_2': '600',
            'price_3': '300'
        },
        headers={'Session-ID': admin_session}
    )
    
    if response.status_code == 200:
        # 获取刚创建的活动ID
        new_event = fetch_query("SELECT id FROM Events WHERE name = ?", ('Sample Test Event',))
        if new_event:
            return new_event[0]['id']
    
    return None

@pytest.fixture
def sample_order(client, user_session, sample_event):
    """创建示例订单"""
    if not sample_event:
        return None
        
    # 获取可用的座位
    response = client.get(f'/get_seats?event_id={sample_event}')
    if response.status_code != 200:
        return None
        
    seats = response.get_json().get('data', [])
    if len(seats) < 2:
        return None
        
    # 预订前两个座位
    seat_ids = [seats[0]['id'], seats[1]['id']]
    response = client.post('/book_ticket', 
        json={
            'event_id': sample_event,
            'seat_ids': seat_ids
        },
        headers={'Session-ID': user_session}
    )
    
    if response.status_code == 200:
        return response.get_json().get('order_id')
    return None

def clear_test_data():
    """清理测试数据"""
    try:
        execute_query("DELETE FROM Events WHERE name LIKE 'Test%' OR name = 'Sample Test Event'")
        execute_query("DELETE FROM Users WHERE username LIKE 'test%'")
        execute_query("DELETE FROM Sessions WHERE username LIKE 'test%'")
    except:
        pass

@pytest.fixture(autouse=True)
def cleanup():
    """自动清理测试数据"""
    yield
    clear_test_data()