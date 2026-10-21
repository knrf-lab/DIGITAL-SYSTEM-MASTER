# Digital Door Lock – Nexys A7-100T (65-point baseline)

Default password: **1-2-3-4** (enter one digit at a time on SW[3:0], SW0 = LSB).

## Files
| File | Purpose |
|---|---|
| `sources_1/new/Door_Lock_Top.vhd` | Top level, board pins → modules (**set as Top**) |
| `sources_1/new/Debouncer.vhd` | Synchronizer + debounce + 1-clock press pulse |
| `sources_1/new/Lock_FSM.vhd` | Moore FSM: digit entry, password register, comparator |
| `sim_1/new/tb_Door_Lock.vhd` | Self-checking testbench (simulation only) |
| `constrs_1/new/pinDefinition.xdc` | Pin constraints |

## Vivado setup
1. New RTL project, part **xc7a100tcsg324-1**.
2. Add the 3 design sources, the XDC as a constraint, and the testbench as a **simulation source**.
3. Simulation: Run Behavioral Simulation → type `run all` in the Tcl console. Expect `ALL TESTS PASSED` (~25 µs).
4. Generate Bitstream → Open Hardware Manager → Program Device.

## Board test checklist
| # | Action | Expected |
|---|---|---|
| 1 | Press CPU_RESET | LD15 (LOCKED) on, all else off |
| 2 | SW=0001, BTNC | LD0 on |
| 3 | SW=0010, BTNC / 0011, BTNC / 0100, BTNC | LD0–LD3 on, one per press |
| 4 | BTNC (submit) | LD14 (UNLOCKED) on, LD15 off, LD0–3 off |
| 5 | Change SW, press BTNC | Nothing changes (blocked) |
| 6 | BTNU | LD15 on, LD14 off |
| 7 | Enter 1-2-4-3, BTNC | LD13 (WRONG) + LD15 on |
| 8 | BTNC | LD13 off, LD0 still off |
| 9 | SW=1010, BTNC | LD0 stays off (invalid ignored) |
| 10 | Enter 2 digits, BTND | LD0–3 off |
| 11 | One press of BTNC | Exactly one progress LED step (debounce works) |
