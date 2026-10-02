def profile_context(request):
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
    return {'user_profile': profile}
