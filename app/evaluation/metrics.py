from __future__ import annotations


def precision(tp, fp):
    return tp / (tp + fp) if tp + fp else 0.0


def recall(tp, fn):
    return tp / (tp + fn) if tp + fn else 0.0


def f1(p, r):
    return 2*p*r/(p+r) if p+r else 0.0


def binary_accuracy(tp, tn, fp, fn):
    total=tp+tn+fp+fn
    return (tp+tn)/total if total else 0.0
