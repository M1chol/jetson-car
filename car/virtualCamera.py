from car.virtualFileHandler import VirtualFileHandler

class VirtualCamera():

    def __init__(self):
        self.fileWriter = VirtualFileHandler()
        pass

    def setup(self, fileWriterFuture):
        return self
    
    def startWorker(self, executor):
        return 
    
    def stop(self):
        return
    
    def getStatus(self) -> bool:
        return True