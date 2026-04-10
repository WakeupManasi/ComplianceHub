def global_context(request):
    context = {}
    if request.user.is_authenticated and request.user.organization:
        try:
            from alerts.models import Alert
            context['unread_count'] = Alert.objects.filter(
                organization=request.user.organization, is_read=False
            ).count()
        except Exception:
            context['unread_count'] = 0
    return context
