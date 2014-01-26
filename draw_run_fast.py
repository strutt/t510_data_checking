from pylab import *
import matplotlib.pyplot as mp
from matplotlib.widgets import Button
import numpy

dirc='/Users/benstrutt/Dropbox/data/'
#fname = 'test_run_7_scope_694_date_1_24_2014_time_12_49_PM.lvm'
#fname = 'test_run_7_scope_MSOA_date_1_24_2014_time_12_49_PM.lvm'
#fname = 'test_run_10_scope_MSOB_date_1_24_2014_time_2_32_PM.lvm'
#fname = 'test_run_10_scope_MSOB_date_1_24_2014_time_1_33_PM.lvm'
#fname = 'test_run_10_scope_MSOB_date_1_24_2014_time_1_33_PM.lvm'
#fname = 'test_run_11_scope_694_date_1_24_2014_time_8_21_PM.lvm'
#fname = 'test_run_11_scope_MSOB_date_1_24_2014_time_9_54_PM.lvm'
#fname = 'test_run_11_scope_MSOA_date_1_24_2014_time_9_54_PM.lvm'
#fname = 'test_run_11_scope_694_date_1_24_2014_time_9_54_PM.lvm'
#fname = 'test_run_12_scope_MSOB_date_1_25_2014_time_8_49_AM.lvm'

#fname = 'test_run_16_scope_MSOB_date_1_25_2014_time_12_35_PM.lvm'
#fname = 'run_7_scope_694_date_1_25_2014_time_12_54_PM.lvm'
#fname = 'run_8_scope_MSOB_date_1_25_2014_time_12_57_PM.lvm'
#fname = 'run_9_scope_MSOB_date_1_25_2014_time_12_59_PM.lvm'


test = ''
#test = 'test_'
run_num = 15
scope_name = 'MSOA'
date = '1_25_2014'
time = '1_25_PM'

fname = test + 'run_' + str(run_num) + '_scope_' + scope_name + '_date_' + date + '_time_' + time + '.lvm'
#fname = 'test_run_18_scope_' + scope_name + '_date_1_25_2014_time_1_04_PM.lvm'

#fname = 'run_34_scope_MSOB_date_1_25_2014_time_4_09_PM.lvm'

look_at_event = 0
attr_list = ['XZE', 'XIN', 'PT_O', 'WFI', 'NR_P', 'YMU', 'YOF']

class Scope:
    def __init__(self, file_name):
        self.file_names = []
        self.events = []
        self.raw_events = [] #for raw strings
        self.num_events = 0
        self.get_data(file_name)
        self.event_index = 0
        self.lines  = []#not really lines...

    def get_data(self, file_name):
        self.file_names.append(file_name)
        for line in file(file_name):
            if line[0:5] == ';:WFM' or line[0:4] == ':WFM':
                raw_event = line
                self.events.append( Event(raw_event, self.num_events) )
                self.num_events += 1
            #elif line[0:6] == '//2014':
                #print line
        print str(self.num_events) + ' found!'

class Event:
    def __init__(self, raw_event, event_num):
        self.waves = []
        self.num_waves = 0
        self.event_number = event_num
#        print raw_event
        raw_waves = raw_event.split(':WFM')
        raw_waves.pop(0) # split string is at beginning so first element is blank string
        for raw_wave in raw_waves:
            #print self.num_waves
            #print raw_wave
            self.num_waves += 1
            self.waves.append( Wave(raw_wave, self.num_waves) )

class Wave:

    def __init__(self, raw_wave, chan):
        self.attribute_names = []
        self.attribute_values = []
        self.samples = []
        self.samples_off = []
        self.times = []
        self.volts = []
        self.volts_off = []
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

        #print self.attribute_names

        # get raw adc counts and subtract y_offset

        y_off = float( self.get_raw_attribute('YOF') )            
        hopefully_samples = self.get_raw_attribute('CURV')
        if hopefully_samples == None:
            for i in range(2): # add some blank samples, see if this works
                self.samples.append(0)
                self.samples_off.append(0)
        else:
            for sample in hopefully_samples.split(','):
                if '//\r\n' in sample:
                    sample = sample.replace('//\r\n','')
                self.samples.append( float(sample) - y_off )
                self.samples_off.append( float(sample) )
        self.num_samples = len(self.samples)

        # get times
        #x_0 = float(self.get_raw_attribute('XZE') )
        #print x_0
        x_0 = 300 * self.channel
        #x_incr = float( self.get_raw_attribute('XIN') )
        x_incr = 1
        self.samp_rate = 1./x_incr
        #print self.samp_rate
        for index in range(self.num_samples):
            self.times.append((x_0 + index*x_incr))

        #get volts
        y_mult = float( self.get_raw_attribute('YMU') )
        for samp in self.samples:
            self.volts.append( samp*y_mult )
        for samp in self.samples_off:
            self.volts_off.append( samp*y_mult)

        #get power spectra
        #self.pow_spec, self.freqs = psd(self.volts, Fs = self.samp_rate)
        ft = numpy.fft.rfft(self.volts)
        self.pow_spec = abs( ft )**2
        for i in range( len( self.pow_spec ) ):
            self.freqs.append( i*self.samp_rate/self.num_samples )
        for index in range( len(self.pow_spec) ):
            val = self.pow_spec[index]
            if val == 0 :
                self.pow_spec_dB.append(0)
            else:
                self.pow_spec_dB.append( 10*np.log10(val) )

    # lookup function for raw attributes from header file
    def get_raw_attribute(self, search_string):
        for attribute_index in range(self.attribute_count):
            if search_string in self.attribute_names[attribute_index]:
                return self.attribute_values[attribute_index]

# now we plot things
# lets keep all plotting data types out here for now
# and update them with information from my data classes

class t510_plots:
    def __init__(self, scope):
        self.num_events = scope.num_events
        self.event_ind = 0
        self.toggle_volts = True
        self.toggle_offset = False

        self.fig = mp.subplot(2, 2, 1)
        xlabel('Time (s)')
        ylabel('Volts (V)')

        self.num_waves = scope.events[self.event_ind].num_waves
        self.lines = []
        for wave_ind in range(self.num_waves):
            y = scope.events[self.event_ind].waves[wave_ind].volts
            t = scope.events[self.event_ind].waves[wave_ind].times
            line, = plot(t, y, label = 'Channel ' + str(wave_ind+1) )
            legend()
            self.lines.append(line)

        self.fig2 = mp.subplot(2, 2, 2)
        xlabel('Frequency (Hz)')
        ylabel('Power (dB)')
        self.lines2 = []
        
        for wave_ind in range(self.num_waves):
            p = scope.events[self.event_ind].waves[wave_ind].pow_spec_dB
            f = scope.events[self.event_ind].waves[wave_ind].freqs
            line, = plot(f, p, label = 'Channel ' + str(wave_ind+1) )
            self.lines2.append(line)
            legend()

        self.fig3 = mp.subplot(2, 2, 3)
        self.fig3.set_title(scope_name + ' Event Header Information')
        axis('off')
        self.info = []

        self.update()

        self.axprev = mp.axes([0.7, 0.05, 0.1, 0.075])
        self.axnext = mp.axes([0.81, 0.05, 0.1, 0.075])
        self.axvolt = mp.axes([0.1, 0.05, 0.1, 0.075])
        self.axoff = mp.axes([0.19, 0.05, 0.1, 0.075])

        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.next)

        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.prev)

        self.bvolts = Button(self.axvolt, 'Volts/ADC')
        self.bvolts.on_clicked(self.volts_toggle)

        self.bvoff = Button(self.axoff, 'Offset')
        self.bvoff.on_clicked(self.offset_toggle)

        mp.show()

    def offset_toggle(self, event):
        self.toggle_offset = not self.toggle_offset
        self.update()

    def volts_toggle(self, event):
        self.toggle_volts = not self.toggle_volts
        mp.subplot(2,2,1)
        if self.toggle_volts == False:
            ylabel('ADC count')
        else:
            ylabel('Volts (V)')
        self.update()
        
    def next(self, event):
        self.event_ind += 1
        self.event_ind = self.event_ind % self.num_events
        self.update()

    def prev(self, event):
        self.event_ind -= 1
        if self.event_ind < 0:
            self.event_ind = self.num_events - 1
        self.update()

    def update(self):
        self.event_ind = self.event_ind % self.num_events
        max_volts = -10000
        min_volts = 10000
        max_pow = -10000
        min_pow = 10000

        #for i in self.fig3.axes.texts:
        #    self.fig3.axes.texts.remove(i)
        for i in range (len( self.fig3.axes.texts )):
            self.fig3.axes.texts.pop()

        for i in range ( len (scope.events[self.event_ind].waves) ):
            y = []
            if self.toggle_volts == True:
                if self.toggle_offset == True:
                    y = scope.events[self.event_ind].waves[i].volts_off
                else:
                    y = scope.events[self.event_ind].waves[i].volts
            else:
                if self.toggle_offset == True:
                    y = scope.events[self.event_ind].waves[i].samples_off
                else:
                    y = scope.events[self.event_ind].waves[i].samples
            t = scope.events[self.event_ind].waves[i].times
            self.lines[i].set_ydata(y)
            self.lines[i].set_xdata(t)
            #print 'Event ' + str(self.event_ind) + ', Channel ' + str(i) + ' has ' + str(len(y)) + ' points'
            max_y = max(y)
            min_y = min(y)
            if max_y > max_volts:
                max_volts = max_y
            if min_y < min_volts:
                min_volts = min_y
        y_lims = [ min_volts*1.5, max_volts*1.5 ]
        self.fig.set_ylim( y_lims )
        self.fig.set_title(scope_name + ': ' + test + 'run ' + str(run_num) + ' Waveforms - Event ' + str(self.event_ind))

        for i in range ( len (scope.events[self.event_ind].waves) ):
            p = scope.events[self.event_ind].waves[i].pow_spec_dB
            f = scope.events[self.event_ind].waves[i].freqs
            if len(p) > 1:
                p.pop() #avoid occasional weird very low value point
                f.pop()
            self.lines2[i].set_ydata(p)
            self.lines2[i].set_xdata(f)
            max_p = max(p)
            min_p = min(p)
            if max_p > max_pow:
                max_pow = max_p
            if min_p < min_pow:
                min_pow = min_p
        y_lims = [ min_pow - 1, max_pow + 1 ]
        self.fig2.set_ylim( y_lims )
        self.fig2.set_title(scope_name + ': ' + test + 'run ' + str(run_num) + ' Spectra - Event ' + str(self.event_ind))

        for wave in scope.events[self.event_ind].waves:
            y_coord = 0.875 - ((wave.channel - 1) * 0.25)
            wave_info = 'Channel ' + str(wave.channel) + ': '
            for attr in attr_list:
                wave_info += attr + ' ' + wave.get_raw_attribute(attr) + ', '
            self.fig3.text(0.05, y_coord, wave_info, fontsize=12)

        mp.draw()



file_name = dirc+fname
scope = Scope(file_name) #contruct data objects for this scope
t510_plots(scope)


class Index:
    ind = 0
    def next(self, event):
        self.ind += 1
        i = self.ind % len(freqs)
        ydata = np.sin(2*np.pi*freqs[i]*t)
        l.set_ydata(ydata)
        mp.draw()

    def prev(self, event):
        self.ind -= 1
        i = self.ind % len(freqs)
        ydata = np.sin(2*np.pi*freqs[i]*t)
        l.set_ydata(ydata)
        mp.draw()

