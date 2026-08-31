# -*- coding: utf-8 -*-


class FileLogger(object):
    def __init__(self, prefix, path):
        self.prefix = prefix
        self.path = path

    def reset(self):
        try:
            with open(self.path, "w", encoding="utf-8") as stream:
                stream.write("")
        except Exception:
            pass

    def log(self, message):
        line = self.prefix + message
        print(line)
        try:
            with open(self.path, "a", encoding="utf-8") as stream:
                stream.write(line + "\n")
        except Exception:
            pass
