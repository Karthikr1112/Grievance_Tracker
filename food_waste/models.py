from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def get_current_month():
    return timezone.localdate().strftime("%B")



class FoodWasteStore(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Store Name")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Food Waste Store"
        verbose_name_plural = "Food Waste Stores"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name


class FoodWasteEntry(models.Model):
    SHORTAGE_CHOICES = [
        ('no', 'No'),
        ('yes', 'Yes'),
    ]

    REVIEW_CHOICES = [
        ('not_good', 'Not Good'),
        ('good', 'Good'),
        ('excellent', 'Excellent'),
    ]

    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]

    store = models.ForeignKey(
        FoodWasteStore,
        on_delete=models.PROTECT,
        related_name='food_waste_entries',
        verbose_name="Store Name"
    )
    date = models.DateField(verbose_name="Date")
    month = models.CharField(
        max_length=20,
        choices=MONTH_CHOICES,
        default=get_current_month,
        verbose_name="Month"
    )

    # Breakfast
    breakfast_menu = models.CharField(max_length=500, blank=True, verbose_name="Breakfast Menu")
    breakfast_received_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Breakfast Received (kg)"
    )
    breakfast_wastage_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Breakfast Wastage (kg)"
    )
    breakfast_shortage = models.CharField(
        max_length=10, choices=SHORTAGE_CHOICES, default='no', verbose_name="Breakfast Shortage"
    )
    breakfast_shortage_count = models.IntegerField(
        null=True, blank=True, verbose_name="Breakfast Shortage Count"
    )
    breakfast_review = models.CharField(
        max_length=20, choices=REVIEW_CHOICES, blank=True, verbose_name="Breakfast Review"
    )
    breakfast_remarks = models.TextField(blank=True, verbose_name="Breakfast Remarks")

    # Lunch
    lunch_menu = models.CharField(max_length=500, blank=True, verbose_name="Lunch Menu")
    lunch_received_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Lunch Received (kg)"
    )
    lunch_wastage_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Lunch Wastage (kg)"
    )
    lunch_shortage = models.CharField(
        max_length=10, choices=SHORTAGE_CHOICES, default='no', verbose_name="Lunch Shortage"
    )
    lunch_shortage_count = models.IntegerField(
        null=True, blank=True, verbose_name="Lunch Shortage Count"
    )
    lunch_review = models.CharField(
        max_length=20, choices=REVIEW_CHOICES, blank=True, verbose_name="Lunch Review"
    )
    lunch_remarks = models.TextField(blank=True, verbose_name="Lunch Remarks")

    # Dinner
    dinner_menu = models.CharField(max_length=500, blank=True, verbose_name="Dinner Menu")
    dinner_received_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Dinner Received (kg)"
    )
    dinner_wastage_kg = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Dinner Wastage (kg)"
    )
    dinner_shortage = models.CharField(
        max_length=10, choices=SHORTAGE_CHOICES, default='no', verbose_name="Dinner Shortage"
    )
    dinner_shortage_count = models.IntegerField(
        null=True, blank=True, verbose_name="Dinner Shortage Count"
    )
    dinner_review = models.CharField(
        max_length=20, choices=REVIEW_CHOICES, blank=True, verbose_name="Dinner Review"
    )
    dinner_remarks = models.TextField(blank=True, verbose_name="Dinner Remarks")

    # Tracking & Audit
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='food_waste_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Food Waste Entry"
        verbose_name_plural = "Food Waste Entries"
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['store', 'date']),
        ]

    def save(self, *args, **kwargs):
        if self.date and not self.month:
            self.month = self.date.strftime("%B")
        elif not self.month:
            self.month = get_current_month()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.store.name} - {self.date} ({self.month})"

    @property
    def total_received_kg(self):
        total = 0
        if self.breakfast_received_kg:
            total += self.breakfast_received_kg
        if self.lunch_received_kg:
            total += self.lunch_received_kg
        if self.dinner_received_kg:
            total += self.dinner_received_kg
        return total

    @property
    def total_wastage_kg(self):
        total = 0
        if self.breakfast_wastage_kg:
            total += self.breakfast_wastage_kg
        if self.lunch_wastage_kg:
            total += self.lunch_wastage_kg
        if self.dinner_wastage_kg:
            total += self.dinner_wastage_kg
        return total

    @property
    def wastage_percentage(self):
        recv = self.total_received_kg
        waste = self.total_wastage_kg
        if recv and recv > 0:
            return round((waste / recv) * 100, 1)
        return 0.0
