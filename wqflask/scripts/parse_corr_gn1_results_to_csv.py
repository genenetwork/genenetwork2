import csv
import sys
from functools import reduce, partial
import pathlib

from lxml import etree

def thread(value, *functions):
    return reduce(lambda result, func: func(result), functions, value)

def parse_file(filename: pathlib.Path):
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
    # print(f"Found {len(found)} with the expected first row")
    return found[0]

def table_contents(table):
    return tuple(
        tuple(" ".join(text.strip() for text in cell.xpath(".//child::text()"))
            for cell in row)
        for row in table.xpath("./tbody/tr"))


def to_dicts(contents):
    frow = contents[0]
    return tuple(dict(zip(frow, row)) for row in contents[1:])

def write_csv(input_file, to_output_file, contents):
    def __write__(stream):
        writer = csv.DictWriter(
            stream, fieldnames=list(contents[0].keys()),
            dialect=csv.unix_dialect)
        writer.writeheader()
        writer.writerows(contents)

    if not to_output_file:
        return __write__(sys.stdout)

    output_file = input_file.parent.joinpath(
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

def run():
    if len(sys.argv) != 3:
        print("Usage: python3 test.py <input-file> <to-ouput-file: [Y/n]>")
        sys.exit(1)

    _this_file, input_file, to_output_file = sys.argv
    input_file = pathlib.Path(input_file).absolute()
    thread(
        input_file,
        parse_file,
        lambda tree: tree.xpath("//table"),
        results_table,
        table_contents,
        to_dicts,
        partial(write_csv, input_file, to_output_file == "Y")
    )

if __name__ == "__main__":
    run()
