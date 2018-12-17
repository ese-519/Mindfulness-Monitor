import numpy as np
from scipy import signal
#from Util.peak_detection import detect_peaks
#from Util.peak_detection import _plot
rrt_signal = np.load("./Util/rrt1.npy")


def bandpass_filter(rrt_data, f1 = 0.2, f2 = 2, num_taps = 5, nyq = 50):
    filter = signal.firwin(num_taps, [f1, f2], pass_zero=False, nyq = nyq)
    data_processed = np.convolve(rrt_data, filter, mode = 'valid')
    return data_processed

def filter_rrt_signal(rrt_data, kernel_size = 4):
    rrt_data = np.convolve(rrt_data, np.ones(kernel_size) / kernel_size, mode = 'valid')
    return rrt_data

def moving_average(rrt_data, num_taps = 5):
    filter = np.ones(num_taps)/num_taps
    data_processed = np.convolve(rrt_data, filter, mode = 'valid')
    return data_processed


import matplotlib.pyplot as plt
fig = plt.figure("1")
ax1 = fig.add_subplot(311)
ax2 = fig.add_subplot(312)
ax3 = fig.add_subplot(313)
sig1 = bandpass_filter(rrt_signal, num_taps = 50)
sig2 = moving_average(sig1, num_taps = 50)
ax1.plot(rrt_signal)
ax2.plot(sig1)
ax3.plot(sig2)

plt.show()




#detect_peaks(filter_rrt_signal(rrt_signal), mpd=200 , show=False)