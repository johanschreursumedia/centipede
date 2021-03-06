import os
from .TaskWrapper import TaskWrapper
from .DCC import DCC

class Gaffer(DCC):
    """
    Performs a task inside gaffer.
    """

    def _command(self):
        """
        For re-implementation: should return a string which is executed as subprocess.
        """
        scriptLoaderPath = os.path.join(
            os.path.dirname(
                os.path.realpath(__file__)
            ),
            'aux',
            'gafferRunSerializedTask.py'
        )

        return 'gaffer env python "{}"'.format(
            scriptLoaderPath
        )

    @classmethod
    def _hookName(cls):
        """
        For re-implementation: should return a string containing the name used for the hook registered in basetools.
        """
        return "gaffer"


# registering task wrapper
TaskWrapper.register(
    'gaffer',
    Gaffer
)
