import os

from easul import util
from easul.algorithm import StoredAlgorithm
import logging
LOG = logging.getLogger(__name__)


class PlanRepository:
    """
    Utility class which simplies the storage of algorithms and metadata.
    """
    def __init__(self, plan):
        self.plan = plan

    def _make_path(self, filename):
        filepath = os.path.dirname(os.path.abspath(filename))
        os.makedirs(filepath, exist_ok=True)

    def store_algorithms(self):
        for algo_name, algorithm in self.plan.algorithms.items():
            if not isinstance(algorithm, StoredAlgorithm):
                 continue

            algorithm.update_from_definition()
            filename = algorithm.filename
            self._make_path(filename)
            LOG.info(f"Save algorithm to '{filename}")
            algorithm.save_to_file(filename)


    def store_metadata(self):
        cwd = os.getcwd()

        for visual_name, visual in self.plan.visuals.items():
            dset = util.string_to_function(visual.metadata_dataset)
            visual.metadata.clear()
            visual.metadata.calculate(dset)
            filename = visual.metadata_filename
            self._make_path(filename)

            LOG.info(f"Save metadata to '{visual.metadata.filename}")

            visual.metadata.save()

        os.chdir(cwd)