
public class ODMClient implements SfmClient {

    private final Connector connector;

    public ODMClient(Connector connector) {
        this.connector = connector;
    }

    public boolean connect() {
        // TODO: Implement connection to OpenDroneMap
        connector.log("Connecting to OpenDroneMap");
        return true;
    }

    public boolean disconnect() {
        // TODO: Implement disconnection from OpenDroneMap
        connector.log("Disconnected from OpenDroneMap");
        return true;
    }

    @Override
    public void processPhotos(String destDir) {
        // TODO Auto-generated method stub
        return;
    }

}
