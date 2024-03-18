package photobox.domain;

import java.util.ArrayList;

public class PbCamera {
    private int cameraId = -1;
    private String cameraName;
    private int width = 4608;
    private int height = 3456;
    private double focalLength = 3421.29912;
    private double principalPointX = 14.3951;
    private double principalPointY = 32.3689;
    private double k[] = { 0.0646574, -0.0800227, 0.0181199, 0 };
    private double p[] = { 0.000629941, 0.00168843 };
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
