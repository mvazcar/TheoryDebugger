"""Semantic and trust regressions for four-way results and explicit repairs."""
from fractions import Fraction
import unittest
from theorydebugger.backend import Answer, CVC5Backend
from theorydebugger.diagnose import classify, diagnose, identity
from theorydebugger.ir import Unsupported, canonical, parse
from theorydebugger.repair import augmented_problem, check_repair


class SequenceBackend:
    def __init__(self, *answers):
        self.answers = iter(answers)

    def check(self, *args):
        return next(self.answers)


class DiagnosisTests(unittest.TestCase):
    def test_four_cases_and_incomplete_pairs(self):
        for pair, expected in [(('present', 'absent'), 'true'), (('present', 'present'), 'mixed'),
                               (('absent', 'present'), 'false'), (('absent', 'absent'), 'inconsistent')]:
            self.assertEqual(classify(*pair), expected)
        for known in ('present', 'absent', 'unknown'):
            self.assertEqual(classify(known, 'unknown'), 'unknown')
            self.assertEqual(classify('unknown', known), 'unknown')

    def test_both_witnesses_are_preserved_and_not_promoted(self):
        p = parse({'variables': ['x'], 'goal': ['>', 'x', 0], 'witness': {'x': -2}})
        r = diagnose(p, CVC5Backend())
        self.assertEqual(r['classification'], 'unknown')
        self.assertEqual(r['solver']['classification'], 'mixed')
        self.assertEqual(r['cases']['refuting']['witness'], {'x': '-2'})
        for case in r['cases'].values():
            self.assertEqual(case['status'], 'present')
            self.assertEqual(case['evidence'], 'exact_evaluation')

    def test_algebraic_and_incomplete_evidence_stays_partial(self):
        p = parse({'variables': ['x'], 'goal': ['>', 'x', 0]})
        r = diagnose(p, SequenceBackend(Answer('sat'), Answer('unknown'),
                                       Answer('sat', {'x': Fraction(-1)})))
        self.assertEqual(r['classification'], 'unknown')
        self.assertEqual(r['cases']['satisfying']['status'], 'unknown')
        self.assertEqual(r['validity']['evidence'], 'exact_evaluation')
        p = parse({'variables': ['x'], 'assumptions': [['=', ['^', 'x', 2], 2], ['>', 'x', 0]], 'goal': True})
        r = diagnose(p, CVC5Backend())
        self.assertEqual(r['classification'], 'unknown')
        self.assertEqual(r['cases']['satisfying']['evidence'], 'solver_only')
        self.assertNotIn('witness', r['cases']['satisfying'])

    def test_repair_preserves_original_and_validates_combined_input(self):
        p = parse({'variables': ['x'], 'assumptions': [['>', 'x', 0]], 'goal': ['>', 'x', 1]})
        original = canonical(p)
        revised = augmented_problem(p, {'assumptions': [['>', 'x', 2]]})
        self.assertEqual(canonical(p), original)
        self.assertEqual(revised.goal, p.goal)
        self.assertEqual(revised.assumptions[:-1], p.assumptions)
        self.assertNotEqual(identity(p), identity(revised))
        self.assertEqual(identity(p), identity(parse({**original, 'name': 'renamed', 'witness': {'x': 4}})))
        for candidate in [{'goal': True, 'assumptions': []}, {'variables': ['y'], 'assumptions': []},
                          {'assumptions': [['>', 'y', 0]]}, {'assumptions': [True] * 30}]:
            with self.assertRaises(Unsupported):
                augmented_problem(p, candidate)

    def test_solver_only_repair_is_never_accepted(self):
        p = parse({'variables': ['x'], 'goal': ['>', 'x', 0]})
        r = check_repair(p, {'assumptions': [['>', 'x', 0]]}, CVC5Backend())
        self.assertFalse(r['accepted'])
        self.assertEqual(r['status'], 'unknown')
        self.assertEqual(r['repaired']['validity']['evidence'], 'solver_only')


if __name__ == '__main__':
    unittest.main()
