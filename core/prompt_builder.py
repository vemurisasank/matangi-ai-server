class PromptBuilder:

    @staticmethod
    def build_scene_prompt(

        script,

        style,

        language,

        scene_count

    ):

        return f"""
        You are an expert cinematic storyboard artist.

        Convert the script into EXACTLY {scene_count} scenes.

        IMPORTANT RULES

        1. Return ONLY JSON.

        2. Do NOT explain anything.

        3. Do NOT use markdown.

        4. Do NOT use ```json.

        5. Return valid JSON.

        6. Use this schema exactly.

        {{
            "scenes":[
                {{
                    "scene":1,
                    "title":"",
                    "environment":"",
                    "character":"",
                    "camera":"",
                    "lighting":"",
                    "mood":"",
                    "image_prompt":""
                }}
            ]
        }}

        Language:

        {language}

        Style:

        {style}

        Script:

        {script}
        """