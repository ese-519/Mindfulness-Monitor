from hapticFeedback import Haptic
import pdb
import numpy as np

from Util.signalProcess import DataReader
from Util.signalProcess import DataProcessor
import os
import time
import sys

import matplotlib.pyplot as plt
 
#add the package to the python directory
#cur_path = "/".join(os.path.dirname(os.path.abspath(__file__)).split("/")[0 : -1])
cur_path = os.path.dirname(os.path.abspath(__file__))
cur_path = os.path.join(cur_path, "ShareMemory")
sys.path.append(cur_path)
from MemShare import ShareMemReader
from MemShare import ShareMemWriter

from visualFeedback import visualFeedback
from visualFeedback import fade

class monitor(object):

    def __init__(self,prevState,currState,prevECG,prevACCEL,prevRR1,prevRR2,currECG,currACCEL,currRR1,currRR2):

        self.prevState = prevState
        self.currState = currState
        self.prevECG = prevECG
        self.prevACCEL = prevACCEL
        self.prevRR = (prevRR1 + prevRR2)/2
        self.currECG = currECG
        self.currACCEL = currACCEL
        self.currRR = (currRR1 + currRR2)/2
    

    def updateOldVals(self):
    
        self.prevECG = self.currECG
        self.prevACCEL = self.currACCEL
        self.prevRR = self.currRR

    def updateVals(self,ecg,accel,rr1,rr2):

        #self.prevECG = self.currECG
        #self.prevACCEL = self.currACCEL
        #self.prevRR = self.currRR
        self.currECG = ecg
        self.currACCEL = accel
        self.currRR = (rr1+rr2)/2

    def updateState(self,state):
        self.prevState = self.currState
        self.currState = state

    def checkProgression(self):
        self.ecgDT = (self.currECG - self.prevECG)/(self.prevECG + 0.0001)
        print(self.currECG, self.prevECG, self.ecgDT)
        self.accelDT = (self.currACCEL - self.prevACCEL)/(self.prevACCEL + 0.0001) #avoid division 0
        self.rrDT = (self.currRR - self.prevRR)/(self.prevRR + 0.0001)


class Patient_monitor(monitor):

    def __init__(self, prevState, currState, prevECG, prevACCEL, prevRR1, prevRR2, currECG, currACCEL, currRR1, currRR2, fhandle, path, analysisPeriod = 3000, samplingDelay = 0.01):

        super().__init__(prevState, currState, prevECG, prevACCEL, prevRR1, prevRR2, currECG, currACCEL, currRR1, currRR2)
        self.buzzer1 = Haptic(12, 1, 50)
        self.buzzer2 = Haptic(13, 1, 50)
        self.share_mem_read_datastream= ShareMemWriter(fhandle, path, int_size = 4)
        self.dr = DataReader()
        # set monitor parameters
        self.analysisPeriod = analysisPeriod  # roughly corresponds to 60 seconds worth of data
        self.samplingDelay = samplingDelay  # seconds between adc readings, to avoid noise and get clean peaks
        self.baseline_ecg = 0
        self.baseline_rr = 0
        self.baseline_accel = 0

        self.target_ecg = 0
        self.target_rr = 0
        self.target_accel = 0

        self.ecg_beat = []
        self.rr_beat = []
        #self.GUI = visualFeedback(480, 320, "", "")

        self.timer = 0

        self.calibrate()

    def calibrate(self):
        # initialize adc

        self.dr.initADC(1000000)
        # initialize haptic feedback
        self.buzzer1.stopPWM()
        self.buzzer2.stopPWM()

        #calibrate share memory
        self.share_mem_read_datastream.calibrate()


    def update_baseline(self):
        #update the baseline value from the current state value
        self.baseline_ecg = self.currECG
        self.baseline_accel = self.currACCEL
        self.baseline_rr = self.currRR

    def warm_up(self, time_warmup):

        while self.currState == -1:
            print("Warming up...")
            time.sleep(time_warmup)
            # increment state to baseline collection
            self.transport_data()
            self.updateState(0)
            # wait for button press, mouseclick, etc.#####################################################################
            # collect baseline data, state 0


    def collect_baseline(self):
        
        print("Collecting baseline data for {period} seconds.".format(period=self.analysisPeriod * self.samplingDelay))
        while self.currState == 0:
            ecg, accel, rr1, rr2, duration = self.dr.collectData(self.analysisPeriod, self.samplingDelay, duration_expect = self.analysisPeriod * self.samplingDelay)
            ecgRate, agitation, rr1Rate, rr2Rate = calcRates(ecg, accel, rr1, rr2, duration)
            ecg = np.array([ecg])
            ecg = 1000 - ecg
            ecg = ecg.tolist()
            #		patient.ECG,patient.ACCEL,patient.RR1,patient.RR2 = calcRates(ecg,accel,rr1,rr2,duration):w
            #		rrAvg = (rr1Rate + rr2Rate)/2
            # check for movement toward next state 0-10% decrease ecg,rr,accel
            self.updateVals(ecgRate, agitation, rr1Rate, rr2Rate)
            self.transport_data()
            self.updateOldVals()
            #update the base line
            self.update_baseline()
            # initialize the haptic feedback to match the baseline BPM
            self.buzzer1.startPWM()
            self.buzzer2.startPWM()
            self.buzzer1.changeFreq(ecgRate)
            self.buzzer2.changeFreq(ecgRate)

            # increment to next state
            self.updateState(1)

        print("Baseline data collected. ECG = {ecg}, Agitation={agitation}, Respiratory ={respiratory}".format(
            ecg=self.currECG, agitation=self.currACCEL, respiratory=self.currRR))


    def updateTarget(self, state):
        if state == 1:
            self.target_ecg = self.prevECG * (1 - 0.05)
            self.target_rr = self.prevRR * (1 - 0.05)


        elif state == 2:

            self.target_ecg = self.prevECG * (1 - 0.1)
            self.target_rr = self.prevRR * (1 - 0.1)

        elif state == 3:

            self.target_ecg = self.prevECG * (1 + 0.05)
            self.target_rr = self.prevRR * (1 + 0.05)

        elif state == 4:

            self.target_ecg = self.prevECG * (1 - 0.05)
            self.target_rr = self.prevRR * (1 - 0.05)

        elif state == 5:

            self.target_ecg = self.prevECG * (1 + 0.05)
            self.target_rr = self.prevRR * (1 + 0.05)

    def updateScreen(self):
        fade(self.GUI, self.currState, 2, self.currECG, self.target_ecg, "10")
    
    def updateBeats(self):
        self.buzzer1.changeFreq(self.currECG)
        self.buzzer2.changeFreq(self.currECG)

    def transport_data(self):
        #print("start data transport")
        data = np.array([self.currState, self.currECG, self.target_ecg, self.timer])
        self.share_mem_read_datastream.write_data_header()
        self.share_mem_read_datastream.write_data(data)

    def checkECG(self, state):

        bReturn = False

        if state == 1:
            if (self.ecgDT < -0.01 and self.ecgDT >= -0.2) or (self.rrDT < -0.01 and self.rrDT >= -0.2):
                bReturn = True

        elif state == 2:
            if self.ecgDT < -0.1 or self.rrDT <= -0.1:
                bReturn = True

        elif state == 3:

            if (self.ecgDT > 0.01 and self.ecgDT <= 0.2) or (self.rrDT > 0.01 and self.rrDT <= 0.2):

                bReturn = True

        elif state == 4:

            if (self.ecgDT < -0.01 and self.ecgDT >= -0.2)  or (self.rrDT < -0.01 and self.rrDT >= -0.2):

                bReturn = True

        elif state == 5:

            if (self.ecgDT > 0.01 and self.ecgDT <= 0.2) or (self.rrDT > 0.01 and self.rrDT <= 0.2):

                bReturn = True

        return bReturn


    def alter_states(self, cur_state, next_state, time_min = 1):
        print("Now entering state {currState}. Meditate toward state {nextState}".format(currState=self.currState,
                                                                                         nextState=next_state))
        time_start = time.time()
        self.updateTarget(cur_state)
        flag = False
        t = 0

        if self.currState == cur_state:

            while True:
                
                ecg, accel, rr1, rr2, duration = self.dr.collectData(self.analysisPeriod, self.samplingDelay, duration_expect = self.analysisPeriod * self.samplingDelay)
                #print(rr1)
                #print(rr2)
                ecg = 1000 - np.array(ecg)
                ecg = ecg.tolist()
                ecgRate, agitation, rr1Rate, rr2Rate = calcRates(ecg, accel, rr1, rr2, duration)
                print("current data value")
                print(ecgRate, agitation, rr1Rate, rr2Rate)

                if (t == 0):
                   # print("first time update")
                    self.updateOldVals()
                self.updateVals(ecgRate, agitation, rr1Rate, rr2Rate)
                self.updateBeats()
                self.ecg_beat.append(self.currECG)
                self.rr_beat.append(self.currRR)
                self.transport_data()
                #self.updateScreen()

                #put in the visual changes
                
                self.checkProgression()
                # check for progression to Pre-meditation routine
                print("change of data wrt baseline")
                print(self.ecgDT, self.accelDT, self.rrDT)

                if self.checkECG(cur_state):

                    #print(t)
                    #print("check satisified")
                    if (t != 0):
                       # print("update the prev value satisfy")
                        self.updateOldVals()

                    
                    print("Proceeding to next routine, waiting for current interval to finish")
                    self.updateState(next_state)
                    #self.buzzer1.cleanup()
                    self.update_baseline()
                    #do something with the visual
                    flag = True

                else:
                    #print the current status
                    print("state transition not satisfied")
                    print(self.currState)
                    #print(self.ecgDT, self.accelDT, self.rrDT)
                t = t + 1
                if (time.time() - time_start) > time_min * 60:
                    
                    if flag:

                        break

                    else:
                        #reset the timer
                        time_start = time.time()
                else:
                    self.timer_val = time_min * 60 - (time.time() - time_start) 

        else:
            print("wrong state")

    def output_data(self):
        return (self.ecg_beat, self.rr_beat)
        #np.save("ECG_data", np.array(self.ecg_beat))
        #np.save("Resp_data", np.array(self.rr_beat))



def calcRates(ecg,accel,rr1,rr2,duration):

    dp_ecg = DataProcessor(duration)
    dp_accel = DataProcessor(duration)
    dp_rr1 = DataProcessor(duration)
    dp_rr2 = DataProcessor(duration)

    ecgPeaks = dp_ecg.find_num_peaks(ecg, mph = 100, mpd=50,show=False, rr_sig = False)
    accelPeaks = dp_accel.findPeaks(accel, 0)
    rr1Peaks = dp_rr1.find_num_peaks(rr1, mph =None, mpd=300,show=False, rr_sig = True)
    rr2Peaks = dp_rr2.find_num_peaks(rr2, mph =None, mpd=300,show=False, rr_sig = True)
    #rr1Peaks = dp_rr1.findPeaks(rr1)
    #rr2Peaks = dp_rr2.findPeaks(rr2)
    #print("rr1peaks", rr1Peaks)
    #print("rr2peaks", rr2Peaks)
    agitation = dp_accel.calcBPM()
    ecgRate = dp_ecg.calcBPM()
    rr1Rate = dp_rr1.calcBPM()
    rr2Rate = dp_rr2.calcBPM()

    return (ecgRate,agitation,rr1Rate,rr2Rate)

def plot(data_ecg, data_resp, idx):
    fig = plt.figure("Data ")
    ax1 = fig.add_subplot(211)
    ax2 = fig.add_subplot(212)
    ax1.plot(data_ecg)
    ax2.plot(data_resp)    
    name = "data_" + str(idx) + ".jpg"
    plt.savefig(name)

def do_it(cur_path):
    with open(cur_path, "r+", encoding="UTF-8") as fshare:
	
        patient = Patient_monitor(-1,-1,0,0,0,0,0,0,0,0, fshare, cur_path, analysisPeriod = 1000)
        patient.warm_up(10)
       

        patient.collect_baseline()
        ecg_data, resp_data = patient.output_data()
        plot(ecg_data, resp_data, 0)
         
        for i in range(1, 6):
            patient.alter_states(i, i + 1, time_min = 0.3)
            ecg_data, resp_data = patient.output_data()
            plot(ecg_data, resp_data, i)
              
        return patient.output_data()
	
def main():

    #global prevColor
    #global nextColor
    #prevColor = (255, 255, 255)
    #nextColor = (255, 255, 255)

    #initialize the monitor
    #cur_dir = "/".join(os.getcwd().split("/")[0: -1])
    cur_dir = os.getcwd()
    cur_path = os.path.join(cur_dir, "memorymap", "data_visual.txt")

    ecg_data, resp_data = do_it(cur_path)
    print("data saved")
    np.save("ECG_data", ecg_data)
    np.save("Resp_data", resp_data)
    #plot(ecg_data, resp_data)

if __name__ == "__main__" :
    main()
