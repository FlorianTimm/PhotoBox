package photobox.odm;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.BindException;
import java.net.InetSocketAddress;

import org.json.JSONObject;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

public class OdmWebHookServer implements HttpHandler {

    private OdmProject odmProject;
    private Thread thread;
    private int port;

    protected OdmWebHookServer(OdmProject odmProject) {
        super();
        this.odmProject = odmProject;
        this.port = 3001;

        while (true) {
            try {
                HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
                server.createContext("/webhook", this);
                server.setExecutor(null); // creates a default executor
                this.thread = new Thread(() -> {
                    server.start();
                });
                break;
            } catch (BindException e) {
                this.port++;
            } catch (IOException e) {
                odmProject.log("Error starting webhook server: " + e.getMessage());
            }
        }
    }

    protected void run() {
        System.out.println("Webhook server started on port " + this.port);
        this.thread.start();
    }

    protected void stop() {
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
        this.odmProject.processWebhook(json);

        String response = "Moin!";
        t.sendResponseHeaders(200, response.length());
        OutputStream os = t.getResponseBody();
        os.write(response.getBytes());
        os.close();
    }

    public int getPort() {
        return this.port;
    }
}
