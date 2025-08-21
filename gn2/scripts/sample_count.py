"""
Script to count rows in PublishData table corresponding to each PublishXRef entry
and update the NSamples field in PublishXRef.

Usage:
python3 sample_count.py {SQL_URI} {filepath/name}
"""

import argparse
from urllib.parse import urlparse
import MySQLdb
from MySQLdb import Error as MySQLdbError
from typing import Dict, Any

from gn_libs.mysqldb import parse_db_url



def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description='Count PublishData rows for each PublishXRef entry and update NSamples'
    )
    parser.add_argument('uri', help='MySQL URI (e.g. mysql://user:pass@host/dbname)')
    parser.add_argument(
        '--output',
        help='Optional file to output results to',
        required=False
    )
    args = parser.parse_args()

    # Parse URI and connect to MySQL
    try:
        conn = MySQLdb.connect(**{
            **parse_db_url(args.uri),
            "autocommit": False
        })
    except ValueError as e:
        print(f"Invalid URI: {str(e)}")
        return
    except MySQLdbError as e:
        print(f"Database connection failed: {str(e)}")
        return

    # Query that selects count of samples (with data) for each phenotype trait
    pheno_data_query = """
    SELECT px.Id, px.InbredSetId, COUNT(pd.Id) as sample_count
    FROM PublishXRef as px
    LEFT OUTER JOIN PublishData AS pd ON px.DataId = pd.Id
    GROUP BY px.Id, px.InbredSetId;
    """

    # Execute query and update PublishXRef table with sample counts
    try:
        with conn.cursor() as cursor:
            # Execute the count query
            cursor.execute(pheno_data_query)
            results = cursor.fetchall()

            if args.output:
                # Write results to CSV if output file is specified
                try:
                    with open(args.output, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(['Id', 'InbredSetId', 'NSamples'])  # header
                        writer.writerows(results)
                    print(f"Results written to {args.output}")
                except IOError as e:
                    print(f"Failed to write output file: {str(e)}")

            # Prepare and execute updates
            update_n_query = """
            UPDATE PublishXRef
            SET NSamples = %s
            WHERE Id = %s AND InbredSetId = %s;
            """

            updated_rows = 0
            for row in results:
                cursor.execute(update_n_query, (row[2], row[0], row[1]))
                updated_rows += cursor.rowcount

            # Commit the transaction
            conn.commit()
            print(f"Successfully updated {updated_rows} records in PublishXRef")

    except MySQLdbError as e:
        conn.rollback()
        print(f"Database operation failed: {str(e)}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
