"""
context_processors.py — Custom Django Template Context Processors

Context processors are functions that add variables to EVERY template's context.
This avoids the need to pass Firebase config manually in every view.

How it works:
    1. This function is registered in settings.py TEMPLATES['OPTIONS']['context_processors']
    2. Django calls it on every request
    3. The returned dict is merged into the template context
    4. Templates can access {{ firebase_config.api_key }}, etc.
"""

from django.conf import settings
import json


def firebase_config(request):
    """
    Make Firebase client-side config available in all templates.

    The config values come from settings.FIREBASE_CONFIG, which reads
    them from environment variables (loaded from .env by python-dotenv).

    In templates, use:
        {{ firebase_config_json|safe }}   — for inline <script> blocks
    """
    return {
        'firebase_config': settings.FIREBASE_CONFIG,
        'firebase_config_json': json.dumps(settings.FIREBASE_CONFIG),
    }
