from glob import glob
from os import path
import os

repo = 'testprod'
commit_id = '3bdc89449dcd518254e3031ee49f1a88aa2320c7'

def checkmakedir( path ):
    if os.path.isdir( path ):
        print('hey, directory already exists!: {}'.format(path))
    else:
        os.makedirs( path )
        print('creating directory... {}'.format(path))

def get_file_number(fname):
    return int(fname.split('.')[-2].split('_')[0])

input_files = "/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/irene/output/*h5"
input_files = glob(input_files)

base_path = "/analysis_test/MC/NEW/NEXT_v1_05_02/Xe0nu/ACTIVE/penthesilea/"
base_path = path.join(base_path, commit_id)

job_dir = base_path + '/jobs/'
cfg_dir = base_path + '/configs/'
log_dir = base_path + '/logs/'
out_dir = base_path + '/output/'
checkmakedir (job_dir)
checkmakedir (cfg_dir)
checkmakedir (log_dir)
checkmakedir (out_dir)

exe_template = open('/home/jmbenlloch/server/templates/exe_ic_docker.sh').read()
cfg_template = open('/home/jmbenlloch/server/templates/penthesilea.conf').read()


for f in input_files[:10]:
    index = get_file_number(f)
    fname = f.split('/')[-1]

    basename = fname.replace('pmaps', 'hdst')
    basename = '.'.join(basename.split('.')[0:-1])

    print(fname)

    print(f)
    print (index, fname)

    cfg_fname = cfg_dir + '{0}.conf'.format(basename)
    job_fname = job_dir + '{0}.sh'  .format(basename)
    fileout   = out_dir + '{0}.h5'  .format(basename)

    stderr = log_dir + '/' + basename + '.err'
    stdout = log_dir + '/' + basename + '.out'
    log    = log_dir + '/' + basename + '.log'

    parameters = {
        'stdout' : stdout,
        'stderr' : stderr,
        'filein' : fname,
        'fileout': fileout,
        'config' : cfg_fname,
        'jobname': fileout,
        'repo'   : repo,
        'tag'    : commit_id,
        'city'   : 'penthesilea',
    }

    with open(job_fname, 'w') as exe_file:
        exe_file.write(exe_template.format(**parameters))

    with open(cfg_fname, 'w') as cfg_file:
        cfg_file.write(cfg_template.format(**parameters))


