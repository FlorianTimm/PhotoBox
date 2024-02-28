public interface SfmClient {
    public boolean connect();

    public boolean disconnect();

    public boolean createProject(String filename);
}
