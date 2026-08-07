class WorkflowValidator:

    @staticmethod
    def validate(workflow):

        if not isinstance(workflow, dict):

            raise Exception(

                "Workflow must be a dictionary."

            )

        return True