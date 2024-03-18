package photobox.domain;

import java.io.File;

public class PbImage {
    private int imageId;
    private File file;
    private PbCamera camera;
    private double lensPosition;
    private double x;
    private double y;
    private double z;
    private double roll;
    private double pitch;
    private double yaw;

    public PbImage(PbCamera camera, File file) {
        this.camera = camera;
        this.file = file;
    }

    public void setPosition(double x, double y, double z) {
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public void setOrientation(double roll, double pitch, double yaw) {
        this.roll = roll;
        this.pitch = pitch;
        this.yaw = yaw;
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

    public double getX() {
        return x;
    }

    public double getY() {
        return y;
    }

    public double getZ() {
        return z;
    }

    public double getRoll() {
        return roll;
    }

    public double getPitch() {
        return pitch;
    }

    public double getYaw() {
        return yaw;
    }

    public PbCamera getCamera() {
        return camera;
    }

    public void setId(int index) {
        this.imageId = index;
    }
}
