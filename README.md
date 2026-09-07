# SignalForge

An intelligence engine that finds and understands opportunities before presenting them to a person.

This repository is licensed under the [Apache License 2.0](LICENSE).

Public repository: [github.com/1realbzy/SignalForge](https://github.com/1realbzy/SignalForge)

## Current status

SignalForge currently includes:

- a generic X/Twitter ingestion source
- a deterministic opportunity-detection baseline
- temporary `twikit==2.2.2` compatibility patches ([docs/dependencies/twikit-2.2.2-compat.md](docs/dependencies/twikit-2.2.2-compat.md))

Extraction, matching, and ranking are not implemented yet.

The installed Python package import path remains `job_board_tool` so existing modules and tests stay stable. The project and distribution name is SignalForge.

See [docs/architecture/source-adapters.md](docs/architecture/source-adapters.md) for ingestion, [docs/opportunity-detection.md](docs/opportunity-detection.md) for detection, and [evals/detection/README.md](evals/detection/README.md) for the local evidence-validation protocol.
