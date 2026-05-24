import enum

class ResultStatus(enum.Enum):
    correct_first_try = "correct_first_try"
    corrected = "corrected"
    skipped = "skipped"