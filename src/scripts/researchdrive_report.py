import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import argparse
import os
import datetime
import pandas
from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QWidget, QVBoxLayout, QLabel, QFileDialog


class MainWindow(QMainWindow):
    input_dir = '../..'

    def __init__(self, input_dir='.'):
        super().__init__()

        self.input_dir = input_dir

        self.setWindowTitle('Research Drive reporting')

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        vertical_layout = QVBoxLayout()

        self.selectfile_button = QPushButton('Select .xlsx reporting file')
        self.selectfile_button.clicked.connect(self.selectfile)

        self.selectfile_label = QLabel('')

        vertical_layout.addWidget(self.selectfile_button)
        vertical_layout.addWidget(self.selectfile_label)

        self.selectdir_button = QPushButton('Select directory')
        self.selectdir_button.clicked.connect(self.selectdir)

        self.selectdir_label = QLabel('')

        vertical_layout.addWidget(self.selectdir_button)
        vertical_layout.addWidget(self.selectdir_label)

        self.button = QPushButton('Process reporting')
        self.button.clicked.connect(self.process_reporting)

        vertical_layout.addWidget(self.button)

        central_widget.setLayout(vertical_layout)

    def selectfile(self):
        fname = QFileDialog.getOpenFileName(self, 'Select file',
                                            self.input_dir, "Excel files (*.xlsx)")
        xlsx_file = fname[0]
        self.selectfile_label.setText(xlsx_file)

        # derive input directory
        self.input_dir = os.path.abspath(os.path.dirname(xlsx_file))

        date_str = datetime.datetime.fromtimestamp(os.path.getmtime(xlsx_file), tz=datetime.timezone.utc).strftime(
            '%Y-%m-%d')

        output_dir = self.selectdir_label.text()

        if output_dir == '':
            output_dir = os.path.join(self.input_dir, 'researchdrive_reporting_{}'.format(date_str))
            self.selectdir_label.setText(output_dir)

    def selectdir(self):
        dirname = QFileDialog.getExistingDirectory(self, 'Select directory', self.input_dir, QFileDialog.ShowDirsOnly)
        if dirname != '':
            self.selectdir_label.setText(dirname)

    def process_reporting(self):
        create_html_files(xlsx_file=self.selectfile_label.text(), output_dir=self.selectdir_label.text())


def create_html_files(xlsx_file, output_dir):
    # check if file exists
    if not os.path.exists(xlsx_file):
        logging.error('"{}" does not exist.'.format(xlsx_file))
        return

    # check if file extension is .xslx
    ext = os.path.splitext(xlsx_file)[-1]
    if not ext.lower() == '.xlsx':
        logging.error('Extension "{}" is not supported.'.format(xlsx_file))
        return

    # derive input directory
    input_dir = os.path.abspath(os.path.dirname(xlsx_file))

    date_str = datetime.datetime.fromtimestamp(os.path.getmtime(xlsx_file), tz=datetime.timezone.utc).strftime(
        '%Y-%m-%d')

    if output_dir is None:
        output_dir = os.path.join(input_dir, 'researchdrive_reporting_{}'.format(date_str))

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    df = pandas.read_excel(xlsx_file, header=1)
    # introduce level (0: project folder; 1: first level sub folder)
    df['level'] = df.shared_path.str.count('/') - 1
    # create column with group name
    df['Group displayname'] = df['Shared as'].str.replace('customgroup_', '')
    df.loc[df['Group displayname'].isin(['individual', 'federated_share']), 'Group displayname'] = ''
    # replace suffix of custom groups
    df.loc[df['Shared as'].str.startswith('customgroup_'), 'Shared as'] = 'group'
    # display federated ID as "Recipient displayname"
    idx = df['Shared as'] == 'federated_share'
    df.loc[idx, 'Recipient displayname'] = df[idx]['Recipient']
    # introduce domain column, displaying the domain of the Recipient
    df['Domain'] = df['Recipient'].apply(lambda s: s.split('@')[1])

    for project in pandas.unique(df.Project):
        project_idx = df.Project==project
        # get name of project folder
        project_folder = df[(project_idx) & (df.level == 0)]['shared_path'].values[0].replace('/', '').replace(
            ' (Projectfolder)', '')

        # create structured autorisation overview
        df_report = \
        df[project_idx].groupby(['level', 'shared_path', 'Permissions', 'Shared as', 'Group displayname', 'Domain'],
                                          group_keys=True)['Recipient displayname'].apply(lambda x: x).to_frame()

        # define full path of html file
        html_file = os.path.join(output_dir, '{}_{}.html'.format(project_folder, date_str))
        # write to html file
        with open(html_file, 'w') as fobj:
            fobj.write(df_report.to_html())

def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Process SURF Research Drive reporting .xlsx file to an autorisation overview')
    parser.add_argument('-f', '--file', default='SURF Reporting.xlsx', help='Filename of source .xlsx file')
    parser.add_argument('-i', '--input-dir', default=None, help='Directory to expect the source .xlsx file in')
    parser.add_argument('-o', '--output-dir', default=None, help='Directory to put the resulting .html files in')
    parser.add_argument('-g', '--gui', action='store_true', help='Use GUI')
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

    logging.info('Starting Research Drive report with\n{}'.format(args_txt))

    if args.gui:
        app = QApplication(sys.argv)

        window = MainWindow(input_dir=args.input_dir)
        window.show()

        app.exec()

    else:
        create_html_files(xlsx_file=args.file, output_dir=args.output_dir)


if __name__ == '__main__':
    main()