package photobox.domain;

import java.util.ArrayList;

public class PbMarker {
    private int markerId;
    private int markerEdgeId;
    private double x;
    private double y;
    private double z;
    private ArrayList<PbMarkerPosition> markerPositions;
    private int id;

    public PbMarker() {
        this.markerPositions = new ArrayList<PbMarkerPosition>();
    }

    public PbMarker(int markerId, int markerEdgeId) {
        this();
        this.markerId = markerId;
        this.markerEdgeId = markerEdgeId;
    }

    public PbMarker(int markerId, int markerEdgeId, double x, double y, double z) {
        this(markerId, markerEdgeId);
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public int getMarkerId() {
        return this.markerId;
    }

    public int getMarkerEdgeId() {
        return this.markerEdgeId;
    }

    public double getX() {
        return this.x;
    }

    public double getY() {
        return this.y;
    }

    public double getZ() {
        return this.z;
    }

    public void addMarkerPosition(PbMarkerPosition markerPosition) {
        this.markerPositions.add(markerPosition);
    }

    public String toString() {
        return this.markerId + "-" + this.markerEdgeId;
    }

    public void setId(int id) {
        this.id = id;
    }

    public PbMarkerPosition[] getMarkerPositions() {
        return this.markerPositions.toArray(new PbMarkerPosition[markerPositions.size()]);
    }

    public int getId() {
        return id;
    }
}
