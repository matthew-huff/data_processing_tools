import argparse
import AverageNC_Data
import data_manipulator
import kriging_data as kd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename',
        help='Pass a .nc file for processing')

    args = parser.parse_args()
    args = vars(args)

    filename = args['filename'].split('.nc')[0]
    outfile = filename+'.geojson'
    outfile_binned = filename+'_binned.geojson'
    print("Will create outfile to " + outfile + " and " + outfile_binned)
    AverageNC_Data.AverageNCData(filename=filename + '.nc', outfile=outfile)
    d = kd.KrigingTool(filename=outfile, settimer=True, fast=True, bo = outfile_binned)



main()