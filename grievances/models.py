from django.db import models
from django.contrib.auth.models import User

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Role(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Store(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
        
    def __str__(self):
        return self.name

class UserProfile(TimeStampedModel):

    APPROVAL_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    emp_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_approved = models.BooleanField(default=False)
    approval_status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='pending')
    stores = models.ManyToManyField(Store, blank=True, related_name='user_profiles')

    def __str__(self):
        role_name = self.role.name if self.role else 'No Role'
        return f"{self.user.username} ({role_name})"

    @property
    def is_admin(self):
        return self.user.is_superuser or (self.role and self.role.name.lower() == 'admin')

    def can_access_system(self):
        return self.user.is_superuser or (self.is_approved and self.approval_status == 'approved')

class EnquiryType(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Grievance(TimeStampedModel):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('hold', 'Hold'),
        ('extension', 'Extension'),
        ('closed', 'Closed'),
    ]

    open_date = models.DateField()
    emp_id = models.CharField(max_length=100)
    emp_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    section = models.CharField(max_length=255)
    
    store = models.ForeignKey(Store, on_delete=models.PROTECT, related_name='grievances')
    enquiry_type = models.ForeignKey(EnquiryType, on_delete=models.PROTECT, related_name='grievances')
    
    enquiry_received_by = models.CharField(max_length=255)
    enquiry_details = models.TextField()
    
    first_level = models.CharField(max_length=255, blank=True)
    second_level = models.CharField(max_length=255, blank=True)
    
    closed_date = models.DateField(null=True, blank=True)
    period_days = models.IntegerField(null=True, blank=True, help_text="Number of days taken to close")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_grievances')
    
    current_status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open',
        db_index=True
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['emp_id']),
            models.Index(fields=['open_date']),
            models.Index(fields=['current_status']),
        ]
        ordering = ['-open_date']
        
    def __str__(self):
        return f"{self.emp_id} - {self.emp_name} - {self.open_date}"
