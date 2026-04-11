from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('browse/', views.browse_view, name='browse'),
    path('match/', views.match_view, name='match'),
    path('sessions/', views.sessions_view, name='sessions'),
    path('request-exchange/', views.request_exchange, name='request_exchange'),
    path('accept-exchange/<int:exchange_id>/', views.accept_exchange, name='accept_exchange'),
    path('reject-exchange/<int:exchange_id>/', views.reject_exchange, name='reject_exchange'),
    path('add-skill/', views.add_skill, name='add_skill'),
    path('remove-skill/<int:teach_id>/', views.remove_skill, name='remove_skill'),
    path('reschedule-session/', views.reschedule_session, name='reschedule_session'),
    path('save-meeting-link/', views.save_meeting_link, name='save_meeting_link'),
    path('send-notification/', views.send_notification, name='send_notification'),
    path('firebase-login/', views.firebase_login, name='firebase_login'),
    path('api/request-exchange/', api_views.api_request_exchange, name='api_request_exchange'),
    path('api/notifications/', api_views.api_notifications, name='api_notifications'),
    path('api/health/', api_views.api_health, name='api_health'),
    path('api/live-users/', api_views.api_live_users, name='api_live_users'),
    path('api/exchanges/<int:exchange_id>/schedule/', api_views.api_schedule_session, name='api_schedule_session'),
    path('api/available-skills/', api_views.api_available_skills, name='api_available_skills'),
]
