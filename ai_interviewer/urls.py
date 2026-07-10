from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('interview/<int:interview_id>/', views.interview_view, name='interview'),
    path('summary/<int:interview_id>/', views.summary_view, name='summary'),
    path('summary/<int:interview_id>/pdf/', views.export_pdf, name='export_pdf'),
    path('history/', views.history_view, name='history'),
]