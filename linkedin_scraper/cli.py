# linkedin_scraper/cli.py
"""
Command-line interface wrapper
"""

def main():
    """Main entry point that imports and runs the original main"""
    # 使用绝对导入，从项目根目录导入
    import sys
    import os
    
    # 将当前包的父目录添加到路径（site-packages）
    # 但由于 main.py 不在包中，这个方式不可靠
    
    # 更好的方法：直接导入模块
    # 如果 main.py 已经安装在 site-packages 中
    try:
        from main import main as _main
        _main()
    except ImportError:
        # 如果 main.py 不在包中，尝试添加路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from main import main as _main
        _main()

if __name__ == "__main__":
    main()