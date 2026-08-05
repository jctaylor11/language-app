import enum

class VocabResultStatus(enum.Enum):
    correct_first_try = "correct_first_try"
    corrected = "corrected"
    skipped = "skipped"


class SentenceResultStatus(enum.Enum):
    correct = "correct"
    skipped = "skipped"


class SessionBoundType(enum.Enum):
    time = "time"
    count = "count"