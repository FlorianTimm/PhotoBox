package photobox.odm;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.net.ProtocolException;
import java.util.HashMap;
import java.util.Map;
import java.util.Timer;
import java.util.TimerTask;

import org.apache.commons.imaging.Imaging;
import org.apache.commons.imaging.common.ImageMetadata;
import org.apache.commons.imaging.formats.jpeg.JpegImageMetadata;
import org.apache.commons.imaging.formats.jpeg.exif.ExifRewriter;
import org.apache.commons.imaging.formats.tiff.TiffImageMetadata;
import org.apache.commons.imaging.formats.tiff.constants.ExifTagConstants;
import org.apache.commons.imaging.formats.tiff.constants.TiffTagConstants;
import org.apache.commons.imaging.formats.tiff.write.TiffOutputDirectory;
import org.apache.commons.imaging.formats.tiff.write.TiffOutputSet;
import org.json.JSONArray;
import org.json.JSONObject;

import photobox.Connector;
import photobox.PhotoBoxFolderReader;
import photobox.ProcessGUI;
import photobox.domain.PbCamera;
import photobox.domain.PbCameraPosition;
import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class OdmProject extends ProcessGUI {
    private OdmWebHookServer whs;

    private Connector connector;
    private String destDir;
    private OdmApi api;

    private String uuid;

    protected OdmProject(Connector connector, String baseUrl, String destDir) {
        super(connector, "OpenDroneMap");
        this.connector = connector;
        this.destDir = destDir;
        this.api = new OdmApi(baseUrl);
        this.createWebHookServer();
    }

    private void createWebHookServer() {
        if (this.whs == null) {
            this.whs = new OdmWebHookServer(this);
            new Thread("OdmWebHookServerThread") {
                public void run() {
                    whs.run();
                }
            }.start();
        }
    }

    protected void processWebhook(JSONObject json) {
        log("Received webhook");
        int statusCode = json.getJSONObject("status").getInt("code");
        String taskId = json.getString("uuid");
        if (statusCode == 100) {
            this.log("Task " + taskId + " is done");
        } else {
            this.log("Task " + taskId + " failed");
        }
    }

    protected void run() {

        try {
            PhotoBoxFolderReader pbfr = new PhotoBoxFolderReader(connector, destDir);

            String uuid = this.createTask(pbfr);
            setLabel("OpenDroneMap: " + uuid);

            PbImage[] images = pbfr.getImages();
            for (PbImage image : images) {
                File orgFile = image.getFile();
                File file = this.editExif(image);
                api.uploadFile("/task/new/upload/" + this.uuid, file, orgFile.getName());
            }

            File gcpFile = this.createGCPFile(pbfr);
            api.uploadFile("/task/new/upload/" + this.uuid, gcpFile, "gcp_file.txt");

            File geoTxtFile = this.createGeoTxtFile(pbfr);
            api.uploadFile("/task/new/upload/" + this.uuid, geoTxtFile, "geo.txt");

            api.request("/task/new/commit/" + this.uuid, new HashMap<String, String>());

            monitorTask();

        } catch (IOException e) {
            e.printStackTrace();
            log("Failed to process photos");
        }

        return;

    }

    private void monitorTask() {
        Timer t = new Timer();
        t.schedule(new TimerTask() {

            private int log_data_row = 0;

            @Override
            public void run() {
                try {
                    JSONObject jsonResponse = api.request("/task/" + uuid + "/info?with_output=" + this.log_data_row);
                    int status = jsonResponse.getJSONObject("status").getInt("code");

                    if (status == 50) {
                        t.cancel();
                        log("Task canceled");
                    }
                    if (status == 20) {
                        float progress = jsonResponse.getFloat("progress");
                        logProgress(Math.round(progress));
                    }
                    JSONArray output = jsonResponse.getJSONArray("output");

                    StringBuilder str = new StringBuilder();
                    for (int i = log_data_row; i < output.length(); i++) {
                        String line = output.getString(i);
                        if (line.length() > 200) {
                            continue;
                        }
                        str.append(line + "\n");
                    }
                    if (str.length() > 0) {
                        log(str.toString());
                        System.out.println(str.toString());
                    }
                    this.log_data_row += output.length();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }, 1000, 1000);
    }

    private String createTask(PhotoBoxFolderReader pbfr) throws IOException, ProtocolException {
        Map<String, String> parameter = new HashMap<String, String>();
        parameter.put("name", pbfr.getFolderName());

        JSONArray options = new JSONArray();
        JSONObject cams = new JSONObject();
        for (PbImage img : pbfr.getImages()) {
            PbCamera cam = img.getCamera();
            JSONObject camParameter = new JSONObject();
            camParameter.put("projection_type", "brown");
            camParameter.put("width", cam.getWidth());
            camParameter.put("height", cam.getHeight());

            camParameter.put("focal_x", img.getFocalLength() / cam.getWidth());
            camParameter.put("focal_y", img.getFocalLength() / cam.getWidth());
            camParameter.put("c_x", img.getPrincipalPointX() / cam.getWidth());
            camParameter.put("c_y", img.getPrincipalPointY() / cam.getWidth());
            camParameter.put("k1", img.getK()[0]);
            camParameter.put("k2", img.getK()[1]);
            camParameter.put("p1", img.getP()[0]);
            camParameter.put("p2", img.getP()[1]);
            camParameter.put("k3", img.getK()[2]);

            double f_fac = Math
                    .round(Math.round(img.getFocalLength() * 36.0 / img.getCamera().getWidth()) / 36.0 * 100.)
                    / 100.;
            // cams.put("raspberry pi /base/soc/i2c0mux/i2c@1/imx708@1a 4608 2592 brown
            // 0.85", camParameter);
            cams.put("raspberry pi " + cam.getCameraName() + " " +
                    cam.getWidth() + " " + cam.getHeight() + " brown " + f_fac, camParameter);

        }
        JSONObject optionCameras = new JSONObject();
        optionCameras.put("name", "cameras");
        optionCameras.put("value", cams.toString());

        /*
         * Parameter 3D-Modell:
         * --use-3dmesh --mesh-size 300000 --mesh-octree-depth 12 --auto-boundary
         * --pc-quality high --pc-ept --cog --gltf
         */

        options.put(optionCameras);
        /*
         * JSONObject optionBoundary = new JSONObject();
         * optionBoundary.put("name", "auto-boundary");
         * optionBoundary.put("value", "true");
         * options.put(optionBoundary);
         */

        parameter.put("options", options.toString());

        parameter.put("webhook", "http://host.docker.internal:" + whs.getPort() + "/webhook");
        System.out.println("Webhook: " + parameter.get("webhook"));

        JSONObject jsonResponse = api.request("/task/new/init", parameter);
        String uuid = jsonResponse.getString("uuid");
        log("Task ID: " + uuid);
        this.uuid = uuid;
        return uuid;
    }

    private File createGeoTxtFile(PhotoBoxFolderReader pbfr) throws IOException {
        StringBuilder str = new StringBuilder();
        str.append("+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        str.append("\n");

        for (PbImage img : pbfr.getImages()) {
            PbCameraPosition pos = img.getCamera().getPosition();
            if (pos == null) {
                continue;
            }
            double[] xyz = transformCoordinates(pos.getX(), pos.getY(), pos.getZ());
            str.append(img.getFile().getName());
            str.append(" ");
            str.append(xyz[0]);
            str.append(" ");
            str.append(xyz[1]);
            str.append(" ");
            str.append(xyz[2]);
            str.append(" ");
            str.append(img.getCamera().getPosition().getYaw() * 180.);
            str.append(" ");
            str.append(img.getCamera().getPosition().getPitch() * 180.);
            str.append(" ");
            str.append(img.getCamera().getPosition().getRoll() * 180.);
            str.append(" ");
            str.append(1);
            str.append(" ");
            str.append(1);
            str.append("\n");

        }
        return createFileFromString(str.toString(), "geo", "txt");

    }

    private File createGCPFile(PhotoBoxFolderReader pbfr) throws IOException {
        StringBuilder str = new StringBuilder();
        str.append("+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        str.append("\n");

        for (PbMarker marker : pbfr.getMarkers()) {
            for (PbMarkerPosition markerPosition : marker.getMarkerPositions()) {
                double[] xyz = transformCoordinates(marker.getX(), marker.getY(), marker.getZ());
                str.append(xyz[0]);
                str.append(" ");
                str.append(xyz[1]);
                str.append(" ");
                str.append(xyz[2]);
                str.append(" ");
                str.append(markerPosition.getX());
                str.append(" ");
                str.append(markerPosition.getY());
                str.append(" ");
                str.append(markerPosition.getImage().getFile().getName());
                str.append(" ");
                str.append(markerPosition.getImage().getCamera().getCameraName());
                str.append("_");
                str.append(marker.getMarkerId());
                str.append("_");
                str.append(marker.getMarkerEdgeId());
                str.append("\n");
            }
        }
        return createFileFromString(str.toString(), "gcp_file", "txt");

    }

    private File createFileFromString(String str, String fileName, String ending) throws IOException {
        // Create a temporary file
        File file = File.createTempFile(fileName, "." + ending);
        log("File path: " + file.getAbsolutePath());

        // Write the string data to the file
        try (FileWriter writer = new FileWriter(file)) {
            writer.write(str.toString());
        }

        return file;
    }

    private File editExif(PbImage img) {
        // vgl. https://github.com/mapillary/OpenSfM/blob/main/opensfm/exif.py#L59
        try {
            File file = img.getFile();
            ImageMetadata meta = Imaging.getMetadata(file);
            final JpegImageMetadata jpegMetadata = (JpegImageMetadata) meta;
            TiffImageMetadata exif = jpegMetadata.getExif();
            File tmp_file = File.createTempFile(file.getName(), ".jpg");
            TiffOutputSet outputSet = exif.getOutputSet();

            TiffOutputDirectory exifDir = outputSet.getOrCreateExifDirectory();
            exifDir.removeField(ExifTagConstants.EXIF_TAG_FOCAL_LENGTH_IN_35MM_FORMAT);
            short focal35 = (short) Math.round(img.getFocalLength() / img.getCamera().getWidth() * 36.0);
            exifDir.add(ExifTagConstants.EXIF_TAG_FOCAL_LENGTH_IN_35MM_FORMAT, focal35);

            TiffOutputDirectory rootDir = outputSet.getOrCreateRootDirectory();
            rootDir.removeField(TiffTagConstants.TIFF_TAG_MODEL);
            rootDir.add(TiffTagConstants.TIFF_TAG_MODEL, img.getCamera().getCameraName());

            new ExifRewriter().updateExifMetadataLossless(file, new FileOutputStream(tmp_file), outputSet);
            return tmp_file;
        } catch (Exception e) {
            e.printStackTrace();
        }
        return null;
    }

    private double[] transformCoordinates(double x, double y, double z) {
        double[] result = new double[3];
        double faktor = 100.;
        result[0] = x * faktor + 500000;
        result[1] = y * faktor + 5900000;
        result[2] = z * faktor;
        return result;
    }
}
