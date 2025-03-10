from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Category, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'created_at')
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    verbose_name = _('Category')
    verbose_name_plural = _('Categories')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_published', 'created_at')
    search_fields = ('name',)
    verbose_name = _('Location')
    verbose_name_plural = _('Locations')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_published', 'pub_date')
    list_filter = ('category', 'is_published', 'pub_date')
    search_fields = ('title', 'text')
    verbose_name = _('Post')
    verbose_name_plural = _('Posts')
