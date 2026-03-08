from django.db import models
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Post


def get_published_posts():
    """Возвращает QuerySet опубликованных постов с комментариями"""
    return Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=models.Count('comments')
    ).order_by('-pub_date')


def get_author_posts(user, viewer=None):
    """
    Возвращает посты пользователя с учетом прав просмотра.
    Если viewer == user (автор смотрит свой профиль) - показывает все посты.
    Иначе - только опубликованные.
    """
    if viewer == user:
        return user.posts.annotate(
            comment_count=models.Count('comments')
        ).order_by('-pub_date')
    else:
        return user.posts.filter(
            is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=models.Count('comments')
        ).order_by('-pub_date')


def get_paginated_posts(posts, page_number, per_page=10):
    """Возвращает page_obj для пагинации"""
    paginator = Paginator(posts, per_page)
    return paginator.get_page(page_number)