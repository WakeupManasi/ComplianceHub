from collections import OrderedDict

from django.shortcuts import render

from .models import FAQ


def faq_list(request):
    """Show active FAQs grouped by category."""
    faqs = FAQ.objects.filter(is_active=True)

    # Group by category, preserving the category choices order
    category_labels = dict(FAQ._meta.get_field('category').choices)
    grouped = OrderedDict()
    for key, label in category_labels.items():
        category_faqs = [f for f in faqs if f.category == key]
        if category_faqs:
            grouped[label] = category_faqs

    return render(request, 'faq/faq_list.html', {'grouped_faqs': grouped})
