import os

from easul import util
from easul.algorithm import StoredAlgorithm
from easul.visual import DatasetMetadata, FileMetadata
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
            filename = visual.metadata_filename
            if not filename or not visual.metadata_dataset:
                continue

            computed = DatasetMetadata(util.string_to_function(visual.metadata_dataset))
            computed.init(visual)
            visual.metadata = FileMetadata(filename=filename, data=computed.data)

            self._make_path(filename)
            LOG.info(f"Save metadata to '{filename}")
            visual.metadata.save()

        os.chdir(cwd)