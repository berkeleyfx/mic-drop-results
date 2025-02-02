# Copyright 2023 Phan Huy

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

from collections.abc import Callable, Generator
import ctypes
import re
import sys
from typing import Any, TypeVar

import cv2
from unidecode import unidecode

from compiled_regex import match_non_username_char, match_space
from constants import *


def is_number(val: Any) -> bool:
    """Checks if value can be converted to type float."""
    try:
        float(val)
        return True
    except ValueError:
        return False


T = TypeVar("T")  # pronounces "typed"
A = TypeVar("A")  # pronounces "anything"


def as_type(t: Callable[[A], T], val: A) -> T | A:
    """Returns value as type t if possible, otherwise returns value as it is.

    Args:
        t (Callable): a callable function that outputs value in the
            desirable type.
        val: the value to convert.

    Examples:
        >>> as_type(float, '004'), as_type(int, 3.2)
        (4.0, 3)

        Returns the value as is if it cannot be converted.

        >>> as_type(int, 'lorem ipsum')
        'lorem ipsum'

    Note:
        Please note that a float under str type (e.g. '3.0') cannot be
        convert directly into type int.

        You could use a wrapper function for t in such cases:

        >>> to_int = lambda str_val: int(float(str_val))
        >>> as_type(to_int, '3.0')
        3
    """
    try:
        return t(val)
    except ValueError:
        return val


def hex_to_rgb(hex_val: str) -> tuple[int, ...]:
    return tuple(int(hex_val.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))


def parse_version(*versions: str) -> Generator[tuple[int, ...], None, None]:
    """Parses version string into tuple (e.g. 'v3.11.1' into (3, 11, 1)).

    Examples:
        >>> parse_version('3.11.1')
        (3, 11, 1)

        You could also parse multiple versions at the same time:

        >>> latest, current = parse_version('v3.11', 'v3.10')
        >>> current
        (3, 10)
    """
    return (tuple(map(int, v.lstrip("v").split("."))) for v in versions)


def abs_dir(*rels: str | Path) -> Path:  # TODO: update docstring
    """Returns the absolute path from a relative path.

    Relative path here uses the path to the running file as a reference
    point instead of the current working directory.

    Examples:
        Given that the directory of the running file is:
        `D:\\\\parent_dir\\\\src\\\\md_results\\\\`

        The demonstration will yield the following result:

        >>> abs_dir('vba', 'macros.py')
        'D:\\\\parent_dir\\\\src\\\\md_results\\\\vba\\\\macros.py'

        You may also pass an absolute directory for the first argument.

        >>> AVATAR_DIR = abs_dir('avatars')
        >>> AVATAR_DIR
        'D:\\\\parent_dir\\\\src\\\\md_results\\\\avatars'
        >>> abs_dir(AVATAR_DIR, 'avatar.png')
        'D:\\\\parent_dir\\\\src\\\\md_results\\\\avatars\\\\avatar.png'
    """
    return MAIN_DIR.joinpath(*rels)


def enable_console():
    """Shows cursor and allows text selection."""
    console.show_cursor(True)
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(
        kernel32.GetStdHandle(-10),
        (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x40 | 0x100),
    )


def disable_console():
    """Disables all console interactions."""
    console.show_cursor(False)
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(
        kernel32.GetStdHandle(-10),
        (0x4 | 0x80 | 0x20 | 0x2 | 0x10 | 0x1 | 0x00 | 0x100),
    )


def inp(*args, hide_text=False, **kwargs) -> str:  # TODO: add docstring, optimize code
    """Wrapper function for rich.console.Console.input().

    This function inherits all the arguments and keyword arguments of
    the built-in print function. It also enables QuickEdit to allow
    the user to copy printed messages, which are usually error details,
    and disables it afterwards.

    Returns:
        The string value of user input.
    """
    enable_console()  # allow copying of the error message
    console.print(*args, **kwargs, end="")
    i = console.input(password=hide_text)
    disable_console()

    return i


class ProgressBar:
    """Creates and prints a progress bar.

    Attributes:
        prog: number of work done. Updates via the add() method.
        total: number of work to perform.
        title: title shown to the left of the progress bar.
        max_title_length: length of the longest title to ensure left
            alignment of the progress bars when there are more than
            one bar.
        bar_length: length of the progress bar in characters.
        desc: description of the task in progress shown below the
            progress bar. Updates via the set_description() method.
    """

    def __init__(
        self, total: int, *, title: str, max_title_length: int, bar_length: int = 40
    ) -> None:
        self.prog: int = 0
        self.total = total
        self.title = title
        self.max_title_length = max_title_length
        self.bar_length = bar_length
        self.desc: str = ""

    def refresh(self) -> None:
        """Reprints the progress bar with updated parameters."""
        filled_length = round(self.bar_length * self.prog / self.total)

        percents = round(100 * self.prog / self.total, 1)
        bar = "█" * filled_length + " " * (self.bar_length - filled_length)

        if self.prog > 0:
            sys.stdout.write(
                "\033[2K\033[A\r"
            )  # delete line, move cursor up, and to beginning of line
            sys.stdout.flush()

        title_right_padding = self.max_title_length - len(self.title) + 1
        sys.stdout.write(
            f'{self.title}{" " * title_right_padding}'
            f"|{bar}| {self.prog}/{self.total} [{percents}%]"
            f"{self.desc}"
        )

        # Preview:      Merge   |████████████████████████| 7/7 [100%]
        #               Group 1 |███████████████         | 5/8 [63%]
        #               Filling in judging data

        if self.prog == self.total:
            sys.stdout.write(
                "\033[2K\r"
            )  # delete line and move cursor to beginning of line

        sys.stdout.flush()

    def set_description(self, desc: str = "") -> None:
        """Sets the description shown below the progress bar."""
        self.desc = "\n" + desc
        self.refresh()

    def add(self, increment: int = 1) -> None:
        """Updates the progress by a specified increment."""
        self.prog += increment
        self.prog = min(self.prog, self.total)
        self.refresh()


def get_avatar_dir(
    uid: str | None = None,
    *,
    og_dir: Path | None = None,
    effect: int = 0,
) -> Path:  # TODO: docstring
    """Returns the local path to the avatar file from user ID."""
    if uid is not None:
        return abs_dir(AVATAR_DIR, f"{effect}_{uid}.png")

    # uid is None:
    if og_dir is None or og_dir.stem == og_dir.name:
        raise ValueError("When uid is None, og_dir must lead to a file.")

    return abs_dir(AVATAR_DIR, f"{effect}_{og_dir.name[2:]}")


def artistic_effect(og_dir: Path, *, effect: int) -> Path:
    """Creates an image with applied artistic effect and returns the path."""
    if effect != 0:
        img = cv2.imread(str(og_dir))
        match effect:  # TODO: add more effects
            case 1:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        fx_dir = get_avatar_dir(og_dir=og_dir, effect=effect)
        cv2.imwrite(str(fx_dir), img)
        return fx_dir

    return og_dir


def parse_coef(run_text: str, *, field_name: str) -> int:
    """Parses the coefficient of a field from the run text."""
    pattern = re.compile(r"(?<={" + field_name + r"})[0-9]")
    coef = pattern.findall(run_text)
    return int(*coef) if coef is not None else 0


def clean_name(text) -> str:
    text = unidecode(str(text))  # simplify special unicode characters
    if t := match_non_username_char.sub("", text):  # remove special characters
        text = t
    text = match_space.sub("", text).lower()  # remove space
    return text
