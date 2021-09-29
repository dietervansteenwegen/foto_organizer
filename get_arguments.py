import argparse

def get_arguments()->tuple:
    """Get and check user arguments.

    """
    input_path = None
    output_path = None
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', 
                        action = 'store',  # stores argument in dest variable, optionally doing type conversion/checking
                        dest='input_path', 
                        help = 'Set the path where the source files are stored right now',
                        type = str)
    parser.add_argument('--input', 
                        action = 'store', 
                        dest='input_path', 
                        help = 'Set the path where the source files are stored right now',
                        type = str)
    parser.add_argument('-o', 
                        action = 'store', 
                        dest='output_path', 
                        help = 'Set the path where the target files should be stored (in subfolders)',
                        type = str)
    parser.add_argument('--output', 
                        action = 'store', 
                        dest='output_path', 
                        help = 'Set the path where the target files should be stored (in subfolders)',
                        type = str)
    parser.add_argument('-c', 
                        action = 'store_true',  # sets dest variable to True if flag/arg is added
                        default = False,
                        dest='camera_info', 
                        help = 'If set, camera type is added in file name')
    parser.add_argument('-H', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'HDR',
                        help = 'If "HDR" is in original filename, add to output filename as well')
    parser.add_argument('-P', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'PORTRAIT',
                        help = 'If "PORTRAIT" is in original filename, add to output filename as well')
    parser.add_argument('-W', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'WA',
                        help = 'If "WA" is in original filename, add to output filename as well')
    parser.add_argument('-B', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'BURST',
                        help = 'If "BURST" is in original filename, add to output filename as well')
    parser.add_argument('-C', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'COVER',
                        help = 'If "COVER" is in original filename, add to output filename as well')
    parser.add_argument('-T', 
                        action = 'append_const',  # adds one predefined keyword to keywords list
                        default = [],
                        dest='keywords', 
                        const = 'TOP',
                        help = 'If "TOP" is in original filename, add to output filename as well')
    parser.add_argument('-K', 
                        action = 'append',  # each time -k is used, the argument is added to the list dest
                        dest='keywords', 
                        default = [],
                        help = 'Additional keywords to keep from original filename')
                        
    results = parser.parse_args()
    

    print('input: {}\noutput: {}\nkeywords: {}'.format(results.input_path, results.output_path, results.keywords))


    return (input_path, output_path)

get_arguments()