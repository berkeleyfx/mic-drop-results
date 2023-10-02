# Copyright 2023 Phan Huy

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

import copy
from enum import Enum, auto
import sys
from traceback import format_exception

from colorama import Fore, Style

from compiled_regex import *
from constants import *
from utils import inp, abs_dir


class Tag(Enum):
    DEV = "DEV"
    SYS = "SYSTEM"
    INTERNET = "ConnectionError"
    FILE_SETTINGS = "settings.ini"
    FILE_TOKEN = "token.txt"
    FILE_DATA = "data.xlsm"


class Traceback:
    templates = {
        "screenshot": [
            "Please take a screenshot of everything displayed below when filling out a bug report."
            " Thank you for your patience in getting this issue resolved."
        ],
        "invalid_config": [
            "Please verify that these config variables are in their valid formats"
            " as specified in the notes from settings.ini."
        ],
        "developer_portal": [
            "You can follow this link to Discord's Developer Portal and create your token.\n"
            "https://discord.com/developers/applications"
        ],
    }

    _err_lookup = {
        # 0 – 19: Dev errors
        0: [Tag.DEV, "Unhandled error."],
        1: [Tag.DEV, "Traceback ID lookup error."],
        # 20 – 29: API errors
        20: [
            Tag.INTERNET,
            "Failed to communicate with Discord's API.",
            "We are unable to download avatars at the moment.",
            "Please check your internet connection and try again.",
        ],
        21: [
            Tag.FILE_TOKEN,
            "No valid bot token found.",
            "Please add your token(s) to token.txt or turn avatar mode in settings.ini off entirely.",
            *templates["developer_portal"],
        ],
        21.1: [
            Tag.FILE_TOKEN,
            "Invalid bot token.",
            "The following bot token is either invalid, has been reset, or deactivated by Discord.",
            "Please replace the following token from token.txt with a new, valid one.",
            *templates["developer_portal"],
        ],
        22: [Tag.DEV, "Unknown Discord's API error."],
        23: [
            Tag.FILE_DATA,
            "Failed to fetch the data of certain users.",
            "We are unable to download the avatars of the following" + " users:",
            "Make sure these user IDs are valid and that they have not"
            + " deleted nor moved to a new account with the same name.",
        ],
        # 30 – 39: Config errors
        30: [
            Tag.FILE_SETTINGS,
            "Missing config variables.",
            "The following config variables do not exist in the current"
            + " settings file:",
            "Please download the latest version of settings.ini from"
            + " this source and try again:\n"
            + TEMPLATES_URL,
        ],
        31: [
            Tag.FILE_SETTINGS,
            "Invalid data type for config variable.",
            *templates["invalid_config"],
        ],
        31.1: [
            Tag.FILE_SETTINGS,
            "Config variable failed requirement check.",
            *templates["invalid_config"],
        ],
        # 40 – 59: System errors
        40: [
            Tag.SYS,
            "Missing required files.",
            "Please download the missing files at:\n" + TEMPLATES_URL,
        ],
        41: [
            Tag.SYS,
            "Failed to import VBA macros due to a privacy setting.",
            "Please open PowerPoint and navigate to:\nFile > Options"
            + " > Trust Center > Trust Center Settings > Macro Settings",
            'Make sure "Trust access to the VBA project object model"'
            + " option is checked.",
        ],
        # 60 and above: Data errors
        60: [
            Tag.FILE_DATA,
            "Sorting columns cannot contain text.",
            "The sorting columns of the following sheet contain text"
            + " but expect numeric data throughout.",
            "Have you pasted data in the wrong column, by any chance?",
        ],
        61: [
            Tag.FILE_DATA,
            "Sorting columns cannot contain empty values.",
            "The sorting columns of the following sheet contain empty"
            + " cell values.",
            "These empty values will be replaced by 0's if you proceed" + " onward.",
        ],
        68: [
            Tag.FILE_DATA,
            "No valid sheet found.",
            "We have examined every sheet from the following Excel file:\n"
            + str(abs_dir("data.xlsm")),
            "No sheet appears to be in the correct and usable format.",
            "Please download a sample data.xlsm file from this source"
            + " and use it as a reference for customizing your own:\n"
            + TEMPLATES_URL,
        ],
        70: [
            Tag.FILE_DATA,
            "Missing an underscore before every user ID.",
            "Please add an underscore (_) before every user ID from the"
            + ' "__uid" column. For example: _1010885414850154587',
            "This is intended to prevent Microsoft Excel and the"
            + " program froms undesirably rounding the UIDs.",
        ],
        71: [
            Tag.FILE_DATA,
            "Template does not exist.",
            "The following template(s) cannot be matched with any slide"
            + " from template.pptm.",
        ],
    }

    def lookup(self, tb: float) -> list[str]:
        try:
            res = copy.deepcopy(self._err_lookup[tb])
            res[1] = f"[{res[0].value}] {res[1]}"

            if res[0] == Tag.DEV:
                res += self.templates["screenshot"]

            return res[1:]
        except KeyError:
            tb_list = [i for i in self._err_lookup if abs(tb - i) < 5]
            if not tb_list:
                tb_list = list(self._err_lookup)

            Error(1).throw(
                f"Traceback ID: {tb}\n" f"Perhaps you are looking for: {tb_list}"
            )
            return []


class ErrorType(Enum):
    ERROR = auto()
    WARNING = auto()
    INFO = auto()


class Error(Traceback):
    def __init__(self, tb: float):
        self.tb = tb
        self.tb_code = self.get_code()

        # Look up content with traceback ID
        self.content: list[str] = super().lookup(tb)

    def get_code(self) -> str:
        whole, decimal = int(self.tb), round(self.tb % 1, 7)

        whole = str(whole).zfill(3)
        decimal = str(decimal).replace(".", "")

        code = whole if int(decimal) == 0 else f"{whole}.{int(decimal)}"
        return f"E-{code}"

    def throw(self, *details: str, err_type: ErrorType = ErrorType.ERROR) -> None:
        self.content += [*details]

        # Redact sensitive information
        for i, x in enumerate(self.content):
            self.content[i] = match_username.sub("user", str(x))

        self._print(*self.content, err_type=err_type)

    def _print(self, *content: str, err_type: ErrorType = ErrorType.ERROR) -> None:
        """Handles and reprints an error with human-readable details.

        Prints an error message with paragraphs explaining the error
        and double-spaced between paragraphs.

        The first paragraph will be shown beside the error type and will
        inherit the color red if it is an error, the color yellow if it
        is a warning, and the default color if it is an info message.

        Args:
            *content: every argument makes a paragraph of the error
                message. The first paragraph should summarize the error
                in one sentence. The rest of the paragraphs will explain
                what causes and how to resolve the error.
            err_type (optional): the error type taken from the ErrorType
                class. Defaults to ErrorType.ERROR.
        """
        if content:
            style = None
            if err_type == ErrorType.ERROR:
                style = "red"
            elif err_type == ErrorType.WARNING:
                style = "yellow"

            console.print(
                f"\n\n[b]{err_type.name}:[/b] {content[0]}"
                + f" (Traceback code: {self.tb_code})",
                style=style,
            )  # error details

        if len(content) > 1:
            console.print()
            console.print(content[1])  # steps to resolve

            if len(content) > 2:
                self._print_indent(*content[2:], sep="\n\n    ")  # extra details

        if err_type == ErrorType.ERROR:
            inp("\nPress Enter to exit the program...", hide_text=True)
            sys.exit(1)
        else:
            inp("\nPress Enter to skip this warning...", hide_text=True)

    def _print_indent(self, *content, sep, indent=4) -> None:
        console.print(
            *[v.replace("\n", "\n" + " " * indent) for v in content], sep=sep
        )  # TODO: use regex


def print_exception_hook(exc_type, exc_value, tb) -> None:
    Error(0).throw("".join(format_exception(exc_type, exc_value, tb))[:-1])
