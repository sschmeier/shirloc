"""
Contains methods which act as python wrappers for kallisto, a psuedoaligner for RNA-Seq data.
"""

import os
import logging


def index():
    pass


def quant(args, ind, outd, files):

    # Setup logger
    logger = logging.getLogger(__name__)

    # Base command for kallisto quant mode
    command = 'kallisto quant {options} -i {index} -o {output_dir} {fastq_files}'
    log_info = ' > {output_dir}/log.txt 2>&1'

    # Initialize format dictionary, f
    f = dict(options='', index='', output_dir='', fastq_files='')

    # Format options key in f
    optional_args = ''
    if args['bias'] == 'yes':
        optional_args = '--bias '

    if args['bootstrap-samples'] != '0':
        optional_args += '-b ' + args['bootstrap-samples'] + ' '

    if args['seed'] != '42':
        optional_args += '--seed ' + args['seed'] + ' '

    if args['plaintext'] == 'yes':
        optional_args += '--plaintext '

    if args['fusion'] == 'yes':
        optional_args += '--fusion '

    if args['single'] == 'yes':
        optional_args += '--single '

    if args['single-overhang'] == 'yes':
        optional_args += '--single-overhang '

    if args['strand'] == 'rf-stranded':
        optional_args += '--rf-stranded '

    if args['strand'] == 'fr-stranded':
        optional_args += 'fr-stranded '

    if args['fragment-length'] != '':
        optional_args += '-l ' + args['fragment-length'] + ' '

    if args['sd'] != '':
        optional_args += '-s ' + args['sd'] + ' '

    if args['threads'] != '':
        optional_args += '-t ' + args['threads'] + ' '

    if args['pseudobam'] == 'yes':
        optional_args += '--pseudobam '

    if args['genomebam'] == 'yes':
        optional_args += '--genomebam '

    if args['gtf'] != '':
        optional_args += '--gtf ' + args['gtf'] + ' '

    if args['chromosomes'] != '':
        optional_args += '--chromosomes' + args['chromosomes'] + ' '

    f['options'] = optional_args.strip(' ')

    # Store index path into format dictionary
    f['index'] = ind

    # Store output directory path into format dictionary
    f['output_dir'] = outd

    # Store fasta file path into format dictionary
    f['fastq_files'] = files

    # Execute command
    logger.debug('kallisto command: %s' % command.format_map(f))
    retcode = os.system(command.format_map(f) + log_info.format_map(f))

    # Return exit code of process
    return retcode

def setup():
    pass
