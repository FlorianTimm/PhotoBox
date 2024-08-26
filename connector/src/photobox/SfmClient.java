package photobox;

public abstract class SfmClient {
    protected final Connector connector;

    public SfmClient(Connector connector) {
        this.connector = connector;
    }

    public abstract boolean connect();

    public abstract boolean disconnect();

    public abstract void processPhotos(String destDir);
}
