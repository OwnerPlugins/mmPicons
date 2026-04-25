#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enigma import eTimer
import os
import ssl
from urllib.request import urlopen, Request


def _get_request_agent():
    from .Utils import RequestAgent
    return RequestAgent()


class DownloadWithProgress:
    def __init__(self, url, outputFile):
        self.url = url
        self.outputFile = outputFile
        self.userAgent = _get_request_agent()
        self.blockSize = 524288  # 512KB
        self.totalSize = 0
        self.progress = 0
        self.progressCallback = None
        self.endCallback = None
        self.errorCallback = None
        self.stopFlag = False
        self.timer = eTimer()
        self.timer.callback.append(self.reportProgress)
        self.timer.start(500, 1)

    def start(self):
        import threading
        self.thread = threading.Thread(target=self._download)
        self.thread.start()
        return self

    def _download(self):
        try:
            req = Request(self.url, headers={'User-Agent': self.userAgent})
            context = ssl._create_unverified_context()
            response = urlopen(req, timeout=30, context=context)
            self.totalSize = int(response.headers.get('Content-Length', 0))
            with open(self.outputFile, 'wb') as f:
                while not self.stopFlag:
                    chunk = response.read(self.blockSize)
                    if not chunk:
                        break
                    self.progress += len(chunk)
                    f.write(chunk)
                    if self.progressCallback:
                        self.timer.start(0, True)
            response.close()
            if self.stopFlag:
                os.unlink(self.outputFile)
                return
            if self.endCallback:
                self.endCallback(self.outputFile)
        except Exception as e:
            if self.errorCallback:
                self.errorCallback(e)

    def stop(self):
        self.stopFlag = True

    def reportProgress(self):
        if self.progressCallback:
            self.progressCallback(self.progress, self.totalSize)

    def addProgress(self, callback):
        self.progressCallback = callback

    def addEnd(self, callback):
        self.endCallback = callback

    def addError(self, callback):
        self.errorCallback = callback

    def addCallback(self, callback):
        print("[Downloader] addCallback deprecated, use addEnd")
        self.endCallback = callback
        return self

    def addErrback(self, callback):
        print("[Downloader] addErrback deprecated, use addError")
        self.errorCallback = callback
        return self


class downloadWithProgress(DownloadWithProgress):
    pass
