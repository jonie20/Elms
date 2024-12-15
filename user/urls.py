from django.conf.urls.static import static
from django.urls import path
from user.views import RegisterView, LoginView, LogoutView, DashView
from user import views
from django.conf import settings

urlpatterns = [
    path('register/',RegisterView.as_view(), name='register-view'),
    path('login/',LoginView.as_view(), name='login-view'),
    path('logout/',LogoutView.as_view(), name='logout-view'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('dash/', DashView.as_view(), name='dash'),

    path('leaveHistory', views.leavehistory, name='leaveHistory')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
