import java.io.File;
import java.util.ArrayList;

import javax.swing.JOptionPane;

import com.agisoft.metashape.Document;
import com.agisoft.metashape.License;
import com.agisoft.metashape.Progress;

public class MetashapeClient implements Progress, SfmClient {

    private final Connector connector;
    private Document project;
    private String projectFileName;

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

    private boolean createProject(String filename) throws RuntimeException {
        try {
            this.projectFileName = filename;
            this.project = new Document();
            this.project.save(this.projectFileName, this);
            // doc.close();
            connector.log("Project created");
            return true;
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to create project");
        }
    }

    private void closeAndSaveProject(Document doc) {
        try {
            this.project.save(this.projectFileName, this);
            this.project.close();
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to save and close project");
        }
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
        this.connector.log("Processing photos");
        try {
            this.createProject(destDir + "/project.psx");
            this.addPhotos(destDir);
            this.closeAndSaveProject(this.project);
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
        }
    }

    private void addPhotos(String destDir) {
        this.connector.log("Adding photos");
        try {
            File[] files = new File(destDir).listFiles();
            ArrayList<String> photoPaths = new ArrayList<String>();
            for (File file : files) {
                if (file.isFile() && file.getName().endsWith(".jpg")) {
                    photoPaths.add(file.getAbsolutePath());
                }
            }
            this.project.addChunk().addPhotos(photoPaths.toArray(new String[photoPaths.size()]), this);
        } catch (Exception e) {
            this.connector.log(e.getMessage());
            e.printStackTrace();
            throw new RuntimeException("Failed to add photos");
        }
    }

    // implement Progress

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
