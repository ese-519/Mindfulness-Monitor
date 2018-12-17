import spidev
import time
from scipy.signal import find_peaks
from scipy import signal
import matplotlib.pyplot as plt
#from scipy.signal import
import sys
import os
import numpy as np
import pdb
#from ShareMemory.MemShare import ShareMemWriter

#add the package to the python directory
cur_path = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0 : -1])
cur_path = os.path.join(cur_path, "ShareMemory")
sys.path.append(cur_path)
#from MemShare import ShareMemWriter
import time
#from peak_detection import detect_peaks
#from peak_detection import _plot

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

    def count_peaks(data, threshold = 480):
        count = 0
        flag = False
        for i in range(len(data)):
            if data[i] > 480 and not flag:
                flag = True
                count = count + 1
            if data[i] < 480 and flag:
                flag = False
        
        return count

    def moving_average(self, data, window):

        cumsum = np.cumsum(np.insert(data, 0, 0))
        return (cumsum[window:] - cumsum[:-window]) /float(window)

    def collectData(self , length, delay, ecg_window = 1, rr_window = 40, duration_expect = 20):

        timeStart = time.time()
        time_data = []
        ecgBuffer = []
        rrBuffer1 = []
        rrBuffer2 = []
        accelBuffer = []

        for i in range(length):
            time_data.append(time)
            ecgBuffer.append(self.ReadChannel(0, self.spi))
            accelBuffer.append(self.ReadChannel(1, self.spi))
            rrBuffer1.append(self.ReadChannel(2, self.spi))
            rrBuffer2.append(self.ReadChannel(3, self.spi))
            time.sleep(delay)
            if (time.time() - timeStart > duration_expect):
                duration = duration_expect
                print("duration satisfied: ", duration)
                break
            if (i == length -1):

                duration = time.time() - timeStart
                print("duration not satisfied: ", duration)


        #rrBuffer1 = self.moving_average(np.array(rrBuffer1), rr_window)
        #rrBuffer2 = self.moving_average(np.array(rrBuffer2), rr_window)

        #rrBuffer1 = rrBuffer1.tolist()
        #rrBuffer2 = rrBuffer2.tolist()
        return (ecgBuffer, accelBuffer, rrBuffer1, rrBuffer2, duration)

class DataProcessor:

    def __init__(self, duration, num_taps_bp = 50, num_taps_ma = 50):
        self.num_taps_bp = num_taps_bp
        self.num_taps_ma = num_taps_ma
        self.duration = duration
        self.buffer = None
        self.peaks = None
        self.BPM = None

    def bandpass_filter(self, rrt_data, f1=0.2, f2=2, num_taps_bp=5, nyq=50):
        filter = signal.firwin(num_taps_bp, [f1, f2], pass_zero=False, nyq=nyq)
        data_processed = np.convolve(rrt_data, filter, mode='valid')
        return data_processed

    def moving_average(self, rrt_data, num_taps_ma=5):
        filter = np.ones(num_taps_ma) / num_taps_ma
        data_processed = np.convolve(rrt_data, filter, mode='valid')
        return data_processed

    def find_num_peaks(self, x, mph=None, mpd=1, threshold=0, edge='rising',
                     kpsh=False, valley=False, show=False, ax=None, rr_sig = False):

        """Detect peaks in data based on their amplitude and other features.

        Parameters
        ----------
        x : 1D array_like
            data.
        mph : {None, number}, optional (default = None)
            detect peaks that are greater than minimum peak height (if parameter
            `valley` is False) or peaks that are smaller than maximum peak height
             (if parameter `valley` is True).
        mpd : positive integer, optional (default = 1)
            detect peaks that are at least separated by minimum peak distance (in
            number of data).
        threshold : positive number, optional (default = 0)
            detect peaks (valleys) that are greater (smaller) than `threshold`
            in relation to their immediate neighbors.
        edge : {None, 'rising', 'falling', 'both'}, optional (default = 'rising')
            for a flat peak, keep only the rising edge ('rising'), only the
            falling edge ('falling'), both edges ('both'), or don't detect a
            flat peak (None).
        kpsh : bool, optional (default = False)
            keep peaks with same height even if they are closer than `mpd`.
        valley : bool, optional (default = False)
            if True (1), detect valleys (local minima) instead of peaks.
        show : bool, optional (default = False)
            if True (1), plot data in matplotlib figure.
        ax : a matplotlib.axes.Axes instance, optional (default = None).

        Returns
        -------
        ind : 1D array_like
            indeces of the peaks in `x`.

        Notes
        -----
        The detection of valleys instead of peaks is performed internally by simply
        negating the data: `ind_valleys = detect_peaks(-x)`

        The function can handle NaN's

        See this IPython Notebook [1]_.

        References
        ----------
        .. [1] http://nbviewer.ipython.org/github/demotu/BMC/blob/master/notebooks/DetectPeaks.ipynb

        Version history
        ---------------
        '1.0.5':
            The sign of `mph` is inverted if parameter `valley` is True

        """
        if rr_sig:
            x = self.bandpass_filter(x, num_taps_bp= self.num_taps_bp)
            x = self.moving_average(x, num_taps_ma = self.num_taps_ma)
        x = np.atleast_1d(x).astype('float64')
        if x.size < 3:
            return np.array([], dtype=int)
        if valley:
            x = -x
            if mph is not None:
                mph = -mph
        # find indices of all peaks
        dx = x[1:] - x[:-1]
        # handle NaN's
        indnan = np.where(np.isnan(x))[0]
        if indnan.size:
            x[indnan] = np.inf
            dx[np.where(np.isnan(dx))[0]] = np.inf
        ine, ire, ife = np.array([[], [], []], dtype=int)
        if not edge:
            ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
        else:
            if edge.lower() in ['rising', 'both']:
                ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
            if edge.lower() in ['falling', 'both']:
                ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
        ind = np.unique(np.hstack((ine, ire, ife)))
        # handle NaN's
        if ind.size and indnan.size:
            # NaN's and values close to NaN's cannot be peaks
            ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == x.size - 1:
            ind = ind[:-1]
        # remove peaks < minimum peak height
        if ind.size and mph is not None:
            ind = ind[x[ind] >= mph]
        # remove peaks - neighbors < threshold
        if ind.size and threshold > 0:
            dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
            ind = np.delete(ind, np.where(dx < threshold)[0])
        # detect small peaks closer than minimum peak distance
        if ind.size and mpd > 1:
            ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if kpsh is True
                    idel = idel | (ind >= ind[i] - mpd) & (ind <= ind[i] + mpd) \
                           & (x[ind[i]] > x[ind] if kpsh else True)
                    idel[i] = 0  # Keep current peak
            # remove the small peaks and sort back the indices by their occurrence
            ind = np.sort(ind[~idel])
        '''
        if show:
            if indnan.size:
                x[indnan] = np.nan
            if valley:
                x = -x
                if mph is not None:
                    mph = -mph
            _plot(x, mph, mpd, threshold, edge, valley, ax, ind)
        '''

        self.peaks = ind
        return ind



    def count_peaks(self, data, threshold = 400):
        count = 0
        flag = False
        for i in range(len(data)):
            if data[i] > threshold and not flag:
                flag = True
                count = count + 1
            if data[i] < threshold and flag:
                flag = False
        self.peaks = np.arange(count)

    def findPeaks(self, dataBuffer, height = 0, threshold = 0, distance = 1):

        peaks, _ = find_peaks(dataBuffer, height = height, threshold = threshold, distance = distance)
        self.peaks = peaks
        return peaks


    def calcBPM(self):

        BPM = len(self.peaks) / self.duration
        self.BPM = BPM
        return self.BPM


def main():
    fig = plt.figure("1")
    ax1 = fig.add_subplot(311)
    ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(313)
    dr = DataReader()
    dr.initADC(1000000)
    data = []
    print("start")
    tic = time.time()
    for i in range(1):
        ecg,accel,rr1,rr2,duration = dr.collectData(6000,0.01)
        print(len(data))
        print(len(rr1))
        data.extend(rr1)
        dp_ecg = DataProcessor(duration)
        dp_accel = DataProcessor(duration)
        dp_rr1 = DataProcessor(duration)
        dp_rr2 = DataProcessor(duration)

        ecgPeaks = dp_ecg.findPeaks(ecg,0)
        accelPeaks = dp_accel.findPeaks(accel,0)
        #rr1Peaks = dp_rr1.findPeaks(rr1,0, distance = 50)
        rr1Peaks = dp_rr1.count_peaks(rr1)
        rr2Peaks = dp_rr2.findPeaks(rr2,0)

        agitation = dp_accel.calcBPM()
        ecgRate = dp_ecg.calcBPM()
        rr1Rate = dp_rr1.calcBPM()
        rr2Rate = dp_rr2.calcBPM()
        print(ecgRate,agitation,rr1Rate,rr2Rate)
    data = np.array(data)
    np.save("rrt1", data)
   # window = signal.general_gaussian(51, p = 0.5, sig = 20)
   # filtered = signal.fftconvolve(window, data)
   # filtered = np.average(data) /np.average(filtered) * filtered
   # filtered = np.roll(filtered, -25)
    #peaks2 = find_peaks(filtered)
   # print(data)
    data_fft = np.abs(np.fft.fft(data))
    print(data_fft)
    numtaps = 3
    f = 0.1
    fil = signal.firwin(numtaps, f)
    data3 = np.convolve(data, fil, 'same') 
    toc = time.time()
    print("time", toc - tic)
   # print(data_fft)
   # data_fft[3:] = 0
    #smoothed = np.fft.irfft(data_fft)
    #print(np.arange(data.shape[0]))
    #pdb.set_trace()
    ax1.plot(np.arange(data.shape[0]),data, 'r')
    ax2.plot(100 /np.arange(data_fft.shape[0]), data_fft)
    ax3.plot(data3)
    plt.show()
if __name__ =="__main__":
    main()


