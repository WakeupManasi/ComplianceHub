from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RiskForm
from .models import Risk


@login_required
def risk_list(request):
    risks = Risk.objects.filter(organization=request.user.organization)
    return render(request, 'risks/risk_list.html', {'risks': risks})


@login_required
def risk_detail(request, pk):
    risk = get_object_or_404(Risk, pk=pk, organization=request.user.organization)
    return render(request, 'risks/risk_detail.html', {'risk': risk})


@login_required
def risk_add(request):
    org = request.user.organization
    if request.method == 'POST':
        form = RiskForm(request.POST, organization=org)
        if form.is_valid():
            risk = form.save(commit=False)
            risk.organization = org
            risk.save()
            messages.success(request, 'Risk added successfully.')
            return redirect('risks:risk_detail', pk=risk.pk)
    else:
        form = RiskForm(organization=org)
    return render(request, 'risks/risk_form.html', {'form': form, 'title': 'Add Risk'})


@login_required
def risk_edit(request, pk):
    org = request.user.organization
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    if request.method == 'POST':
        form = RiskForm(request.POST, instance=risk, organization=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Risk updated successfully.')
            return redirect('risks:risk_detail', pk=risk.pk)
    else:
        form = RiskForm(instance=risk, organization=org)
    return render(request, 'risks/risk_form.html', {'form': form, 'title': 'Edit Risk'})
