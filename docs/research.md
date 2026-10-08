# Forgetting Curve

Psychological model that describes the rate at which information is forgotten if not actively reinforced (Boros, 2025). Memory decays exponentially. When information is actively recalled, the rate of forgetting slows, future recalls become easier, and more durable.

This raises the question of the most efficient time for active recall: too early and you still remember it well, too late and you've already forgotten it.

## Spaced Repetition

> "the optimal strategy is to review something right before you forget it" (Sinha, 2026)

Problem with a fixed schedule: not all information has the same difficulty, so treating everything uniformly is inefficient.

## Systems

The systems described (SM-2 and FSRS) require the user to grade themselves. My algorithm will infer this based on the telemetry.

### SM-2 Algorithm

Fixed-multiplier algorithm. Significant because it inspired many applications using spaced repetition, previously used by Anki and Quizlet (SuperMemo World, 2026). The latest is SM-20, which is more advanced - but SM-2 has a good balance of simplicity and accessibility.

It maintains state for repetition count, easiness factor, and interval. The user grades each card from 0-5, which adjusts the easiness factor (Sinha, 2026).

- If grade > 2, the next interval is a function of the current interval and easiness factor: `i(n) = i(n-1) * ef` for `n > 2`, where `i(1) = 1` and `i(2) = 6`.
- If grade ≤ 2, the repetition count resets to 0 and the interval resets to 1.

The easiness factor starts at 2.5 and is updated as a function of the user's grade and its previous value, with a minimum of 1.3:

`ef = ef + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))`

**Code**

Adapted to Python from the Go implementation in Sinha (2026).

```python
class Card:
    def __init__(self, repetition=0, interval=0, ef=2.5):
        self.repetition = repetition
        self.interval = interval
        self.ef = ef

    def __repr__(self):
        return f"Card(repetition={self.repetition}, interval={self.interval}, ef={self.ef})"

def review(card: Card, quality: int) -> None:
    if quality < 3:
        card.repetition = 0
        card.interval = 1
        return

    if card.repetition == 0:
        card.interval = 1
    elif card.repetition == 1:
        card.interval = 6
    else:
        card.interval = int(card.interval * card.ef)

    card.repetition += 1

    ef = card.ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    card.ef = max(ef, 1.3)
```

SM is the algorithm family used by SuperMemo for their spaced repetition software.

### FSRS

Aims to be more efficient and learn patterns better than SM-2.

It is based off "Three Component Model of Memory", which uses three variables, "DSR" (Anki, 2026):

- **Retrievability (R)**: R(time since last review, stability) is the probability someone can successfully recall the information at a given moment.
- **Stability (S)**: Time (in days) for R to decrease from 100% to 90%. The most critical part of FSRS.
- **Difficulty (D)**: No precise definition, just crude metric representing the inherent difficulty - e.g is derived from the user's grades (Again, Hard, Good, Easy).

R changes daily, while D and S update only on review. Accurate estimation of DSR values analyses the user's review history and uses machine learning to find parameters that provide the best fit to their reviews. In the case of my app - this will be looking at the vocab reviews AND the sentence word reviews.
