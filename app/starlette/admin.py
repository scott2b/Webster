from .templates import render

async def admin(request):
    return render('admin.html', {})
