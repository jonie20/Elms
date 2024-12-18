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
    # path('add-employee', views.add_employee, name="add-employee"),
    path('manage-employee', views.manage_employee, name="manage-employee"),
    path('add-notice', views.add_notice, name="add-notice")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# +static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
