import re
from datetime import datetime

from slugify import slugify as python_slugify
from sqlalchemy.orm import Session


# Kazakh to Latin transliteration map
KAZAKH_TO_LATIN = {
    'А': 'A', 'а': 'a',
    'Ә': 'A', 'ә': 'a',
    'Б': 'B', 'б': 'b',
    'В': 'V', 'в': 'v',
    'Г': 'G', 'г': 'g',
    'Ғ': 'G', 'ғ': 'g',
    'Д': 'D', 'д': 'd',
    'Е': 'E', 'е': 'e',
    'Ё': 'Yo', 'ё': 'yo',
    'Ж': 'Zh', 'ж': 'zh',
    'З': 'Z', 'з': 'z',
    'И': 'I', 'и': 'i',
    'Й': 'Y', 'й': 'y',
    'К': 'K', 'к': 'k',
    'Қ': 'Q', 'қ': 'q',
    'Л': 'L', 'л': 'l',
    'М': 'M', 'м': 'm',
    'Н': 'N', 'н': 'n',
    'Ң': 'N', 'ң': 'n',
    'О': 'O', 'о': 'o',
    'Ө': 'O', 'ө': 'o',
    'П': 'P', 'п': 'p',
    'Р': 'R', 'р': 'r',
    'С': 'S', 'с': 's',
    'Т': 'T', 'т': 't',
    'У': 'U', 'у': 'u',
    'Ұ': 'U', 'ұ': 'u',
    'Ү': 'U', 'ү': 'u',
    'Ф': 'F', 'ф': 'f',
    'Х': 'H', 'х': 'h',
    'Һ': 'H', 'һ': 'h',
    'Ц': 'Ts', 'ц': 'ts',
    'Ч': 'Ch', 'ч': 'ch',
    'Ш': 'Sh', 'ш': 'sh',
    'Щ': 'Shch', 'щ': 'shch',
    'Ъ': '', 'ъ': '',
    'Ы': 'Y', 'ы': 'y',
    'І': 'I', 'і': 'i',
    'Ь': '', 'ь': '',
    'Э': 'E', 'э': 'e',
    'Ю': 'Yu', 'ю': 'yu',
    'Я': 'Ya', 'я': 'ya',
}


def transliterate_kazakh(text: str) -> str:
    """Transliterate Kazakh Cyrillic text to Latin.
    
    Args:
        text: Text in Kazakh Cyrillic
        
    Returns:
        Transliterated text in Latin
    """
    result = []
    for char in text:
        result.append(KAZAKH_TO_LATIN.get(char, char))
    return ''.join(result)


def generate_slug(text: str, max_length: int = 100) -> str:
    """Generate a URL-friendly slug from text.
    
    Supports Kazakh Cyrillic by transliterating to Latin first.
    
    Args:
        text: Text to convert to slug (can be in Kazakh Cyrillic)
        max_length: Maximum length of slug
        
    Returns:
        URL-friendly slug
    """
    # First transliterate Kazakh to Latin
    transliterated = transliterate_kazakh(text)
    
    # Then slugify
    slug = python_slugify(transliterated, max_length=max_length)
    return slug


def generate_unique_slug(
    db: Session,
    model: type,
    text: str,
    max_length: int = 100
) -> str:
    """Generate a unique slug for a model.
    
    Args:
        db: Database session
        model: SQLAlchemy model class
        text: Text to convert to slug (can be in Kazakh Cyrillic)
        max_length: Maximum length of slug
        
    Returns:
        Unique slug
    """
    base_slug = generate_slug(text, max_length - 10)  # Reserve space for counter
    slug = base_slug
    counter = 1
    
    # Check if slug exists
    while db.query(model).filter(model.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


def generate_slug_with_timestamp(text: str, max_length: int = 100) -> str:
    """Generate a slug with timestamp for uniqueness.
    
    Args:
        text: Text to convert to slug (can be in Kazakh Cyrillic)
        max_length: Maximum length of slug
        
    Returns:
        Slug with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base_slug = generate_slug(text, max_length - len(timestamp) - 1)
    return f"{base_slug}-{timestamp}"
