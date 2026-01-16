# create_test_activities.py
"""
إضافة بيانات تجريبية للأنشطة
"""

from database.session import session_scope, db_manager
from database.models import (
    ActivityCategory, ActivityType, Activity, 
    ActivityBeneficiary, Beneficiary, Family
)
from datetime import date, timedelta
import random

def create_test_activities():
    """إنشاء بيانات تجريبية للأنشطة"""
    
    print("🚀 بدء إنشاء بيانات تجريبية للأنشطة...")
    
    with session_scope() as session:
        # 1. فئات الأنشطة
        categories_data = [
            {"name": "مساعدات عينية", "name_en": "In-Kind Assistance", "color": "#FF6B6B"},
            {"name": "مساعدات مالية", "name_en": "Financial Assistance", "color": "#4ECDC4"},
            {"name": "أنشطة ثقافية", "name_en": "Cultural Activities", "color": "#45B7D1"},
            {"name": "أنشطة تعليمية", "name_en": "Educational Activities", "color": "#96CEB4"},
            {"name": "أنشطة صحية", "name_en": "Health Activities", "color": "#FFEAA7"},
        ]
        
        for cat_data in categories_data:
            category = ActivityCategory(
                name=cat_data["name"],
                name_en=cat_data["name_en"],
                color=cat_data["color"],
                is_active=True
            )
            session.add(category)
        
        session.flush()
        print(f"✅ تم إنشاء {len(categories_data)} فئة نشاط")
        
        # 2. أنواع الأنشطة
        activity_types_data = [
            {"name": "توزيع سلال غذائية", "category_id": 1, "code": "FOOD01"},
            {"name": "توزيع ملابس", "category_id": 1, "code": "CLOTH01"},
            {"name": "مساعدات مالية شهرية", "category_id": 2, "code": "FIN01"},
            {"name": "مساعدات طارئة", "category_id": 2, "code": "EMERG01"},
            {"name": "رحلات ترفيهية", "category_id": 3, "code": "TRIP01"},
            {"name": "حفلات أعياد", "category_id": 3, "code": "PARTY01"},
            {"name": "دورات تقوية", "category_id": 4, "code": "EDU01"},
            {"name": "ورش عمل", "category_id": 4, "code": "WORKSHOP01"},
            {"name": "كشف طبي مجاني", "category_id": 5, "code": "MED01"},
            {"name": "توعية صحية", "category_id": 5, "code": "HEALTH01"},
        ]
        
        for type_data in activity_types_data:
            activity_type = ActivityType(
                name=type_data["name"],
                category_id=type_data["category_id"],
                code=type_data["code"],
                is_active=True
            )
            session.add(activity_type)
        
        session.flush()
        print(f"✅ تم إنشاء {len(activity_types_data)} نوع نشاط")
        
        # 3. أنشطة عينة
        activity_titles = [
            "توزيع سلال غذائية رمضان 2026",
            "توزيع ملابس الشتاء للأطفال",
            "مساعدات مالية للأسر المتعففة",
            "رحلة ترفيهية لأطفال الأسر",
            "دورات تقوية لطلاب الثانوية",
            "كشف طبي مجاني للعيون",
            "حفلة عيد الفطر للأطفال",
            "ورشة عمل الخياطة للسيدات",
            "توزيع لحوم الأضاحي",
            "برنامج التوعية الصحية"
        ]
        
        statuses = ['planned', 'in_progress', 'completed']
        priorities = ['low', 'medium', 'high']
        
        today = date.today()
        
        for i, title in enumerate(activity_titles):
            # تاريخ عشوائي في الأشهر الـ3 القادمة
            days_offset = random.randint(-30, 90)
            start_date = today + timedelta(days=days_offset)
            
            # مدة النشاط 1-7 أيام
            duration = random.randint(1, 7)
            end_date = start_date + timedelta(days=duration)
            
            activity = Activity(
                title=title,
                activity_type_id=random.randint(1, 10),
                start_date=start_date,
                end_date=end_date,
                duration_days=duration,
                location=f"موقع {i+1}",
                city=["الرياض", "جدة", "مكة", "الدمام", "القصيم"][i % 5],
                estimated_cost=random.randint(1000, 10000),
                actual_cost=random.randint(800, 9500),
                currency="SAR",
                status=statuses[i % 3],
                priority=priorities[i % 3],
                responsible_person=["أحمد محمد", "سالم علي", "فاطمة خالد"][i % 3],
                description=f"وصف تفصيلي لنشاط {title}",
                created_by=1  # مستخدم admin
            )
            session.add(activity)
        
        session.flush()
        print(f"✅ تم إنشاء {len(activity_titles)} نشاط")
        
        # 4. إضافة مشاركين عشوائيين للأنشطة
        print("🔄 إضافة مشاركين للأنشطة...")
        
        # جلب بعض المستفيدين
        beneficiaries = session.query(Beneficiary).limit(20).all()
        activities = session.query(Activity).all()
        
        participant_roles = ["مستفيد رئيسي", "مشارك", "متطوع", "منظم"]
        
        for activity in activities:
            # إضافة 3-8 مشاركين لكل نشاط
            num_participants = random.randint(3, 8)
            selected_beneficiaries = random.sample(beneficiaries, 
                                                  min(num_participants, len(beneficiaries)))
            
            for beneficiary in selected_beneficiaries:
                participant = ActivityBeneficiary(
                    activity_id=activity.id,
                    beneficiary_id=beneficiary.id,
                    role=random.choice(participant_roles),
                    status='active',
                    start_date=activity.start_date
                )
                session.add(participant)
        
        print("✅ تمت إضافة المشاركين")
        
        session.commit()
        print("🎉 تم إنشاء جميع البيانات التجريبية بنجاح!")
        print(f"📊 الإحصائيات:")
        print(f"   - الفئات: {len(categories_data)}")
        print(f"   - الأنواع: {len(activity_types_data)}")
        print(f"   - الأنشطة: {len(activity_titles)}")
        print(f"   - المشاركين: {sum(len(a.beneficiaries) for a in activities)}")

if __name__ == "__main__":
    create_test_activities()