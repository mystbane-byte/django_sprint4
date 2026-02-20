from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.utils import timezone
from django.db import models
from .models import Post, Category, Comment
from .forms import PostForm, CommentForm, ProfileEditForm


User = get_user_model()


def index(request):
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=models.Count('comments')  # <-- ДОБАВИТЬ
    ).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # Проверка доступа к посту
    if not post.is_published and request.user != post.author:
        return redirect('blog:index')
    
    if post.pub_date > timezone.now() and request.user != post.author:
        return redirect('blog:index')
    
    comments = post.comments.all()
    form = CommentForm()
    comment_count = comments.count()
    
    context = {
        'post': post,
        'comments': comments,
        'form': form,
        'comment_count': comment_count,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug, is_published=True)
    post_list = category.posts.filter(
        is_published=True,
        pub_date__lte=timezone.now()
    ).annotate(
        comment_count=models.Count('comments')
    ).order_by('-pub_date')
    
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'category': category, 'page_obj': page_obj}
    return render(request, 'blog/category.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    
    if request.user == user:
        posts = user.posts.annotate(
            comment_count=models.Count('comments') 
        ).order_by('-pub_date')
    else:
        posts = user.posts.filter(
            is_published=True,
            pub_date__lte=timezone.now()
        ).annotate(
            comment_count=models.Count('comments')  # <-- ДОБАВИТЬ
        ).order_by('-pub_date')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request, username):  # <-- ДОБАВЬТЕ ПАРАМЕТР username
    # Проверка, что пользователь редактирует свой профиль
    if request.user.username != username:
        return redirect('blog:profile', username=request.user.username)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    
    context = {'form': form}
    return render(request, 'blog/user.html', context)


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()
    
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    # Проверка прав: только автор может редактировать
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = PostForm(instance=post)
    
    context = {'form': form}
    return render(request, 'blog/create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    
    return redirect('blog:post_detail', post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    
    # Проверка прав: только автор может редактировать
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)
    else:
        form = CommentForm(instance=comment)
    
    context = {'form': form, 'comment': comment}
    return render(request, 'blog/comment.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    
    context = {'comment': comment}
    return render(request, 'blog/comment_delete.html', context)


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post_id)
    
    if request.method == 'POST':
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    
    context = {'post': post}
    return render(request, 'blog/delete.html', context)