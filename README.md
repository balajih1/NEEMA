# IGIGI Synthesis Engine - v0.4 (Phase 4)

**IGIGI** is now capable of **Engineering Synthesis**.
It can solve for unknown design parameters (like gear teeth counts) that satisfy high-level constraints.

## New in v0.4
*   **Integer Inference**: Automatically treats `_teeth` or `_count` variables as Integers in the solver.
*   **Material Injection**: The Reasoner now understands `primitive mat: Material` and injects physics constants into the Z3 context.
*   **Gearbox Demo**: `neema/examples/gearbox.neema` demonstrates automatic gear train design.

## Usage
Run the Gearbox Demo:
```bash
python3 neema/neema.py neema/examples/gearbox.neema --export
```

## How It Works
1.  **Define**: You specify a range (`10 .. 50`) and a Ratio (`1:3`).
2.  **Reason**: IGIGI uses Z3 to find integers (e.g., 10 and 30) that fit.
3.  **Export**: The solved values are exported to `gearbox.alogi.json`.
