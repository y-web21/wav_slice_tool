from io import TextIOWrapper
import pathlib
import sys
from typing import Generic, TypeVar


def main():
    """
    if run as script, this func is executed.
    """
    obs = textTool(sys.argv[0])
    obs.read()


T = TypeVar('T')


class textTool(Generic[T]):
    """
    convert text to json
    """

    def __init__(self, path: str = '') -> None:
        super().__init__()
        self.__textPath = path

    def toJSON(self):
        """
        nothing
        """
        pass

    def read(self, path: str = '') -> T:
        """
        docstring
        """
        if path == '':
            path = self.__textPath
        try:
            text = open(path)
        except Exception as e:
            print(repr(e))

        if not isinstance(text, TextIOWrapper):
            raise FileTypeError(f'reading illegal file')

        return self


class FileTypeError(Exception):
    pass


if __name__ == "__main__":
    main()
