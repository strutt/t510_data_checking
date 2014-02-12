from ROOT import *
import look_at_run # my raw data objects
from array import array

def main(run, test_prefix):
    run_name = test_prefix + str(run)
    scopes = look_at_run.main(run, test_prefix)

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
        n1 = array('i', [0]) # number of samples in waveforms
        n2 = array('i', [0]) 
        n3 = array('i', [0])
        n4 = array('i', [0])
        ch1 = array('f', maxn*[0.]) # sample waveforms
        ch2 = array('f', maxn*[0.])
        ch3 = array('f', maxn*[0.])
        ch4 = array('f', maxn*[0.])

        event_time = array('i', [0]) # time since start of day in seconds

        # This will allow us to iterate over the channels, isn't python wonderful
        ns = [n1, n2, n3, n4]
        chs = [ch1, ch2, ch3, ch4]
        
        # Setting branch addresses has been somewhat pythonized
        # so there is a redeeming feature here.
        t.Branch('n1', n1, 'n1/I')
        t.Branch('n2', n2, 'n2/I')
        t.Branch('n3', n3, 'n3/I')
        t.Branch('n4', n4, 'n4/I')
        t.Branch('ch1', ch1, 'ch1[n1]/F')
        t.Branch('ch2', ch2, 'ch2[n2]/F')
        t.Branch('ch3', ch3, 'ch3[n3]/F')
        t.Branch('ch4', ch4, 'ch4[n4]/F')
        t.Branch('event_time', event_time, 'event_time/I')

        # Get events for this scope
        for j, event in enumerate(scope.events):

            ts = event.time_stamp
            ts2 = ts.split(':')
            hour = int(ts2[0])
            mins = int(ts2[1])
            secs = int(ts2[2])
            event_time[0] = hour*3600 + mins*60 + secs

            # Get waves for this event
            for k, wave in enumerate(event.waves):
                ns[k][0] = len(wave.samples)
                if ns[k][0] > maxn:
                    print 'Error! Number of samples greater than guess of maximum length - alter code!'
                    print "PyROOT isn't very clever doing things this way around (writing to root things)"
                    exit(-1)
                for ind, samp in enumerate(wave.samples):
                    chs[k][ind] = samp

            # Make sure things go in the tree
            t.Fill()                
        f.Write()
    f.Close()

def time_in_seconds():
    pass
    
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
