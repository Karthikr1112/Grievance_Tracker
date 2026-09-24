import csv
import json
from datetime import timedelta
from collections import OrderedDict
from functools import wraps

import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse

from .forms import GrievanceForm, CustomUserCreationForm, CustomUserEditForm
from .models import Grievance, Store, EnquiryType, Role, UserProfile


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        profile = getattr(request.user, 'profile', None)
        is_admin = request.user.is_superuser or (profile and profile.is_admin)
        if not is_admin:
            messages.error(request, "Access denied. Administrator privileges are required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def approved_user_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            profile = getattr(request.user, 'profile', None)
            if not profile or not profile.is_approved or profile.approval_status != 'approved':
                user = request.user
                status = profile.approval_status if profile else 'pending'
                auth_logout(request)
                if status == 'rejected':
                    messages.error(request, "Your account request was rejected by an administrator.")
                    return render(request, 'grievances/login.html')
                else:
                    messages.success(request, "Your account is pending admin approval. Please wait for an administrator to approve your access.")
                    return render(request, 'grievances/login.html', {
                        'show_pending_popup': True,
                        'popup_user': user,
                    })
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def custom_login(request):
    if request.user.is_authenticated:
        if not request.user.is_superuser:
            profile = getattr(request.user, 'profile', None)
            if not profile or not profile.is_approved or profile.approval_status != 'approved':
                user = request.user
                status = profile.approval_status if profile else 'pending'
                auth_logout(request)
                if status == 'rejected':
                    messages.error(request, "Your account request was rejected by an administrator.")
                    return render(request, 'grievances/login.html')
                else:
                    messages.success(request, "Your account is pending admin approval. Please wait for an administrator to approve your access.")
                    return render(request, 'grievances/login.html', {
                        'show_pending_popup': True,
                        'popup_user': user,
                    })
        return redirect('dashboard')

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        if not email:
            email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'

        api_url = "https://stylehr.in/api/login/"
        payload = {
            "email": email,
            "password": password
        }

        user_authenticated = False

        # 1. Attempt Style HR API authentication
        try:
            response = requests.post(api_url, json=payload, timeout=5)

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    data = {}

                # Try to extract the firm abbreviation (prefix)
                prefix = ""
                if 'store' in data and isinstance(data['store'], dict):
                    firm = data['store'].get('firm')
                    if isinstance(firm, dict):
                        prefix = firm.get('abbreviation') or firm.get('prefix') or ""

                if not prefix:
                    for key in ['prefix', 'firm_abbreviation', 'abbreviation', 'firm_prefix']:
                        if key in data and data[key]:
                            prefix = str(data[key]).strip()
                            break

                if not prefix:
                    for parent_key in ['user', 'employee', 'data', 'profile', 'firm', 'store']:
                        if parent_key in data and isinstance(data[parent_key], dict):
                            p_dict = data[parent_key]
                            for key in ['prefix', 'firm_abbreviation', 'abbreviation', 'firm_prefix']:
                                if key in p_dict and p_dict[key]:
                                    prefix = str(p_dict[key]).strip()
                                    break
                            if prefix:
                                break
                
                # Extract employee code
                code = data.get('employee_code') or ""
                if not code:
                    for parent_key in ['user', 'employee', 'data', 'profile']:
                        if parent_key in data and isinstance(data[parent_key], dict):
                            code = data[parent_key].get('employee_code') or data[parent_key].get('code') or ""
                            if code:
                                break
                
                # Build employee ID
                emp_id = None
                if code:
                    emp_id = str(code).strip()

                if not emp_id:
                    for key in ['employee_id', 'emp_id', 'employee_code', 'emp_code', 'code']:
                        if key in data and data[key]:
                            emp_id = str(data[key]).strip()
                            break

                if not emp_id and '@' not in email:
                    emp_id = email

                # Format prefix with employee code (e.g. 97-9701)
                if emp_id and prefix:
                    prefix = str(prefix).strip()
                    if not (emp_id.lower().startswith(f"{prefix.lower()}-") or emp_id.lower() == prefix.lower()):
                        emp_id = f"{prefix}-{emp_id}"

                # Extract Email
                retrieved_email = None
                for key in ['email', 'email_address', 'official_email', 'personal_email']:
                    if key in data and data[key]:
                        retrieved_email = str(data[key]).strip()
                        break
                if not retrieved_email:
                    for parent_key in ['user', 'employee', 'data', 'profile']:
                        if parent_key in data and isinstance(data[parent_key], dict):
                            parent_data = data[parent_key]
                            for key in ['email', 'email_address', 'official_email', 'personal_email']:
                                if key in parent_data and parent_data[key]:
                                    retrieved_email = str(parent_data[key]).strip()
                                    break
                            if retrieved_email:
                                break

                # Extract full name
                full_name = ""
                login_username = data.get('username') or ""
                if login_username and '@' not in login_username and not any(char.isdigit() for char in login_username):
                    full_name = login_username.strip()

                if not full_name:
                    for key in ['name', 'full_name', 'employee_name', 'emp_name', 'display_name', 'displayName', 'fullName']:
                        if key in data and data[key]:
                            full_name = str(data[key]).strip()
                            break
                if not full_name:
                    for parent_key in ['user', 'employee', 'data', 'profile']:
                        if parent_key in data and isinstance(data[parent_key], dict):
                            parent_data = data[parent_key]
                            for key in ['name', 'full_name', 'employee_name', 'emp_name', 'display_name', 'displayName', 'fullName']:
                                if key in parent_data and parent_data[key]:
                                    full_name = str(parent_data[key]).strip()
                                    break
                            if full_name:
                                break

                username_to_use = emp_id if emp_id else email
                email_to_use = retrieved_email if retrieved_email else (email if '@' in email else '')

                user, created = User.objects.get_or_create(username=username_to_use, defaults={'email': email_to_use})
                
                # Get or create UserProfile
                profile, p_created = UserProfile.objects.get_or_create(user=user)
                if p_created:
                    profile.emp_id = emp_id or username_to_use
                    if user.is_superuser:
                        profile.role, _ = Role.objects.get_or_create(name='admin')
                        profile.is_approved = True
                        profile.approval_status = 'approved'
                    else:
                        profile.role, _ = Role.objects.get_or_create(name='hr')
                        profile.is_approved = False
                        profile.approval_status = 'pending'
                    profile.save()

                # Update user fields
                needs_save = False
                if full_name:
                    parts = full_name.split(' ', 1)
                    first = parts[0]
                    last = parts[1] if len(parts) > 1 else ""
                    if user.first_name != first or user.last_name != last:
                        user.first_name = first
                        user.last_name = last
                        needs_save = True
                
                if email_to_use and user.email != email_to_use:
                    user.email = email_to_use
                    needs_save = True

                if needs_save:
                    user.save()

                # Verify approval status
                if not user.is_superuser and profile.approval_status == 'rejected':
                    messages.error(request, "Your account request was rejected by an administrator.")
                    return render(request, 'grievances/login.html')
                elif not user.is_superuser and (not profile.is_approved or profile.approval_status == 'pending'):
                    messages.success(request, "Your account is pending admin approval. Please wait for an administrator to approve your access.")
                    return render(request, 'grievances/login.html', {
                        'show_pending_popup': True,
                        'popup_user': user,
                    })

                # Store credentials in Cache for 7 days
                try:
                    redis_cred_data = {
                        'user_id': user.id,
                        'username': user.username,
                        'password_hash': make_password(password),
                    }
                    cache_ttl = 7 * 86400  # 7 days
                    
                    if email:
                        cache.set(f"stylehr_cred:{email.strip().lower()}", redis_cred_data, timeout=cache_ttl)
                    if user.username:
                        cache.set(f"stylehr_cred:{user.username.strip().lower()}", redis_cred_data, timeout=cache_ttl)
                    if user.email:
                        cache.set(f"stylehr_cred:{user.email.strip().lower()}", redis_cred_data, timeout=cache_ttl)
                    if '-' in user.username:
                        code_part = user.username.split('-', 1)[1]
                        cache.set(f"stylehr_cred:{code_part.strip().lower()}", redis_cred_data, timeout=cache_ttl)
                except Exception:
                    pass

                auth_login(request, user)
                user_authenticated = True
        except Exception:
            pass

        # 2. Fallback: Check Redis/local cache if API failed or user not authenticated via API
        if not user_authenticated:
            try:
                clean_input = email.strip().lower() if email else ''
                cached_cred = cache.get(f"stylehr_cred:{clean_input}")
                
                if not cached_cred and clean_input:
                    local_u = User.objects.filter(
                        Q(email__iexact=clean_input) | 
                        Q(username__iexact=clean_input) | 
                        Q(username__iendswith=f"-{clean_input}")
                    ).first()
                    
                    if local_u:
                        cached_cred = (
                            cache.get(f"stylehr_cred:{local_u.username.lower()}") or
                            (cache.get(f"stylehr_cred:{local_u.email.lower()}") if local_u.email else None)
                        )

                if cached_cred and check_password(password, cached_cred['password_hash']):
                    local_user = User.objects.filter(id=cached_cred['user_id']).first()
                    if local_user:
                        local_profile = getattr(local_user, 'profile', None)
                        if not local_user.is_superuser and local_profile and local_profile.approval_status == 'rejected':
                            messages.error(request, "Your account request was rejected by an administrator.")
                            return render(request, 'grievances/login.html')
                        elif not local_user.is_superuser and (not local_profile or not local_profile.is_approved or local_profile.approval_status == 'pending'):
                            messages.success(request, "Your account is pending admin approval. Please wait for an administrator to approve your access.")
                            return render(request, 'grievances/login.html', {
                                'show_pending_popup': True,
                                'popup_user': local_user,
                            })

                        auth_login(request, local_user)
                        user_authenticated = True
            except Exception:
                pass

        # 3. Fallback: Check local Django database users & superusers
        if not user_authenticated:
            user = authenticate(request, username=email, password=password)
            if user is None:
                local_u = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).first()
                if local_u:
                    user = authenticate(request, username=local_u.username, password=password)

            if user is not None:
                user_profile = getattr(user, 'profile', None)
                if not user.is_superuser and user_profile and user_profile.approval_status == 'rejected':
                    messages.error(request, "Your account request was rejected by an administrator.")
                    return render(request, 'grievances/login.html')
                elif not user.is_superuser and (not user_profile or not user_profile.is_approved or user_profile.approval_status == 'pending'):
                    messages.success(request, "Your account is pending admin approval. Please wait for an administrator to approve your access.")
                    return render(request, 'grievances/login.html', {
                        'show_pending_popup': True,
                        'popup_user': user,
                    })

                auth_login(request, user)
                user_authenticated = True

        if user_authenticated:
            request.session.set_expiry(0)  # Browser close
            messages.success(request, f"Welcome back, {request.user.get_full_name() or request.user.username}!")
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username/email or password.")

    # For GET requests, clear leftover session messages
    storage = messages.get_messages(request)
    for _ in storage:
        pass

    return render(request, 'grievances/login.html', {
        'next': request.GET.get('next', '')
    })


def pending_approval_view(request):
    pending_user = None
    if request.user.is_authenticated:
        pending_user = request.user
        auth_logout(request)
    return render(request, 'grievances/login.html', {
        'show_pending_popup': True,
        'popup_user': pending_user,
    })


def logout_view(request):
    auth_logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


def get_user_grievance_queryset(user):
    """
    Returns grievances scoped by user role:
    - Superuser / Admin (role.name == 'admin'): ALL records across all stores.
    - HR (role.name == 'hr'): Records for their assigned stores. If no stores assigned, NO records.
    """
    qs = Grievance.objects.select_related('store', 'enquiry_type', 'created_by')
    if user.is_superuser:
        return qs

    profile = getattr(user, 'profile', None)
    if profile and profile.is_admin:
        return qs

    if profile and profile.role and profile.role.name.lower() == 'hr':
        assigned_stores = profile.stores.all()
        if assigned_stores.exists():
            return qs.filter(store__in=assigned_stores)

    # If role is neither admin nor hr (or HR has no stores), return none
    return qs.none()


@approved_user_required
def dashboard_view(request):
    qs = get_user_grievance_queryset(request.user)
        
    total_count = qs.count()
    open_count = qs.filter(current_status='open').count()
    hold_count = qs.filter(current_status='hold').count()
    extension_count = qs.filter(current_status='extension').count()
    closed_count = qs.filter(current_status='closed').count()

    # Chart 1: By Status
    status_counts = qs.values('current_status').annotate(count=Count('id'))
    choices_dict = dict(Grievance.STATUS_CHOICES)
    status_labels = [choices_dict.get(item['current_status'], item['current_status']) for item in status_counts]
    status_data = [item['count'] for item in status_counts]
    
    # Chart 2: By Store
    store_counts = qs.filter(store__isnull=False).values('store__name').annotate(count=Count('id')).order_by('-count')[:8]
    store_labels = [item['store__name'] for item in store_counts]
    store_data = [item['count'] for item in store_counts]

    # Chart 3: By Enquiry Type / Category (Top 15 Categories)
    type_counts = qs.filter(enquiry_type__isnull=False).values('enquiry_type__name').annotate(count=Count('id')).order_by('-count')[:15]
    type_labels = [item['enquiry_type__name'] for item in type_counts]
    type_data = [item['count'] for item in type_counts]

    # Chart 4: Timeline / Inflow Trend (Day, Week, Month)
    dates_qs = qs.values('open_date').annotate(count=Count('id')).order_by('open_date')
    
    day_dict = OrderedDict()
    for item in dates_qs:
        d = item['open_date']
        if d:
            day_str = d.strftime("%Y-%m-%d")
            day_dict[day_str] = day_dict.get(day_str, 0) + item['count']
    day_labels = list(day_dict.keys())
    day_data = list(day_dict.values())

    week_dict = OrderedDict()
    for item in dates_qs:
        d = item['open_date']
        if d:
            start_of_week = d - timedelta(days=d.weekday())
            week_str = start_of_week.strftime("%Y-%m-%d")
            week_dict[week_str] = week_dict.get(week_str, 0) + item['count']
    week_labels = list(week_dict.keys())
    week_data = list(week_dict.values())

    month_dict = OrderedDict()
    for item in dates_qs:
        d = item['open_date']
        if d:
            month_str = d.strftime("%b %Y")
            month_dict[month_str] = month_dict.get(month_str, 0) + item['count']
    month_labels = list(month_dict.keys())
    month_data = list(month_dict.values())

    trend_datasets = {
        'day': {'labels': day_labels, 'data': day_data, 'title': 'Daily Grievances Volume Trend', 'subtitle': 'Last 30 Active Days'},
        'week': {'labels': week_labels, 'data': week_data, 'title': 'Weekly Grievances Volume Trend', 'subtitle': 'Weekly Inflow Trend'},
        'month': {'labels': month_labels, 'data': month_data, 'title': 'Monthly Grievances Volume Trend', 'subtitle': 'Monthly Historical Trend'}
    }


    colors = [
        {'gradient': 'from-indigo-500 to-indigo-700', 'shadow': 'shadow-indigo-500/30', 'text': 'text-indigo-100'},
        {'gradient': 'from-rose-500 to-rose-600', 'shadow': 'shadow-rose-500/30', 'text': 'text-rose-100'},
        {'gradient': 'from-amber-400 to-amber-500', 'shadow': 'shadow-amber-500/30', 'text': 'text-amber-100'},
        {'gradient': 'from-purple-500 to-purple-600', 'shadow': 'shadow-purple-500/30', 'text': 'text-purple-100'},
        {'gradient': 'from-emerald-400 to-emerald-500', 'shadow': 'shadow-emerald-500/30', 'text': 'text-emerald-100'},
    ]
    import random
    random.shuffle(colors)
    context = {

        'total_count': total_count,
        'open_count': open_count,
        'hold_count': hold_count,
        'extension_count': extension_count,
        'closed_count': closed_count,
        'status_labels': status_labels,
        'status_data': status_data,
        'store_labels': store_labels,
        'store_data': store_data,
        'type_labels': type_labels,
        'type_data': type_data,
        'trend_datasets_json': json.dumps(trend_datasets),
        'day_labels': day_labels,
        'day_data': day_data,
        'kpi_colors': colors,
    }
    return render(request, 'grievances/dashboard.html', context)


@approved_user_required
def grievance_create_view(request):
    if request.method == 'POST':
        form = GrievanceForm(request.POST, user=request.user)
        if form.is_valid():
            grievance = form.save(commit=False)
            grievance.created_by = request.user
            grievance.save()
            messages.success(request, 'Grievance created successfully!')
            return redirect('grievance_create')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GrievanceForm(user=request.user)
        
    return render(request, 'grievances/form.html', {'form': form})


@approved_user_required
def grievance_list_view(request):
    queryset = get_user_grievance_queryset(request.user)
    
    # Get filter parameters
    status = request.GET.get('status')
    store_id = request.GET.get('store')
    enquiry_type_id = request.GET.get('enquiry_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    emp_id = request.GET.get('emp_id')
    
    # Apply filters
    if status:
        queryset = queryset.filter(current_status=status)
    if store_id:
        queryset = queryset.filter(store_id=store_id)
    if enquiry_type_id:
        queryset = queryset.filter(enquiry_type_id=enquiry_type_id)
    if start_date:
        queryset = queryset.filter(open_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(open_date__lte=end_date)
    if emp_id:
        queryset = queryset.filter(emp_id__icontains=emp_id)

    # Handle Export
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="grievances.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'S.No', 'Open Date', 'Emp ID', 'Emp Name', 'Designation', 'Department', 'Section', 'Store Name', 
            'Enquiry Type', 'Enquiry Received By', 'Enquiry Details', '1st Level', '2nd Level',
            'Closed Date', 'Period Days', 'Created By', 'Created At', 'Current Status'
        ])
        
        for i, g in enumerate(queryset):
            writer.writerow([
                i+1, g.open_date, g.emp_id, g.emp_name, g.designation, g.department, g.section, 
                g.store.name if g.store else '', 
                g.enquiry_type.name if g.enquiry_type else '',
                g.enquiry_received_by,
                g.enquiry_details,
                g.first_level,
                g.second_level,
                g.closed_date,
                g.period_days,
                g.created_by.username if g.created_by else '',
                g.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                g.get_current_status_display()
            ])
        return response

    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    # Accessible stores for filter dropdown
    stores_qs = Store.objects.filter(is_active=True)
    if not request.user.is_superuser:
        profile = getattr(request.user, 'profile', None)
        if profile and not profile.is_admin:
            role_name = profile.role.name.lower() if profile.role else 'hr'
            if role_name == 'hr' and profile.stores.exists():
                stores_qs = profile.stores.filter(is_active=True)
            else:
                stores_qs = Store.objects.none()


    colors = [
        {'gradient': 'from-indigo-500 to-indigo-700', 'shadow': 'shadow-indigo-500/30', 'text': 'text-indigo-100'},
        {'gradient': 'from-rose-500 to-rose-600', 'shadow': 'shadow-rose-500/30', 'text': 'text-rose-100'},
        {'gradient': 'from-amber-400 to-amber-500', 'shadow': 'shadow-amber-500/30', 'text': 'text-amber-100'},
        {'gradient': 'from-purple-500 to-purple-600', 'shadow': 'shadow-purple-500/30', 'text': 'text-purple-100'},
        {'gradient': 'from-emerald-400 to-emerald-500', 'shadow': 'shadow-emerald-500/30', 'text': 'text-emerald-100'},
    ]
    import random
    random.shuffle(colors)
    context = {

        'grievances': page_obj,
        'stores': stores_qs,
        'enquiry_types': EnquiryType.objects.filter(is_active=True),
        'status_choices': Grievance.STATUS_CHOICES,
        'filters': request.GET,
        'query_string': query_params.urlencode(),
    }
    return render(request, 'grievances/list.html', context)


@approved_user_required
def grievance_update_view(request, pk):
    qs = get_user_grievance_queryset(request.user)
    grievance = get_object_or_404(qs, pk=pk)
    
    if request.method == 'POST':
        form = GrievanceForm(request.POST, instance=grievance, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Grievance updated successfully!')
            return redirect('grievance_list')
    else:
        form = GrievanceForm(instance=grievance, user=request.user)
        
    return render(request, 'grievances/form.html', {'form': form, 'is_edit': True})


@approved_user_required
def grievance_delete_view(request, pk):
    profile = getattr(request.user, 'profile', None)
    is_admin = request.user.is_superuser or (profile and profile.is_admin)
    if not is_admin:
        messages.error(request, 'You do not have permission to delete records.')
        return redirect('grievance_list')
        
    grievance = get_object_or_404(Grievance, pk=pk)
    grievance.delete()
    messages.success(request, 'Grievance deleted successfully!')
    return redirect('grievance_list')


# ==========================================
# USER MANAGEMENT VIEWS (Admin Only)
# ==========================================

@admin_required
def user_list_view(request):
    queryset = User.objects.select_related('profile').prefetch_related('profile__stores').order_by('-date_joined')

    # Summary Metrics
    total_users = queryset.count()
    pending_users = UserProfile.objects.filter(approval_status='pending').count()
    approved_users = UserProfile.objects.filter(approval_status='approved').count()
    admin_users = User.objects.filter(Q(is_superuser=True) | Q(profile__role__name__iexact='admin')).distinct().count()

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__emp_id__icontains=search_query)
        )

    # Filter: Role
    role_filter = request.GET.get('role')
    if role_filter:
        queryset = queryset.filter(profile__role__name__iexact=role_filter)

    # Filter: Status
    status_filter = request.GET.get('status')
    if status_filter:
        queryset = queryset.filter(profile__approval_status=status_filter)

    # Pagination
    paginator = Paginator(queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']


    colors = [
        {'gradient': 'from-indigo-500 to-indigo-700', 'shadow': 'shadow-indigo-500/30', 'text': 'text-indigo-100'},
        {'gradient': 'from-rose-500 to-rose-600', 'shadow': 'shadow-rose-500/30', 'text': 'text-rose-100'},
        {'gradient': 'from-amber-400 to-amber-500', 'shadow': 'shadow-amber-500/30', 'text': 'text-amber-100'},
        {'gradient': 'from-purple-500 to-purple-600', 'shadow': 'shadow-purple-500/30', 'text': 'text-purple-100'},
        {'gradient': 'from-emerald-400 to-emerald-500', 'shadow': 'shadow-emerald-500/30', 'text': 'text-emerald-100'},
    ]
    import random
    random.shuffle(colors)
    context = {

        'users': page_obj,
        'total_users': total_users,
        'pending_users': pending_users,
        'approved_users': approved_users,
        'admin_users': admin_users,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'roles': Role.objects.all(),
        'query_string': query_params.urlencode(),
    }
    return render(request, 'grievances/users/user_list.html', context)


@admin_required
def user_create_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            stores_count = user.profile.stores.count()
            messages.success(request, f"User '{user.username}' created successfully with {stores_count} assigned store(s)!")
            return redirect('user_list')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'grievances/users/user_form.html', {
        'form': form,
        'is_edit': False,
        'all_stores': Store.objects.filter(is_active=True),
    })


@admin_required
def user_update_view(request, pk):
    target_user = get_object_or_404(User.objects.select_related('profile').prefetch_related('profile__stores'), pk=pk)
    is_approving = request.GET.get('approve') == '1'

    if request.method == 'POST':
        form = CustomUserEditForm(request.POST, target_user=target_user)
        if form.is_valid():
            user = form.save()
            stores_names = ", ".join([s.name for s in user.profile.stores.all()]) or "None"
            if is_approving or user.profile.approval_status == 'approved':
                messages.success(request, f"User '{user.username}' approved and assigned to store(s): {stores_names}!")
            else:
                messages.success(request, f"User '{user.username}' updated successfully!")
            return redirect('user_list')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = CustomUserEditForm(target_user=target_user, is_approving=is_approving)

    return render(request, 'grievances/users/user_form.html', {
        'form': form,
        'target_user': target_user,
        'is_edit': True,
        'is_approving': is_approving,
        'all_stores': Store.objects.filter(is_active=True),
    })


@admin_required
def user_action_view(request, pk, action):
    target_user = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if action == 'approve':
        # When approving a user, open the edit page to assign role and multiple stores!
        return redirect(f"/users/{target_user.pk}/edit/?approve=1")
    elif action == 'reject':
        profile.is_approved = False
        profile.approval_status = 'rejected'
        profile.save()
        messages.warning(request, f"User '{target_user.username}' has been rejected.")
    elif action == 'reset_pending':
        profile.is_approved = False
        profile.approval_status = 'pending'
        profile.save()
        messages.info(request, f"User '{target_user.username}' status set to pending.")
    else:
        messages.error(request, "Invalid action.")

    redirect_url = request.META.get('HTTP_REFERER') or 'user_list'
    return redirect(redirect_url)


@admin_required
def user_delete_view(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    
    if target_user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('user_list')

    username = target_user.username
    target_user.delete()
    messages.success(request, f"User '{username}' deleted successfully.")
    return redirect('user_list')
