"""Build a nested tree structure from flat file paths for the file tree UI."""


def build_file_tree(paths: list[str]) -> list[dict]:
    """Convert a sorted list of relative file paths into a nested folder/file tree."""
    root: dict = {}
    for path in paths:
        parts = path.split("/")
        node = root
        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]

    def to_list(node: dict, name: str = "") -> list[dict]:
        """Recursively convert the nested dict into a list of typed tree nodes."""
        items = []
        for key, children in sorted(node.items()):
            if children:
                items.append({
                    "name": key,
                    "type": "folder",
                    "children": to_list(children, key),
                })
            else:
                items.append({"name": key, "type": "file"})
        return items

    return to_list(root)
