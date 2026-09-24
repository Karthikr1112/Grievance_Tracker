from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Role, UserProfile, Store, EnquiryType, Grievance

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    filter_horizontal = ('stores',)

class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_emp_id', 'get_role', 'get_status', 'is_staff', 'is_superuser')
    
    def get_emp_id(self, obj):
        return obj.profile.emp_id if hasattr(obj, 'profile') else '-'
    get_emp_id.short_description = 'Emp ID'
    
    def get_role(self, obj):
        return obj.profile.role.name if hasattr(obj, 'profile') and obj.profile.role else '-'
    get_role.short_description = 'Role'
    
    def get_status(self, obj):
        return obj.profile.get_approval_status_display() if hasattr(obj, 'profile') else '-'
    get_status.short_description = 'Approval Status'

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'emp_id', 'role', 'approval_status', 'is_approved')
    list_filter = ('role', 'approval_status', 'is_approved')
    search_fields = ('user__username', 'emp_id', 'user__email')
    filter_horizontal = ('stores',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('name',)
    list_filter = ('is_active',)
    actions = ['deactivate_selected', 'activate_selected']

    @admin.action(description='Deactivate selected stores (Safely archive without losing data)')
    def deactivate_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} store(s) successfully deactivated.")

    @admin.action(description='Activate selected stores')
    def activate_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} store(s) successfully activated.")

@admin.register(EnquiryType)
class EnquiryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('name',)
    list_filter = ('is_active',)
    actions = ['deactivate_selected', 'activate_selected']

    @admin.action(description='Deactivate selected enquiry types (Safely archive)')
    def deactivate_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} enquiry type(s) successfully deactivated.")

    @admin.action(description='Activate selected enquiry types')
    def activate_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} enquiry type(s) successfully activated.")

@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = (
        'emp_id', 'emp_name', 'open_date', 'store', 'enquiry_type', 
        'enquiry_received_by', 'current_status', 'created_at'
    )
    list_filter = ('current_status', 'store', 'enquiry_type', 'open_date')
    search_fields = ('emp_id', 'emp_name', 'enquiry_details')
    list_select_related = ('store', 'enquiry_type', 'created_by')
