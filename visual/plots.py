import matplotlib.pyplot as plt
import pandas as pd
import os
import pathlib
import matplotlib.colors as mcolors
import numpy as np



def _save_figure(fig, output_data_path, name):
    save_dir = pathlib.Path(os.path.join(output_data_path, "charts"))
    save_dir.mkdir(exist_ok=True)  # auto-create once

    fig.savefig(save_dir / name, dpi=300, bbox_inches="tight")


def _order_units(output_data_path):
    """
    Returns a list of unit names ordered by preferred technology type.
    """
    unit_data_path = os.path.join(output_data_path, "unit_data.csv")
    if not os.path.exists(unit_data_path):
        raise FileNotFoundError(f"Unit data CSV not found: {unit_data_path}")

    unit_data = pd.read_csv(unit_data_path, index_col="Unit")

    preferred_order = ["Storage", "Coal", "CCGT", "OCGT", "Solar", "Wind"]

    ordered_units = []
    for tech in preferred_order:
        units_of_tech = unit_data.index[unit_data["Technology"] == tech].tolist()
        ordered_units.extend(units_of_tech)

    return ordered_units, unit_data


def _unit_colors(unit_data, ordered_units):
    """
    Returns a dictionary mapping unit names to colors.
    Multiple units of the same Technology get slightly different shades.
    """
    # Base colors per technology
    base_colors = {
        "Storage": "#9e4ad3",  # purple
        "Coal": "#8c564b",     # brown
        "OCGT": "#c99e54",     # orange
        "CCGT": "#ea5b34",     # red-orange
        "Solar": "#ffd700",    # yellow
        "Wind": "#1f77b4"      # blue
    }

    colors = {}
    # Group units by Technology
    tech_groups = unit_data.loc[ordered_units].groupby("Technology")

    for tech, units in tech_groups:
        n = len(units)
        base_color = base_colors.get(tech, "#333333")  # fallback

        # Generate shades if multiple units
        if n == 1:
            colors[units.index[0]] = base_color
        else:
            # Convert base color to RGB
            rgb = mcolors.to_rgb(base_color)
            # Create n shades by lightening/darkening
            for i, u in enumerate(units.index):
                factor = 0.8 + 0.4 * i / (n - 1)  # 0.8 -> 1.2
                shade = tuple(min(1, c * factor) for c in rgb)
                colors[u] = mcolors.to_hex(shade)

    return colors


def plot_dispatch(output_data_path, name="", plot_price=True, scenario=0):
    # --- Paths ---
    power_generated_path = os.path.join(output_data_path, "results", "power_generated_MW.csv")
    power_charged_path = os.path.join(output_data_path, "results", "power_charged_MW.csv")
    settings_path = os.path.join(output_data_path, "settings.csv")
    energy_price_path = os.path.join(output_data_path, "results", "energy_price_$pMWh.csv")

    # --- Unit order and colors ---
    order, unit_data = _order_units(output_data_path)
    colors = _unit_colors(unit_data, order)

    # --- Load CSVs ---
    power_generated = pd.read_csv(power_generated_path, index_col=[0, 1]).xs(scenario, level="scenarios")
    power_charged = pd.read_csv(power_charged_path, index_col=[0, 1]).xs(scenario, level="scenarios")

    # --- Load settings ---
    settings = pd.read_csv(settings_path, index_col=0)
    interval_duration = float(settings.loc["IntervalDurationHrs", "Value"])
    starting_hour = float(settings.loc["StartingHour", "Value"]) if "StartingHour" in settings.index else 0

    # --- Align and reorder ---
    power_generated, power_charged = power_generated.align(power_charged, fill_value=0)
    ordered_units = [u for u in order if u in power_generated.columns]
    power_generated = power_generated[ordered_units]
    power_charged = power_charged[ordered_units]

    # --- Net dispatch ---
    net = power_generated - power_charged
    df_pos, df_neg = net.clip(lower=0), net.clip(upper=0)

    fig, ax = plt.subplots(figsize=(12, 6))

    # --- Positive stacked area ---
    df_pos.plot.area(ax=ax, stacked=True, linewidth=0., color=[colors[u] for u in df_pos.columns])

    # --- Reset color cycle for negative plot ---
    ax.set_prop_cycle(None)

    # --- Negative stacked area (battery charging) ---
    ax.set_ylim(-1, 1)
    df_neg_renamed = df_neg.rename(columns=lambda x: '_' + x)  # hide legend duplicates
    df_neg_renamed.plot.area(ax=ax, stacked=True, linewidth=0., color=[colors[u] for u in df_neg.columns])

    # --- Y-axis padding ---
    y_min = np.floor(df_neg.sum(axis=1).min() / 500) * 500
    y_max = np.ceil(df_pos.sum(axis=1).max() / 1000) * 1000
    y_padding = 0.05 * max(1, y_max - y_min)
    ax.set_ylim([y_min - y_padding, y_max + y_padding])

    if len(power_generated) == 48:
        tick_indices = [0, 8, 16, 24, 32, 40]
    elif len(power_generated) == 24:
        tick_indices = [0, 4, 8, 12, 16, 20]
    else:
        n_ticks = 6  # number of ticks you want
        n_intervals = len(power_generated)
        tick_indices = np.linspace(0, n_intervals - 1, n_ticks, dtype=int)

    # get the corresponding time in hours
    tick_times = [starting_hour + i * interval_duration for i in tick_indices]

    # format as HH:MM
    tick_labels = [f"{int(t)%24:02d}:{int((t%1)*60):02d}" for t in tick_times]

    ax.set_xticks(tick_indices)
    ax.set_xticklabels(tick_labels, rotation=45)
    ax.set_xlim([0, len(power_generated)-1])

    # --- Secondary axis for energy price ---
    if plot_price and os.path.exists(energy_price_path):
        energy_price = pd.read_csv(energy_price_path, index_col=0)[str(scenario)]
        energy_price = energy_price.reindex(power_generated.index, method='nearest')
        ax2 = ax.twinx()
        ax2.plot(range(len(energy_price)), energy_price, color="black", linestyle="--", label="Energy Price ($/MWh)")
        ax2.set_ylabel("Energy Price ($/MWh)")
        ax2.legend(loc="upper right")

        max_price = energy_price.max()
        # Round up to next "nice" number (e.g., nearest 10 or 50)
        nice_max = int(np.ceil(max_price / 100 + 1.5) * 100)
        ax2.set_ylim([0, nice_max])

    # --- Final touches ---
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Power (MW)")
    ax.set_xlabel("Time of Day")
    ax.set_title(f"{name}: Dispatch")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper left")

    _save_figure(fig, output_data_path, name=f"dispatch_scenario_{scenario}.png")

    print(f"Plotted dispatch figure for scenario {scenario}.")

    return fig
