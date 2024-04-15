package photobox.odm;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;

import org.json.JSONObject;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import photobox.Connector;

public class OdmWebHookServer implements HttpHandler {

    private Connector connector;
    private OdmClient odmClient;
    private Thread thread;

    public OdmWebHookServer(Connector connector, OdmClient odmClient) {
        super();
        this.connector = connector;
        this.odmClient = odmClient;
    }

    public void run() {

        try {
            HttpServer server = HttpServer.create(new InetSocketAddress(3001), 0);

            server.createContext("/webhook", this);
            server.setExecutor(null); // creates a default executor
            this.thread = new Thread(() -> {
                server.start();
            });
            this.thread.start();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    public void stop() {
        this.thread.interrupt();
    }

    @Override
    public void handle(HttpExchange t) throws IOException {
        StringBuilder sb = new StringBuilder();
        InputStream ios = t.getRequestBody();
        int i;
        while ((i = ios.read()) != -1) {
            sb.append((char) i);
        }
        JSONObject json = new JSONObject(sb.toString());
        this.odmClient.processWebhook(json);

        String response = "Moin!";
        t.sendResponseHeaders(200, response.length());
        OutputStream os = t.getResponseBody();
        os.write(response.getBytes());
        os.close();
    }
}
