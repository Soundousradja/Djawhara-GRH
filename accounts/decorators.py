from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Autorise l'accès uniquement aux utilisateurs ayant l'un des rôles indiqués
    (ou au Directeur Général / superutilisateur, qui a toujours accès à tout)."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            profile = getattr(request.user, 'profile', None)
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            if profile and (profile.is_manager or profile.role in roles):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cette page.")
        return _wrapped
    return decorator
