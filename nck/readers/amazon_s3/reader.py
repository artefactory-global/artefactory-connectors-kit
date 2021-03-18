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

import boto3
from nck.readers.object_storage.reader import ObjectStorageReader


class AmazonS3Reader(ObjectStorageReader):
    def __init__(self, bucket, bucket_region, access_key_id, access_key_secret, prefix, format, dest_key_split=-1, **kwargs):
        self.boto_config = {
            "region_name": bucket_region,
            "aws_access_key_id": access_key_id,
            "aws_secret_access_key": access_key_secret,
        }
        super().__init__(bucket, prefix, format, dest_key_split, platform="S3", **kwargs)

    def create_client(self, config):

        return boto3.resource("s3", **self.boto_config)

    def create_bucket(self, client, bucket):
        return client.Bucket(bucket)

    def list_objects(self, bucket, prefix):
        return bucket.objects.filter(Prefix=prefix)

    @staticmethod
    def get_timestamp(_object):
        return _object.last_modified

    @staticmethod
    def get_key(_object):
        return _object.key

    @staticmethod
    def to_object(_object):
        return _object.Object()

    @staticmethod
    def download_object_to_file(_object, stream):
        _object.download_fileobj(stream)
