// Browser port of choke_model/model.py. No page code in here, so it can be
// tested from Node against the Python model (tests/test_simulator.py).
//
// The equation is the same one, divided through by the baseline oxygen C0:
//
//   dc/dt = a * [ q(t) * (1 / (1 - E) - c)  -  E / (1 - E) * m(c) ]
//
// c = C / C0, a = CBF / CBV (per second), E = OEF, q(t) = fraction of normal
// blood flow, m(c) = (1 + kappa) * c / (kappa + c).
const ChokeModel = (() => {
  "use strict";

  // Fraction of normal brain blood flow at time t (seconds).
  function flowFraction(t, s) {
    if (t < s.tOn || t >= s.tOff) return 1;
    const v = s.vertebralShare;
    const held = (1 - v) * (1 - s.carotidCut) + v * s.vertebralOpen;
    const sinceOn = t - s.tOn;
    return sinceOn < s.ramp ? 1 + (held - 1) * (sinceOn / s.ramp) : held;
  }

  function rate(c, q, p) {
    const cc = Math.max(c, 0);
    const use = ((1 + p.kappa) * cc) / (p.kappa + cc);
    const a = p.cbf / 60 / p.cbv;
    return a * (q * (1 / (1 - p.oef) - c) - (p.oef / (1 - p.oef)) * use);
  }

  // Fourth-order Runge-Kutta with a fixed step. tOn, tOff and ramp must be
  // whole multiples of dt so that no step straddles a jump in flow.
  function simulate(p, s, tEnd, dt = 0.01) {
    const n = Math.round(tEnd / dt);
    const t = new Float64Array(n + 1);
    const c = new Float64Array(n + 1);
    const q = new Float64Array(n + 1);
    c[0] = 1;
    q[0] = flowFraction(0, s);
    const eps = dt * 1e-6;
    for (let i = 0; i < n; i++) {
      const t0 = i * dt;
      const q1 = flowFraction(t0 + eps, s);
      const q2 = flowFraction(t0 + dt / 2, s);
      const q4 = flowFraction(t0 + dt - eps, s);
      const k1 = rate(c[i], q1, p);
      const k2 = rate(c[i] + (dt / 2) * k1, q2, p);
      const k3 = rate(c[i] + (dt / 2) * k2, q2, p);
      const k4 = rate(c[i] + dt * k3, q4, p);
      c[i + 1] = c[i] + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4);
      t[i + 1] = (i + 1) * dt;
      q[i + 1] = flowFraction(t[i + 1], s);
    }
    return { t, c, q };
  }

  // First time c falls below the threshold, and the first time it rises back.
  function crossings(run, threshold) {
    const { t, c } = run;
    let loc = null;
    let recovery = null;
    for (let i = 1; i < c.length; i++) {
      const before = c[i - 1] - threshold;
      const after = c[i] - threshold;
      if (loc === null && before >= 0 && after < 0) {
        loc = t[i - 1] + ((t[i] - t[i - 1]) * before) / (before - after);
      } else if (loc !== null && before < 0 && after >= 0) {
        recovery = t[i - 1] + ((t[i] - t[i - 1]) * before) / (before - after);
        break;
      }
    }
    return { loc, recovery };
  }

  return { flowFraction, rate, simulate, crossings };
})();

if (typeof module !== "undefined") module.exports = ChokeModel;
