import csv
from io import TextIOWrapper
import os
from pathlib import Path
import re
import sys
from typing import Generic, List, Tuple, TypeVar
from pydub import AudioSegment


def main():
    """
    if run as script, this func is executed.
    """
    obs = wavSlice(sys.argv[1])
    obs.setInputWavesDir(sys.argv[3]).open().setToMainList().open(
        sys.argv[2], isCsv=True).setToIdFileList().setBpm(110)
    obs.formatList()


T = TypeVar('T')


class wavSlice(Generic[T]):
    """
    gen a long wav file to a short wav file with the specified note and bpm.
    """

    def __init__(self, path: str = '') -> None:
        super().__init__()
        self._textPath = path
        self._bpm = 120

    def setBpm(self, bpm: int) -> T:
        self._bpm = bpm
        return self

    def setInputWavesDir(self, dir_: str) -> T:
        self._dir = dir_
        return self

    # @classmethod
    def open(self, path: str = '', isCsv: bool = False) -> T:
        """
        docstring
        """
        if path == '':
            path = self._textPath
        try:
            file = open(path)
        except Exception as e:
            print(repr(e))

        if not isinstance(file, TextIOWrapper):
            raise FileTypeError(f'reading illegal file')

        self._text = []
        if isCsv:
            self._text = [line for line in csv.reader(file)]
        else:
            self._text = [line.strip() for line in file.readlines()]

        file.close
        return self

    def setToMainList(self) -> T:
        """
        set _mainList opened list
        """
        self._mainList = self._text
        return self

    def setToIdFileList(self) -> T:
        """
        set _idFileList opened list
        id="filepath"
        """
        self._idFileList = self._text
        return self

    def exportShellscript(self, path: str, overwrite: bool = False) -> None:
        """
        docstring
        """
        raise NotImplementedError

        out = Path(path)

        if out.exists() and not overwrite:
            raise FileExistsError

        # sox input.wav output.wav trim 0.000 1.500
        with open(out, mode='w', encoding='utf-8',) as file:
            pass

    # HACK: temp
    def formatList(self):
        """
        parse original text.

        doc rules
        # = comment. inline comment is not supported.
        id,num = note. can use dot.
        e.g.
        # this is comment
        01,8 = id 01 is convert to eighth note.
        05,4. = id 05 is convert to dotted quarter note.
        """
        self._mainList = wavSlice.removeComments(self._mainList, '#')
        self._mainList = wavSlice.removeBlankLines(self._mainList)

        self._mainList = [[line.split(',')[0], line.split(',')[1:]] for line in self._mainList]
        self._mainList = [[x[0], y] for x in self._mainList for y in x[1]]

        for xx in self._mainList:
            inputFile = self.idToFilePath(xx[0])
            ms = self.noteStrToMs(xx[1], self._bpm)
            outputFile = re.sub(r'(.*)(.wav)', r'\g<1>_' + str(ms) + r'\2', inputFile)
            self.sliceByPydub(inputFile, outputFile, ms)

    def sliceByPydub(self, input: str, output: str, end: int, begin: int = 0) -> None:
        """
        TODO: this method move to pydub wrapper class
        """
        if Path(output).exists():
            os.remove(output)
        sound = AudioSegment.from_file(input, format="wav")
        if sound.duration_seconds * 1000 > end - begin:
            sound[begin:end].fade_out(20).export(output, format="wav")
        else:
            print(f'{output} is too long specified.\tsound duration: {int(sound.duration_seconds * 1000)}ms')

    def idToFilePath(self, id_: str) -> str:
        filename = [x[1] for x in self._idFileList if x[0] == id_][0]
        return str(Path(self._dir, filename))

    @staticmethod
    def parseDotted(numString: str) -> Tuple[int, float]:
        """
        input: num string, suffix dot, double-dotted, dash(1.25)
        ICEBOX: validate numString. now runtime error.
        """
        if '..' in numString:
            return int(numString.replace('..', '')), 1.75
        elif '.' in numString:
            return int(numString.replace('.', '')), 1.5
        elif '-' in numString:
            return int(numString.replace('-', '')), 1.25

        return int(numString), 1

    @staticmethod
    def noteIntToMs(note: int, multiplier: float = 1, bpm: int = 120) -> int:
        """
        CROTCHET = quarter note ms
        # note to millisecond
        CROTCHET = 60 * 1000 / 110
        """
        CROTCHET: int = 60 * 1000 / bpm
        return int(4 / note * CROTCHET * multiplier)

    @staticmethod
    def noteStrToMs(numString: str, bpm: float) -> int:
        """
        input: num string, suffix dot, double-dotted, dash(1.25)
        """
        note, multiplier = wavSlice.parseDotted(numString)
        return wavSlice.noteIntToMs(note, multiplier, bpm)

    @staticmethod
    def removeComments(trg: List[str], symbol: str):
        """
        ICEBOX: support multiple symbol
        ICEBOX: support inline comment
        """
        regex = re.compile(r'^' + symbol + '.*$')
        return [line for line in trg if not regex.match(line)]

    @staticmethod
    def removeBlankLines(trg: List[str]):
        return [line for line in trg if '' != line]


class FileTypeError(Exception):
    pass


if __name__ == "__main__":
    main()
