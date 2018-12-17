import spidev
import time
from scipy.signal import find_peaks



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

    def collectData(self, length, delay):

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

class DataProcessor:

    def __init__(self, duration):
        self.duration = duration
        self.buffer = None
        self.peaks = None
        self.BPM = None

    def findPeaks(self, dataBuffer, height):

        peaks, _ = find_peaks(dataBuffer, height = height)
        self.peaks = peaks
        return peaks


    def calcBPM(self):

        BPM = len(self.peaks) / self.duration
        self.BPM = BPM
        return self.BPM


def main():

    dr = DataReader()
    dr.initADC(1000000)

    ecg,accel,rr1,rr2,duration = dr.collectData(60,0.1)
    dp_ecg = DataProcessor(duration)
    dp_accel = DataProcessor(duration)
    dp_rr1 = DataProcessor(duration)
    dp_rr2 = DataProcessor(duration)

    ecgPeaks = dp_ecg.find_num_Peaks(ecg,0)
    accelPeaks = dp_accel.findPeaks(accel,0)
    rr1Peaks = dp_rr1.find_num_Peaks(rr1,0)
    rr2Peaks = dp_rr2.findPeaks(rr2,0)

    agitation = dp_accel.calcBPM()
    ecgRate = dp_ecg.calcBPM()
    rr1Rate = rr1Peaks.calcBPM()
    rr2Rate = rr2Peaks.calcBPM()
    print(ecgRate,agitation,rr1Rate,rr2Rate)

if __name__ =="__name__":
    main()


