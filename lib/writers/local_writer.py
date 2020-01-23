import click
import logging
import os

from lib.writers.writer import Writer
from lib.commands.command import processor


@click.command(name="write_local")
@click.option("--local-directory", required=True)
@processor()
def local(**kwargs):
    return LocalWriter(**kwargs)


class LocalWriter(Writer):

    def __init__(self, local_directory):
        self._local_directory = local_directory

    def write(self, stream):
        """
            Write file to console, mainly used for debugging
        """

        path = os.path.join(self._local_directory, stream.name)

        logging.info("Writing stream %s to %s", stream.name, path)
        file = stream.as_file()
        with open(path, 'wb') as h:
            while True:
                buffer = file.read(1024)
                if len(buffer) > 0:
                    h.write(buffer)
                else:
                    break
