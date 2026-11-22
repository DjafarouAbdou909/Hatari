"""Share of training messages that trigger each signal, for section 7.6 of docs/07_risk_methodology.md.

Only the training part of the corpus is read.

Usage, from the repository root, after python -m hatari.data.corpus:

    python -m hatari.analysis.signal_check
"""

from __future__ import annotations

import pandas as pd

from hatari.analysis.eda import load_training
from hatari.analysis.signals import DEFINITIONS, detect

REVISION_THRESHOLD = 0.05


def trigger_rates(frame: pd.DataFrame) -> pd.DataFrame:
    found = [{signal.id for signal in detect(text)} for text in frame["text"]]
    hits = pd.DataFrame({definition.id: [definition.id in ids for ids in found] for definition in DEFINITIONS})
    rates = hits.groupby([frame["language"].to_numpy(), frame["suspicious"].to_numpy()]).mean().T
    rates.columns = [f"{language}_{'suspicious' if suspicious else 'legitimate'}" for language, suspicious in rates.columns]
    return rates


def main() -> None:
    rates = trigger_rates(load_training())
    print(rates.round(3).to_string())
    flagged = rates.index[rates["en_legitimate"] > REVISION_THRESHOLD].tolist()
    print("signals above the revision threshold on legitimate English messages:", flagged or "none")


if __name__ == "__main__":
    main()
