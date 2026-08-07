import json


class WorkflowVariables:

    @staticmethod
    def replace(

        workflow,

        variables

    ):

        text = json.dumps(

            workflow

        )

        for key, value in variables.items():

            text = text.replace(

                "{{" + key + "}}",

                str(value)

            )

        return json.loads(

            text

        )