import accounts.views as aviews
from django.urls import path

app_name = 'accounts'
urlpatterns = [
    path('search/', aviews.UserList.as_view(), name='user-list'),
    path('create/', aviews.UserCreate.as_view(), name='user-create'),
    path('update/<uuid:user_uuid>/', aviews.UserUpdate.as_view(), name='user-update'),
    path('update/password/<uuid:user_uuid>/', aviews.UserUpdatePassword.as_view(), name='user-update-password'),
    path('delete/<uuid:user_uuid>/', aviews.UserDelete.as_view(), name='user-delete'),
    path('logs/', aviews.AccessLogs.as_view(), name='access-logs'),

]
