from cv2.aruco import Dictionary_create, CORNER_REFINE_SUBPIX, detectMarkers, DetectorParameters
import pandas as pd
import numpy as np
from cv2 import cvtColor, COLOR_BGR2GRAY, imread
import Metashape  # Metashape Pro 1.8.5
from tkinter import filedialog, Tk
from glob import glob

root = Tk()
root.withdraw()
folder_selected = '/mnt/ssd_daten/Studium/MScGeodaesieGeoinformatik/hcuCloud/4_Thesis/bilderserien/wuerfel10'
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


"""
chunk.matchPhotos(downscale=1, generic_preselection=True,
                  reference_preselection=False)
chunk.alignCameras()
chunk.buildDepthMaps(downscale=4, filter_mode=Metashape.AggressiveFiltering)
chunk.buildDenseCloud()
chunk.buildModel(surface_type=Metashape.Arbitrary,
                 interpolation=Metashape.EnabledInterpolation)
chunk.buildUV(mapping_mode=Metashape.GenericMapping)
#chunk.buildTexture(blending_mode=Metashape.MosaicBlending, texture_size=4096)
"""

doc.save()
