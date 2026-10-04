# Review of the epistemic formal core

October 3, 2026 · Scope: displayed Vector 6/7 formulas and their dependency explanations

## 1. Sources and method

Reviewed the complete six-page Vector 6 and four-page Vector 7 reports from the author's Paraclete repository, including visual inspection of the relevant proof and axiom pages. Consulted the integrated manuscript's epistemic sections. Original source documents were not edited.

- [Vector 6: Epistemic-Ethical Bridge](https://github.com/angrysky56/Toward-Transcendent-Moral-Instrumentality/blob/1d06900e0e2c52189ea568ea60b65f4eb3ed5c0e/logic/paraclete_vector6_epistemic_bridge.pdf)
- [Vector 7: Epistemic-Deontological Bridge](https://github.com/angrysky56/Toward-Transcendent-Moral-Instrumentality/blob/1d06900e0e2c52189ea568ea60b65f4eb3ed5c0e/logic/paraclete_vector7_epistemic_deontological.pdf)

The revision identifier above was read from the local source checkout; both pinned GitHub file pages were also reachable during review. SHA-256 identifies the actual reviewed local bytes:

| Document | SHA-256 |
| --- | --- |
| Vector 6 | `5b698628222e2962812fb195d6ec1027c1b71ae3c090c5b1408b0f2c8097f925` |
| Vector 7 | `d2ad5bfb4385c159b1c7ad3dd03f463376dc84122c3cdd8c843ac54aa66e7945` |
| OM-KT original white paper | `cd2e5ba0cd8c79f01e9373e8254421aaa849c25305229123b7a0959e6d8a1f14` |

The inspected source checkout contained PDF verification reports, but no standalone Vector 6/7 Prover9 inputs, full raw solver outputs, or Mace4 interpretation files were located. Prover9 and Mace4 executables were not available on the current command path. Accordingly, historical proof lengths, timings, and exact solver traces were **not reproduced**.

Instead, the displayed unary formulas were transcribed into a small standard-library checker. All 256 truth assignments to eight predicates were enumerated. Because these formulas are universally quantified, pointwise, and contain only unary predicates without cross-element relations or existential requirements, this enumeration is complete for the transcribed fragment over nonempty domains. It is not an audit of every axiom in the larger framework.

Run from this project's directory:

```sh
python3 scripts/check_formal_core.py
```

The checker is self-contained: it does not read a sibling project, contact a service, or call a model.

## 2. Formulas checked

All formulas below are universally quantified over `x`:

```text
E1: RationalAgent(x) -> HasEpistemicObligations(x)
E2: HasEpistemicObligations(x) -> SeeksDisconfirmation(x)
E3: TierVirtue(x) & Wisdom(x) -> HasEpistemicObligations(x)
E4: ViolatesEpistemicObligation(x) -> not TierVirtue(x)
E5: not SeeksDisconfirmation(x) -> ViolatesEpistemicObligation(x)
E6: TierDeont(x) -> HasEpistemicObligations(x)
I3: InZone3(x) -> TierDeont(x)
EB: TierDeont(x) -> not TierVirtue(x)
```

`I3` and `EB` are the bridge and Emergency Brake directions used in the Vector 7 dependency table; the complete affect/zone theory was not imported.

## 3. Results that hold

The transcribed E1-E6 core is satisfiable, and each of its six axioms is independent of the other five. The core together with I3 and EB is also satisfiable, including an assignment with Zone 3 active. Thus, the checked Clear Sight results are not consequences of an inconsistent premise set.

| Result | Sufficient premises | Finding |
| --- | --- | --- |
| EDT: TierDeont -> SeeksDisconfirmation | E6, E2 | Holds |
| CSC: InZone3 -> HasEpistemicObligations | I3, E6 | Holds |
| CSC-full: InZone3 -> SeeksDisconfirmation | I3, E6, E2 | Holds |
| EBE: InZone3 -> SeeksDisconfirmation & not TierVirtue | I3, E6, E2, EB | Holds |
| EIT: TierVirtue & Wisdom -> SeeksDisconfirmation | E4, E5 alone suffice; E3, E2 provide another path | Holds; dependency explanation needs correction |
| DCT: RationalAgent & not SeeksDisconfirmation -> not TierVirtue | E4, E5 alone suffice; E1, E2 also entail it vacuously | Holds; interpretation needs qualification |

These results justify retaining the formal conditional structure as design rationale. They do not establish prompt effectiveness, actual disconfirmation behavior, or the truth of the chosen normative premises.

## 4. Corrections needed in source explanations

### EIT does not need E3

Vector 6, section 3.1, names E3/E4/E5 as the used premises and says the direct Wisdom-to-obligation path suffices without E2. Its displayed summary nevertheless includes E2. More importantly, E4 and E5 already entail:

```text
not SeeksDisconfirmation -> ViolatesEpistemicObligation -> not TierVirtue
```

By classical contraposition, `TierVirtue -> SeeksDisconfirmation`. Adding Wisdom to the antecedent gives EIT without E3. The separate path E3 followed by E2 also proves EIT, but requires E2. Axiom independence is not the same as necessity for a particular theorem.

### DCT's rational-agent antecedent is impossible under E1/E2

E1/E2 give `RationalAgent -> SeeksDisconfirmation`. Therefore `RationalAgent & not SeeksDisconfirmation` cannot occur in any model satisfying them. DCT is true along this path because its antecedent is impossible, not because the formulas represent an observed transition from rational virtue to collapse.

E4/E5 separately establish the non-seeking-to-non-virtue implication without E1/E2 or RationalAgent. Consequently, the source statement that E1/E2 are necessary for DCT is incorrect. The theorem can remain a conditional exclusion statement; it should not be presented as a dynamic account without an explicit temporal or violation model.

### The routes are not strictly disjoint

Vector 7, section 4.3, and the integrated manuscript describe the three pathways as using strictly disjoint axiom subsets. The paths to disconfirmation via agency, wisdom/obligation, and deontology all use E2. Distinct antecedents and independent bridge axioms are meaningful; disjoint proof dependencies are not established by these paths.

### E6 is an added axiom, not an independently proved premise

Vector 7 correctly introduces E6 as a new axiom and reports its independence. Some surrounding labels say "proved V7." The precise statement is: E6 is stipulated as a governance premise; downstream results follow from it and the other displayed axioms. Independence means the old axioms do not supply that premise.

### Weak versus strong Clear Sight

Replacing E6 with `TierDeont -> SeeksDisconfirmation` fails to entail the **obligation-form** CSC, because seeking disconfirmation does not imply the obligation predicate. However, together with I3 it still entails **behavioral** CSC-full. The stronger axiom supports an additional formal obligation property; it is not required for the narrower behavioral implication.

A one-element countermodel to obligation-form CSC under the weak bridge sets Zone3, TierDeont, and SeeksDisconfirmation true, with every other predicate false. It satisfies E1-E5, I3, EB, and the weak bridge, but falsifies `InZone3 -> HasEpistemicObligations`. The checker prints this witness.

## 5. Operational interpretation for OM-KT

Use the checked implication as a design requirement: when a serious constraint activates, the system must preserve relevant evidence checking. Test whether outputs and actions satisfy that requirement.

The predicates do not encode degrees of scrutiny, time costs, actual access to evidence, or proportionality. In particular, these formulas establish preservation of the requirement, not a quantitative increase in the burden of proof. Those stronger operational rules need separate specification and evaluation.

Do not transfer the Emergency Brake's `not TierVirtue` predicate into a blanket instruction to abandon wisdom, integrity, empathy, or fairness. In OM-KT, suspend unconstrained optimization while retaining those practical criteria. The source's tier-status semantics and the desired agent behavior must be distinguished explicitly.

The research plan consequently treats the formal core as a clear conditional specification, with corrections to its commentary. It does not treat symbolic labels such as SeeksDisconfirmation as evidence that an LLM actually performs the relevant checks.
