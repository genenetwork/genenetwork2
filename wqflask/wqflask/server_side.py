# handles server side table processing



class ServerSideTable(object):
    """
        This class is used to do server-side processing
        on the DataTables table such as paginating, sorting,
        filtering(not implemented) etc. This takes the load off
        the client-side and reduces the size of data interchanged.

        Usage:
            ServerSideTable(table_data, request_values)
        where,
            `table_data` must have data members
            `rows_count` as number of rows in the table,
            `table_rows` as data rows of the table,
            `header_data_names` as headers names of the table.

            `request_values` must have request arguments values
            including the DataTables server-side processing arguments.

        Have a look at snp_browser_table() function in 
        wqflask/wqflask/views.py for reference use.
    """

    def __init__(self, rows_count, table_rows, header_data_names, request_values):
        self.request_values = request_values
        self.sEcho = self.request_values['sEcho']

        self.rows_count = rows_count
        self.table_rows = table_rows
        self.header_data_names = header_data_names
        
        self.sort_rows()
        self.paginate_rows()

    def sort_rows(self):
        """
        Sorts the rows taking in to account the column (or columns) that the
        user has selected.
        """
        def is_reverse(str_direction):
            """ Maps the 'desc' and 'asc' words to True or False. """
            return True if str_direction == 'desc' else False

        if (self.request_values['iSortCol_0'] != "") and (int(self.request_values['iSortingCols']) > 0):
            for i in range(0, int(self.request_values['iSortingCols'])):
                column_number = int(self.request_values['iSortCol_' + str(i)])
                column_name = self.header_data_names[column_number - 1]
                sort_direction = self.request_values['sSortDir_' + str(i)]
                self.table_rows = sorted(self.table_rows,
                              key=lambda x: x[column_name],
                              reverse=is_reverse(sort_direction))

    def paginate_rows(self):
        """
        Selects a subset of the filtered and sorted data based on if the table
        has pagination, the current page and the size of each page.
        """
        def requires_pagination():
            """ Check if the table is going to be paginated """
            if self.request_values['iDisplayStart'] != "":
                if int(self.request_values['iDisplayLength']) != -1:
                    return True
            return False

        if not requires_pagination():
            return

        start = int(self.request_values['iDisplayStart'])
        length = int(self.request_values['iDisplayLength'])

        # if search returns only one page
        if len(self.table_rows) <= length:
            # display only one page
            self.table_rows = self.table_rows[start:]
        else:
            limit = -len(self.table_rows) + start + length
            if limit < 0:
                # display pagination
                self.table_rows = self.table_rows[start:limit]
            else:
                # display last page of pagination
                self.table_rows = self.table_rows[start:]

    def get_page(self):
        output = {}
        output['sEcho'] = str(self.sEcho)
        output['iTotalRecords'] = str(float('Nan'))
        output['iTotalDisplayRecords'] = str(self.rows_count)
        output['data'] = self.table_rows
        return output
