"""Draw the model as one diagram: figures/model_diagram.png.

Every number printed on the diagram is read from the model's parameters or
computed by the model, so the picture cannot drift from the code.

    python -m scripts.make_diagram
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from choke_model.analysis import central_threshold
from choke_model.params import Params

ROOT = Path(__file__).resolve().parents[1]
BLOOD, VEIN, INK, MUTED = "#c0392b", "#34618f", "#1c2530", "#5d6b78"


def arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float], color: str, width: float) -> None:
    """One flow arrow."""
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=18, lw=width, color=color,
                                 shrinkA=0, shrinkB=0))


def main() -> None:
    p = Params()
    theta = central_threshold(p)
    vertebral = p.vertebral_share
    fig, ax = plt.subplots(figsize=(9.4, 4.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # The one compartment.
    ax.add_patch(FancyBboxPatch((3.9, 1.7), 2.6, 2.1, boxstyle="round,pad=0.05,rounding_size=0.15",
                                fc="#f6ebe8", ec=INK, lw=1.4))
    ax.text(5.2, 3.2, "oxygen in the blood\ninside the brain", ha="center", va="center", fontsize=11, color=INK)
    ax.text(5.2, 2.45, "C(t)", ha="center", va="center", fontsize=15, color=INK, style="italic")
    ax.text(5.2, 1.98, f"unconscious when C / C0 < {theta:.2f} (fitted)", ha="center", va="center",
            fontsize=8.5, color=MUTED)

    # Arterial supply: carotid and vertebral. Line width follows each one's share of flow.
    arrow(ax, (0.9, 3.35), (3.85, 3.0), BLOOD, 5.0 * (1 - vertebral) + 1)
    arrow(ax, (0.9, 2.0), (3.85, 2.45), BLOOD, 5.0 * vertebral + 1)
    ax.text(0.85, 3.72, f"carotid arteries, {100 * (1 - vertebral):.0f}% of flow", fontsize=10, color=BLOOD)
    ax.text(0.85, 1.52, f"vertebral arteries, {100 * vertebral:.0f}% of flow", fontsize=10, color=BLOOD)
    ax.text(0.85, 1.2, "left open by a blood choke (assumed)", fontsize=8.5, color=MUTED)
    # The choke: a bar across the carotid supply.
    ax.plot([2.25, 2.55], [3.62, 2.72], color=INK, lw=3.2, solid_capstyle="round")
    ax.text(2.4, 4.05, "a blood choke\ncuts this flow", ha="center", fontsize=9, color=INK)
    ax.text(2.55, 2.42, "in:  F(t) · Ca", fontsize=10, color=INK, style="italic")

    # Venous outflow and consumption.
    arrow(ax, (6.55, 2.75), (9.1, 2.75), VEIN, 4.0)
    ax.text(7.8, 3.0, "out in venous blood", ha="center", fontsize=10, color=VEIN)
    ax.text(7.8, 2.4, "F(t) · C / V", ha="center", fontsize=10, color=INK, style="italic")
    arrow(ax, (5.2, 1.65), (5.2, 0.55), INK, 3.0)
    ax.text(5.4, 1.05, "used by brain tissue", fontsize=10, color=INK)
    ax.text(5.4, 0.72, "M(C)", fontsize=10, color=INK, style="italic")

    ax.text(5.0, 4.75, "One box: oxygen arrives in arterial blood, leaves in venous blood, and is used up",
            ha="center", fontsize=11, color=INK)
    fig.tight_layout()
    out = ROOT / "figures" / "model_diagram.png"
    fig.savefig(out, dpi=150, facecolor="white")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
