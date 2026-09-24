from .models import UserProfile

def user_management_context(request):
    profile = getattr(request.user, 'profile', None)
    if request.user.is_authenticated and (request.user.is_superuser or (profile and profile.is_admin)):
        try:
            pending_count = UserProfile.objects.filter(approval_status='pending').count()
        except Exception:
            pending_count = 0
        return {
            'pending_users_count': pending_count
        }
    return {
        'pending_users_count': 0
    }
