from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from django.http import Http404
from django.utils import timezone

from .models import Post, Category, Comment
from .forms import PostForm, CommentForm

POSTS_LIMIT = 10


def get_base_post_queryset(user=None):
    """Возвращает базовый QuerySet для постов с необходимыми связями."""
    queryset = Post.objects.select_related('author', 'category', 'location')
    if user is None or not user.is_authenticated:

        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=now()
        )
    else:

        queryset = queryset.filter(
            category__is_published=True,
            pub_date__lte=now()
        )
    return queryset


def index(request: HttpRequest) -> HttpResponse:
    posts = get_base_post_queryset().order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/index.html', {'page_obj': page_obj})


def category_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Страница с публикациями определённой категории."""
    category = get_object_or_404(Category, slug=slug, is_published=True)
    posts = (get_base_post_queryset().filter(category=category)
             .order_by('-pub_date'))
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/category.html',
                  {'category': category, 'page_obj': page_obj})


def post_detail(request: HttpRequest, pk: int) -> HttpResponse:
    post = get_object_or_404(Post, pk=pk)

    if ((not post.is_published or not post.category.is_published
            or post.pub_date > timezone.now())
            and post.author != request.user):
        raise Http404("Пост не найден")

    comments = post.comments.all()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('blog:login')
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', pk=pk)
    else:
        comment_form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': comment_form,
        'comments': comments,
        'user': request.user,
    })


def register(request: HttpRequest) -> HttpResponse:
    """Регистрация нового пользователя."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('blog:login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration_form.html',
                  {'form': form})


@login_required
def profile_redirect(request):
    return redirect('blog:profile', username=request.user.username)


@login_required
def create_post(request: HttpRequest) -> HttpResponse:
    """Создание нового поста."""
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    return render(request, 'blog/create.html', {'form': form})


@login_required(login_url=reverse_lazy('blog:login'))
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)

    # Проверка, что пользователь является автором поста
    if post.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', pk=pk)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/edit_post.html', {'form': form, 'post': post})


@login_required
def delete_post(request: HttpRequest, pk: int) -> HttpResponse:
    """Удаление поста."""
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return redirect('blog:post_detail', pk=pk)

    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/post_confirm_delete.html', {'post': post})


@login_required
def profile_view(request: HttpRequest, username: str) -> HttpResponse:
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile_user.pk).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)  # Пагинация
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'blog/profile.html', {
        'profile_user': profile_user,
        'page_obj': page_obj,
    })


@login_required
def add_comment(request, pk):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, pk=pk)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', pk=pk)
    else:
        form = CommentForm()

    return render(request, 'blog/detail.html', {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
    })


@login_required
def edit_comment(request, post_id, comment_id):
    # Получаем комментарий по ID
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем, является ли текущий пользователь автором комментария
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', pk=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comments.html', {
        'form': form,
        'comment': comment,
        'action': 'edit',  # Указываем, что это редактирование
    })


@login_required
def delete_comment(request, post_id, comment_id):
    # Получаем комментарий по ID
    comment = get_object_or_404(Comment, id=comment_id)

    # Проверяем, является ли текущий пользователь автором комментария
    if comment.author != request.user:
        return redirect('blog:post_detail', pk=post_id)

    if request.method == 'POST':
        # Удаляем комментарий
        comment.delete()
        return redirect('blog:post_detail', pk=post_id)

    return render(request, 'blog/comments.html', {
        'comment': comment,
        'action': 'delete',  # Указываем, что это удаление
    })
