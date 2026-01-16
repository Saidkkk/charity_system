# modules/activities.py - النسخة المصححة
"""
نظام إدارة الأنشطة والفعاليات - النسخة الآمنة
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
from sqlalchemy import func  # ⬅️ المهم!
from database.session import session_scope
from database.models import (
    Activity, ActivityType, ActivityCategory, 
    ActivityBeneficiary, Beneficiary, User
)

# إعدادات النظام
SYSTEM_CURRENCY = "EGP"  # جنيه مصري
CURRENCY_NAME = "جنيها"   # اسم العملة بالعربية

def _manage_activity_types(user_data=None):
    """
    إدارة أنواع الأنشطة - المصححة
    """
    st.subheader("🏷️ إدارة أنواع الأنشطة")
    
    if user_data and user_data.get('role') not in ['admin', 'supervisor']:
        st.error("⚠️ تحتاج إلى صلاحية مشرف أو مسؤول")
        return
    
    tab1, tab2, tab3 = st.tabs(["📋 عرض الأنواع", "➕ نوع جديد", "🏷️ فئات الأنشطة"])
    
    with tab1:
        with session_scope() as session:
            types = session.query(ActivityType).all()
            
            if not types:
                st.info("لا توجد أنواع أنشطة")
                return
            
            for atype in types:
                with st.expander(f"🏷️ {atype.name}"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"**الكود:** {atype.code or 'بدون'}")
                        st.write(f"**الفئة:** {atype.category.name if atype.category else 'بدون'}")
                        st.write(f"**الحالة:** {'نشط' if atype.is_active else 'غير نشط'}")
                    
                    with col2:
                        if st.button(f"✏️ تعديل", key=f"edit_type_{atype.id}"):
                            st.session_state.edit_activity_type_id = atype.id
                            st.rerun()
                    
                    with col3:
                        if st.button(f"🗑️ حذف", key=f"delete_type_{atype.id}", type="secondary"):
                            # التحقق من عدم وجود أنشطة مرتبطة
                            activities_count = session.query(Activity).filter(
                                Activity.activity_type_id == atype.id
                            ).count()
                            
                            if activities_count > 0:
                                st.error(f"❌ لا يمكن حذف النوع لأنه مرتبط بـ {activities_count} نشاط")
                            else:
                                session.delete(atype)
                                session.commit()
                                st.success("✅ تم الحذف")
                                st.rerun()
    
    with tab2:
        with st.form("add_activity_type_form"):
            name = st.text_input("اسم النوع *", max_chars=100)
            code = st.text_input("الكود (اختياري)", max_chars=20)
            description = st.text_area("الوصف", height=100)
            
            # اختيار الفئة
            with session_scope() as session:
                categories = session.query(ActivityCategory).filter(
                    ActivityCategory.is_active == True
                ).all()
                
                if not categories:
                    st.warning("⚠️ يجب إضافة فئات أولاً")
                    category_id = None
                else:
                    category_options = {c.name: c.id for c in categories}
                    selected_category = st.selectbox(
                        "الفئة *",
                        list(category_options.keys())
                    )
                    category_id = category_options[selected_category]
            
            is_active = st.checkbox("نشط", value=True)
            
            submitted = st.form_submit_button("➕ إضافة النوع")
            
            if submitted:
                if not name or not category_id:
                    st.error("الاسم والفئة مطلوبان")
                    return
                
                try:
                    with session_scope() as session:
                        new_type = ActivityType(
                            name=name,
                            code=code or None,
                            description=description or None,
                            category_id=category_id,
                            is_active=is_active
                        )
                        
                        session.add(new_type)
                        session.commit()  # ⬅️ هذا السطر المهم!
                        
                        st.success(f"✅ تمت إضافة نوع '{name}'")
                        st.balloons()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ خطأ: {str(e)}")
    
    with tab3:
        _manage_activity_categories(user_data)

def _edit_activity_type_form(type_id: int, user_data=None):
    """
    تعديل نوع النشاط
    """
    st.subheader("✏️ تعديل نوع النشاط")
    
    try:
        with session_scope() as session:
            activity_type = session.query(ActivityType).filter(ActivityType.id == type_id).first()
            
            if not activity_type:
                st.error("نوع النشاط غير موجود")
                return
            
            with st.form(f"edit_activity_type_{type_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("اسم النوع", value=activity_type.name or "")
                    new_code = st.text_input("الكود", value=activity_type.code or "")
                
                with col2:
                    new_is_active = st.checkbox("نشط", value=activity_type.is_active)
                    
                    # الفئات
                    categories = session.query(ActivityCategory).filter(
                        ActivityCategory.is_active == True
                    ).all()
                    
                    if categories:
                        category_options = {c.name: c.id for c in categories}
                        current_category_name = activity_type.category.name if activity_type.category else ""
                        
                        selected_category = st.selectbox(
                            "الفئة",
                            list(category_options.keys()),
                            index=list(category_options.keys()).index(current_category_name) 
                            if current_category_name in category_options else 0
                        )
                        category_id = category_options[selected_category]
                    else:
                        st.warning("لا توجد فئات")
                        category_id = None
                
                new_description = st.text_area("الوصف", value=activity_type.description or "", height=100)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 حفظ التغييرات")
                with col_cancel:
                    if st.form_submit_button("❌ إلغاء"):
                        if 'edit_activity_type_id' in st.session_state:
                            del st.session_state.edit_activity_type_id
                        st.rerun()
                
                if submitted:
                    try:
                        activity_type.name = new_name
                        activity_type.code = new_code if new_code else None
                        activity_type.description = new_description if new_description else None
                        activity_type.is_active = new_is_active
                        
                        if category_id:
                            activity_type.category_id = category_id
                        
                        session.commit()
                        
                        st.success("✅ تم تحديث نوع النشاط!")
                        
                        # مسح حالة التعديل
                        if 'edit_activity_type_id' in st.session_state:
                            del st.session_state.edit_activity_type_id
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ خطأ: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")

def _manage_activity_categories(user_data=None):
    """
    إدارة فئات الأنشطة - مع التعديل والحذف
    """
    st.subheader("🏷️ فئات الأنشطة")
    
    if user_data and user_data.get('role') not in ['admin', 'supervisor']:
        st.error("⚠️ تحتاج إلى صلاحية مشرف أو مسؤول")
        return
    
    tab1, tab2 = st.tabs(["📋 الفئات", "➕ فئة جديدة"])
    
    with tab1:
        with session_scope() as session:
            categories = session.query(ActivityCategory).all()
            
            if not categories:
                st.info("لا توجد فئات")
                return
            
            for category in categories:
                with st.expander(f"🎯 {category.name} ({'نشط' if category.is_active else 'غير نشط'})"):
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.write(f"**الوصف:** {category.description or 'بدون وصف'}")
                        st.write(f"**اللون:** ")
                        st.markdown(f"""
                        <div style="background-color:{category.color or '#4CAF50'}; 
                                    width:30px; height:30px; border-radius:4px;">
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # عدد أنواع الأنشطة في هذه الفئة
                        types_count = session.query(ActivityType).filter(
                            ActivityType.category_id == category.id
                        ).count()
                        st.write(f"**عدد الأنواع:** {types_count}")
                        
                        # زر التعديل
                        if st.button(f"✏️ تعديل", key=f"edit_cat_{category.id}", use_container_width=True):
                            st.session_state.edit_category_id = category.id
                            st.rerun()
                    
                    with col3:
                        # زر الحذف
                        if st.button(f"🗑️ حذف", key=f"delete_cat_{category.id}", 
                                   type="secondary", use_container_width=True):
                            # التحقق من عدم وجود أنواع مرتبطة
                            types_count = session.query(ActivityType).filter(
                                ActivityType.category_id == category.id
                            ).count()
                            
                            if types_count > 0:
                                st.error(f"❌ لا يمكن حذف الفئة لأنها مرتبطة بـ {types_count} نوع نشاط")
                            else:
                                confirm = st.checkbox(f"أؤكد حذف فئة '{category.name}'", 
                                                    key=f"confirm_del_cat_{category.id}")
                                if confirm:
                                    session.delete(category)
                                    session.commit()
                                    st.success("✅ تم الحذف")
                                    st.rerun()
    
    with tab2:
        with st.form("add_category_form"):
            name = st.text_input("اسم الفئة *", max_chars=50)
            description = st.text_area("الوصف", height=100)
            
            col1, col2 = st.columns(2)
            with col1:
                color = st.color_picker("اختر لون", "#4CAF50")
            
            with col2:
                is_active = st.checkbox("نشط", value=True)
            
            submitted = st.form_submit_button("➕ إضافة الفئة")
            
            if submitted:
                if not name:
                    st.error("اسم الفئة مطلوب")
                    return
                
                try:
                    with session_scope() as session:
                        # التحقق من عدم التكرار
                        existing = session.query(ActivityCategory).filter(
                            ActivityCategory.name == name
                        ).first()
                        
                        if existing:
                            st.error("⚠️ الفئة موجودة مسبقاً")
                            return
                        
                        new_category = ActivityCategory(
                            name=name,
                            description=description or None,
                            color=color,
                            is_active=is_active
                        )
                        
                        session.add(new_category)
                        session.commit()
                        
                        st.success(f"✅ تمت إضافة فئة '{name}'")
                        st.balloons()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ خطأ: {str(e)}")

def _edit_category_form(category_id: int, user_data=None):
    """
    تعديل فئة الأنشطة
    """
    st.subheader("✏️ تعديل فئة الأنشطة")
    
    try:
        with session_scope() as session:
            category = session.query(ActivityCategory).filter(
                ActivityCategory.id == category_id
            ).first()
            
            if not category:
                st.error("الفئة غير موجودة")
                return
            
            with st.form(f"edit_category_{category_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_name = st.text_input("اسم الفئة", value=category.name or "")
                    new_description = st.text_area("الوصف", 
                                                  value=category.description or "",
                                                  height=100)
                
                with col2:
                    new_color = st.color_picker("اختر لون", 
                                               value=category.color or "#4CAF50")
                    new_is_active = st.checkbox("نشط", value=category.is_active)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 حفظ التغييرات", type="primary")
                with col_cancel:
                    if st.form_submit_button("❌ إلغاء", type="secondary"):
                        if 'edit_category_id' in st.session_state:
                            del st.session_state.edit_category_id
                        st.rerun()
                
                if submitted:
                    if not new_name:
                        st.error("اسم الفئة مطلوب")
                        return
                    
                    try:
                        # التحقق من عدم التكرار (إذا تغير الاسم)
                        if new_name != category.name:
                            existing = session.query(ActivityCategory).filter(
                                ActivityCategory.name == new_name
                            ).first()
                            if existing:
                                st.error("⚠️ اسم الفئة موجود مسبقاً")
                                return
                        
                        category.name = new_name
                        category.description = new_description if new_description else None
                        category.color = new_color
                        category.is_active = new_is_active
                        
                        session.commit()
                        
                        st.success("✅ تم تحديث الفئة!")
                        
                        # مسح حالة التعديل
                        if 'edit_category_id' in st.session_state:
                            del st.session_state.edit_category_id
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ خطأ: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")                    

def show_activities(user_data=None):
    """
    الواجهة الرئيسية للأنشطة
    """
    st.title("📅 إدارة الأنشطة والفعاليات")
    
    # التحقق من حالات التعديل
    if 'edit_activity_id' in st.session_state:
        _edit_activity_form(st.session_state.edit_activity_id, user_data)
        return
    
    if 'edit_activity_type_id' in st.session_state:
        # دالة تعديل نوع النشاط (يمكن إضافتها لاحقاً)
        st.info("تعديل نوع النشاط - قيد التطوير")
        if st.button("العودة"):
            del st.session_state.edit_activity_type_id
            st.rerun()
        return
    
    # علامات التبويب الرئيسية - المحسنة
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 قائمة الأنشطة",
        "➕ نشاط جديد", 
        "👥 إدارة المشاركين",
        "🏷️ أنواع الأنشطة",
        "📊 إحصائيات"
    ])
    
    with tab1:
        _show_activities_list(user_data)
    
    with tab2:
        _add_new_activity(user_data)
    
    with tab3:
        _manage_participants(user_data)
    
    with tab4:
        _manage_activity_types(user_data)
    
    with tab5:
        _show_statistics(user_data)


def _show_activities_list(user_data=None):
    """
    عرض قائمة الأنشطة
    """
    st.subheader("📋 قائمة الأنشطة")
    
    # فلترة الأنشطة
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox(
            "فلترة بالحالة",
            ["الكل", "planned", "in_progress", "completed", "cancelled"],
            format_func=lambda x: {
                "الكل": "الكل",
                "planned": "مخطط",
                "in_progress": "قيد التنفيذ",
                "completed": "مكتمل",
                "cancelled": "ملغي"
            }.get(x, x)
        )
    
    with col2:
        date_filter = st.selectbox(
            "فلترة بالتاريخ",
            ["الكل", "هذا الشهر", "الأسبوع الحالي", "المستقبلية", "الماضية"]
        )
    
    with col3:
        search_query = st.text_input("بحث بالعنوان")
    
    try:
        with session_scope() as session:
            # بناء الاستعلام
            query = session.query(Activity)
            
            # تطبيق الفلترة
            if status_filter != "الكل":
                query = query.filter(Activity.status == status_filter)
            
            if date_filter != "الكل":
                today = date.today()
                if date_filter == "هذا الشهر":
                    first_day = date(today.year, today.month, 1)
                    last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
                    query = query.filter(Activity.start_date.between(first_day, last_day))
                elif date_filter == "الأسبوع الحالي":
                    start_week = today - timedelta(days=today.weekday())
                    end_week = start_week + timedelta(days=6)
                    query = query.filter(Activity.start_date.between(start_week, end_week))
                elif date_filter == "المستقبلية":
                    query = query.filter(Activity.start_date >= today)
                elif date_filter == "الماضية":
                    query = query.filter(Activity.start_date < today)
            
            if search_query:
                query = query.filter(Activity.title.ilike(f"%{search_query}%"))
            
            # جلب البيانات
            activities = query.order_by(Activity.start_date.desc()).limit(100).all()
            
            if not activities:
                st.info("📭 لا توجد أنشطة مطابقة للبحث")
                return
            
            # عرض البيانات
            for activity in activities:
                with st.expander(f"**{activity.title}** - {_get_status_ar(activity.status)}"):
                    _display_activity_details(activity, session, user_data)
    
    except Exception as e:
        st.error(f"حدث خطأ في جلب البيانات: {str(e)}")

def _display_activity_details(activity: Activity, session, user_data=None):
    """
    عرض تفاصيل النشاط
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**التاريخ:** {activity.start_date.strftime('%Y-%m-%d')}")
        if activity.end_date:
            st.write(f"**إلى:** {activity.end_date.strftime('%Y-%m-%d')}")
        
        st.write(f"**المكان:** {activity.location or 'غير محدد'}")
        st.write(f"**المدينة:** {activity.city or 'غير محدد'}")
        
        if activity.estimated_cost:
            st.write(f"**التكلفة المتوقعة:** {activity.estimated_cost:,.2f} {CURRENCY_NAME}")
        
        if activity.actual_cost:
            st.write(f"**التكلفة الفعلية:** {activity.actual_cost:,.2f} {CURRENCY_NAME}")
    
    with col2:
        st.write(f"**حالة الأولوية:** {_get_priority_ar(activity.priority)}")
        st.write(f"**المسؤول:** {activity.responsible_person or 'غير محدد'}")
        st.write(f"**فريق العمل:** {activity.team_members or 'غير محدد'}")
        
        # عدد المشاركين
        participants_count = session.query(ActivityBeneficiary).filter(
            ActivityBeneficiary.activity_id == activity.id
        ).count()
        st.write(f"**عدد المشاركين:** {participants_count}")
    
    # عرض الوصف
    if activity.description:
        st.markdown("### 📝 الوصف")
        st.write(activity.description)
    
    # خيارات التعديل
    if user_data and user_data.get('role') in ['admin', 'supervisor']:
        st.markdown("---")
        col_edit, col_participants = st.columns(2)
        
        with col_edit:
            if st.button(f"✏️ تعديل النشاط", key=f"edit_{activity.id}"):
                st.session_state.edit_activity_id = activity.id
                st.rerun()
        
        # with col_participants:
        #     if st.button(f"👥 إدارة المشاركين", key=f"participants_{activity.id}"):
        #         st.session_state.manage_participants_id = activity.id
        #         st.rerun()

def _add_new_activity(user_data=None):
    """
    إضافة نشاط جديد
    """
    st.subheader("➕ إضافة نشاط جديد")
    
    with st.form("add_activity_form"):
        # المعلومات الأساسية
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("عنوان النشاط *", max_chars=200)
            
            # أنواع الأنشطة
            with session_scope() as session:
                activity_types = session.query(ActivityType).filter(
                    ActivityType.is_active == True
                ).all()
                
                type_options = {t.name: t.id for t in activity_types}
                
                if type_options:
                    activity_type_id = st.selectbox(
                        "نوع النشاط *",
                        list(type_options.keys())
                    )
                    selected_type_id = type_options[activity_type_id]
                else:
                    st.warning("⚠️ يجب إضافة أنواع الأنشطة أولاً")
                    selected_type_id = None
        
        with col2:
            start_date = st.date_input(
                "تاريخ البدء *",
                min_value=date.today()
            )
            
            end_date = st.date_input(
                "تاريخ الانتهاء",
                min_value=date.today()
            )
        
        # الموقع والتكلفة
        col3, col4 = st.columns(2)
        
        with col3:
            location = st.text_input("الموقع", max_chars=200)
            city = st.text_input("المدينة", max_chars=50)
        
        with col4:
            estimated_cost = st.number_input(
                f"التكلفة المتوقعة ({CURRENCY_NAME})",  # ⬅️ هنا
                min_value=0.0,
                value=0.0,
                step=100.0
            )
        
        # معلومات إضافية
        description = st.text_area("وصف النشاط", height=150)
        
        col5, col6 = st.columns(2)
        
        with col5:
            responsible_person = st.text_input("اسم المسؤول", max_chars=100)
            team_members = st.text_input("فريق العمل (افصل بفواصل)")
        
        with col6:
            status = st.selectbox(
                "حالة النشاط",
                ["planned", "in_progress", "completed", "cancelled"],
                format_func=lambda x: {
                    "planned": "مخطط",
                    "in_progress": "قيد التنفيذ",
                    "completed": "مكتمل",
                    "cancelled": "ملغي"
                }.get(x, x)
            )
            
            priority = st.selectbox(
                "الأولوية",
                ["low", "medium", "high", "urgent"],
                format_func=lambda x: {
                    "low": "منخفضة",
                    "medium": "متوسطة",
                    "high": "عالية",
                    "urgent": "عاجلة"
                }.get(x, x)
            )
        
        submitted = st.form_submit_button("➕ إضافة النشاط")
        
        if submitted:
            # التحقق من الحقول المطلوبة
            if not all([title, selected_type_id, start_date]):
                st.error("⚠️ يرجى ملء جميع الحقول المطلوبة (*)")
                return
            
            try:
                # حساب مدة النشاط
                duration_days = None
                if end_date and end_date > start_date:
                    duration_days = (end_date - start_date).days
                
                with session_scope() as session:
                    # الحصول على user_id للمنشئ
                    created_by = None
                    if user_data:
                        created_by = user_data.get('user_id')
                    elif 'user_id' in st.session_state:
                        created_by = st.session_state.user_id
                    
                    # إنشاء النشاط
                    new_activity = Activity(
                        title=title,
                        activity_type_id=selected_type_id,
                        start_date=start_date,
                        end_date=end_date if end_date else None,
                        duration_days=duration_days,
                        location=location or None,
                        city=city or None,
                        estimated_cost=estimated_cost if estimated_cost > 0 else None,
                        currency=SYSTEM_CURRENCY,
                        status=status,
                        priority=priority,
                        responsible_person=responsible_person or None,
                        team_members=team_members or None,
                        description=description or None,
                        created_by=created_by
                    )
                    
                    session.add(new_activity)
                    session.flush()
                    
                    st.success(f"✅ تمت إضافة النشاط '{title}' بنجاح!")
                    st.balloons()
                    
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء الإضافة: {str(e)}")

def _manage_participants(user_data=None):
    """
    إدارة مشاركين النشاط
    """
    st.subheader("👥 إدارة المشاركين في الأنشطة")
    
    # اختيار النشاط
    try:
        with session_scope() as session:
            activities = session.query(Activity).order_by(Activity.start_date.desc()).limit(50).all()
            
            if not activities:
                st.info("📭 لا توجد أنشطة")
                return
            
            activity_options = {
                f"{a.title} ({a.start_date.strftime('%Y-%m-%d')})": a.id 
                for a in activities
            }
            
            selected_activity = st.selectbox(
                "اختر النشاط",
                list(activity_options.keys())
            )
            
            if selected_activity:
                activity_id = activity_options[selected_activity]
                _manage_activity_participants(activity_id, session, user_data)
    
    except Exception as e:
        st.error(f"حدث خطأ: {str(e)}")

def _manage_activity_participants(activity_id: int, session, user_data=None):
    """
    إدارة المشاركين في نشاط محدد - النسخة النهائية
    """

    # # زر العودة في الأعلى
    # col_back, col_title = st.columns([1, 4])
    # with col_back:
    #     if st.button("⬅️ العودة للقائمة", type="secondary"):
    #         if 'manage_participants_id' in st.session_state:
    #             del st.session_state.manage_participants_id
    #         if 'selected_beneficiary_for_activity' in st.session_state:
    #             del st.session_state.selected_beneficiary_for_activity
    #         st.rerun()


    # جلب النشاط
    activity = session.query(Activity).filter(Activity.id == activity_id).first()
    
    if not activity:
        st.error("النشاط غير موجود")
        return
    
    st.markdown(f"### 🎯 النشاط: **{activity.title}**")
    
    # ========== عرض المشاركين الحاليين ==========
    st.subheader("👥 المشاركين الحاليين")
    
    participants = session.query(ActivityBeneficiary).filter(
        ActivityBeneficiary.activity_id == activity_id
    ).all()
    
    if participants:
        for p in participants:
            beneficiary = session.query(Beneficiary).filter(
                Beneficiary.id == p.beneficiary_id
            ).first()
            
            if beneficiary:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{beneficiary.full_name_ar}**")
                    if beneficiary.national_id:
                        st.caption(f"الرقم القومي: {beneficiary.national_id}")
                
                with col2:
                    st.write(f"الدور: {p.role or 'مشارك'}")
                    st.write(f"الحالة: {p.status or 'نشط'}")
                
                with col3:
                    if st.button(f"🗑️", key=f"remove_{p.id}", help="إزالة المشارك"):
                        session.delete(p)
                        session.commit()
                        st.success("تمت الإزالة")
                        st.rerun()
                st.markdown("---")
    else:
        st.info("لا يوجد مشاركين")
    
    # ========== إضافة مشارك جديد ==========
    st.subheader("➕ إضافة مشارك جديد")
    
    # البحث عن المستفيدين
    search_query = st.text_input("🔍 ابحث عن مستفيد (بالاسم أو الرقم القومي)")
    
    # متغير لحفظ الاختيار
    if 'selected_beneficiary_for_activity' not in st.session_state:
        st.session_state.selected_beneficiary_for_activity = None
    
    # عرض نتائج البحث
    if search_query:
        beneficiaries = session.query(Beneficiary).filter(
            (Beneficiary.full_name_ar.ilike(f"%{search_query}%")) |
            (Beneficiary.national_id.ilike(f"%{search_query}%"))
        ).limit(20).all()
        
        if beneficiaries:
            st.write(f"**النتائج ({len(beneficiaries)})**")
            
            # إنشاء أعمدة لعرض النتائج
            cols_per_row = 2
            for i in range(0, len(beneficiaries), cols_per_row):
                cols = st.columns(cols_per_row)
                
                for j in range(cols_per_row):
                    if i + j < len(beneficiaries):
                        beneficiary = beneficiaries[i + j]
                        
                        with cols[j]:
                            with st.container(border=True):
                                # معلومات المستفيد
                                st.write(f"**{beneficiary.full_name_ar}**")
                                if beneficiary.national_id:
                                    st.caption(f"الرقم: {beneficiary.national_id}")
                                if beneficiary.phone:
                                    st.caption(f"📞 {beneficiary.phone}")
                                
                                # التحقق إذا كان مضافاً
                                existing = session.query(ActivityBeneficiary).filter(
                                    ActivityBeneficiary.activity_id == activity_id,
                                    ActivityBeneficiary.beneficiary_id == beneficiary.id
                                ).first()
                                
                                if existing:
                                    st.warning("⚠️ مضاف بالفعل")
                                else:
                                    # زر الاختيار
                                    if st.button(f"اختر", 
                                               key=f"select_{beneficiary.id}_{activity_id}",
                                               use_container_width=True,
                                               type="secondary"):
                                        st.session_state.selected_beneficiary_for_activity = beneficiary.id
                                        st.success(f"✅ تم اختيار: {beneficiary.full_name_ar}")
                                        st.rerun()
        else:
            st.warning("⚠️ لم يتم العثور على نتائج")
    
    # ========== المستفيد المختار ==========
    if st.session_state.selected_beneficiary_for_activity:
        beneficiary = session.query(Beneficiary).filter(
            Beneficiary.id == st.session_state.selected_beneficiary_for_activity
        ).first()
        
        if beneficiary:
            st.success(f"✅ **المستفيد المختار:** {beneficiary.full_name_ar}")
            
            # نموذج إضافة المشارك
            with st.form("add_selected_participant"):
                role = st.text_input("الدور في النشاط", value="مشارك")
                notes = st.text_area("ملاحظات (اختياري)")
                
                col_add, col_clear = st.columns(2)
                with col_add:
                    add_submitted = st.form_submit_button("➕ إضافة المشارك", type="primary")
                with col_clear:
                    if st.form_submit_button("🗑️ مسح الاختيار"):
                        st.session_state.selected_beneficiary_for_activity = None
                        st.rerun()
                
                if add_submitted:
                    try:
                        # التحقق من عدم التكرار
                        existing = session.query(ActivityBeneficiary).filter(
                            ActivityBeneficiary.activity_id == activity_id,
                            ActivityBeneficiary.beneficiary_id == beneficiary.id
                        ).first()
                        
                        if existing:
                            st.error("⚠️ هذا المستفيد مضاف بالفعل لهذا النشاط")
                        else:
                            # إضافة المشارك
                            new_participant = ActivityBeneficiary(
                                activity_id=activity_id,
                                beneficiary_id=beneficiary.id,
                                role=role or None,
                                status='active',
                                start_date=date.today(),
                                notes=notes or None
                            )
                            
                            session.add(new_participant)
                            session.commit()
                            
                            st.success(f"✅ تمت إضافة {beneficiary.full_name_ar} كمشارك")
                            
                            # مسح التحديد
                            st.session_state.selected_beneficiary_for_activity = None
                            st.rerun()
                            
                    except Exception as e:
                        session.rollback()
                        st.error(f"❌ حدث خطأ: {str(e)}")
    # # في نهاية الدالة، أضف زر العودة أيضاً
    # st.markdown("---")
    # if st.button("⬅️ العودة لقائمة الأنشطة", use_container_width=True, type="secondary"):
    #     if 'manage_participants_id' in st.session_state:
    #         del st.session_state.manage_participants_id
    #     if 'selected_beneficiary_for_activity' in st.session_state:
    #         del st.session_state.selected_beneficiary_for_activity
    #     st.rerun()



def _edit_activity_form(activity_id: int, user_data=None):
    """
    تعديل نشاط
    """
    st.subheader("✏️ تعديل النشاط")
    
    try:
        with session_scope() as session:
            activity = session.query(Activity).filter(Activity.id == activity_id).first()
            
            if not activity:
                st.error("النشاط غير موجود")
                return
            
            with st.form(f"edit_activity_{activity_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_title = st.text_input("عنوان النشاط", value=activity.title or "")
                    new_location = st.text_input("الموقع", value=activity.location or "")
                    new_city = st.text_input("المدينة", value=activity.city or "")
                
                with col2:
                    new_start_date = st.date_input(
                        "تاريخ البدء",
                        value=activity.start_date if activity.start_date else date.today()
                    )
                    
                    # حالة النشاط
                    status_options = ["planned", "in_progress", "completed", "cancelled"]
                    status_labels = {
                        "planned": "مخطط",
                        "in_progress": "قيد التنفيذ", 
                        "completed": "مكتمل",
                        "cancelled": "ملغي"
                    }
                    current_status_index = status_options.index(activity.status) if activity.status in status_options else 0
                    
                    new_status = st.selectbox(
                        "حالة النشاط",
                        status_options,
                        index=current_status_index,
                        format_func=lambda x: status_labels.get(x, x)
                    )
                
                new_description = st.text_area("الوصف", value=activity.description or "", height=100)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 حفظ التغييرات")
                with col_cancel:
                    if st.form_submit_button("❌ إلغاء"):
                        if 'edit_activity_id' in st.session_state:
                            del st.session_state.edit_activity_id
                        st.rerun()
                
                if submitted:
                    try:
                        activity.title = new_title
                        activity.location = new_location
                        activity.city = new_city
                        activity.start_date = new_start_date
                        activity.status = new_status
                        activity.description = new_description
                        activity.updated_at = datetime.now()
                        
                        session.commit()
                        
                        st.success("✅ تم تحديث النشاط!")
                        
                        # مسح حالة التعديل
                        if 'edit_activity_id' in st.session_state:
                            del st.session_state.edit_activity_id
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"خطأ: {str(e)}")
    
    except Exception as e:
        st.error(f"خطأ: {str(e)}")

def _show_statistics(user_data=None):
    """
    عرض إحصائيات الأنشطة
    """
    st.subheader("📊 إحصائيات الأنشطة")
    
    try:
        with session_scope() as session:
            # إحصائيات أساسية
            total_activities = session.query(Activity).count()
            completed_activities = session.query(Activity).filter(
                Activity.status == 'completed'
            ).count()
            
            # عدد المشاركين الإجمالي
            total_participants = session.query(ActivityBeneficiary).count()
            
            # مؤشرات الأداء
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("إجمالي الأنشطة", total_activities)
            
            with col2:
                st.metric("الأنشطة المكتملة", completed_activities)
            
            with col3:
                completion_rate = (completed_activities / total_activities * 100) if total_activities > 0 else 0
                st.metric("نسبة الإكمال", f"{completion_rate:.1f}%")
            
            with col4:
                st.metric("إجمالي المشاركات", total_participants)
            
            st.markdown("---")
            
            # توزيع الأنشطة حسب الحالة
            st.subheader("📈 توزيع الأنشطة حسب الحالة")
            
            status_counts = session.query(
                Activity.status,
                func.count(Activity.id)
            ).group_by(Activity.status).all()
            
            if status_counts:
                status_labels = {
                    'planned': 'مخطط',
                    'in_progress': 'قيد التنفيذ',
                    'completed': 'مكتمل',
                    'cancelled': 'ملغي'
                }
                
                labels = [status_labels.get(s[0], s[0]) for s in status_counts]
                values = [s[1] for s in status_counts]
                
                fig_status = px.pie(
                    names=labels,
                    values=values,
                    title="توزيع الأنشطة حسب الحالة"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            # أنشطة الشهر الحالي
            st.subheader("📅 أنشطة الشهر الحالي")
            
            today = date.today()
            first_day = date(today.year, today.month, 1)
            last_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
            
            monthly_activities = session.query(Activity).filter(
                Activity.start_date.between(first_day, last_day)
            ).all()
            
            if monthly_activities:
                activities_data = []
                for activity in monthly_activities:
                    activities_data.append({
                        "النشاط": activity.title,
                        "التاريخ": activity.start_date.strftime("%Y-%m-%d"),
                        "الحالة": _get_status_ar(activity.status),
                        "المكان": activity.location or "غير محدد"
                    })
                
                st.dataframe(
                    pd.DataFrame(activities_data),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("لا توجد أنشطة هذا الشهر")
    
    except Exception as e:
        st.error(f"حدث خطأ في جلب الإحصائيات: {str(e)}")

def _get_status_ar(status):
    """تحويل حالة النشاط للعربية"""
    status_map = {
        'planned': 'مخطط',
        'in_progress': 'قيد التنفيذ',
        'completed': 'مكتمل',
        'cancelled': 'ملغي'
    }
    return status_map.get(status, status)

def _get_priority_ar(priority):
    """تحويل الأولوية للعربية"""
    priority_map = {
        'low': 'منخفضة',
        'medium': 'متوسطة',
        'high': 'عالية',
        'urgent': 'عاجلة'
    }
    return priority_map.get(priority, priority)

# ==================== التعامل مع التعديل ====================


# ==================== التشغيل الرئيسي ====================

def show_activities_main(user_data=None):
    """
    الدالة الرئيسية مع معالجة الحالات
    """
    # التحقق من حالة تعديل النشاط
    if 'edit_activity_id' in st.session_state:
        _edit_activity_form(st.session_state.edit_activity_id, user_data)
        return
    
    # التحقق من حالة تعديل نوع النشاط
    if 'edit_activity_type_id' in st.session_state:
        _edit_activity_type_form(st.session_state.edit_activity_type_id, user_data)
        return

    # التحقق من حالة تعديل الفئة
    if 'edit_category_id' in st.session_state:
        _edit_category_form(st.session_state.edit_category_id, user_data)
        return
    
    # التحقق من حالة إدارة المشاركين
    if 'manage_participants_id' in st.session_state:
        try:
            with session_scope() as session:
                _manage_activity_participants(
                    st.session_state.manage_participants_id, 
                    session, 
                    user_data
                )
        except Exception as e:
            st.error(f"خطأ: {str(e)}")
        return
    
    # العرض العادي
    show_activities(user_data)


# ==================== التشغيل المباشر ====================

if __name__ == "__main__":
    show_activities_main()