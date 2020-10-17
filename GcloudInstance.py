from googleapiclient import discovery
from google.cloud import storage
import os
import time
import pickle
from config import ZONE, PROJECT_NAME, VM_NAME
from pathlib import Path


class GcloudInstance:

    def __init__(self, service_name: str, version: str, credentials_path: str, bucket_name: str):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        self._storage_client = storage.Client()
        self.compute = discovery.build(service_name, version)  # Google API resource object
        self.operation = None
        self.project = None
        self.zone = None
        self.name = None
        self.bucket = self._storage_client.bucket(bucket_name)
        self.bucket_name = bucket_name

    def get_existing_instance(self, project=PROJECT_NAME, zone=ZONE, name=VM_NAME):
        self.project = project
        self.zone = zone
        self.name = name
        self.operation = self.compute.instances().get(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def status(self):
        if self.operation is None:
            return "Object has no current operation/instance."
        return self.operation['status']

    def _wait_for_operation(self) -> object:

        while self.operation is not None:
            result = self.compute.zoneOperations().get(
                project=self.project,
                zone=self.zone,
                operation=self.operation).execute()

            if result['status'] == 'DONE':
                if 'error' in result:
                    raise Exception(result['error'])
                return result

            time.sleep(1)

    def delete_instance(self) -> None:
        return self.compute.instances().delete(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def stop_instance(self):
        return self.compute.instances().stop(
            project=self.project,
            zone=self.zone,
            instance=self.name).execute()

    def start_instance(self):
        if self.operation is not None and self.status() != 'RUNNING':
            self.compute.instances().start(
                project=self.project,
                zone=self.zone,
                instance=self.name).execute()

    def upload_file(self, data=None, to_pickle=False, source_filename=None):
        """
        Uploads a picklable file to the gcloud bucket attached to this object
        :param source_filename: name of the file to be uploaded
        :param to_pickle: boolean indicator, default is False
        :param data: Any data to be uploaded
        :return: int code 1 for success, -1 for failure
        """

        try:
            if source_filename is None:
                source_filename = 'tmp_input/input_data.pkl'
            if to_pickle and data is not None:
                with open(source_filename, 'wb') as f:
                    pickle.dump(data, f)
            dest_and_src_path = str(Path('tmp_input', source_filename))

            blob = self.bucket.blob(dest_and_src_path)

            blob.upload_from_filename(dest_and_src_path)
            return 1
        except Exception as e:
            print(e)
            return -1

    def upload_dir(self, rootdir: str):
        paths = [str(path) for path in Path(rootdir).rglob('*') if '.gitignore' not in path.stem]
        for path in paths:
            self.upload_file(source_filename=path.split('/')[-1])

    def download_from_bucket(self, dest_file_name: str, source_blob_name: str):
        try:
            blob = self.bucket.blob(source_blob_name)
            blob.download_to_filename(dest_file_name)
            return 1
        except Exception as e:
            print(e)
            return -1

    def list_bucket_objects(self) -> [str]:
        return list(self._storage_client.list_blobs(self.bucket_name))
