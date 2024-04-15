package photobox.odm;

import java.io.IOException;
import org.json.JSONObject;

import photobox.Connector;
import photobox.SfmClient;

public class OdmClient implements SfmClient {

    private final Connector connector;
    private String baseURL;
    private OdmWebHookServer whs;

    public OdmClient(Connector connector) {
        this.connector = connector;
        this.baseURL = "http://localhost:3000";
    }

    public boolean connect() {
        try {
            OdmApi api = new OdmApi(baseURL);
            JSONObject jsonResponse = api.request("/info");
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
            this.whs = new OdmWebHookServer(connector, this);
            new Thread("OdmWebHookServerThread") {
                public void run() {
                    whs.run();
                }
            }.start();
        }
    }

    protected void processWebhook(JSONObject json) {
        connector.log("Received webhook");
        int statusCode = json.getJSONObject("status").getInt("code");
        String taskId = json.getString("uuid");
        if (statusCode == 100) {
            this.connector.log("Task " + taskId + " is done");
        } else {
            this.connector.log("Task " + taskId + " failed");
        }
    }

    public boolean disconnect() {
        // connector.log("Disconnected from OpenDroneMap");
        return true;
    }

    @Override
    public void processPhotos(String destDir) {
        this.connector.log("Processing photos");

        OdmProject project = new OdmProject(connector, baseURL, destDir);
        new Thread("OdmProcessPhotosThread") {
            public void run() {
                project.run();
            }
        }.start();
    }

}
