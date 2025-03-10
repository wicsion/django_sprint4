from django.urls import path, include
from .views import (
    register, create_post, edit_post, delete_post, add_comment,
    index, category_posts, post_detail, profile_view,
    profile_redirect, edit_comment, delete_comment
)

app_name = 'blog'

urlpatterns = [
    path('', index, name='index'),
    path('category/<slug:slug>/', category_posts, name='category_posts'),
    path('posts/<int:pk>/', post_detail, name='post_detail'),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', register, name='registration'),
    path('posts/create/', create_post, name='create_post'),
    path('posts/<int:pk>/edit/', edit_post, name='edit_post'),
    path('posts/<int:pk>/delete/', delete_post, name='delete_post'),
    path('posts/<int:pk>/comment/', add_comment, name='add_comment'),
    path('profile_redirect/', profile_redirect, name='profile_redirect'),
    path('profile/<str:username>/', profile_view, name='profile'),
    path('posts/<int:post_id>/comments/<int:comment_id>/edit/', edit_comment,
         name='edit_comment'),
    path('posts/<int:post_id>/comments/<int:comment_id>/delete/',
         delete_comment,
         name='delete_comment'),

]
