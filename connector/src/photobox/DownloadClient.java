package photobox;

public class DownloadClient extends SfmClient {
    /**
     * Placeholder, if no Software is selected. Does nothing.
     * 
     */

    public DownloadClient(Connector connector) {
        super(connector);
    }

    public boolean connect() {
        return true;
    }

    public boolean disconnect() {
        return true;
    }

    @Override
    public void processPhotos(String destDir) {
        return;
    }
}
