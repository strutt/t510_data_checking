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
#fname3 = 'test_run_11_scope_MSOB_date_1_24_2014_time_9_54_PM.lvm'
#fname2 = 'test_run_11_scope_MSOA_date_1_24_2014_time_9_54_PM.lvm'
#fname1 = 'test_run_11_scope_694_date_1_24_2014_time_9_54_PM.lvm'
#fname = 'test_run_12_scope_MSOB_date_1_25_2014_time_8_49_AM.lvm'

#fname1 = 'test_run_12_scope_MSOA_date_1_25_2014_time_8_57_AM.lvm'
#fname2 = 'test_run_12_scope_MSOB_date_1_25_2014_time_8_57_AM.lvm'
#fname3 = 'test_run_12_scope_694_date_1_25_2014_time_8_57_AM.lvm'

#test_prefix = 'test_'
test_prefix = ''
run = 16
date = '1_25_2014'
time = '1_27_PM'
#file_times = []
#file_times.append('1_42_PM')
#file_times.append('1_42_PM')
#file_times.append('1_42_PM')

#run_20_scope_MSOA_date_1_25_2014_time_1_42_PM.lvm

look_at_event = 0
attr_list = ['XZE', 'XIN', 'WFI', 'NR_P', 'YMU', 'YOF']

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
        
        #694, the bastard, requires special attention
        if self.waves[-1].num_samples == 20000:
            #temp_times = self.waves[-1].times
            #temp_volts = self.waves[-1].volts
            #temp_volts_off = self.waves[-1].volts_off
            temp_samples_off = self.waves[-1].samples_off
            #temp_samples_off = self.waves[-1].samples_off

            start = 0
            incr = 5000
            for wave in self.waves:
                #wave.times = temp_times[start:start+incr]
                #wave.volts = temp_volts[start:start+incr]
                #wave.volts_off = temp_volts_off[start:start+incr]
                wave.samples_off = temp_samples_off[start:start+incr]
                #print 'length of samples... ' + str(len(wave.samples_off))
                #wave.samples_off = temp_samples_off[start:start+incr]
                #wave.num_samples = incr
                wave.get_other()
                #wave.find_pow_spec()
                start += incr


class Wave:

    def __init__(self, raw_wave, chan):
        self.attribute_names = []
        self.attribute_values = []
        self.samples_off = []
        self.attribute_count = 0
        self.num_samples = 0
        self.channel = chan
        self.pow_spec = []
        self.pow_spec_dB = []
        self.freqs = []
        self.samp_rate = 0
        self.volts = []
        self.samples = []
        self.times = []
        self.volts_off = []

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

        hopefully_samples = self.get_raw_attribute('CURV')
        if hopefully_samples == None:
            pass
            #for i in range(2): # add some blank samples, see if this works
                #self.samples.append(0)
                #self.samples_off.append(0)
        else:
            for sample in hopefully_samples.split(','):
                if '//\r\n' in sample:
                    sample = sample.replace('//\r\n','')
                self.samples_off.append( float(sample) )
        self.num_samples = len(self.samples_off)
        #print self.num_samples

        if len(self.samples_off) > 0 and len(self.samples_off) < 20000:
            self.get_other()
            #get pow spec


    def get_other(self):

        self.num_samples = len(self.samples_off)
        # get times
        x_0 = float(self.get_raw_attribute('XZE') )
        #x_incr = float( self.get_raw_attribute('XIN') )
        x_incr = 1 #float( self.get_raw_attribute('XIN') )
        self.samp_rate = 1./x_incr
        #print self.samp_rate

        #while len( self.volts ) > 0:
        #    self.volts.pop()
        #while len( self.samples ) > 0:
        #    self.samples.pop()
        #while len( self.times ) > 0:
        #    self.times.pop()
        #while len(self.volts) > 0:
        #    self.volts_off.pop()

        y_off = float( self.get_raw_attribute('YOF') )            
        for sample in self.samples_off:
            self.samples.append( float(sample) - y_off )

        for index in range(self.num_samples):
            self.times.append((x_0 + index*x_incr))

        #get volts
        y_mult = float( self.get_raw_attribute('YMU') )
        for samp in self.samples_off:
            self.volts.append( (samp - y_off)*y_mult )
        for samp in self.samples_off:
            self.volts_off.append( samp*y_mult)

        #print 'In get others' + str(self.num_samples)
        self.find_pow_spec()

    def find_pow_spec(self):
        #get power spectra
        #print str(len(self.volts)) + '  ' + str(len(self.volts_off))
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
    def __init__(self, scopes):
        self.event_ind = 0
        self.toggle_volts = True
        self.toggle_offset = False
        self.figs = []
        self.figs2 = []
        self.figs3 = []
        
        scope_num = 0
        self.lines = []
        self.lines2 = []
        for scope in scopes:
            
            self.num_events = []
            self.num_events.append(scope.num_events)

            fig = mp.subplot(6, 2, 4*scope_num + 1)
            self.figs.append(fig)
            xlabel('Time (s)')
            ylabel('Volts (V)')

            self.num_waves = scopes[0].events[self.event_ind].num_waves
            for wave_ind in range(self.num_waves):
                y = scope.events[self.event_ind].waves[wave_ind].volts
                t = scope.events[self.event_ind].waves[wave_ind].times
                #if scope_num == 0:
                #    print 'Setup :' + str(self.event_ind) + ' ' + str(wave_ind) + ':'
                #    print 'y len ' + str(len(y))
                #    print 't len ' + str(len(t))
                line, = plot(t, y, label = 'Channel ' + str(wave_ind+1) )
                if scope_num == 0:
                    legend()
                self.lines.append(line)

            fig2 = mp.subplot(6, 2, 4*scope_num + 2)
            self.figs2.append(fig2)
            xlabel('Frequency (Hz)')
            ylabel('Power (dB)')
        
            for wave_ind in range(self.num_waves):
                p = scope.events[self.event_ind].waves[wave_ind].pow_spec_dB
                f = scope.events[self.event_ind].waves[wave_ind].freqs
                line, = plot(f, p, label = 'Channel ' + str(wave_ind+1) )
                self.lines2.append(line)
            if scope_num == 0:
                legend()

            fig3 = mp.subplot(6, 2, 4*scope_num + 3)
            self.figs3.append(fig3)
            #fig3.set_title('Event Header Information')
            axis('off')

            scope_num += 1
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
        for scope_num in range(3):
            mp.subplot(6, 2, 4*scope_num + 1)
            if self.toggle_volts == False:
                ylabel('ADC count')
            else:
                ylabel('Volts (V)')
        self.update()
        
    def next(self, event):
        self.event_ind += 1
        self.event_ind = self.event_ind % self.num_events[0]
        self.update()

    def prev(self, event):
        self.event_ind -= 1
        if self.event_ind < 0:
            self.event_ind = self.num_events[0] - 1
        self.update()

    def update(self):
        scope_num = 0
        for scope in scopes:
            max_volts = -1
            min_volts = 1
            max_pow = -10000
            min_pow = 10000
            self.event_ind = self.event_ind % self.num_events[0]

            #remove header info
            for i in range (len( self.figs3[scope_num].axes.texts )):
                self.figs3[scope_num].axes.texts.pop()

            # each wave in the current scope, current event
            for i in range ( len (scopes[scope_num].events[self.event_ind].waves) ):
                y = []
                if self.toggle_volts == True:
                    if self.toggle_offset == True:
                        y = scope.events[self.event_ind].waves[i].volts_off
                    else:
                        y = scope.events[self.event_ind].waves[i].volts
                        if i == 3:
                            print y
                else:
                    if self.toggle_offset == True:
                        y = scope.events[self.event_ind].waves[i].samples_off
                    else:
                        y = scope.events[self.event_ind].waves[i].samples
                t = scope.events[self.event_ind].waves[i].times
                max_t = max(t)
                min_t = min(t)
                #if scope_num == 0:
                    #print y
                #    print 'Channel ' + str(i) + ': '
                #    print len(t)
                #    print len(y)
                #    print 'Event ' + str(self.event_ind) + ' has ' + str(scope.events[0].num_waves)
                self.lines[scope_num*3 + i].set_ydata(y)
                self.lines[scope_num*3 + i].set_xdata(t)
                max_y = max(y)
                min_y = min(y)
                if i == 3:
                    print max(y)

                if max_y > max_volts:
                    max_volts = max_y
                if min_y < min_volts:
                    min_volts = min_y

            if min_volts > 0:
                min_volts *= 0.9
            else:
                min_volts *= 1.1

            if max_volts < 0:
                max_volts*= 0.9
            else:
                max_volts *= 1.1

            y_lims = [ min_volts, max_volts ]
            x_lims = [ min_t, max_t]
            self.figs[scope_num].set_ylim( y_lims )
            self.figs[scope_num].set_xlim( x_lims )
            self.figs[scope_num].set_title(scope_names[scope_num] + ' Waveforms - Event ' + str(self.event_ind))

            for i in range ( len (scope.events[self.event_ind].waves) ):
                p = scope.events[self.event_ind].waves[i].pow_spec_dB
                f = scope.events[self.event_ind].waves[i].freqs
                if len(p) > 1:
                    p.pop() #avoid occasional weird very low value point
                    f.pop()
                self.lines2[scope_num*3 + i].set_ydata(p)
                self.lines2[scope_num*3 + i].set_xdata(f)
                max_p = max(p)
                min_p = min(p)
                if max_p > max_pow:
                    max_pow = max_p
                if min_p < min_pow:
                    min_pow = min_p
            y_lims = [ min_pow - 1, max_pow + 1 ]
            self.figs2[scope_num].set_ylim( y_lims )
            self.figs2[scope_num].set_title(scope_names[scope_num] + ' Power Spectra - Event ' + str(self.event_ind))

            for wave in scope.events[self.event_ind].waves:
                y_coord = 0.875 - ((wave.channel - 1) * 0.25)
                wave_info = 'Channel ' + str(wave.channel) + ': '
                for attr in attr_list:
                    wave_info += attr + ' ' + wave.get_raw_attribute(attr) + ', '
                self.figs3[scope_num].text(0.05, y_coord, wave_info, fontsize=12)
            scope_num += 1
        mp.draw()

#fname1 = 'test_run_12_scope_MSOA_date_1_25_2014_time_8_57_AM.lvm'
#fname2 = 'test_run_12_scope_MSOB_date_1_25_2014_time_8_57_AM.lvm'
#fname3 = 'test_run_12_scope_694_date_1_25_2014_time_8_57_AM.lvm'
#file_name1 = dirc+fname1
#file_name2 = dirc+fname2
#file_name3 = dirc+fname3

scope_names = []
scope_names.append('694')
scope_names.append('MSOA')
scope_names.append('MSOB')

file_names = []
for i in range(3):
    file_name = dirc
    file_name += test_prefix + 'run_' + str(run) + '_scope_' + scope_names[i] + '_date_'
    file_name += date + '_time_' + time + '.lvm'
    file_names.append( file_name )
    print file_name


scopes = []
for file_name in file_names:
    scopes.append( Scope(file_name) ) #contruct data objects for this scope
t510_plots(scopes)
