package photobox.odm;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.net.ProtocolException;
import java.util.HashMap;
import java.util.Map;

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
import photobox.domain.PbCamera;
import photobox.domain.PbCameraPosition;
import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class OdmProject {

    private Connector connector;
    private String destDir;
    private OdmApi api;

    protected OdmProject(Connector connector, String baseUrl, String destDir) {
        this.connector = connector;
        this.destDir = destDir;
        this.api = new OdmApi(baseUrl);
    }

    protected void run() {

        try {
            PhotoBoxFolderReader pbfr = new PhotoBoxFolderReader(connector, destDir);

            String uuid = createTask(pbfr);

            PbImage[] images = pbfr.getImages();
            for (PbImage image : images) {
                File orgFile = image.getFile();
                File file = this.editExif(image);
                api.uploadFile("/task/new/upload/" + uuid, file, orgFile.getName());
            }

            File gcpFile = this.createGCPFile(pbfr);
            api.uploadFile("/task/new/upload/" + uuid, gcpFile, "gcp_file.txt");

            File geoTxtFile = this.createGeoTxtFile(pbfr);
            api.uploadFile("/task/new/upload/" + uuid, geoTxtFile, "geo.txt");

            api.request("/task/new/commit/" + uuid, new HashMap<String, String>());

        } catch (IOException e) {
            e.printStackTrace();
            connector.log("Failed to process photos");
        }

        return;

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

            // TODO: Replace with actual camera parameters
            /*
             * camParameter.put("focal_x", 0.742411768569596);
             * camParameter.put("focal_y", 0.742411768569596);
             * camParameter.put("c_x", 0.001966772527179585);
             * camParameter.put("c_y", 0.0049603303245847295);
             * camParameter.put("k1", 0.04624957024186535);
             * camParameter.put("k2", -0.02315359409038173);
             * camParameter.put("p1", 0.0003167781080551945);
             * camParameter.put("p2", 5.496613842429826e-05);
             * camParameter.put("k3", -0.03875582329858454);
             */

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

        parameter.put("webhook", "http://host.docker.internal:3001/webhook");

        JSONObject jsonResponse = api.request("/task/new/init", parameter);
        String uuid = jsonResponse.getString("uuid");
        connector.log("Task ID: " + uuid);
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
        this.connector.log("File path: " + file.getAbsolutePath());

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
