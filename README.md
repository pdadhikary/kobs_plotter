# Kobs-Plotter

A general purpose curve fitting tool for tabular data. Load your Excel file,
select a model, and get fitted parameters with goodness-of-fit statistics — no
coding required.

![System Architecture for Kobs-Plotter](./assets/diagrams/architecture_diagram.png)

---

## Installation

Kobs-Plotter is distributed as a command-line tool via **uv**. If you don't
have uv installed, follow the
[official installation guide](https://docs.astral.sh/uv/getting-started/installation/)
first — it takes under a minute.

### Recommended — install from GitHub

Open your terminal (PowerShell on Windows) and run:

```bash
uv tool install https://github.com/pdadhikary/kobs_plotter
```

That's it. uv handles all dependencies automatically.

### Manual — install from source

Use this only if you want to modify the source code.

1. Download the latest release from the [Releases](https://github.com/pdadhikary/kobs_plotter/releases) page and extract the zip, or clone the repository:

```bash
   git clone https://github.com/pdadhikary/kobs_plotter.git
   cd kobs_plotter
```

1. Install the tool:

```bash
   uv tool install .
```

---

## Running the app

Once installed, launch the app from any terminal:

```bash
kobs-plotter
```

---

## Usage

> Usage guide coming soon.

---

## Built with

| Library | Purpose |
|---|---|
| [PySide6](https://wiki.qt.io/Qt_for_Python) | GUI framework |
| [NumPy](https://numpy.org/) | Numerical operations and data transforms |
| [Pandas](https://pandas.pydata.org/) | Excel file loading |
| [SciPy](https://scipy.org/) | Curve fitting and statistics |
| [Matplotlib](https://matplotlib.org/) | Plot rendering |

---

## Citation

If you use Kobs-Plotter in your research, please cite it as:

> Adhikary, P. D. (2026). Kobs-Plotter (Version 0.2.0) [Software].
> GitHub. <https://github.com/pdadhikary/kobs_plotter>

```bibtex
@software{adhikary2025kobsplotter,
    author       = {Adhikary, Prachurya Deepta},
    title        = {Kobs-Plotter: A desktop application for nonlinear curve fitting of tabular data},
    year         = {2026},
    publisher    = {GitHub},
    version      = {0.2.0},
    url          = {https://github.com/pdadhikary/kobs_plotter}
}
```

> **Note:** Please replace `year` with the year of the version you used,
> and add a `version` field with the specific release version from the
> [Releases](https://github.com/pdadhikary/kobs_plotter/releases) page.

### Citing dependencies

The following libraries underpin the core computation — many journals require
these to be cited alongside the software that uses them:

- **NumPy** — Harris, C.R., Millman, K.J., van der Walt, S.J. et al. Array programming with NumPy. Nature 585, 357–362 (2020). <https://doi.org/10.1038/s41586-020-2649-2>
- **SciPy** — Virtanen, P. et al. (2020). SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python. *Nature Methods*, 17(3), 261–272. <https://doi.org/10.1038/s41592-019-0686-2>
- **Matplotlib** — J. D. Hunter, "Matplotlib: A 2D Graphics Environment", *Computing in Science & Engineering*, vol. 9, no. 3, pp. 90-95, 2007. <https://doi.org/10.5281/zenodo.20654446>
- **Pandas** — The pandas development team. Pandas-dev/pandas: Pandas. v3.0.3, Zenodo, 11 May 2026, <https://doi.org/10.5281/zenodo.20127038>.
