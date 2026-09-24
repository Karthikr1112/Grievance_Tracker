import openpyxl
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.html import format_html
from django.utils import timezone
from .models import UserProfile, EnquiryType, Grievance, GrievanceStatus, UserRole
from django.db.models import Count
from .models import UserProfile, Role, EnquiryType, Grievance, GrievanceStatus

# Register your models here.

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Dedicated Admin interface to create and manage custom user roles dynamically.
    Dedicated Admin interface to create and manage custom user roles directly from the Django Admin.
    """
    list_display = (
        'name',
        'is_admin',
        'can_level_1_resolve',
        'can_level_2_resolve',
        'can_manage_enquiry_types',
        'scope_to_assigned_store',
        'user_count',
        'created_at'
    )
    list_filter = (
        'is_admin',
        'can_level_1_resolve',
        'can_level_2_resolve',
        'can_manage_enquiry_types',
        'scope_to_assigned_store'
    )
    list_display = ('name', 'description', 'user_count', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

    fieldsets = (
        ('Role Identification', {
            'fields': ('name', 'description')
        }),
        ('Role Permissions & Access Control', {
            'description': 'Configure the capabilities granted to users assigned this role.',
            'fields': (
                'is_admin',
                'can_level_1_resolve',
                'can_level_2_resolve',
                'can_manage_enquiry_types',
                'scope_to_assigned_store',
            )
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(users_total=Count('profiles'))

    @admin.display(description='Assigned Users')
    @admin.display(description='Total Assigned Users')
    def user_count(self, obj):
        return obj.users_total


# Define inline for UserProfile inside standard User admin
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile & RBAC Role'
    verbose_name_plural = 'Profile & Dynamic Role'
    verbose_name_plural = 'Profile & Role'
    fk_name = 'user'
    extra = 0


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')

    @admin.display(description='Role')
    def get_role(self, instance):
        if hasattr(instance, 'profile'):
            return instance.profile.get_role_display()
        return "No Profile"
        if hasattr(instance, 'profile') and instance.profile.role:
            return instance.profile.role.name
        return "Unassigned"


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(EnquiryType)
class EnquiryTypeAdmin(admin.ModelAdmin):
    """
    Dedicated admin page to add, edit, and manage Enquiry Types with active toggle and grievance count.
    """
    list_display = ('name', 'is_active', 'grievance_count', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

    def get_queryset(self, request):
        # Optimization: annotate grievance count to avoid N+1 query
        from django.db.models import Count
        qs = super().get_queryset(request)
        return qs.annotate(grievances_total=Count('grievances'))

    @admin.display(description='Total Grievances')
    def grievance_count(self, obj):
        return obj.grievances_total


@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    """
    Enterprise Django Admin for Grievances:
    - Optimized with list_select_related to completely eliminate N+1 queries.
    - Export selected records to formatted Excel workbook.
    - Color-coded status badges, search, and hierarchy.
    """
    # CRITICAL N+1 Query Prevention in Django Admin:
    list_select_related = ('enquiry_type', 'created_by', 'updated_by')

    list_display = (
        'id',
        'open_date',
        'emp_id',
        'emp_name',
        'store_name',
        'department',
        'enquiry_type_link',
        'status_badge',
        'period_days',
        'closed_date'
    )
    list_filter = (
        'current_status',
        'enquiry_type',
        'department',
        'store_name',
        ('open_date', admin.DateFieldListFilter),
        ('closed_date', admin.DateFieldListFilter),
    )
    search_fields = (
        'id',
        'emp_id',
        'emp_name',
        'store_name',
        'department',
        'enquiry_received_by',
        'enquiry_details',
    )
    date_hierarchy = 'open_date'
    readonly_fields = ('period_days', 'created_at', 'updated_at', 'created_by', 'updated_by')
    actions = ['export_to_excel', 'mark_as_resolved', 'mark_as_closed']

    fieldsets = (
        ('Employee & Store Information', {
            'fields': (
                ('open_date', 'current_status'),
                ('emp_id', 'emp_name'),
                ('designation', 'department'),
                ('section', 'store_name'),
            )
        }),
        ('Enquiry Details', {
            'fields': (
                ('enquiry_type', 'enquiry_received_by'),
                'enquiry_details',
            )
        }),
        ('Resolution Workflow & Escalation', {
            'fields': (
                'first_level',
                'second_level',
                ('closed_date', 'period_days'),
            )
        }),
        ('Audit Information', {
            'classes': ('collapse',),
            'fields': (
                ('created_by', 'updated_by'),
                ('created_at', 'updated_at'),
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.display(description='Enquiry Type')
    def enquiry_type_link(self, obj):
        return obj.enquiry_type.name

    @admin.display(description='Current Status')
    def status_badge(self, obj):
        colors = {
            GrievanceStatus.OPEN: '#dc3545',
            GrievanceStatus.IN_PROGRESS: '#0d6efd',
            GrievanceStatus.LEVEL_1_REVIEW: '#fd7e14',
            GrievanceStatus.LEVEL_2_ESCALATED: '#6f42c1',
            GrievanceStatus.RESOLVED: '#198754',
            GrievanceStatus.CLOSED: '#6c757d',
        }
        color = colors.get(obj.current_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            obj.get_current_status_display()
        )

    @admin.action(description='Export Selected Grievances to Excel')
    def export_to_excel(self, request, queryset):
        # Optimization: fetch related records in one go
        queryset = queryset.select_related('enquiry_type')

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "GRIEVANCE TRACKER - RRPL"

        headers = [
            "S.No", "Open Date", "Emp ID", "Emp Name", "Designation",
            "Department", "Section", "Store Name", "Enquiry Type",
            "Enquiry Received By", "Enquiry Details", "1st Level",
            "2nd Level", "Closed Date", "Period Days", "Current Status"
        ]
        ws.append(headers)

        # Style header row
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
            cell.fill = openpyxl.styles.PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
            cell.alignment = openpyxl.styles.Alignment(horizontal="center", vertical="center")

        for obj in queryset:
            ws.append([
                obj.id,
                obj.open_date.strftime('%Y-%m-%d') if obj.open_date else '',
                obj.emp_id,
                obj.emp_name,
                obj.designation,
                obj.department,
                obj.section,
                obj.store_name,
                obj.enquiry_type.name if obj.enquiry_type else '',
                obj.enquiry_received_by,
                obj.enquiry_details,
                obj.first_level or '',
                obj.second_level or '',
                obj.closed_date.strftime('%Y-%m-%d') if obj.closed_date else '',
                obj.period_days,
                obj.get_current_status_display(),
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        filename = f"RRPL_Grievance_Report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb.save(response)
        return response

    @admin.action(description='Mark Selected as Resolved')
    def mark_as_resolved(self, request, queryset):
        queryset.update(
            current_status=GrievanceStatus.RESOLVED,
            closed_date=timezone.now().date(),
            updated_by=request.user
        )
        self.message_user(request, f"{queryset.count()} grievance(s) successfully marked as Resolved.")

    @admin.action(description='Mark Selected as Closed')
    def mark_as_closed(self, request, queryset):
        queryset.update(
            current_status=GrievanceStatus.CLOSED,
            closed_date=timezone.now().date(),
            updated_by=request.user
        )
        self.message_user(request, f"{queryset.count()} grievance(s) successfully marked as Closed.")
