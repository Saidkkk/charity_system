# init_db.py - النسخة المحدثة
import sys
from pathlib import Path
from datetime import datetime

# إضافة المسار الرئيسي للنظام
sys.path.append(str(Path(__file__).parent))

from config import Config
from database.session import db_manager
from database.models import User, UserRole, UserStatus

def create_default_users(session):
    """إنشاء المستخدمين الافتراضيين"""
    try:
        print("👥 جارٍ إنشاء المستخدمين الافتراضيين...")
        
        # قائمة المستخدمين الافتراضيين
        default_users = [
            {
                "username": "admin",
                "email": "admin@charity.org",
                "password_hash": "admin123",  # في الإنتاج: استخدم bcrypt أو similar
                "full_name": "مدير النظام",
                "phone": "0501234567",
                "role": UserRole.admin,
                "status": UserStatus.active,
                "department": "الإدارة",
                "position": "مدير النظام"
            },
            {
                "username": "supervisor",
                "email": "supervisor@charity.org",
                "password_hash": "supervisor123",
                "full_name": "المشرف العام",
                "phone": "0501112233",
                "role": UserRole.SUPERVISOR,
                "status": UserStatus.ACTIVE,
                "department": "الإشراف",
                "position": "مشرف عام"
            },
            {
                "username": "employee1",
                "email": "employee@charity.org",
                "password_hash": "employee123",
                "full_name": "موظف الجمعية",
                "phone": "0509998888",
                "role": UserRole.EMPLOYEE,
                "status": UserStatus.ACTIVE,
                "department": "المتابعة",
                "position": "موظف متابعة"
            }
        ]
        
        users_count = 0
        for user_data in default_users:
            # التحقق من عدم وجود المستخدم
            existing_user = session.query(User).filter(
                (User.username == user_data["username"]) | 
                (User.email == user_data["email"])
            ).first()
            
            if not existing_user:
                user = User(**user_data)
                session.add(user)
                users_count += 1
                print(f"   ✓ تم إنشاء المستخدم: {user_data['username']}")
            else:
                print(f"   ⚠️  المستخدم موجود مسبقاً: {user_data['username']}")
        
        session.commit()
        print(f"✅ تم إنشاء {users_count} مستخدم جديد")
        return users_count
        
    except Exception as e:
        session.rollback()
        print(f"❌ خطأ في إنشاء المستخدمين: {e}")
        import traceback
        traceback.print_exc()
        return 0

def create_default_activity_categories(session):
    """إنشاء فئات الأنشطة الافتراضية"""
    try:
        from database.models import ActivityCategory
        
        default_categories = [
            {"name": "زيارات ميدانية", "name_en": "Field Visits", "color": "#3B82F6", "icon": "visit"},
            {"name": "توزيع مساعدات", "name_en": "Aid Distribution", "color": "#10B981", "icon": "distribution"},
            {"name": "أنشطة توعوية", "name_en": "Awareness Activities", "color": "#8B5CF6", "icon": "awareness"},
            {"name": "تدريبات وورش عمل", "name_en": "Trainings & Workshops", "color": "#F59E0B", "icon": "training"},
            {"name": "فعاليات خاصة", "name_en": "Special Events", "color": "#EF4444", "icon": "event"},
        ]
        
        for category_data in default_categories:
            existing = session.query(ActivityCategory).filter_by(name=category_data["name"]).first()
            if not existing:
                category = ActivityCategory(**category_data)
                session.add(category)
        
        session.commit()
        print("✅ تم إنشاء فئات الأنشطة الافتراضية")
        
    except Exception as e:
        session.rollback()
        print(f"⚠️  خطأ في إنشاء فئات الأنشطة: {e}")

def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🚀 نظام إدارة الجمعية الخيرية - تهيئة قاعدة البيانات")
    print("=" * 60)
    print()
    
    # إنشاء المجلدات
    print("📁 جارٍ إنشاء المجلدات المطلوبة...")
    folders = [
        Config.DATABASE_PATH.parent,
        Path("static"),
        Path("logs"),
        Path("static/css"),
        Path("static/images"),
        Path("data/backups")
    ]
    
    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {folder}")
    
    print("✅ تم إنشاء المجلدات")
    print()
    
    # اختبار الاتصال
    print("🔌 جارٍ فحص اتصال قاعدة البيانات...")
    if db_manager.test_connection():
        print("✅ تم فحص الاتصال بنجاح")
    else:
        print("❌ فشل اختبار الاتصال بقاعدة البيانات")
        return
    
    print()
    print("📊 جارٍ إنشاء البيانات الأولية...")
    print()
    
    # الحصول على جلسة قاعدة البيانات
    session = db_manager.get_session()
    
    try:
        # إنشاء البيانات الأولية
        users_count = create_default_users(session)
        create_default_activity_categories(session)
        
        # عرض ملخص قاعدة البيانات
        from sqlalchemy import inspect
        inspector = inspect(db_manager.engine)
        tables = inspector.get_table_names()
        
        print()
        print("📋 ملخص قاعدة البيانات:")
        print(f"   - عدد الجداول: {len(tables)}")
        print(f"   - عدد المستخدمين: {users_count}")
        print(f"   - مسار قاعدة البيانات: {Config.DATABASE_PATH}")
        
        if Config.DATABASE_PATH.exists():
            size = Config.DATABASE_PATH.stat().st_size
            print(f"   - حجم قاعدة البيانات: {size:,} بايت ({size/1024:.1f} كيلوبايت)")
        
        print()
        print("✨ تم الانتهاء من التهيئة بنجاح!")
        print()
        print("🔑 بيانات الدخول الافتراضية:")
        print("   - اسم المستخدم: admin | كلمة المرور: admin123")
        print("   - اسم المستخدم: supervisor | كلمة المرور: supervisor123")
        print("   - اسم المستخدم: employee1 | كلمة المرور: employee123")
        print()
        print("⚠️  ملاحظة: في الإنتاج الحقيقي، يجب تغيير كلمات المرور الافتراضية!")
        
    except Exception as e:
        print(f"❌ خطأ أثناء التهيئة: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()