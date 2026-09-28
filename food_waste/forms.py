from django import forms
from django.utils import timezone
from .models import FoodWasteStore, FoodWasteEntry


class FoodWasteForm(forms.ModelForm):
    class Meta:
        model = FoodWasteEntry
        fields = [
            'store', 'date', 'month',
            # Breakfast
            'breakfast_menu', 'breakfast_received_kg', 'breakfast_wastage_kg',
            'breakfast_shortage', 'breakfast_shortage_count', 'breakfast_review', 'breakfast_remarks',
            # Lunch
            'lunch_menu', 'lunch_received_kg', 'lunch_wastage_kg',
            'lunch_shortage', 'lunch_shortage_count', 'lunch_review', 'lunch_remarks',
            # Dinner
            'dinner_menu', 'dinner_received_kg', 'dinner_wastage_kg',
            'dinner_shortage', 'dinner_shortage_count', 'dinner_review', 'dinner_remarks',
        ]
        widgets = {
            'store': forms.Select(attrs={
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'month': forms.Select(attrs={
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            # Breakfast
            'breakfast_menu': forms.TextInput(attrs={
                'placeholder': 'e.g. Idli, Vada, Chutney, Sambar',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_received_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-received block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_wastage_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-wastage block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_shortage': forms.Select(attrs={
                'class': 'shortage-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_shortage_count': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'Count / Persons',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_review': forms.Select(attrs={
                'class': 'review-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'breakfast_remarks': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Add review remarks, food quality feedback or observations...',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 p-3 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),

            # Lunch
            'lunch_menu': forms.TextInput(attrs={
                'placeholder': 'e.g. Rice, Dal, Veg Curry, Curd',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_received_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-received block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_wastage_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-wastage block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_shortage': forms.Select(attrs={
                'class': 'shortage-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_shortage_count': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'Count / Persons',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_review': forms.Select(attrs={
                'class': 'review-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'lunch_remarks': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Add review remarks, food quality feedback or observations...',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 p-3 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),

            # Dinner
            'dinner_menu': forms.TextInput(attrs={
                'placeholder': 'e.g. Chapathi, Paneer Masala, Rice',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_received_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-received block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_wastage_kg': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'class': 'meal-wastage block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_shortage': forms.Select(attrs={
                'class': 'shortage-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_shortage_count': forms.NumberInput(attrs={
                'min': '0',
                'placeholder': 'Count / Persons',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_review': forms.Select(attrs={
                'class': 'review-select block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
            'dinner_remarks': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Add review remarks, food quality feedback or observations...',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 p-3 text-sm text-gray-800 transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        base_input_classes = (
            'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 '
            'transition focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 focus:outline-none'
        )

        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = base_input_classes

        # Separate Food Waste Store queryset
        self.fields['store'].queryset = FoodWasteStore.objects.filter(is_active=True).order_by('name')
        self.fields['store'].empty_label = "Select Store / Location"

        # Month dropdown choices
        self.fields['month'].choices = FoodWasteEntry.MONTH_CHOICES

        # Review choices with blank prompt
        review_choices = [('', 'Select Review')] + list(FoodWasteEntry.REVIEW_CHOICES)
        self.fields['breakfast_review'].choices = review_choices
        self.fields['lunch_review'].choices = review_choices
        self.fields['dinner_review'].choices = review_choices

        # Default date and current month if new entry
        today = timezone.localdate()
        current_month = today.strftime("%B")  # e.g., "September"

        if not self.initial.get('date') and not (self.instance and self.instance.pk):
            self.initial['date'] = today

        if not self.initial.get('month') and not (self.instance and self.instance.pk):
            self.initial['month'] = current_month
