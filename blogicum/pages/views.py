from django.views.generic import TemplateView
from django.shortcuts import render


class AboutView(TemplateView):
    template_name = 'pages/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['additional_data'] = 'Some extra data for the template'
        return context


class RulesView(TemplateView):
    template_name = 'pages/rules.html'


def csrf_failure(request, reason=""):
    """Обработчик ошибки CSRF."""
    return render(request, 'pages/403csrf.html', {'reason': reason},
                  status=403)


def page_not_found(request, exception):
    """Обработчик ошибки 404."""
    return render(request, 'pages/404.html', status=404)


def server_error(request):
    """Обработчик ошибки 500."""
    return render(request, 'pages/500.html', status=500)
