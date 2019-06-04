import config

import click

from config import logging

from google.cloud import bigquery
from lib.streams.normalized_json_stream import NormalizedJSONStream
from lib.writers.writer import Writer
from lib.writers.gcs_writer import GCSWriter
from lib.commands.command import processor
from lib.utils.args import extract_args
from tenacity import retry, wait_exponential, before_sleep_log, before_log


@click.command(name="write_bq")
@click.option('--bq-dataset', help="BQ Dataset", required=True)
@click.option('--bq-table', help="BQ Table", required=True)
@click.option('--bq-bucket', help="BQ GCS Bucket", required=True)
@click.option('--bq-partition-column', help="BQ Partition Column")
@click.option('--bq-write-disposition', help="BQ Write Disposition", default="truncate", type=click.Choice(['truncate', 'append']))
@click.option('--bq-location', help="BQ Location", default="EU", type=click.Choice(['EU', 'US']))
@click.option('--bq-keep-files', help="BQ Keep GCS files", is_flag=True, default=False)
@processor
def bq(**kwargs):
    return BigQueryWriter(**extract_args('bq_', kwargs))


class BigQueryWriter(Writer):

    _client = None

    def __init__(self, dataset, table, bucket, partition_column, write_disposition, location, keep_files):

        self._client = bigquery.Client(project=config.PROJECT_ID)
        self._dataset = dataset
        self._table = table
        self._bucket = bucket
        self._partition_column = partition_column
        self._write_disposition = write_disposition
        self._location = location
        self._keep_files = keep_files

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10),
           reraise=True,
           before=before_log(config.logger, logging.INFO),
           before_sleep=before_sleep_log(config.logger, logging.INFO))
    def write(self, stream):

        normalized_stream = NormalizedJSONStream.create_from_stream(stream)

        gcs_writer = GCSWriter(self._bucket)
        gcs_uri, blob = gcs_writer.write(normalized_stream)

        table_ref = self._get_table_ref()

        load_job = self._client.load_table_from_uri(gcs_uri, table_ref, job_config=self.job_config())

        logging.info("Loading data into BigQuery %s:%s", self._dataset, self._table)
        result = load_job.result()

        assert result.state == 'DONE'

        if not self._keep_files:
            logging.info("Deleting GCS file: %s", gcs_uri)
            blob.delete()

    def _get_dataset(self):
        dataset_ref = self._client.dataset(self._dataset)
        return bigquery.Dataset(dataset_ref)

    def _get_table_ref(self):
        dataset = self._get_dataset()
        return dataset.table(self._table)

    def job_config(self):
        job_config = bigquery.LoadJobConfig()
        job_config.create_disposition = bigquery.job.CreateDisposition.CREATE_IF_NEEDED
        job_config.source_format = bigquery.job.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.autodetect = True

        if self._write_disposition == 'truncate':
            job_config.write_disposition = bigquery.job.WriteDisposition.WRITE_TRUNCATE
        elif self._write_disposition == 'append':
            job_config.write_disposition = bigquery.job.WriteDisposition.WRITE_APPEND
        else:
            raise Exception("Unknown BigQuery write disposition")

        if self._partition_column:
            job_config.time_partitioning = bigquery.table.TimePartitioning(
                bigquery.table.TimePartitioningType.DAY,
                self._partition_column
            )

        return job_config
