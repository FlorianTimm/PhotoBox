package photobox;

import java.io.File;

import photobox.metashape.MetashapeClient;

public class Connector {
    private int port = 50267;
    private String host = "localhost";
    private ConnectorGUI gui;
    private boolean isConnected = false;
    private PhotoBoxClient photoBox;
    private SfmClient sfmClient;
    private String software = "Download";
    private File directory;

    public static void main(String[] args) {
        new Connector(args);
    }

    public Connector(String[] args) {
        // Regex to match a hostname or an IP address
        final String regex = "(^([A-Za-z](\\w+\\.)*\\w+)|^(\\d{1,3}.){3}\\d{1,3})(\\:\\d{1,5})?";

        // If the argument is a valid hostname or IP address, use it
        for (String arg : args) {
            if (arg.matches(regex)) {
                String[] h = args[0].split(":");
                this.host = h[0];
                if (h.length > 1) {
                    this.port = Integer.parseInt(h[1]);
                }
            }
            break;
        }

        this.directory = new File(System.getProperty("user.home") + "/PhotoBox");

        this.gui = new ConnectorGUI(this);

        log("PhotoBoxConnector started");

    }

    public boolean toggleConnect() {
        if (this.isConnected) {
            return !this.disconnect();
        } else {
            return this.connect();
        }
    }

    public boolean connect() {
        this.photoBox = new PhotoBoxClient(this.host, this.port, this);

        if (!this.photoBox.connect()) {
            return false;
        }

        if (!this.sfmClient.connect()) {
            this.photoBox.disconnect();
            return false;
        }
        this.photoBox.setSfmClient(this.sfmClient);
        this.gui.setConnected();
        this.isConnected = true;
        return true;
    }

    public void processPhotos(String destDir) {
        if (this.sfmClient == null) {
            this.setSoftware(this.software);
            return;
        }
        boolean wasConnected = this.isConnected;
        if (!wasConnected) {
            this.gui.log("Not connected");
            this.sfmClient.connect();
        }
        this.sfmClient.processPhotos(destDir);
        if (!wasConnected) {
            this.sfmClient.disconnect();
        }
    }

    public void takePhoto() {
        if (!this.isConnected) {
            this.gui.log("Not connected");
            return;
        }

        this.photoBox.takePhoto();
    }

    public boolean disconnect() {
        if (!this.photoBox.disconnect()) {
            this.gui.log("Failed to disconnect from PhotoBox");
            return false;
        }
        if (!this.sfmClient.disconnect()) {
            this.gui.log("Failed to disconnect from " + this.software);
            return false;
        }

        this.isConnected = false;
        this.gui.setDisconnected();
        return true;
    }

    // Getters and setters
    public void setHost(String host) {
        this.host = host;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public void setSoftware(String software) throws IllegalArgumentException {
        this.software = software;
        if (this.software.equals("Metashape")) {
            this.sfmClient = new MetashapeClient(this);
        } else if (this.software.equals("ODM")) {
            this.sfmClient = new ODMClient(this);
        } else if (this.software.equals("Download")) {
            this.sfmClient = new DownloadClient();
        } else {
            this.gui.log("Invalid software");
            throw new IllegalArgumentException("Invalid software");
        }
    }

    public String getHost() {
        return this.host;
    }

    public int getPort() {
        return this.port;
    }

    public String getSoftware() {
        return this.software;
    }

    public boolean isConnected() {
        return this.isConnected;
    }

    public void log(String message) {
        System.out.println(message);
        this.gui.log(message);
    }

    public File getDirectory() {
        return this.directory;
    }

    public void setDirectory(File directory) {
        this.directory = directory;
    }
}
