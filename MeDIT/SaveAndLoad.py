import numpy as np
import h5py
import os
import SimpleITK as sitk
import pydicom
import imageio
from copy import deepcopy
from collections import OrderedDict
import matplotlib.pyplot as plt

from Normalize import Normalize01

def SaveArrayAsImage(image, store_path, roi=0, dip=300):
    # image = Normalize01(image)
    plt.imshow(image, cmap='Greys_r')
    if np.max(roi) != 0:
        plt.contour(roi, colors='g')
    plt.axis('off')
    plt.gca().set_axis_off()
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.savefig(store_path, format='tif', dpi=300, bbox_inches='tight', pad_inches = 0)
    plt.close()

def SaveH5(store_path, data, tag, data_type=np.float32):
    if not isinstance(data, list):
        data = [data]
    if not isinstance(tag, list):
        tag = [tag]
    if not isinstance(data_type, list):
        data_type = [data_type]

    file = h5py.File(store_path, 'w')
    for index in range(len(dat)):
        file.create_dataset(tag[index], data=data[index], dtype=data_type[index])
    file.close()

def LoadH5(data_path, tag, data_type=np.float32):
    file = h5py.File(data_path, 'r')
    data = np.asarray(file[tag], dtype=data_type)
    file.close()
    return data

def LoadNiiData(file_path, dtype=np.float32, is_show_info=False):
    image = sitk.ReadImage(file_path)
    data = np.asarray(sitk.GetArrayFromImage(image), dtype=dtype)

    data = np.transpose(data)
    show_data = np.swapaxes(data, 0, 1)

    if is_show_info:
        print('Image size is: ', image.GetSize())
        print('Image resolution is: ', image.GetSpacing())
        print('Image direction is: ', image.GetDirection())

    return image, data, show_data

def LoadNiiHeader(file_path, is_show_info=True):
    reader = sitk.ImageFileReader()
    reader.SetFileName(file_path)
    reader.LoadPrivateTagsOn()
    reader.ReadImageInformation()
    info = OrderedDict()
    for k in reader.GetMetaDataKeys():
        v = reader.GetMetaData(k)
        info[k] = v

    dimension = int(info['dim[0]'])
    spaceing = []
    center = [float(info['qoffset_x']), float(info['qoffset_y']), float(info['qoffset_z'])]
    shape = []
    for d in range(dimension):
        spaceing.append(float(info['pixdim[' + str(d+1) + ']']))
        shape.append(float(info['dim[' + str(d + 1) + ']']))

    info['dimension'] = dimension
    info['spacing'] = spaceing
    info['center'] = center
    info['shape'] = shape

    if is_show_info:
        print(info)

    return info

def GetDataFromSimpleITK(image, dtype=np.float16):
    data = np.asarray(sitk.GetArrayFromImage(image), dtype=dtype)
    data = np.transpose(data)
    show_data = np.swapaxes(data, 0, 1)

    return data, show_data

def SaveDicomByRefer(data, dicom_data, store_path):
    if isinstance(dicom_data, str) and dicom_data[-3:] == 'dcm':
        dicom_data = pydicom.dcmread(dicom_data)

    try:
        assert(data.shape == dicom_data.pixel_array.shape)
    except:
        print("The data shape must be same with the shape of the dicom data. ")

    ds = deepcopy(dicom_data)
    ds.PixelData = data.tostring()
    ds.save_as(store_path)

def GetDicomData(data_path):
    ds = pydicom.dcmread(data_path)
    data = ds.pixel_array

    return ds, data

def SaveAsGif(image_list, store_path, duration=1):
    gif = []
    for image in image_list:
        gif.append(deepcopy(image))

    imageio.mimsave(store_path, gif, duration=duration)

def LoadROI(file_path):
    suffix = os.path.splitext(file_path)[1]
    if suffix == 'roi':
        return read_roi_file(file_path)
    elif suffix == 'zip':
        return read_roi_zip(file_path)
    else:
        print('Only read .roi and .zip file')
        return None

####################################################################
'''
The following code was copyed from  https://github.com/hadim/read-roi. If I need to fork the raw source of the code 
form GitHub, please let me know. 
'''
import struct
import zipfile
import logging

__all__ = ['read_roi_file', 'read_roi_zip']
OFFSET = dict(VERSION_OFFSET=4,
              TYPE=6,
              TOP=8,
              LEFT=10,
              BOTTOM=12,
              RIGHT=14,
              N_COORDINATES=16,
              X1=18,
              Y1=22,
              X2=26,
              Y2=30,
              XD=18,
              YD=22,
              WIDTHD=26,
              HEIGHTD=30,
              STROKE_WIDTH=34,
              SHAPE_ROI_SIZE=36,
              STROKE_COLOR=40,
              FILL_COLOR=44,
              SUBTYPE=48,
              OPTIONS=50,
              ARROW_STYLE=52,
              ELLIPSE_ASPECT_RATIO=52,
              ARROW_HEAD_SIZE=53,
              ROUNDED_RECT_ARC_SIZE=54,
              POSITION=56,
              HEADER2_OFFSET=60,
              COORDINATES=64)

ROI_TYPE = dict(polygon=0,
                rect=1,
                oval=2,
                line=3,
                freeline=4,
                polyline=5,
                noRoi=6,
                freehand=7,
                traced=8,
                angle=9,
                point=10)

OPTIONS = dict(SPLINE_FIT=1,
               DOUBLE_HEADED=2,
               OUTLINE=4,
               OVERLAY_LABELS=8,
               OVERLAY_NAMES=16,
               OVERLAY_BACKGROUNDS=32,
               OVERLAY_BOLD=64,
               SUB_PIXEL_RESOLUTION=128,
               DRAW_OFFSET=256)

HEADER_OFFSET = dict(C_POSITION=4,
                     Z_POSITION=8,
                     T_POSITION=12,
                     NAME_OFFSET=16,
                     NAME_LENGTH=20,
                     OVERLAY_LABEL_COLOR=24,
                     OVERLAY_FONT_SIZE=28,
                     AVAILABLE_BYTE1=30,
                     IMAGE_OPACITY=31,
                     IMAGE_SIZE=32,
                     FLOAT_STROKE_WIDTH=36)

SUBTYPES = dict(TEXT=1,
                ARROW=2,
                ELLIPSE=3,
                IMAGE=4)

def get_byte(data, base):
    if isinstance(base, int):
        return data[base]
    elif isinstance(base, list):
        return [data[b] for b in base]

def get_short(data, base):
    b0 = data[base]
    b1 = data[base + 1]
    n = (b0 << 8) + b1
    return n

def get_int(data, base):
    b0 = data[base]
    b1 = data[base + 1]
    b2 = data[base + 2]
    b3 = data[base + 3]
    n = ((b0 << 24) + (b1 << 16) + (b2 << 8) + b3)
    return n

def get_float(data, base):
    s = struct.pack('I', get_int(data, base))
    return struct.unpack('f', s)[0]

def read_roi_file(fpath):
    """
    """

    if isinstance(fpath, zipfile.ZipExtFile):
        data = fpath.read()
        name = os.path.splitext(os.path.basename(fpath.name))[0]
    elif isinstance(fpath, str):
        fp = open(fpath, 'rb')
        data = fp.read()
        fp.close()
        name = os.path.splitext(os.path.basename(fpath))[0]
    else:
        logging.error("Can't read {}".format(fpath))
        return None

    logging.debug("Read ROI for \"{}\"".format(name))

    size = len(data)
    code = '>'

    roi = {}

    magic = get_byte(data, list(range(4)))
    magic = "".join([chr(c) for c in magic])

    # TODO: raise error if magic != 'Iout'

    version = get_short(data, OFFSET['VERSION_OFFSET'])
    roi_type = get_byte(data, OFFSET['TYPE'])
    subtype = get_short(data, OFFSET['SUBTYPE'])
    top = get_short(data, OFFSET['TOP'])
    left = get_short(data, OFFSET['LEFT'])

    if top > 6000:
        top -= 2**16
    if left > 6000:
        left -= 2**16

    bottom = get_short(data, OFFSET['BOTTOM'])
    right = get_short(data, OFFSET['RIGHT'])
    width = right - left
    height = bottom - top
    n_coordinates = get_short(data, OFFSET['N_COORDINATES'])
    options = get_short(data, OFFSET['OPTIONS'])
    position = get_int(data, OFFSET['POSITION'])
    hdr2Offset = get_int(data, OFFSET['HEADER2_OFFSET'])

    logging.debug("n_coordinates: {n_coordinates}")
    logging.debug("position: {position}")
    logging.debug("options: {options}")

    sub_pixel_resolution = (options == OPTIONS['SUB_PIXEL_RESOLUTION']) and version >= 222
    draw_offset = sub_pixel_resolution and (options == OPTIONS['DRAW_OFFSET'])
    sub_pixel_rect = version >= 223 and sub_pixel_resolution and (
        roi_type == ROI_TYPE['rect'] or roi_type == ROI_TYPE['oval'])

    logging.debug("sub_pixel_resolution: {sub_pixel_resolution}")
    logging.debug("draw_offset: {draw_offset}")
    logging.debug("sub_pixel_rect: {sub_pixel_rect}")

    # Untested
    if sub_pixel_rect:
        xd = getFloat(data, OFFSET['XD'])
        yd = getFloat(data, OFFSET['YD'])
        widthd = getFloat(data, OFFSET['WIDTHD'])
        heightd = getFloat(data, OFFSET['HEIGHTD'])
        logging.debug("Entering in sub_pixel_rect")

    # Untested
    if hdr2Offset > 0 and hdr2Offset + HEADER_OFFSET['IMAGE_SIZE'] + 4 <= size:
        channel = get_int(data, hdr2Offset + HEADER_OFFSET['C_POSITION'])
        slice = get_int(data, hdr2Offset + HEADER_OFFSET['Z_POSITION'])
        frame = get_int(data, hdr2Offset + HEADER_OFFSET['T_POSITION'])
        overlayLabelColor = get_int(data, hdr2Offset + HEADER_OFFSET['OVERLAY_LABEL_COLOR'])
        overlayFontSize = get_short(data, hdr2Offset + HEADER_OFFSET['OVERLAY_FONT_SIZE'])
        imageOpacity = get_byte(data, hdr2Offset + HEADER_OFFSET['IMAGE_OPACITY'])
        imageSize = get_int(data, hdr2Offset + HEADER_OFFSET['IMAGE_SIZE'])
        logging.debug("Entering in hdr2Offset")

    is_composite = get_int(data, OFFSET['SHAPE_ROI_SIZE']) > 0

    # Not implemented
    if is_composite:
        if version >= 218:
            pass
        if channel > 0 or slice > 0 or frame > 0:
            pass

    if roi_type == ROI_TYPE['rect']:
        roi = {'type': 'rectangle'}

        if sub_pixel_rect:
            roi.update(dict(left=xd, top=yd, width=widthd, height=heightd))
        else:
            roi.update(dict(left=left, top=top, width=width, height=height))

        roi['arc_size'] = get_short(data, OFFSET['ROUNDED_RECT_ARC_SIZE'])

    elif roi_type == ROI_TYPE['oval']:
        roi = {'type': 'oval'}

        if sub_pixel_rect:
            roi.update(dict(left=xd, top=yd, width=widthd, height=heightd))
        else:
            roi.update(dict(left=left, top=top, width=width, height=height))

    elif roi_type == ROI_TYPE['line']:
        roi = {'type': 'line'}

        x1 = get_float(data, OFFSET['X1'])
        y1 = get_float(data, OFFSET['Y1'])
        x2 = get_float(data, OFFSET['X2'])
        y2 = get_float(data, OFFSET['Y2'])

        if subtype == SUBTYPES['ARROW']:
            # Not implemented
            pass
        else:
            roi.update(dict(x1=x1, x2=x2, y1=y1, y2=y2))
            roi['draw_offset'] = draw_offset

    elif roi_type in [ROI_TYPE[t] for t in ["polygon", "freehand", "traced", "polyline", "freeline", "angle", "point"]]:
        x = []
        y = []
        base1 = OFFSET['COORDINATES']
        base2 = base1 + 2 * n_coordinates
        for i in range(n_coordinates):
            xtmp = get_short(data, base1 + i * 2)
            ytmp = get_short(data, base2 + i * 2)
            x.append(left + xtmp)
            y.append(top + ytmp)

        if sub_pixel_resolution:
            xf = []
            yf = []
            base1 = OFFSET['COORDINATES'] + 4 * n_coordinates
            base2 = base1 + 4 * n_coordinates
            for i in range(n_coordinates):
                xf.append(get_float(data, base1 + i * 4))
                yf.append(get_float(data, base2 + i * 4))

        if roi_type == ROI_TYPE['point']:
            roi = {'type': 'point'}

            if sub_pixel_resolution:
                roi.update(dict(x=xf, y=yf, n=n_coordinates))
            else:
                roi.update(dict(x=x, y=y, n=n_coordinates))

        if roi_type == ROI_TYPE['polygon']:
            roi = {'type': 'polygon'}

        elif roi_type == ROI_TYPE['freehand']:
            roi = {'type': 'freehand'}
            if subtype == SUBTYPES['ELLIPSE']:
                ex1 = get_float(data, OFFSET['X1'])
                ey1 = get_float(data, OFFSET['Y1'])
                ex2 = get_float(data, OFFSET['X2'])
                ey2 = get_float(data, OFFSET['Y2'])
                roi['aspect_ratio'] = get_float(
                    data, OFFSET['ELLIPSE_ASPECT_RATIO'])
                roi.update(dict(ex1=ex1, ey1=ey1, ex2=ex2, ey2=ey2))

        elif roi_type == ROI_TYPE['traced']:
            roi = {'type': 'traced'}

        elif roi_type == ROI_TYPE['polyline']:
            roi = {'type': 'polyline'}

        elif roi_type == ROI_TYPE['freeline']:
            roi = {'type': 'freeline'}

        elif roi_type == ROI_TYPE['angle']:
            roi = {'type': 'angle'}

        else:
            roi = {'type': 'freeroi'}

        if sub_pixel_resolution:
            roi.update(dict(x=xf, y=yf, n=n_coordinates))
            #roi.update(dict(x=x, y=y, n=n_coordinates))
        else:
            roi.update(dict(x=x, y=y, n=n_coordinates))
    else:
        # TODO: raise an error for 'Unrecognized ROI type'
        pass

    roi['name'] = name

    if version >= 218:
        # Not implemented
        # Read stroke width, stroke color and fill color
        pass

    if version >= 218 and subtype == SUBTYPES['TEXT']:
        # Not implemented
        # Read test ROI
        pass

    if version >= 218 and subtype == SUBTYPES['IMAGE']:
        # Not implemented
        # Get image ROI
        pass

    roi['position'] = position
    if channel > 0 or slice > 0 or frame > 0:
        roi['position'] = dict(channel=channel, slice=slice, frame=frame)

    return {name: roi}

def read_roi_zip(zip_path):
    """
    """
    from collections import OrderedDict
    rois = OrderedDict()
    zf = zipfile.ZipFile(zip_path)
    for n in zf.namelist():
        rois.update(read_roi_file(zf.open(n)))
    return rois



