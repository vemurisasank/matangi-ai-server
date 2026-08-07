import json
import os

from core.workflows.cache import WorkflowCache


class WorkflowLoader:

    @staticmethod
    def load(workflow_name):

        # Check cache first
        cached = WorkflowCache.get(workflow_name)

        if cached:

            return cached

        # Load workflow from disk
        path = os.path.join(

            "workflows",

            f"{workflow_name}.json"

        )

        with open(

            path,

            "r",

            encoding="utf-8"

        ) as file:

            workflow = json.load(file)

        # Store in cache
        WorkflowCache.set(

            workflow_name,

            workflow

        )

        return workflow