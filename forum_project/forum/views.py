from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Category, Post, Comment, Like
from .forms import (
    RegistrationForm,
    CustomAuthenticationForm,
    ProfileEditForm,
    PostForm,
    CommentForm,
)

#Главная страница

def home(request):
    categories_list = Category.objects.all().order_by('title')
    paginator = Paginator(categories_list, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'forum/home.html', {'page_obj': page_obj})

@login_required(login_url='login')
def add_category_redirect(request):
    return redirect('category_add')

#Категории

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = ['title', 'description', 'image']
    template_name = 'forum/category_form.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

def category_detail(request, pk):
    category = get_object_or_404(Category, pk=pk)
    posts = Post.objects.filter(category=category).order_by('-created_at')
    paginator = Paginator(posts, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'forum/category_detail.html', {'category': category, 'page_obj': page_obj})
# TODO
    # def category_delete

#Посты 
@method_decorator(login_required, name='dispatch')
class PostCreateView(View):
    def get(self, request, category_id):
        form = PostForm()
        return render(request, 'forum/post_add.html', {'form': form, 'category_id': category_id})

    def post(self, request, category_id):
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.category_id = category_id
            post.user = request.user
            post.save()
            return redirect('category_detail', pk=category_id)
        return render(request, 'forum/post_add.html', {'form': form, 'category_id': category_id})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    likes_count = post.likes.count()
    user_liked = post.likes.filter(user=request.user).exists() if request.user.is_authenticated else False

    form = CommentForm(request.POST) if request.method == 'POST' and request.user.is_authenticated else CommentForm()

    if request.user.is_authenticated and request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        comment.save()
        return redirect('post_detail', post_id=post.id)

    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form if request.user.is_authenticated else None,
        'likes_count': likes_count,
        'user_liked': user_liked,
    })

# TODO
    # def post_delete

#Регистрация и вход 

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegistrationForm()
    return render(request, 'forum/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect(request.POST.get('next') or request.GET.get('next') or 'profile')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'forum/login.html', {'form': form, 'next': request.GET.get('next', '')})

#Профиль

@login_required
def profile_view(request):
    return render(request, 'forum/profile.html', {
        'user_categories': request.user.categories.all(),
        'user_posts': request.user.posts.all().order_by('-created_at'),
    })

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'forum/profile_edit.html', {'form': form})

#Лайки 
@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count(),
    })

# счетчик лайков
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('-created_at')
    likes_count = post.likes.count()
    user_liked = post.likes.filter(user=request.user).exists() if request.user.is_authenticated else False

    if request.user.is_authenticated and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.post = post
            comment.save()
            return redirect('post_detail', post_id=post.id)
    else:
        form = CommentForm() if request.user.is_authenticated else None

    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'likes_count': likes_count,
        'user_liked': user_liked,
    })

# лайк дизлайк
@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})


