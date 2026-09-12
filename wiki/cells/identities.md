---
type: anatomical-identities
updated: 2026-09-12
status: locally-derived-anatomy
---
# Exact cell identities and KC subtypes

Generated from [atlas.json](data/atlas.json) and [neurons.csv](data/neurons.csv), which retain source hashes and raw labels. All counts are for this retained MaleCNS graph. Cells and directed edges are different counts.

## KC subtypes

| Raw type | Family | Cells | Home edges / contacts | Away edges / contacts | Away gamma-eligible edges |
| --- | --- | ---: | ---: | ---: | ---: |
| `KC` | other | 2 | 0 / 0 | 0 / 0 | 0 |
| `KCa'b'-ap1` | apbp | 199 | 111 / 163 | 440 / 5,667 | 0 |
| `KCa'b'-ap2` | apbp | 291 | 107 / 175 | 583 / 7,548 | 0 |
| `KCa'b'-m` | apbp | 205 | 98 / 152 | 415 / 6,102 | 0 |
| `KCab-c` | ab | 488 | 529 / 2,591 | 0 / 0 | 0 |
| `KCab-m` | ab | 536 | 702 / 4,142 | 3 / 3 | 0 |
| `KCab-p` | ab | 129 | 128 / 558 | 0 / 0 | 0 |
| `KCab-s` | ab | 657 | 924 / 5,859 | 2 / 2 | 0 |
| `KCg` | gamma | 1 | 1 / 24 | 2 / 47 | 2 |
| `KCg-d` | gamma | 206 | 206 / 3,273 | 419 / 6,038 | 419 |
| `KCg-m` | gamma | 1,342 | 1,368 / 24,213 | 2,800 / 37,578 | 2,800 |
| `KCg-s1` | gamma | 2 | 3 / 138 | 4 / 293 | 4 |
| `KCg-s2` | gamma | 2 | 2 / 92 | 5 / 153 | 5 |
| `KCg-s3` | gamma | 2 | 2 / 49 | 4 / 84 | 4 |
| `KCg-s4` | gamma | 2 | 3 / 31 | 5 / 64 | 5 |

Home stays unfiltered. Broad labels remain broad; `KCg` is gamma by the declared prefix policy, whereas `KC` is unresolved. [Interpretation](kenyon-cells.md).

## Every selected or historical target cell

These are raw instance labels, including the source spellings `y`, `a`, `B` and apostrophes. Do not infer anatomical location from the soma side alone. PAM11/MBON07 are historical targets, not current teaching/readout selections.

| Type | Body ID | Raw instance | Transmitter | Soma side | Root side |
| --- | ---: | --- | --- | --- | --- |
| PPL101 | 11327 | `PPL101(y1ped)_R` | dopamine | R | unlabeled |
| PPL101 | 11900 | `PPL101(y1ped)_L` | dopamine | L | unlabeled |
| PAM12 | 61360 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 91391 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 91875 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 96571 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 104460 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 105447 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 111665 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 113001 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 126900 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 135171 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 138585 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 139280 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 139378 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 144625 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 146418 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 152428 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 157257 | `PAM12(y3)_L` | dopamine | L | unlabeled |
| PAM12 | 158917 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 196622 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 206851 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 520384 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM12 | 552362 | `PAM12(y3)_R` | dopamine | R | unlabeled |
| PAM11 | 114661 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 119763 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 137539 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 138822 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 139706 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 145749 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 147857 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 157016 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 204930 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 215931 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 224500 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 238644 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 273182 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| PAM11 | 319321 | `PAM11(a1)_R` | dopamine | R | unlabeled |
| PAM11 | 520616 | `PAM11(a1)_L` | dopamine | L | unlabeled |
| MBON11 | 10704 | `MBON11(y1pedc>a/B)_L` | gaba | L | unlabeled |
| MBON11 | 11402 | `MBON11(y1pedc>a/B)_R` | gaba | R | unlabeled |
| MBON09 | 18713 | `MBON09(y3B'1)_L` | gaba | L | unlabeled |
| MBON09 | 19267 | `MBON09(y3B'1)_L` | gaba | L | unlabeled |
| MBON09 | 21242 | `MBON09(y3B'1)_R` | gaba | R | unlabeled |
| MBON09 | 523060 | `MBON09(y3B'1)_R` | gaba | R | unlabeled |
| MBON07 | 12859 | `MBON07(a1)_R` | glutamate | R | unlabeled |
| MBON07 | 15626 | `MBON07(a1)_L` | glutamate | L | unlabeled |
| MBON07 | 18603 | `MBON07(a1)_L` | glutamate | L | unlabeled |
| MBON07 | 515338 | `MBON07(a1)_R` | glutamate | R | unlabeled |
| APL | 10540 | `APL_R` | gaba | R | unlabeled |
| APL | 10977 | `APL_L` | gaba | L | unlabeled |

The full [cell CSV](data/neurons.csv) also includes every KC, ALPN, MBON and the union of DAN-class and pure-dopamine cells. The [edge CSV](data/reward-edges.csv) lists every selected pre/post body-ID pair and its contact count.

[Cell atlas](index.md) · [MBON territory interpretation](mbons.md)
