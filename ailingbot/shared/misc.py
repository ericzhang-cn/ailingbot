import importlib
import typing

from ailingbot.shared.errors import ComponentNotFoundError


def get_class_dynamically(package_class_name: str) -> typing.Type:
    """Dynamically get class type by package path and class name.

    :param package_class_name: Package and class name like package_name.sub_package_name.ClassName
    :type package_class_name: str
    :return: Instance.
    :rtype: object
    """
    module_path, class_name = package_class_name.rsplit('.', 1)
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError):
        raise ComponentNotFoundError(
            f'Class `{module_path}.{class_name}` not found.', critical=True
        )
