# modules/beneficiaries.py - النسخة المبسطة والفعالة
"""
نظام إدارة المستفيدين والأسر - النسخة المبسطة
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from sqlalchemy import func
from database.session import session_scope
from database.models import Family, Beneficiary

# ==================== دوال الأسرة ====================

def show_families_simple():
    """عرض الأسر - مبسط"""
    st.subheader("🏠 قائمة الأسر")
    
    with session_scope() as session:
        families = session.query(Family).all()
        
        if not families:
            st.info("لا توجد أسر")
            return
        
        for family in families:
            with st.expander(f"{family.family_name} 📞 {family.phone or 'بدون هاتف'}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**الكود:** {family.family_code}")
                    st.write(f"**العنوان:** {family.address or 'بدون عنوان'}")
                    st.write(f"**المدينة:** {family.city or 'بدون مدينة'}")
                
                with col2:
                    st.write(f"**عدد المستفيدين:** {len(family.beneficiaries)}")
                    st.write(f"**الحالة:** {family.family_status or 'غير محدد'}")
                    st.write(f"**تاريخ التسجيل:** {family.registration_date}")
                
                # زر التعديل السريع
                if st.button(f"✏️ تعديل {family.family_name}", key=f"edit_{family.id}"):
                    st.session_state.edit_family_id = family.id
                    st.rerun()

def edit_family_simple(family_id: int):
    """تعديل أسرة - فعال"""
    st.subheader("✏️ تعديل أسرة")
    
    with session_scope() as session:
        family = session.query(Family).filter(Family.id == family_id).first()
        
        if not family:
            st.error("الأسرة غير موجودة")
            return
        
        # النموذج
        with st.form(f"edit_family_form_{family_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_name = st.text_input("اسم الأسرة", value=family.family_name or "")
                new_phone = st.text_input("الهاتف", value=family.phone or "")
                new_code = st.text_input("كود الأسرة", value=family.family_code or "")
            
            with col2:
                new_address = st.text_area("العنوان", value=family.address or "", height=100)
                new_city = st.text_input("المدينة", value=family.city or "")
                new_status = st.selectbox(
                    "حالة الأسرة",
                    ["", "فقيرة", "متوسطة", "ميسورة", "متعسرة"],
                    index=["", "فقيرة", "متوسطة", "ميسورة", "متعسرة"].index(
                        family.family_status
                    ) if family.family_status in ["", "فقيرة", "متوسطة", "ميسورة", "متعسرة"] else 0
                )
            
            col_submit, col_cancel = st.columns(2)
            with col_submit:
                submitted = st.form_submit_button("💾 حفظ", use_container_width=True)
            with col_cancel:
                if st.form_submit_button("❌ إلغاء", use_container_width=True):
                    if 'edit_family_id' in st.session_state:
                        del st.session_state.edit_family_id
                    st.rerun()
            
            if submitted:
                try:
                    # التحديث
                    family.family_name = new_name
                    family.phone = new_phone
                    family.family_code = new_code
                    family.address = new_address
                    family.city = new_city
                    family.family_status = new_status if new_status else None
                    family.updated_at = datetime.now()
                    
                    session.commit()
                    
                    st.success(f"✅ تم تحديث {new_name}")
                    
                    # مسح حالة التعديل
                    if 'edit_family_id' in st.session_state:
                        del st.session_state.edit_family_id
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"خطأ: {str(e)}")

def add_family_simple():
    """إضافة أسرة جديدة - مبسطة"""
    st.subheader("➕ إضافة أسرة جديدة")
    
    with st.form("add_family_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            family_code = st.text_input("كود الأسرة *", max_chars=20)
            family_name = st.text_input("اسم الأسرة *", max_chars=100)
            phone = st.text_input("الهاتف *", max_chars=15)
        
        with col2:
            address = st.text_area("العنوان *", height=100)
            city = st.text_input("المدينة", max_chars=50)
            status = st.selectbox("حالة الأسرة", ["", "فقيرة", "متوسطة", "ميسورة"])
        
        submitted = st.form_submit_button("➕ إضافة الأسرة")
        
        if submitted:
            if not all([family_code, family_name, phone, address]):
                st.error("يرجى ملء الحقول المطلوبة (*)")
                return
            
            try:
                with session_scope() as session:
                    # التحقق من عدم تكرار الكود
                    existing = session.query(Family).filter(Family.family_code == family_code).first()
                    if existing:
                        st.error("كود الأسرة موجود مسبقاً")
                        return
                    
                    new_family = Family(
                        family_code=family_code,
                        family_name=family_name,
                        phone=phone,
                        address=address,
                        city=city or None,
                        family_status=status if status else None,
                        registration_date=date.today()
                    )
                    
                    session.add(new_family)
                    session.commit()
                    
                    st.success(f"✅ تمت إضافة أسرة {family_name}")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

# ==================== دوال المستفيدين ====================

def show_beneficiaries_simple():
    """عرض المستفيدين - مبسط"""
    st.subheader("👥 قائمة المستفيدين")
    
    with session_scope() as session:
        beneficiaries = session.query(Beneficiary).limit(50).all()
        
        if not beneficiaries:
            st.info("لا توجد مستفيدين")
            return
        
        for beneficiary in beneficiaries:
            st.write(f"**{beneficiary.full_name_ar}** - 📞 {beneficiary.phone or 'بدون'}")

def add_beneficiary_simple():
    """إضافة مستفيد - مبسط"""
    st.subheader("👤 إضافة مستفيد جديد")
    
    # الحصول على الأسر
    with session_scope() as session:
        families = session.query(Family).all()
        family_options = {f.family_name: f.id for f in families}
    
    with st.form("add_beneficiary_form"):
        full_name_ar = st.text_input("الاسم بالعربية *", max_chars=100)
        national_id = st.text_input("الرقم القومي", max_chars=14)
        phone = st.text_input("الهاتف", max_chars=15)
        
        if family_options:
            selected_family = st.selectbox("الأسرة *", list(family_options.keys()))
            family_id = family_options[selected_family]
        else:
            st.warning("يجب إضافة أسرة أولاً")
            family_id = None
        
        submitted = st.form_submit_button("➕ إضافة المستفيد")
        
        if submitted:
            if not full_name_ar or not family_id:
                st.error("يرجى ملء الحقول المطلوبة (*)")
                return
            
            try:
                with session_scope() as session:
                    new_beneficiary = Beneficiary(
                        full_name_ar=full_name_ar,
                        national_id=national_id or None,
                        phone=phone or None,
                        family_id=family_id,
                        registration_date=date.today(),
                        status='active'
                    )
                    
                    session.add(new_beneficiary)
                    session.commit()
                    
                    st.success(f"✅ تمت إضافة {full_name_ar}")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"خطأ: {str(e)}")

# ==================== الواجهة الرئيسية ====================

def show_beneficiaries(user_data=None):
    """
    الواجهة الرئيسية - النسخة النهائية المبسطة
    """
    st.title("👨‍👩‍👧‍👦 إدارة المستفيدين والأسر")
    
    # التحقق من حالة التعديل
    if 'edit_family_id' in st.session_state:
        edit_family_simple(st.session_state.edit_family_id)
        return
    
    # علامات التبويب الرئيسية
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 الأسر",
        "👥 المستفيدين", 
        "➕ أسرة جديدة",
        "👤 مستفيد جديد"
    ])
    
    with tab1:
        show_families_simple()
    
    with tab2:
        show_beneficiaries_simple()
    
    with tab3:
        add_family_simple()
    
    with tab4:
        add_beneficiary_simple()

# ==================== التشغيل المباشر ====================

if __name__ == "__main__":
    show_beneficiaries()