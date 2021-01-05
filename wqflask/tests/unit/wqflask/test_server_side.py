import unittest

from wqflask.server_side import ServerSideTable


class TestServerSideTableTests(unittest.TestCase):
    """
    Test the ServerSideTable class

    test table:
        first, second, third
        'd', 4, 'zz'
        'b', 2, 'aa'
        'c', 1, 'ss'
    """

    def test_get_page(self):
        rows_count = 3
        table_rows = [
            {'first': 'd', 'second': 4, 'third': 'zz'}, 
            {'first': 'b', 'second': 2, 'third': 'aa'}, 
            {'first': 'c', 'second': 1, 'third': 'ss'},
        ]
        headers = ['first', 'second', 'third']
        request_args = {'sEcho': '1', 'iSortCol_0': '1', 'iSortingCols': '1', 'sSortDir_0': 'asc', 'iDisplayStart': '0', 'iDisplayLength': '3'}

        test_page = ServerSideTable(rows_count, table_rows, headers, request_args).get_page()
        self.assertEqual(test_page['sEcho'], '1')
        self.assertEqual(test_page['iTotalRecords'], 'nan')
        self.assertEqual(test_page['iTotalDisplayRecords'], '3')
        self.assertEqual(test_page['data'], [{'first': 'b', 'second': 2, 'third': 'aa'}, {'first': 'c', 'second': 1, 'third': 'ss'}, {'first': 'd', 'second': 4, 'third': 'zz'}])
