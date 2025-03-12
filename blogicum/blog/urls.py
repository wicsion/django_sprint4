from django.urls import path, include

from . import views

app_name = 'blog'

# Пути, связанные с постами
post_urls = [
    path('create/', views.PostCreateView.as_view(), name='create_post'),
    path('<int:post_id>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<int:post_id>/edit/', views.edit_post, name='edit_post'),
    path('<int:post_id>/delete/', views.delete_post, name='delete_post'),
]

# Пути, связанные с комментариями
comment_urls = [
    path('<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:post_id>/edit_comment/<int:comment_id>/',
         views.edit_comment, name='edit_comment'),
    path('<int:post_id>/delete_comment/<int:comment_id>/',
         views.delete_comment, name='delete_comment'),
]

urlpatterns = [
    path('', views.PostListView.as_view(), name='index'),
    path('posts/', include(post_urls)),
    path('posts/', include(comment_urls)),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.UserDetailView.as_view(),
         name='profile'),
    path('category/<slug:category_slug>/',
         views.CategoryPostListView.as_view(), name='category_posts'),
]
