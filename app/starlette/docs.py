from .templates import render


def docs(request):
    return render('docs.html', {})
