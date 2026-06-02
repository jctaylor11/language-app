from kiwipiepy import Kiwi

kiwi = Kiwi()

PREDICATE_TAGS = frozenset({"VV", "VA"})                # Stem + "다" gives the citation form for verb (VV) and adjective verb (VA)
PREDICATE_SUFFIX_TAGS = frozenset({"XSV", "XSA"})       # Derivational suffixes that turn a preceding noun/root into a predicate
COMPOUND_ROOT_TAGS = frozenset({"NNG", "NNP", "XR"})    # Roots that combine with a predicate suffix (e.g 공부 + 하 → 공부하다)
NOUN_TAGS = frozenset({"NNG", "NNP", "NP"})             # Nouns emitted verbatim - their particles are separate tokens, so they fall away
INVARIANT_TAGS = frozenset({"MAG", "MAJ", "MM"})        # Adverbs/modifier already in citation form since they dont conjugate


def extract_lemmas(sentence: str) -> list[str]:
    """Return the citation form of every content word in a Korean sentence.

    The sentence is tokenised in one pass so Kiwi can use surrounding context to disambiguate homographs. 
    Particles and inflectional endings are dropped, noun + 하다/되다 style compounds are rejoined.
    """
    tokens = kiwi.tokenize(sentence)
    citations: list[str] = []

    i = 0
    while i < len(tokens):
        token = tokens[i]
        next_token = tokens[i + 1] if i + 1 < len(tokens) else None

        # Noun/root + derivational suffix → predicate compound
        if (
            token.tag in COMPOUND_ROOT_TAGS
            and next_token is not None
            and next_token.tag in PREDICATE_SUFFIX_TAGS
        ):
            citations.append(token.form + next_token.form + "다")
            i += 2
            continue

        # Standalone verb or adjective → stem + 다
        if token.tag in PREDICATE_TAGS:
            citations.append(token.form + "다")
            i += 1
            continue

        # Plain noun, or uninflected adverb
        if token.tag in NOUN_TAGS or token.tag in INVARIANT_TAGS:
            citations.append(token.form)
            i += 1
            continue

        i += 1

    return citations