package photobox;

public class DownloadClient implements SfmClient {
    /**
     * Placeholder, if no Software is selected. Does nothing.
     * 
     */

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
