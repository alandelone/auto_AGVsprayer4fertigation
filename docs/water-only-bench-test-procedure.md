# Water-Only Bench Test Procedure

## Scope

FEAT-005 defines the safe bench procedure before any fertilizer or chemical test. Use clean water only.

## Preconditions

- Pump and valves are on a fused 12 V actuator rail.
- Pixhawk/Raspberry Pi logic power is isolated from actuator power.
- Physical e-stop cuts pump/valve power independent of software.
- Low-liquid and pressure interlocks are wired or simulated before spray tests.
- No one stands in the spray fan during pressure or catch-cup tests.

## Ordered Tests

1. **Dry wiring inspection**: actuator power off; confirm fuses, polarity, flyback protection, hose clamps, labels, and no direct Pixhawk-to-load wiring.
2. **E-stop cut test**: latch e-stop and verify pump/valves cannot energize.
3. **Prime/leak test**: fill with clean water; pulse pump below 40 PSI; inspect fittings and hose movement.
4. **Pressure trips**: verify low pressure <15 PSI and high pressure >70 PSI shut pump/valves off with no automatic resume.
5. **Low-liquid interlock**: simulate or trigger low liquid; pump/valves must shut off and require manual reset.
6. **Zone valves**: at 40 PSI, command LEFT, RIGHT, BOTH, OFF; confirm only requested nozzle(s) spray.
7. **Catch-cup flow**: at 40 PSI, collect each nozzle for 60 seconds; target each 11002-class nozzle is 0.60–0.90 L/min; left/right difference <=20%.
8. **Fault safe state**: during LEFT/BOTH spray, trigger e-stop, low-liquid, and pressure fault; every fault must produce pump off + both valves closed + operator review.

## Pass Rule

All tests must be PASS in `templates/bench-test-log.template.json` before fertilizer or chemical tests.

## Stop Conditions

- Leak near electrical wiring.
- Pump runs dry or pressure oscillates violently.
- E-stop fails to cut actuator power.
- Valve leaks when commanded closed.
- Pressure exceeds 70 PSI or sensor reading is unstable/untrusted.
