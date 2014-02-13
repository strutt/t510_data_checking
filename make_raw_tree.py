from ROOT import * # Not too inefficient since ROOT doesn't import everything by default
import look_at_run # My raw data objects
from array import array

def main(run, test_prefix):


    run_name = test_prefix + str(run)
    scopes = look_at_run.main(run, test_prefix)
    print 'Making raw data tree for run ' + run_name

    # Create a TFile
    f_name = 'raw_data_' + run_name + '.root' 
    f = TFile(f_name, 'recreate')

    # Get scope objects, which contain data.
    # We will construct a separate tree for each scope
    for i, scope in enumerate(scopes):
        t_name = 'raw_tree_' + scope.name
        t = TTree(t_name, t_name)
        
        # Guess at longest array length we will encounter.
        # There may be a more elegant way to do this...
        maxn = 20000
        
        # This is some very convoluted shit here to get ROOT
        # to work with python. I almost gave up because of this.
        # Anything going into a tree must be an array, not very pythonic

        n_samps1 = array('i', [0]) # number of samples in waveforms
        n_samps2 = array('i', [0]) 
        n_samps3 = array('i', [0]) 
        n_samps4 = array('i', [0]) 

        ch1 = array('f', maxn*[0.]) # waveforms
        ch2 = array('f', maxn*[0.])
        ch3 = array('f', maxn*[0.])
        ch4 = array('f', maxn*[0.])

        # Arrays of other waveformy things
        x_0 = array('f', 4*[0.]) # start time
        x_incr = array('f', 4*[0.]) # delta t
        y_off = array('f', 4*[0.]) # sample offset in ADC counts?, set on scope
        y_mult = array('f', 4*[0.]) # conversion factor from ADC to volts, set on scope

        event_time = array('i', [0]) # time since start of day in seconds

        # This will allow us to iterate over the channels, isn't python wonderful
        ns = [n_samps1, n_samps2, n_samps3, n_samps4]
        chs = [ch1, ch2, ch3, ch4]

        t.Branch('n_samps1', n_samps1, 'n_samps1/I')
        t.Branch('n_samps2', n_samps2, 'n_samps2/I')
        t.Branch('n_samps3', n_samps3, 'n_samps3/I')
        t.Branch('n_samps4', n_samps4, 'n_samps4/I')
        t.Branch('ch1', ch1, 'ch1[n_samps1]/F')
        t.Branch('ch2', ch2, 'ch2[n_samps2]/F')
        t.Branch('ch3', ch3, 'ch3[n_samps3]/F')
        t.Branch('ch4', ch4, 'ch4[n_samps4]/F')
        t.Branch('event_time', event_time, 'event_time/I')
        
        t.Branch('x0', x_0, 'x_0[4]/F')
        t.Branch('x_incr', x_incr, 'x_incr[4]/F')
        t.Branch('y_off', y_off, 'y_off[4]/F')
        t.Branch('y_mult', y_mult, 'y_mult[4]/F')
        
        # Get events for this scope
        for j, event in enumerate(scope.events):

            # Convert time string into seconds since midnight
            event_time[0] = time_in_seconds(event.time_stamp)

            # Get waves for this event
            for k, wave in enumerate(event.waves):
                # Copy conversion info, some of this may be redundant, some more may be needed...
                ns[k][0] = len(wave.samples)
                
                print scope.name
                print 'event ' + str(j)
                print 'wave ' + str(k)
                print ns[k][0]
                x_0[k] = wave.x_0
                x_incr[k] = wave.x_incr
                y_off[k] = wave.y_off
                y_mult[k] = wave.y_mult

                if ns[k][0] > maxn:
                    print 'Error! Number of samples greater than guess of maximum length - alter code!'
                    print "PyROOT isn't very clever doing things this way around (writing to root things)"
                    exit(-1)
                # Copy waveform into array
                for ind, samp in enumerate(wave.samples):
                    chs[k][ind] = samp

            # Make sure things go in the tree
            t.Fill()
        f.Write()
    f.Close()

def time_in_seconds(time_stamp):
    """
    Takes a string of HH:MM:SS and converts it to the number of senconds
    since the day began
    """
    ts = time_stamp.split(':')
    hour = int(ts[0])
    mins = int(ts[1])
    secs = int(ts[2])
    return hour*3600 + mins*60 + secs

    
if __name__ == "__main__":
    from os import sys
    # First argv is name of program.
    # Using a set to avoid repetitions.
    run = 0
    test_prefix = ''
    if len(sys.argv) > 1:
        run = sys.argv[1]
    if len(sys.argv) > 2:
        test_prefix = 'test_'
    main(run, test_prefix)
