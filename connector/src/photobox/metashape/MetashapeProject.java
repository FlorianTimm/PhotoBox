package photobox.metashape;

import java.util.Optional;

import com.agisoft.metashape.Calibration;
import com.agisoft.metashape.Camera;
import com.agisoft.metashape.Chunk;
import com.agisoft.metashape.Document;
import com.agisoft.metashape.Marker;
import com.agisoft.metashape.Photo;
import com.agisoft.metashape.Progress;
import com.agisoft.metashape.Sensor;
import com.agisoft.metashape.Vector;
import com.agisoft.metashape.Marker.Reference;
import com.agisoft.metashape.Marker.Projection;

import photobox.Connector;
import photobox.PhotoBoxFolderReader;
import photobox.domain.PbCamera;
import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class MetashapeProject implements Progress {
    private Connector connector;
    private Document project;
    private String projectFilePath;
    private Chunk chunk;
    private String projectFolder;
    private PhotoBoxFolderReader pbfr;

    public MetashapeProject(Connector connector, String projectFolder) {
        this(connector, projectFolder, projectFolder + "/project.psx");
    }

    public MetashapeProject(Connector connector, String projectFolder, String projectFilePath) {
        this.projectFilePath = projectFilePath;
        this.connector = connector;
        this.projectFolder = projectFolder;
    }

    public void run() {
        this.connector.log("Processing photos");
        try {
            this.createProject();
            this.pbfr = new PhotoBoxFolderReader(connector, projectFolder);
            this.addPhotos();
            this.addMarkerCoordinates();
            this.addMarkerPositions();
            this.closeAndSaveProject();
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
        }
    }

    private boolean createProject() throws RuntimeException {
        try {
            this.project = new Document();
            this.project.save(this.projectFilePath, this);
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

    private void addPhotos() {
        PbImage[] images = this.pbfr.getImages();
        String[] imagePaths = new String[images.length];

        for (int i = 0; i < images.length; i++) {
            imagePaths[i] = images[i].getFile().getAbsolutePath();
        }

        this.chunk = this.project.addChunk();
        this.chunk.addPhotos(imagePaths, this);

        Camera[] cameras = this.chunk.getCameras();

        for (int i = 0; i < cameras.length; i++) {
            Camera camera = cameras[i];
            Photo photo = camera.getPhoto().get();
            String path = photo.getPath();
            int index = getIndexOfArray(imagePaths, path);
            if (index == -1) {
                throw new RuntimeException("Failed to find index of image path");
            }
            PbImage image = images[index];
            image.setId(camera.getKey());
            camera.setLabel(image.getFile().getName());

            if (!image.getCamera().isCameraIdSet()) {
                PbCamera c = image.getCamera();
                c.setCameraId(camera.getKey());
                Sensor sensor = camera.getSensor().get();
                sensor.setLabel(c.getCameraName());
                sensor.setPixelSize(0.0014, 0.0014);
                Calibration calib = new Calibration();
                calib.setF(image.getCamera().getFocalLength());
                calib.setCx(image.getCamera().getPrincipalPointX());
                calib.setCy(image.getCamera().getPrincipalPointY());
                calib.setK1(image.getCamera().getK()[0]);
                calib.setK2(image.getCamera().getK()[1]);
                calib.setK3(image.getCamera().getK()[2]);
                calib.setK4(image.getCamera().getK()[3]);
                calib.setP1(image.getCamera().getP()[0]);
                calib.setP2(image.getCamera().getP()[1]);

                sensor.setUserCalib(Optional.of(calib));
                sensor.setFixed(true);
            } else {
                camera.setSensor(this.chunk.getSensor(image.getCamera().getCameraId()));
            }
        }
    }

    private int getIndexOfArray(String[] array, String value) {
        for (int i = 0; i < array.length; i++) {
            if (array[i].equals(value)) {
                return i;
            }
        }
        return -1;
    }

    private void addMarkerCoordinates() {
        this.connector.log("Adding marker coordinates");
        PbMarker[] markers = this.pbfr.getMarkers();
        for (PbMarker marker : markers) {
            Marker m = this.chunk.addMarker();
            marker.setId(m.getKey());

            double x = marker.getX();
            double y = marker.getY();
            double z = marker.getZ();

            Vector v = new Vector(x, y, z);
            Reference r = new Reference();
            r.setLocation(Optional.of(v));
            m.setReference(r);
            m.setSelected(true);
            m.setEnabled(true);
            m.setLabel(marker.toString());
        }

    }

    private void addMarkerPositions() {

        PbMarker[] markers = this.pbfr.getMarkers();

        for (PbMarker marker : markers) {
            int mid = marker.getId();
            Marker m = this.chunk.getMarker(mid).get();
            for (PbMarkerPosition markerPosition : marker.getMarkerPositions()) {
                double x = markerPosition.getX();
                double y = markerPosition.getY();
                Vector v = new Vector(x, y);
                Projection p = new Projection();
                p.setPoint(Optional.of(v));
                p.setPinned(true);
                m.setProjection(markerPosition.getImage().getImageId(), Optional.of(p));
                m.setSelected(true);
                m.setEnabled(true);
            }
        }

    }

    private void closeAndSaveProject() {
        try {
            this.project.save(this.projectFilePath, this);
            this.project.close();
            connector.log("Project saved and closed");
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to save and close project");
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
