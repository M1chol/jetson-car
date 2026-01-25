from car.virtualFileHandler import VirtualFileWriter

class VirtualCamera():

    def __init__(self):
        self.fileWriter = VirtualFileWriter()
        pass

    def setup(self, fileWriterFuture):
        return self
    
    def startWorker(self, executor):
        return 
    
    def stop(self):
        return
    
    def getStatus(self) -> bool:
        return True