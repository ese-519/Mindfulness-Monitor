import spidev
import time
import os
import RPi.GPIO as GPIO

#initialize GPIO

class Haptic(object):

	def __init__(self,pin,freq,duty):
		self.pin = pin
		self.freq = freq
		self.duty = duty
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(self.pin,GPIO.OUT)
		self.pwm = GPIO.PWM(self.pin,self.freq)		

	def startPWM(self):
		self.pwm.start(self.duty)

	def stopPWM(self):
		self.pwm.stop()

	def changeFreq(self,freq):
		self.freq = freq
		self.pwm.ChangeFrequency(freq)

	def changeDuty(self,duty):
		self.duty = duty
		self.pwm.ChangeDutyCycle(duty)

	def cleanup(self):
		self.stopPWM()
		GPIO.cleanup()

def main():
	GPIO.cleanup()
#	buzzer1 = Haptic(13,1,50)
#	buzzer2 = Haptic(18,1,50)
	
#	buzzer1.startPWM()
#	buzzer2.startPWM()
#	time.sleep(2)

#	buzzer1.changeFreq(2)
#	time.sleep(2)

#	buzzer1.stopPWM()
#	buzzer2.stopPWM()	
#	buzzer1.cleanup()
#	buzzer2.cleanup()
if __name__ =="__name__":
	main()

#initialize SPI
#spi = spidev.SpiDev()
#spi.open(0,0)
#spi.max_speed_hz = 1000000

#def ReadChannel(channel):
 #   adc = spi.xfer2([1,(8 + channel)<<4,0])
  #  data = ((adc[1]&3)<<8) + adc[2]
   # return data
#delay = 1
