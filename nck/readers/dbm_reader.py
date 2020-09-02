# GNU Lesser General Public License v3.0 only
# Copyright (C) 2020 Artefact
# licence-information@artefact.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import click
import logging
import httplib2

import requests
import datetime

from googleapiclient import discovery
from oauth2client import client, GOOGLE_REVOKE_URI
from tenacity import retry, wait_exponential, stop_after_delay
from click import ClickException

from nck.commands.command import processor
from nck.readers.reader import Reader
from nck.utils.args import extract_args
from nck.streams.format_date_stream import FormatDateStream

from nck.utils.text import get_generator_dict_from_str_csv

from nck.helpers.dbm_helper import POSSIBLE_REQUEST_TYPES

DISCOVERY_URI = "https://analyticsreporting.googleapis.com/$discovery/rest"

default_start_date = datetime.date.today() - datetime.timedelta(days=2)
default_end_date = datetime.date.today()


@click.command(name="read_dbm")
@click.option("--dbm-access-token", default=None)
@click.option("--dbm-refresh-token", required=True)
@click.option("--dbm-client-id", required=True)
@click.option("--dbm-client-secret", required=True)
@click.option("--dbm-query-metric", multiple=True)
@click.option("--dbm-query-dimension", multiple=True)
@click.option("--dbm-request-type", type=click.Choice(POSSIBLE_REQUEST_TYPES), required=True)
@click.option("--dbm-query-id")
@click.option("--dbm-query-title")
@click.option("--dbm-query-frequency", default="ONE_TIME")
@click.option("--dbm-query-param-type", default="TYPE_TRUEVIEW")
@click.option("--dbm-start-date", type=click.DateTime())
@click.option("--dbm-end-date", type=click.DateTime())
@click.option(
    "--dbm-add-date-to-report",
    type=click.BOOL,
    default=False,
    help=(
        "Sometimes the date range on which metrics are computed is missing from the report. "
        "If this option is set to True, this range will be added."
    ),
)
@click.option("--dbm-filter", type=click.Tuple([str, str]), multiple=True)
@click.option("--dbm-file-type", multiple=True)
@click.option(
    "--dbm-date-format",
    default="%Y-%m-%d",
    help="And optional date format for the output stream. "
    "Follow the syntax of https://docs.python.org/3.8/library/datetime.html#strftime-strptime-behavior",
)
@click.option(
    "--dbm-day-range",
    required=True,
    default="LAST_7_DAYS",
    type=click.Choice(
        ["PREVIOUS_DAY", "LAST_30_DAYS", "LAST_90_DAYS", "LAST_7_DAYS", "PREVIOUS_MONTH", "PREVIOUS_WEEK"]
    ),
)
@processor("dbm_access_token", "dbm_refresh_token", "dbm_client_secret")
def dbm(**kwargs):
    # Should add validation argument in function of request_type
    return DbmReader(**extract_args("dbm_", kwargs))


class DbmReader(Reader):
    API_NAME = "doubleclickbidmanager"
    API_VERSION = "v1.1"

    def __init__(self, access_token, refresh_token, client_secret, client_id, **kwargs):
        credentials = client.GoogleCredentials(
            access_token,
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=refresh_token,
            token_expiry=None,
            token_uri="https://accounts.google.com/o/oauth2/token",
            user_agent=None,
            revoke_uri=GOOGLE_REVOKE_URI,
        )

        http = credentials.authorize(httplib2.Http())
        credentials.refresh(http)

        self._client = discovery.build(self.API_NAME, self.API_VERSION, http=http, cache_discovery=False)

        self.kwargs = kwargs

    def get_query(self, query_id):
        if query_id:
            return self._client.queries().getquery(queryId=query_id).execute()
        else:
            raise ClickException("Please provide a 'query_id' in order to find your query")

    def get_existing_query(self):
        query_id = self.kwargs.get("query_id", None)
        query = self.get_query(query_id)
        if query:
            return query
        else:
            raise ClickException(f"No query found with the id {query_id}")

    def get_query_body(self):
        body_q = {
            "metadata": {
                "format": "CSV",
                "title": self.kwargs.get("query_title", "NO_TITLE_GIVEN"),
                "dataRange": self.kwargs.get("day_range", "LAST_7_DAYS"),
            },
            "params": {
                "type": self.kwargs.get("query_param_type", "TYPE_TRUEVIEW"),
                "groupBys": self.kwargs.get("query_dimension"),
                "metrics": self.kwargs.get("query_metric"),
                "filters": [{"type": filt[0], "value": str(filt[1])} for filt in self.kwargs.get("filter")],
            },
            "schedule": {"frequency": self.kwargs.get("query_frequency", "ONE_TIME")},
        }
        if self.kwargs.get("start_date") is not None and self.kwargs.get("end_date") is not None:
            body_q["metadata"]["dataRange"] = "CUSTOM_DATES"
            body_q["reportDataStartTimeMs"] = 1000 * int(
                (self.kwargs.get("start_date") + datetime.timedelta(days=1)).timestamp()
            )
            body_q["reportDataEndTimeMs"] = 1000 * int(
                (self.kwargs.get("end_date") + datetime.timedelta(days=1)).timestamp()
            )
        return body_q

    def create_and_get_query(self):
        body_query = self.get_query_body()
        query = self._client.queries().createquery(body=body_query).execute()
        return query

    @retry(wait=wait_exponential(multiplier=1, min=60, max=3600), stop=stop_after_delay(36000))
    def _wait_for_query(self, query_id):
        logging.info("waiting for query of id : {} to complete running".format(query_id))
        query_infos = self.get_query(query_id)
        if query_infos["metadata"]["running"] or (
            "googleCloudStoragePathForLatestReport" not in query_infos["metadata"]
            and "googleDrivePathForLatestReport" not in query_infos["metadata"]
        ):
            raise Exception("Query still running.")
        else:
            return query_infos

    def get_query_report_url(self, existing_query=True):
        if existing_query:
            query_infos = self.get_existing_query()
        else:
            query_infos = self.create_and_get_query()
            query_id = query_infos["queryId"]
            query_infos = self._wait_for_query(query_id)

        if (
            "googleCloudStoragePathForLatestReport" in query_infos["metadata"]
            and len(query_infos["metadata"]["googleCloudStoragePathForLatestReport"]) > 0
        ):
            url = query_infos["metadata"]["googleCloudStoragePathForLatestReport"]
        else:
            url = query_infos["metadata"]["googleDrivePathForLatestReport"]

        return url

    def get_query_report(self, existing_query=True):
        url = self.get_query_report_url(existing_query)
        report = requests.get(url, stream=True)
        if self.kwargs["query_param_type"] == "TYPE_REACH_AND_FREQUENCY" and self.kwargs["add_date_to_report"]:
            return get_generator_dict_from_str_csv(
                report.iter_lines(),
                add_date=True,
                day_range=self.kwargs["day_range"],
                date_format=self.kwargs.get("date_format"),
            )
        else:
            return get_generator_dict_from_str_csv(report.iter_lines())

    def list_query_reports(self):
        reports_infos = self._client.reports().listreports(queryId=self.kwargs.get("query_id")).execute()
        for report in reports_infos["reports"]:
            yield report

    def get_lineitems_body(self):
        if len(self.kwargs.get("filter")) > 0:
            filter_types = [filt[0] for filt in self.kwargs.get("filter")]
            assert (
                len([filter_types[0] == filt for filt in filter_types if filter_types[0] == filt]) == 1
            ), "Lineitems accept just one filter type, multiple filter types detected"
            filter_ids = [str(filt[1]) for filt in self.kwargs.get("filter")]

            return {"filterType": filter_types[0], "filterIds": filter_ids, "format": "CSV", "fileSpec": "EWF"}
        else:
            return {}

    def get_lineitems_objects(self):
        body_lineitems = self.get_lineitems_body()
        response = self._client.lineitems().downloadlineitems(body=body_lineitems).execute()
        lineitems = response["lineItems"]
        lines = lineitems.split("\n")
        return get_generator_dict_from_str_csv(lines)

    def read(self):
        request_type = self.kwargs.get("request_type")
        if request_type == "existing_query":
            data = [self.get_existing_query()]
        elif request_type == "custom_query":
            data = [self.create_and_get_query()]
        elif request_type == "existing_query_report":
            data = self.get_query_report(existing_query=True)
        elif request_type == "custom_query_report":
            data = self.get_query_report(existing_query=False)
        elif request_type == "list_reports":
            data = self.list_query_reports()
        elif request_type == "lineitems_objects":
            data = self.get_lineitems_objects()

        def result_generator():
            for record in data:
                yield record

        # should replace results later by a good identifier
        yield FormatDateStream("results", result_generator(), keys=["Date"], date_format=self.kwargs.get("date_format"))
