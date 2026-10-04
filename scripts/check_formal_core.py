"""Check the transcribed unary OM-KT source axioms without external dependencies.

This checks the displayed formulas, not the original Prover9/Mace4 runs.
Every axiom is universal and pointwise, with only unary predicates. Enumerating
all Boolean assignments to one element is therefore complete for these formulas
over arbitrary nonempty domains. No claim extends to the full Paraclete corpus.
"""

from itertools import product
from typing import Callable

Assignment = dict[str, bool]
Formula = Callable[[Assignment], bool]

NAMES = ("rational", "obligation", "seeks", "virtue", "wisdom", "violation", "deont", "zone3")
ASSIGNMENTS = [dict(zip(NAMES, values)) for values in product((False, True), repeat=len(NAMES))]
AXIOMS: dict[str, Formula] = {
    "E1": lambda x: not x["rational"] or x["obligation"],
    "E2": lambda x: not x["obligation"] or x["seeks"],
    "E3": lambda x: not (x["virtue"] and x["wisdom"]) or x["obligation"],
    "E4": lambda x: not x["violation"] or not x["virtue"],
    "E5": lambda x: x["seeks"] or x["violation"],
    "E6": lambda x: not x["deont"] or x["obligation"],
    "I3": lambda x: not x["zone3"] or x["deont"],
    "EB": lambda x: not x["deont"] or not x["virtue"],
    "weak_E6": lambda x: not x["deont"] or x["seeks"],
}
GOALS: dict[str, Formula] = {
    "EIT": lambda x: not (x["virtue"] and x["wisdom"]) or x["seeks"],
    "DCT": lambda x: not (x["rational"] and not x["seeks"]) or not x["virtue"],
    "EDT": lambda x: not x["deont"] or x["seeks"],
    "CSC": lambda x: not x["zone3"] or x["obligation"],
    "CSC_full": lambda x: not x["zone3"] or x["seeks"],
    "EBE": lambda x: not x["zone3"] or (x["seeks"] and not x["virtue"]),
}


def models(premises: tuple[str, ...]) -> list[Assignment]:
    """Return every satisfying assignment for the named premises."""
    return [x for x in ASSIGNMENTS if all(AXIOMS[name](x) for name in premises)]


def counterexamples(premises: tuple[str, ...], goal: Formula) -> list[Assignment]:
    """Return witnesses that satisfy premises and falsify the goal."""
    return [x for x in models(premises) if not goal(x)]


def require(condition: bool, description: str) -> None:
    """Raise on an unexpected result, even when Python optimizations are enabled."""
    if not condition:
        raise RuntimeError(description)
    print(f"PASS: {description}")


def main() -> None:
    """Check consistency, axiom independence, implications, and source caveats."""
    core = ("E1", "E2", "E3", "E4", "E5", "E6")
    complete = core + ("I3", "EB")
    require(bool(models(complete)), "E1-E6 + I3 + EB are satisfiable")
    require(any(x["zone3"] for x in models(complete)), "satisfiable with Zone3 active")
    require(any(x["virtue"] and x["wisdom"] for x in models(core)), "satisfiable with Virtue and Wisdom active")
    for name in core:
        others = tuple(n for n in core if n != name)
        require(bool(counterexamples(others, AXIOMS[name])), f"{name} independent of the other five core axioms")
    for name, goal in GOALS.items():
        require(not counterexamples(complete, goal), f"core + I3 + EB entail {name}")
    for goal in ("EIT", "DCT"):
        require(not counterexamples(("E4", "E5"), GOALS[goal]), f"E4 + E5 alone entail {goal}")
    require(not counterexamples(("E1", "E2"), GOALS["DCT"]), "E1 + E2 alone entail DCT")
    require(not any(x["rational"] and not x["seeks"] for x in models(("E1", "E2"))), "DCT antecedent impossible under E1 + E2")
    weak = ("E1", "E2", "E3", "E4", "E5", "I3", "EB", "weak_E6")
    witnesses = counterexamples(weak, GOALS["CSC"])
    require(bool(witnesses), "weak bridge does not entail obligation-form CSC")
    require(not counterexamples(weak, GOALS["CSC_full"]), "weak bridge does entail behavioral CSC_full")
    print("Weak-bridge CSC counterexample:", witnesses[0])
    print("Checked all 256 assignments; no model calls or theorem-prover rerun.")


if __name__ == "__main__":
    main()
