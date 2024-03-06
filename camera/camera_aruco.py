from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers, detectMarkers
from cv2 import cvtColor, COLOR_BGR2GRAY


class Aruco:
    def __init__(self):
        self.parameter = DetectorParameters.create()
        self.parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX
        self.dict = Dictionary_create(32, 3)

    def detect_from_rgb(self, image: bytes) -> list[dict[str, int | float]]:
        img = cvtColor(image, COLOR_BGR2GRAY)
        return self.detect(img)

    def detect(self, image: bytes) -> list[dict[str, int | float]]:
        corners, ids, _ = detectMarkers(
            image, self.dict, parameters=self.parameter)
        if ids is None:
            return []
        marker = [{'marker': int(id_[0]),
                   'ecke': eid,
                   'x': float(e[0]),
                   'y': float(e[1])} for ecke, id_ in zip(corners, ids) for eid, e in enumerate(ecke[0])]
        print("Found Aruco: ", len(marker))
        return marker