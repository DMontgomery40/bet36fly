"""Aso et al.2019, eLife49257, Methods equations1–3, reimplemented here.

Latent d/n and delayed expressed D/N are phenomenological memory variables,
not biochemical concentrations. Seconds and experimental activity *levels*
are explicit; this module has no somatic-spike mapping or circuit integration.
Source: https://doi.org/10.7554/eLife.49257 (corrected2020 transcript analysis).
"""

from dataclasses import dataclass
import math
from numbers import Real


def _number(value, name, *, lower=0.0, upper=math.inf, positive=False):
    try:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ValueError
        result = float(value)
        if not math.isfinite(result) or result < lower or result > upper or (positive and result == 0):
            raise ValueError
        return result
    except (ValueError, OverflowError, TypeError):
        raise ValueError(f"{name} is outside its finite numeric domain.") from None


@dataclass(frozen=True)
class SourceState:
    d: float = 0.0
    n: float = 0.0
    D: float = 0.0
    N: float = 0.0

    def __post_init__(self):
        for name in ("d", "n", "D", "N"):
            object.__setattr__(self, name, _number(getattr(self, name), name, upper=1.0))


@dataclass(frozen=True)
class Parameters:
    A_D: float = 4.3 / 60
    A_N: float = 0.96 / 60
    B_D: float = 0.26 / 60
    B_N: float = 0.16 / 60
    tau_D: float = 30.0
    tau_N: float = 600.0

    def __post_init__(self):
        for name in ("A_D", "A_N", "B_D", "B_N", "tau_D", "tau_N"):
            object.__setattr__(
                self, name, _number(getattr(self, name), name, positive=name.startswith("tau"))
            )


def _control(state, da_enabled, no_enabled):
    if not isinstance(state, SourceState):
        raise ValueError("state must be a SourceState.")
    if type(da_enabled) is not bool or type(no_enabled) is not bool:
        raise ValueError("Branch controls require actual bool values.")
    if not da_enabled and (state.d != 0 or state.D != 0):
        raise ValueError("DA-null requires an unpopulated branch from the start.")
    if not no_enabled and (state.n != 0 or state.N != 0):
        raise ValueError("NO-null requires an unpopulated branch from the start.")


def _response_weights(lt, mt):
    """Positive convolution coefficients for x'=lambda(a-x), X'=(x-X)/tau.

    X(t)=X0*v+x0*j+a*k. k is the two-stage step response. Its tiny-time
    O(t²) term is evaluated directly, never by subtracting O(t) quantities.
    Infinite scaled rates here arise only from finite-input float overflow;
    they denote exponentially settled limits, not accepted infinite inputs.
    """
    if math.isinf(lt):
        return (0.0, 0.0, 1.0) if math.isinf(mt) else (math.exp(-mt), 0.0, -math.expm1(-mt))
    if math.isinf(mt):
        return 0.0, math.exp(-lt), -math.expm1(-lt)
    lo, hi = min(lt, mt), max(lt, mt)
    gap = hi - lo
    v = math.exp(-mt)
    j = mt * math.exp(-mt) if gap == 0 else (mt / gap) * math.exp(-lo) * -math.expm1(-gap)
    if hi <= 0.5:
        # Integral of the two exponential impulse responses, expanded in
        # nonnegative lt=lambda*t and mt=t/tau; symmetric homogeneous powers.
        terms, power_sum, factorial, lo_power = [], 1.0, 2.0, 1.0
        for order in range(24):
            if order:
                lo_power *= lo
                power_sum = hi * power_sum + lo_power
                factorial *= order + 2
            terms.append((-1.0 if order % 2 else 1.0) * power_sum / factorial)
        k = (lt * mt) * math.fsum(terms)
    else:
        # Symmetric form uses the smaller scaled rate. It stays accurate
        # when one rate is tiny while the other is already well relaxed.
        common = lo * math.exp(-lo) if gap == 0 else (lo / gap) * math.exp(-lo) * -math.expm1(-gap)
        k = -math.expm1(-lo) - common
    return v, j, k


def _branch(x, X, seconds, rate, tau, target):
    if seconds == 0:
        return x, X
    lt, mt = rate * seconds, seconds / tau
    if rate == 0 or lt == 0:
        return x, math.fsum((X * math.exp(-mt), x * -math.expm1(-mt)))
    if mt == 0:
        return (x + (1 - x) * -math.expm1(-lt) if target else x * math.exp(-lt)), X
    x1 = x + (1 - x) * -math.expm1(-lt) if target else x * math.exp(-lt)
    if x == X == target:
        return x1, X
    v, j, k = _response_weights(lt, mt)
    X1 = math.fsum((X * v, x * j, target * k))
    if X1 > 0.5:
        # Evaluate the complementary convex combination near the upper
        # boundary. This preserves tiny distances to one without summing
        # rounded coefficients to 1+ULP. Near zero retain the direct O(t²)
        # response above. This is algebraic evaluation, not state clipping.
        X1 = 1 - math.fsum(((1 - X) * v, (1 - x) * j, (1 - target) * k))
    return x1, X1


def advance(state, seconds, *, kc_active, dan_active, da_enabled=True, no_enabled=True, params=Parameters()):
    """Return a new state after one constant-input interval; never reset or clip."""
    _control(state, da_enabled, no_enabled)
    if type(kc_active) is not bool or type(dan_active) is not bool:
        raise ValueError("Activity levels require actual bool values, not spikes or labels.")
    if not isinstance(params, Parameters):
        raise ValueError("params must be Parameters.")
    seconds = _number(seconds, "seconds")
    target = 1.0 if kc_active and dan_active else 0.0
    ad = params.A_D if kc_active else params.B_D
    an = params.A_N if kc_active else params.B_N
    d, D = _branch(state.d, state.D, seconds, ad if dan_active and da_enabled else 0.0, params.tau_D, target)
    n, N = _branch(state.n, state.N, seconds, an if dan_active and no_enabled else 0.0, params.tau_N, target)
    return SourceState(d, n, D, N)


def quiet_limit(state, *, da_enabled=True, no_enabled=True):
    """Complete no-input limit: latent memory survives; expressed state catches up."""
    _control(state, da_enabled, no_enabled)
    return SourceState(state.d, state.n, state.d, state.n)


def weight(state):
    """Source multiplicative relative synaptic efficacy, in [0,2]."""
    if not isinstance(state, SourceState):
        raise ValueError("state must be a SourceState.")
    return (1 - state.D) * (1 + state.N)
