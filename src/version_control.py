# version_control.py

class VersionControl:
    def __init__(self):
        self.versions = []

    def add_version(self, version):
        self.versions.append(version)

    def get_latest_version(self):
        return self.versions[-1] if self.versions else None

    def list_versions(self):
        return self.versions
