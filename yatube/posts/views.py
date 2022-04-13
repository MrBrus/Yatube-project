from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect, reverse

from .models import Post, Group, Comment, User, Follow
from .forms import PostForm, CommentForm

POSTS_ON_PAGE = 10


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_numb = request.GET.get('page')
    page_obj = paginator.get_page(page_numb)
    title = 'Последние обновления на сайте.'
    context = {
        'page_obj': page_obj,
        'title': title
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    description = group.description
    posts = group.posts.all()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_numb = request.GET.get('page')
    page_obj = paginator.get_page(page_numb)
    context = {
        'group': group,
        'description': description,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    number_of_authors_posts = posts.count()
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_numb = request.GET.get('page')
    page_obj = paginator.get_page(page_numb)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=author
        ).exists()
    else:
        following = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'number_of_authors_posts': number_of_authors_posts
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("posts:profile", request.user.username)
    return render(request, "posts/create_post.html",
                  {"form": form, 'is_edit': False})


def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/create_post.html',
                  {'post': post, 'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, pk=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    return render(request, 'posts/post_detail.html', {'form': form})


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_numb = request.GET.get('page')
    page_obj = paginator.get_page(page_numb)
    title = 'Ваша личная лента'
    context = {'posts': posts,
               'page_obj': page_obj,
               'title': title,
               'follow': True}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=user,
                                        author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse("posts:profile", args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user,
                                        author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect("posts:profile", username=author)
