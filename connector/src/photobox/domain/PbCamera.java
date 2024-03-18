package photobox.domain;

import java.util.ArrayList;

public class PbCamera {
    private int cameraId = -1;
    private String cameraName;
    private int width = 4608;
    private int height = 3456;
    private double focalLength = 3451.31891;
    private double principalPointX = 2.75058;
    private double principalPointY = 28.0038;
    private double k[] = { -0.0365779, 0.792583, -2.57419, 2.54451 };
    private double p[] = { 0.00613243, 0.00806988 };
    private ArrayList<PbImage> images;

    public PbCamera(String cameraName) {
        this.cameraName = cameraName;
        this.images = new ArrayList<PbImage>();
    }

    public void setCameraId(int cameraId) {
        this.cameraId = cameraId;
    }

    public boolean isCameraIdSet() {
        return this.cameraId >= 0;
    }

    public int getCameraId() {
        return cameraId;
    }

    public String getCameraName() {
        return cameraName;
    }

    public double getFocalLength() {
        return focalLength;
    }

    public double getPrincipalPointX() {
        return principalPointX;
    }

    public double getPrincipalPointY() {
        return principalPointY;
    }

    public PbImage[] getImages() {
        return images.toArray(new PbImage[images.size()]);
    }

    public void addImage(PbImage image) {
        this.images.add(image);
    }

    public double[] getK() {
        return k;
    }

    public double[] getP() {
        return p;
    }

    public String toString() {
        return this.cameraName;
    }

    public int getWidth() {
        return width;
    }

    public int getHeight() {
        return height;
    }

}
