from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pending-approval/', views.pending_approval_view, name='pending_approval'),
    path('', views.dashboard_view, name='dashboard'),
    path('list/', views.grievance_list_view, name='grievance_list'),
    path('create/', views.grievance_create_view, name='grievance_create'),
    path('edit/<int:pk>/', views.grievance_update_view, name='grievance_update'),
    path('delete/<int:pk>/', views.grievance_delete_view, name='grievance_delete'),
    
    # User Management (Admin Only)
    path('users/', views.user_list_view, name='user_list'),
    path('users/create/', views.user_create_view, name='user_create'),
    path('users/<int:pk>/edit/', views.user_update_view, name='user_update'),
    path('users/<int:pk>/action/<str:action>/', views.user_action_view, name='user_action'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
]
