"""
Convert dict/list values to XML using only the Python standard library.
"""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any


def _add_element(
    parent: ET.Element,
    key: str,
    value: Any,
    item_func: Callable[[str], str] | None = None,
) -> None:
    """Recursively append a value to an XML parent element."""
    element = ET.SubElement(parent, key)

    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _add_element(element, child_key, child_value, item_func)
    elif isinstance(value, list):
        item_name = item_func(key) if item_func else "item"
        for item in value:
            _add_element(element, item_name, item, item_func)
    elif isinstance(value, bool):
        element.text = str(value).lower()
    elif value is None:
        element.text = ""
    else:
        element.text = str(value)


def dict_to_xml(
    data: Any,
    root_name: str = "root",
    item_func: Callable[[str], str] | None = None,
) -> str:
    """Return an XML string for a dictionary or list."""
    root = ET.Element(root_name)

    if isinstance(data, dict):
        for key, value in data.items():
            _add_element(root, key, value, item_func)
    elif isinstance(data, list):
        item_name = item_func(root_name) if item_func else "item"
        for item in data:
            _add_element(root, item_name, item, item_func)
    else:
        root.text = str(data)

    return ET.tostring(root, encoding="unicode", xml_declaration=False)
