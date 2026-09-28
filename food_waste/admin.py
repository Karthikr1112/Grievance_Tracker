from django.contrib import admin
from .models import FoodWasteStore, FoodWasteEntry


@admin.register(FoodWasteStore)
class FoodWasteStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(FoodWasteEntry)
class FoodWasteEntryAdmin(admin.ModelAdmin):
    list_display = (
        'store',
        'date',
        'month',
        'total_received_kg',
        'total_wastage_kg',
        'wastage_percentage',
        'created_by',
        'created_at',
    )
    list_filter = ('store', 'date', 'month', 'breakfast_shortage', 'lunch_shortage', 'dinner_shortage')
    search_fields = ('store__name', 'date', 'month', 'breakfast_menu', 'lunch_menu', 'dinner_menu')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
