# database/models.py - النماذج الجديدة مع نظام المستخدمين
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean,
    Numeric, ForeignKey, JSON, Enum, Table, LargeBinary,
    CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

Base = declarative_base()

# ============== أنواع التعداد (Enums) ==============

class UserRole(str, enum.Enum):
    """أدوار المستخدمين"""
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    EMPLOYEE = "employee"
    VIEWER = "viewer"

class UserStatus(str, enum.Enum):
    """حالة المستخدم"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"

class ActivityStatus(str, enum.Enum):
    """حالة النشاط"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class DonationStatus(str, enum.Enum):
    """حالة التبرع"""
    PENDING = "pending"
    RECEIVED = "received"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

# ============== نظام المستخدمين والمصادقة ==============

class User(Base):
    """مستخدمي النظام"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    
    # معلومات الدخول
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # المعلومات الشخصية
    full_name = Column(String(100), nullable=False)
    phone = Column(String(15))
    #phone2 = Column(String(15))
    
    # الدور والصلاحيات
    #role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    role = Column(String(20), nullable=False, default='employee')  # ← غيّر هنا
    #status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    status = Column(String(20), nullable=False, default='active')  # ← وغيّر هنا
        
    # معلومات إضافية
    department = Column(String(50))
    position = Column(String(50))
    employee_id = Column(String(20), unique=True)
    
    # إعدادات المستخدم
    language = Column(String(10), default="ar")
    timezone = Column(String(50), default="Africa/Cairo")
    theme = Column(String(20), default="light")
    
    # التواريخ
    last_login = Column(DateTime)
    password_changed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("UserLog", back_populates="user", cascade="all, delete-orphan")
    
    # قيود
    __table_args__ = (
        Index('ix_users_role_status', 'role', 'status'),
        CheckConstraint("role IN ('admin', 'supervisor', 'employee', 'viewer')", name='ck_user_role'),
        CheckConstraint("status IN ('active', 'inactive', 'suspended', 'pending')", name='ck_user_status'),
    )


class UserSession(Base):
    """جلسات المستخدمين"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    # معلومات الجلسة
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_info = Column(JSON)
    
    # حالة الجلسة
    is_active = Column(Boolean, default=True)
    
    # التواريخ
    login_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, onupdate=func.now())
    expires_at = Column(DateTime)
    logout_at = Column(DateTime)
    
    # علاقات
    user = relationship("User", back_populates="sessions")
    
    # قيود
    __table_args__ = (
        Index('ix_user_sessions_user_active', 'user_id', 'is_active'),
        Index('ix_user_sessions_token', 'session_token'),
    )


class UserLog(Base):
    """سجلات أنشطة المستخدمين"""
    __tablename__ = 'user_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    
    # معلومات السجل
    action = Column(String(50), nullable=False)  # login, logout, create, update, delete
    module = Column(String(50))  # activities, beneficiaries, donations, etc.
    record_id = Column(Integer)  # معرف السجل المتأثر
    description = Column(Text)
    
    # بيانات إضافية
    ip_address = Column(String(45))
    user_agent = Column(Text)
    changes = Column(JSON)  # التغييرات التي تمت
    
    created_at = Column(DateTime, server_default=func.now())
    
    # علاقات
    user = relationship("User", back_populates="logs")
    
    # قيود وفهارس
    __table_args__ = (
        Index('ix_user_logs_user_action', 'user_id', 'action'),
        Index('ix_user_logs_module', 'module'),
        Index('ix_user_logs_created', 'created_at'),
    )

# ============== نظام المستفيدين والأسر ==============

class Family(Base):
    """جدول الأسر"""
    __tablename__ = 'families'
    
    id = Column(Integer, primary_key=True)
    
    # معلومات الأسرة
    family_code = Column(String(20), unique=True, nullable=False, index=True)
    family_name = Column(String(100), nullable=False)
    
    # العنوان
    address = Column(Text, nullable=False)
    city = Column(String(50))
    region = Column(String(50))
    
    # الاتصال
    phone = Column(String(15))
    phone2 = Column(String(15))
    
    # الحالة الاجتماعية للأسرة
    family_status = Column(String(30))  # فقيرة، متوسطة، ميسورة
    housing_type = Column(String(30))  # ملك، إيجار
    rooms_count = Column(Integer)
    dependents_count = Column(Integer)
    
    # الدخل
    total_monthly_income = Column(Numeric(10, 2))
    income_source = Column(Text)
    
    # التسجيلات
    registration_date = Column(Date, server_default=func.current_date())
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    created_by= Column(Integer, ForeignKey('users.id'))
    
    # علاقات
    beneficiaries = relationship("Beneficiary", back_populates="family", cascade="all, delete-orphan")
    
    # قيود
    __table_args__ = (
        Index('ix_families_city_status', 'city', 'family_status'),
        UniqueConstraint('family_code', name='uq_family_code'),
    )


class Beneficiary(Base):
    """المستفيدون"""
    __tablename__ = 'beneficiaries'
    
    id = Column(Integer, primary_key=True)
    family_id = Column(Integer, ForeignKey('families.id'))
    
    # المعلومات الشخصية
    national_id = Column(String(14), unique=True, index=True)
    full_name_ar = Column(String(100), nullable=False)
    full_name_en = Column(String(100))
    
    # الاسم المفكك
    first_name = Column(String(50))
    father_name = Column(String(50))
    grandfather_name = Column(String(50))
    family_name = Column(String(50))
    
    # المعلومات الحيوية
    birth_date = Column(Date)
    gender = Column(String(1))  # M, F
    blood_type = Column(String(3))
    
    # الحالة الاجتماعية
    marital_status = Column(String(20))  # single, married, divorced, widowed
    marriage_date = Column(Date)
    children_count = Column(Integer, default=0)
    
    # التعليم والمهنة
    education_level = Column(String(50))
    qualification = Column(String(100))
    occupation = Column(String(100))
    monthly_income = Column(Numeric(10, 2))
    
    # الصحة
    health_status = Column(String(30))
    has_disabilities = Column(Boolean, default=False)
    disability_type = Column(String(100))
    
    # الاتصال
    phone = Column(String(15))
    phone2 = Column(String(15))
    email = Column(String(100))
    
    # العنوان (إذا مختلف عن الأسرة)
    address = Column(Text)
    city = Column(String(50))
    region = Column(String(50))
    
    # معلومات إضافية
    is_family_head = Column(Boolean, default=False)
    monthly_expenses = Column(Numeric(10, 2))
    housing_description = Column(Text)
    
    # الحالة
    status = Column(String(20), default='active')  # active, inactive, suspended, deceased
    
    # التواريخ
    registration_date = Column(Date, server_default=func.current_date())
    last_visit_date = Column(Date)
    next_followup_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    family = relationship("Family", back_populates="beneficiaries")
    activities = relationship("ActivityBeneficiary", back_populates="beneficiary", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="beneficiary", cascade="all, delete-orphan")
    
    # قيود
    __table_args__ = (
        Index('ix_beneficiaries_family', 'family_id'),
        Index('ix_beneficiaries_city', 'city'),
        Index('ix_beneficiaries_status', 'status'),
        CheckConstraint("gender IN ('M', 'F')", name='ck_beneficiary_gender'),
    )

# ============== نظام الأنشطة ==============

class ActivityCategory(Base):
    """فئات الأنشطة"""
    __tablename__ = 'activity_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    name_en = Column(String(50))
    description = Column(Text)
    icon = Column(String(50))
    color = Column(String(7))  # HEX color
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    activity_types = relationship("ActivityType", back_populates="category", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_activity_categories_active', 'is_active'),
    )


class ActivityType(Base):
    """أنواع الأنشطة"""
    __tablename__ = 'activity_types'
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('activity_categories.id'), nullable=False)
    
    name = Column(String(100), nullable=False)
    name_en = Column(String(100))
    code = Column(String(20), unique=True)
    description = Column(Text)
    
    # إعدادات النوع
    requires_beneficiary = Column(Boolean, default=True)
    requires_duration = Column(Boolean, default=False)
    requires_location = Column(Boolean, default=True)
    requires_cost = Column(Boolean, default=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    category = relationship("ActivityCategory", back_populates="activity_types")
    custom_fields = relationship("CustomField", back_populates="activity_type", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="activity_type", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_activity_types_category', 'category_id'),
        UniqueConstraint('code', name='uq_activity_type_code'),
    )


class CustomField(Base):
    """الحقول المخصصة لكل نوع نشاط"""
    __tablename__ = 'custom_fields'
    
    id = Column(Integer, primary_key=True)
    activity_type_id = Column(Integer, ForeignKey('activity_types.id'), nullable=False)
    
    # تعريف الحقل
    field_name = Column(String(50), nullable=False)
    field_type = Column(String(20), nullable=False)  # text, number, date, select, boolean
    field_label_ar = Column(String(100), nullable=False)
    field_label_en = Column(String(100))
    
    # إعدادات الحقل
    is_required = Column(Boolean, default=False)
    is_unique = Column(Boolean, default=False)
    default_value = Column(Text)
    
    # للقوائم المختارة
    options = Column(JSON)
    
    # التحقق
    min_value = Column(Numeric(10, 2))
    max_value = Column(Numeric(10, 2))
    min_length = Column(Integer)
    max_length = Column(Integer)
    
    # العرض
    sort_order = Column(Integer, default=0)
    group_name = Column(String(50))
    help_text_ar = Column(Text)
    help_text_en = Column(Text)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # علاقات
    activity_type = relationship("ActivityType", back_populates="custom_fields")
    field_values = relationship("FieldValue", back_populates="custom_field", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_custom_fields_activity_type', 'activity_type_id'),
        CheckConstraint("field_type IN ('text', 'number', 'date', 'select', 'boolean')", name='ck_field_type'),
    )


class Activity(Base):
    """الأنشطة المنفذة"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True)
    activity_type_id = Column(Integer, ForeignKey('activity_types.id'), nullable=False)
    
    # المعلومات الأساسية
    title = Column(String(200), nullable=False)
    description = Column(Text)
    
    # التواريخ
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    duration_days = Column(Integer)
    
    # الموقع
    location = Column(String(200))
    city = Column(String(50))
    region = Column(String(50))
    
    # التكاليف
    estimated_cost = Column(Numeric(12, 2))
    actual_cost = Column(Numeric(12, 2))
    currency = Column(String(3), default='EGP')
    
    # الحالة
    status = Column(Enum(ActivityStatus), default=ActivityStatus.PLANNED)
    priority = Column(String(20), default='medium')  # low, medium, high, urgent
    
    # المسؤولية
    responsible_person = Column(String(100))
    team_members = Column(Text)
    
    # التسجيلات
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    notes = Column(Text)
    
    # علاقات
    activity_type = relationship("ActivityType", back_populates="activities")
    beneficiaries = relationship("ActivityBeneficiary", back_populates="activity", cascade="all, delete-orphan")
    field_values = relationship("FieldValue", back_populates="activity", cascade="all, delete-orphan")
    creator_user = relationship("User", foreign_keys=[created_by])
    
    # قيود وفهارس
    __table_args__ = (
        Index('ix_activities_type_status', 'activity_type_id', 'status'),
        Index('ix_activities_dates', 'start_date', 'end_date'),
        Index('ix_activities_location', 'location'),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name='ck_activity_priority'),
    )


class ActivityBeneficiary(Base):
    """ربط المستفيدين بالأنشطة"""
    __tablename__ = 'activity_beneficiaries'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey('beneficiaries.id'), nullable=False)
    
    # دور المستفيد في النشاط
    role = Column(String(50))  # مستفيد رئيسي، مشارك، متطوع
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default='active')  # active, completed, withdrawn
    
    notes = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    # علاقات
    activity = relationship("Activity", back_populates="beneficiaries")
    beneficiary = relationship("Beneficiary", back_populates="activities")
    
    # قيود
    __table_args__ = (
        UniqueConstraint('activity_id', 'beneficiary_id', name='uq_activity_beneficiary'),
        Index('ix_activity_beneficiaries_activity', 'activity_id'),
        Index('ix_activity_beneficiaries_beneficiary', 'beneficiary_id'),
    )


class FieldValue(Base):
    """قيم الحقول المخصصة"""
    __tablename__ = 'field_values'
    
    id = Column(Integer, primary_key=True)
    activity_id = Column(Integer, ForeignKey('activities.id'), nullable=False)
    custom_field_id = Column(Integer, ForeignKey('custom_fields.id'), nullable=False)
    
    # القيم (نخزن في عمود حسب النوع)
    text_value = Column(Text)
    number_value = Column(Numeric(10, 2))
    date_value = Column(Date)
    boolean_value = Column(Boolean)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    activity = relationship("Activity", back_populates="field_values")
    custom_field = relationship("CustomField", back_populates="field_values")
    
    # قيود
    __table_args__ = (
        UniqueConstraint('activity_id', 'custom_field_id', name='uq_field_value'),
        Index('ix_field_values_activity', 'activity_id'),
        Index('ix_field_values_field', 'custom_field_id'),
    )

# ============== نظام التبرعات ==============

class Donor(Base):
    """المتبرعون"""
    __tablename__ = 'donors'
    
    id = Column(Integer, primary_key=True)
    
    # نوع المتبرع
    donor_type = Column(String(20), nullable=False)  # individual, company, organization
    donor_code = Column(String(20), unique=True)
    
    # للأفراد
    full_name = Column(String(100))
    national_id = Column(String(14), unique=True)
    
    # للشركات
    company_name = Column(String(200))
    commercial_registration = Column(String(50))
    
    # الاتصال
    phone = Column(String(15))
    email = Column(String(100))
    address = Column(Text)
    city = Column(String(50))
    
    # معلومات إضافية
    occupation = Column(String(100))
    contact_preference = Column(String(20))  # phone, email
    
    # الحالة
    status = Column(String(20), default='active')
    
    # التواريخ
    first_donation_date = Column(Date)
    last_donation_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    donations = relationship("Donation", back_populates="donor", cascade="all, delete-orphan")
    
    # قيود
    __table_args__ = (
        Index('ix_donors_type_status', 'donor_type', 'status'),
        UniqueConstraint('donor_code', name='uq_donor_code'),
        CheckConstraint("donor_type IN ('individual', 'company', 'organization')", name='ck_donor_type'),
    )

# أضف هذا النموذج قبل نموذج Donation في models.py

class DonationAllocation(Base):
    """تخصيص التبرعات للمستفيدين"""
    __tablename__ = 'donation_allocations'
    
    id = Column(Integer, primary_key=True)
    donation_id = Column(Integer, ForeignKey('donations.id'), nullable=False)
    beneficiary_id = Column(Integer, ForeignKey('beneficiaries.id'), nullable=False)
    activity_id = Column(Integer, ForeignKey('activities.id'))  # اختياري: إذا كان مرتبطاً بنشاط
    
    allocated_amount = Column(Numeric(12, 2), nullable=False)
    allocation_date = Column(Date, nullable=False, server_default=func.current_date())
    
    # حالة التخصيص
    status = Column(String(20), default='allocated')  # allocated, distributed, cancelled
    distribution_date = Column(Date)
    distributed_by = Column(Integer, ForeignKey('users.id'))
    
    # معلومات إضافية
    purpose = Column(String(200))
    notes = Column(Text)
    
    # التواريخ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    donation = relationship("Donation", back_populates="allocations")
    beneficiary = relationship("Beneficiary")
    activity = relationship("Activity")
    distributor_user = relationship("User", foreign_keys=[distributed_by])
    
    # قيود
    __table_args__ = (
        Index('ix_donation_allocations_donation', 'donation_id'),
        Index('ix_donation_allocations_beneficiary', 'beneficiary_id'),
        UniqueConstraint('donation_id', 'beneficiary_id', name='uq_donation_beneficiary'),
    )


class Donation(Base):
    """التبرعات"""
    __tablename__ = 'donations'
    
    id = Column(Integer, primary_key=True)
    donor_id = Column(Integer, ForeignKey('donors.id'))
    
    # معلومات عامة
    donation_number = Column(String(50), unique=True, nullable=False)
    donation_type = Column(String(20), nullable=False)  # cash, in_kind, service
    
    # التواريخ
    donation_date = Column(Date, nullable=False, server_default=func.current_date())
    receipt_date = Column(Date)
    
    # المبلغ
    amount = Column(Numeric(12, 2))
    currency = Column(String(3), default='EGP')
    
    # طريقة الدفع
    payment_method = Column(String(30))  # cash, check, bank_transfer
    
    # الحالة
    status = Column(Enum(DonationStatus), default=DonationStatus.PENDING)
    
    # التخصيص
    purpose = Column(String(200))
    is_zakat = Column(Boolean, default=False)
    is_sadaqah = Column(Boolean, default=False)
    
    # الإيصال
    receipt_number = Column(String(50), unique=True)
    receipt_issued = Column(Boolean, default=False)
    
    # التسجيلات
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    notes = Column(Text)
    
    # علاقات
    donor = relationship("Donor", back_populates="donations")
    items = relationship("DonationItem", back_populates="donation", cascade="all, delete-orphan")
    allocations = relationship("DonationAllocation", back_populates="donation", cascade="all, delete-orphan")
    creator_user = relationship("User", foreign_keys=[created_by])
    
    # قيود
    __table_args__ = (
        Index('ix_donations_donor_date', 'donor_id', 'donation_date'),
        Index('ix_donations_status', 'status'),
        CheckConstraint("donation_type IN ('cash', 'in_kind', 'service')", name='ck_donation_type'),
    )


class DonationItem(Base):
    """بنود التبرعات العينية"""
    __tablename__ = 'donation_items'
    
    id = Column(Integer, primary_key=True)
    donation_id = Column(Integer, ForeignKey('donations.id'), nullable=False)
    
    item_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20))
    unit_value = Column(Numeric(10, 2))
    total_value = Column(Numeric(12, 2))
    
    condition = Column(String(20))  # new, used_good
    storage_location = Column(String(100))
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # علاقات
    donation = relationship("Donation", back_populates="items")
    
    __table_args__ = (
        Index('ix_donation_items_donation', 'donation_id'),
    )

# ============== جداول النظام الأساسية ==============

class Attachment(Base):
    """الملفات المرفقة"""
    __tablename__ = 'attachments'
    
    id = Column(Integer, primary_key=True)
    beneficiary_id = Column(Integer, ForeignKey('beneficiaries.id'))
    activity_id = Column(Integer, ForeignKey('activities.id'))
    donation_id = Column(Integer, ForeignKey('donations.id'))
    
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    
    title = Column(String(100))
    description = Column(Text)
    document_type = Column(String(50))
    
    uploaded_at = Column(DateTime, server_default=func.now())
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    
    # علاقات
    beneficiary = relationship("Beneficiary", back_populates="attachments")
    uploader_user = relationship("User")
    
    __table_args__ = (
        Index('ix_attachments_beneficiary', 'beneficiary_id'),
        Index('ix_attachments_activity', 'activity_id'),
    )


class SystemLog(Base):
    """سجلات النظام"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    log_level = Column(String(20))  # info, warning, error, critical
    log_type = Column(String(50))  # system, backup, security, audit
    message = Column(Text, nullable=False)
    
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    table_name = Column(String(50))
    record_id = Column(Integer)
    changes = Column(JSON)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # علاقات
    user = relationship("User")
    
    __table_args__ = (
        Index('ix_system_logs_level_type', 'log_level', 'log_type'),
        Index('ix_system_logs_created', 'created_at'),
    )


class Notification(Base):
    """الإشعارات"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # معلومات الإشعار
    notification_type = Column(String(20), nullable=False)  # reminder, alert, info
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # السياق
    related_table = Column(String(50))
    related_id = Column(Integer)
    action_url = Column(String(500))
    
    # التواريخ
    created_at = Column(DateTime, server_default=func.now())
    scheduled_for = Column(DateTime)
    sent_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # الحالة
    status = Column(String(20), default='pending')  # pending, sent, read
    priority = Column(String(20), default='medium')  # low, medium, high
    
    # بيانات إضافية (اسم معدل لتجنب مشكلة metadata)
    meta_data = Column(JSON, name='metadata')  # تم التصحيح هنا
    
    # علاقات
    user = relationship("User")
    
    __table_args__ = (
        Index('ix_notifications_user_status', 'user_id', 'status'),
        Index('ix_notifications_type', 'notification_type'),
        Index('ix_notifications_created', 'created_at'),
    )


# ============== دوال المساعدة ==============

def get_all_models():
    """الحصول على جميع النماذج"""
    return [
        User, UserSession, UserLog,
        Family, Beneficiary,
        ActivityCategory, ActivityType, CustomField, Activity,
        ActivityBeneficiary, FieldValue,
        Donor, Donation, DonationItem, DonationAllocation,
        Attachment, SystemLog, Notification
    ]