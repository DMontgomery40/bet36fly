# Finite Aso source protocol: declared activity and clock conventions

September 13, 2026; independent source interpretation from `7698c15`.
No model, fit, saved-history or neural experiment was run for this review.

**The selected calculation is seven protocols × four pathway settings: 28
finite conditions.** Root selected this matrix before any outcomes, including
an explicit correction of Figure 7's duplicated time label. The complete
copied manuscript and correction were read, including Methods, figure
captions, author response and references.
The actual Figure 6, 7, 8 and Figure 8 supplement 1 panels were inspected in
the official version-3 figure PDF, pages 27, 29, 31 and 32. This is an
equation-component calculation with declared activity conventions; it is
not recovered author-code execution or behavioral reproduction.

Primary: [Aso et al. 2019, eLife 49257](https://elifesciences.org/articles/49257).
Root retrieved the [official article API](https://api.elifesciences.org/articles/49257)
and [version-3 figures](https://cdn.elifesciences.org/articles/49257/elife-49257-figures-v3.pdf)
on September 13, 2026. The figure PDF has SHA256
`19fdc72e1175362926b56f2dad0f86d72b3c6036bbf1a876c6ee6fbc3008f5e4`.
The [2020 correction](https://doi.org/10.7554/eLife.64094) changes RNA-seq
processing, not these model equations or training figures.

## Experimental and model activity are distinct

Figure 1C specifies one minute of odor with thirty one-second red-light
pulses, then one minute without odor/light, then one minute of the other
odor without light. The light is 627 nm, 34.9 µW/mm². Methods used groups
of about 20 female flies, age 4–10 days, and reciprocal OCT/MCH assignments.
These are optogenetic stimulation conditions, not dopamine concentration
or observed DAN spike counts.

Equations 1–3 instead switch by KC/DAN **activity level**. They do not give
a light-to-activity transfer or explicitly state whether every dark second
interrupts induction. Figure 8B draws light pulses, but Figure 8A labels
KC/DAN ON/OFF states; this does not resolve the effective activity convention.
For the selected calculation, declare DAN active throughout each indicated
10- or 60-second stimulation window, including DAN-only bouts. This is a model-level interpretation,
not a claim that light was continuously on. Do not divide rates by two,
replace each light pulse with a neuronal spike, or tune either convention
against results. A separate literal pulse-train calculation would be a
different prespecified input convention.

## Selected single finite matrix

Times below are **seconds from the start of the complete assay**. Intervals
are half-open. The common Figure 6A test occupies `[840,900)` seconds.

| Acquisition condition | Odor A with DAN activity | Odor B without DAN activity |
| --- | --- | --- |
| Naïve control | None | None |
| 1 × 10 s | `[60,70)` | `[180,190)` |
| 1 × 1 min | `[60,120)` | `[180,240)` |
| 3 × 1 min | `[60,120)`, `[300,360)`, `[540,600)` | `[180,240)`, `[420,480)`, `[660,720)` |

Add three Figure 7 branches: reversal, odor-only and DAN-only, with the
explicit schedule below. Cross all seven protocols with **both pathways,
DA-only/NO-null, NO-only/DA-null, and neither pathway**. The last is an added
analytical control, not an additional claimed biological null experiment.
Initialize all four states to zero once per condition; never reset between
odors, pairings or tests. Use the fixed component's
published `A_D=4.3/60`, `A_N=.96/60`, `B_D=.26/60`, `B_N=.16/60` per second,
and `tau_D=30`, `tau_N=600` seconds. Null branches are absent from the start,
not acute removal of an already populated state. This is an idealization
of the source's TH-null and NOS-inhibited manipulations.

Retain four KC classes: A-only, B-only, shared and neither. Their activity
is defined by membership in the named odor windows; shared KCs respond to
either odor. These are analytical classes, not a newly sampled finite odor
population. Outside paired or DAN-only windows DAN is inactive, so the
contract holds latent effects fixed while expression continues. During the
odor-choice test DAN remains inactive; presentation of either odor cannot
change latent state under this equation component. Do not invent simultaneous
odor activation as a measurement of what each freely moving fly experienced.

Save all four states and normalized weight at every segment boundary and
at each test's start, start of its last 30 seconds, and end. For Figure 6
these times are 840, 870 and 900 s. These are endpoint measurements, not
time-averaged weights or behavioral PI. Preserve finite expression through
the entire test; no automatic infinite quiet tail.

## What may be checked

Numerical agreement with an independent exact/high-precision solution is
a valid implementation requirement. State bounds, absent-branch zeros,
retained latent memory and unchanged naïve states are model invariants.
The source's qualitative comparisons are faster DA-associated induction,
slower accumulation of NO-associated effects and opposite signs in the two
isolated pathways (Figure 6B and Figure 8C). Save disagreements without
retuning; do not infer experimental significance from a deterministic state.

Experimental PI uses odor-quadrant fly counts, reciprocal odor assignments,
and the final 30 seconds of each test (Figure 1D–G and Figure 2 caption).
The model adds a separate odor-population/MBON/softmax construction: random
10% KC activity, `r=(1/N_KC)Σw_i s_i`, and fitted readout gains 14.8/12.6
for isolated pathways or 14.3 for the multiplicative model (Methods,
“Inferring parameters…”). No author code, exact odor realizations or
behavioral raw-value table was recovered here. Do not claim exact Figure 8
PI reproduction or add its readout gain to the existing circuit. The proposed
four KC-class outputs deliberately stop before that readout choice.

## Reversal, spacing and exclusions

Figure 7A's upper schematic is unambiguous: A+ at minutes `[1,2)`, `[7,8)`,
`[11,12)`; B at `[3,4)`, `[9,10)`, `[13,14)`; Tests 1 and 2 at `[5,6)` and
`[15,16)`. Thus its three initial pairings differ from Figure 6A's schedule.
Subsequent branches are reversed odor pairing, odors alone, or DAN activity
alone; the figure shows three such interventions with a probe after the
first and third. Figure 7B–D qualitatively reports faster reversal and
DAN-only updating in wild type, and no significant odor-only change.

The lower axis, however, prints **16,17,18,19,20,20,21,…31** at equally
spaced ticks. The selected contract explicitly uses the continuous one-minute
grid: Tests 3 and 4 are `[21,22)` and `[31,32)`. Its reverse-paired B windows
are `[17,18)`, `[23,24)`, `[27,28)`; unpaired A windows are `[19,20)`,
`[25,26)`, `[29,30)`. Odor-only uses those same odor windows without DAN;
DAN-only uses only the three B-window times as DAN activation with no odor.
All Figure 7 conditions retain the same initial training and Tests 1–2,
then continue to 32 min (1920 s) without resets. This is a declared axis
correction, not an exact reproduction of the contradictory printed labels.

Figure 8 supplement 1 also describes “first two” and “second two” pairings
despite Figure 7's three physical induction bouts
per phase; it appears to refer to the four observation groups, but that is
an interpretation. Methods additionally refers to nonexistent “Figure 7F”.
These defects do not invalidate the equations; they prevent claiming an
unqualified exact reversal-protocol reproduction. The chosen clock and
physical three-bout count are fixed before results and must remain visible
in the result's interpretation.

Figure 6 includes 10× spaced training and a 4× condition absent from the
Methods fit list; their full exact schedules are unnecessary for this first
matrix. Exclude 24-hour retention: Figure 8E uses separately fitted background
DAN rates, distinct from true quiet and from the frozen evoked `B` values.
The source also explicitly fails to explain enhanced long-term consolidation
after 10× spaced training. Figure 6C's 1/3/5/10-minute delayed behavioral
detectability does not make the component's early NO state identically zero.

No matrix outcome would calibrate somatic spikes, receptors, NO diffusion,
PAM12 cotransmission, or a 400-ms MaleCNS episode. The accepted masks, gains,
qualification criterion and previously failed screens remain unchanged.
