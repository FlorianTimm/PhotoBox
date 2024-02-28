import java.io.BufferedReader;
import java.io.File;
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

            String message = "Moin";

            // Send message
            OutputStream outputStream = this.socket.getOutputStream();
            InputStream inputStream = this.socket.getInputStream();

            this.receiver = new Thread(() -> {
                try {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream));
                    while (true) {
                        String line = reader.readLine();
                        if (line != null) {
                            connector.log(line);
                            String[] w = line.split(":", 2);
                            for (int i = 0; i < w.length; i++) {
                                w[i] = w[i].trim();
                                connector.log(w[i]);
                            }
                            switch (w[0]) {
                                case "photoZip":
                                    downloadPhotos(w[1]);
                                    break;
                                default:
                                    break;
                            }
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

            // BufferedReader reader = new BufferedReader(new
            // InputStreamReader(inputStream));

            outputStream.write(message.getBytes());
            outputStream.flush();

            // String line = reader.readLine();

            // System.out.println(line);

            return true;
        } catch (IOException e) {
            e.printStackTrace();
            this.connector.log(e.getMessage());
        }
        return false;
    }

    private void downloadPhotos(String zipName) {
        connector.log("Downloading photos");
        File dir = connector.getDirectory();
        if (dir == null) {
            connector.log("No directory selected");
            return;
        } else if (!dir.isDirectory()) {
            dir.mkdir();
            connector.log(dir.getAbsolutePath() + " is created as a directory.");
        }
        connector.log("Downloading photos to " + dir.getAbsolutePath());
        String urlString = "http://" + zipName;
        String filename = urlString.substring(urlString.lastIndexOf('/') + 1);
        String zipTarget = dir.getAbsolutePath() + "/" + filename;
        try {
            URL website = new URL(urlString);
            ReadableByteChannel rbc = Channels.newChannel(website.openStream());
            FileOutputStream fos = new FileOutputStream(zipTarget);
            fos.getChannel().transferFrom(rbc, 0, Long.MAX_VALUE);
            fos.close();
            connector.log("Downloaded " + zipName);
            unzipFile(zipTarget);
        } catch (MalformedURLException e) {
            connector.log(zipName + " is not a valid URL");
            e.printStackTrace();
        } catch (IOException e) {
            connector.log("Could not download " + zipName);
            e.printStackTrace();
        }
    }

    private void unzipFile(String zipFilePath) {
        try {
            // from:
            // https://www.digitalocean.com/community/tutorials/java-unzip-file-example
            connector.log("Unzipping " + zipFilePath);
            String destDir = new File(zipFilePath).getAbsolutePath()
                    .substring(0, zipFilePath.lastIndexOf('.'));
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
                System.out.println("Unzipping to " + newFile.getAbsolutePath());
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
        } catch (FileNotFoundException e) {
            connector.log(zipFilePath + " not found");
            e.printStackTrace();
        } catch (ZipException e) {
            connector.log(zipFilePath + " is not a valid zip file");
            e.printStackTrace();
        } catch (IOException e) {
            connector.log("Could not unzip " + zipFilePath);
            e.printStackTrace();
        } finally {
            connector.log("Unzipped " + zipFilePath);
        }
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

}
