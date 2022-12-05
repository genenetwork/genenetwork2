import csv
import sys
import json
from pathlib import Path
from functools import reduce, partial
from typing import Any, Union, Sequence, Optional
from argparse import Action, Namespace, ArgumentError, ArgumentParser

from lxml import etree

def thread(value, *functions):
    return reduce(lambda result, func: func(result), functions, value)

def parse_file(filename: Path):
    with open(filename, encoding="utf-8") as inpfl:
        raw_html = inpfl.read()

    return etree.HTML(raw_html)

def first_row_headers(table):
    return tuple(
        " ".join(text.strip() for text in cell.xpath(".//child::text()"))
        for cell in table.xpath("./tbody/tr[1]/td"))

def results_table(tables):
    found = tuple(filter(
        lambda table: (
            first_row_headers(table)[0:4] ==
            ("Index", "Record ID", "Symbol", "Description")),
        tables))
    return found[0]

def table_contents(table):
    return tuple(
        tuple(" ".join(text.strip() for text in cell.xpath(".//child::text()"))
            for cell in row)
        for row in table.xpath("./tbody/tr"))


def to_dicts(contents):
    frow = contents[0]
    return tuple(dict(zip(frow, row)) for row in contents[1:])

def write_csv(
        input_file: Path, output_dir: Union[bool, Path],
        contents: Sequence[dict]) -> Sequence[Sequence[str]]:
    def __write__(stream):
        writer = csv.DictWriter(
            stream, fieldnames=list(contents[0].keys()),
            dialect=csv.unix_dialect)
        writer.writeheader()
        writer.writerows(contents)

    if not bool(output_dir):
        return __write__(sys.stdout)

    output_file = output_dir.joinpath(
        f"{input_file.stem}__results.csv")
    with open(output_file, "w", encoding="utf-8") as out_file:
        return __write__(out_file)

def output_stream():
    if not to_output_file:
        return sys.stdout

    output_file = input_file.parent.joinpath(
        f"{input_file.stem}.csv")
    with open(output_file) as out_file:
        yield out_file

class FileCheck(Action):
    """Action class to check existence of a given file path."""

    def __init__(self, option_strings, dest, **kwargs):
        "Initialise the FileCheck action class"
        super().__init__(option_strings, dest, **kwargs)

    def __call__(# pylint: disable=[signature-differs]
            self, parser: ArgumentParser, namespace: Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str] = "") -> None:
        """Check existence of a given file path and set it, or raise an
        exception."""
        the_path = str(values or "")
        the_file = Path(the_path).absolute().resolve()
        if not the_file.is_file():
            raise ArgumentError(
                self,
                f"The file '{values}' does not exist or is a folder/directory.")

        setattr(namespace, self.dest, the_file)

class DirectoryCheck(Action):
    """Action class to check the existence of a particular directory"""
    def __init__(self, option_strings, dest, **kwargs):
        """Init `DirectoryCheck` action object."""
        super().__init__(option_strings, dest, **kwargs)

    def __call__(
            self, parser: ArgumentParser, namespace: Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str] = "") -> None:
        the_dir = Path(str(values or "")).absolute().resolve()
        if not the_dir.is_dir():
            raise ArgumentError(
                self, f"The directory '{the_dir}' does not exist!")

        setattr(namespace, self.dest, the_dir)

def gn1_parser(subparsers) -> None:
    parser = subparsers.add_parser("gn1")
    parser.add_argument(
        "inputfile", help="The HTML file to parse", action=FileCheck)
    parser.add_argument(
        "--outputdir", help="Path to output directory", action=DirectoryCheck,
        default=False)
    parser.set_defaults(
        func=lambda args: thread(
            args.inputfile,
            parse_file,
            lambda tree: tree.xpath("//table"),
            results_table,
            table_contents,
            to_dicts,
            partial(write_csv, args.inputfile, args.outputdir)))

def tablejson_script(scripts):
    for script in scripts:
        script_content = thread(
            script.xpath('.//child::text()'),
            lambda val: "".join(val).strip())
        if script_content.find("var tableJson") >= 0:
            return json.loads(thread(
                script_content,
                lambda val: val[len("var tableJson = "):].strip()))
        continue
    return None

def gn2_parser(subparsers) -> None:
    parser = subparsers.add_parser("gn2")
    parser.add_argument(
        "inputfile", help="The HTML file to parse", action=FileCheck)
    parser.add_argument(
        "--outputdir", help="Path to output directory", action=DirectoryCheck,
        default=False)
    parser.set_defaults(
        func=lambda args: thread(
            args.inputfile,
            parse_file,
            lambda tree: tree.xpath("//script"),
            tablejson_script,
            partial(write_csv, args.inputfile, args.outputdir)
        ))

def parse_cli_args():
    parser = ArgumentParser(
        "parse_corr_html_results_to_csv",
        description = "Parse correlation results from the given HTML file.")
    subparsers = parser.add_subparsers(
        title="subcommands", description="Valid subcommands",
        help="additional help")
    gn1_parser(subparsers)
    gn2_parser(subparsers)

    return parser.parse_args()

def run():
    args = parse_cli_args()
    args.func(args)

if __name__ == "__main__":
    run()
