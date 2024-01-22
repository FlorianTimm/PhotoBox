from cv2.aruco import Dictionary_create, CORNER_REFINE_SUBPIX, detectMarkers, DetectorParameters
import pandas as pd
import numpy as np
from cv2 import cvtColor, COLOR_BGR2GRAY, imread
import Metashape  # Metashape Pro 1.8.5
from tkinter import filedialog, Tk
from glob import glob
from Metashape import Calibration

root = Tk()
root.withdraw()
folder_selected = '/mnt/ssd_daten/Studium/MScGeodaesieGeoinformatik/4_Thesis/bilderserien/Masstab'
# folder_selected = filedialog.askdirectory()
print(folder_selected)

doc = Metashape.Document()
doc.save(path=(folder_selected + "/project.psz"))
print(doc)
chunk = doc.addChunk()

files = glob(folder_selected+"/*.jpg")
files.extend(glob(folder_selected+"/*.JPG"))
files.extend(glob(folder_selected+"/*.jpeg"))
files.extend(glob(folder_selected+"/*.JPEG"))

files.sort()

chunk.addPhotos(files)

aruco_dict = Dictionary_create(32, 3)
parameter = DetectorParameters.create()
parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX
LUT_IN = [0, 158, 216, 255]
LUT_OUT = [0, 22, 80, 176]
lut = np.interp(np.arange(0, 256),
                LUT_IN, LUT_OUT).astype(np.uint8)

marker: dict[str, Metashape.Marker] = {}
for j, img in enumerate(files):
    imgCV = imread(img)
    gray = cvtColor(imgCV, COLOR_BGR2GRAY)
    tmp_corners, tmp_ids, t = detectMarkers(
        gray, aruco_dict, parameters=parameter)
    for c, i in zip(tmp_corners, tmp_ids):
        for k in range(len(c[0])):
            m = i[0]*10+k
            if str(m) not in marker:
                marker[str(m)] = chunk.addMarker()
                marker[str(m)].label = str(m)
            marker[str(m)].projections[chunk.cameras[j]] = Metashape.Marker.Projection(
                Metashape.Vector(c[0][k]), True)

keys = set([int(i) // 10 for i in marker.keys()])

for i in keys:

    i1 = marker[str(i*10+0)]
    i2 = marker[str(i*10+1)]
    i3 = marker[str(i*10+2)]
    i4 = marker[str(i*10+3)]

    b = 0.0343

    for m1, m2, l in [(i1, i2, b), (i2, i3, b), (i3, i4, b), (i4, i1, b), (i1, i3, b*2**0.5), (i2, i4, b*2**0.5)]:
        sb = chunk.addScalebar(m1, m2)
        sb.reference.distance = l
        sb.reference.accuracy = 0.0005
        sb.label = "Scalebar " + str(m1.label) + "-" + str(m2.label)


"""for c in chunk.cameras:
    user_calib = Calibration()
    user_calib.f = 3411.03821
    user_calib.cx = -9.86464
    user_calib.cy = 23.6335
    user_calib.k1 = 0.068886
    user_calib.k2 = -0.129288
    user_calib.k3 = 0.0786447
    user_calib.p1 = -0.00168585
    user_calib.p2 = 0.00179698
    c.sensor.user_calib = user_calib"""

chunk.importReference(folder_selected+"/marker.txt",
                      format=Metashape.ReferenceFormatCSV, columns="nxyz", delimiter=";", skip_rows=2)

chunk.matchPhotos(downscale=3, generic_preselection=True,
                  reference_preselection=False)
chunk.alignCameras()


"""
chunk.buildDepthMaps(downscale=4, filter_mode=Metashape.AggressiveFiltering)
chunk.buildDenseCloud()
chunk.buildModel(surface_type=Metashape.Arbitrary,
                 interpolation=Metashape.EnabledInterpolation)
chunk.buildUV(mapping_mode=Metashape.GenericMapping)
#chunk.buildTexture(blending_mode=Metashape.MosaicBlending, texture_size=4096)
"""

doc.save()
