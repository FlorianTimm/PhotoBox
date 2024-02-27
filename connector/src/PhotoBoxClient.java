public class PhotoBoxClient {

    private final String host;
    private final int port;
    private Connector connector;

    public PhotoBoxClient(String host, int port, Connector connector) {
        this.host = host;
        this.port = port;
        this.connector = connector;
    }

    public boolean connect() {
        this.connector.log("Connecting to " + this.host + ":" + this.port);
        return true;
    }

    public void disconnect() {
        this.connector.log("Disconnecting from " + this.host + ":" + this.port);
    }

}
