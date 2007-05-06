#! /usr/bin/env /usr/local/bin/python

#    $Id: map_walker.py 935 2007-03-21 13:49:34Z johnholland $

import sys
from os.path import dirname, abspath, join, isdir, isfile
import pyx12.params 

def getMapPath():
    """
    First, try relative path
    Then look in standard installation location
    """
    params = pyx12.params.params()
    map_path = params.get('map_path')
    return map_path
