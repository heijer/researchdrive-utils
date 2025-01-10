import logging
from logging.handlers import TimedRotatingFileHandler
import argparse
import sys
from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton, QMessageBox, QHBoxLayout, QWidget, QVBoxLayout,\
    QLineEdit, QLabel, QComboBox
import re
import os
import configparser
from researchdrive import ResearchDrive


class MainWindow(QMainWindow):
    config = None
    projectfolder_name = None
    dry_run_txt = ''
    privileges_txt = ''
    privileges = True

    def __init__(self, config=None):
        super().__init__()
        self.config = config

        api_url = 'https://{}/dashboard/api/'.format(config['API']['environment_domain'])
        api_key  = config['API']['key']
        self.RD_API = ResearchDrive(url=api_url, token=api_key)

        contracts_df = self.RD_API.get_contracts()
        if contracts_df.empty:
            logging.warning('Research Drive user has no privileges to create project folders')
            self.privileges = False
            self.privileges_txt = '(insufficient privileges)'

        if 'dry_run' in config['API']:
            self.RD_API.dry_run = config['API']['dry_run'] == 'True'
            if self.RD_API.dry_run:
                logging.info('Research Drive API is called in DRY-RUN mode')
                self.dry_run_txt = '(dry run)'

        self.setWindowTitle(config['GENERAL']['title'])

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        vertical_layout = QVBoxLayout()

        # NAME
        name_layout = self.create_name_layout()
        vertical_layout.addLayout(name_layout)

        # PROJECT_OWNER
        project_owner_layout = self.create_project_owner_layout()
        vertical_layout.addLayout(project_owner_layout)

        # DESCRIPTION
        description_layout = self.create_description_layout()
        vertical_layout.addLayout(description_layout)

        # CONTRACT
        contract_layout = self.create_contract_layout()
        vertical_layout.addLayout(contract_layout)

        # QUOTUM
        quotum_layout = self.create_quotum_layout()
        vertical_layout.addLayout(quotum_layout)

        # button
        button_layout = self.create_button_layout()
        vertical_layout.addLayout(button_layout)

        central_widget.setLayout(vertical_layout)

    def create_name_layout(self):
        horizontal_layout = QHBoxLayout()

        name_label = QLabel(self.config['NAME']['label'])
        self.name_widget = QLineEdit()
        self.name_widget.textChanged.connect(self.name_changed)

        horizontal_layout.addWidget(name_label)
        horizontal_layout.addWidget(self.name_widget)

        return horizontal_layout

    def create_project_owner_layout(self):
        horizontal_layout = QHBoxLayout()

        me_df = self.RD_API.get_me()
        accounts_df = self.RD_API.get_accounts()
        project_owner_usernames = []
        if 'items' in self.config['PROJECT_OWNER']:
            project_owner_usernames = [item for item in self.config['PROJECT_OWNER']['items'].split(',') if item in accounts_df.username.values.tolist()]
        if len(project_owner_usernames) == 0:
            project_owner_usernames = me_df.username.values.tolist()
        self.owner_df = accounts_df[accounts_df.username.isin(project_owner_usernames)]
        project_owner_items = [self.owner_df[self.owner_df['username']==username]['name'].values[0] for username in project_owner_usernames]

        project_owner_label = QLabel(self.config['PROJECT_OWNER']['label'])
        self.project_owner_widget = QComboBox()
        self.project_owner_widget.addItems(project_owner_items)

        horizontal_layout.addWidget(project_owner_label)
        horizontal_layout.addWidget(self.project_owner_widget)

        return horizontal_layout

    def create_description_layout(self):
        horizontal_layout = QHBoxLayout()

        description_label = QLabel(self.config['DESCRIPTION']['label'])
        self.description_widget = QLineEdit()

        horizontal_layout.addWidget(description_label)
        horizontal_layout.addWidget(self.description_widget)

        return horizontal_layout

    def create_contract_layout(self):
        horizontal_layout = QHBoxLayout()

        contract_label = QLabel(self.config['CONTRACT']['label'])
        self.contract_widget = QComboBox()
        if not self.privileges:
            contract_items = ['No privileges']
        else:
            contracts_df = self.RD_API.get_contracts()
            contract_items = []
            if 'items' in self.config['CONTRACT']:
                contract_items = [item for item in self.config['CONTRACT']['items'].split(',') if item in contracts_df.contract_id.values.tolist()]
            if len(contract_items) == 0:
                contract_items = contracts_df.contract_id.values.tolist()
        self.contract_widget.addItems(contract_items)

        horizontal_layout.addWidget(contract_label)
        horizontal_layout.addWidget(self.contract_widget)

        return horizontal_layout

    def create_quotum_layout(self):
        horizontal_layout = QHBoxLayout()

        quotum_label = QLabel(self.config['QUOTUM']['label'])
        self.quotum_widget = QComboBox()
        quotum_items = self.config['QUOTUM']['items'].split(',')
        self.quotum_widget.addItems(quotum_items)

        horizontal_layout.addWidget(quotum_label)
        horizontal_layout.addWidget(self.quotum_widget)

        return horizontal_layout

    def create_button_layout(self):
        horizontal_layout = QHBoxLayout()

        self.create_button = QPushButton()
        self.create_button.setText('Create projectfolder {} {}'.format(self.dry_run_txt, self.privileges_txt))
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self.create_button_clicked)

        horizontal_layout.addWidget(self.create_button)

        return horizontal_layout

    def name_changed(self):
        lst = []
        elements_count = 0
        if len(self.name_widget.text()) > 0:
            elements_count += 1
            # strip any leading characters
            project_name = re.sub(r'^\W+', '', self.name_widget.text())
            # strip any trailing characters
            project_name = re.sub(r'\W+$', '', project_name)
            # replace any spaces of non-accepted characters with hyphens
            project_name = re.sub(r'(?<=\w)\W+(?=\w)', '-', project_name)
            lst.append(project_name)
        self.projectfolder_name = "_".join(lst)
        self.create_button.setText('Create projectfolder "{}" {} {}'.format(self.projectfolder_name, self.dry_run_txt, self.privileges_txt))
        if elements_count == 1 and self.privileges:
            self.create_button.setEnabled(True)
        else:
            self.create_button.setEnabled(False)

    def create_button_clicked(self, s):

        dlg = QMessageBox(self)
        dlg.setWindowTitle("Create folder?")

        projectfolders_df = self.RD_API.get_projectfolders()
        if self.projectfolder_name in projectfolders_df.name.values:
            create = False
            dlg.setText('Project folder with name "{}" already exists'.format(self.projectfolder_name))
        else:
            create = True
            dlg.setText("Create projectfolder\nName: {}\nOwner: {}\nContract: {}\nQuotum: {}".format(self.projectfolder_name,
                                                                                         self.project_owner_widget.currentText(),
                                                                                         self.contract_widget.currentText(),
                                                                                         self.quotum_widget.currentText()))
        dlg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        button = dlg.exec()

        if button == QMessageBox.Ok:
            if create:
                quotum = int(self.quotum_widget.currentText().split(' ')[0])
                reponse = self.RD_API.create_folder(name=self.projectfolder_name,
                                          description=self.description_widget.text().strip(),
                                          owner={'name': self.project_owner_widget.currentText()},
                                          contract={'contract_id': self.contract_widget.currentText()},
                                          quotum=quotum)
                logging.info(reponse)


class MainWindowWindesheim(MainWindow):

    def __init__(self, config=None):
        super().__init__(config=config)

    def create_name_layout(self):
        horizontal_layout = QHBoxLayout()

        project_number_label = QLabel("Project number")
        self.project_number_widget = QLineEdit("")
        self.project_number_widget.textChanged.connect(self.name_changed)

        domain_label = QLabel("Domain")
        self.domain_widget = QComboBox()
        domain_default = ''
        domain_items = [domain_default] + [s.strip() for s in self.config['NAME']['domain_items'].split(',')]
        if 'domain_default' in self.config['NAME']:
            domain_default = self.config['NAME']['domain_default'].strip()
            if domain_default in domain_items:
                domain_items.remove(domain_default)
                domain_items[0] = domain_default

        self.domain_widget.addItems(domain_items)
        self.domain_widget.currentTextChanged.connect(self.name_changed)

        name_label = QLabel(self.config['NAME']['label'])
        self.name_widget = QLineEdit()
        self.name_widget.textChanged.connect(self.name_changed)

        horizontal_layout.addWidget(project_number_label)
        horizontal_layout.addWidget(self.project_number_widget)
        horizontal_layout.addWidget(domain_label)
        horizontal_layout.addWidget(self.domain_widget)
        horizontal_layout.addWidget(name_label)
        horizontal_layout.addWidget(self.name_widget)

        return horizontal_layout

    def name_changed(self):
        lst = []
        elements_count = 0
        if len(self.project_number_widget.text()) > 0:
            n = re.sub(r'\D+', '', self.project_number_widget.text())
            if len(n) > 0:
                elements_count += 1
                lst.append('{:06d}'.format(int(n)))
        if len(self.domain_widget.currentText()) > 0:
            elements_count += 1
            lst.append(self.domain_widget.currentText())
        if len(self.name_widget.text()) > 0:
            elements_count += 1
            # strip any leading characters
            project_name = re.sub(r'^\W+', '', self.name_widget.text())
            # strip any trailing characters
            project_name = re.sub(r'\W+$', '', project_name)
            # replace any spaces of non-accepted characters with hyphens
            project_name = re.sub(r'(?<=\w)\W+(?=\w)', '-', project_name)
            lst.append(project_name)
        self.projectfolder_name = "_".join(lst)
        self.create_button.setText('Create projectfolder "{}" {} {}'.format(self.projectfolder_name, self.dry_run_txt, self.privileges_txt))
        if elements_count == 3 and self.privileges:
            self.create_button.setEnabled(True)
        else:
            self.create_button.setEnabled(False)


def main():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    parser = argparse.ArgumentParser(
        description='Application to create project folder in SURF Research Drive API')
    application_dir = os.path.dirname(os.path.abspath(os.path.basename(__file__)))
    default_configfile = os.path.join(application_dir, os.path.splitext(os.path.basename(__file__))[0] + '.cfg')

    parser.add_argument('-c', '--config-file', default=default_configfile, help='Config file')
    parser.add_argument('-l', '--log-file', default=None, help='File path to log file')
    args = parser.parse_args()

    config = configparser.ConfigParser()
    configfile = args.config_file
    config.read(configfile)

    institute = config['API']['environment_domain'].split('.')[0].lower()

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

    logging.info('Starting Application to create SURF Research Drive project folder with\n{}'.format(args_txt))

    app = QApplication(sys.argv)


    if institute == 'windesheim':
        window = MainWindowWindesheim(config=config)
    else:
        window = MainWindow(config=config)

    window.show()

    app.exec()


if __name__ == '__main__':
    main()
