# app.py - النسخة الأساسية
import streamlit as st
from auth.authentication import login, logout, is_authenticated, get_current_user
from modules import show_dashboard, show_beneficiaries
from modules.activities import show_activities_main
from modules.donations import show_donations_main as show_donations

# إعدادات الصفحة
st.set_page_config(
    page_title="نظام إدارة الجمعية الخيرية",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق تخصيصات CSS
def apply_custom_css():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #2E86C1;
        padding: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    .success-box {
        background-color: #D5F4E6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-right: 5px solid #28B463;
    }
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()


def main_page():
    """الصفحة الرئيسية"""
    st.title("🕌 نظام إدارة الجمعية الخيرية")
    st.markdown("---")
    
    # التحقق من وجود جلسة
    if 'session_token' in st.session_state and st.session_state.session_token:
        user_data = get_current_user(st.session_state.session_token)
        if user_data:
            show_authenticated_ui(user_data)
            return
    
    # عرض واجهة تسجيل الدخول
    show_login_ui()

def show_login_ui():
    """عرض واجهة تسجيل الدخول"""
    st.subheader("تسجيل الدخول")
    
    with st.form("login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        
        submitted = st.form_submit_button("دخول", type="primary", use_container_width=True)
        
        if submitted:
            # هنا القيم ستكون صحيحة!
            st.write("Username:", username)
            st.write("Password:", password)
            
            if not username or not password:
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور")
                return
            
            result = login(username, password)
            
            if result["success"]:
                st.session_state.session_token = result["session_token"]
                st.session_state.user_data = result["user"]
                st.success(f"مرحباً {result['user']['full_name']}!")
                st.rerun()
            else:
                st.error(result["message"])
    
    # عرض معلومات المساعدة خارج النموذج
    st.info("""
    **بيانات الدخول الافتراضية:**
    
    👑 **مدير النظام**
    - المستخدم: admin
    - كلمة المرور: admin123
    
    📊 **مشرف**
    - المستخدم: supervisor
    - كلمة المرور: supervisor123
    
    👨‍💼 **موظف**
    - المستخدم: employee1
    - كلمة المرور: employee123
    """)

    
def show_authenticated_ui(user_data):
    """عرض الواجهة بعد تسجيل الدخول"""
    
    # القائمة الجانبية
    with st.sidebar:
        st.title(f"مرحباً، {user_data['full_name']}")
        st.caption(f"👤 {user_data['role']}")
        st.markdown("---")
        
        # بناء القائمة حسب الدور
        menu_items = []
        
        menu_items.append("🏠 لوحة التحكم")
        menu_items.append("👥 المستفيدون")
        menu_items.append("📅 الأنشطة")
        menu_items.append("💰 التبرعات")
        menu_items.append("📊 التقارير")
        
        if user_data['role'] in ['admin', 'supervisor']:
            menu_items.append("👨‍💼 الموظفون")
            menu_items.append("🏢 إدارة الأسر")  # تغيير الاسم لتكون أكثر وضوحاً
        
        if user_data['role'] == 'admin':
            menu_items.append("⚙️ الإعدادات")
        
        selected = st.selectbox(
            "القائمة الرئيسية",
            menu_items,
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        if st.button("🚪 تسجيل الخروج", use_container_width=True, type="secondary"):
            # تسجيل الخروج من النظام
            if 'session_token' in st.session_state:
                logout_result = logout(st.session_state.session_token)
                if logout_result['success']:
                    st.success("✅ تم تسجيل الخروج بنجاح")
                else:
                    st.error(f"❌ {logout_result['message']}")
            
            # مسح بيانات الجلسة
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            st.rerun()
    
    # عرض المحتوى حسب الاختيار
    if selected == "🏠 لوحة التحكم":
        show_dashboard(user_data)
    elif selected == "👥 المستفيدون":
        show_beneficiaries(user_data)
    elif selected == "📅 الأنشطة":
        #st.info("🚧 صفحة الأنشطة قيد التطوير")
        show_activities_main(user_data)
    elif selected == "💰 التبرعات":
        # st.info("🚧 صفحة التبرعات قيد التطوير")
        show_donations(user_data)
    elif selected == "📊 التقارير":
        st.info("🚧 صفحة التقارير قيد التطوير")
        # show_reports(user_data)
    elif selected == "👨‍💼 الموظفون" and user_data['role'] in ['admin', 'supervisor']:
        st.info("🚧 صفحة إدارة الموظفين قيد التطوير")
    elif selected == "🏢 إدارة الأسر" and user_data['role'] in ['admin', 'supervisor']:
        # يمكنك إما:
        # 1. استدعاء show_beneficiaries مع معامل إضافي
        # 2. إنشاء صفحة منفصلة لإدارة الأسر
        # سأستخدم حالياً نفس صفحة المستفيدين حيث تحتوي على إدارة الأسر
        show_beneficiaries(user_data)
    elif selected == "⚙️ الإعدادات" and user_data['role'] == 'admin':
        st.info("🚧 صفحة الإعدادات قيد التطوير")
    # ... وهكذا لباقي الصفحات

def show_dashboard(user_data):
    """عرض لوحة التحكم"""
    st.header("🏠 لوحة التحكم")
    st.write(f"مرحباً بك في نظام إدارة الجمعية، {user_data['full_name']}!")
    
    # إحصائيات سريعة
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 المستفيدون", "150")
    
    with col2:
        st.metric("📅 الأنشطة", "24")
    
    with col3:
        st.metric("💰 التبرعات", "₣45,320")
    
    with col4:
        st.metric("🏢 الأسر", "42")

# def show_beneficiaries(user_data):
#     """عرض صفحة المستفيدين"""
#     st.header("👥 إدارة المستفيدين")
#     st.write("هنا يمكنك إدارة بيانات المستفيدين والأسر")

# def show_activities(user_data):
#     """عرض صفحة الأنشطة"""
#     st.header("📅 إدارة الأنشطة")
#     st.write("هنا يمكنك إدارة الأنشطة والفعاليات")

if __name__ == "__main__":
    main_page()