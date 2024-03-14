import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Optional;

import javax.swing.JOptionPane;

import com.agisoft.metashape.Camera;
import com.agisoft.metashape.Chunk;
import com.agisoft.metashape.Document;
import com.agisoft.metashape.License;
import com.agisoft.metashape.Marker;
import com.agisoft.metashape.Progress;
import com.agisoft.metashape.Vector;
import com.agisoft.metashape.Marker.Projection;
import com.agisoft.metashape.Marker.Reference;

import org.json.JSONArray;
import org.json.JSONObject;

public class MetashapeClient implements Progress, SfmClient {

    private final Connector connector;
    private Document project;
    private String projectFileName;
    private Chunk chunk;
    private HashMap<String, Marker> markers;
    private HashMap<String, Camera> cameras;

    public MetashapeClient(Connector connector) {
        this.connector = connector;
        this.markers = new HashMap<String, Marker>();
        this.cameras = new HashMap<String, Camera>();
    }

    public boolean connect() {
        if (!loadLibrary()) {
            connector.log("Failed to load library");
            return false;
        }

        if (!testLicense()) {
            connector.log("Failed to validate license");
            return false;
        }
        connector.log("Connected to Metashape");
        return true;
    }

    public boolean disconnect() {
        connector.log("Disconnected from Metashape");
        return true;
    }

    private boolean createProject(String filename) throws RuntimeException {
        try {
            this.projectFileName = filename;
            this.project = new Document();
            this.project.save(this.projectFileName, this);
            // this.chunk = this.project.addChunk();
            // doc.close();
            connector.log("Project created");
            return true;
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to create project");
        }
    }

    private void closeAndSaveProject(Document doc) {
        try {
            this.project.save(this.projectFileName, this);
            this.project.close();
            connector.log("Project saved and closed");
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to save and close project");
        }
    }

    private boolean loadLibrary() {
        ArrayList<Error> errors = new ArrayList<Error>();
        try {
            System.loadLibrary("metashape");
            return true;
        } catch (UnsatisfiedLinkError e) {
            errors.add(e);
        }

        String currentDirectory = System.getProperty("user.dir");
        String os = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();
        String path = "";
        if (os.contains("win") && arch.contains("64")) {
            path = "/lib/jniLibs/win64/metashape.dll";
        } else if (os.contains("win") && arch.contains("32")) {
            path = "/lib/jniLibs/win32/metashape.dll";
        } else if (os.toLowerCase().contains("mac")) {
            path = "/lib/jniLibs/macosx64/libmetashape.dylib";
        } else if (os.toLowerCase().contains("nix") || os.toLowerCase().contains("nux")) {
            path = "/lib/jniLibs/linux64/libmetashape.so";
        }

        try {
            System.load(currentDirectory + path);
            return true;
        } catch (UnsatisfiedLinkError e) {
            errors.add(e);
        }

        for (Error e : errors) {
            connector.log(e.getMessage());
            e.printStackTrace();
        }
        return false;
    }

    private boolean testLicense() {
        if (License.isValid()) {
            return true;
        }
        JOptionPane.showMessageDialog(null, "License is invalid");
        return false;
    }

    @Override
    public void processPhotos(String destDir) {
        this.connector.log("Processing photos");
        try {
            this.createProject(destDir + "/project.psx");
            this.addPhotos(destDir);
            this.addMarkerCoordinates(destDir);
            this.addMarkerPositions(destDir);
            this.closeAndSaveProject(this.project);
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
        }
    }

    private void addMarkerCoordinates(String destDir) {
        this.connector.log("Adding marker coordinates");
        try {
            // Read the JSON file
            String jsonFilePath = destDir + "/marker.json";
            String jsonContent = new String(Files.readAllBytes(Paths.get(jsonFilePath)));

            // Parse the JSON content
            JSONObject markerFileJson = new JSONObject(jsonContent);
            Iterator<String> markersJson = markerFileJson.keys();
            while (markersJson.hasNext()) {
                String markerId = markersJson.next();
                JSONObject markerJson = markerFileJson.getJSONObject(markerId);
                System.out.println("Marker: " + markerId);
                System.out.println(markerJson);
                Iterator<String> edgesJson = markerJson.keys();
                while (edgesJson.hasNext()) {
                    String edgeId = edgesJson.next();
                    JSONArray edgeJson = markerJson.getJSONArray(edgeId);
                    // Process the value here
                    System.out.println("Edge: " + edgeId);
                    System.out.println(edgeJson);

                    double x = edgeJson.getDouble(0);
                    double y = edgeJson.getDouble(1);
                    double z = edgeJson.getDouble(2);

                    Marker m = this.chunk.addMarker();
                    Vector v = new Vector(x, y, z);
                    Reference r = new Reference();
                    r.setLocation(Optional.of(v));
                    m.setReference(r);
                    m.setLabel(markerId + '-' + edgeId);
                    this.markers.put(markerId + '-' + edgeId, m);
                }
            }
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add marker coordinates");
        }
    }

    private void addMarkerPositions(String destDir) {
        try {
            // Read the JSON file
            String jsonFilePath = destDir + "/aruco.json";
            String jsonContent = new String(Files.readAllBytes(Paths.get(jsonFilePath)));

            // Parse the JSON content
            JSONObject arucoFileJson = new JSONObject(jsonContent);
            Iterator<String> markersJson = arucoFileJson.keys();
            while (markersJson.hasNext()) {
                String hostname = markersJson.next();
                JSONArray markerJson = arucoFileJson.getJSONArray(hostname);
                for (int i = 0; i < markerJson.length(); i++) {
                    JSONObject marker = markerJson.getJSONObject(i);
                    int markerId = marker.getInt("id");
                    int markerCorner = marker.getInt("corner");
                    double x = marker.getDouble("x");
                    double y = marker.getDouble("y");
                    Marker m = this.markers.get(markerId + "-" + markerCorner);
                    if (m == null) {
                        m = this.chunk.addMarker();
                        m.setLabel(markerId + "-" + markerCorner);
                        this.markers.put(markerId + "-" + markerCorner, m);
                    }
                    Vector v = new Vector(x, y);
                    Projection p = new Projection();
                    p.setPoint(Optional.of(v));
                    p.setPinned(true);
                    m.setProjection(this.cameras.get(hostname).getKey(), Optional.of(p));
                }

            }
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add marker positions");
        }
    }

    private void addPhotos(String destDir) {
        this.connector.log("Adding photos");
        try {
            File[] files = new File(destDir).listFiles();
            ArrayList<String> photoPathList = new ArrayList<String>();
            for (File file : files) {
                if (file.isFile() && file.getName().toLowerCase().endsWith(".jpg")) {
                    photoPathList.add(file.getAbsolutePath());
                }
            }

            String[] photoPaths = photoPathList.toArray(new String[0]);

            this.chunk = this.project.addChunk();
            this.chunk.addPhotos(photoPaths, this);

            // Sensor sensor = this.chunk.addSensor();
            Camera[] cams = this.chunk.getCameras();

            for (int i = 0; i < cams.length; i++) {
                Camera cam = cams[i];
                String path = cam.getPhoto().get().getPath();
                File f = new File(path);
                String filename = f.getName();
                int index = filename.lastIndexOf(".");
                int index_ = filename.lastIndexOf("_");
                if (index_ > 0) {
                    index = index_;
                }
                String hostname = filename.substring(0, index);
                cam.setLabel(hostname);
                cam.getMeta().put("hostname", hostname);
                cam.getMeta().put("LensPosition", "999");
                this.cameras.put(hostname, cam);
            }

        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add photos");
        }
    }

    // implement Progress

    @Override
    public void progress(double progress) {
        this.connector.log("Progress: " + progress);
    }

    @Override
    public void status(String status) {
        this.connector.log("Status: " + status);
    }

    @Override
    public boolean aborted() {
        this.connector.log("Aborted");
        return false;
    }

}
