from django.urls import path
from django.contrib.auth import views as auth_views
from .import views

urlpatterns = [
    path('',views.home, name = 'home'),
    path('sessions/',views.session_list,name='session_list'),
    path('create/',views.create_session, name='create_session'),
    path('<int:pk>/edit/',views.update_sessions, name='update_session'),
    path('<int:pk>/delete',views.delete_session, name='delete_session'),
    path('sessions/export/',views.export_sessions,name='export_sessions'),
    path('sessions/<int:pk>/',views.session_detail,name='session_detail'),
    path('login/',auth_views.LoginView.as_view(template_name='login.html'),name='login'),
    path('logout/',auth_views.LogoutView.as_view(),name='logout'),
    path("goal/update/", views.update_goal, name="update_goal"),
]