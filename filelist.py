from os import walk

class FileList:

    @staticmethod
    def get(directory):
        file_names = []
        for (dp, dn, fn) in walk(directory):
            file_names.extend(fn)
            break

        file_names.sort()
        return file_names
