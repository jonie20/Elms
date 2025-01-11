from django.conf.urls.static import static
from django.urls import path
from user.views import RegisterView, LoginView, LogoutView, DashView
from user import views
from django.conf import settings

urlpatterns = [
    path('add-employee/', RegisterView.as_view(), name='add-employee'),
    path('login/', LoginView.as_view(), name='login-view'),
    path('logout/', LogoutView.as_view(), name='logout-view'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('dash/', DashView.as_view(), name='dash'),
    path('leaveHistory', views.leavehistory, name='leaveHistory'),
    path('board/', views.board, name="dashboard"),
    path('huduma-centres', views.manage_centres, name="manage-centres"),
    path('manage-leaves', views.manage_leaves, name="manage-leaves"),
    path('manage-employee', views.manage_employee, name="manage-employee"),
    path('add-notice', views.add_notice, name="add-notice"),
    path('setpassword', views.set_pass, name="reset_pass"),
    path('update-leave/<int:pk>/', views.update_leave_status, name='update_leave_status'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# +static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
