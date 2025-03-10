from django import forms

from .models import Post, Comment  # Импортируем модель Comment


# Форма для создания/редактирования постов
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'category', 'location', 'image']


# Форма для добавления комментариев
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
