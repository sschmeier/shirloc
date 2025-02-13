"""


"""

# Import built-in python modules
import argparse
import datetime
import logging
import os
import sys
import time
import csv

# Import bin modules
import argparse
import manifesto
import system_check
import kallisto_wrapper
import sherlock_classes
import sherlock_methods
from version import __version__

if __name__ == '__main__':

    # Store the value of the start time of analysis.
    time_stamp = str(datetime.datetime.now())
    initial_time = time.time()

    # Setup of argparse for processing the input script arguments.
    parser = argparse.ArgumentParser(description="An analysis pipeline that quantitates shifts in ribosomal occupancy "
                                                 "of transcripts from polysome fractionated RNA-Seq data.",
                                     prog="bin")
    optional = parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    required.add_argument("-x", type=str, default=None, metavar="MODE", choices=('create_manifest','run'),
                          help="specify which mode to execute; create_manifest or run")
    required.add_argument("-o", type=str, default=None, metavar="OUTDIR",
                          help="specify path of the desired output folder", required=True)
    optional.add_argument("-v", "--version", action='version', version='%(prog)s ' + __version__)
    optional.add_argument("--log", type=str, default='info', metavar="",
                          help="desired log level: DEBUG, INFO (Default), WARNING")
    parser._action_groups.append(optional)
    args = parser.parse_args()

    # Copies manifest file into the output folder.
    if args.x == 'create_manifest':
        manifest = open(args.o + 'manifest.txt', 'w')
        manifest.write(manifesto.text)
        samp_tbl = csv.writer(open(args.o + 'sample_table.csv', 'w'), delimiter = ',')
        samp_tbl.writerow(manifesto.sample_table)

    # Run the analysis pipeline using parameters specified in 'manifest.txt'.
    if args.x == 'run':

        # Creating sub-directories in output path
        for folder in ['logs','kallisto_output','sleuth_output','sherlock_output']:
            if not os.path.exists(args.o + '/' + folder):
                os.makedirs(args.o + '/' + folder)

        # Preparing logging console for __main__
        numeric_level = getattr(logging, args.log.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % args.log)
        logging.basicConfig(filename=args.o + '/logs/log.bin.' + time_stamp + '.txt',
                            level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s \t %(message)s',
                            filemode='w')
        logger = logging.getLogger(__name__)
        logger.debug('sherlock version: %s' % __version__)
        logger.debug('Input command: ' + " ".join(sys.argv))

        # Defining Handler to write messages to sys.stdout
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(numeric_level)
        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%y-%m-%d %H:%M:%S')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
        logger.info('Beginning analysis with sherlock ver=%s' % __version__)

        # Perform system check for necessary executables in PATH
        logger.debug('Performing system check to ensure necessary executables are installed.')
        system_check.sherlock_ready()

        # Parsing manifest.txt for parameters and experiment information
        logger.info('Parsing manifest.txt for parameters and experimental information.')
        metadata = manifesto.parse(args.o)

        # Check metadata for any inconsistencies before proceeding with analysis
        # TODO create method to check errors in manifest.txt

        # Check if kallisto index has been provided, if not create index using annotation file provided
        # TODO create method to check index or generate
        kallisto_ind = metadata['parameters']['k']['index']
        if kallisto_ind == '':
            logger.info('Please provide a kallisto index for the organism used in the study.')
            logger.debug('Abort: Missing kallisto index')
            sys.exit()

        # Run kallisto quant on all sample FASTQ files using desired parameters if needed
        if metadata['parameters']['k']['skip'] == 'no':
            for sample_num in metadata['samples'].keys():

                # Read dictionary into object
                sample_info = sherlock_classes.Sample_entry_read(metadata['samples'][sample_num])

                # Create output folder for kallisto output
                outf = args.o + 'kallisto_output/' + sample_info.id
                if not os.path.exists(outf):
                    os.makedirs(outf)
                open(outf + '/log.txt', 'a').close()

                # Store kallisto output path into sample_dictionary
                metadata['samples'][sample_num]['kallisto_outpath'] = outf

                # Run kallisto quant on file
                logger.info('Running kallisto quant on sample %i out of %i' % (sample_num, len(metadata['samples'])))

                retcode = kallisto_wrapper.quant(metadata['parameters']['k'], kallisto_ind, outf, sample_info.kallisto_file_in)

                # Check if kallisto quant exited with error
                if retcode != 0:
                    logger.info('Error: kallisto quant exited with code %i' % retcode)
                    sys.exit(1)

        elif metadata['parameters']['k']['skip'] == 'yes':
            logger.info('Skipping kallisto quant step on samples...')

            # Store kallisto output path into sample_dictionary
            for sample_num in metadata['samples'].keys():

                # Read dictionary into object
                sample_info = sherlock_classes.Sample_entry_read(metadata['samples'][sample_num])

                # Check and store kallisto output path into sample_dictionary
                outf = args.o + 'kallisto_output/' + sample_info.id
                if not os.path.exists(outf):
                    logger.info('Error: Expected directory of kallisto output for sample %i not found' % sample_num)
                    sys.exit(2)
                metadata['samples'][sample_num]['kallisto_outpath'] = args.o + 'kallisto_output/' + sample_info.id + '/'

        else:
            logger.info('Please provide valid options for "k:skip" in manifest.txt file.')

        # Preparing directories and sleuth metadata.txt files for sleuth analysis
        # TODO Create a method to check for proper directories present in case of skip
        logger.info('Preparing directories and files for sleuth analysis.')
        sleuth_paths = sherlock_methods.sleuth_setup(metadata['samples'], args.o + 'sleuth_output/')

        # Perform sleuth differential expression tests between fractions in each group
        if metadata['parameters']['sl']['skip'] == 'no':
            logger.info('Performing sleuth analysis within group fractions.')
            sherlock_methods.sleuth_execute(sleuth_paths)
            logger.debug('Sleuth analysis on all comparisons are complete.')

        elif metadata['parameters']['sl']['skip'] == 'yes':
            logger.info('Skipping sleuth analysis within group fractions...')

        else:
            logger.info('Please provide valid options for "sl:skip" in manifest.txt file.')

        # Summarize sleuth results
        logger.info('Consolidating sleuth analysis output.')
        sherlock_methods.sleuth_consolidate(args.o + 'sleuth_output/', sleuth_paths)

        # Perform sherlock analysis
        logger.info('Performing sherlock analysis to quantitate shifts of transcripts in polysomes.')
        sherlock_methods.sherlock_compare(args.o, metadata['comparisons'])