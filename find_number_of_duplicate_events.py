import look_at_run
import matplotlib.pyplot as mp

def main():
    scope_set = {'694', 'MSOA', 'MSOB'}
    TDS_duplicates = []
    MSOA_duplicates = []
    MSOB_duplicates = []
    TDS_num_waves = []
    MSOA_num_waves = []
    MSOB_num_waves = []
    TDS_duplicates2 = []
    MSOA_duplicates2 = []
    MSOB_duplicates2 = []

    first_run = 221
    last_run = 221
    runs = range(first_run, last_run+1)
    test_prefix = ''
    #test_prefix = 'test_'
    for run in runs:
        print '***********'
        print 'run ' + str(run)
        print '***********'

        scopes = look_at_run.main(run, test_prefix)
        if len(scopes) < 3:
            these_scopes = [scope.name for scope in scopes]
            temp_set = set(these_scopes)
            missing_scopes = list(scope_set - temp_set)
            print missing_scopes
            for ms in missing_scopes:
                if ms == '694':
                    TDS_duplicates.append(0)
                    TDS_duplicates2.append(0)
                    TDS_num_waves.append(0)
                elif ms == 'MSOA':
                    MSOA_duplicates.append(0)
                    MSOA_duplicates2.append(0)
                    MSOA_num_waves.append(0)
                elif ms == 'MSOB':
                    MSOB_duplicates.append(0)
                    MSOB_duplicates2.append(0)
                    MSOB_num_waves.append(0)

        for scope_ind, scope in enumerate(scopes):
            n = 0
            for event in scopes[scope_ind].events:
                n += event.num_waves
            m = max(1, n)

            if scope.name == '694':
                TDS_duplicates.append(scope.check_for_repeated_waveforms())
                TDS_duplicates2.append(float(TDS_duplicates[-1])/m)
                TDS_num_waves.append(n)
            elif scope.name == 'MSOA':
                MSOA_duplicates.append(scope.check_for_repeated_waveforms())
                MSOA_duplicates2.append(float(MSOA_duplicates[-1])/m)
                MSOA_num_waves.append(n)
            elif scope.name == 'MSOB':
                MSOB_duplicates.append(scope.check_for_repeated_waveforms())
                MSOB_duplicates2.append(float(MSOB_duplicates[-1])/m)
                MSOB_num_waves.append(n)

    fig = mp.figure() #plot(runs, TDS_duplicates)
    ax0 = fig.add_subplot(3,1,1)
    ax0.scatter(runs, TDS_num_waves, label = 'TDS694', color = 'blue')
    ax0.scatter(runs, MSOA_num_waves, label = 'MSOA', color = 'red')
    ax0.scatter(runs, MSOB_num_waves, label = 'MSOB', color = 'green')

    mp.title('Number of waveforms')
    mp.xlabel('Run number')
    mp.ylabel('Total number of waveforms')
    mp.legend()

    ax1 = fig.add_subplot(3,1,2)
    ax1.scatter(runs, TDS_duplicates, label = 'TDS694', color = 'blue')
    ax1.scatter(runs, MSOA_duplicates, label = 'MSOA', color = 'red')
    ax1.scatter(runs, MSOB_duplicates, label = 'MSOB', color = 'green')

    mp.title('Duplicated waveforms')
    mp.xlabel('Run number')
    mp.ylabel('Number of repeated waveforms')
    mp.legend()

    ax2 = fig.add_subplot(3,1,3)
    ax2.scatter(runs, TDS_duplicates2, label = 'TDS694', color = 'blue')
    ax2.scatter(runs, MSOA_duplicates2, label = 'MSOA', color = 'red')
    ax2.scatter(runs, MSOB_duplicates2, label = 'MSOB', color = 'green')
    ax2.set_ylim([0, 1])
    mp.title('Fraction of duplicated waveforms')
    mp.xlabel('Run number')
    mp.ylabel('Fraction of repeated waveforms')
    mp.legend()

    mp.show()

if __name__ == "__main__":
    main()
