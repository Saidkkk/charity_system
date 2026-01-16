# auth/permissions.py - النسخة المصححة
from typing import List, Dict, Any, Set, Tuple
from enum import Enum
from config import Config

class PermissionLevel(str, Enum):
    """مستويات الصلاحيات"""
    NONE = "none"
    VIEW = "view"
    CREATE = "create"
    EDIT = "edit"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    ALL = "all"

class Resource(str, Enum):
    """موارد النظام"""
    ACTIVITIES = "activities"
    ACTIVITY_CATEGORIES = "activity_categories"
    ACTIVITY_TYPES = "activity_types"
    BENEFICIARIES = "beneficiaries"
    FAMILIES = "families"
    DONATIONS = "donations"
    DONORS = "donors"
    EMPLOYEES = "employees"
    USERS = "users"
    REPORTS = "reports"
    STATISTICS = "statistics"
    SETTINGS = "settings"
    NOTIFICATIONS = "notifications"
    BACKUP = "backup"
    LOGS = "logs"

class Permission:
    """كائن يمثل صلاحية"""
    
    def __init__(self, resource: Resource, level: PermissionLevel, scope: str = "all"):
        self.resource = resource
        self.level = level
        self.scope = scope
    
    def __str__(self) -> str:
        return f"{self.level.value}:{self.resource.value}:{self.scope}"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Permission):
            return False
        return (self.resource == other.resource and 
                self.level == other.level and 
                self.scope == other.scope)
    
    def __hash__(self):
        """جعل الكائن قابلاً للتجزئة"""
        return hash((self.resource.value, self.level.value, self.scope))
    
    def to_tuple(self) -> Tuple:
        """تحويل إلى tuple للتخزين"""
        return (self.resource.value, self.level.value, self.scope)
    
    @classmethod
    def from_tuple(cls, tuple_data: Tuple):
        """إنشاء من tuple"""
        return cls(Resource(tuple_data[0]), PermissionLevel(tuple_data[1]), tuple_data[2])
    
    def check(self, user_role: str, user_id: int = None, resource_owner_id: int = None) -> bool:
        """التحقق من الصلاحية"""
        if user_role == "admin":
            return True
        
        role_permissions = Config.ROLE_PERMISSIONS.get(user_role, [])
        
        if "*" in role_permissions:
            return True
        
        permission_str = f"{self.level.value}:{self.resource.value}"
        
        for perm in role_permissions:
            if permission_str == perm:
                return True
            if perm.endswith(":*") and permission_str.startswith(perm[:-2]):
                return True
        
        if resource_owner_id is not None and user_id is not None:
            if self.scope == "own" and resource_owner_id == user_id:
                return True
        
        return False

class PermissionManager:
    """مدير الصلاحيات"""
    
    def __init__(self):
        self._permissions_cache = {}
        self._initialize_permissions()
    
    def _initialize_permissions(self):
        """تهيئة الصلاحيات المحددة مسبقاً"""
        # صلاحيات المدير (كل الصلاحيات)
        admin_perms = set()
        for resource in Resource:
            admin_perms.add(Permission(resource, PermissionLevel.ALL, "all"))
        self._permissions_cache["admin"] = admin_perms
        
        # صلاحيات المشرف
        supervisor_perms = set()
        for resource in Resource:
            if resource not in [Resource.USERS, Resource.SETTINGS, Resource.BACKUP]:
                supervisor_perms.add(Permission(resource, PermissionLevel.VIEW, "all"))
                supervisor_perms.add(Permission(resource, PermissionLevel.CREATE, "all"))
                supervisor_perms.add(Permission(resource, PermissionLevel.EDIT, "all"))
                supervisor_perms.add(Permission(resource, PermissionLevel.EXPORT, "all"))
            
            if resource in [Resource.DONATIONS, Resource.ACTIVITIES]:
                supervisor_perms.add(Permission(resource, PermissionLevel.APPROVE, "limited"))
                supervisor_perms.add(Permission(resource, PermissionLevel.DELETE, "limited"))
        
        self._permissions_cache["supervisor"] = supervisor_perms
        
        # صلاحيات الموظف
        employee_perms = set()
        resources_for_employee = [
            Resource.ACTIVITIES, Resource.BENEFICIARIES, 
            Resource.FAMILIES, Resource.DONATIONS, Resource.DONORS
        ]
        
        for resource in resources_for_employee:
            employee_perms.add(Permission(resource, PermissionLevel.VIEW, "all"))
            employee_perms.add(Permission(resource, PermissionLevel.CREATE, "own"))
            employee_perms.add(Permission(resource, PermissionLevel.EDIT, "own"))
            employee_perms.add(Permission(resource, PermissionLevel.EXPORT, "own"))
        
        self._permissions_cache["employee"] = employee_perms
        
        # صلاحيات المراجع
        viewer_perms = set()
        for resource in Resource:
            if resource not in [Resource.USERS, Resource.SETTINGS]:
                viewer_perms.add(Permission(resource, PermissionLevel.VIEW, "all"))
                viewer_perms.add(Permission(resource, PermissionLevel.EXPORT, "limited"))
        
        self._permissions_cache["viewer"] = viewer_perms
    
    def get_permissions(self, role: str) -> Set[Permission]:
        """الحصول على صلاحيات دور معين"""
        return self._permissions_cache.get(role, set())
    
    def has_permission(self, role: str, permission: Permission) -> bool:
        """التحقق من وجود صلاحية معينة"""
        if role == "admin":
            return True
        
        permissions = self.get_permissions(role)
        return permission in permissions
    
    def can_view(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية المشاهدة"""
        permission = Permission(resource, PermissionLevel.VIEW, scope)
        return self.has_permission(role, permission)
    
    def can_create(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية الإنشاء"""
        permission = Permission(resource, PermissionLevel.CREATE, scope)
        return self.has_permission(role, permission)
    
    def can_edit(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية التعديل"""
        permission = Permission(resource, PermissionLevel.EDIT, scope)
        return self.has_permission(role, permission)
    
    def can_delete(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية الحذف"""
        permission = Permission(resource, PermissionLevel.DELETE, scope)
        return self.has_permission(role, permission)
    
    def can_approve(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية الاعتماد"""
        permission = Permission(resource, PermissionLevel.APPROVE, scope)
        return self.has_permission(role, permission)
    
    def can_export(self, role: str, resource: Resource, scope: str = "all") -> bool:
        """التحقق من صلاحية التصدير"""
        permission = Permission(resource, PermissionLevel.EXPORT, scope)
        return self.has_permission(role, permission)
    
    def get_allowed_resources(self, role: str, level: PermissionLevel) -> List[Resource]:
        """الحصول على الموارد المسموح بها"""
        permissions = self.get_permissions(role)
        resources = []
        
        for perm in permissions:
            if perm.level == level or perm.level == PermissionLevel.ALL:
                resources.append(perm.resource)
        
        return list(set(resources))  # إزالة التكرارات
    
    def check_resource_access(self, role: str, resource: Resource, 
                            action: str, user_id: int = None, 
                            resource_data: Dict = None) -> bool:
        """التحقق من الوصول للمورد"""
        
        level_map = {
            "view": PermissionLevel.VIEW,
            "create": PermissionLevel.CREATE,
            "edit": PermissionLevel.EDIT,
            "delete": PermissionLevel.DELETE,
            "approve": PermissionLevel.APPROVE,
            "export": PermissionLevel.EXPORT
        }
        
        if action not in level_map:
            return False
        
        level = level_map[action]
        scope = "all"
        
        if resource_data and user_id:
            if "created_by" in resource_data and resource_data["created_by"] == user_id:
                scope = "own"
            elif "department" in resource_data and "user_department" in resource_data:
                if resource_data["department"] == resource_data["user_department"]:
                    scope = "department"
        
        permission = Permission(resource, level, scope)
        return self.has_permission(role, permission)
    
    def get_role_summary(self, role: str) -> Dict[str, Any]:
        """الحصول على ملخص صلاحيات الدور"""
        permissions = self.get_permissions(role)
        
        summary = {
            "role": role,
            "role_name": Config.get_role_name(role),
            "total_permissions": len(permissions),
            "resources": {},
            "allowed_actions": {}
        }
        
        for perm in permissions:
            resource_name = perm.resource.value
            
            if resource_name not in summary["resources"]:
                summary["resources"][resource_name] = []
            
            summary["resources"][resource_name].append({
                "level": perm.level.value,
                "scope": perm.scope
            })
            
            if perm.level.value not in summary["allowed_actions"]:
                summary["allowed_actions"][perm.level.value] = []
            
            summary["allowed_actions"][perm.level.value].append(resource_name)
        
        return summary

# إنشاء نسخة وحيدة من مدير الصلاحيات
permission_manager = PermissionManager()

# دوال مختصرة للاستخدام
def check_permission(role: str, permission_str: str) -> bool:
    """التحقق من صلاحية (واجهة توافقية مع Config)"""
    try:
        parts = permission_str.split(":", 2)
        
        if len(parts) < 2:
            return False
        
        level_str, resource_str = parts[0], parts[1]
        scope = parts[2] if len(parts) > 2 else "all"
        
        try:
            level = PermissionLevel(level_str)
            resource = Resource(resource_str)
        except ValueError:
            return False
        
        permission = Permission(resource, level, scope)
        return permission_manager.has_permission(role, permission)
        
    except Exception:
        return False

def has_role_permission(role: str, resource: str, action: str, 
                       user_id: int = None, resource_data: Dict = None) -> bool:
    """التحقق من صلاحية الدور على مورد معين"""
    try:
        resource_enum = Resource(resource)
        return permission_manager.check_resource_access(
            role, resource_enum, action, user_id, resource_data
        )
    except ValueError:
        return False

def get_user_permissions(user_role: str, user_id: int = None) -> Dict[str, Any]:
    """الحصول على صلاحيات المستخدم بشكل مفصل"""
    return permission_manager.get_role_summary(user_role)

def can_access_module(user_role: str, module_name: str) -> bool:
    """التحقق من إمكانية الوصول لوحدة معينة"""
    module_resource_map = {
        "dashboard": Resource.ACTIVITIES,
        "activities": Resource.ACTIVITIES,
        "beneficiaries": Resource.BENEFICIARIES,
        "donations": Resource.DONATIONS,
        "employees": Resource.EMPLOYEES,
        "reports": Resource.REPORTS,
        "notifications": Resource.NOTIFICATIONS,
        "settings": Resource.SETTINGS
    }
    
    if module_name not in module_resource_map:
        return False
    
    resource = module_resource_map[module_name]
    return permission_manager.can_view(user_role, resource)