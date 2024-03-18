package photobox.domain;

public class PbMarkerPosition {
    private PbMarker marker;
    private PbImage image;
    private double x;
    private double y;

    public PbMarkerPosition(PbMarker marker, PbImage image, double x, double y) {
        this.marker = marker;
        this.image = image;
        this.x = x;
        this.y = y;
    }

    public PbMarker getMarker() {
        return this.marker;
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
