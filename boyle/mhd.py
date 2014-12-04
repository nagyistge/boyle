# -*- coding: utf-8 -*-
# ======================================================================
# Program:   Diffusion Weighted MRI Reconstruction
# Module:    $RCSfile: mhd_utils.py,v $
# Language:  Python
# Author:    $Author: bjian $
# Date:      $Date: 2008/10/27 05:55:55 $
# Version:   $Revision: 1.2 $
# Last Edited by alexsavio and oiertwo 2014/11/10
# ======================================================================

import os
import os.path as op
import numpy as np
import array
from functools import reduce


# the order of these tags matter
MHD_TAGS = ['ObjectType',
            'NDims',
            'BinaryData',
            'BinaryDataByteOrderMSB',
            'CompressedData',
            'CompressedDataSize',
            'TransformMatrix',
            'Offset',
            'CenterOfRotation',
            'AnatomicalOrientation',
            'ElementSpacing',
            'DimSize',
            'ElementType',
            'ElementDataFile',
            'Comment',
            'SeriesDescription',
            'AcquisitionDate',
            'AcquisitionTime',
            'StudyDate',
            'StudyTime']


MHD_TO_NUMPY_TYPE   = {'MET_FLOAT' : np.float,
                       'MET_UCHAR' : np.uint8,
                       'MET_CHAR'  : np.int8,
                       'MET_USHORT': np.uint8,
                       'MET_SHORT' : np.int8,
                       'MET_UINT'  : np.uint32,
                       'MET_INT'   : np.int32,
                       'MET_ULONG' : np.uint64,
                       'MET_ULONG' : np.int64,
                       'MET_FLOAT' : np.float32,
                       'MET_DOUBLE': np.float64}


NDARRAY_TO_ARRAY_TYPE = {np.float  : 'f',
                         np.uint8  : 'H',
                         np.int8   : 'h',
                         np.uint16 : 'I',
                         np.int16  : 'i',
                         np.uint32 : 'I',
                         np.int32  : 'i',
                         np.uint64 : 'I',
                         np.int64  : 'i',
                         np.float32: 'f',
                         np.float64: 'd',}


NUMPY_TO_MHD_TYPE = {v: k for k, v in MHD_TO_NUMPY_TYPE.items()}
#ARRAY_TO_NDARRAY_TYPE = {v: k for k, v in NDARRAY_TO_ARRAY_TYPE.items()}


def read_meta_header(filename):
    """Return a dictionary of meta data from meta header file"""
    fileIN = open(filename, "r")
    line = fileIN.readline()

    meta_dict = {}
    tag_flag = [False]*len(MHD_TAGS)
    while line:
        tags = str.split(line, '=')
        # print tags[0]
        for i in range(len(MHD_TAGS)):
            tag = MHD_TAGS[i]
            if (str.strip(tags[0]) == tag) and (not tag_flag[i]):
                # print tags[1]
                meta_dict[tag] = str.strip(tags[1])
                tag_flag[i] = True
        line = fileIN.readline()
    #  comment
    fileIN.close()
    return meta_dict


def load_raw_data_with_mhd(filename):
    meta_dict = read_meta_header(filename)
    dim       = int(meta_dict['NDims'])

    assert(meta_dict['ElementType'] in MHD_TO_NUMPY_TYPE)

    arr = [int(i) for i in meta_dict['DimSize'].split()]
    volume = reduce(lambda x, y: x*y, arr[0:dim-1], 1)

    pwd = op.dirname(filename)
    raw_file = meta_dict['ElementDataFile']
    data_file = op.join(pwd, raw_file)

    ndtype  = MHD_TO_NUMPY_TYPE[meta_dict['ElementType']]
    arrtype = NDARRAY_TO_ARRAY_TYPE[ndtype]

    with open(data_file, 'rb') as fid:
        binvalues = array.array(arrtype)
        binvalues.fromfile(fid, volume*arr[dim-1])

    data = np.array  (binvalues, ndtype)
    data = np.reshape(data, (arr[dim-1], volume))

    if dim == 3:
        # Begin 3D fix
        dimensions = [int(i) for i in meta_dict['DimSize'].split()]
        dimensions.reverse()
        data = data.reshape(dimensions)
        # End 3D fix

    return (data, meta_dict)


def write_meta_header(filename, meta_dict):
    header = ''
    # do not use tags = meta_dict.keys() because the order of tags matters
    for tag in MHD_TAGS:
        if tag in meta_dict.keys():
            header += '{} = {}\n'.format(tag, meta_dict[tag])
    f = open(filename, 'w')
    f.write(header)
    f.close()


def dump_raw_data(filename, data):
    """ Write the data into a raw format file. Big endian is always used. """
    if data.ndim == 3:
        # Begin 3D fix
        data = data.reshape([data.shape[0], data.shape[1]*data.shape[2]])
        # End 3D fix

    rawfile = open(filename, 'wb')
    a = array.array('f')
    for o in data:
        a.fromlist(list(o))
    # if is_little_endian():
    #     a.byteswap()
    a.tofile(rawfile)
    rawfile.close()


def write_mhd_file(mhdfile, data, shape):
    assert(mhdfile[-4:] == '.mhd')
    meta_dict = {}
    meta_dict['ObjectType'] = 'Image'
    meta_dict['BinaryData'] = 'True'
    meta_dict['BinaryDataByteOrderMSB'] = 'False'
    meta_dict['ElementType'] = NUMPY_TO_MHD_TYPE[data.dtype]
    meta_dict['NDims'] = str(len(shape))
    meta_dict['DimSize'] = ' '.join([str(i) for i in shape])
    meta_dict['ElementDataFile'] = os.path.split(mhdfile)[1].replace('.mhd', '.raw')
    write_meta_header(mhdfile, meta_dict)

    pwd = os.path.split(mhdfile)[0]
    if pwd:
        data_file = op.join(pwd, meta_dict['ElementDataFile'])
    else:
        data_file = meta_dict['ElementDataFile']

    dump_raw_data(data_file, data)