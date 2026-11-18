import enum

class VocabResultStatus(enum.Enum):
    correct_first_try = "correct_first_try"
    corrected = "corrected"
    peeked = "peeked"
    skipped = "skipped"


class SentenceResultStatus(enum.Enum):
    correct = "correct"
    peeked = "peeked"
    skipped = "skipped"


class SessionBoundType(enum.Enum):
    time = "time"
    count = "count"


class SessionType(enum.Enum):
    vocab = "vocab"
    sentence = "sentence"


class GlossType(enum.Enum):
    primary = "primary"
    tolerated = "tolerated"
