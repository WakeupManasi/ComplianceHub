from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import VendorForm
from .models import Vendor


@login_required
def vendor_list(request):
    vendors = Vendor.objects.filter(organization=request.user.organization)
    return render(request, 'vendors/vendor_list.html', {'vendors': vendors})


@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk, organization=request.user.organization)
    monitoring_events = vendor.monitoring_events.order_by('-created_at')[:20]
    return render(request, 'vendors/vendor_detail.html', {
        'vendor': vendor,
        'monitoring_events': monitoring_events,
    })


@login_required
def vendor_add(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.organization = request.user.organization
            vendor.save()
            messages.success(request, 'Vendor added successfully.')
            return redirect('vendors:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm()
    return render(request, 'vendors/vendor_form.html', {'form': form, 'title': 'Add Vendor'})


@login_required
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk, organization=request.user.organization)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully.')
            return redirect('vendors:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'vendors/vendor_form.html', {'form': form, 'title': 'Edit Vendor'})
