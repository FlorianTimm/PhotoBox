import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.Socket;

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

    public boolean disconnect() {
        this.connector.log("Disconnecting from " + this.host + ":" + this.port);
        try {
            this.receiver.interrupt();
            this.socket.close();
            return true;
        } catch (IOException e) {
            e.printStackTrace();
            this.connector.log(e.getMessage());
        }
        return false;
    }

}
