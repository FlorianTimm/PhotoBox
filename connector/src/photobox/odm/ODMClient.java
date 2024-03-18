package photobox.odm;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.ProtocolException;
import java.net.URL;
import java.util.HashMap;
import java.util.Map;

import org.json.JSONArray;
import org.json.JSONObject;

import photobox.Connector;
import photobox.PhotoBoxFolderReader;
import photobox.SfmClient;
import photobox.domain.PbCamera;
import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class ODMClient implements SfmClient {

    private final Connector connector;
    private String baseURL;
    private WebHookServer whs;

    public ODMClient(Connector connector) {
        this.connector = connector;
        this.baseURL = "http://localhost:3000";
    }

    public boolean connect() {
        try {
            JSONObject jsonResponse = apiRequest("/info");
            connector.log("Connected to OpenDroneMap");
            connector.log("OpenDroneMap version: " + jsonResponse.getString("version"));
            this.createWebHookServer();
            return true;
        } catch (IOException e) {
            connector.log("Failed to connect to OpenDroneMap");
            return false;
        }
    }

    private void createWebHookServer() {
        if (this.whs == null) {
            this.whs = new WebHookServer(connector, this);
            this.whs.run();
        }
    }

    public boolean disconnect() {
        connector.log("Disconnected from OpenDroneMap");
        return true;
    }

    @Override
    public void processPhotos(String destDir) {
        this.connector.log("Processing photos");

        try {
            PhotoBoxFolderReader pbfr = new PhotoBoxFolderReader(connector, destDir);

            String uuid = createTask(pbfr);

            PbImage[] images = pbfr.getImages();
            for (PbImage image : images) {
                File file = image.getFile();
                uploadFile("/task/new/upload/" + uuid, file);
            }

            File gcpFile = this.createGCPFile(pbfr);
            uploadFile("/task/new/upload/" + uuid, gcpFile, "gcp_file.txt");
            apiRequest("/task/new/commit/" + uuid, new HashMap<String, String>());

        } catch (IOException e) {
            e.printStackTrace();
            connector.log("Failed to process photos");
        }

        return;

    }

    private String createTask(PhotoBoxFolderReader pbfr) throws IOException, ProtocolException {
        PbCamera cam = pbfr.getCameras()[0];

        Map<String, String> parameter = new HashMap<String, String>();
        parameter.put("name", pbfr.getFolderName());

        JSONArray options = new JSONArray();

        JSONObject camParameter = new JSONObject();
        camParameter.put("projection_type", "brown");
        camParameter.put("width", cam.getWidth());
        camParameter.put("height", cam.getHeight());

        // TODO: Replace with actual camera parameters
        camParameter.put("focal_x", 0.742411768569596);
        camParameter.put("focal_y", 0.742411768569596);
        camParameter.put("c_x", 0.001966772527179585);
        camParameter.put("c_y", 0.0049603303245847295);
        camParameter.put("k1", 0.04624957024186535);
        camParameter.put("k2", -0.02315359409038173);
        camParameter.put("p1", 0.0003167781080551945);
        camParameter.put("p2", 5.496613842429826e-05);
        camParameter.put("k3", -0.03875582329858454);

        /*
         * camParameter.put("focal_x", cam.getFocalLength() / cam.getWidth());
         * camParameter.put("focal_y", cam.getFocalLength() / cam.getWidth());
         * camParameter.put("c_x", cam.getPrincipalPointX() / cam.getWidth());
         * camParameter.put("c_y", cam.getPrincipalPointY() / cam.getWidth());
         * camParameter.put("k1", cam.getK()[0]);
         * camParameter.put("k2", cam.getK()[1]);
         * camParameter.put("p1", cam.getP()[0]);
         * camParameter.put("p2", cam.getP()[1]);
         * camParameter.put("k3", cam.getK()[2]);
         */

        JSONObject cams = new JSONObject();
        cams.put("raspberry pi /base/soc/i2c0mux/i2c@1/imx708@1a 4608 2592 brown 0.85", camParameter);

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

        JSONObject jsonResponse = apiRequest("/task/new/init", parameter);
        String uuid = jsonResponse.getString("uuid");
        connector.log("Task ID: " + uuid);
        return uuid;
    }

    private File createGCPFile(PhotoBoxFolderReader pbfr) throws IOException {
        StringBuilder str = new StringBuilder();
        str.append("+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        str.append("\n");

        for (PbMarker marker : pbfr.getMarkers()) {
            for (PbMarkerPosition markerPosition : marker.getMarkerPositions()) {
                str.append(marker.getX() * 100 + 500000);
                str.append(" ");
                str.append(marker.getY() * 100 + 5900000);
                str.append(" ");
                str.append(marker.getZ() * 100);
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

    private JSONObject apiRequest(String urlPart)
            throws IOException, ProtocolException {

        URL url = new URL(baseURL + urlPart);

        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");

        int responseCode = connection.getResponseCode();

        // Check if the request was successful
        if (responseCode == HttpURLConnection.HTTP_OK) {
            // Read the response from the API
            BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            String line;
            StringBuilder response = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();

            JSONObject jsonResponse = new JSONObject(response.toString());

            // Close the connection
            connection.disconnect();

            return jsonResponse;
        } else {

            connection.disconnect();

            throw new IOException("Failed to connect to OpenDroneMap");
        }

    }

    private void uploadFile(String urlPart, File file) throws IOException {
        uploadFile(urlPart, file, file.getName());
    }

    private JSONObject uploadFile(String urlPart, File file, String fileName) throws IOException {
        return apiRequest(urlPart, null, file, fileName);
    }

    private JSONObject apiRequest(String urlPart, Map<String, String> parameter) throws IOException {
        return apiRequest(urlPart, parameter, null, null);
    }

    private JSONObject apiRequest(String urlPart, Map<String, String> parameter, File file,
            String fileName) throws IOException {
        URL url = new URL(baseURL + urlPart);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);

        // Set the content type to multipart/form-data
        String boundary = "---------------------------" + System.currentTimeMillis();
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);

        OutputStream outputStream = connection.getOutputStream();

        if (parameter != null) {
            for (Map.Entry<String, String> entry : parameter.entrySet()) {
                outputStream.write(("--" + boundary + "\r\n").getBytes());
                outputStream.write(("Content-Disposition: form-data; name=\"" + entry.getKey() + "\"\r\n").getBytes());
                outputStream.write(("\r\n").getBytes());
                outputStream.write((entry.getValue() + "\r\n").getBytes());
            }
        }

        if (file != null) {
            outputStream.write(("--" + boundary + "\r\n").getBytes());
            outputStream.write(
                    ("Content-Disposition: form-data; name=\"images\"; filename=\"" + fileName + "\"\r\n")
                            .getBytes());
            outputStream.write(("Content-Type: application/octet-stream\r\n").getBytes());
            outputStream.write(("\r\n").getBytes());

            byte[] buffer = new byte[4096];
            int bytesRead;
            try (FileInputStream fileInputStream = new FileInputStream(file)) {
                while ((bytesRead = fileInputStream.read(buffer)) != -1) {
                    outputStream.write(buffer, 0, bytesRead);
                }
            }
            outputStream.write(("\r\n").getBytes());
        }

        outputStream.write(("\r\n").getBytes());
        outputStream.write(("--" + boundary + "--\r\n").getBytes());

        // Get the response code
        int responseCode = connection.getResponseCode();

        // Check if the request was successful
        if (responseCode == HttpURLConnection.HTTP_OK) {
            // Read the response from the API
            BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            String line;
            StringBuilder response = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                response.append(line);
            }
            reader.close();
            JSONObject jsonResponse = new JSONObject(response.toString());
            // Close the connection
            connection.disconnect();
            return jsonResponse;
        } else {
            connection.disconnect();
            throw new IOException("Failed to connect to OpenDroneMap");
        }
    }

    public void processWebhook(JSONObject json) {
        connector.log("Received webhook");
        int statusCode = json.getJSONObject("status").getInt("code");
        String taskId = json.getString("uuid");
        if (statusCode == 100) {
            this.connector.log("Task " + taskId + " is done");
        } else {
            this.connector.log("Task " + taskId + " failed");
        }
    }

}
