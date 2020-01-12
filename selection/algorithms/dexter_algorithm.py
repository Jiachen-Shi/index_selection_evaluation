from ..selection_algorithm import SelectionAlgorithm
from ..index import Index
import subprocess
import logging
import os


DEFAULT_PARAMETERS = {'min_saving_percentage': 50}


class DexterAlgorithm(SelectionAlgorithm):
    def __init__(self, database_connector, parameters):
        SelectionAlgorithm.__init__(self, database_connector, parameters,
                                    DEFAULT_PARAMETERS)

    def calculate_best_indexes(self, workload):
        min_percentage = self.parameters['min_saving_percentage']
        database_name = self.database_connector.db_name

        index_columns = []

        for query in workload.queries:
            command = (f'dexter {database_name}'
                       f' --min-cost-savings-pct {min_percentage} -s " ')
            command += query.text
            command += '"'
            # TODO prepare statement if create and drop view in statement
            # and update query text
            p = subprocess.Popen(command, cwd=os.getcwd(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, shell=True)
            with p.stdout:
                output_string = p.stdout.read().decode('utf-8')
            p.wait()

            log_output = output_string.replace('\n', '')
            logging.debug(f'{query}: {log_output}')

            if 'public.' in output_string:
                index = output_string.split('public.')[1].split(' (')
                table_name = index[0]
                column_names = index[1].split(')')[0].split(', ')
                columns = []
                for column_name in column_names:
                    column_object = next((c for c in query.columns
                                          if c.name == column_name
                                          and c.table.name == table_name),
                                         None)
                    columns.append(column_object)
                # Check if the same index columns already in list
                if columns not in index_columns:
                    index_columns.append(columns)
        return [Index(c) for c in index_columns]