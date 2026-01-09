# The Book of NEEMA
**Engineering the Impossible**

> "We shape our tools, and thereafter our tools shape us."

---

## Table of Contents

1.  [Part I: The Learner's Guide](#part-i-the-learners-guide)
    *   [Introduction](#introduction)
    *   [Your First Entity](#your-first-entity)
    *   [The Philosophy: Knowledge vs. Data](#the-philosophy)
2.  [Part II: The User Manual](#part-ii-the-user-manual)
    *   [Installation & CLI](#installation--cli)
    *   [The NEEMA Language](#the-neema-language)
        *   [Governance Header](#governance-header)
        *   [Entities & Properties](#entities--properties)
        *   [Symbolic Ranges](#symbolic-ranges)
        *   [Invariants](#invariants)
    *   [The IGIGI Reasoner](#the-igigi-reasoner)
    *   [Interoperability (ALOGI & Blender)](#interoperability)
3.  [Part III: The Developer's Bible](#part-iii-the-developers-bible)
    *   [Architecture Overview](#architecture-overview)
    *   [The Governor](#the-governor)
    *   [The Reasoner (Z3)](#the-reasoner-z3)
    *   [Extending the Standard](#extending-the-standard)

---

# Part I: The Learner's Guide

## Introduction
Welcome to **NEEMA** (Neural Episteme for Engineering & Manufacturing Automation).

NEEMA is not just a programming language; it is a **Constitutional Language** for physical objects. In most languages (Python, C++), you write code to *do* things. In NEEMA, you write code to define what things *are* and what they *must be*.

It enforces:
1.  **Governance**: Who are you? Do you have clearance to build this?
2.  **Physics**: Will this break under load?
3.  **Geometry**: Does this shape match the mathematical requirements?

## Your First Entity
Create a file called `simple_beam.neema`:

```rust
// 1. Governance Header (Required)
meta {
    id: "urn:my:first:beam"
    authority: "SELF"
    intent: "learning"
}

// 2. Entity Definition
entity StructuralBeam {
    // 3. Properties (What is it made of?)
    primitive mat: Material = "AISI_316L"
    property length: Float = 10.0
    property load: Float = 500.0

    // 4. Invariants (The Constitution)
    invariant safety_check {
        // "Yield Strength" is automatically injected by the Material
        require( load < (mat_yield_strength * 0.5) )
        else error( "Beam adds too much load for this material!" )
    }
}
```

Run it:
```bash
python3 neema/neema.py simple_beam.neema
```
If it passes, you know your design is safe to build.

## The Philosophy
We are moving from **CAD** (Computer Aided Design) to **CAE** (Computer Automated Epistemology).
*   **Old Way**: Draw a shape. Hope it works. Simulation checks it later.
*   **NEEMA Way**: Define the constraints. The shape is only valid if it satisfies them.

---

# Part II: The User Manual

## Installation & CLI

### Prerequisites
*   Python 3.8+
*   Z3 Solver (`pip install z3-solver`)

### Usage
```bash
python3 neema/neema.py <file.neema> [flags]
```
**Flags:**
*   `--export`: Generates an `.alogi.json` file for use in other tools.

## The NEEMA Language

### Governance Header
Every file **must** start with a `meta` block. This allows organizations to track "High Risk" designs.
```rust
meta {
    id: "urn:uuid:..."
    authority: "IGIGI_LABS"
    intent: "civilian_energy" | "military" | "medical"
    risk_class: "benign" | "dual_use"
}
```
*   **Risk Class**: If set to `dual_use`, the compiler runs stricter checks.

### Entities & Properties
Entities represent physical objects.
```rust
entity Gearbox {
    property ratio: Float = 3.0
    property housing_material: String = "Aluminum"
}
```

### Symbolic Ranges (The "Magic")
You don't always know the exact value. You can define a **Design Space**.
```rust
property thickness: Float = 1.0 .. 5.0
```
This tells the **IGIGI Reasoner**: *"I don't care what the thickness is, as long as it is between 1mm and 5mm AND satisfies all other rules."*
IGIGI will then **solve** for the optimal thickness.

### Invariants
Rules that must never be broken.
```rust
invariant heat_limit {
    require( (temp < 100.0) or (material == "Tungsten") )
}
```
Supports: `and`, `or`, `not`, nested parentheses `( )`.

## The IGIGI Reasoner
IGIGI is the brain. It runs in two modes:
1.  **Validator**: Checks if your specific values are wrong.
2.  **Solicitor**: Takes your *Symbolic Ranges* and calculates specific values that work.

**Example**:
Input: `x = 1..10`, `require(x > 5)`
Output: `x = 6`

## Interoperability
NEEMA is the Source of Truth. **ALOGI** is the bridge.
1.  Run `neema.py file.neema --export` -> `file.alogi.json`.
2.  **Blender**: Run `blender --python neema/connectors/blender_connector.py -- file.alogi.json`.
    *   This imports your verified design into 3D space.

---

# Part III: The Developer's Bible

## Architecture Overview
The compiler (`neema/`) is a pure Python implementation.

1.  **Lexer** (`lexer.py`): Regex-based tokenizer. Handles `primitive`, `..` ranges.
2.  **Parser** (`parser.py`): Recursive descent parser. Produces a flexible AST.
3.  **Governor** (`governor.py`):
    *   **Pass 1**: Governance checks (User clearance vs Intent).
    *   **Pass 2**: Basic Physics calculation (using Python `eval`).
    *   *Note*: Governor uses "Midpoints" for ranges to do quick sanity checks.
4.  **Reasoner** (`reasoner.py`):
    *   **Formal Verification**: Converts AST to **Z3 Constraints**.
    *   **Solver**: Detects logical contradictions and solves for free variables.
5.  **Exporter** (`alogi.py`): Serializes the "Sanctified" AST to JSON.

## The Reasoner (Z3)
The Reasoner translates NEEMA concepts into SMT (Satisfiability Modulo Theories) logic.
*   `Float` -> `z3.Real`
*   `..` Range -> `solver.add(x >= min, x <= max)`
*   `primitive mat: Material` -> Look up in `MATERIAL_DB`, create constants (e.g., `mat_yield_strength`), inject equality constraints.

**Integer Inference**:
The Reasoner uses a heuristic: if a variable name ends in `_teeth` or `_count`, it declares it as a `z3.Int` instead of `z3.Real`.

## Extending the Standard
To add new materials:
1.  Edit `neema/governor.py` -> `MATERIAL_DB`.
2.  Edit `neema/reasoner.py` -> `MATERIAL_DB` (Keep them in sync!).
    *   *Future Work*: Move DB to a shared JSON file.

To add new logic operators:
Modify `NeemaLexer.TOKEN_SPECS` and `NeemaReasoner.process_entity` string replacement logic.
