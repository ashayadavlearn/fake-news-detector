"""
utils.py
Shared text preprocessing utilities used by both the training pipeline
(train_model.py) and the live prediction pipeline (predict.py).
"""

import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Make sure the NLTK corpora are available. This is safe to call every
# time the app starts -- if the data is already present it's a no-op.
for _pkg, _path in [
    ("stopwords", "corpora/stopwords"),
    ("wordnet", "corpora/wordnet"),
    ("omw-1.4", "corpora/omw-1.4"),
]:
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_pkg, quiet=True)

_STOPWORDS = set(stopwords.words("english"))
_LEMMATIZER = WordNetLemmatizer()
_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HTML_RE = re.compile(r"<.*?>")
_DIGIT_RE = re.compile(r"\d+")
_MULTISPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """
    Full preprocessing pipeline applied to a raw news headline/article:
      1. Lowercase
      2. Strip URLs / HTML tags
      3. Remove punctuation
      4. Remove digits
      5. Tokenize on whitespace
      6. Remove stopwords
      7. Lemmatize each remaining token

    Returns a single cleaned string ready to be fed into the TF-IDF
    vectorizer.
    """
    if not text:
        return ""

    text = text.lower()
    text = _URL_RE.sub(" ", text)
    text = _HTML_RE.sub(" ", text)
    text = text.translate(_PUNCT_TABLE)
    text = _DIGIT_RE.sub(" ", text)
    text = _MULTISPACE_RE.sub(" ", text).strip()

    tokens = text.split()
    tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]
    tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]

    return " ".join(tokens)


def truncate(text: str, length: int = 80) -> str:
    """Shorten text for display purposes (e.g. history table titles)."""
    text = text.strip().replace("\n", " ")
    return text if len(text) <= length else text[: length - 1].rstrip() + "..."
