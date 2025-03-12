from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db.models import Count
from django.db.models.query import QuerySet
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, DetailView

from .forms import CommentCreateForm, PostForm, UserEditForm
from .models import Category, Post, Comment

POSTS_ON_PAGE = 10


def get_paginator_page(request, query_set, posts_on_page=POSTS_ON_PAGE):
    """Возвращает страницу с пагинацией для заданного queryset."""
    return (Paginator(query_set, posts_on_page)
            .get_page(request.GET.get('page')))


def get_published_posts(
    posts: QuerySet = Post.objects.all(),
    use_filtering: bool = True,
    use_select_related: bool = True,
    use_annotation: bool = True,
) -> QuerySet:
    """
    Возвращает queryset с опубликованными постами.

    :param posts: Исходный queryset.
    :param use_filtering: Применять фильтрацию по дате и публикации.
    :param use_select_related: Использовать select_related.
    :param use_annotation: Добавлять аннотацию с количеством комментариев.
    :return: Отфильтрованный и оптимизированный queryset.
    """
    if use_filtering:
        posts = posts.filter(
            pub_date__lt=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    if use_select_related:
        posts = posts.select_related('category', 'location', 'author')
    if use_annotation:
        posts = posts.annotate(comment_count=Count('comments'))
    return posts.order_by('-pub_date')


class PostListView(ListView):
    """Отображает список опубликованных постов."""

    paginate_by = POSTS_ON_PAGE
    template_name = 'blog/index.html'
    queryset = get_published_posts(
        use_filtering=True,
        use_select_related=True,
        use_annotation=True
    )


@login_required
def delete_post(request, post_id):
    """Удаляет пост, если пользователь является его автором."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', request.user.username)
    return render(
        request,
        'blog/create.html',
        {'post': post, 'form': PostForm(instance=post)}
    )


@login_required
def edit_post(request, post_id):
    """Редактирует пост, если пользователь является его автором."""
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request, 'blog/create.html', {'form': form, 'post': post}
    )


@login_required
def edit_comment(request, post_id, comment_id):
    """Редактирует комментарий, если пользователь является его автором."""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    form = CommentCreateForm(request.POST or None, instance=comment)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request, 'blog/comment.html', {'form': form, 'comment': comment}
    )


@login_required
def delete_comment(request, post_id, comment_id):
    """Удаляет комментарий, если пользователь является его автором."""
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)
    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=post_id)

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request, 'blog/comment.html', {'comment': comment}
    )


@login_required
def add_comment(request, post_id):
    """Добавляет комментарий к посту."""
    post = get_object_or_404(Post, id=post_id)

    form = CommentCreateForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    return render(request, 'detail.html', {'form': form, 'post': post})


class PostDetailView(DetailView):
    """Отображает детальную информацию о посте."""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        """Возвращает пост с проверкой условий отображения."""
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            id=self.kwargs['post_id']
        )

        if post.author != self.request.user and (
            not post.is_published
            or not post.category.is_published
            or post.pub_date > timezone.now()
        ):
            raise Http404("Пост не найден")
        return post

    def get_context_data(self, **kwargs):
        """Добавляет комментарии и форму в контекст."""
        return super().get_context_data(
            **kwargs,
            comments=Comment.objects
            .filter(post=self.kwargs['post_id']).select_related('author'),
            form=CommentCreateForm()
        )


class CategoryPostListView(ListView):
    """Отображает список постов в категории."""

    paginate_by = POSTS_ON_PAGE
    template_name = "blog/category.html"

    def get_category_or_404(self):
        """Возвращает категорию или вызывает 404."""
        return get_object_or_404(
            Category,
            slug=self.kwargs.get('category_slug'),
            is_published=True
        )

    def get_queryset(self):
        """Возвращает queryset с постами категории."""
        return (get_published_posts(self.get_category_or_404().posts)
                .order_by('-pub_date'))

    def get_context_data(self, **kwargs):
        """Добавляет категорию в контекст."""
        return super().get_context_data(
            **kwargs,
            category=self.get_category_or_404()
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    """Создает новый пост."""

    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm

    def get_success_url(self):
        """Возвращает URL для перенаправления."""
        return reverse(
            'blog:profile',
            args=[self.request.user.username]
        )

    def form_valid(self, form):
        """Присваивает автору поста текущего пользователя."""
        form.instance.author = self.request.user
        return super().form_valid(form)


class UserLoginView(LoginView):
    """Отображает страницу входа."""

    template_name = 'registration/login.html'

    def get_success_url(self):
        """Возвращает URL для перенаправления после успешного входа."""
        return reverse_lazy('blog:profile',
                            kwargs={'username': self.request.user.username})


class UserDetailView(ListView):
    """Отображает профиль пользователя с его постами."""

    paginate_by = POSTS_ON_PAGE
    template_name = 'blog/profile.html'

    def get_user(self):
        """Возвращает пользователя по username."""
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        """Возвращает queryset с постами пользователя."""
        user = self.get_user()
        return get_published_posts(
            user.posts,
            use_filtering=self.request.user != user,
            use_select_related=True,
            use_annotation=True
        )

    def get_context_data(self, **kwargs):
        """Добавляет профиль пользователя в контекст."""
        context = super().get_context_data(**kwargs)
        context['profile'] = self.get_user()
        return context


@login_required
def edit_profile(request):
    """Редактирует профиль пользователя."""
    form = UserEditForm(request.POST or None, instance=request.user)
    if form.is_valid():
        form.save()
        return redirect('blog:profile', request.user.username)

    return render(request, 'blog/user.html', {'form': form})
