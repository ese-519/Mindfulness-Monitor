#import spidev
import time
import sys
import os
import sqlalchemy
import pdb
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float

#from ShareMemory.MemShare import ShareMemWriter

#add the package to the python directory
cur_path = os.path.dirname(os.path.abspath(__file__))
cur_path = os.path.join(cur_path, "ShareMemory")
sys.path.append(cur_path)
from MemShare import ShareMemWriter
from sqlalchemy import create_engine




class DataReader:

    def __init__(self):

        self.spi = spidev.SpiDev()

    def initADC(self, freq):
        self.spi.open(0, 0)
        self.spi.max_speed_hz = freq

    def ReadChannel(self, channel, spi):
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        return data

    def collectData(self , length, delay):

        timeStart = time.time()

        ecgBuffer = []
        rrBuffer1 = []
        rrBuffer2 = []
        accelBuffer = []

        for i in range(length):
            ecgBuffer.append(self.ReadChannel(0, self.spi))
            accelBuffer.append(self.ReadChannel(1, self.spi))
            rrBuffer1.append(self.ReadChannel(2, self.spi))
            rrBuffer2.append(self.ReadChannel(3, self.spi))
            time.sleep(delay)
        duration = time.time() - timeStart
        return (ecgBuffer, accelBuffer, rrBuffer1, rrBuffer2, duration)

def main():
    Base = declarative_base()

    class User(Base):
        __tablename__ = 'user'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        time = Column(Float)
        ECG = Column(Integer)
        RR = Column(Integer)
        Accel = Column(Float)

        def __repr__(self):
            return "<User(name = '%s', time = '%f', ECG = '%d', RR = '%d', Accel = '%f'>" % (
            self.name, self.time, self.ECG, self.RR, self.Accel)

    print(sqlalchemy.__version__)
    print(User.__table__)
    Base.metadata.create_all(engine)
    pdb.set_trace()
    return 0

if __name__ == "__main__":
    main()
