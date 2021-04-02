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
import unittest
from ack.streams.stream import Stream


class TestStreamBaseClassMethods(unittest.TestCase):
    def test_encode_and_decode_not_implemented(self):
        # let's build a generator
        generator = (x ** 2 for x in range(11))

        testStream = Stream("test", generator)
        with self.assertRaises(NotImplementedError):
            testStream.decode_record("")

        with self.assertRaises(NotImplementedError):
            testStream.encode_record("")

        with self.assertRaises(NotImplementedError):
            for el in testStream.readlines():
                print(el)

        with self.assertRaises(NotImplementedError):
            testStream.as_file().read()

    def test_can_iter_over(self):
        generator = (x ** 2 for x in range(11))
        testStream = Stream("test", generator)
        res = 0
        for el in testStream:
            res = el
        assert res == 10 ** 2


class TestsWithImplementedMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # let's build a generator
        cls.generator = ()

    def setUp(self) -> None:
        self.generator = (x ** 2 for x in range(11))

    class miniStream(Stream):
        extension = "polopop"
        mime_type = "application/polopop"

        @classmethod
        def decode_record(cls, record):
            return int(record)

        @classmethod
        def encode_record(cls, record) -> str:
            return str(record)

    def test_read_params(self):
        testStream = self.miniStream("test", self.generator)

        assert testStream.extension == "polopop"
        assert testStream.mime_type == "application/polopop"

    def test_can_iter_over_via_readlines(self):
        testStream = self.miniStream("test", self.generator)
        res = 0
        for el in testStream.readlines():
            res = el
        assert res == 10 ** 2

    def test_can_read_as_a_file(self):
        testStream = self.miniStream("test_file", self.generator)
        file = testStream.as_file()
        assert file.tell() == 0
        bytes_array = file.read()
        assert file.tell() > 0
        string_array = bytes_array.decode("utf-8")
        res = string_array.split("\n")
        assert int(res[10]) == 10 ** 2

    def test_can_read_as_a_file_chunked(self):
        testStream = self.miniStream("test_file_2", self.generator)
        file = testStream.as_file()
        bytes_array = b""
        assert file.tell() == 0
        buffer = file.read(1)
        bytes_array += buffer
        assert file.tell() == 1
        while len(buffer) > 0:
            buffer = file.read(1)
            bytes_array += buffer

        string_arrray = bytes_array.decode("utf-8")
        res = string_arrray.split("\n")
        assert int(res[10]) == 10 ** 2
