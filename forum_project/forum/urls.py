from django.urls import path
from . import views
from .views import PostCreateView, post_detail, register_view, login_view, profile_view
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('category/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('category/<int:pk>/', views.category_detail, name='category_detail'),
    path('category/<int:category_id>/post/add/', PostCreateView.as_view(), name='post_add'),
    path('post/<int:post_id>/', post_detail, name='post_detail'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
]