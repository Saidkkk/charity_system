# modules/donations.py
"""
نظام إدارة التبرعات - النسخة المبسطة والكفؤة
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from sqlalchemy import func
from database.session import session_scope
from database.models import Donation, Donor, DonationItem, Beneficiary, DonationAllocation

# إعدادات النظام
SYSTEM_CURRENCY = "EGP"  # جنيه مصري
CURRENCY_NAME = "جنيه"   # اسم العملة بالعربية

def show_donations(user_data=None):
    """الواجهة الرئيسية للتبرعات"""
    st.title("💰 إدارة التبرعات")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 قائمة التبرعات",
        "➕ تبرع جديد",
        "👤 إدارة المتبرعين",
        "📊 إحصائيات"
    ])
    
    with tab1:
        _show_donations_list(user_data)
    
    with tab2:
        _add_new_donation(user_data)
    
    with tab3:
        _manage_donors(user_data)
    
    with tab4:
        _show_donation_statistics(user_data)

def _show_donations_list(user_data=None):
    """عرض قائمة التبرعات"""
    st.subheader("📋 قائمة التبرعات")
    
    # فلترة التبرعات
    col1, col2, col3 = st.columns(3)
    
    with col1:
        type_filter = st.selectbox(
            "فلترة بالنوع",
            ["الكل", "cash", "in_kind", "service"],
            format_func=lambda x: {
                "الكل": "الكل",
                "cash": "نقدي",
                "in_kind": "عين",
                "service": "خدمة"
            }.get(x, x),
            key="donation_type_filter"
        )
    
    with col2:
        status_filter = st.selectbox(
            "فلترة بالحالة",
            ["الكل", "pending", "received", "verified", "cancelled"],
            format_func=lambda x: {
                "الكل": "الكل",
                "pending": "قيد الانتظار",
                "received": "مستلم",
                "verified": "مؤكد",
                "cancelled": "ملغي"
            }.get(x, x),
            key="donation_status_filter"
        )
    
    with col3:
        date_filter = st.selectbox(
            "فلترة بالتاريخ",
            ["الكل", "هذا الشهر", "الأسبوع الحالي", "اليوم"],
            key="donation_date_filter"
        )
    
    try:
        with session_scope() as session:
            # بناء الاستعلام
            query = session.query(Donation)
            
            # تطبيق الفلاتر
            if type_filter != "الكل":
                query = query.filter(Donation.donation_type == type_filter)
            
            if status_filter != "الكل":
                query = query.filter(Donation.status == status_filter)
            
            if date_filter != "الكل":
                today = date.today()
                if date_filter == "هذا الشهر":
                    first_day = date(today.year, today.month, 1)
                    last_day = date(today.year, today.month + 1, 1) - pd.Timedelta(days=1)
                    query = query.filter(Donation.donation_date.between(first_day, last_day))
                elif date_filter == "الأسبوع الحالي":
                    start_week = today - pd.Timedelta(days=today.weekday())
                    end_week = start_week + pd.Timedelta(days=6)
                    query = query.filter(Donation.donation_date.between(start_week, end_week))
                elif date_filter == "اليوم":
                    query = query.filter(Donation.donation_date == today)
            
            # جلب البيانات
            donations = query.order_by(Donation.donation_date.desc()).limit(100).all()
            
            if not donations:
                st.info("📭 لا توجد تبرعات مطابقة للبحث")
                return
            
            # عرض البيانات
            for donation in donations:
                with st.expander(f"تبرع #{donation.id} - {donation.donation_date.strftime('%Y-%m-%d')}"):
                    _display_donation_details(donation, session, user_data)
    
    except Exception as e:
        st.error(f"حدث خطأ في جلب البيانات: {str(e)}")

def _display_donation_details(donation: Donation, session, user_data=None):
    """عرض تفاصيل التبرع"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**رقم التبرع:** {donation.donation_number}")
        st.write(f"**المتبرع:** {donation.donor.full_name if donation.donor else 'غير محدد'}")
        st.write(f"**النوع:** {_get_donation_type_ar(donation.donation_type)}")
        st.write(f"**التاريخ:** {donation.donation_date.strftime('%Y-%m-%d')}")
    
    with col2:
        if donation.amount:
            st.write(f"**المبلغ:** {donation.amount:,.2f} {donation.currency}")
        
        st.write(f"**الحالة:** {_get_donation_status_ar(donation.status)}")
        st.write(f"**طريقة الدفع:** {_get_payment_method_ar(donation.payment_method)}")
        
        if donation.purpose:
            st.write(f"**الغرض:** {donation.purpose}")
    
    # عرض البنود العينية إن وجدت
    if donation.items:
        st.markdown("### 🎁 البنود العينية")
        items_data = []
        for item in donation.items:
            items_data.append({
                "البند": item.item_name,
                "الكمية": item.quantity,
                "الوحدة": item.unit,
                "القيمة": f"{item.total_value:,.2f}" if item.total_value else "غير محدد"
            })
        
        st.dataframe(pd.DataFrame(items_data), hide_index=True)
    
    # خيارات التعديل
    if user_data and user_data.get('role') in ['admin', 'supervisor']:
        st.markdown("---")
        col_edit, col_delete = st.columns(2)
        
        with col_edit:
            if st.button(f"✏️ تعديل التبرع", key=f"edit_donation_{donation.id}"):
                st.session_state.edit_donation_id = donation.id
                st.rerun()
        
        with col_delete:
            if st.button(f"🗑️ حذف التبرع", key=f"delete_donation_{donation.id}", type="secondary"):
                # استخدام timestamp لمفتاح فريد
                import time
                confirm_suffix = str(int(time.time()))
                
                if _delete_donation(donation.id, session, confirm_suffix):
                    st.rerun()

def _add_new_donation(user_data=None):
    """إضافة تبرع جديد"""
    st.subheader("➕ تبرع جديد")
    
    with st.form("add_donation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            donation_type = st.selectbox(
                "نوع التبرع *",
                ["cash", "in_kind", "service"],
                format_func=lambda x: {
                    "cash": "نقدي",
                    "in_kind": "عين",
                    "service": "خدمة"
                }.get(x, x),
                key="donation_type_input"
            )
            
            amount = st.number_input(
                f"المبلغ ({CURRENCY_NAME})",
                min_value=0.0,
                value=0.0,
                step=100.0,
                key="donation_amount"
            )
            
            # اختيار المتبرع
            with session_scope() as session:
                donors = session.query(Donor).filter(Donor.status == 'active').all()
                donor_options = ["جديد"] + [f"{d.full_name or d.company_name} ({d.phone or 'بدون هاتف'})" for d in donors]
                
                selected_donor = st.selectbox(
                    "المتبرع *",
                    donor_options,
                    key="select_donor"
                )
            
        with col2:
            payment_method = st.selectbox(
                "طريقة الدفع",
                ["", "cash", "check", "bank_transfer", "credit_card"],
                format_func=lambda x: {
                    "": "اختر طريقة",
                    "cash": "نقد",
                    "check": "شيك",
                    "bank_transfer": "تحويل بنكي",
                    "credit_card": "بطاقة ائتمان"
                }.get(x, x),
                key="payment_method"
            )
            
            purpose = st.text_input("الغرض (اختياري)", key="donation_purpose")
            
            status = st.selectbox(
                "حالة التبرع",
                ["pending", "received", "verified"],
                format_func=lambda x: {
                    "pending": "قيد الانتظار",
                    "received": "مستلم",
                    "verified": "مؤكد"
                }.get(x, x),
                key="donation_status"
            )
        
        # إذا كان تبرعاً عينياً
        if donation_type == "in_kind":
            st.markdown("### 🎁 تفاصيل البنود العينية")
            
            col3, col4 = st.columns(2)
            with col3:
                item_name = st.text_input("اسم البند", key="item_name")
                quantity = st.number_input("الكمية", min_value=0.0, value=1.0, step=1.0, key="item_quantity")
            
            with col4:
                unit = st.text_input("الوحدة", value="قطعة", key="item_unit")
                unit_value = st.number_input(f"قيمة الوحدة ({CURRENCY_NAME})", min_value=0.0, value=0.0, key="item_unit_value")
        
        notes = st.text_area("ملاحظات (اختياري)", height=100, key="donation_notes")
        
        col_submit, col_clear = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("➕ إضافة التبرع", type="primary")
        with col_clear:
            if st.form_submit_button("🗑️ مسح النموذج", type="secondary"):
                st.rerun()
        
        if submitted:
            # التحقق من الحقول المطلوبة
            if not donation_type:
                st.error("⚠️ نوع التبرع مطلوب")
                return
            
            if donation_type == "cash" and amount <= 0:
                st.error("⚠️ المبلغ يجب أن يكون أكبر من صفر")
                return
            
            try:
                with session_scope() as session:
                    # معالجة المتبرع
                    donor_id = None
                    
                    if selected_donor != "جديد":
                        # البحث عن المتبرع المختار
                        donor_name = selected_donor.split("(")[0].strip()
                        donor = session.query(Donor).filter(
                            (Donor.full_name == donor_name) | 
                            (Donor.company_name == donor_name)
                        ).first()
                        
                        if donor:
                            donor_id = donor.id
                    else:
                        # إضافة متبرع جديد
                        st.info("سيتم إضافة المتبرع كمتبرع عام")
                    
                    # إنشاء رقم تبرع تلقائي
                    donation_number = f"DON-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                    
                    # إنشاء التبرع
                    new_donation = Donation(
                        donation_number=donation_number,
                        donation_type=donation_type,
                        donation_date=date.today(),
                        amount=amount if amount > 0 else None,
                        currency=SYSTEM_CURRENCY,
                        payment_method=payment_method if payment_method else None,
                        purpose=purpose or None,
                        status=status,
                        donor_id=donor_id,
                        notes=notes or None,
                        receipt_issued=False,
                        created_by=user_data.get('user_id') if user_data else None
                    )
                    
                    session.add(new_donation)
                    session.flush()
                    
                    # إضافة البنود العينية إذا كان تبرع عيني
                    if donation_type == "in_kind" and item_name:
                        total_value = quantity * unit_value if unit_value > 0 else None
                        
                        donation_item = DonationItem(
                            donation_id=new_donation.id,
                            item_name=item_name,
                            quantity=quantity,
                            unit=unit or None,
                            unit_value=unit_value if unit_value > 0 else None,
                            total_value=total_value
                        )
                        
                        session.add(donation_item)
                    
                    session.commit()
                    
                    st.success(f"✅ تمت إضافة التبرع برقم {donation_number}")
                    st.balloons()
                    
                    # عرض البيانات المضافة
                    with st.expander("عرض بيانات التبرع المضافة"):
                        st.json({
                            "رقم التبرع": donation_number,
                            "النوع": donation_type,
                            "المبلغ": f"{amount:,.2f} {CURRENCY_NAME}" if amount > 0 else "غير محدد",
                            "التاريخ": date.today().strftime("%Y-%m-%d"),
                            "الحالة": status
                        })
                    
            except Exception as e:
                st.error(f"❌ حدث خطأ أثناء الإضافة: {str(e)}")
                import traceback
                st.error(traceback.format_exc())

def _manage_donors(user_data=None):
    """إدارة المتبرعين"""
    st.subheader("👤 إدارة المتبرعين")
    
    if user_data and user_data.get('role') not in ['admin', 'supervisor']:
        st.error("⚠️ تحتاج إلى صلاحية مشرف أو مسؤول")
        return
    
    tab1, tab2 = st.tabs(["📋 قائمة المتبرعين", "➕ متبرع جديد"])
    
    with tab1:
        try:
            with session_scope() as session:
                donors = session.query(Donor).order_by(Donor.created_at.desc()).limit(100).all()
                
                if not donors:
                    st.info("📭 لا توجد متبرعين")
                    return
                
                for donor in donors:
                    with st.expander(f"{'👤' if donor.donor_type == 'individual' else '🏢'} {donor.full_name or donor.company_name}"):
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**النوع:** {_get_donor_type_ar(donor.donor_type)}")
                            st.write(f"**الكود:** {donor.donor_code or 'بدون'}")
                            st.write(f"**الهاتف:** {donor.phone or 'غير متوفر'}")
                            st.write(f"**البريد:** {donor.email or 'غير متوفر'}")
                            st.write(f"**المدينة:** {donor.city or 'غير محدد'}")
                            st.write(f"**الحالة:** {donor.status}")
                        
                        with col2:
                            if st.button(f"✏️", key=f"edit_donor_{donor.id}", help="تعديل"):
                                st.session_state.edit_donor_id = donor.id
                                st.rerun()

                        with col3:
                            if st.button(f"🗑️", key=f"delete_donor_{donor.id}", type="secondary", help="حذف"):
                                # استخدام timestamp لمفتاح فريد
                                import time
                                confirm_suffix = str(int(time.time()))
                                
                                if _delete_donor_with_confirm(donor.id, session, confirm_suffix):
                                    st.rerun()
                        st.markdown("---")
                                    
                        # عدد تبرعات المتبرع
                        donations_count = session.query(Donation).filter(
                            Donation.donor_id == donor.id
                        ).count()
                        
                        st.write(f"**عدد التبرعات:** {donations_count}")
                        
                        if donations_count > 0:
                            # إجمالي تبرعات المتبرع
                            total_donated = session.query(func.sum(Donation.amount)).filter(
                                Donation.donor_id == donor.id,
                                Donation.status.in_(['received', 'verified'])
                            ).scalar() or 0
                            
                            st.write(f"**إجمالي التبرعات:** {total_donated:,.2f} {CURRENCY_NAME}")
        
        except Exception as e:
            st.error(f"حدث خطأ: {str(e)}")
    
    with tab2:
        with st.form("add_donor_form"):
            donor_type = st.selectbox(
                "نوع المتبرع *",
                ["individual", "company", "organization"],
                format_func=lambda x: {
                    "individual": "فرد",
                    "company": "شركة",
                    "organization": "مؤسسة"
                }.get(x, x),
                key="donor_type_input"
            )
            
            if donor_type == "individual":
                full_name = st.text_input("الاسم الكامل *", max_chars=100, key="donor_full_name")
                national_id = st.text_input("الرقم القومي", max_chars=14, key="donor_national_id")
                company_name = None
                commercial_reg = None
            else:
                company_name = st.text_input("اسم الشركة/المؤسسة *", max_chars=200, key="donor_company_name")
                commercial_reg = st.text_input("السجل التجاري", max_chars=50, key="donor_commercial_reg")
                full_name = None
                national_id = None
            
            col1, col2 = st.columns(2)
            
            with col1:
                phone = st.text_input("رقم الهاتف *", max_chars=15, key="donor_phone")
                email = st.text_input("البريد الإلكتروني", max_chars=100, key="donor_email")
            
            with col2:
                address = st.text_area("العنوان", height=80, key="donor_address")
                city = st.text_input("المدينة", max_chars=50, key="donor_city")
            
            submitted = st.form_submit_button("➕ إضافة المتبرع")
            
            if submitted:
                # التحقق من الحقول المطلوبة
                if donor_type == "individual" and not full_name:
                    st.error("⚠️ الاسم الكامل مطلوب للأفراد")
                    return
                
                if donor_type != "individual" and not company_name:
                    st.error("⚠️ اسم الشركة/المؤسسة مطلوب")
                    return
                
                if not phone:
                    st.error("⚠️ رقم الهاتف مطلوب")
                    return
                
                try:
                    with session_scope() as session:
                        # إنشاء كود المتبرع
                        import secrets
                        donor_code = f"DNR-{secrets.token_hex(3).upper()}"
                        
                        new_donor = Donor(
                            donor_type=donor_type,
                            donor_code=donor_code,
                            full_name=full_name,
                            national_id=national_id or None,
                            company_name=company_name,
                            commercial_registration=commercial_reg or None,
                            phone=phone,
                            email=email or None,
                            address=address or None,
                            city=city or None,
                            status='active'
                        )
                        
                        session.add(new_donor)
                        session.commit()
                        
                        donor_name = full_name or company_name
                        st.success(f"✅ تمت إضافة المتبرع '{donor_name}'")
                        st.balloons()
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ حدث خطأ: {str(e)}")

def _edit_donor_form(donor_id: int, user_data=None):
    """تعديل بيانات متبرع"""
    st.subheader("✏️ تعديل بيانات متبرع")
    
    try:
        with session_scope() as session:
            donor = session.query(Donor).filter(Donor.id == donor_id).first()
            
            if not donor:
                st.error("المتبرع غير موجود")
                return
            
            with st.form(f"edit_donor_{donor_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if donor.donor_type == "individual":
                        new_name = st.text_input("الاسم الكامل", value=donor.full_name or "")
                        new_national_id = st.text_input("الرقم القومي", value=donor.national_id or "")
                    else:
                        new_company = st.text_input("اسم الشركة", value=donor.company_name or "")
                        new_commercial_reg = st.text_input("السجل التجاري", value=donor.commercial_registration or "")
                    
                    new_phone = st.text_input("رقم الهاتف", value=donor.phone or "")
                
                with col2:
                    new_email = st.text_input("البريد الإلكتروني", value=donor.email or "")
                    new_city = st.text_input("المدينة", value=donor.city or "")
                    
                    new_status = st.selectbox(
                        "الحالة",
                        ["active", "inactive"],
                        index=0 if donor.status == "active" else 1,
                        format_func=lambda x: "نشط" if x == "active" else "غير نشط"
                    )
                
                new_address = st.text_area("العنوان", value=donor.address or "", height=80)
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submitted = st.form_submit_button("💾 حفظ التغييرات")
                with col_cancel:
                    if st.form_submit_button("❌ إلغاء"):
                        if 'edit_donor_id' in st.session_state:
                            del st.session_state.edit_donor_id
                        st.rerun()
                
                if submitted:
                    try:
                        if donor.donor_type == "individual":
                            donor.full_name = new_name
                            donor.national_id = new_national_id if new_national_id else None
                        else:
                            donor.company_name = new_company
                            donor.commercial_registration = new_commercial_reg if new_commercial_reg else None
                        
                        donor.phone = new_phone
                        donor.email = new_email if new_email else None
                        donor.city = new_city if new_city else None
                        donor.address = new_address if new_address else None
                        donor.status = new_status
                        donor.updated_at = datetime.now()
                        
                        session.commit()
                        st.success("✅ تم تحديث بيانات المتبرع!")
                        
                        if 'edit_donor_id' in st.session_state:
                            del st.session_state.edit_donor_id
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ خطأ: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")

def _delete_donation(donation_id: int, session, confirm_key_suffix=""):
    """حذف تبرع مع تأكيد"""
    donation = session.query(Donation).filter(Donation.id == donation_id).first()
    
    if not donation:
        st.error("التبرع غير موجود")
        return False
    
    # مفتاح فريد للتأكيد
    confirm_key = f"confirm_delete_donation_{donation_id}_{confirm_key_suffix}"
    
    # إذا لم يتم التأكيد بعد
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    # إذا تم الضغط على حذف ولم يتم التأكيد بعد
    if not st.session_state[confirm_key]:
        st.warning(f"⚠️ **تأكيد الحذف**")
        st.write(f"هل أنت متأكد من حذف التبرع رقم **{donation.donation_number}**؟")
        st.write(f"**المتبرع:** {donation.donor.full_name if donation.donor else 'غير محدد'}")
        st.write(f"**المبلغ:** {donation.amount or 0} {donation.currency}")
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button(f"✅ نعم، أحذف", key=f"yes_delete_{donation_id}", 
                        type="primary", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()
        
        with col_cancel:
            if st.button(f"❌ إلغاء", key=f"cancel_delete_{donation_id}",
                        type="secondary", use_container_width=True):
                # مسح حالة التأكيد
                if confirm_key in st.session_state:
                    del st.session_state[confirm_key]
                st.info("تم إلغاء الحذف")
                return False
        
        return False  # لم يتم الحذف بعد
    
    # إذا تم التأكيد، ننفذ الحذف
    else:
        try:
            # التحقق من عدم وجود تخصيصات مرتبطة
            allocations_count = session.query(DonationAllocation).filter(
                DonationAllocation.donation_id == donation_id
            ).count()
            
            if allocations_count > 0:
                st.error(f"❌ لا يمكن حذف التبرع لأنه مرتبط بـ {allocations_count} تخصيص")
                # مسح حالة التأكيد
                if confirm_key in st.session_state:
                    del st.session_state[confirm_key]
                return False
            
            # التحقق من عدم وجود بنود عينية
            items_count = session.query(DonationItem).filter(
                DonationItem.donation_id == donation_id
            ).count()
            
            if items_count > 0:
                # حذف البنود العينية أولاً
                session.query(DonationItem).filter(
                    DonationItem.donation_id == donation_id
                ).delete()
            
            # حذف التبرع
            donation_number = donation.donation_number
            session.delete(donation)
            session.commit()
            
            st.success(f"✅ تم حذف التبرع رقم {donation_number}")
            
            # مسح حالة التأكيد
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            
            return True
            
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء الحذف: {str(e)}")
            # مسح حالة التأكيد
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            return False
        
def _delete_donor_with_confirm(donor_id: int, session, confirm_key_suffix=""):
    """حذف متبرع مع تأكيد"""
    donor = session.query(Donor).filter(Donor.id == donor_id).first()
    
    if not donor:
        st.error("المتبرع غير موجود")
        return False
    
    # مفتاح فريد للتأكيد
    confirm_key = f"confirm_delete_donor_{donor_id}_{confirm_key_suffix}"
    
    # إذا لم يتم التأكيد بعد
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False
    
    donor_name = donor.full_name or donor.company_name or "غير محدد"
    
    # إذا تم الضغط على حذف ولم يتم التأكيد بعد
    if not st.session_state[confirm_key]:
        st.warning(f"⚠️ **تأكيد حذف المتبرع**")
        st.write(f"هل أنت متأكد من حذف المتبرع: **{donor_name}**؟")
        st.write(f"**الكود:** {donor.donor_code}")
        st.write(f"**الهاتف:** {donor.phone}")
        
        # التحقق من وجود تبرعات مرتبطة
        donations_count = session.query(Donation).filter(
            Donation.donor_id == donor_id
        ).count()
        
        if donations_count > 0:
            st.error(f"❌ **تحذير:** هذا المتبرع لديه {donations_count} تبرع!")
            st.info("إذا حذفت المتبرع، ستظل التبرعات موجودة ولكن ستظهر كـ 'غير محدد'")
        
        col_confirm, col_cancel = st.columns(2)
        
        with col_confirm:
            if st.button(f"✅ نعم، أحذف", key=f"yes_del_donor_{donor_id}", 
                        type="primary", use_container_width=True):
                st.session_state[confirm_key] = True
                st.rerun()
        
        with col_cancel:
            if st.button(f"❌ إلغاء", key=f"cancel_del_donor_{donor_id}",
                        type="secondary", use_container_width=True):
                # مسح حالة التأكيد
                if confirm_key in st.session_state:
                    del st.session_state[confirm_key]
                st.info("تم إلغاء الحذف")
                return False
        
        return False  # لم يتم الحذف بعد
    
    # إذا تم التأكيد، ننفذ الحذف
    else:
        try:
            donor_name = donor.full_name or donor.company_name or "غير محدد"
            donor_code = donor.donor_code
            
            # حذف المتبرع
            session.delete(donor)
            session.commit()
            
            st.success(f"✅ تم حذف المتبرع {donor_name} ({donor_code})")
            
            # مسح حالة التأكيد
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            
            return True
            
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء حذف المتبرع: {str(e)}")
            # مسح حالة التأكيد
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            return False
                
def _edit_donation_form(donation_id: int, user_data=None):
    """تعديل تبرع"""
    st.subheader("✏️ تعديل تبرع")
    
    try:
        with session_scope() as session:
            donation = session.query(Donation).filter(Donation.id == donation_id).first()
            
            if not donation:
                st.error("التبرع غير موجود")
                return
            
            with st.form(f"edit_donation_{donation_id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_status = st.selectbox(
                        "حالة التبرع",
                        ["pending", "received", "verified", "cancelled"],
                        index=["pending", "received", "verified", "cancelled"].index(
                            donation.status
                        ) if donation.status in ["pending", "received", "verified", "cancelled"] else 0,
                        format_func=lambda x: {
                            "pending": "قيد الانتظار",
                            "received": "مستلم",
                            "verified": "مؤكد",
                            "cancelled": "ملغي"
                        }.get(x, x)
                    )
                    
                    if donation.donation_type == "cash":
                        new_amount = st.number_input(
                            f"المبلغ ({CURRENCY_NAME})",
                            min_value=0.0,
                            value=float(donation.amount) if donation.amount else 0.0,
                            step=100.0
                        )
                
                with col2:
                    new_purpose = st.text_input("الغرض", value=donation.purpose or "")
                    
                    new_payment_method = st.selectbox(
                        "طريقة الدفع",
                        ["", "cash", "check", "bank_transfer", "credit_card"],
                        index=["", "cash", "check", "bank_transfer", "credit_card"].index(
                            donation.payment_method
                        ) if donation.payment_method in ["", "cash", "check", "bank_transfer", "credit_card"] else 0,
                        format_func=lambda x: {
                            "": "اختر طريقة",
                            "cash": "نقد",
                            "check": "شيك",
                            "bank_transfer": "تحويل بنكي",
                            "credit_card": "بطاقة ائتمان"
                        }.get(x, x)
                    )
                
                new_notes = st.text_area("ملاحظات", value=donation.notes or "", height=100)
                
                col_submit, col_cancel, col_delete = st.columns([2, 1, 1])
                
                with col_submit:
                    submitted = st.form_submit_button("💾 حفظ التغييرات")
                
                with col_cancel:
                    if st.form_submit_button("❌ إلغاء"):
                        if 'edit_donation_id' in st.session_state:
                            del st.session_state.edit_donation_id
                        st.rerun()
                                
                with col_delete:
                    if st.form_submit_button("🗑️ حذف", type="secondary"):
                        # استخدام timestamp لمفتاح فريد
                        import time
                        confirm_suffix = str(int(time.time()))
                        
                        if _delete_donation(donation_id, session, confirm_suffix):
                            if 'edit_donation_id' in st.session_state:
                                del st.session_state.edit_donation_id
                            st.rerun()

                if submitted:
                    try:
                        donation.status = new_status
                        donation.purpose = new_purpose if new_purpose else None
                        donation.payment_method = new_payment_method if new_payment_method else None
                        donation.notes = new_notes if new_notes else None
                        
                        if donation.donation_type == "cash":
                            donation.amount = new_amount if new_amount > 0 else None
                        
                        donation.updated_at = datetime.now()
                        
                        session.commit()
                        st.success("✅ تم تحديث التبرع!")
                        
                        if 'edit_donation_id' in st.session_state:
                            del st.session_state.edit_donation_id
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ خطأ: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")        

def _show_donation_statistics(user_data=None):
    """عرض إحصائيات التبرعات"""
    st.subheader("📊 إحصائيات التبرعات")
    
    try:
        with session_scope() as session:
            # إحصائيات أساسية
            total_donations = session.query(func.sum(Donation.amount)).filter(
                Donation.status.in_(['received', 'verified'])
            ).scalar() or 0
            
            donations_count = session.query(Donation).count()
            donors_count = session.query(Donor).filter(Donor.status == 'active').count()
            
            # مؤشرات الأداء
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(f"إجمالي التبرعات ({CURRENCY_NAME})", f"{total_donations:,.2f}")
            
            with col2:
                st.metric("عدد التبرعات", donations_count)
            
            with col3:
                st.metric("عدد المتبرعين النشطين", donors_count)
            
            st.markdown("---")
            
            # توزيع التبرعات حسب النوع
            st.subheader("📈 توزيع التبرعات حسب النوع")
            
            type_counts = session.query(
                Donation.donation_type,
                func.count(Donation.id),
                func.sum(Donation.amount)
            ).group_by(Donation.donation_type).all()
            
            if type_counts:
                type_data = []
                for tc in type_counts:
                    type_data.append({
                        "النوع": _get_donation_type_ar(tc[0]),
                        "العدد": tc[1],
                        f"الإجمالي ({CURRENCY_NAME})": f"{tc[2] or 0:,.2f}"
                    })
                
                st.dataframe(
                    pd.DataFrame(type_data),
                    use_container_width=True,
                    hide_index=True
                )
            
            # أحدث التبرعات
            st.subheader("🆕 أحدث التبرعات")
            
            recent_donations = session.query(Donation).order_by(
                Donation.donation_date.desc()
            ).limit(10).all()
            
            if recent_donations:
                recent_data = []
                for donation in recent_donations:
                    donor_name = donation.donor.full_name if donation.donor else "غير محدد"
                    recent_data.append({
                        "التاريخ": donation.donation_date.strftime("%Y-%m-%d"),
                        "المتبرع": donor_name,
                        "النوع": _get_donation_type_ar(donation.donation_type),
                        f"المبلغ ({CURRENCY_NAME})": f"{donation.amount or 0:,.2f}",
                        "الحالة": _get_donation_status_ar(donation.status)
                    })
                
                st.dataframe(
                    pd.DataFrame(recent_data),
                    use_container_width=True,
                    hide_index=True
                )
            
            # أهم المتبرعين
            st.subheader("🏆 أهم المتبرعين")
            
            top_donors = session.query(
                Donor.full_name,
                Donor.company_name,
                func.sum(Donation.amount),
                func.count(Donation.id)
            ).join(Donation).group_by(Donor.id).order_by(
                func.sum(Donation.amount).desc()
            ).limit(5).all()
            
            if top_donors:
                donor_data = []
                for donor in top_donors:
                    donor_name = donor[0] or donor[1] or "غير محدد"
                    donor_data.append({
                        "المتبرع": donor_name,
                        f"إجمالي التبرعات ({CURRENCY_NAME})": f"{donor[2] or 0:,.2f}",
                        "عدد التبرعات": donor[3]
                    })
                
                st.dataframe(
                    pd.DataFrame(donor_data),
                    use_container_width=True,
                    hide_index=True
                )
    
    except Exception as e:
        st.error(f"حدث خطأ في جلب الإحصائيات: {str(e)}")

# ==================== دوال مساعدة ====================

def _get_donation_type_ar(donation_type):
    """تحويل نوع التبرع للعربية"""
    type_map = {
        'cash': 'نقدي',
        'in_kind': 'عين',
        'service': 'خدمة'
    }
    return type_map.get(donation_type, donation_type)

def _get_donation_status_ar(status):
    """تحويل حالة التبرع للعربية"""
    status_map = {
        'pending': 'قيد الانتظار',
        'received': 'مستلم',
        'verified': 'مؤكد',
        'cancelled': 'ملغي'
    }
    return status_map.get(status, status)

def _get_payment_method_ar(method):
    """تحويل طريقة الدفع للعربية"""
    method_map = {
        'cash': 'نقد',
        'check': 'شيك',
        'bank_transfer': 'تحويل بنكي',
        'credit_card': 'بطاقة ائتمان'
    }
    return method_map.get(method, method or 'غير محدد')

def _get_donor_type_ar(donor_type):
    """تحويل نوع المتبرع للعربية"""
    type_map = {
        'individual': 'فرد',
        'company': 'شركة',
        'organization': 'مؤسسة'
    }
    return type_map.get(donor_type, donor_type)

# ==================== التشغيل الرئيسي ====================

def show_donations_main(user_data=None):
    """
    الدالة الرئيسية مع معالجة الحالات
    """
    # التحقق من حالة تعديل التبرع
    if 'edit_donation_id' in st.session_state:
        _edit_donation_form(st.session_state.edit_donation_id, user_data)
        return
    
    # التحقق من حالة تعديل المتبرع
    if 'edit_donor_id' in st.session_state:
        _edit_donor_form(st.session_state.edit_donor_id, user_data)
        return
    
    # العرض العادي
    show_donations(user_data)
    


# ==================== التشغيل المباشر ====================

if __name__ == "__main__":
    show_donations_main()