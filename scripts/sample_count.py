"""
To run script:
python3 sample_count.py {SQL_URI} {filepath/name}

"""

import csv
import argparse
from urllib.parse import urlparse
import MySQLdb

def parse_mysql_uri(uri):
    """Parse a MySQL URI into connection components"""
    parsed_uri = urlparse(uri)

    return {
        'host': parsed_uri.hostname or 'localhost',
        'user': parsed_uri.username,
        'password': parsed_uri.password,
        'database': parsed_uri.path.lstrip('/'),
        'port': parsed_uri.port or 3306
    }

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description='Execute SQL query and export results to CSV'
    )
    parser.add_argument('uri', help='MySQL URI (e.g. mysql://user:pass@host/dbname)')
    parser.add_argument('output', help='File to output results to')
    args = parser.parse_args()

    # Parse URI and connect to MySQL
    try:
        db_config = parse_mysql_uri(args.uri)
        conn = MySQLdb.connect(
            host=db_config['host'],
            user=db_config['user'],
            passwd=db_config['password'],
            db=db_config['database'],
            port=db_config['port']
        )
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return

    # Query that selects count of samples (with data) for each phenotype trait
    pheno_data_query = """
    SELECT px.Id, px.InbredSetId, COUNT(pd.Id)
    FROM PublishXRef as px
        LEFT OUTER JOIN PublishData AS pd ON px.DataId = pd.Id
    GROUP BY px.Id, px.InbredSetId;
    """

    # Execute query and write results
    output_file = args.output
    try:
        with conn.cursor() as cursor:
            cursor.execute(pheno_data_query)
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            with open(output_file, 'w', newline='') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(column_names)
                writer.writerows(rows)
                
        print(f"Successfully wrote {len(rows)} rows to {output_file}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
