package photobox;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileFilter;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.MalformedURLException;
import java.net.Socket;
import java.net.URL;
import java.net.UnknownHostException;
import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;
import java.util.zip.ZipEntry;
import java.util.zip.ZipException;
import java.util.zip.ZipInputStream;

public class PhotoBoxClient {

    private final String host;
    private final int port;
    private Connector connector;
    private Socket socket;
    private Thread receiver;
    private SfmClient sfmClient;

    public PhotoBoxClient(String host, int port, Connector connector) {
        this.host = host;
        this.port = port;
        this.connector = connector;
    }

    public boolean connect() {
        this.connector.log("Connecting to " + this.host + ":" + this.port);

        try {
            // Connect to port
            this.socket = new Socket(host, port);

            // Send message
            OutputStream outputStream = this.socket.getOutputStream();
            InputStream inputStream = this.socket.getInputStream();

            this.receiver = new Thread(() -> {
                try {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
                    while (true) {
                        String line = reader.readLine();
                        if (line != null) {
                            String[] w = line.split(":", 3);
                            for (int i = 0; i < w.length; i++) {
                                w[i] = w[i].trim();
                            }
                            switch (w[0]) {
                                case "heartbeat":
                                    // connector.log("Heartbeat");
                                    break;
                                case "photoZip":
                                    connector.log("Photos downloading: " + w[1]);
                                    downloadPhotos(w[1], w[2]);
                                    break;
                                case "aruco":
                                    connector.log("Aruco downloading: " + w[1]);
                                    downloadText(w[1], w[2]);
                                    break;
                                case "marker":
                                    connector.log("Marker downloading: " + w[1]);
                                    downloadText(w[1], w[2]);
                                    break;
                                case "meta":
                                    connector.log("Meta downloading: " + w[1]);
                                    downloadText(w[1], w[2]);
                                    break;
                                default:
                                    connector.log("Unknown message: " + line);
                                    break;
                            }
                            connector.log("Received: " + line);
                        }
                        if (Thread.interrupted()) {
                            break;
                        }
                    }
                } catch (IOException e) {
                    e.printStackTrace();
                }
            });

            this.receiver.setDaemon(true);
            this.receiver.setName("Receiver");
            this.receiver.start();

            String message = "time:" + System.currentTimeMillis() + "\n";

            outputStream.write(message.getBytes());
            outputStream.flush();

            return true;
        } catch (IOException e) {
            e.printStackTrace();
            this.connector.log(e.getMessage());
        }
        return false;
    }

    private void downloadPhotos(String id, String zipName) {
        String urlString = "http://" + zipName;
        String filename = urlString.substring(urlString.lastIndexOf('/') + 1);
        String zipTarget = download(urlString, id, filename);
        if (zipTarget == null) {
            return;
        }
        unzipFile(id, zipTarget);
    }

    private void downloadText(String id, String arucoName) {
        String urlString = "http://" + arucoName;
        String filename = urlString.substring(urlString.lastIndexOf('/') + 1);
        download(urlString, id, filename);
    }

    private String download(String urlString, String id, String filename) {
        connector.log("Downloading photos");
        File dir = connector.getDirectory();
        if (dir == null) {
            connector.log("No directory selected");
            return null;
        }

        File targetDir = new File(dir.getAbsolutePath() + File.separator + id);
        if (!targetDir.isDirectory()) {
            targetDir.mkdir();
            connector.log(targetDir.getAbsolutePath() + " is created as a directory.");
        }
        connector.log("Downloading photos to " + targetDir.getAbsolutePath());
        String targetPath = targetDir.getAbsolutePath() + "/" + filename;
        try {
            URL website = new URL(urlString);
            InputStream websiteStream;
            try {
                websiteStream = website.openStream();
            } catch (UnknownHostException e) {
                String path = website.toString();
                connector.log("Unknown host: " + website.getHost());
                connector.log("Trying to download from " + this.host);
                website = new URL(path.replace("http://" + website.getHost(), "http://" + this.host));
                websiteStream = website.openStream();
            }

            ReadableByteChannel rbc = Channels.newChannel(websiteStream);
            FileOutputStream fos = new FileOutputStream(targetPath);
            fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);
            fos.close();
            connector.log("Downloaded " + filename);
            checkReady(id, targetDir.getAbsolutePath());
            return targetPath;
        } catch (MalformedURLException e) {
            connector.log(urlString + " is not a valid URL");
            e.printStackTrace();
        } catch (IOException e) {
            connector.log("Could not download " + urlString);
            e.printStackTrace();
        }
        return null;
    }

    private void unzipFile(String id, String zipFilePath) {
        try {
            // from:
            // https://www.digitalocean.com/community/tutorials/java-unzip-file-example
            connector.log("Unzipping " + zipFilePath);
            String destDir = new File(zipFilePath).getParent();
            File desFile = new File(destDir);
            if (!desFile.exists()) {
                desFile.mkdir();
            }
            byte[] buffer = new byte[1024];
            FileInputStream fis;

            fis = new FileInputStream(zipFilePath);

            ZipInputStream zis = new ZipInputStream(fis);
            ZipEntry ze = zis.getNextEntry();
            while (ze != null) {
                String fileName = ze.getName();
                File newFile = new File(destDir + File.separator + fileName);
                this.connector.log("Unzipping to " + newFile.getAbsolutePath());
                // create directories for sub directories in zip
                new File(newFile.getParent()).mkdirs();
                FileOutputStream fos = new FileOutputStream(newFile);
                int len;
                while ((len = zis.read(buffer)) > 0) {
                    fos.write(buffer, 0, len);
                }
                fos.close();
                // close this ZipEntry
                zis.closeEntry();
                ze = zis.getNextEntry();
            }
            // close last ZipEntry
            zis.closeEntry();
            zis.close();
            fis.close();
            connector.log("Unzipped " + zipFilePath);
            checkReady(id, destDir);
        } catch (FileNotFoundException e) {
            connector.log(zipFilePath + " not found");
            e.printStackTrace();
        } catch (ZipException e) {
            connector.log(zipFilePath + " is not a valid zip file");
            e.printStackTrace();
        } catch (IOException e) {
            connector.log("Could not unzip " + zipFilePath);
            e.printStackTrace();
        }
    }

    private void checkReady(String id, String destDir) {
        if (sfmClient == null) {
            connector.log("SfmClient is not set");
            return;
        }
        if (!(new File(destDir + File.separator + "aruco.json").exists())) {
            connector.log("Aruco not found");
            return;
        }
        if (!(new File(destDir + File.separator + "marker.json").exists())) {
            connector.log("Marker not found");
            return;
        }
        if (!(new File(destDir + File.separator + "meta.json").exists())) {
            connector.log("Meta not found");
            return;
        }

        File files = new File(destDir);
        File[] jpg = files.listFiles(new FileFilter() {
            @Override
            public boolean accept(File pathname) {
                if (pathname.getName().toLowerCase().endsWith(".jpg")) {
                    return true;
                }
                return false;
            }
        });
        if (jpg.length == 0) {
            connector.log("No jpg files found");
            return;
        }
        sfmClient.processPhotos(destDir);
    }

    private void send(String message) {
        try {
            OutputStream outputStream = this.socket.getOutputStream();
            outputStream.write(message.getBytes());
            outputStream.flush();
        } catch (IOException e) {
            e.printStackTrace();
            this.connector.log(e.getMessage());
        }
    }

    public void takePhoto() {
        this.send("photo");
    }

    public boolean disconnect() {
        this.connector.log("Disconnecting from " + this.host + ":" + this.port);
        try {
            this.socket.close();
            this.receiver.interrupt();
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            this.connector.log(e.getMessage());
        }
        return false;
    }

    public void setSfmClient(SfmClient sfmClient) {
        this.sfmClient = sfmClient;
    }

}
