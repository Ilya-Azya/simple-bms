from core.permissions import is_admin


def admin_status(request):
    return {
        "is_admin_user": is_admin(request.user) if request.user.is_authenticated else False
    }
