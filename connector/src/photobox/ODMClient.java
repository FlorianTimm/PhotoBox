package photobox;

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
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

import org.json.JSONObject;

import photobox.domain.PbImage;
import photobox.domain.PbMarker;
import photobox.domain.PbMarkerPosition;

public class ODMClient implements SfmClient {

    private final Connector connector;
    private String baseURL;

    public ODMClient(Connector connector) {
        this.connector = connector;
        this.baseURL = "http://localhost:3000";
    }

    public boolean connect() {
        try {
            JSONObject jsonResponse = apiRequest("/info");
            connector.log("Connected to OpenDroneMap");
            connector.log("OpenDroneMap version: " + jsonResponse.getString("version"));
            return true;
        } catch (IOException e) {
            connector.log("Failed to connect to OpenDroneMap");
            return false;
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
            Map<String, String> parameter = new HashMap<String, String>();
            parameter.put("name", "test");

            JSONObject jsonResponse = apiRequest("/task/new/init", parameter);
            String uuid = jsonResponse.getString("uuid");
            connector.log("Task ID: " + uuid);

            PhotoBoxFolderReader pbfr = new PhotoBoxFolderReader(connector, destDir);
            PbImage[] images = pbfr.getImages();
            for (PbImage image : images) {
                File file = image.getFile();
                uploadFile("/task/new/upload/" + uuid, file);
            }

            File file = this.createGCPFile(pbfr);

            uploadFile("/task/new/upload/" + uuid, file);
            apiRequest("/task/new/commit/" + uuid, new HashMap<String, String>());

        } catch (IOException e) {
            e.printStackTrace();
            connector.log("Failed to process photos");
        }

        return;

    }

    private File createGCPFile(PhotoBoxFolderReader pbfr) throws IOException {
        StringBuilder str = new StringBuilder();
        str.append("+proj=utm +zone=32 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs");
        str.append("\n");

        for (PbMarker marker : pbfr.getMarkers()) {
            for (PbMarkerPosition markerPosition : marker.getMarkerPositions()) {
                str.append(marker.getX() + 500000);
                str.append(" ");
                str.append(marker.getY() + 5900000);
                str.append(" ");
                str.append(marker.getZ());
                str.append(" ");
                str.append(markerPosition.getX());
                str.append(" ");
                str.append(markerPosition.getY());
                str.append(" ");
                str.append(markerPosition.getImage().getFile().getName());
                str.append("\n");
            }
        }

        // Create a temporary file
        File gcpFile = File.createTempFile("gcp_file", ".txt");
        System.out.println("File path: " + gcpFile.getAbsolutePath());

        // Write the string data to the file
        try (FileWriter writer = new FileWriter(gcpFile)) {
            writer.write(str.toString());
        }

        return gcpFile;
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

    private JSONObject apiRequest(String urlPart, Map<String, String> parameter)
            throws IOException, ProtocolException {

        URL url = new URL(baseURL + urlPart);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");

        // Create a StringBuilder to store the form data
        StringBuilder formData = new StringBuilder();

        for (Map.Entry<String, String> entry : parameter.entrySet()) {
            formData.append(URLEncoder.encode(entry.getKey(), "UTF-8"));
            formData.append("=");
            formData.append(URLEncoder.encode(entry.getValue(), "UTF-8"));
            formData.append("&");
        }

        // Convert the StringBuilder to a byte array
        byte[] postData = formData.toString().getBytes(StandardCharsets.UTF_8);

        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setDoOutput(true);

        try (OutputStream outputStream = connection.getOutputStream()) {
            outputStream.write(postData);
        }

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

    public void uploadFile(String urlPart, File file) throws IOException {
        URL url = new URL(baseURL + urlPart);
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);

        // Set the content type to multipart/form-data
        String boundary = "---------------------------" + System.currentTimeMillis();
        connection.setRequestProperty("Content-Type", "multipart/form-data; boundary=" + boundary);

        try (OutputStream outputStream = connection.getOutputStream();
                FileInputStream fileInputStream = new FileInputStream(file)) {

            // Write the file data to the request body
            outputStream.write(("--" + boundary + "\r\n").getBytes());
            outputStream.write(
                    ("Content-Disposition: form-data; name=\"images\"; filename=\"" + file.getName() + "\"\r\n")
                            .getBytes());
            outputStream.write(("Content-Type: application/octet-stream\r\n").getBytes());
            outputStream.write(("\r\n").getBytes());

            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = fileInputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }

            outputStream.write(("\r\n").getBytes());
            outputStream.write(("--" + boundary + "--\r\n").getBytes());
        }

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
            System.out.println(jsonResponse);
            // Close the connection
            connection.disconnect();

        } else {
            connection.disconnect();
            throw new IOException("Failed to connect to OpenDroneMap");
        }
    }

}
