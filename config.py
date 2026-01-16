# config.py - إصدار متوافق مع Streamlit Cloud
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()

def is_streamlit_cloud():
    """التأكد إذا كنا على Streamlit Cloud"""
    return 'STREAMLIT_CLOUD' in os.environ or 'STREAMLIT_CLOUD' in os.environ.get('SERVER_SOFTWARE', '')

class Config:
    """إعدادات النظام - متوافق مع Streamlit Cloud"""
    
    # ============== اكتشاف البيئة ==============
    IS_CLOUD = is_streamlit_cloud()
    
    # ============== مسارات النظام ==============
    if IS_CLOUD:
        # على السحابة: استخدم /tmp للبيانات
        DATA_DIR = Path("/tmp/charity_data")
        DATABASE_PATH = DATA_DIR / "charity.db"
        UPLOAD_FOLDER = DATA_DIR / "uploads"
        LOGS_DIR = DATA_DIR / "logs"
        BACKUP_DIR = DATA_DIR / "backups"
        print("🔧 تشغيل في بيئة Streamlit Cloud")
    else:
        # محلياً: استخدم المجلدات العادية
        DATA_DIR = BASE_DIR / "data"
        DATABASE_PATH = DATA_DIR / "charity.db"
        UPLOAD_FOLDER = DATA_DIR / "uploads"
        LOGS_DIR = BASE_DIR / "logs"
        BACKUP_DIR = DATA_DIR / "backups"
        print("💻 تشغيل محلي")
    
    STATIC_DIR = BASE_DIR / "static"
    
    # ============== قاعدة البيانات ==============
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
    DATABASE_ECHO = False
    
    # ============== إعدادات التطبيق ==============
    APP_NAME = "نظام إدارة الجمعية الخيرية"
    APP_VERSION = "1.0.0"
    DEBUG = False if IS_CLOUD else True  # تعطيل DEBUG على السحابة
    
    # ============== إعدادات الأمان ==============
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    
    # أدوار النظام
    ROLES = {
        "admin": "مدير النظام",
        "supervisor": "مشرف",
        "employee": "موظف",
        "viewer": "مراجع"
    }
    
    # ============== دوال المساعدة ==============
    @classmethod
    def setup_directories(cls):
        """إنشاء المجلدات المطلوبة - آمن للـ Cloud"""
        try:
            # مجلدات يجب إنشاؤها
            directories = [
                cls.DATA_DIR,
                cls.UPLOAD_FOLDER,
                cls.LOGS_DIR,
                cls.STATIC_DIR,
                cls.BACKUP_DIR
            ]
            
            for directory in directories:
                if directory:
                    directory.mkdir(exist_ok=True, parents=True)
                    print(f"✅ تم إنشاء/التحقق من: {directory}")
            
            # إنشاء مجلدات static إذا لم تكن موجودة
            (cls.STATIC_DIR / "css").mkdir(exist_ok=True, parents=True)
            (cls.STATIC_DIR / "images").mkdir(exist_ok=True, parents=True)
            
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء المجلدات: {e}")
            # على Cloud، حاول مجلد /tmp فقط
            if cls.IS_CLOUD:
                try:
                    Path("/tmp/charity_simple").mkdir(exist_ok=True)
                    cls.DATABASE_PATH = Path("/tmp/charity_simple/charity.db")
                    print(f"✅ استخدم مسار بديل: {cls.DATABASE_PATH}")
                    return True
                except:
                    return False
            return False
    
    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        """التحقق من صلاحية دور معين"""
        if role == "admin":
            return True
        # ... باقي المنطق (بسيط للنشر الأول)
        return True

# ============== التنفيذ الفوري ==============
settings = Config()

# إنشاء المجلدات تلقائياً عند التحميل
if __name__ == "__main__":
    print("=" * 50)
    print(f"🌍 البيئة: {'Cloud' if settings.IS_CLOUD else 'Local'}")
    print(f"📁 DATA_DIR: {settings.DATA_DIR}")
    print(f"🗄️  DATABASE: {settings.DATABASE_PATH}")
    print(f"🔗 DATABASE_URL: {settings.DATABASE_URL}")
    
    if settings.setup_directories():
        print("✅ تهيئة النظام ناجحة!")
    else:
        print("⚠️  هناك مشكلة في التهيئة")
    print("=" * 50)