import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum, Q, Count
from django.http import HttpResponse

from grievances.views import approved_user_required, admin_required
from .models import FoodWasteStore, FoodWasteEntry
from .forms import FoodWasteForm


def is_user_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.is_admin)


def get_user_food_waste_queryset(user):
    """
    Returns food waste records scoped by user role:
    - Superuser / Admin (role.name == 'admin'): ALL records across all stores.
    - Regular users: Only their OWN records (created_by=user).
    """
    qs = FoodWasteEntry.objects.select_related('store', 'created_by')
    if is_user_admin(user):
        return qs
    return qs.filter(created_by=user)


@approved_user_required
def food_waste_create_view(request):
    if request.method == 'POST':
        form = FoodWasteForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.created_by = request.user
            entry.save()
            messages.success(request, f'Food waste log for {entry.store.name} ({entry.month}) recorded successfully!')
            return redirect('food_waste_create')
        else:
            messages.error(request, 'Please check the form and correct the errors below.')
    else:
        form = FoodWasteForm(user=request.user)

    return render(request, 'food_waste/form.html', {
        'form': form,
        'is_edit': False,
    })


@approved_user_required
def food_waste_edit_view(request, pk):
    qs = get_user_food_waste_queryset(request.user)
    entry = get_object_or_404(qs, pk=pk)

    if request.method == 'POST':
        form = FoodWasteForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            saved_entry = form.save(commit=False)
            if not saved_entry.created_by:
                saved_entry.created_by = entry.created_by or request.user
            saved_entry.save()
            messages.success(request, f'Food waste log #{entry.id} updated successfully!')
            return redirect('food_waste_list')
        else:
            messages.error(request, 'Please check the form and correct the errors below.')
    else:
        form = FoodWasteForm(instance=entry, user=request.user)

    return render(request, 'food_waste/form.html', {
        'form': form,
        'entry': entry,
        'is_edit': True,
    })


@approved_user_required
def food_waste_list_view(request):
    queryset = get_user_food_waste_queryset(request.user)

    # Filter parameters
    store_id = request.GET.get('store')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    month = request.GET.get('month')
    shortage = request.GET.get('shortage')

    if store_id:
        queryset = queryset.filter(store_id=store_id)
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    if month:
        queryset = queryset.filter(month=month)
    if shortage == 'yes':
        queryset = queryset.filter(
            Q(breakfast_shortage='yes') | Q(lunch_shortage='yes') | Q(dinner_shortage='yes')
        )

    # CSV Export
    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="food_waste_records_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Store', 'Date', 'Month',
            # Breakfast
            'Breakfast Menu', 'Breakfast Received (kg)', 'Breakfast Wastage (kg)', 'Breakfast Shortage', 'Breakfast Shortage Count', 'Breakfast Review', 'Breakfast Remarks',
            # Lunch
            'Lunch Menu', 'Lunch Received (kg)', 'Lunch Wastage (kg)', 'Lunch Shortage', 'Lunch Shortage Count', 'Lunch Review', 'Lunch Remarks',
            # Dinner
            'Dinner Menu', 'Dinner Received (kg)', 'Dinner Wastage (kg)', 'Dinner Shortage', 'Dinner Shortage Count', 'Dinner Review', 'Dinner Remarks',
            # Totals
            'Total Received (kg)', 'Total Wastage (kg)', 'Wastage %', 'Created By', 'Created At'
        ])

        for entry in queryset:
            writer.writerow([
                entry.id,
                entry.store.name if entry.store else '',
                entry.date,
                entry.month,
                # Breakfast
                entry.breakfast_menu,
                entry.breakfast_received_kg or 0,
                entry.breakfast_wastage_kg or 0,
                entry.get_breakfast_shortage_display(),
                entry.breakfast_shortage_count or 0,
                entry.get_breakfast_review_display(),
                entry.breakfast_remarks,
                # Lunch
                entry.lunch_menu,
                entry.lunch_received_kg or 0,
                entry.lunch_wastage_kg or 0,
                entry.get_lunch_shortage_display(),
                entry.lunch_shortage_count or 0,
                entry.get_lunch_review_display(),
                entry.lunch_remarks,
                # Dinner
                entry.dinner_menu,
                entry.dinner_received_kg or 0,
                entry.dinner_wastage_kg or 0,
                entry.get_dinner_shortage_display(),
                entry.dinner_shortage_count or 0,
                entry.get_dinner_review_display(),
                entry.dinner_remarks,
                # Totals
                entry.total_received_kg,
                entry.total_wastage_kg,
                f"{entry.wastage_percentage}%",
                entry.created_by.username if entry.created_by else '',
                entry.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
        return response

    # Metrics calculation
    total_logs = queryset.count()
    aggregates = queryset.aggregate(
        b_recv=Sum('breakfast_received_kg'),
        l_recv=Sum('lunch_received_kg'),
        d_recv=Sum('dinner_received_kg'),
        b_waste=Sum('breakfast_wastage_kg'),
        l_waste=Sum('lunch_wastage_kg'),
        d_waste=Sum('dinner_wastage_kg'),
    )

    total_received = (aggregates['b_recv'] or 0) + (aggregates['l_recv'] or 0) + (aggregates['d_recv'] or 0)
    total_wastage = (aggregates['b_waste'] or 0) + (aggregates['l_waste'] or 0) + (aggregates['d_waste'] or 0)
    wastage_pct = round((total_wastage / total_received) * 100, 1) if total_received > 0 else 0.0

    shortage_incidents = queryset.filter(
        Q(breakfast_shortage='yes') | Q(lunch_shortage='yes') | Q(dinner_shortage='yes')
    ).count()

    # Page size
    per_page = request.GET.get('per_page', '50')
    try:
        per_page = int(per_page)
        if per_page not in [10, 15, 25, 50, 100]:
            per_page = 15
    except (ValueError, TypeError):
        per_page = 15

    # Pagination
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    # Separate Food Waste Stores for filter dropdown
    stores = FoodWasteStore.objects.filter(is_active=True).order_by('name')

    return render(request, 'food_waste/list.html', {
        'page_obj': page_obj,
        'query_string': query_params.urlencode(),
        'per_page': per_page,
        'total_logs': total_logs,
        'total_received': total_received,
        'total_wastage': total_wastage,
        'wastage_pct': wastage_pct,
        'shortage_incidents': shortage_incidents,
        'stores': stores,
        'months': FoodWasteEntry.MONTH_CHOICES,
        'selected_store': store_id,
        'start_date': start_date,
        'end_date': end_date,
        'month': month,
        'shortage': shortage,
    })


@approved_user_required
def food_waste_delete_view(request, pk):
    qs = get_user_food_waste_queryset(request.user)
    entry = get_object_or_404(qs, pk=pk)

    # Permission check: admin or the user who created it
    is_admin = request.user.is_superuser or (
        hasattr(request.user, 'profile') and request.user.profile.is_admin
    )
    if not is_admin and entry.created_by != request.user:
        messages.error(request, "You do not have permission to delete this food waste entry.")
        return redirect('food_waste_list')

    if request.method == 'POST':
        entry_store = entry.store.name
        entry_date = entry.date
        entry.delete()
        messages.success(request, f"Food waste entry for {entry_store} on {entry_date} was deleted.")
        return redirect('food_waste_list')

    return render(request, 'food_waste/delete_confirm.html', {'entry': entry})


@admin_required
def food_waste_report_view(request):
    qs = get_user_food_waste_queryset(request.user)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    month = request.GET.get('month')
    store_id = request.GET.get('store')

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if month:
        qs = qs.filter(month=month)

    all_stores = FoodWasteStore.objects.filter(is_active=True).order_by('name')
    if store_id:
        qs = qs.filter(store_id=store_id)
        stores_list = list(all_stores.filter(id=store_id))
    else:
        stores_list = list(all_stores)

    store_rows = []
    grand_totals = {
        'entries': 0,
        'b_recv': 0.0,
        'b_waste': 0.0,
        'l_recv': 0.0,
        'l_waste': 0.0,
        'd_recv': 0.0,
        'd_waste': 0.0,
        'total_recv': 0.0,
        'total_waste': 0.0,
        'shortages': 0,
    }

    for idx, st in enumerate(stores_list, 1):
        store_qs = qs.filter(store=st)
        agg = store_qs.aggregate(
            cnt=Count('id'),
            b_recv=Sum('breakfast_received_kg'),
            b_waste=Sum('breakfast_wastage_kg'),
            l_recv=Sum('lunch_received_kg'),
            l_waste=Sum('lunch_wastage_kg'),
            d_recv=Sum('dinner_received_kg'),
            d_waste=Sum('dinner_wastage_kg'),
            b_short=Sum('breakfast_shortage_count'),
            l_short=Sum('lunch_shortage_count'),
            d_short=Sum('dinner_shortage_count'),
        )

        cnt = agg['cnt'] or 0
        b_r = float(agg['b_recv'] or 0)
        b_w = float(agg['b_waste'] or 0)
        l_r = float(agg['l_recv'] or 0)
        l_w = float(agg['l_waste'] or 0)
        d_r = float(agg['d_recv'] or 0)
        d_w = float(agg['d_waste'] or 0)
        t_r = b_r + l_r + d_r
        t_w = b_w + l_w + d_w
        pct = round((t_w / t_r) * 100, 1) if t_r > 0 else 0.0
        short = (agg['b_short'] or 0) + (agg['l_short'] or 0) + (agg['d_short'] or 0)

        grand_totals['entries'] += cnt
        grand_totals['b_recv'] += b_r
        grand_totals['b_waste'] += b_w
        grand_totals['l_recv'] += l_r
        grand_totals['l_waste'] += l_w
        grand_totals['d_recv'] += d_r
        grand_totals['d_waste'] += d_w
        grand_totals['total_recv'] += t_r
        grand_totals['total_waste'] += t_w
        grand_totals['shortages'] += short

        store_rows.append({
            'index': idx,
            'store': st,
            'cnt': cnt,
            'b_recv': b_r,
            'b_waste': b_w,
            'l_recv': l_r,
            'l_waste': l_w,
            'd_recv': d_r,
            'd_waste': d_w,
            'total_recv': t_r,
            'total_waste': t_w,
            'wastage_pct': pct,
            'shortage_count': short,
        })

    grand_totals['wastage_pct'] = (
        round((grand_totals['total_waste'] / grand_totals['total_recv']) * 100, 1)
        if grand_totals['total_recv'] > 0 else 0.0
    )

    if request.GET.get('export') == 'excel':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="food_waste_store_matrix_{datetime.now().strftime("%Y%m%d_%H%M")}.csv"'
        writer = csv.writer(response)

        writer.writerow([
            'S.No', 'Particulars (Store Name)',
            'Breakfast Recv (kg)', 'Breakfast Waste (kg)',
            'Lunch Recv (kg)', 'Lunch Waste (kg)',
            'Dinner Recv (kg)', 'Dinner Waste (kg)',
            'Total Recv (kg)', 'Total Wastage (kg)',
            'Wastage Rate %', 'Shortages'
        ])

        for row in store_rows:
            writer.writerow([
                row['index'], row['store'].name,
                row['b_recv'], row['b_waste'],
                row['l_recv'], row['l_waste'],
                row['d_recv'], row['d_waste'],
                row['total_recv'], row['total_waste'],
                f"{row['wastage_pct']}%", row['shortage_count']
            ])

        writer.writerow([
            '', 'Grand Total',
            grand_totals['b_recv'], grand_totals['b_waste'],
            grand_totals['l_recv'], grand_totals['l_waste'],
            grand_totals['d_recv'], grand_totals['d_waste'],
            grand_totals['total_recv'], grand_totals['total_waste'],
            f"{grand_totals['wastage_pct']}%", grand_totals['shortages']
        ])
        return response

    return render(request, 'food_waste/report.html', {
        'store_rows': store_rows,
        'grand_totals': grand_totals,
        'all_stores': all_stores,
        'months': FoodWasteEntry.MONTH_CHOICES,
        'selected_store': store_id,
        'start_date': start_date,
        'end_date': end_date,
        'month': month,
    })

