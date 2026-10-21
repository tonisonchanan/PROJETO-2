"""Normalização de texto usada pela busca e pela conferência."""
import re
import unicodedata

# Palavras que não ajudam a achar um produto e atrapalham a busca do chat.
STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "da", "do", "das", "dos",
    "e", "ou", "em", "no", "na", "nos", "nas", "para", "pra", "por", "com",
    "que", "qual", "quais", "quanto", "quanta", "custa", "custam", "preco", "valor",
    "voces", "vcs", "voce", "tem", "tenho", "vende", "vendem", "venda", "existe",
    "eu", "me", "meu", "minha", "se", "isso", "esse", "essa", "este", "esta",
    "gostaria", "queria", "quero", "saber", "sobre", "produto", "produtos",
    "ola", "oi", "bom", "boa", "dia", "tarde", "noite", "favor", "obrigado",
    "como", "onde", "quando", "eh", "ser", "serve", "usar", "uso", "algum", "alguma",
    "mais", "melhor", "indica", "indicam", "recomenda", "preciso", "limpar", "tirar",
}

# Volume ou peso escrito junto, separado ou por extenso: "5L", "5 l", "5 litros", "1 kg".
_UNIDADES = {"ml": "ml", "mililitro": "ml", "mililitros": "ml", "l": "l", "lt": "l", "lts": "l",
             "litro": "l", "litros": "l", "kg": "kg", "quilo": "kg", "quilos": "kg", "kilo": "kg",
             "g": "g", "grama": "g", "gramas": "g"}
_MEDIDA = re.compile(r"(\d+(?:[.,]\d+)?)\s*(" + "|".join(sorted(_UNIDADES, key=len, reverse=True)) + r")\b")
_MEDIDA_NORMALIZADA = re.compile(r"\b\d+(?:\.\d+)?(?:ml|l|kg|g)\b")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem pontuação e com medidas juntas ("5 L" vira "5l")."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = _MEDIDA.sub(lambda m: m.group(1).replace(",", ".") + _UNIDADES[m.group(2)], texto)
    texto = re.sub(r"[^a-z0-9.%]+", " ", texto)
    return " ".join(texto.split())


def medidas(texto: str) -> set[str]:
    """Medidas presentes no texto, já normalizadas, como {"5l"} ou {"500ml"}."""
    return set(_MEDIDA_NORMALIZADA.findall(normalizar(texto)))


def chave_nome(texto: str) -> str:
    """Nome sem medidas e sem plural simples, para comparar "limpa piso" com "Limpa Pisos 2 L"."""
    sem_medida = _MEDIDA_NORMALIZADA.sub(" ", normalizar(texto))
    return " ".join(p[:-1] if len(p) > 3 and p.endswith("s") else p for p in sem_medida.split())


def palavras_chave(texto: str) -> list[str]:
    return [p for p in normalizar(texto).split() if p not in STOPWORDS and len(p) > 1]
