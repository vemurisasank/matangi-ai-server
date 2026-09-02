from core.workflows.registry import WorkflowRegistry
from core.workflows.loader import WorkflowLoader
from providers.comfyui.workflow_loader import WorkflowLoader as ComfyWorkflowLoader
from core.workflows.variables import WorkflowVariables
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

        if workflow_file == "z_image_text_to_image_api.json":

            workflow = ComfyWorkflowLoader.load(
                variables["prompt"],
                variables["width"],
                variables["height"],
                variables["seed"],
                variables.get("reference_images", [])
            )

        else:

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
