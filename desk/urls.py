from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views
urlpatterns = [path("",views.inbox,name="inbox"),path("ticket/<int:pk>/",views.ticket,name="ticket"),path("login/",LoginView.as_view(template_name="login.html")),path("logout/",LogoutView.as_view())]
