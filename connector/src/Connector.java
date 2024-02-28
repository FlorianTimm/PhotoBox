import java.io.File;

class Connector {
    private int port = 50267;
    private String host = "localhost";
    private ConnectorGUI gui;
    private boolean isConnected = false;
    private PhotoBoxClient photoBox;
    private SfmClient sfmClient;
    private String software = "Metashape";
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

    public void toggleConnect() {
        if (this.isConnected) {
            this.disconnect();
        } else {
            this.connect();
        }
    }

    public boolean connect() {
        this.photoBox = new PhotoBoxClient(this.host, this.port, this);

        if (!this.photoBox.connect()) {
            return false;
        }

        if (this.software.equals("Metashape")) {
            this.sfmClient = new MetashapeClient(this);
        } else {
            this.sfmClient = new ODMClient(this);
        }

        if (!this.sfmClient.connect()) {
            this.photoBox.disconnect();
            return false;
        }

        this.gui.setConnected();
        this.isConnected = true;
        return true;
    }

    public void takePhoto() {
        if (!this.isConnected) {
            this.gui.log("Not connected");
            return;
        }

        this.photoBox.takePhoto();
    }

    public void disconnect() {
        if (!this.photoBox.disconnect()) {
            this.gui.log("Failed to disconnect from PhotoBox");
            return;
        }
        if (!this.sfmClient.disconnect()) {
            this.gui.log("Failed to disconnect from " + this.software);
            return;
        }

        this.isConnected = false;
        this.gui.setDisconnected();
    }

    // Getters and setters
    public void setHost(String host) {
        this.host = host;
    }

    public void setPort(int port) {
        this.port = port;
    }

    public void setSoftware(String software) {
        this.software = software;
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
