import re


def generate_slug(title: str) -> str:
    """Génère un slug URL-friendly à partir d'un titre."""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')
