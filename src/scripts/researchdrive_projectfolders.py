import warnings
from logging.handlers import TimedRotatingFileHandler
warnings.simplefilter(action='ignore', category=UserWarning)

import logging
import sys
import argparse
import os
import datetime
import pandas
import configparser
import researchdrive


def excelwriter(xlsx_file, df_report, sheet_name='Sheet1', autofit=True):
    with pandas.ExcelWriter(xlsx_file, engine='xlsxwriter') as writer:
        df_report.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False, na_rep='')

        # Get the xlsxwriter workbook and worksheet objects.
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Get the dimensions of the dataframe.
        (max_row, max_col) = df_report.shape

        # Create a list of column headers, to use in add_table().
        column_settings = []
        for header in df_report.columns:
            column_settings.append({'header': header})

        # Add the table.
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

        if autofit:
            worksheet.autofit()


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Query SURF Research Drive API to get an overview of project folders')
    default_configfile = os.path.splitext(os.path.abspath(os.path.basename(__file__)))[0] + '.cfg'

    parser.add_argument('-c', '--config-file', default=default_configfile, help='Config file')
    parser.add_argument('-o', '--output-dir', default=None, help='Directory to put the resulting .xlsx file in')
    parser.add_argument('-l', '--log-file', default=None, help='File path to log file')
    args = parser.parse_args()

    if args.log_file is not None:
        args.log_file = os.path.abspath(args.log_file)
        rootLogger = logging.getLogger()
        logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
        fileHandler = TimedRotatingFileHandler(args.log_file,
                                               when="midnight",
                                               interval=1,
                                               backupCount=5)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

    args_txt = ''
    for key,val in vars(args).items():
        args_txt += '\t{}: {}\n'.format(key, val)

    logging.info('Starting Application to create overview of SURF Research Drive project folders with\n{}'.format(args_txt))

    config = configparser.ConfigParser()
    configfile = args.config_file
    config.read(configfile)

    institute = config['API']['environment_domain'].split('.')[0].lower()
    api_url = 'https://{}/dashboard/api/'.format(config['API']['environment_domain'])
    api_key = config['API']['key']

    ResearchDriveAPI = researchdrive.ResearchDrive(url=api_url, token=api_key)
    df = ResearchDriveAPI.get_projectfolders()

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = os.path.abspath('.')
        # os.path.join(, os.path.splitext(os.path.basename(__file__))[0])

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    logging.info('Institute: {}'.format(institute))
    if institute == 'windesheim':
        # domains are specified as comma separated list. Split and make sure they are in uppercase
        domains = config['GENERAL']['domains'].upper().split(',')
        mapping = {}
        for key in config['MAPPING']:
            mapping[key.upper()] = config['MAPPING'][key].upper().split(',')

        # derive project number
        logging.info('Adding column "project_number"')
        # project numbers are defined as 6 digit numbers starting with nonzero
        df['project_number'] = df.name.str.extract(r'(^[1-9]\d{5})')
        # derive domain, being the second element of the underscore separated name
        df['domain'] = df.name.str.extract(r'^\d{4,6}_(' + "|".join(domains) + r')_')
        logging.info('Adding column "domain"')
        # check compliance with name convention
        logging.info('Adding column "name_convention"')
        # name should start with 6 digit number, followed by underscore and domain code, followed by underscore projectname slug
        df['name_convention'] = df.name.str.contains(r'^\d{6}_(' + r'|'.join(domains) + r')_[0-9a-zA-Z-]')
        # apply mapping of project numbers to domains
        for domain, project_numbers in mapping.items():
            df.loc[df.project_number.isin(list(project_numbers)), 'domain'] = domain
        # derive whether this concerns a test folder
        logging.info('Adding column "test"')
        # a projectfolder is considered as test if it does not start with a 4-6 digit number OR if both domain and project number is not available
        df['test'] = ~df.name.str.contains(r'(^[1-9]\d{3,5})') | (pandas.isna(df.domain) & pandas.isna(df.project_number))

        sort_columns = ['domain', 'project_number', 'owner_name']
    else:
        sort_columns = ['owner_name']

    # include selected columns and show excluded columns in log
    columns = config['GENERAL']['columns'].split(',')
    excluded_columns = list(set(df.columns)-set(columns))
    if len(excluded_columns) > 0:
        logging.info('Columns excluded: {}'.format(','.join(excluded_columns)))
    df_report = df[df['status.value'] == 'active'].sort_values(sort_columns)[columns]

    # construct name of xlsx file
    date_str = datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y-%m-%d')
    xlsx_file = os.path.join(output_dir, '{}_{}_{}.xlsx'.format(os.path.splitext(os.path.basename(__file__))[0], institute, date_str))
    # write table to xlsx file
    logging.info('Writing overview of projectfolders to "{}"'.format(xlsx_file))
    excelwriter(xlsx_file, df_report, sheet_name='Sheet1', autofit=True)

if __name__ == '__main__':
    main()