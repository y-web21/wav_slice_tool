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
    obs = wavSlice(* sys.argv[2:5])
    obs.open(sys.argv[1]).setOpenedFileToList().slice()

T = TypeVar('T')


class wavSlice(Generic[T]):
    """
    gen a long wav file to a short wav file with the specified note and bpm.
    """

    def __init__(self, bpm: int, inputDir: str, outputDir: str = '') -> None:
        super().__init__()
        self._bpm = int(bpm)
        self._inputDir = inputDir
        self._outputDir = outputDir if outputDir != '' else inputDir

    def setBpm(self, bpm: int) -> T:
        self._bpm = int(bpm)
        return self

    def setInputWavesDir(self, inputDir: str) -> T:
        self._inDir = inputDir
        return self

    def setOutputWavesDir(self, outputDir: str) -> T:
        self._outDir = outputDir
        return self

    # @classmethod
    def open(self, path: str, isCsv: bool = True) -> T:
        """
        docstring
        """
        try:
            file = open(path)
        except Exception as e:
            print(repr(e))

        if not isinstance(file, TextIOWrapper):
            raise FileTypeError(f'reading illegal file')

        self._openedText = []
        if isCsv:
            self._openedText = [line for line in csv.reader(file)]
        else:
            self._openedText = [line.strip() for line in file.readlines()]

        file.close
        return self

    def setOpenedFileToList(self) -> T:
        """
        """
        self._sliceDefinitions = [[x[0], x[1], x[2], y] for x in self._openedText for y in x[3:]]
        return self

    def setOpenedFileToSplitList(self) -> T:
        """
        """
        self._splitDefinitions = [[x[0], x[1], x[2], y] for x in self._openedText for y in x[3:]]
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
    def slice(self):
        """
        parse csv. and slice a wav file from 0 ms.

        csv file rules.
        1. no header. (field name not required on line 1)
        2. field  ->  notes(not use, for user memo.), wav_file_name, suffix, ...note_length
        e.g.
        base#c, 2204cps.wav, 8    # slice to eighth note length.
        screech, wow_metal.wav, 4, 4.    # slice to quarter note and dotted quarter note length.
        """

        for xx in self._sliceDefinitions:
            inputFile = str(Path(self._inputDir, xx[1]))

            note, multiplier = wavSlice.parseNoteDotted(xx[3])
            ms = wavSlice.noteIntToMs(note, multiplier, self._bpm)

            if xx[2] != '':
                suffix = xx[2]
            else:
                suffix = str(ms) if self.getSuffix(multiplier) == 'none'else str(note) + self.getSuffix(multiplier)

            outputFile = re.sub(r'(.*)(.wav)', r'\g<1>_' + suffix + r'\2', str(Path(self._outputDir, xx[1])))
            self._sliceByPydub(inputFile, outputFile, ms)

    fadeOut:int = 20
    def _sliceByPydub(self, input: str, output: str, end: int, begin: int = 0) -> None:
        """
        TODO: this method move to pydub wrapper class
        """
        if Path(output).exists():
            os.remove(output)
        sound = AudioSegment.from_file(input, format="wav")
        if sound.duration_seconds * 1000 > end - begin:
            sound[begin:end].fade_out(self.fadeOut).export(output, format="wav")
        else:
            print(f'{output} is too long specified.\tsound duration: {int(sound.duration_seconds * 1000)}ms')

    def getSuffix(self, multiplier: float) -> str:
        if multiplier == 1.75:
            return 'dd'
        elif multiplier == 1.5:
            return 'dot'
        elif multiplier == 1.25:
            return 'none'
        return ''

    @ staticmethod
    def parseNoteDotted(numString: str) -> Tuple[int, float, str]:
        """
        arg: num string, suffix dot, double-dotted, dash(1.25)
        return: (int(args1), multiplier, suffix_string)
        ICEBOX: validate numString. now runtime error.
        """
        if '..' in numString:
            return int(numString.replace('..', '')), 1.75
        elif '.' in numString:
            return int(numString.replace('.', '')), 1.5
        elif '-' in numString:
            return int(numString.replace('-', '')), 1.25

        return int(numString), 1

    @ staticmethod
    def noteIntToMs(note: int, multiplier: float = 1, bpm: int = 120) -> int:
        """
        CROTCHET = quarter note ms
        # note to millisecond
        CROTCHET = 60 * 1000 / 110
        """
        CROTCHET: int = 60 * 1000 / bpm
        return int(4 / note * CROTCHET * multiplier)

    @ staticmethod
    def removeComments(trg: List[str], symbol: str):
        """
        ICEBOX: support multiple symbol
        ICEBOX: support inline comment
        """
        regex = re.compile(r'^' + symbol + '.*$')
        return [line for line in trg if not regex.match(line)]

    @ staticmethod
    def removeBlankLines(trg: List[str]):
        return [line for line in trg if '' != line]


class FileTypeError(Exception):
    pass


if __name__ == "__main__":
    main()
