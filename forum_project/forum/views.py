from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from .models import Category, Post, Comment
from django.utils.decorators import method_decorator
from django.views import View
from .forms import PostForm, CommentForm
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordChangeForm
from .forms import RegistrationForm, CustomAuthenticationForm, ProfileEditForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

def home(request):
    categories_list = Category.objects.all().order_by('title')
    paginator = Paginator(categories_list, 6)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'forum/home.html', context)

@login_required(login_url='login')
def add_category_redirect(request):
    return redirect('category_add')

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

    context = {
        'category': category,
        'page_obj': page_obj
    }
    return render(request, 'forum/category_detail.html', context)


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

    if request.user.is_authenticated:
        if request.method == 'POST':
            form = CommentForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.user = request.user
                comment.post = post
                comment.save()
                return redirect('post_detail', post_id=post.id)
        else:
            form = CommentForm()
    else:
        form = None

    return render(request, 'forum/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })

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
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('profile')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'forum/login.html', {'form': form, 'next': request.GET.get('next', '')})


@login_required
def profile_view(request):
    user = request.user
    user_categories = user.categories.all()
    user_posts = user.posts.all().order_by('-created_at')

    return render(request, 'forum/profile.html', {
        'user_categories': user_categories,
        'user_posts': user_posts,
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

@method_decorator(csrf_exempt, name='dispatch')
class LogoutViewAllowGet(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)