from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='food_waste_create', permanent=False), name='food_waste_home'),
    path('add/', views.food_waste_create_view, name='food_waste_create'),
    path('records/', views.food_waste_list_view, name='food_waste_list'),
    path('<int:pk>/edit/', views.food_waste_edit_view, name='food_waste_edit'),
    path('<int:pk>/delete/', views.food_waste_delete_view, name='food_waste_delete'),
    path('reports/', views.food_waste_report_view, name='food_waste_report'),
]
