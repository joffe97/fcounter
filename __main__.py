from pathlib import Path
import json
from sys import stderr, argv
from typing import Any, Optional, Type
import argparse


class FCounterFile:
    FCOUNTER_STORAGE_FILE = Path(f"{argv[0]}/fcounter.json")

    __COUNTER_VALUE_STR = "counter_value"
    __PREV_COUNTER_VALUE_STR = "prev_counter_value"

    def __init__(self) -> None:
        if not self.FCOUNTER_STORAGE_FILE.exists():
            self.FCOUNTER_STORAGE_FILE.touch(0o777)

    def read_json(self) -> dict:
        file_text = self.FCOUNTER_STORAGE_FILE.read_text()
        return json.loads(file_text) if file_text else dict()

    def write_json(self, json_dict: dict):
        json_str = json.dumps(json_dict)
        self.FCOUNTER_STORAGE_FILE.write_text(json_str)

    def get_variable(self, name: str, var_type: Type) -> Optional[Any]:
        value = self.read_json().get(name)
        return var_type(value) if value is not None else None

    def set_variable(self, name: str, value: object):
        json_dict = self.read_json()
        json_dict[name] = value
        self.write_json(json_dict)

    @property
    def prev_counter_value(self) -> Optional[float]:
        value_int = self.get_variable(self.__PREV_COUNTER_VALUE_STR, int)
        if value_int is None:
            return None
        return value_int / 100

    @prev_counter_value.setter
    def prev_counter_value(self, value: Optional[float]):
        file_value = float(value * 100) if value is not None else None
        self.set_variable(self.__PREV_COUNTER_VALUE_STR, file_value)

    @property
    def counter_value(self) -> float:
        return (self.get_variable(self.__COUNTER_VALUE_STR, int) or 0) / 100

    @counter_value.setter
    def counter_value(self, value: float):
        self.prev_counter_value = self.counter_value

        file_value = float(value * 100)
        self.set_variable(self.__COUNTER_VALUE_STR, file_value)


class FCounter:
    def __init__(self, fcounter_file: FCounterFile) -> None:
        self.fcounter_file = fcounter_file

    def add(self, num: float):
        self.fcounter_file.counter_value += num

    def sub(self, num: float):
        self.fcounter_file.counter_value -= num

    def set(self, num: float):
        self.fcounter_file.counter_value = num

    def revert(self) -> bool:
        prev_counter_value = self.fcounter_file.prev_counter_value
        if prev_counter_value is None:
            prev_counter_value = 0.0
        (
            self.fcounter_file.counter_value,
            self.fcounter_file.prev_counter_value,
        ) = (prev_counter_value, self.fcounter_file.counter_value)
        return True

    def get_cur_count(self) -> float:
        return self.fcounter_file.counter_value


class System:
    def __init__(self) -> None:
        self.argparser = argparse.ArgumentParser()

        self.argparser.add_argument("number", type=float, nargs="?")
        self.argparser.add_argument(
            "-s",
            "--set",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        self.argparser.add_argument(
            "-d",
            "--decrement",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        self.argparser.add_argument(
            "-r",
            "--revert",
            action=argparse.BooleanOptionalAction,
            default=False,
        )
        self.argparser.add_argument(
            "-p",
            "--print",
            action=argparse.BooleanOptionalAction,
            default=False,
        )

        args = self.argparser.parse_args()

        self.fcounter = FCounter(FCounterFile())

        self.number: Optional[int] = args.number
        self.set: bool = args.set
        self.decrement: bool = args.decrement
        self.revert: bool = args.revert
        self.print: bool = args.print

    def run(self):
        if self.revert:
            if (
                self.number is not None
                or self.decrement
                or self.print
                or self.set
            ):
                stderr.write("Invalid input")
                return
            self.fcounter.revert()
        elif self.print:
            if (
                self.number is not None
                or self.decrement
                or self.revert
                or self.set
            ):
                stderr.write("Invalid input")
                return
        elif self.number is not None:
            if self.decrement and self.set:
                stderr.write("Invalid input")
                return
            fcounter_handle_func = (
                FCounter.set
                if self.set
                else FCounter.sub if self.decrement else FCounter.add
            )
            fcounter_handle_func(self.fcounter, self.number)

        count_str = format(self.fcounter.get_cur_count(), ".2f")
        count_str = count_str.rstrip(".0") or "0"
        print(count_str)


if __name__ == "__main__":
    System().run()
