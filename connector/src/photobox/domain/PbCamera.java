package photobox.domain;

import java.util.ArrayList;

public class PbCamera {
    private int cameraId = -1;
    private String cameraName;
    private int width = 4608;
    private int height = 3456;
    private double focalLength = 3387.30;
    private double focalLengthFactor = 21.65;
    private double principalPointX = 9.43;
    private double principalPointXFactor = 0.28;
    private double principalPointY = 26.77;
    private double principalPointYFactor = -1.14;
    private double k[] = { -0.008054, 0.233690, -0.384440, 0. };
    private double kFactor[] = { 0.018608, -0.104750, 0.131100, 0. };
    private double p[] = { 0., 0. };
    private double pFactor[] = { 0., 0. };
    private ArrayList<PbImage> images;
    private PbCameraPosition position;

    public PbCamera(String cameraName) {
        this.cameraName = cameraName;
        this.images = new ArrayList<PbImage>();
    }

    public void setPosition(PbCameraPosition position) {
        this.position = position;
    }

    public PbCameraPosition getPosition() {
        return position;
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

    public double getFocalLength(double lensPosition) {
        return focalLength + focalLengthFactor * lensPosition;
    }

    public double getPrincipalPointX(double lensPosition) {
        return principalPointX + principalPointXFactor * lensPosition;
    }

    public double getPrincipalPointY(double lensPosition) {
        return principalPointY + principalPointYFactor * lensPosition;
    }

    public PbImage[] getImages() {
        return images.toArray(new PbImage[images.size()]);
    }

    public void addImage(PbImage image) {
        this.images.add(image);
    }

    public double[] getK(double lensPosition) {
        double[] k = new double[4];
        for (int i = 0; i < 3; i++) {
            k[i] = this.k[i] + this.kFactor[i] * lensPosition;
        }
        return k;
    }

    public double[] getP(double lensPosition) {
        double[] p = new double[2];
        for (int i = 0; i < 2; i++) {
            p[i] = this.p[i] + this.pFactor[i] * lensPosition;
        }
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
