package photobox;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Iterator;

import org.json.JSONArray;
import org.json.JSONObject;

import photobox.domain.PbCamera;
import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class PhotoBoxFolderReader {

    private Connector connector;
    private String projectFolder;

    private ArrayList<PbCamera> cameras = new ArrayList<PbCamera>();
    private ArrayList<PbMarker> markers = new ArrayList<PbMarker>();
    private ArrayList<PbImage> images = new ArrayList<PbImage>();

    public PhotoBoxFolderReader(Connector connector, String projectFolder) {
        this.connector = connector;
        this.projectFolder = projectFolder;

        this.cameras = new ArrayList<PbCamera>();
        this.markers = new ArrayList<PbMarker>();
        this.images = new ArrayList<PbImage>();

        this.readPhotos();
        this.readMarkerCoordinates();
        this.readMarkerPositions();
    }

    private PbCamera getCameraByName(String hostname) {
        for (PbCamera camera : this.cameras) {
            if (camera.getCameraName().equals(hostname)) {
                return camera;
            }
        }
        return null;
    }

    private void readPhotos() {
        this.connector.log("Adding photos");
        try {
            File[] files = new File(this.projectFolder).listFiles();
            ArrayList<String> photoPathList = new ArrayList<String>();
            for (File file : files) {
                if (file.isFile() && file.getName().toLowerCase().endsWith(".jpg")) {
                    photoPathList.add(file.getAbsolutePath());

                    String filename = file.getName();
                    int index = filename.lastIndexOf(".");
                    int index_ = filename.lastIndexOf("_");
                    if (index_ > 0) {
                        index = index_;
                    }
                    String hostname = filename.substring(0, index);

                    PbCamera camera = this.getCameraByName(hostname);
                    if (camera == null) {
                        camera = new PbCamera(hostname);
                        this.cameras.add(camera);
                    }
                    PbImage image = new PbImage(camera, file);
                    camera.addImage(image);
                    this.images.add(image);
                }
            }
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add photos");
        }
    }

    private void readMarkerCoordinates() {

        try {
            // Read the JSON file
            String jsonFilePath = this.projectFolder + "/marker.json";
            String jsonContent = new String(Files.readAllBytes(Paths.get(jsonFilePath)));

            // Parse the JSON content
            JSONObject markerFileJson = new JSONObject(jsonContent);
            Iterator<String> markersJson = markerFileJson.keys();
            while (markersJson.hasNext()) {
                String markerId = markersJson.next();
                JSONObject markerJson = markerFileJson.getJSONObject(markerId);

                Iterator<String> edgesJson = markerJson.keys();
                while (edgesJson.hasNext()) {
                    String edgeId = edgesJson.next();
                    JSONArray edgeJson = markerJson.getJSONArray(edgeId);

                    double x = edgeJson.getDouble(0);
                    double y = edgeJson.getDouble(1);
                    double z = edgeJson.getDouble(2);

                    this.markers.add(new PbMarker(Integer.parseInt(markerId), Integer.parseInt(edgeId), x, y, z));
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
            throw new RuntimeException("Failed to add marker coordinates");
        }
    }

    private PbMarker getMarker(int markerId, int markerEdgeId) {
        for (PbMarker marker : this.markers) {
            if (marker.getMarkerId() == markerId && marker.getMarkerEdgeId() == markerEdgeId) {
                return marker;
            }
        }
        return null;
    }

    private void readMarkerPositions() {

        try {

            // Read the JSON file
            String jsonFilePath = this.projectFolder + "/aruco.json";
            String jsonContent = new String(Files.readAllBytes(Paths.get(jsonFilePath)));

            // Parse the JSON content
            JSONObject arucoFileJson = new JSONObject(jsonContent);
            Iterator<String> markersJson = arucoFileJson.keys();
            while (markersJson.hasNext()) {
                String hostname = markersJson.next();
                JSONArray markerJson = arucoFileJson.getJSONArray(hostname);
                for (int i = 0; i < markerJson.length(); i++) {
                    JSONObject jsonMarker = markerJson.getJSONObject(i);
                    int markerId = jsonMarker.getInt("id");
                    int markerCorner = jsonMarker.getInt("corner");
                    double x = jsonMarker.getDouble("x");
                    double y = jsonMarker.getDouble("y");

                    PbCamera camera = this.getCameraByName(hostname);
                    PbImage image = camera.getImages()[0];
                    PbMarker marker = this.getMarker(markerId, markerCorner);
                    if (marker == null) {
                        marker = new PbMarker();
                    }

                    PbMarkerPosition markerPosition = new PbMarkerPosition(marker, image, x, y);
                    marker.addMarkerPosition(markerPosition);
                }

            }
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add marker positions");
        }
    }

    public PbCamera[] getCameras() {
        return this.cameras.toArray(new PbCamera[this.cameras.size()]);
    }

    public PbMarker[] getMarkers() {
        return this.markers.toArray(new PbMarker[this.markers.size()]);
    }

    public PbImage[] getImages() {
        return this.images.toArray(new PbImage[this.images.size()]);
    }

    public String getFolderName() {
        File folder = new File(this.projectFolder);
        return folder.getName();
    }
}
