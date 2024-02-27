
import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.Dimension;
import java.awt.event.ActionEvent;

import javax.swing.BoxLayout;
import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.UIManager;

public class ConnectorGUI extends JFrame implements java.awt.event.ActionListener {
    private Connector connector;
    private JTextField textHostname;
    private JTextField textPort;
    private JButton connect;
    private JTextArea logArea;
    private ButtonGroup selectSfmSoftware;
    private JRadioButton rODM;
    private JRadioButton rMetashape;

    public ConnectorGUI(Connector connector) {
        super("PhotoBoxConnector");

        this.connector = connector;
        this.setSize(600, 400);
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setIconImage(getIconImage());

        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }

        Container cp = this.getContentPane();
        cp.setLayout(new BorderLayout());

        JPanel left = new JPanel();
        left.setLayout(new BoxLayout(left, javax.swing.BoxLayout.Y_AXIS));
        left.setMaximumSize(new Dimension(300, 600));
        left.setSize(new Dimension(300, 600));
        cp.add(left, BorderLayout.WEST);

        left.add(new JLabel("Hostname"));
        this.textHostname = new JTextField();
        this.textHostname.setText(this.connector.getHost());
        this.textHostname.setMaximumSize(new Dimension(300, 30));
        left.add(this.textHostname);

        left.add(new JLabel("Port"));
        this.textPort = new JTextField();
        this.textPort.setText(Integer.toString(this.connector.getPort()));
        this.textPort.setMaximumSize(new Dimension(300, 30));
        left.add(this.textPort);

        this.rMetashape = new JRadioButton("Agisoft Metashape");
        this.rMetashape.setActionCommand("Metashape");
        this.rMetashape.setSelected(connector.getSoftware().equals("Metashape"));
        left.add(this.rMetashape);

        this.rODM = new JRadioButton("OpenDroneMap");
        this.rODM.setActionCommand("ODM");
        this.rODM.setSelected(connector.getSoftware().equals("ODM"));
        left.add(this.rODM);

        this.selectSfmSoftware = new ButtonGroup();
        this.selectSfmSoftware.add(rMetashape);
        this.selectSfmSoftware.add(rODM);
        this.connect = new JButton("Connect");
        this.connect.addActionListener(this);
        left.add(this.connect);

        this.logArea = new JTextArea();
        this.logArea.setEditable(false);
        this.logArea.setLineWrap(true);
        this.logArea.setWrapStyleWord(true);
        JScrollPane scrollPane = new JScrollPane(this.logArea);
        cp.add(scrollPane, java.awt.BorderLayout.CENTER);

        this.requestFocus();
        // this.pack();

        this.setLocationRelativeTo(null);

        this.setVisible(true);
    }

    public void setConnected() {
        toggleInput(false);
        this.connect.setText("Disconnect");
    }

    public void setDisconnected() {
        toggleInput(true);
        this.connect.setText("Connect");
    }

    private void toggleInput(boolean enabled) {
        this.textHostname.setEnabled(enabled);
        this.textPort.setEnabled(enabled);
        this.rODM.setEnabled(enabled);
        this.rMetashape.setEnabled(enabled);
    }

    @Override
    public void actionPerformed(ActionEvent arg0) {
        connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        connector.setHost(textHostname.getText());
        connector.setPort(Integer.parseInt(this.textPort.getText()));
        connector.toggleConnect();
    }

    protected void log(String message) {
        this.logArea.append(message + "\n");
    }
}
