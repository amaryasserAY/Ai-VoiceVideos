import os
import sys
import streamlit.web.cli as stcli

def resolve_path(path):
    """تحديد المسار الصحيح سواء في الوضع العادي أو بعد التغليف"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, path)

if __name__ == "__main__":
    # 1. تحديد مسار التطبيق الرئيسي
    app_path = resolve_path("app.py")
    
    # 2. إعداد أوامر تشغيل Streamlit
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
        "--server.headless=true",  # تشغيل بدون واجهة تحكم
        "--theme.base=dark"        # فرض الثيم الداكن
    ]
    
    # 3. التشغيل
    print(f"🚀 Launching AI Editor from: {app_path}")
    sys.exit(stcli.main())