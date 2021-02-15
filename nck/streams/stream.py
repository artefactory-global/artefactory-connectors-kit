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
from datetime import datetime
import time
import io


class Stream(object):
    _name = None
    _source_generator = None

    extension = None
    mime_type = "application/octet-stream"

    def __init__(self, name, source_generator):
        """
            _source_generator is a generator yielding dicts
        """
        self._name = self.create_stream_name(name)
        self._source_generator = source_generator
        self._iterator = iter(source_generator)

    def __len__(self):
        return self._source_generator.__len__()

    def __iter__(self):
        """
            The raw stream object can also be iterated.
            You'll get the raw elements yielded by the generator.
        """
        return self._iterator

    def as_file(self) -> io.BufferedReader:
        return self._iterable_to_stream(self._iterator, self.encode_record_as_bytes)

    def readlines(self):
        """
            Yield each element of a the generator, one by one.
            (ex: line by line for file)
        """
        for record in self:
            yield self.decode_record(self.encode_record(record))

    @classmethod
    def create_from_stream(cls, source_stream):
        if isinstance(source_stream, cls):
            return source_stream

        return cls(source_stream.name, source_stream.readlines())

    @classmethod
    def encode_record_as_bytes(cls, record) -> bytes:
        return (cls.encode_record(record) + "\n").encode("utf-8")

    @classmethod
    def encode_record(cls, record) -> str:
        raise NotImplementedError

    @classmethod
    def decode_record(cls, record):
        raise NotImplementedError

    @staticmethod
    def create_stream_name(name):
        ts = time.time()
        ts_as_string = datetime.fromtimestamp(ts).strftime("%Y-%m-%d-%H-%M-%S")
        return f"{name}_{ts_as_string}"

    @property
    def name(self):
        return ".".join(filter(None, [self._name, self.extension]))

    @staticmethod
    def _iterable_to_stream(iterable, encode, buffer_size=io.DEFAULT_BUFFER_SIZE):
        """
        Credit goes to 'Mechanical snail'
            at https://stackoverflow.com/questions/6657820/python-convert-an-iterable-to-a-stream

        Lets you use an iterable (e.g. a generator) that yields bytestrings as a
        read-only
        input stream.

        The stream implements Python 3's newer I/O API (available in Python 2's io
        module).
        For efficiency, the stream is buffered.
        """

        class IterStream(io.RawIOBase):
            def __init__(self):
                self.leftover = None
                self.count = 0

            def readable(self):
                return True

            def readinto(self, b):
                try:
                    chunck_length = len(b)  # We're supposed to return at most this much
                    chunk = self.leftover or encode(next(iterable))
                    output, self.leftover = chunk[:chunck_length], chunk[chunck_length:]
                    b[: len(output)] = output
                    self.count += len(output)
                    return len(output)
                except StopIteration:
                    return 0  # indicate EOF

            # tell should be implemented for GCS
            def tell(self):
                return self.count

        return io.BufferedReader(IterStream(), buffer_size=buffer_size)
