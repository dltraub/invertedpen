import json

import numpy as np
import pytest

from invertedpen.simulation_logging import SimulationLogger, load_run


def test_logger_writes_npz_and_metadata(tmp_path) -> None:
    logger = SimulationLogger(
        tmp_path,
        tag="test",
        metadata={"seed": 4},
        signal_metadata={"state": {"unit": "SI"}},
    )
    logger.log(0, time=0.0, state=np.zeros(2))
    logger.log(1, time=0.1, state=np.ones(2))

    run_path = logger.finalize()
    metadata, arrays = load_run(run_path)

    assert metadata["status"] == "complete"
    assert metadata["configuration"]["seed"] == 4
    assert metadata["signals"]["state"]["unit"] == "SI"
    np.testing.assert_allclose(arrays["state"], [[0, 0], [1, 1]])


def test_logger_rejects_inconsistent_samples(tmp_path) -> None:
    logger = SimulationLogger(tmp_path)
    logger.log(0, state=np.zeros(2))

    with pytest.raises(ValueError, match="changed shape"):
        logger.log(1, state=np.zeros(3))


def test_logger_context_preserves_incomplete_run(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="broken"):
        with SimulationLogger(tmp_path) as logger:
            logger.log(0, state=np.zeros(1))
            raise RuntimeError("broken")

    paths = list(tmp_path.iterdir())
    assert len(paths) == 1
    metadata = json.loads((paths[0] / "metadata.json").read_text())
    assert metadata["status"] == "incomplete"
    assert metadata["error"]["message"] == "broken"
