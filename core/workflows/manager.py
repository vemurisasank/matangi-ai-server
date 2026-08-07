from core.workflows.loader import WorkflowLoader

from core.workflows.variables import WorkflowVariables

from core.workflows.registry import WorkflowRegistry

from core.workflows.validator import WorkflowValidator

class WorkflowManager:

    @staticmethod
    def build(

        workflow_name,

        variables

    ):

        workflow_file = WorkflowRegistry.get(

            workflow_name

        )

        if workflow_file is None:

            raise Exception(

                f"Workflow '{workflow_name}' not found."

            )

        workflow = WorkflowLoader.load(

            workflow_file

        )

        workflow = WorkflowVariables.replace(

            workflow,

            variables

        )

        WorkflowValidator.validate(

            workflow

        )

        return workflow