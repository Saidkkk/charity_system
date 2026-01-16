# modules/dashboard.py - لوحة التحكم الرئيسية
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from database.session import session_scope
from database.models import (
    User, Activity, Beneficiary, Donation, Family,
    ActivityStatus, DonationStatus
)
from auth.authentication import get_current_user

def show_dashboard():
    """عرض لوحة التحكم"""
    
    user = get_current_user()
    
    # ========== الإحصائيات السريعة ==========
    
    st.markdown("### 📊 نظرة عامة على النظام")
    
    # الحصول على الإحصائيات
    with session_scope() as session:
        # إجمالي المستفيدين
        total_beneficiaries = session.query(Beneficiary).count()
        
        # إجمالي الأنشطة
        total_activities = session.query(Activity).count()
        
        # إجمالي التبرعات
        total_donations = session.query(Donation).filter(
            Donation.status == DonationStatus.VERIFIED
        ).count()
        
        # إجمالي الأسر
        total_families = session.query(Family).count()
        
        # الأنشطة النشطة
        active_activities = session.query(Activity).filter(
            Activity.status == ActivityStatus.IN_PROGRESS
        ).count()
        
        # التبرعات الشهرية
        start_of_month = date.today().replace(day=1)
        monthly_donations = session.query(Donation).filter(
            Donation.donation_date >= start_of_month,
            Donation.status == DonationStatus.VERIFIED
        ).count()
        
        # المستفيدين الجدد هذا الشهر
        new_beneficiaries = session.query(Beneficiary).filter(
            Beneficiary.registration_date >= start_of_month
        ).count()
        
        # الأنشطة المكتملة
        completed_activities = session.query(Activity).filter(
            Activity.status == ActivityStatus.COMPLETED
        ).count()
    
    # عرض البطاقات
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="👥 إجمالي المستفيدين",
            value=f"{total_beneficiaries:,}",
            delta=f"+{new_beneficiaries} جديد",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="📋 إجمالي الأنشطة",
            value=f"{total_activities:,}",
            delta=f"{completed_activities} مكتمل",
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="💰 إجمالي التبرعات",
            value=f"{total_donations:,}",
            delta=f"+{monthly_donations} شهرياً",
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            label="🏠 إجمالي الأسر",
            value=f"{total_families:,}",
            delta=f"{active_activities} نشط",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # ========== الرسوم البيانية ==========
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 توزيع الأنشطة")
        
        # بيانات الأنشطة حسب الحالة
        activity_data = {
            'الحالة': ['مخطط', 'جاري التنفيذ', 'مكتمل', 'ملغي'],
            'العدد': [
                session.query(Activity).filter_by(status=ActivityStatus.PLANNED).count(),
                session.query(Activity).filter_by(status=ActivityStatus.IN_PROGRESS).count(),
                session.query(Activity).filter_by(status=ActivityStatus.COMPLETED).count(),
                session.query(Activity).filter_by(status=ActivityStatus.CANCELLED).count()
            ]
        }
        
        df_activities = pd.DataFrame(activity_data)
        
        fig1 = px.pie(
            df_activities,
            values='العدد',
            names='الحالة',
            color_discrete_sequence=['#3498db', '#2ecc71', '#f39c12', '#e74c3c'],
            hole=0.4
        )
        
        fig1.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 توزيع المستفيدين")
        
        # بيانات المستفيدين حسب المدينة
        with session_scope() as session:
            beneficiaries_by_city = session.query(
                Beneficiary.city,
                Beneficiary.gender
            ).filter(Beneficiary.city.isnot(None)).all()
        
        if beneficiaries_by_city:
            cities = [b[0] for b in beneficiaries_by_city if b[0]]
            gender_counts = {'M': 0, 'F': 0}
            
            for _, gender in beneficiaries_by_city:
                if gender in gender_counts:
                    gender_counts[gender] += 1
            
            gender_data = {
                'النوع': ['ذكور', 'إناث'],
                'العدد': [gender_counts['M'], gender_counts['F']]
            }
            
            df_gender = pd.DataFrame(gender_data)
            
            fig2 = px.bar(
                df_gender,
                x='النوع',
                y='العدد',
                color='النوع',
                color_discrete_map={'ذكور': '#3498db', 'إناث': '#e74c3c'},
                text='العدد'
            )
            
            fig2.update_layout(
                showlegend=False,
                yaxis_title="عدد المستفيدين",
                xaxis_title=""
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("لا توجد بيانات كافية لعرض التوزيع")
    
    st.markdown("---")
    
    # ========== آخر الأنشطة ==========
    
    st.markdown("#### 📝 آخر الأنشطة")
    
    with session_scope() as session:
        recent_activities = session.query(Activity).order_by(
            Activity.created_at.desc()
        ).limit(5).all()
    
    if recent_activities:
        activities_data = []
        for activity in recent_activities:
            status_ar = {
                'planned': 'مخطط',
                'in_progress': 'جاري التنفيذ',
                'completed': 'مكتمل',
                'cancelled': 'ملغي'
            }.get(activity.status.value, activity.status.value)
            
            activities_data.append({
                'النشاط': activity.title,
                'التاريخ': activity.start_date.strftime('%Y-%m-%d'),
                'الحالة': status_ar,
                'الموقع': activity.location[:30] + '...' if activity.location and len(activity.location) > 30 else activity.location or 'غير محدد'
            })
        
        df_recent = pd.DataFrame(activities_data)
        st.dataframe(df_recent, use_container_width=True, hide_index=True)
    else:
        st.info("لا توجد أنشطة مسجلة بعد")
    
    # ========== الوصول السريع ==========
    
    st.markdown("---")
    st.markdown("#### 🚀 الوصول السريع")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ إضافة نشاط جديد", use_container_width=True):
            st.session_state['current_page'] = 'activities'
            st.rerun()
    
    with col2:
        if st.button("👥 إضافة مستفيد جديد", use_container_width=True):
            st.session_state['current_page'] = 'beneficiaries'
            st.rerun()
    
    with col3:
        if st.button("💰 تسجيل تبرع جديد", use_container_width=True):
            st.session_state['current_page'] = 'donations'
            st.rerun()
    
    with col4:
        if st.button("📊 عرض التقارير", use_container_width=True):
            st.session_state['current_page'] = 'reports'
            st.rerun()
    
    # ========== معلومات النظام ==========
    
    with st.expander("ℹ️ معلومات النظام", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**معلومات المستخدم:**")
            st.write(f"- **الاسم:** {user['full_name']}")
            st.write(f"- **الدور:** {user['role']}")
            st.write(f"- **اسم المستخدم:** {user['username']}")
            
            # آخر دخول
            with session_scope() as session:
                user_obj = session.query(User).filter_by(id=user['id']).first()
                if user_obj and user_obj.last_login:
                    st.write(f"- **آخر دخول:** {user_obj.last_login.strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            st.markdown("**إحصائيات النظام:**")
            st.write(f"- **عدد الجداول:** 18 جدول")
            st.write(f"- **إصدار النظام:** 1.0.0")
            st.write(f"- **تاريخ التشغيل:** {datetime.now().strftime('%Y-%m-%d')}")
            st.write(f"- **الوقت الحالي:** {datetime.now().strftime('%H:%M:%S')}")