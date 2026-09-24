from django import forms
from django.contrib.auth.models import User
from .models import Grievance, Store, EnquiryType, UserProfile, Role

class GrievanceForm(forms.ModelForm):
    class Meta:
        model = Grievance
        fields = [
            'open_date', 'emp_id', 'emp_name', 'designation', 'department', 'section',
            'store', 'enquiry_type', 'enquiry_received_by', 'enquiry_details',
            'first_level', 'second_level', 'closed_date', 'period_days', 'current_status'
        ]
        widgets = {
            'open_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
            }),
            'closed_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
            }),
            'enquiry_details': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Provide detailed facts, context, and specifics of the employee inquiry or complaint...',
                'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 p-4 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
            }),
            'emp_id': forms.TextInput(attrs={'placeholder': 'e.g. EMP-1048'}),
            'emp_name': forms.TextInput(attrs={'placeholder': 'e.g. John Doe'}),
            'designation': forms.TextInput(attrs={'placeholder': 'e.g. Senior Associate'}),
            'department': forms.TextInput(attrs={'placeholder': 'e.g. Operations / Logistics'}),
            'section': forms.TextInput(attrs={'placeholder': 'e.g. Customer Support'}),
            'enquiry_received_by': forms.TextInput(attrs={'placeholder': 'Name of officer or channel'}),
            'first_level': forms.TextInput(attrs={'placeholder': 'Assigned 1st level officer'}),
            'second_level': forms.TextInput(attrs={'placeholder': 'Escalated 2nd level authority'}),
            'period_days': forms.NumberInput(attrs={'placeholder': 'Days taken to resolve', 'min': 0}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        base_input_classes = 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = base_input_classes
                
        # Filter stores based on user permissions
        store_qs = Store.objects.filter(is_active=True)
        if user and not user.is_superuser:
            profile = getattr(user, 'profile', None)
            if profile and profile.role != 'admin':
                assigned = profile.stores.filter(is_active=True)
                # If user has assigned stores, restrict to them
                if assigned.exists():
                    store_qs = assigned
        
        self.fields['store'].queryset = store_qs
        self.fields['store'].empty_label = "Select Store / Location"
        self.fields['enquiry_type'].queryset = EnquiryType.objects.filter(is_active=True)
        self.fields['enquiry_type'].empty_label = "Select Category / Type"


class CustomUserCreationForm(forms.Form):
    username = forms.CharField(
        label="Username / Employee Code",
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 97-1048 or john.doe',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    emp_id = forms.CharField(
        label="Employee ID / Code",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 97-1048',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'employee@company.com',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    approval_status = forms.ChoiceField(
        choices=UserProfile.APPROVAL_CHOICES,
        initial='approved',
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    stores = forms.ModelMultipleChoiceField(
        queryset=Store.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'rounded text-indigo-600 focus:ring-indigo-500'}),
        required=False,
        help_text="Select one or multiple stores to assign to this user."
    )
    is_active = forms.BooleanField(initial=True, required=False)
    is_approved = forms.BooleanField(initial=True, required=False)
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Optional password for local login',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    confirm_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password or confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")

        status = cleaned_data.get('approval_status')
        if status == 'approved':
            cleaned_data['is_approved'] = True
        elif status in ['pending', 'rejected']:
            cleaned_data['is_approved'] = False

        return cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        email = self.cleaned_data.get('email', '')
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        password = self.cleaned_data.get('password')

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=self.cleaned_data.get('is_active', True)
        )
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        role = self.cleaned_data.get('role')
        if role and role.name.lower() == 'admin':
            user.is_staff = True

        user.save()

        # Create Profile
        profile = UserProfile.objects.create(
            user=user,
            emp_id=self.cleaned_data.get('emp_id') or username,
            role=self.cleaned_data.get('role'),
            is_approved=self.cleaned_data.get('is_approved', True),
            approval_status=self.cleaned_data.get('approval_status', 'approved')
        )
        stores = self.cleaned_data.get('stores')
        if stores:
            profile.stores.set(stores)

        return user


class CustomUserEditForm(forms.Form):
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'First Name',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last Name',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'placeholder': 'employee@company.com',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    emp_id = forms.CharField(
        label="Employee ID / Code",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 97-1048',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    approval_status = forms.ChoiceField(
        choices=UserProfile.APPROVAL_CHOICES,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        })
    )
    stores = forms.ModelMultipleChoiceField(
        queryset=Store.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'rounded text-indigo-600 focus:ring-indigo-500'}),
        required=False,
        help_text="Check the stores this user is assigned to."
    )
    is_active = forms.BooleanField(required=False)
    is_approved = forms.BooleanField(required=False)
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Leave blank to keep unchanged',
            'class': 'block w-full rounded-xl border border-gray-200 bg-gray-50/50 px-4 py-2.5 text-sm text-gray-800 transition focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 focus:outline-none'
        }),
        help_text="Optional: Enter a new password to reset."
    )

    def __init__(self, *args, target_user=None, is_approving=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = target_user
        if target_user:
            profile = getattr(target_user, 'profile', None)
            if not self.is_bound:
                self.fields['first_name'].initial = target_user.first_name
                self.fields['last_name'].initial = target_user.last_name
                self.fields['email'].initial = target_user.email
                self.fields['is_active'].initial = target_user.is_active
                if profile:
                    self.fields['emp_id'].initial = profile.emp_id
                    self.fields['role'].initial = profile.role
                    self.fields['stores'].initial = profile.stores.all()
                    if is_approving:
                        self.fields['approval_status'].initial = 'approved'
                        self.fields['is_approved'].initial = True
                    else:
                        self.fields['approval_status'].initial = profile.approval_status
                        self.fields['is_approved'].initial = profile.is_approved

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('approval_status')
        if status == 'approved':
            cleaned_data['is_approved'] = True
        elif status in ['pending', 'rejected']:
            cleaned_data['is_approved'] = False
        return cleaned_data

    def save(self):
        user = self.target_user
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data.get('email', '')
        user.is_active = self.cleaned_data.get('is_active', True)

        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)

        if self.cleaned_data.get('role') == 'admin':
            user.is_staff = True

        user.save()

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.emp_id = self.cleaned_data.get('emp_id')
        profile.role = self.cleaned_data.get('role', 'user')
        profile.approval_status = self.cleaned_data.get('approval_status')
        profile.is_approved = self.cleaned_data.get('is_approved')
        profile.save()

        stores = self.cleaned_data.get('stores')
        if stores is not None:
            profile.stores.set(stores)

        return user
