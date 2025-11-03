from pathlib import PurePath
from blake3 import blake3
from django.core.files.storage import FileSystemStorage
from django.forms import ValidationError


class MediaFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise (Exception("name's length is greater than max_length"))
        return name

    def _save(self, name, content):
        if self.exists(name):
            # if the file exists, do not call the superclasses _save method
            return name
        # if the file is new, DO call it
        return super(MediaFileSystemStorage, self)._save(name, content)


def compute_hash(content, chunk_size=None) -> str:
    content.seek(0)
    return blake3(content).hexdigest()


def get_filename(content, filename):
    file_ext = PurePath(filename).suffix
    file_root = compute_hash(content=content)
    # file_ext includes the dot.
    if file_root is None:
        raise ValidationError("")
    return PurePath("{0}/{1}".format(file_root[:2], file_root[2:])).with_suffix(file_ext)


def get_filename_with_hash(_hash):
    # file_ext includes the dot.
    if _hash is None:
        raise ValidationError("")
    return PurePath("{0}/{1}".format(_hash[:2], _hash[2:]))


mfs = MediaFileSystemStorage()
