"""Build ordered reference-image packages for scene image generation."""


class ReferencePackageBuilder:
    """Collect reference images associated with a scene and its assets."""

    _REFERENCE_KEYS = (
        "reference_image",
        "reference_images",
        "reference",
        "image",
        "image_path",
        "filename",
        "file",
        "path",
        "file_path",
    )

    def build(self, scene, characters=None, environments=None, props=None):
        """Return the scene's character, environment, and prop references."""
        characters = characters or []
        environments = environments or []
        props = props or []

        character_references = self._references_for_scene_items(
            self._scene_value(scene, "characters", []),
            characters,
        )
        environment_references = self._references_for_scene_items(
            self._scene_value(scene, "environment", []),
            environments,
        )
        prop_references = self._references_for_scene_items(
            self._scene_value(scene, "props", []),
            props,
        )

        all_references = self._unique(
            character_references
            + environment_references
            + prop_references
        )[:3]

        return {
            "character_references": character_references,
            "environment_references": environment_references,
            "prop_references": prop_references,
            "all_references": all_references,
        }

    def _references_for_scene_items(self, scene_items, available_items):
        references = []
        for scene_item in self._as_list(scene_items):
            for item in available_items:
                if self._items_match(scene_item, item):
                    references.extend(self._extract_references(item))
        return self._unique(references)

    def _items_match(self, scene_item, available_item):
        if scene_item is available_item:
            return True

        if isinstance(scene_item, dict) and isinstance(available_item, dict):
            for key in ("id", "name", "title"):
                scene_value = scene_item.get(key)
                available_value = available_item.get(key)
                if (
                    scene_value is not None
                    and available_value is not None
                    and str(scene_value) == str(available_value)
                ):
                    return True
            return False

        return str(scene_item).strip() == str(available_item).strip()

    def _extract_references(self, item):
        if isinstance(item, dict):
            values = [
                item[key]
                for key in self._REFERENCE_KEYS
                if key in item
            ]
        else:
            values = [
                getattr(item, key)
                for key in self._REFERENCE_KEYS
                if hasattr(item, key)
            ]

        references = []
        for value in values:
            for reference in self._as_list(value):
                if isinstance(reference, dict):
                    reference = self._extract_reference_value(reference)
                if reference is not None and str(reference).strip():
                    references.append(str(reference).strip())
        return references

    def _extract_reference_value(self, reference):
        for key in self._REFERENCE_KEYS:
            if key in reference:
                return reference[key]
        return None

    def _scene_value(self, scene, key, default):
        if isinstance(scene, dict):
            return scene.get(key, default)
        return getattr(scene, key, default)

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return [value]

    def _unique(self, values):
        result = []
        seen = set()
        for value in values:
            normalized = str(value).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result
