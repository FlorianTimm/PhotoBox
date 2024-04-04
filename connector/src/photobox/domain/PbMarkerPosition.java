package photobox.domain;

public class PbMarkerPosition {
    private PbImage image;
    private double x;
    private double y;

    public PbMarkerPosition(PbImage image, double x, double y) {
        this.image = image;
        this.x = x;
        this.y = y;
    }

    public double getX() {
        return x;
    }

    public double getY() {
        return y;
    }

    public PbImage getImage() {
        return image;
    }

}
