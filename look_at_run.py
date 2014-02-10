from pylab import *
import matplotlib.pyplot as mp
from matplotlib.widgets import Button
import numpy
import glob
import sys
import math

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
    for i in range(len(scope_names)):
        file_name = dirc
        file_name += test_prefix + 'run_' + str(run) + '_scope_' + scope_names[i] + '*.lvm'
        # If there are muliple files with the same run name, this selects the most recent one.
        # (The time the data was taken appears in the file name, so the most recent one will be last).
        file_names.append(glob.glob(file_name)[-1])

    # Create my data objects from the specified file names.
    scopes = []
    for file_name in file_names:
        scopes.append( Scope(file_name) ) 

    # Start event viewer.
    Event_Viewer(scopes, run, scope_names, test_prefix, attr_list) 

    # Start time stamp viewer
    t = Time_Stamp_Viewer(scopes, run, scope_names, test_prefix)
    t.plot_time_stamps()

    # Start peak correlator
    p = Peak_Correlator(scopes, run, test_prefix)
    #p.draw_694_plots()
    p.draw_sband_plots() #max abs relative to sband
    #p.draw_self_plots()
    #p.draw_max_adc_plots()
    show()

class Scope:
    """
    This class contains all the events in a run for a particular scope, plus other useful information.
    """
    def __init__(self, file_name):
        self.file_names = []
        self.events = []
        self.raw_events = []
        self.event_times = []
        self.num_events = 0
        self.get_data(file_name)
        self.event_index = 0
        self.lines  = []

    def get_data(self, file_name):
        self.file_names.append(file_name)
        for line in file(file_name):
            if line[0:5] == ';:WFM' or line[0:4] == ':WFM':
                raw_event = line
                self.raw_events.append( raw_event )

            # Picks out event time in finalised header
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
    """
    A class which contains 4 waveforms and a timestamp
    """
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
    """
    The Wave class is initialized by being handed a "raw waveform", which is a string from the raw data.
    The raw data string will contain many pieces of information, including the waveform.
    This class puts all the pieces of information in some semblance of order, hopefully.
    """
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

        # Get attributes from the raw waveform.
        attributes = raw_wave.split(';') # The Attributes are colon separated.
        for attribute in attributes:
            attribute_parts = attribute.split(' ', 1) # Names are separated from values by a single space.
            if len(attribute_parts) == 2: # There may be some blank fields, this should ignore them.
                self.attribute_names.append(attribute_parts[0])
                self.attribute_values.append(attribute_parts[1])
                self.attribute_count += 1

        # Get raw adc counts and subtract y_offset.
        hopefully_samples = self.get_raw_attribute('CURV')
        if hopefully_samples == None:
            pass
            #for i in range(2): # add some blank samples, see if this works
                #self.samples.append(0)
                #self.samples_off.append(0)
        else:
            for sample in hopefully_samples.split(','):
                # I'm not sure if this is necessary, but there are some return and newline characters. 
                if '//\r\n' in sample:
                    sample = sample.replace('//\r\n','')
                self.samples_off.append( float(sample) )
        self.num_samples = len(self.samples_off)

        # At least one scope reads out all four waveforms as a single waveform (silly labview).
        # This if statement should stop the waveform information being grabbed for that scope.
        if len(self.samples_off) > 0 and len(self.samples_off) < 20000:
            self.get_other()

    def get_other(self):

        self.num_samples = len(self.samples_off)
        x_0 = float(self.get_raw_attribute('XZE') ) # XZE is x0, the time of the initial sample.
        #x_0 = 0
        x_incr = float( self.get_raw_attribute('XIN') )
        #x_incr = 1
        self.samp_rate = 1./x_incr

        y_off = float( self.get_raw_attribute('YOF') ) # YOF is the y-offset in volts on the scope.
        for sample in self.samples_off:
            self.samples.append( float(sample) - y_off )

        for index in range(self.num_samples):
            self.times.append((x_0 + index*x_incr)) # Populate the list of times.

        y_mult = float( self.get_raw_attribute('YMU') ) # YMU is the y-multiplier, i.e. volts/adc conversion.
        
        # Here we populate a list of samples, both zeroed and offset so the user can switch between them
        # in the display.
        for samp in self.samples_off:
            self.volts.append( (samp - y_off)*y_mult )
        for samp in self.samples_off:
            self.volts_off.append( samp*y_mult)

    # This is a lookup function which means raw attributes can be picked out by their name.
    def get_raw_attribute(self, search_string):
        for attribute_index in range(self.attribute_count):
            if search_string in self.attribute_names[attribute_index]:
                return self.attribute_values[attribute_index]

class Event_Viewer:

    """
    This is the class that turns the data objects into a (hopefully) pretty display.
    There should only be one instance of this running.
    """

    def __init__(self, scopes, run, scope_names, test_prefix, attr_list):
        self.attr_list = attr_list
        self.num_scopes = len(scopes)
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

        # Generate the display title
        super_title = ''
        if len(test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(run)
        mp.suptitle(super_title, fontsize = 24)

        # Get data frim 
        for scope in self.scopes:
            if scope.num_events > self.max_events:
                self.max_events = scope.num_events

            fig = mp.subplot(self.num_scopes, 2, 2*scope_num + 1)
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

            fig3 = mp.subplot(self.num_scopes, 2, 2*scope_num + 2)
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
        for scope_num in range(self.num_scopes):
            mp.subplot(self.num_scopes, 2, 2*scope_num + 1)
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
        self.num_scopes = len(scopes)
        self.test_prefix = test_prefix
        self.MSOA_1 = []
        self.MSOB_2 = []
        self.MSOB_4 = []
        self.MSOA_3 = []
        self.MSOA_2 = []
        self.MSOB_1 = []
        self.MSOB_3 = []
        self.MSOA_4 = []
        self.TDS694_1 = []
        self.TDS694_2 = []
        self.TDS694_3 = []
        self.TDS694_4 = []

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
                    #https://docs.google.com/spreadsheet/ccc?key=0Am4F6sc-E5YzdGhuQ1lKX2lEaU1uUTRxa21RMSOB_2J6ZVE&usp=sharing#gid=0
                    #print str(scope_ind) + ' ' + str(self.num_scopes)
                    if scope_ind == 0 and wave_ind == 0:
                        self.TDS694_1.append(max_val)
                    elif scope_ind == 0 and wave_ind == 1:
                        self.TDS694_2.append(max_val)
                    elif scope_ind == 0 and wave_ind == 2:
                        self.TDS694_3.append(max_val)
                    elif scope_ind == 0 and wave_ind == 3:
                        self.TDS694_4.append(max_val)
                    elif scope_ind == 1 and wave_ind == 0:
                        self.MSOA_1.append(max_val)
                    elif scope_ind == 1 and wave_ind == 1:
                        self.MSOA_2.append(max_val)
                    elif scope_ind == 1 and wave_ind == 2:
                        self.MSOA_3.append(max_val)
                    elif scope_ind == 1 and wave_ind == 3:
                        self.MSOA_4.append(max_val)
                    elif scope_ind == 2 and wave_ind == 0:
                        self.MSOB_1.append(max_val)
                    elif scope_ind == 2 and wave_ind == 1:
                        self.MSOB_2.append(max_val)
                    elif scope_ind == 2 and wave_ind == 2:
                        self.MSOB_3.append(max_val)
                    elif scope_ind == 2 and wave_ind == 3:
                        self.MSOB_4.append(max_val)


    def correlation(self, x, y):
        lx = len(x)
        ly = len(y)
        if ly > lx:
            dl = ly - lx
            for i in range(dl):
                y.append(0)
        elif lx > ly:
            dl = lx - ly
            for i in range(dl):
                x.append(0)

            
        xmean = 0
        xrms = 0
        for xi in x:
            xmean += xi
            xrms += xi*xi
        xmean /= len(x)
        xrms = xrms/len(x) - xmean*xmean
        xrms = math.sqrt(xrms)

        ymean = 0
        yrms = 0
        for yi in y:
            ymean += yi
            yrms += yi*yi
        ymean /= len(y)
        yrms = yrms/len(y) - ymean*ymean
        yrms = math.sqrt(yrms)
        
        rho = 0
        for i in range(len(x)):
            rho += (x[i] - xmean)*(y[i] - ymean)
        rho /= len(x)
        rho /= (xrms*yrms)

        return rho


    def draw_max_adc_plots(self):
        fig = mp.figure()
        super_title = ''
        if len(self.test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(self.run)
        mp.suptitle(super_title, fontsize = 24)
        if self.num_scopes > 0:
            ax1 = fig.add_subplot(self.num_scopes,1,1)
            e = range( len( self.TDS694_1) )
            ax1.scatter(e, self.TDS694_1, label = '694: 1', color='blue')
            ax1.scatter(e, self.TDS694_2, label = '694: 2', color='red')
            ax1.scatter(e, self.TDS694_3, label = '694: 3', color='green')
            ax1.scatter(e, self.TDS694_4, label = '694: 4', color='black')
            ax1.set_ylim([0, 128])
            title('Scope 694')
            xlabel('Event')
            ylabel('ADC counts')
            legend()
        if self.num_scopes > 1 :
            ax2 = fig.add_subplot(self.num_scopes,1,2)
            e = range( len( self.MSOA_1) )
            #print e
            #print self.MSOA_1
            ax2.scatter(e, self.MSOA_1, label = 'MSOA_1', color='blue')
            ax2.scatter(e, self.MSOA_2, label = 'MSOA_2', color='red')
            ax2.scatter(e, self.MSOB_3, label = 'MSOA_3', color='green')
            ax2.scatter(e, self.MSOB_4, label = 'MSOA_4', color='black')
            ax2.set_ylim([0, 128])
            title('Scope MSOA')
            xlabel('Event')
            ylabel('ADC counts')
            legend()
        if self.num_scopes > 2:
            ax3 = fig.add_subplot(self.num_scopes,1,3)
            e = range( len( self.MSOB_1) )
            ax3.scatter(e, self.MSOB_1, label = 'MSOB_1', color='blue')
            ax3.scatter(e, self.MSOB_2, label = 'MSOB_2', color='red')
            ax3.scatter(e, self.MSOB_3, label = 'MSOB_3', color='green')
            ax3.scatter(e, self.MSOB_4, label = 'MSOB_4', color='black')
            ax3.set_ylim([0, 128])
            title('Scope MSOB')
            xlabel('Event')
            ylabel('ADC counts')
            legend()

        print 'TDS694_1 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.TDS694_1, self.TDS694_4))
        print 'TDS694_2 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.TDS694_2, self.TDS694_4))
        print 'TDS694_3 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.TDS694_3, self.TDS694_4))
        print 'TDS694_4 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.TDS694_4, self.TDS694_4))
        print ''
        print 'MSOA_1 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOA_1, self.TDS694_4))
        print 'MSOA_2 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOA_2, self.TDS694_4))
        print 'MSOA_3 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOA_3, self.TDS694_4))
        print 'MSOA_4 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOA_4, self.TDS694_4))
        print ''
        print 'MSOB_1 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOB_1, self.TDS694_4))
        print 'MSOB_2 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOB_2, self.TDS694_4))
        print 'MSOB_3 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOB_3, self.TDS694_4))
        print 'MSOB_4 vs TDS694_4, rho = {0:.3f}'.format(self.correlation(self.MSOB_4, self.TDS694_4))
        print ''
        print ''

    def draw_sband_plots(self):
        fig = mp.figure()
        super_title = ''
        if len(self.test_prefix) > 0:
            super_title = 'Test '
        super_title += 'Run ' + str(self.run)
        mp.suptitle(super_title, fontsize = 24)
        ax0 = fig.add_subplot(self.num_scopes,1,1)
        l = min([len(self.TDS694_4), len(self.TDS694_1)])
        ax0.scatter(self.TDS694_4[0:l], self.TDS694_1[0:l], label = '694_1', color='blue')
        ax0.scatter(self.TDS694_4[0:l], self.TDS694_2[0:l], label = '694_2', color='red')
        ax0.scatter(self.TDS694_4[0:l], self.TDS694_3[0:l], label = '694_3', color='green')
        ax0.scatter(self.TDS694_4[0:l], self.TDS694_4[0:l], label = '694_4', color='black')
        ax0.set_ylim([0, 128])
        ax0.set_xlim([0, 128])
        title('Scope MSOA')
        xlabel('S-band (ADC counts)')
        ylabel('Seavey channels (ADC counts)')
        legend()

        if self.num_scopes > 1:
            ax1 = fig.add_subplot(self.num_scopes,1,2)
            l = min([len(self.TDS694_4), len(self.MSOA_1)])
            ax1.scatter(self.TDS694_4[0:l], self.MSOA_1[0:l], label = 'MSOA_1', color='blue')
            ax1.scatter(self.TDS694_4[0:l], self.MSOA_2[0:l], label = 'MSOA_2', color='red')
            ax1.scatter(self.TDS694_4[0:l], self.MSOA_3[0:l], label = 'MSOA_3', color='green')
            ax1.scatter(self.TDS694_4[0:l], self.MSOA_4[0:l], label = 'MSOA_4', color='black')
            ax1.set_ylim([0, 128])
            ax1.set_xlim([0, 128])
            title('Scope MSOA')
            xlabel('S-band (ADC counts)')
            ylabel('Seavey channels (ADC counts)')
            legend()

        if self.num_scopes == 3:
            ax2 = fig.add_subplot(self.num_scopes,1,3)
            l = min([len(self.TDS694_4), len(self.MSOB_2)])
            ax2.scatter(self.TDS694_4[0:l], self.MSOB_1[0:l], label = 'MSOB_1', color='blue')
            ax2.scatter(self.TDS694_4[0:l], self.MSOB_2[0:l], label = 'MSOB_2', color='red')
            ax2.scatter(self.TDS694_4[0:l], self.MSOB_3[0:l], label = 'MSOB_3', color='green')
            ax2.scatter(self.TDS694_4[0:l], self.MSOB_4[0:l], label = 'MSOB_4', color='black')
            ax2.set_ylim([0, 128])
            ax2.set_xlim([0, 128])
            title('Scope MSOB')
            xlabel('S-band (ADC counts)')
            ylabel('Seavey channels (ADC counts)')
            legend()

if __name__ == "__main__":
    main()
