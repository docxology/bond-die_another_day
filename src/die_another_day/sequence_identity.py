"""DNA sequence identity verification and gene-therapy edit detection.

ICARUS / *Die Another Day* (2002) concept extension of
:mod:`die_another_day.identity_detection`. Where the biometric module screens a
numeric marker vector, this module verifies identity at the sequence level:

* :func:`generate_genome` deterministically synthesises a reference genome
  over the {A, C, G, T} alphabet with a configured GC content.
* :func:`mutate_genome` introduces scattered sequencing substitutions and
  optionally one *contiguous* block of changes — the signature of a
  gene-therapy-grade edit, which rewrites a stretch of loci coherently.
* :func:`hamming_distance` and :func:`edit_distance` (Levenshtein, O(mn)
  dynamic programming) score overall similarity; :func:`kmer_jaccard` gives a
  noise-robust k-mer fingerprint similarity.
* :func:`mismatch_clusters` finds contiguous runs of mismatching loci;
  :func:`verify_identity` flags a probe as a suspected replacement when a
  contiguous edit block reaches ``cluster_min`` bases — scattered sequencing
  noise rarely forms such a run, so this separates substitution from noise.

All functions are pure and deterministic: identical inputs (including the same
seed) reproduce identical sequences and verdicts.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = [
    "DNA_ALPHABET",
    "SequenceVerdict",
    "edit_distance",
    "generate_genome",
    "hamming_distance",
    "kmer_jaccard",
    "mismatch_clusters",
    "mutate_genome",
    "verify_identity",
]

#: DNA alphabet, ordered for deterministic sampling.
DNA_ALPHABET = ("A", "C", "G", "T")


@dataclass(frozen=True)
class SequenceVerdict:
    """Identity verdict for one probe sequence against the enrolled reference."""

    matched: bool
    replacement_suspected: bool
    hamming: int
    hamming_rate: float
    edit_distance: int
    jaccard: float
    clusters: tuple[tuple[int, int], ...]
    genome_length: int
    kmer_k: int
    method: str


def _validate_sequence(seq: str, label: str) -> None:
    if not isinstance(seq, str) or not seq:
        raise ValueError(f"{label} must be a non-empty string")
    unknown = set(seq) - set(DNA_ALPHABET)
    if unknown:
        raise ValueError(f"{label} contains non-DNA characters: {sorted(unknown)}")


def generate_genome(length: int, *, seed: int, gc: float = 0.5) -> str:
    """Deterministically synthesise a genome of ``length`` bases.

    Bases are drawn from {A, C, G, T} with the configured GC content (default
    0.5) using a seeded RNG, so the same ``seed`` reproduces the same genome.
    """
    if length < 1:
        raise ValueError("length must be >= 1")
    if not 0.0 <= gc <= 1.0:
        raise ValueError("gc must lie in [0, 1]")
    rng = np.random.default_rng(seed)
    probs = np.array([(1.0 - gc) / 2.0, (1.0 - gc) / 2.0, gc / 2.0, gc / 2.0])
    picks = rng.choice(DNA_ALPHABET, size=length, p=probs)
    return "".join(str(base) for base in picks)


def mutate_genome(
    reference: str,
    *,
    seed: int,
    n_substitutions: int = 0,
    cluster_length: int = 0,
    cluster_start: int | None = None,
) -> str:
    """Introduce deterministic point substitutions and one contiguous edit block.

    Args:
        reference: The enrolled reference genome.
        seed: RNG seed (deterministic mutation set).
        n_substitutions: Number of scattered single-base errors to add.
        cluster_length: Length of the contiguous gene-therapy edit block
            (0 disables it).
        cluster_start: Start index of the block; ``None`` picks one
            deterministically.
    """
    _validate_sequence(reference, "reference")
    if n_substitutions < 0:
        raise ValueError("n_substitutions must be >= 0")
    if cluster_length < 0:
        raise ValueError("cluster_length must be >= 0")
    rng = np.random.default_rng(seed)
    bases = list(reference)
    length = len(bases)
    occupied: set[int] = set()

    def _other_base(current: str) -> str:
        """Pick a deterministic replacement base different from ``current``."""
        return str(rng.choice([b for b in DNA_ALPHABET if b != current]))

    if cluster_length > 0:
        if cluster_start is None:
            cluster_start = int(rng.integers(0, max(1, length - cluster_length + 1)))
        if cluster_start < 0 or cluster_start + cluster_length > length:
            raise ValueError("cluster_start + cluster_length exceeds genome length")
        for offset in range(cluster_length):
            index = cluster_start + offset
            bases[index] = _other_base(bases[index])
            occupied.add(index)

    if n_substitutions > 0:
        available = [i for i in range(length) if i not in occupied]
        if n_substitutions > len(available):
            raise ValueError("n_substitutions exceeds available non-cluster positions")
        picks = rng.choice(available, size=n_substitutions, replace=False)
        for index in picks:
            bases[int(index)] = _other_base(bases[int(index)])
    return "".join(bases)


def hamming_distance(a: str, b: str) -> int:
    """Number of positions at which two equal-length sequences differ."""
    _validate_sequence(a, "a")
    _validate_sequence(b, "b")
    if len(a) != len(b):
        raise ValueError("hamming_distance requires equal-length sequences")
    return sum(1 for ca, cb in zip(a, b, strict=True) if ca != cb)


def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance via O(mn) dynamic programming.

    Counts insertions, deletions, and substitutions needed to turn ``a`` into
    ``b``; tolerant of length differences (indels).
    """
    _validate_sequence(a, "a")
    _validate_sequence(b, "b")
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current[j] = min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost)
        previous = current
    return previous[len(b)]


def kmer_jaccard(a: str, b: str, k: int) -> float:
    """Jaccard similarity of the k-mer fingerprints of two sequences.

    Returns ``0.0`` when either sequence is shorter than ``k`` (no k-mers to
    compare).
    """
    _validate_sequence(a, "a")
    _validate_sequence(b, "b")
    if k < 1:
        raise ValueError("k must be >= 1")
    if len(a) < k or len(b) < k:
        return 0.0
    # Both sequences are at least k long here, so each k-mer set is non-empty
    # and the union can never be empty — no unreachable empty-union branch.
    kmers_a = {a[i : i + k] for i in range(len(a) - k + 1)}
    kmers_b = {b[i : i + k] for i in range(len(b) - k + 1)}
    union = kmers_a | kmers_b
    return float(len(kmers_a & kmers_b) / len(union))


def mismatch_clusters(a: str, b: str, min_run: int = 1) -> tuple[tuple[int, int], ...]:
    """Contiguous runs of mismatching positions, as ``(start, end)`` spans.

    Only runs of at least ``min_run`` consecutive mismatches are returned.
    """
    _validate_sequence(a, "a")
    _validate_sequence(b, "b")
    if len(a) != len(b):
        raise ValueError("mismatch_clusters requires equal-length sequences")
    if min_run < 1:
        raise ValueError("min_run must be >= 1")
    clusters: list[tuple[int, int]] = []
    start: int | None = None
    for i, (ca, cb) in enumerate(zip(a, b, strict=True)):
        if ca != cb:
            if start is None:
                start = i
        elif start is not None:
            if i - start >= min_run:
                clusters.append((start, i))
            start = None
    if start is not None and len(a) - start >= min_run:
        clusters.append((start, len(a)))
    return tuple(clusters)


def verify_identity(
    reference: str,
    probe: str,
    *,
    k: int = 9,
    match_jaccard: float = 0.90,
    cluster_min: int = 12,
) -> SequenceVerdict:
    """Verify a probe genome against the enrolled reference.

    A probe is a suspected replacement when it carries a contiguous mismatch
    run of at least ``cluster_min`` bases (a coherent gene-therapy edit); it is
    matched only when its k-mer similarity clears ``match_jaccard`` AND no such
    block is present.
    """
    _validate_sequence(reference, "reference")
    _validate_sequence(probe, "probe")
    if len(reference) != len(probe):
        raise ValueError("verify_identity requires equal-length sequences")
    if k < 1:
        raise ValueError("k must be >= 1")
    if not 0.0 <= match_jaccard <= 1.0:
        raise ValueError("match_jaccard must lie in [0, 1]")
    if cluster_min < 1:
        raise ValueError("cluster_min must be >= 1")

    hamming = hamming_distance(reference, probe)
    rate = hamming / len(reference)
    lev = edit_distance(reference, probe)
    jac = kmer_jaccard(reference, probe, k)
    clusters = mismatch_clusters(reference, probe, min_run=1)
    long_clusters = tuple(c for c in clusters if c[1] - c[0] >= cluster_min)
    replacement_suspected = bool(long_clusters)
    matched = jac >= match_jaccard and not replacement_suspected
    return SequenceVerdict(
        matched=matched,
        replacement_suspected=replacement_suspected,
        hamming=hamming,
        hamming_rate=rate,
        edit_distance=lev,
        jaccard=jac,
        clusters=clusters,
        genome_length=len(reference),
        kmer_k=k,
        method="levenshtein-kmer-cluster",
    )
