package photobox.odm;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.ProtocolException;
import java.net.URL;
import java.util.Map;

import org.json.JSONObject;

public class OdmApi {

    private String baseURL;

    public OdmApi(String baseURL) {
        this.baseURL = baseURL;
    }

    protected JSONObject request(String urlPart)
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

    /*
     * private void uploadFile(String urlPart, File file) throws IOException {
     * uploadFile(urlPart, file, file.getName());
     * }
     */

    protected JSONObject uploadFile(String urlPart, File file, String fileName) throws IOException {
        return request(urlPart, null, file, fileName);
    }

    protected JSONObject request(String urlPart, Map<String, String> parameter) throws IOException {
        return request(urlPart, parameter, null, null);
    }

    private JSONObject request(String urlPart, Map<String, String> parameter, File file,
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

}
