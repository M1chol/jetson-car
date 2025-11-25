import car.gamepad

class VirtualGamepad(car.gamepad.Gamepad):
    
    def getGamePad(self) -> bool:
        return True
    
    def updateGamepad(self) -> None:
        pass