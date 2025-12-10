#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

def run_quick_test():
    """快速运行一个简单的测试来验证环境"""
    script_dir = Path(__file__).parent
    venv_python = script_dir / "5003p" / "Scripts" / "python.exe"
    
    print("🔍 验证测试环境...")
    
    # 运行一个简单的测试文件
    cmd = [
        str(venv_python),
        "-m", "pytest", 
        "tests/test_user.py::TestUserLogin::test_login_success",
        "-v",
        "--tb=short",
        "--no-header"
    ]
    
    print(f"🔧 执行: {' '.join(cmd[-3:])}")
    
    try:
        result = subprocess.run(cmd, cwd=script_dir, capture_output=True, text=True, timeout=120)
        
        print("📊 输出:")
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️ 错误:")
            print(result.stderr)
            
        print(f"🔚 返回码: {result.returncode}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

if __name__ == "__main__":
    success = run_quick_test()
    print(f"\n🎯 测试环境验证: {'✅ 正常' if success else '❌ 异常'}")