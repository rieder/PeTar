#!/usr/bin/env python3

import numpy as np
import multiprocessing as mp
import sys
import petar
import getopt

if __name__ == '__main__':

    filename_prefix='data'
    average_mode='sphere'
    read_flag=False
    n_cpu=0

    def usage():
        print("A tool for processing a list of snapshot data to detect binaries, calculate Langragian radii and properties, get the density center and core radius")
        print("Usage: petar.data.process [options] data_filename")
        print("data_filename: A list of snapshot data path, each line for one snapshot")
        print("option:")
        print("  -h(--help): help")
        print("  -p(--filename-prefix): prefix of output file names for: [prefix].[lagr|esc.[single|binary]|core] (data)")
        print("  -m(--mass-fraction): Lagrangian radii mass fraction (0.1,0.3,0.5,0.7,0.9)")
        print("  -G(--gravitational-constant): Gravitational constant (if interrupt-mode=bse: ",petar.G_MSUN_PC_MYR,"; else 1.0)")
        print("  -b(--r-max-binary): maximum sepration for detecting binaries (0.1)")
        print("  -B(--full-binary): calculate full binary orbital parameters (simple_mode=False in Binary class), this option increases computing time")
        print("  -a(--average-mode): Lagrangian properity average mode: sphere: average from center to Lagragian radii; shell: average between two neighbor radii (sphere)")
        print("  -r(--read-data): read existing single, binary and core data to avoid expensive KDTree construction, no argument, disabled in default")
        print("  -e(--r-escape): a constant escape distance criterion, in default, it is 20*half-mass radius")
        print("  -i(--interrupt-mode): interruption mode: no, base, bse (no)")
        print("  -n(--n-cpu): number of CPU threads for parallel processing (all threads)")

    try:
        shortargs = 'p:m:G:b:Ba:re:i:n:h'
        longargs = ['mass-fraction=','gravitational-constant=','r-max-binary=','full-binary','average-mode=', 'filename-prefix=','read-data','r-escape=','interrupt-mode=','n-cpu=','help']
        opts,remainder= getopt.getopt( sys.argv[1:], shortargs, longargs)

        kwargs=dict()
        for opt,arg in opts:
            if opt in ('-h','--help'):
                usage()
                sys.exit(1)
            elif opt in ('-p','--filename-prefix'):
                filename_prefix = arg
            elif opt in ('-m','--mass-fraction'):
                kwargs['mass_fraction'] = np.array([float(x) for x in arg.split(',')])
            elif opt in ('-G','--gravitational-constant'):
                kwargs['G'] = float(arg)
            elif opt in ('-b','--r-max-binary'):
                kwargs['r_max_binary'] = float(arg)
            elif opt in ('-B','--full-binary'):
                kwargs['simple_binary'] = False
            elif opt in ('-a','--average-mode'):
                kwargs['average_mode'] = arg
            elif opt in ('-n','--n-cpu'):
                n_cpu = int(arg)
            elif opt in ('-i','--interrupt-mode'):
                kwargs['interrupt_mode'] = arg
            elif opt in ('-r','--read-data'):
                read_flag = True
            elif opt in ('-e','--r-escape'):
                kwargs['r_escape'] = float(arg)
            else:
                assert False, "unhandeld option"

    except getopt.GetoptError:
        print('getopt error!')
        usage()
        sys.exit(1)

    filename = remainder[0]

    if (not 'G' in kwargs.keys()):
        if ('interrupt_mode' in kwargs.keys()):
            if (kwargs['interrupt_mode']=='bse'): kwargs['G'] = 0.00449830997959438 # pc^3/(Msun*Myr^2)

    kwargs['filename_prefix'] = filename_prefix

    for key, item in kwargs.items(): print(key,':',item)

    fl = open(filename,'r')
    file_list = fl.read()
    path_list = file_list.splitlines()
     
    result,time_profile = petar.parallelDataProcessList(path_list, n_cpu, read_flag, **kwargs)

    for key in ['lagr','core','bse_status', 'esc_single', 'esc_binary']:
        if key in result.keys():
            key_filename  = filename_prefix + '.' + key
            result[key].savetxt(key_filename)
            print (key,"data is saved in file:",key_filename)
     
    print ('CPU time profile:')
    for key, item in time_profile.items():
        print (key,item,)
