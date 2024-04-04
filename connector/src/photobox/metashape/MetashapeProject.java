package photobox.metashape;

import java.util.Optional;
import java.io.File;

import com.agisoft.metashape.Calibration;
import com.agisoft.metashape.Camera;
import com.agisoft.metashape.Chunk;
import com.agisoft.metashape.Document;
import com.agisoft.metashape.Marker;
import com.agisoft.metashape.Photo;
import com.agisoft.metashape.Progress;
import com.agisoft.metashape.Sensor;
import com.agisoft.metashape.Vector;
import com.agisoft.metashape.tasks.AlignCameras;
import com.agisoft.metashape.tasks.MatchPhotos;
import com.agisoft.metashape.Marker.Reference;
import com.agisoft.metashape.Marker.Projection;
import com.agisoft.metashape.ReferencePreselectionMode;

import photobox.Connector;
import photobox.PhotoBoxFolderReader;
import photobox.domain.PbCamera;
import photobox.domain.PbCameraPosition;
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
            this.saveProject();
            this.orientPhotos();
            this.closeAndSaveProject();
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
        }
    }

    private boolean createProject() throws RuntimeException {
        try {
            this.project = new Document();
            saveProject();
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

    private void saveProject() {
        this.project.save(this.projectFilePath, this);
    }

    private void addPhotos() {
        PbImage[] images = this.pbfr.getImages();
        String[] imagePaths = new String[images.length];
        String[] imageFileNames = new String[images.length];

        for (int i = 0; i < images.length; i++) {
            imagePaths[i] = images[i].getFile().getAbsolutePath();
            imageFileNames[i] = images[i].getFile().getName();
        }

        this.chunk = this.project.addChunk();
        this.chunk.addPhotos(imagePaths, this);

        Camera[] cameras = this.chunk.getCameras();

        for (int i = 0; i < cameras.length; i++) {
            Camera camera = cameras[i];
            Photo photo = camera.getPhoto().get();
            String path = photo.getPath();
            File file = new File(path);
            int index = getIndexOfArray(imagePaths, file.getAbsolutePath());
            if (index == -1) {
                index = getIndexOfArray(imageFileNames, file.getName());
            }
            if (index == -1) {
                this.connector.log("Failed to find image index");
                continue;
            }
            PbImage image = images[index];
            image.setId(camera.getKey());
            camera.setLabel(image.getFile().getName());

            PbCameraPosition position = image.getCamera().getPosition();
            if (position != null) {
                com.agisoft.metashape.Camera.Reference cameraReference = new com.agisoft.metashape.Camera.Reference();
                Vector coord = new Vector(position.getX(), position.getY(), position.getZ());
                cameraReference.setLocation(Optional.of(coord));
                /*
                 * Vector rot = new Vector(position.getRoll() / 3.14 * 180, position.getPitch()
                 * / 3.14 * 180, position.getYaw() / 3.14 * 180);
                 * cameraReference.setRotation(Optional.of(rot));
                 */
                Vector locationAccVector = new Vector(0.1, 0.1, 0.1);
                cameraReference.setLocationAccuracy(Optional.of(locationAccVector));
                camera.setReference(cameraReference);
            }

            if (!image.getCamera().isCameraIdSet()) {
                PbCamera cam = image.getCamera();
                cam.setCameraId(camera.getKey());
                Sensor sensor = camera.getSensor().get();
                sensor.setLabel(cam.getCameraName());
                sensor.setPixelSize(0.0014, 0.0014);
                Calibration calib = new Calibration();
                calib.setF(image.getFocalLength());
                calib.setCx(image.getPrincipalPointX());
                calib.setCy(image.getPrincipalPointY());
                calib.setK1(image.getK()[0]);
                calib.setK2(image.getK()[1]);
                calib.setK3(image.getK()[2]);
                calib.setK4(image.getK()[3]);
                calib.setP1(image.getP()[0]);
                calib.setP2(image.getP()[1]);
                calib.setHeight(image.getCamera().getHeight());
                calib.setWidth(image.getCamera().getWidth());

                sensor.setUserCalib(Optional.of(calib));
                // sensor.setFixed(true);
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
            m.setLabel(marker.toString());
            m.setType(Marker.Type.TypeRegular);
            m.setReference(r);
            m.setSelected(true);
            m.setEnabled(true);
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

    private void orientPhotos() {
        this.connector.log("Orienting photos");
        try (MatchPhotos match_photos = new MatchPhotos()) {
            match_photos.setDownscale(5);
            match_photos.setReferencePreselectionMode(ReferencePreselectionMode.ReferencePreselectionSource);
            match_photos.setKeypointLimit(40000);
            match_photos.setTiepointLimit(4000);
            match_photos.setGuidedMatching(true);
            match_photos.apply(this.chunk, this);
            match_photos.delete();

        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to orient photos");
        }

        try (AlignCameras align_cameras = new AlignCameras()) {
            align_cameras.apply(this.chunk, this);
            align_cameras.delete();
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to align cameras");
        }
    }

    private void closeAndSaveProject() {
        try {
            saveProject();
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
