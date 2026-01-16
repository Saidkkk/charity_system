# add_users.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database.session import db_manager, session_scope
from database.models import User, UserRole, UserStatus

def add_users_directly():
    """إضافة المستخدمين مباشرة إلى قاعدة البيانات"""
    with session_scope() as session:
        # قائمة المستخدمين
        users_data = [
            {
                "username": "admin",
                "email": "admin@charity.org",
                "password_hash": "admin123",
                "full_name": "مدير النظام",
                "phone": "0501234567",
                "role": UserRole.ADMIN,
                "status": UserStatus.ACTIVE,
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
        
        added_count = 0
        for data in users_data:
            # تحقق إذا كان المستخدم موجوداً
            existing = session.query(User).filter_by(username=data["username"]).first()
            if not existing:
                user = User(**data)
                session.add(user)
                added_count += 1
                print(f"✅ أضيف المستخدم: {data['username']}")
        
        # session.commit() يتم تلقائياً في session_scope
        print(f"\n🎉 تمت إضافة {added_count} مستخدم جديد")
        
        # عرض جميع المستخدمين للتحقق
        print("\n📋 جميع المستخدمين في النظام:")
        all_users = session.query(User).all()
        for user in all_users:
            print(f"  - {user.username} ({user.full_name}) - {user.role.value}")

if __name__ == "__main__":
    add_users_directly()