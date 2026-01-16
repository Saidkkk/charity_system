# auth/authentication.py - النسخة المصححة
from database.session import session_scope
from database.models import User, UserSession
from datetime import datetime, timedelta
import secrets

class AuthManager:
    """مدير المصادقة"""
    
    def __init__(self):
        self.current_user = None
    
    def login(self, username: str, password: str, ip_address: str = None, user_agent: str = None):
        """تسجيل دخول المستخدم"""
        with session_scope() as session:
            try:
                # البحث عن المستخدم
                user = session.query(User).filter(User.username == username).first()
                
                if not user:
                    return {"success": False, "message": "اسم المستخدم غير موجود"}
                
                # التحقق من حالة الحساب
                if user.status != 'active':
                    status_messages = {
                        'inactive': 'الحساب غير نشط',
                        'suspended': 'الحساب موقوف',
                        'pending': 'الحساب قيد الانتظار'
                    }
                    msg = status_messages.get(str(user.status).lower(), 'الحساب غير نشط')
                    return {"success": False, "message": msg}
                
                # التحقق من كلمة المرور (نص عادي مؤقتاً)
                if password != user.password_hash:
                    return {"success": False, "message": "كلمة المرور غير صحيحة"}
                
                # إنشاء جلسة جديدة
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(days=1)
                
                user_session = UserSession(
                    user_id=user.id,
                    session_token=session_token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=expires_at,
                    is_active=True
                )
                
                session.add(user_session)
                
                # تحديث آخر دخول
                user.last_login = datetime.now()
                
                # إرجاع البيانات
                return {
                    "success": True,
                    "session_token": session_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "role": str(user.role),  # تأكد أنه نص
                        "email": user.email,
                        "department": user.department
                    }
                }
                
            except Exception as e:
                print(f"❌ خطأ في تسجيل الدخول: {e}")
                import traceback
                traceback.print_exc()
                return {"success": False, "message": "حدث خطأ أثناء تسجيل الدخول"}
    
    def logout(self, session_token: str):
        """تسجيل خروج المستخدم"""
        with session_scope() as session:
            try:
                user_session = session.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True
                ).first()
                
                if user_session:
                    user_session.is_active = False
                    user_session.logout_at = datetime.now()
                    return {
                    "success": True,
                    "message": "تم تسجيل الخروج بنجاح"
                }
                return {
                    "success": False,
                    "message": "لم يتم العثور على الجلسة"
                }
            except Exception as e:
                print(f"❌ خطأ في تسجيل الخروج: {e}")
                return {
                    "success": False,
                    "message": "❌ خطأ في تسجيل الخروج: {e}"
                }
    
    def validate_session(self, session_token: str):
        """التحقق من صحة الجلسة"""
        with session_scope() as session:
            try:
                user_session = session.query(UserSession).filter(
                    UserSession.session_token == session_token,
                    UserSession.is_active == True,
                    UserSession.expires_at > datetime.now()
                ).first()
                
                if not user_session:
                    return None
                
                # تحديث وقت آخر نشاط
                user_session.last_activity = datetime.now()
                
                # الحصول على بيانات المستخدم
                user = session.query(User).filter(
                    User.id == user_session.user_id
                ).first()
                
                if not user:
                    return None
                
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": str(user.role),  # تأكد أنه نص
                    "email": user.email,
                    "department": user.department
                }
            except Exception as e:
                print(f"❌ خطأ في التحقق من الجلسة: {e}")
                return None

# إنشاء نسخة عامة
auth_manager = AuthManager()

# دوال مساعدة
def login(username: str, password: str, **kwargs):
    return auth_manager.login(username, password, **kwargs)

def logout(session_token: str):
    return auth_manager.logout(session_token)

def is_authenticated(session_token: str):
    return auth_manager.validate_session(session_token) is not None

def get_current_user(session_token: str):
    return auth_manager.validate_session(session_token)