import java.util.ArrayList;

import javax.swing.JOptionPane;

import com.agisoft.metashape.Document;
import com.agisoft.metashape.License;
import com.agisoft.metashape.Progress;

public class MetashapeClient implements Progress, SfmClient {

    private final Connector connector;

    public MetashapeClient(Connector connector) {
        this.connector = connector;

    }

    public boolean connect() {
        if (!loadLibrary()) {
            connector.log("Failed to load library");
            return false;
        }

        if (!testLicense()) {
            connector.log("Failed to validate license");
            return false;
        }
        connector.log("Connected to Metashape");
        return true;
    }

    public boolean disconnect() {
        connector.log("Disconnected from Metashape");
        return true;
    }

    public boolean createProject() {
        return createProject("project.psx");
    }

    public boolean createProject(String filename) {
        try {
            Document doc = new Document();
            doc.save("project.psx", this);
            doc.close();
            connector.log("Project created");
            return true;
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
        }
        return false;
    }

    private boolean loadLibrary() {
        ArrayList<Error> errors = new ArrayList<Error>();
        try {
            System.loadLibrary("metashape");
            return true;
        } catch (UnsatisfiedLinkError e) {
            errors.add(e);
        }

        String currentDirectory = System.getProperty("user.dir");
        String os = System.getProperty("os.name").toLowerCase();
        String arch = System.getProperty("os.arch").toLowerCase();
        String path = "";
        if (os.contains("win") && arch.contains("64")) {
            path = "/lib/jniLibs/win64/metashape.dll";
        } else if (os.contains("win") && arch.contains("32")) {
            path = "/lib/jniLibs/win32/metashape.dll";
        } else if (os.toLowerCase().contains("mac")) {
            path = "/lib/jniLibs/macosx64/libmetashape.dylib";
        } else if (os.toLowerCase().contains("nix") || os.toLowerCase().contains("nux")) {
            path = "/lib/jniLibs/linux64/libmetashape.so";
        }

        try {
            System.load(currentDirectory + path);
            return true;
        } catch (UnsatisfiedLinkError e) {
            errors.add(e);
        }

        for (Error e : errors) {
            connector.log(e.getMessage());
            e.printStackTrace();
        }
        return false;
    }

    private boolean testLicense() {
        if (License.isValid()) {
            return true;
        }
        JOptionPane.showMessageDialog(null, "License is invalid");
        return false;
    }

    @Override
    public void progress(double progress) {
        this.connector.log("Progress: " + progress);
    }

    @Override
    public void status(String status) {
        this.connector.log("Status: " + status);
    }

    @Override
    public boolean aborted() {
        this.connector.log("Aborted");
        return false;
    }
}
