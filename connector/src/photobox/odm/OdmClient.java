package photobox.odm;

import java.io.IOException;
import org.json.JSONObject;

import photobox.Connector;
import photobox.SfmClient;

public class OdmClient extends SfmClient {
    private String baseURL;

    public OdmClient(Connector connector, String baseURL) {
        super(connector);
        this.baseURL = baseURL; // "http://localhost:3000";
    }

    public boolean connect() {
        try {
            OdmApi api = new OdmApi(baseURL);
            JSONObject jsonResponse = api.request("/info");
            connector.log("Connected to OpenDroneMap");
            connector.log("OpenDroneMap version: " + jsonResponse.getString("version"));
            return true;
        } catch (IOException e) {
            connector.log("Failed to connect to OpenDroneMap");
            return false;
        }
    }

    public boolean disconnect() {
        // connector.log("Disconnected from OpenDroneMap");
        return true;
    }

    @Override
    public void processPhotos(String destDir) {
        connector.log("Processing photos");

        OdmProject project = new OdmProject(connector, baseURL, destDir);
        new Thread("OdmProcessPhotosThread") {
            public void run() {
                project.run();
            }
        }.start();
    }

}
