print("Accounts views module loaded", flush=True)
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomUserCreationForm
from businesses.models import Business


def landing_page(request):
    print("Landing page view called", flush=True)
    return render(request, 'accounts/landing.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            # Create a default business for the user
            Business.objects.create(owner=user, name="My Business")
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    businesses = Business.objects.filter(owner=request.user)
    return render(request, 'businesses/dashboard.html', {'businesses': businesses})
