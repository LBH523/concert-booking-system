import pytest
import json
from database.db import fetch_query

class TestUserRegistration:
    """测试用户注册功能 (FR-UM-001)"""
    
    def test_successful_registration(self, client):
        """测试成功注册"""
        response = client.post('/register', json={
            'username': 'newuser',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'Registration successful'
        
        # 验证用户确实被创建在数据库中
        users = fetch_query("SELECT * FROM Users WHERE username = ?", ('newuser',))
        assert len(users) == 1
        assert users[0]['username'] == 'newuser'
        assert users[0]['is_admin'] == 0  # 默认不是管理员
    
    def test_duplicate_username(self, client):
        """测试用户名重复注册"""
        # 先注册一个用户
        client.post('/register', json={
            'username': 'duplicate_user',
            'password': 'password123'
        })
        
        # 尝试用相同用户名再次注册
        response = client.post('/register', json={
            'username': 'duplicate_user',
            'password': 'anotherpass'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['status'] == 'fail'
        assert data['message'] == 'Username already exists'
    
    def test_missing_username(self, client):
        """测试缺少用户名"""
        response = client.post('/register', json={
            'password': 'password123'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'fail'
        assert 'Username or password is required' in data['message']
    
    def test_missing_password(self, client):
        """测试缺少密码"""
        response = client.post('/register', json={
            'username': 'testuser'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'fail'
        assert 'Username or password is required' in data['message']
    
    def test_empty_request(self, client):
        """测试空请求"""
        response = client.post('/register', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'fail'

class TestUserLogin:
    """测试用户登录功能 (FR-UM-002)"""
    
    def test_successful_login(self, client):
        """测试成功登录"""
        # 先注册用户
        client.post('/register', json={
            'username': 'loginuser',
            'password': 'loginpass'
        })
        
        # 尝试登录
        response = client.post('/login', json={
            'username': 'loginuser',
            'password': 'loginpass'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['message'] == 'Login successful'
        assert 'session_id' in data
        
        # 验证会话被创建
        session_id = data['session_id']
        sessions = fetch_query("SELECT * FROM Sessions WHERE session_id = ?", (session_id,))
        assert len(sessions) == 1
        assert sessions[0]['username'] == 'loginuser'
        assert sessions[0]['is_admin'] == 0
    
    def test_invalid_credentials(self, client):
        """测试无效凭据"""
        response = client.post('/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'fail'
        assert data['message'] == 'Invalid credentials'
    
    def test_wrong_password(self, client):
        """测试错误密码"""
        # 注册用户
        client.post('/register', json={
            'username': 'wrongpass_user',
            'password': 'correctpass'
        })
        
        # 使用错误密码登录
        response = client.post('/login', json={
            'username': 'wrongpass_user',
            'password': 'wrongpass'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['status'] == 'fail'
        assert data['message'] == 'Invalid credentials'
    
    def test_login_session_replacement(self, client):
        """测试登录时替换旧会话"""
        username = 'session_user'
        password = 'sessionpass'
        
        # 注册用户
        client.post('/register', json={
            'username': username,
            'password': password
        })
        
        # 第一次登录
        response1 = client.post('/login', json={
            'username': username,
            'password': password
        })
        session_id_1 = response1.get_json()['session_id']
        
        # 验证第一个会话存在
        sessions1 = fetch_query("SELECT * FROM Sessions WHERE session_id = ?", (session_id_1,))
        assert len(sessions1) == 1
        
        # 第二次登录（应该替换第一个会话）
        response2 = client.post('/login', json={
            'username': username,
            'password': password
        })
        session_id_2 = response2.get_json()['session_id']
        
        # 验证新会话存在
        sessions2 = fetch_query("SELECT * FROM Sessions WHERE session_id = ?", (session_id_2,))
        assert len(sessions2) == 1
        
        # 验证旧会话被删除
        old_sessions = fetch_query("SELECT * FROM Sessions WHERE session_id = ?", (session_id_1,))
        assert len(old_sessions) == 0
    
    def test_admin_login(self, client):
        """测试管理员登录"""
        # 手动创建管理员用户
        from database.db import execute_query
        execute_query(
            "INSERT INTO Users (username, password, is_admin) VALUES (?, ?, ?)",
            ('test_admin', 'adminpass', 1)
        )
        
        # 管理员登录
        response = client.post('/login', json={
            'username': 'test_admin',
            'password': 'adminpass'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        
        # 验证管理员权限
        session_id = data['session_id']
        sessions = fetch_query("SELECT * FROM Sessions WHERE session_id = ?", (session_id,))
        assert len(sessions) == 1
        assert sessions[0]['is_admin'] == 1