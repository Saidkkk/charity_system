# database/session.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from config import Config

# استخدم Base من models بدلاً من إنشاء قاعدة جديدة
from database.models import Base

class DatabaseManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._init_engine()
        self._create_tables()
    
    def _init_engine(self):
        """تهيئة محرك قاعدة البيانات"""
        try:
            print(f"📁 مسار قاعدة البيانات: {Config.DATABASE_PATH}")
            print(f"📁 هل المجلد موجود؟: {Config.DATABASE_PATH.parent.exists()}")
            
            # إنشاء المجلد إذا لم يكن موجوداً
            Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
            
            # إنشاء المحرك
            self.engine = create_engine(
                Config.DATABASE_URL,
                connect_args={"check_same_thread": False},
                echo=False,  # تعطيل في الإنتاج
                pool_pre_ping=True
            )
            
            # إنشاء جلسة محلية
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            print("✅ تم تهيئة محرك قاعدة البيانات بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_tables(self):
        """إنشاء جميع الجداول"""
        try:
            # استيراد جميع النماذج أولاً
            from database.models import get_all_models
            
            # إنشاء جميع الجداول
            Base.metadata.create_all(bind=self.engine)
            print(f"✅ تم إنشاء {len(get_all_models())} جدول بنجاح")
            
            # عرض الجداول المنشأة
            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            print(f"📋 الجداول المنشأة ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء الجداول: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def test_connection(self):
        """اختبار الاتصال بقاعدة البيانات"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                value = result.scalar()
                if value == 1:
                    print("✅ اختبار الاتصال ناجح")
                    return True
                else:
                    print(f"⚠️  اختبار الاتصال عاد قيمة غير متوقعة: {value}")
                    return False
        except Exception as e:
            print(f"❌ فشل اختبار الاتصال: {e}")
            return False
    
    def get_session(self):
        """الحصول على جلسة قاعدة البيانات"""
        return self.SessionLocal()
    
    def get_engine(self):
        """الحصول على محرك قاعدة البيانات"""
        return self.engine

# إنشاء نسخة عامة
db_manager = DatabaseManager()

# database/session.py - أضف في النهاية

from contextlib import contextmanager

@contextmanager
def session_scope():
    """محيط الجلسة لإدارة سياق قاعدة البيانات"""
    session = db_manager.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()    


