from pylab import *
import matplotlib.pyplot as mp
from matplotlib.widgets import Button
import numpy
import glob
import sys
#from scipy.stats.stats import pearsonr
#import scipy

def main():
    dirc='/Users/benstrutt/Dropbox/data/'
    test_prefix = ''
    run = sys.argv[1]
    if len(sys.argv) > 2:
        test_prefix = 'test_'

    look_at_event = 0
    attr_list = ['XZE', 'XIN', 'NR_P', 'YMU', 'YOF']

    scope_names = []
    scope_names.append('694')
    scope_names.append('MSOA')
    scope_names.append('MSOB')

    file_names = []
    for i in range(3):
        file_name = dirc
        file_name += test_prefix + 'run_' + str(run) + '_scope_' + scope_names[i] + '*.lvm'
        file_names.append(glob.glob(file_name)[-1])
    #    print file_name

    #contruct data objects for scopes from files
    scopes = []
    for file_name in file_names:
        scopes.append( Scope(file_name) ) 

    #start event viewer
    #Event_Viewer(scopes, run, scope_names, test_prefix, attr_list) 

    #start time stamp viewer
    #t = Time_Stamp_Viewer(scopes, run, scope_names, test_prefix)
    #t.plot_time_stamps()

    #start peak correlator
    p = Peak_Correlator(scopes, run, test_prefix)
    p.draw_self_plots()
    #p.correlate()

    MSOAs = []
    MSOBs = []
    TDS694s = []
    scope_MSOAs = []
    scope_MSOBs = []
    scope_TDS694s = []

    if 0:
        for run in range(33, 48+1):
            TDS694s = glob.glob(dirc + 'run_' + str(run) + '_scope_694*.lvm')
            MSOAs = glob.glob(dirc + 'run_' + str(run) + '_scope_MSOA*.lvm')
            MSOBs = glob.glob(dirc + 'run_' + str(run) + '_scope_MSOB*.lvm')

            scope_MSOA = None
            scope_MSOB = None
            scope_TDS694 = None

            for file_name in TDS694s:
                print file_name
                scope_TDS694 = Scope(file_name)
            for file_name in MSOAs:
                print file_name
                scope_MSOA = Scope(file_name)
            for file_name in MSOBs:
                print file_name
                scope_MSOB = Scope(file_name)

            event_times = Time_Stamp_Viewer([scope_TDS694, scope_MSOA, scope_MSOB])
            event_times.plot_time_stamps()
            del scope_MSOA
            del scope_MSOB
            del scope_TDS694
            del event_times



    show()


class Scope:
    def __init__(self, file_name):
        self.file_names = []
        self.events = []
        self.raw_events = [] # for raw strings
        self.event_times = [] # time stamp string
        self.num_events = 0
        self.get_data(file_name)
        self.event_index = 0
        self.lines  = []#not really lines...

    def get_data(self, file_name):
        self.file_names.append(file_name)
        for line in file(file_name):
            if line[0:5] == ';:WFM' or line[0:4] == ':WFM':
                raw_event = line
                self.raw_events.append( raw_event )

             #picks out event time in finalised header
            elif line[0:3] == '//"':
                event_time = line.split('"')[1]
                self.event_times.append(event_time)

        start_event = 0
        if '694' in file_name:
            start_event = 1 #discard first event if on 694 
        for event_ind in range( start_event, len( self.raw_events ) ):
            self.num_events += 1
            event_time = self.event_times[event_ind]
            raw_event = self.raw_events[event_ind]
            self.events.append( Event(event_ind, raw_event, event_time) )
        print str(self.num_events) + ' found!'



class Event:
    def __init__(self, event_num, raw_event, event_time):
        self.time_stamp = event_time
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
        
        #that 694 bastard requires special attention
        if self.waves[-1].num_samples == 20000 or self.waves[-1].num_samples == 40000 :
            temp_samples_off = self.waves[-1].samples_off

            start = 0
            incr = self.waves[-1].num_samples/4
            for wave in self.waves:
                wave.samples_off = temp_samples_off[start:start+incr]
                wave.get_other()
                start += incr


class Wave:

    def __init__(self, raw_wave, chan):
        self.attribute_names = []
        self.attribute_values = []
        self.samples_off = []
        self.attribute_count = 0
        self.num_samples = 0
        self.channel = chan
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
        #x_0 = float(self.get_raw_attribute('XZE') )
        x_0 = 0
        x_incr = 1#float( self.get_raw_attribute('XIN') )
        #print x_incr
        self.samp_rate = 1./x_incr

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

    # lookup function for raw attributes from header file
    def get_raw_attribute(self, search_string):
        for attribute_index in range(self.attribute_count):
            if search_string in self.attribute_names[attribute_index]:
                return self.attribute_values[attribute_index]

# now we plot things
# lets keep all plotting data types out here for now
# and update them with information from my data classes

class Event_Viewer:
    def __init__(self, scopes, run, scope_names, test_prefix, attr_list):
        self.attr_list = attr_list
        self.scopes = scopes
        self.scope_names = scope_names
        self.event_ind = 0
        self.toggle_volts = False
        self.toggle_offset = False
        self.toggle_offset2 = False
        self.toggle_delay = True
        self.figs = []
        self.figs3 = []
        self.max_events = 0
        
        scope_num = 0
        self.lines = []
        self.lines2 = []

        super_title = ''
        if len(test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(run)
        mp.suptitle(super_title, fontsize = 24)

        for scope in self.scopes:
            if scope.num_events > self.max_events:
                self.max_events = scope.num_events

            fig = mp.subplot(3, 2, 2*scope_num + 1)
            self.figs.append(fig)
            xlabel('Time (s)')
            ylabel('ADC count')

            self.num_waves = scopes[0].events[self.event_ind].num_waves
            for wave_ind in range(self.num_waves):
                y = scope.events[self.event_ind].waves[wave_ind].volts
                t = scope.events[self.event_ind].waves[wave_ind].times
                my_label = ''
                if scope_num == 0:
                    my_label = '694'
                elif scope_num == 1:
                    my_label = 'MSOA'
                else:
                    my_label = 'MSOB'
                my_label += ': ' + str(wave_ind+1)
                line, = plot(t, y, label = my_label )
                self.lines.append(line)
            legend()

            fig3 = mp.subplot(3, 2, 2*scope_num + 2)
            self.figs3.append(fig3)
            axis('off')

            scope_num += 1
        self.update()
        
        self.axnext = mp.axes([0, 0.95, 0.06, 0.05])
        self.axprev = mp.axes([0.06, 0.95, 0.06, 0.05])
        self.axvolt = mp.axes([0.12, 0.95, 0.06, 0.05])
        self.axsoff = mp.axes([0.18, 0.95, 0.06, 0.05])
        self.axdoff = mp.axes([0.24, 0.95, 0.06, 0.05])
        self.axddel = mp.axes([0.3, 0.95, 0.06, 0.05])

        self.bnext = Button(self.axnext, 'Next')
        self.bnext.on_clicked(self.next)
            
        self.bprev = Button(self.axprev, 'Previous')
        self.bprev.on_clicked(self.prev)
        
        self.bvolts = Button(self.axvolt, 'Volts/ADC')
        self.bvolts.on_clicked(self.volts_toggle)
            
        self.bsoff = Button(self.axsoff, 'Scope Offset')
        self.bsoff.on_clicked(self.offset_toggle)

        self.bdoff = Button(self.axdoff, 'Display Offset')
        self.bdoff.on_clicked(self.offset_toggle2)

        self.bddel = Button(self.axddel, 'Display Delay')
        self.bddel.on_clicked(self.delay_toggle)
        mp.show()

    def delay_toggle(self, event):
        self.toggle_delay = not self.toggle_delay
        self.update()

    def offset_toggle2(self, event):
        self.toggle_offset2 = not self.toggle_offset2
        self.update()

    def offset_toggle(self, event):
        self.toggle_offset = not self.toggle_offset
        self.update()

    def volts_toggle(self, event):
        self.toggle_volts = not self.toggle_volts
        for scope_num in range(3):
            mp.subplot(3, 2, 2*scope_num + 1)
            if self.toggle_volts == False:
                ylabel('ADC count')
            else:
                ylabel('Volts (V)')
        self.update()
        
    def next(self, event):
        self.event_ind += 1
        self.event_ind = self.event_ind % self.max_events
        self.update()

    def prev(self, event):
        self.event_ind -= 1
        if self.event_ind < 0:
            self.event_ind = self.max_events - 1
        self.update()

    def update(self):
        scope_num = 0
        for scope in self.scopes:
            max_volts = -1
            min_volts = 1

            #remove header info
            for i in range (len( self.figs3[scope_num].axes.texts )):
                self.figs3[scope_num].axes.texts.pop()
            
            if self.event_ind < scope.num_events:

                # each wave in the current scope, current event
                for wave_ind in range ( len (self.scopes[scope_num].events[self.event_ind].waves) ):
                    y = []
                    if self.toggle_volts == True:
                        if self.toggle_offset == True:
                            y = scope.events[self.event_ind].waves[wave_ind].volts_off
                        else:
                            y = scope.events[self.event_ind].waves[wave_ind].volts
                    else:
                        if self.toggle_offset == True:
                            y = scope.events[self.event_ind].waves[wave_ind].samples_off
                        else:
                            y = scope.events[self.event_ind].waves[wave_ind].samples

                    dy = 0
                    if self.toggle_offset2 == True:
                        dy = -wave_ind
                    if self.toggle_volts == False:
                        dy *= 64                

                    y2 = []
                    for y_ind in range(len(y)):
                        y2.append(y[y_ind] + dy)

                    t = []
                    dt = 0
                    t0 = scope.events[self.event_ind].waves[wave_ind].times[0]
                    t1 = scope.events[self.event_ind].waves[wave_ind].times[1]
                    num_points = scope.events[self.event_ind].waves[wave_ind].num_samples
                    if self.toggle_delay == True:
                        dt = 300*wave_ind*(t1 - t0)

                    for t_ind in range(num_points):
                        t.append(scope.events[self.event_ind].waves[wave_ind].times[t_ind] + dt)

                    self.lines[scope_num*4 + wave_ind].set_ydata(y2)
                    self.lines[scope_num*4 + wave_ind].set_xdata(t)

                    max_y = max(y2)
                    min_y = min(y2)

                    del t

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
                self.figs[scope_num].set_ylim( y_lims )
                self.figs[scope_num].set_title(self.scope_names[scope_num] + ' Waveforms - Event ' + str(self.event_ind) + ': ' + scope.events[self.event_ind].time_stamp)

                self.figs3[scope_num].set_title(self.scope_names[scope_num] + ' Header Info - Event ' + str(self.event_ind) + ': ' + scope.events[self.event_ind].time_stamp)
                for wave in scope.events[self.event_ind].waves:
                    y_coord = 0.875 - ((wave.channel - 1) * 0.25)
                    wave_info = 'Channel ' + str(wave.channel) + ': '
                    for attr in self.attr_list:
                        wave_info += attr + ' ' + wave.get_raw_attribute(attr) + ', '
                    self.figs3[scope_num].text(0.05, y_coord, wave_info, fontsize=12)
            
            else:
                pass
            scope_num += 1
        mp.draw()


class Time_Stamp_Viewer:
    def __init__(self, scopes, run, scope_names, test_prefix):
        self.run = run
        self.test_prefix = test_prefix
        self.scope_names = scope_names
        self.scopes = scopes
        self.scope_event_times = []
        self.num_events = []
        self.t0 = []
        for scope in scopes:
            event_times = []
            self.num_events.append(scope.num_events)
            for event in scope.events:
                ts = event.time_stamp
                ts2 = ts.split(':')
                for tsi in ts2:
                    hour = int(ts2[0])
                    mins = int(ts2[1])
                    secs = int(ts2[2])
                time_secs = hour*3600 + mins*60 + secs
                if len(event_times) == 0:
                    event_times.append(0)
                    self.t0.append(time_secs)
                else:
                    event_times.append(time_secs - self.t0[-1])
                #event_times[-1] -= event_times[0] #relative to start
            self.scope_event_times.append(event_times)

        self.dts = []
        for scope_ind in range(len(self.scopes)):
            dt = []
            for i in range( 1, len( self.scope_event_times[scope_ind] )):
                dt.append(self.scope_event_times[scope_ind][i] - self.scope_event_times[scope_ind][i-1])
            self.dts.append(dt)

        self.dts2 = []
        for scope_ind in range(len(self.scopes)):
            dt2 = []
            num_events = min([self.scopes[scope_ind].num_events, self.scopes[0].num_events])
            for i in range( num_events ):
                dt2.append( self.scope_event_times[scope_ind][i] - self.scope_event_times[0][i] )
            self.dts2.append(dt2)


    def plot_time_stamps(self):

        super_title = ''
        if len(self.test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(self.run)
        mp.suptitle(super_title, fontsize = 24)
        
        mp.subplot(3,1,1)        
        xlabel('Event number in run ' + str(self.run))
        ylabel('Time since scope start time (s)')
        for i in range( len(self.scopes) ):
            plot(range(self.num_events[i]),self.scope_event_times[i], label = self.scope_names[i], marker='o')
        legend()

        mp.subplot(3,1,2)
        xlabel('Event number in run ' + str(self.run))
        ylabel('dt between scope events (s)')
        for scope_ind in range(len(self.scopes)):
            plot(range(len(self.dts[scope_ind])) , self.dts[scope_ind], label = self.scope_names[scope_ind], marker='o')
        legend()

        mp.subplot(3,1,3)
        xlabel('Event number in run ' + str(self.run))
        ylabel('dt relative to TDS694 (s)')
        for scope_ind in range(len(self.scopes)):
            plot(range(len(self.dts2[scope_ind])) , self.dts2[scope_ind], label = self.scope_names[scope_ind], marker='o')
        legend()



class Peak_Correlator:
    def __init__(self, scopes, run, test_prefix): #get peak for all events in scopes
        self.run = run
        self.test_prefix = test_prefix
        self.v1 = []
        self.v2 = []
        self.v3 = []
        self.v4 = []
        self.h1 = []
        self.h2 = []
        self.h3 = []
        self.h4 = []
        self.scintillator = []
        self.monitor = []
        self.vhf = []
        self.sband = []

        for scope_ind in range(len(scopes)):
            for event in scopes[scope_ind].events:
                for wave_ind in range(len(event.waves)):
                    wave = event.waves[wave_ind]
                    max_val = 0
                    a = max(wave.samples)
                    b = abs(min(wave.samples))
                    if b > a:
                        max_val = b
                    else:
                        max_val = a

                    #here we go... check google doc for header layout
                    #https://docs.google.com/spreadsheet/ccc?key=0Am4F6sc-E5YzdGhuQ1lKX2lEaU1uUTRxa21RV2J6ZVE&usp=sharing#gid=0
                    if scope_ind == 0 and wave_ind == 0:
                        self.scintillator.append(max_val)
                    elif scope_ind == 0 and wave_ind == 1:
                        self.monitor.append(max_val)
                    elif scope_ind == 0 and wave_ind == 2:
                        self.vhf.append(max_val)
                    elif scope_ind == 0 and wave_ind == 3:
                        self.sband.append(max_val)
                    elif scope_ind == 1 and wave_ind == 0:
                        self.v1.append(max_val)
                    elif scope_ind == 1 and wave_ind == 1:
                        self.h1.append(max_val)
                    elif scope_ind == 1 and wave_ind == 2:
                        self.v4.append(max_val)
                    elif scope_ind == 1 and wave_ind == 3:
                        self.h4.append(max_val)
                    elif scope_ind == 2 and wave_ind == 0:
                        self.h2.append(max_val)
                    elif scope_ind == 2 and wave_ind == 1:
                        self.v2.append(max_val)
                    elif scope_ind == 2 and wave_ind == 2:
                        self.h3.append(max_val)
                    elif scope_ind == 2 and wave_ind == 3:
                        self.v3.append(max_val)

    def correlate(self):

        l = min([len(self.sband), len(self.v1)])
        print pearsonr(self.sband[0:l], self.v1[0:l], label = 'v1', color='blue')
        print pearsonr(self.sband[0:l], self.h1[0:l], label = 'h1', color='red')
        print pearsonr(self.sband[0:l], self.v4[0:l], label = 'v4', color='green')
        print pearsonr(self.sband[0:l], self.h4[0:l], label = 'h4', color='black')

        print pearsonr(self.sband[0:l], self.h2[0:l], label = 'h2', color='blue')
        print pearsonr(self.sband[0:l], self.v2[0:l], label = 'v2', color='red')
        print pearsonr(self.sband[0:l], self.h3[0:l], label = 'h3', color='green')
        print pearsonr(self.sband[0:l], self.v3[0:l], label = 'v3', color='black')

    def draw_sband_plots(self):
                        
        fig = mp.figure()
        ax1 = fig.add_subplot(2,1,1)
        l = min([len(self.v1), len(self.v2)])
        ax1.scatter(self.v1[0:l], self.v1[0:l], label = 'v1-v2', color='blue')
        ax1.scatter(self.v1[0:l], self.v2[0:l], label = 'v1-v3', color='red')
        ax1.scatter(self.v1[0:l], self.v3[0:l], label = 'v1-v4', color='green')
        ax1.scatter(self.v2[0:l], self.v3[0:l], label = 'v2-v3', color='black')
        ax1.scatter(self.v2[0:l], self.v4[0:l], label = 'v2-v4', color='cyan')
        ax1.scatter(self.v3[0:l], self.v4[0:l], label = 'v3-v4', color='yellow')
        ax1.set_ylim([0, 128])
        ax1.set_xlim([0, 128])

        title('VPol Channels')
        xlabel('S-band (ADC counts)')
        ylabel('Seavey channels (ADC counts)')
        legend()

        ax2 = fig.add_subplot(2,1,2)
        l = min([len(self.h1), len(self.h2)])
        ax2.scatter(self.h1[0:l], self.h1[0:l], label = 'h1-h2', color='blue')
        ax2.scatter(self.h1[0:l], self.h2[0:l], label = 'h1-h3', color='red')
        ax2.scatter(self.h1[0:l], self.h3[0:l], label = 'h1-h4', color='green')
        ax2.scatter(self.h2[0:l], self.h3[0:l], label = 'h2-h3', color='black')
        ax2.scatter(self.h2[0:l], self.h4[0:l], label = 'h2-h4', color='cyan')
        ax2.scatter(self.h3[0:l], self.h4[0:l], label = 'h3-h4', color='yellow')
        ax2.set_ylim([0, 128])
        ax2.set_xlim([0, 128])
        title('HPol Channels')
        xlabel('S-band (ADC counts)')
        ylabel('Seavey channels (ADC counts)')
        legend()

    def draw_self_plots(self):
        fig = mp.figure()
        super_title = ''
        if len(self.test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(self.run)
        mp.suptitle(super_title, fontsize = 24)
        ax1 = fig.add_subplot(2,1,1)
        l = min([len(self.sband), len(self.v1)])
        ax1.scatter(self.sband[0:l], self.v1[0:l], label = 'v1', color='blue')
        ax1.scatter(self.sband[0:l], self.h1[0:l], label = 'h1', color='red')
        ax1.scatter(self.sband[0:l], self.v4[0:l], label = 'v4', color='green')
        ax1.scatter(self.sband[0:l], self.h4[0:l], label = 'h4', color='black')
        ax1.set_ylim([0, 128])
        ax1.set_xlim([0, 128])
        title('Scope MSOA')
        xlabel('S-band (ADC counts)')
        ylabel('Seavey channels (ADC counts)')
        legend()

        ax2 = fig.add_subplot(2,1,2)
        l = min([len(self.sband), len(self.v2)])
        ax2.scatter(self.sband[0:l], self.h2[0:l], label = 'h2', color='blue')
        ax2.scatter(self.sband[0:l], self.v2[0:l], label = 'v2', color='red')
        ax2.scatter(self.sband[0:l], self.h3[0:l], label = 'h3', color='green')
        ax2.scatter(self.sband[0:l], self.v3[0:l], label = 'v3', color='black')
        ax2.set_ylim([0, 128])
        ax2.set_xlim([0, 128])
        title('Scope MSOB')
        xlabel('S-band (ADC counts)')
        ylabel('Seavey channels (ADC counts)')
        legend()

if __name__ == "__main__":
    main()
