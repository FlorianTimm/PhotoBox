package photobox.metashape;

import java.util.ArrayList;
import javax.swing.JOptionPane;
import com.agisoft.metashape.License;

import photobox.Connector;
import photobox.SfmClient;

public class MetashapeClient extends SfmClient {

    public MetashapeClient(Connector connector) {
        super(connector);
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
    public void processPhotos(String destDir) {
        connector.log("Processing photos");
        MetashapeProject project = new MetashapeProject(connector, destDir);
        new Thread("MetashapeProcessPhotosThread") {
            public void run() {
                project.run();
            }
        }.start();
    }

}
