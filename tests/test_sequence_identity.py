"""DNA sequence identity verification tests (real data, no mocks)."""

from __future__ import annotations

import pytest

from die_another_day import sequence_identity as si


def test_generate_genome_only_dna_and_length() -> None:
    genome = si.generate_genome(100, seed=7)
    assert len(genome) == 100
    assert set(genome) <= set(si.DNA_ALPHABET)


def test_generate_genome_deterministic() -> None:
    a = si.generate_genome(50, seed=3)
    b = si.generate_genome(50, seed=3)
    assert a == b


def test_generate_genome_validation() -> None:
    with pytest.raises(ValueError):
        si.generate_genome(0, seed=1)
    with pytest.raises(ValueError):
        si.generate_genome(10, seed=1, gc=1.5)


def test_mutate_genome_scattered_count() -> None:
    ref = si.generate_genome(1000, seed=7)
    mutated = si.mutate_genome(ref, seed=7, n_substitutions=5)
    assert si.hamming_distance(ref, mutated) == 5


def test_mutate_genome_cluster_plus_scattered() -> None:
    ref = si.generate_genome(1500, seed=7)
    mutated = si.mutate_genome(ref, seed=7, n_substitutions=5, cluster_length=12)
    assert si.hamming_distance(ref, mutated) == 17


def test_mutate_genome_validation() -> None:
    ref = si.generate_genome(100, seed=7)
    with pytest.raises(ValueError):
        si.mutate_genome(ref, seed=7, n_substitutions=-1)
    with pytest.raises(ValueError):
        si.mutate_genome(ref, seed=7, cluster_length=-1)
    with pytest.raises(ValueError):
        si.mutate_genome(ref, seed=7, cluster_length=10, cluster_start=95)
    with pytest.raises(ValueError):
        si.mutate_genome(ref, seed=7, n_substitutions=200)


def test_mutate_genome_empty_or_bad_alphabet() -> None:
    with pytest.raises(ValueError):
        si.mutate_genome("", seed=7)
    with pytest.raises(ValueError):
        si.mutate_genome("ACGX", seed=7)


def test_hamming_known() -> None:
    assert si.hamming_distance("AACC", "AACG") == 1
    assert si.hamming_distance("AAAA", "AAAA") == 0
    assert si.hamming_distance("AAAA", "TTTT") == 4


def test_hamming_validation() -> None:
    with pytest.raises(ValueError):
        si.hamming_distance("AAA", "AA")
    with pytest.raises(ValueError):
        si.hamming_distance("", "AA")
    with pytest.raises(ValueError):
        si.hamming_distance("AAA", "AAN")


def test_edit_distance_known() -> None:
    assert si.edit_distance("AAGT", "AGGT") == 1  # substitution
    assert si.edit_distance("ACGT", "ACGT") == 0
    assert si.edit_distance("ACG", "ACGT") == 1  # insertion
    assert si.edit_distance("ACGT", "A") == 3  # deletions


def test_edit_distance_empty_rejected() -> None:
    with pytest.raises(ValueError):
        si.edit_distance("", "AAA")


def test_edit_distance_validation() -> None:
    with pytest.raises(ValueError):
        si.edit_distance("ACGT", "ACX")


def test_kmer_jaccard_equal() -> None:
    seq = si.generate_genome(200, seed=7)
    assert si.kmer_jaccard(seq, seq, 9) == pytest.approx(1.0)


def test_kmer_jaccard_shorter_than_k_zero() -> None:
    assert si.kmer_jaccard("AC", "AC", 5) == 0.0


def test_kmer_jaccard_validation() -> None:
    with pytest.raises(ValueError):
        si.kmer_jaccard("ACGT", "ACGT", 0)


def test_mismatch_clusters() -> None:
    # "AACCT" vs "AAGGT": mismatches at 2 and 3 => one cluster of {2,3}.
    clusters = si.mismatch_clusters("AACCT", "AAGGT")
    assert clusters == ((2, 4),)


def test_mismatch_clusters_min_run() -> None:
    clusters = si.mismatch_clusters("AACCT", "AAGGT", min_run=3)
    assert clusters == ()


def test_mismatch_clusters_trailing_run() -> None:
    # A run that extends all the way to the end of the sequence.
    assert si.mismatch_clusters("AAAA", "TTTT") == ((0, 4),)


def test_mismatch_clusters_validation() -> None:
    with pytest.raises(ValueError):
        si.mismatch_clusters("AC", "CA", min_run=0)
    with pytest.raises(ValueError):
        si.mismatch_clusters("AC", "A")


def test_verify_genuine_matches() -> None:
    ref = si.generate_genome(1500, seed=7)
    probe = si.mutate_genome(ref, seed=7, n_substitutions=5)
    verdict = si.verify_identity(ref, probe)
    assert verdict.matched is True
    assert verdict.replacement_suspected is False
    assert verdict.jaccard >= 0.9


def test_verify_replaced_suspected() -> None:
    ref = si.generate_genome(1500, seed=7)
    probe = si.mutate_genome(ref, seed=7, n_substitutions=5, cluster_length=12)
    verdict = si.verify_identity(ref, probe)
    assert verdict.replacement_suspected is True
    assert verdict.matched is False


def test_verify_identical() -> None:
    ref = si.generate_genome(100, seed=7)
    verdict = si.verify_identity(ref, si.mutate_genome(ref, seed=7))
    assert verdict.matched is True
    assert verdict.hamming == 0
    assert verdict.edit_distance == 0


def test_verify_validation() -> None:
    ref = si.generate_genome(100, seed=7)
    with pytest.raises(ValueError):
        si.verify_identity(ref, ref, k=0)
    with pytest.raises(ValueError):
        si.verify_identity(ref, ref, match_jaccard=1.5)
    with pytest.raises(ValueError):
        si.verify_identity(ref, ref, cluster_min=0)
    with pytest.raises(ValueError):
        si.verify_identity(ref, ref[:-1])
