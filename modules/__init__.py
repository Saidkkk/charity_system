# modules/__init__.py (التحديث)
"""
تصدير جميع وحدات النظام
"""

from .dashboard import show_dashboard
from .beneficiaries import show_beneficiaries
from .activities import show_activities_main as show_activities
from .donations import show_donations_main as show_donations
# سيتم إضافة الوحدات الأخرى لاحقاً
# from .donations import show_donations
# from .reports import show_reports

__all__ = [
    'show_dashboard',
    'show_beneficiaries',
    'show_activities',
    'show_donations',
    # 'show_reports'
]