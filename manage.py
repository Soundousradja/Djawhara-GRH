#!/usr/bin/env python
"""Utilitaire de ligne de commande Django pour Djawhara GRH."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djawhara_grh.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django est introuvable. Avez-vous activé votre environnement virtuel "
            "et installé les dépendances (pip install -r requirements.txt) ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
