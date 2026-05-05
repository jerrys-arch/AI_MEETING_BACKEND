def detect_language(text: str) -> str:
    """
    Detect if text is Amharic or English.
    Amharic uses Ethiopic script: Unicode range U+1200–U+137F
    If more than 10% of characters are Ethiopic → Amharic
    Otherwise → English
    """
    if not text:
        return "en"

    ethiopic_count = sum(1 for c in text if '\u1200' <= c <= '\u137F')
    ratio = ethiopic_count / len(text)

    detected = "am" if ratio > 0.1 else "en"
    print(f"LANGUAGE DETECTED: {detected} (ethiopic ratio: {ratio:.2f})")
    return detected