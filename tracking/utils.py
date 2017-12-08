import re


def get_clean_title(title):
    clean_title = title.lower()
    clean_title = re.sub(r'á', 'a', clean_title)
    clean_title = re.sub(r'é', 'e', clean_title)
    clean_title = re.sub(r'í', 'i', clean_title)
    clean_title = re.sub(r'ó', 'o', clean_title)
    clean_title = re.sub(r'ú', 'u', clean_title)
    clean_title = re.sub(r'ü', 'u', clean_title)
    clean_title = re.sub(r'[^\w\d\s]', '', clean_title)

    return clean_title.strip()
