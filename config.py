# config.py - إعدادات النظام الأساسية
import os
from pathlib import Path
from datetime import timedelta
BASE_DIR = Path(__file__).parent.absolute()
class Config:
    """إعدادات النظام الأساسية"""
    
    # ============== مسارات النظام ==============
    
    DATA_DIR = BASE_DIR / "data"
    DATABASE_PATH = BASE_DIR / "data" / "charity.db"    
    STATIC_DIR = BASE_DIR / "static"
    LOGS_DIR = BASE_DIR / "logs"
    
    # ============== قاعدة البيانات ==============
    #DATABASE_URL = "sqlite:///data/charity.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"    
    DATABASE_ECHO = False  # True لعرض استعلامات SQL للتdebug
    
    # ============== إعدادات التطبيق ==============
    APP_NAME = "نظام إدارة الجمعية الخيرية"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "نظام متكامل لإدارة أنشطة الجمعيات الخيرية"
    DEBUG = True

    # إعدادات الجلسة
    SESSION_TIMEOUT = 60 * 60 * 24  # 24 ساعة
    
    # إعدادات الملفات
    UPLOAD_FOLDER = BASE_DIR / "data" / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


    # ============== الألوان والتصميم ==============
    PRIMARY_COLOR = "#3498db"      # أزرق
    SECONDARY_COLOR = "#2ecc71"    # أخضر
    ACCENT_COLOR = "#e74c3c"       # أحمر
    BACKGROUND_COLOR = "#f8f9fa"   # رمادي فاتح
    TEXT_COLOR = "#2c3e50"         # رمادي غامق
    
    # ============== إعدادات الأمان ==============
    SECRET_KEY = "charity-system-secret-key-2024-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ساعة
    
    # أدوار النظام
    ROLES = {
        "admin": "مدير النظام",
        "supervisor": "مشرف",
        "employee": "موظف",
        "viewer": "مراجع"
    }
    
    # صلاحيات الأدوار
    ROLE_PERMISSIONS = {
        "admin": ["*"],  # كل الصلاحيات
        "supervisor": [
            "view:*", "create:*", "edit:*", "delete:limited",
            "export:*", "approve:limited"
        ],
        "employee": [
            "view:*", "create:own", "edit:own", 
            "export:own", "delete:none"
        ],
        "viewer": ["view:*", "export:limited", "create:none", "edit:none"]
    }
    
    # ============== إعدادات النسخ الاحتياطي ==============
    BACKUP_ENABLED = True
    BACKUP_DIR = DATA_DIR / "backups"
    BACKUP_RETENTION_DAYS = 30
    
    # ============== إعدادات التقارير ==============
    REPORT_DATE_FORMAT = "%Y-%m-%d"
    REPORT_TIME_FORMAT = "%H:%M:%S"
    DEFAULT_TIMEZONE = "Africa/Cairo"
    
    # ============== دوال المساعدة ==============
    @classmethod
    def setup_directories(cls):
        """إنشاء المجلدات المطلوبة للنظام"""
        directories = [
            cls.DATA_DIR,
            cls.STATIC_DIR,
            cls.LOGS_DIR,
            cls.STATIC_DIR / "css",
            cls.STATIC_DIR / "images",
            cls.BACKUP_DIR if cls.BACKUP_ENABLED else None
        ]
        
        for directory in directories:
            if directory:
                directory.mkdir(exist_ok=True, parents=True)
                print(f"📁 تم إنشاء المجلد: {directory}")
    
    @classmethod
    def get_role_name(cls, role_key: str) -> str:
        """الحصول على اسم الدور بالعربية"""
        return cls.ROLES.get(role_key, "غير معروف")
    
    @classmethod
    def check_permission(cls, role: str, permission: str) -> bool:
        """التحقق من صلاحية دور معين"""
        permissions = cls.ROLE_PERMISSIONS.get(role, [])
        
        # إذا كان الدور admin فله كل الصلاحيات
        if role == "admin":
            return True
        
        # التحقق من الصلاحية العامة (*)
        if "*" in permissions:
            return True
        
        # التحقق من الصلاحية المحددة
        for perm in permissions:
            if permission in perm:
                return True
        
        return False

# إنشاء نسخة من الإعدادات
settings = Config()