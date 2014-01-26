from pylab import *
import matplotlib.pyplot as mp
from matplotlib.widgets import Button
import math

dirc='/Users/benstrutt/Dropbox/data/'
#fname = 'test_run_7_scope_694_date_1_24_2014_time_12_49_PM.lvm'
fname = 'test_run_7_scope_MSOA_date_1_24_2014_time_12_49_PM.lvm'
look_at_event = 100

class Run:
    def __init__(self, file_name):
        self.file_names = []
        self.events = []
        self.raw_events = [] #for raw strings
        self.num_events = 0
        self.get_data(file_name)
        self.event_index = 0

    def get_data(self, file_name):
        self.file_names.append(file_name)
        for line in file(file_name):
            if line[0:11] == ';:WFMOUTPRE' or line[0:10] == ':WFMOUTPRE' or line[0:8] == ':WFMPRE:' or line[0:6] == ':WFMO:':
                raw_event = line
                self.events.append( Event(raw_event, self.num_events) )
                self.num_events += 1
            #elif line[0:6] == '//2014':
                #print line

    def plot_events(self, event_ind):
        clf()
        #close()
        self.event_index = event_ind
        self.events[self.event_index].plot_waves_volts()
        self.axprev = mp.axes([0.7, 0.05, 0.1, 0.075])
        self.axnext = mp.axes([0.81, 0.05, 0.1, 0.075])
        self.bnext = Button(self.axnext, 'next')
        self.bnext.on_clicked(self.next)
        self.bprev = Button(self.axprev, 'prev')
        self.bprev.on_clicked(self.prev)

    def next(self, event):
        self.event_index += 1
        if self.event_index == self.num_events:
            self.event_index = 0
        self.plot_events(self.event_index)

    def prev(self, event):
        if self.event_index == 0:
            self.event_index = self.num_events - 1
        else:
            self.event_index -= 1
        self.plot_events(self.event_index)


class Event:
    def __init__(self, raw_event, event_num):
        self.waves = []
        self.num_waves = 0
        self.event_number = event_num
#        print raw_event
        raw_waves = raw_event.split(':WFMOUTPRE:')
        raw_waves.pop(0) # split string is at beginning so first element is blank string
        for raw_wave in raw_waves:
            #print self.num_waves
            #print raw_wave
            self.num_waves += 1
            self.waves.append( Wave(raw_wave, self.num_waves) )

    def plot_waves_volts(self):
        mp.subplot(2, 2, 1)
        for wave in self.waves:
            wave.plot_wave_volts()
            title('Event ' + str(self.event_number) + ' waveform')
            legend()
        mp.subplot(2, 2, 2)
        for wave in self.waves:
            wave.plot_pow_spec_dB()
            title('Event ' + str(self.event_number) + ' power spectrum')
            legend()
        event_info = mp.subplot(2, 2, 3)
        event_info.set_title('Event Header Information')
        event_info.axis('off')
        attr_list = ['WFID', 'NR_PT', 'YMULT', 'YOFF']
        for wave in self.waves:
            y_coord = 0.875 - ((wave.channel - 1) * 0.25)
            wave_info = 'Channel ' + str(wave.channel) + ': '
            for attr in attr_list:
                wave_info += attr + ' ' + wave.get_raw_attribute(attr) + ', '
            event_info.text(0.05, y_coord, wave_info, fontsize=12)
        #text(2, 6, r'an equation: $E=mc^2$', fontsize=15)
    
class Wave:

    def __init__(self, raw_wave, chan):
        self.attribute_names = []
        self.attribute_values = []
        self.samples = []
        self.times = []
        self.volts = []
        self.attribute_count = 0
        self.num_samples = 0
        self.channel = chan
        self.pow_spec = []
        self.pow_spec_dB = []
        self.freqs = []
        self.samp_rate = 0

        # get attributes
        attributes = raw_wave.split(';')
        for attribute in attributes:
            attribute_parts = attribute.split(' ', 1)
            if len(attribute_parts) == 2: #there may be some blank fields, this should ignore them
                self.attribute_names.append(attribute_parts[0])
                self.attribute_values.append(attribute_parts[1])
                self.attribute_count += 1

        # get raw adc counts and subtract y_offset
        y_off = float( self.get_raw_attribute('YOFF') )
        for sample in self.get_raw_attribute('CURV').split(','):
            if '//\r\n' in sample:
                sample = sample.replace('//\r\n','')
            self.samples.append( float(sample) - y_off )
        self.num_samples = len(self.samples)

        # get times
        x_0 = float( self.get_raw_attribute('XZERO') )
        x_incr = float( self.get_raw_attribute('XINCR') )
        self.samp_rate = 1./x_incr
        #print self.samp_rate
        for index in range(self.num_samples):
            self.times.append((x_0 + index*x_incr))

        #get volts
        y_mult = float( self.get_raw_attribute('YMULT') )
        for samp in self.samples:
            self.volts.append( samp*y_mult )

        #get power spectra
        self.pow_spec, self.freqs = psd(self.volts, Fs = self.samp_rate)
        for index in range( len(self.pow_spec) ):
            val = self.pow_spec[index]
            if val == 0 :
                self.pow_spec_dB.append(0)
            else:
                self.pow_spec_dB.append( math.log10(val) )
            #for index in range( len(self.freqs) ):
            #self.freqs[index] *= 1e-6 #convert to MHz
            

    # lookup function for raw attributes from header file
    def get_raw_attribute(self, search_string):
        for attribute_index in range(self.attribute_count):
            if search_string in self.attribute_names[attribute_index]:
                return self.attribute_values[attribute_index]

    # plotting function
    def plot_wave_volts(self):
        my_label = 'Channel ' + str(self.channel)
        plot(self.times, self.volts, label=my_label)
        xlabel('Time (s)')
        ylabel('Volts (V)')

    def plot_pow_spec_dB(self):
        my_label = 'Channel ' + str(self.channel)
        plot(self.freqs, self.pow_spec_dB, label=my_label)
        xlabel('Frequency (Hz)')
        ylabel('Power Spectrum (dB)')
        

file_name = dirc+fname
this_run = Run(file_name) #contruct data objects for this run
this_run.plot_events(look_at_event)
#print this_run.events[10].num_events
#print this_run.events[10].get_raw_attribute('')
print this_run.events[10].waves[0].attribute_names
#print this_run.events[5].waves[0].attribute_names
print this_run.events[10].waves[0].get_raw_attribute('YMULT')


show() #show pylib plots

