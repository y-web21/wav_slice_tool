from copy import deepcopy
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
    # obs.open(sys.argv[1]).setOpenedFileToList().slice()
    obs.readSettingFile(sys.argv[1]).split()


T = TypeVar('T')


class wavSlice(Generic[T]):
    """
    gen a long wav file to a short wav file with the specified note and bpm.
    """

    def __init__(self, bpm: int, inputDir: str, outputDir: str = '') -> None:
        super().__init__()
        self._bpm = int(bpm)
        self.paths = { 'inputDir': inputDir }
        self.paths['outputDir'] = outputDir if outputDir != '' else inputDir

        self.paths = self._solveRelativePath(self.paths)

        if not Path(self.paths['outputDir']).exists():
            os.mkdir(self.paths['outputDir'])

    @ staticmethod
    def _solveRelativePath(paths:dict[str]) -> dict[str]:
        for x, y in paths.items():
            if not Path(y).is_absolute():
                paths[x] = str(Path(y).resolve())
        return paths

    def setBpm(self, bpm: int) -> T:
        self._bpm = int(bpm)
        return self

    def readSettingFile(self, path: str, isCsv: bool = True) -> T:
        """
        docstring
        """
        self.paths['definitionFile'] =  path
        self._solveRelativePath(self.paths)
        try:
            file = open(self.paths['definitionFile'])
        except Exception as e:
            print(repr(e))

        if not isinstance(file, TextIOWrapper):
            raise FileTypeError(f'reading illegal file')

        self._openedText = []
        if isCsv:
            self._definitions = [line for line in csv.reader(file)]
        else:
            self._definitions = [line.strip() for line in file.readlines()]

        file.close
        return self

    def _iterSliceDefinition(self) -> List:
        for line in self._definitions:
            yield [[line[0], line[1], line[2], x] for x in line[3:]]

    def _iterSplitDefinition(self) -> List:
        return self._iterSliceDefinition()

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
        base#c, 2204cps.wav,, 8    # slice to eighth note length.
        screech, wow_metal.wav,, 4, 4.    # slice to quarter note and dotted quarter note length.
        """

        for chunk in self._iterSliceDefinition():

            for line in chunk:
                inputFile = str(Path(self.paths['inputDir'], line[1]))

                note, multiplier = wavSlice.parseNoteDotted(line[3])
                ms = wavSlice.noteIntToMs(note, multiplier, self._bpm)

                if line[2] != '':
                    suffix = line[2]
                else:
                    suffix = str(ms) if self._getSuffix(multiplier) == 'none'else str(note) + self._getSuffix(multiplier)

                outputFile = re.sub(r'(.*)(.wav)', r'\g<1>_' + suffix + r'\2', str(Path(self.paths['outputDir'], line[1])))
                self._sliceByPydub(inputFile, outputFile, 0, ms)

    # HACK: temp
    def split(self):
        """
        parse csv. and split a wav file.

        csv file rules.
        1. no header. (field name not required on line 1)
        2. field  ->  notes(not use, for user memo.), input wav file, (optional) suffix, ...split timings
        e.g.
        base#c, 2204cps.wav,, 8    # split into 2 files with eighth note timing.
        screech, wow_metal.wav,, 980ms, 4    # split into 3 files. after 980 ms, quarter note timing.
        """

        for chunk in self._iterSplitDefinition():
            currentMsPosition = 0
            digit = len(str(len(chunk))) if len(str(len(chunk)))  > 1  else 2
            chunk.append(deepcopy(chunk[-1]))
            chunk[-1][2] = 'eof'
            chunk[-1][3] = ''

            for i, instruction in enumerate(chunk):
                inputFile = str(Path(self.paths['inputDir'], instruction[1]))

                # TODO: process cutout
                if not re.match(r'^.*ms$', instruction[3]):
                    note, multiplier = wavSlice.parseNoteDotted(instruction[3])
                    ms = wavSlice.noteIntToMs(note, multiplier, self._bpm)
                    suffix = f'{str(ms)}ms' if self._getSuffix(
                        multiplier) == 'none'else str(note) + self._getSuffix(multiplier)
                else:
                    ms = int(str(instruction[3]).replace('ms',''))
                    suffix = f'{str(ms)}ms'

                if instruction[2] != '':
                    suffix = instruction[2]

                outputFile = re.sub(r'(.*)(.wav)', r'\g<1>_' + str(i).zfill(digit) + r'_' +
                                    suffix + r'\2', str(Path(self.paths['outputDir'], instruction[1])))

                self._sliceByPydub(inputFile, outputFile, currentMsPosition, ms + currentMsPosition)

                currentMsPosition += ms


    fadeOut: int = 20

    def _sliceByPydub(self, input: str, output: str, begin: int = 0, end: int = -1) -> None:
        """pydub pydub pydub

        TODO: this method move to pydub wrapper class
        Slicing a single wav file

        Args:
            input (str): input wave file path
            output (str): output wave file path
            end (int): begin of cut position(ms)
            begin (int): begin of cut position(ms)

        Returns:
            bool: Description of return value

        """
        if Path(output).exists():
            os.remove(output)

        sound = AudioSegment.from_file(input, format="wav")

        if end < 0:
            end = int(sound.duration_seconds * 1000)

        if sound.duration_seconds * 1000 > end:
            sound[begin:end].fade_out(self.fadeOut).export(output, format="wav")
        else:
            print(f'{output} is too long specified.\tsound duration: {int(sound.duration_seconds * 1000)}ms')

    @ staticmethod
    def _getSuffix(multiplier: float) -> str:
        if multiplier == 1.75:
            return 'dd'
        elif multiplier == 1.5:
            return 'dot'
        elif multiplier == 1.25:
            return 'none'
        return ''

    @ staticmethod
    def parseNoteDotted(numString: str) -> Tuple[int, float]:
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
        elif '' != numString:
            return int(numString), 1
        return -1, 1

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
