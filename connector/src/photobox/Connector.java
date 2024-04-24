package photobox;

import java.io.File;

import javax.swing.SwingUtilities;

import photobox.metashape.MetashapeClient;
import photobox.odm.OdmClient;

public class Connector {
    // TODO: Save the last used host and port in a file
    // https://www.codejava.net/coding/reading-and-writing-configuration-for-java-application-using-properties-class

    private int port = 50267;
    private String host = "192.168.1.1";
    private ConnectorGui gui;
    private boolean isConnected = false;
    private PhotoBoxClient photoBox;
    private SfmClient sfmClient;
    private String software = "Download";
    private File directory;
    private boolean calcModel = true;
    private String odmUrl = "http://localhost:3000";

    public static void main(String[] args) {
        new Connector(args);
    }

    private Connector(String[] args) {
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

        this.gui = new ConnectorGui(this);
        new Thread("GUI Thread") {
            public void run() {
                gui.startGui();
            }
        }.start();

        log("PhotoBoxConnector started");

    }

    protected boolean toggleConnect() {
        if (this.isConnected) {
            return !this.disconnect();
        } else {
            return this.connect();
        }
    }

    private boolean connect() {
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

    protected void processPhotos(String destDir) {
        if (this.sfmClient == null) {
            this.setSoftware(this.software);
            return;
        }
        boolean wasConnected = this.isConnected;
        if (!wasConnected) {
            this.log("Not connected");
            this.sfmClient.connect();
        }
        this.sfmClient.processPhotos(destDir);
        if (!wasConnected) {
            this.sfmClient.disconnect();
        }
    }

    protected void takePhoto() {
        if (!this.isConnected) {
            this.log("Not connected");
            return;
        }

        this.photoBox.takePhoto();
    }

    private boolean disconnect() {
        if (!this.photoBox.disconnect()) {
            this.log("Failed to disconnect from PhotoBox");
            return false;
        }
        if (!this.sfmClient.disconnect()) {
            this.log("Failed to disconnect from " + this.software);
            return false;
        }

        this.isConnected = false;
        this.gui.setDisconnected();
        return true;
    }

    // Getters and setters
    protected void setHost(String host) {
        this.host = host;
    }

    protected void setPort(int port) {
        this.port = port;
    }

    protected void setSoftware(String software) throws IllegalArgumentException {
        this.software = software;
        if (this.software.equals("Metashape")) {
            this.sfmClient = new MetashapeClient(this);
        } else if (this.software.equals("ODM")) {
            this.sfmClient = new OdmClient(this, this.getOdmUrl());
        } else if (this.software.equals("Download")) {
            this.sfmClient = new DownloadClient(this);
        } else {
            this.log("Invalid software");
            throw new IllegalArgumentException("Invalid software");
        }
    }

    protected String getHost() {
        return this.host;
    }

    protected int getPort() {
        return this.port;
    }

    protected String getSoftware() {
        return this.software;
    }

    public void log(String message) {
        System.out.println(message);
        SwingUtilities.invokeLater(() -> {
            this.gui.log(message);
        });
    }

    protected File getDirectory() {
        return this.directory;
    }

    protected void setDirectory(File directory) {
        this.directory = directory;
    }

    protected void setCalculateModel(boolean selected) {
        this.calcModel = selected;
    }

    public boolean getCalculateModel() {
        return this.calcModel;
    }

    public String getOdmUrl() {
        return this.odmUrl;
    }

    public void setOdmUrl(String odmUrl) {
        this.odmUrl = odmUrl;
    }

    public ConnectorGui getGui() {
        return this.gui;
    }
}
