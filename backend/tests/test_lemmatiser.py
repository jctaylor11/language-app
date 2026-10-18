import pytest

from backend.lemmatiser import extract_lemmas


def test_extract_lemmas_drops_particles_from_nouns():
    assert extract_lemmas("물을 마셔요") == ["물", "마시다"]  # 을 is a separate token (JKO), so the noun comes out bare


def test_extract_lemmas_returns_verb_as_stem_plus_da():
    assert extract_lemmas("먹었어요") == ["먹다"]


def test_extract_lemmas_keeps_irregular_verbs():
    assert extract_lemmas("음악을 들었어요") == ["음악", "듣다"]  # Kiwi tags 듣 as VV-I, which an exact tag match would drop


def test_extract_lemmas_keeps_irregular_adjectives():
    assert extract_lemmas("날씨가 추워요") == ["날씨", "춥다"]  # 춥 is VA-I


def test_extract_lemmas_rejoins_noun_and_suffix_into_one_predicate():
    assert extract_lemmas("공부해") == ["공부하다"]  # One word, so it must not split into 공부 + 하다 and inflate lemma_count


def test_extract_lemmas_rejoins_noun_and_irregular_suffix():
    assert extract_lemmas("걱정스러워요") == ["걱정스럽다"]  # 스럽 is XSA-I, so the suffix check needs the base tag too


def test_extract_lemmas_keeps_numerals_and_drops_dependent_nouns():
    assert extract_lemmas("사과 다섯 개를 샀어요") == ["사과", "다섯", "사다"]  # 개 is a dependent noun (NNB), which is excluded from the words scope


def test_extract_lemmas_keeps_interjections():
    assert extract_lemmas("와 맛있어요") == ["와", "맛있다"]


# Known edge case - noun suffixes (XSN) are sometimes dropped. Strict makes it fail when fixed, and the marker can be removed
@pytest.mark.xfail(strict=True, reason="Noun suffixes (XSN) are dropped, so 대학생 comes out as 대학") 
def test_extract_lemmas_keeps_noun_suffixes():
    assert extract_lemmas("대학생이에요") == ["대학생"]
