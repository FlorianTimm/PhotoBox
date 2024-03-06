import pytest

from camera_aruco import Aruco
from cv2 import imread
from cv2 import cvtColor, COLOR_BGR2GRAY


class TestCameraAruco:
    img = imread('tests/test.jpg')
    img_sw = cvtColor(img, COLOR_BGR2GRAY)

    @pytest.fixture
    def aruco(self):
        return Aruco()

    def test_detect_from_rgb(self, aruco: Aruco):
        marker = aruco.detect_from_rgb(self.img)
        print(len(marker))
        assert len(marker) == 24
        assert type(marker[0]['marker']) == int
        assert type(marker[0]['ecke']) == int
        assert type(marker[0]['x']) == float
        assert type(marker[0]['y']) == float
        assert marker[0]['x'] >= 0
        assert marker[0]['y'] >= 0
        assert marker[0]['x'] <= 4608
        assert marker[0]['y'] <= 2592

    def test_detect(self, aruco):
        marker = aruco.detect(self.img_sw)
        assert len(marker) == 24
        assert type(marker[0]['marker']) == int
        assert type(marker[0]['ecke']) == int
        assert type(marker[0]['x']) == float
        assert type(marker[0]['y']) == float
        assert marker[0]['x'] >= 0
        assert marker[0]['y'] >= 0
        assert marker[0]['x'] <= 4608
        assert marker[0]['y'] <= 2592
