import gspread
from google.oauth2 import service_account
from nck.utils.args import extract_args
from nck.commands.command import processor
from nck.readers.reader import Reader
from google.auth.transport.requests import AuthorizedSession
import click
from nck.streams.normalized_json_stream import NormalizedJSONStream


@click.command(name="read_gs")
@click.option("--gs-project-id", default=None, required=True)
@click.option("--gs-private-key-id", required=True)
@click.option("--gs-private-key-path", required=True)
@click.option("--gs-client-email", required=True)
@click.option("--gs-client-id", required=True)
@click.option("--gs-client-cert", required=True)
@click.option("--gs-sheet-name", default=None, required=True)
@processor("gs_private_key_id", "gs_private_key_path", "gs_client_id", "gs_client_cert")
def google_sheets(**kwargs):
    return GSheetsReader(**extract_args("gs_", kwargs))


class GSheetsReader(Reader):
    _scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/spreadsheets',
               "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    def __init__(
            self,
            project_id: str,
            private_key_id: str,
            private_key_path: str,
            client_email: str,
            client_id: str,
            client_cert: str,
            sheet_name: str):
        self._sheet_name = sheet_name
        private_key_txt = open(private_key_path, 'r').read().replace("\\n", "\n")
        self._keyfile_dict = {
            'type': 'service_account',
            'project_id': project_id,
            'private_key_id': private_key_id,
            'private_key': private_key_txt,
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'client_email': client_email,
            'client_id': client_id,
            'client_x509_cert_url': client_cert,
            'token_uri': 'https://accounts.google.com/o/oauth2/token',
        }
        self._credentials = service_account.Credentials.from_service_account_info(info=self._keyfile_dict)
        self._scoped_credentials = self._credentials.with_scopes(
            ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
        )
        gc = gspread.Client(auth=self._scoped_credentials)
        gc.session = AuthorizedSession(self._scoped_credentials)

    def read(self):
        gc = gspread.Client(auth=self._scoped_credentials)
        gc.session = AuthorizedSession(self._scoped_credentials)
        sheet = gc.open(self._sheet_name).sheet1
        list_of_hashes = sheet.get_all_records()

        def result_generator():
            for record in list_of_hashes:
                yield record

        yield NormalizedJSONStream(sheet, result_generator())
