public interface SfmClient {
    public boolean connect();

    public boolean disconnect();

    public void processPhotos(String destDir);
}
