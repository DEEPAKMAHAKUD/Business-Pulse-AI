from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Business
from .forms import BusinessForm


@login_required
def business_create(request):
    if request.method == 'POST':
        form = BusinessForm(request.POST)
        if form.is_valid():
            business = form.save(commit=False)
            business.owner = request.user
            business.save()
            messages.success(request, 'Business created successfully.')
            return redirect('dashboard')
    else:
        form = BusinessForm()
    return render(request, 'businesses/business_form.html', {'form': form})


@login_required
def business_detail(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    return render(request, 'businesses/business_detail.html', {'business': business})


@login_required
def business_update(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = BusinessForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, 'Business updated successfully.')
            return redirect('business_detail', pk=business.pk)
    else:
        form = BusinessForm(instance=business)
    return render(request, 'businesses/business_form.html', {'form': form})


@login_required
def business_delete(request, pk):
    business = get_object_or_404(Business, pk=pk, owner=request.user)
    if request.method == 'POST':
        business.delete()
        messages.success(request, 'Business deleted successfully.')
        return redirect('dashboard')
    return render(request, 'businesses/business_confirm_delete.html', {'business': business})
