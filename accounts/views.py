import os
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.http import FileResponse
from django.shortcuts import render, redirect

from .models import Profile


def auth_choice(request):
    return render(request, 'registration/auth_choice.html')


def register_view(request):
    is_manager = bool(
        request.user.is_authenticated and (
            request.user.is_superuser or (
                getattr(request.user, 'profile', None) and request.user.profile.is_manager
            )
        )
    )

    if request.user.is_authenticated and not is_manager:
        messages.info(request, 'Vous n’avez pas l’autorisation de créer un compte. Demandez au responsable.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.email = request.POST.get('email', '')
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()

            if request.user.is_authenticated and is_manager:
                role = request.POST.get('role') or Profile.ROLE_RH
            else:
                role = Profile.ROLE_RH

            user.profile.role = role
            user.profile.save()

            if request.user.is_authenticated:
                messages.success(request, 'Compte créé avec succès pour ce nouvel utilisateur.')
                return redirect('dashboard')

            login(request, user)
            messages.success(request, 'Votre compte responsable a été créé avec succès.')
            return redirect('dashboard')
        return render(request, 'registration/register.html', {'form': form, 'is_manager': is_manager})

    form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form, 'roles': Profile.ROLE_CHOICES, 'is_manager': is_manager})


@login_required
def backup_database(request):
    db_path = Path(settings.BASE_DIR) / 'db.sqlite3'

    if not db_path.exists():
        messages.error(request, 'Aucune base de données trouvée pour la sauvegarde.')
        return redirect('dashboard')

    response = FileResponse(
        open(db_path, 'rb'),
        as_attachment=True,
        filename='djawhara_grh_backup.sqlite3'
    )
    response['Content-Type'] = 'application/octet-stream'
    return response


@login_required
def restore_database(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('backup_file')

        if not uploaded_file:
            messages.error(request, 'Aucun fichier sélectionné.')
            return redirect('restore_database')

        if not uploaded_file.name.lower().endswith(('.sqlite3', '.db')):
            messages.error(request, 'Le fichier doit être une base SQLite (.sqlite3 ou .db).')
            return redirect('restore_database')

        db_path = Path(settings.BASE_DIR) / 'db.sqlite3'

        with open(db_path, 'wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        messages.success(request, 'sauvegarde restaurée')
        return redirect('dashboard')

    return render(request, 'accounts/backup_restore.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        messages.error(request, "Identifiant ou mot de passe incorrect.")

    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
