package photobox.domain;

import java.io.File;

public class PbImage {
    private int imageId;
    private File file;
    private PbCamera camera;
    private double lensPosition;

    public PbImage(PbCamera camera, File file, double lensPosition) {
        this.camera = camera;
        this.file = file;
        this.lensPosition = lensPosition;
    }

    public int getImageId() {
        return imageId;
    }

    public File getFile() {
        return file;
    }

    public double getLensPosition() {
        return lensPosition;
    }

    public PbCamera getCamera() {
        return camera;
    }

    public void setId(int index) {
        this.imageId = index;
    }

    public double getFocalLength() {
        return this.camera.getFocalLength(this.lensPosition);
    }

    public double getPrincipalPointX() {
        return this.camera.getPrincipalPointX(this.lensPosition);
    }

    public double getPrincipalPointY() {
        return this.camera.getPrincipalPointY(this.lensPosition);
    }

    public double[] getK() {
        return this.camera.getK(this.lensPosition);
    }

    public double[] getP() {
        return this.camera.getP(this.lensPosition);
    }
}
