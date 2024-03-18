package photobox;

import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.Dimension;
import java.io.File;

import javax.swing.BoxLayout;
import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JRadioButton;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.UIManager;
import javax.swing.text.DefaultCaret;

public class ConnectorGUI extends JFrame {
    private Connector connector;
    private JTextField textHostname;
    private JTextField textPort;
    private JButton connect;
    private JTextArea logArea;
    private ButtonGroup selectSfmSoftware;
    private JRadioButton rODM;
    private JRadioButton rMetashape;
    private JButton photoButton;
    private JButton directoryButton;
    private JRadioButton rDownload;

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

        JMenuBar menuBar = new JMenuBar();
        JMenu menu = new JMenu("File");

        JMenuItem loadFolder = new JMenuItem("Load Folder");
        loadFolder.addActionListener((e) -> {
            JFileChooser fileChooser = new JFileChooser(connector.getDirectory());
            fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            int option = fileChooser.showOpenDialog(this);
            if (option == JFileChooser.APPROVE_OPTION) {
                File file = fileChooser.getSelectedFile();
                this.connector.processPhotos(file.getAbsolutePath());
            }
        });
        menu.add(loadFolder);

        JMenuItem exit = new JMenuItem("Exit");
        exit.addActionListener((e) -> {
            System.exit(0);
        });
        menu.add(exit);
        menuBar.add(menu);

        JMenu about = new JMenu("About...");
        about.addActionListener((e) -> {
            JOptionPane.showMessageDialog(null, "PhotoBoxConnector\n\nAuthor: Florian Timm\nVersion: 0.1",
                    "About PhotoBoxConnector", JOptionPane.INFORMATION_MESSAGE);
        });
        menuBar.add(about);

        this.setJMenuBar(menuBar);

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

        this.rDownload = new JRadioButton("Just download");
        this.rDownload.setActionCommand("Download");
        this.rDownload.setSelected(connector.getSoftware().equals("Download"));
        left.add(this.rDownload);
        this.rDownload.addActionListener((e) -> {
            connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        });

        this.rMetashape = new JRadioButton("Agisoft Metashape");
        this.rMetashape.setActionCommand("Metashape");
        this.rMetashape.setSelected(connector.getSoftware().equals("Metashape"));
        left.add(this.rMetashape);
        this.rMetashape.addActionListener((e) -> {
            connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        });

        this.rODM = new JRadioButton("OpenDroneMap");
        this.rODM.setActionCommand("ODM");
        this.rODM.setSelected(connector.getSoftware().equals("ODM"));
        left.add(this.rODM);
        this.rODM.addActionListener((e) -> {
            connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        });

        this.selectSfmSoftware = new ButtonGroup();
        this.selectSfmSoftware.add(rMetashape);
        this.selectSfmSoftware.add(rODM);
        this.selectSfmSoftware.add(rDownload);

        this.connect = new JButton("Connect");
        this.connect.addActionListener((e) -> {
            connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
            connector.setHost(textHostname.getText());
            connector.setPort(Integer.parseInt(this.textPort.getText()));
            connector.toggleConnect();
        });
        left.add(this.connect);

        JPanel top = new JPanel();
        top.setLayout(new BoxLayout(top, javax.swing.BoxLayout.X_AXIS));
        cp.add(top, BorderLayout.NORTH);

        JTextField directoryTextField = new JTextField();
        directoryTextField.setEditable(false);
        directoryTextField.setText(connector.getDirectory().getAbsolutePath());
        directoryTextField.setEnabled(false);
        top.add(directoryTextField);

        this.directoryButton = new JButton("Select Directory");
        this.directoryButton.addActionListener((e) -> {
            JFileChooser fileChooser = new JFileChooser(connector.getDirectory());
            fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            int option = fileChooser.showOpenDialog(this);
            if (option == JFileChooser.APPROVE_OPTION) {
                File file = fileChooser.getSelectedFile();
                directoryTextField.setText(file.getAbsolutePath());
                connector.setDirectory(file);
            }
        });
        top.add(this.directoryButton);

        this.logArea = new JTextArea();
        this.logArea.setEditable(false);
        this.logArea.setLineWrap(true);
        this.logArea.setWrapStyleWord(true);
        JScrollPane scrollPane = new JScrollPane(this.logArea);
        cp.add(scrollPane, java.awt.BorderLayout.CENTER);
        DefaultCaret caret = (DefaultCaret) this.logArea.getCaret();
        caret.setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE);

        this.photoButton = new JButton("Take Photo");
        this.photoButton.addActionListener((e) -> {
            connector.takePhoto();
        });
        cp.add(this.photoButton, java.awt.BorderLayout.SOUTH);
        this.photoButton.setEnabled(false);

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
        this.directoryButton.setEnabled(enabled);
        this.textHostname.setEnabled(enabled);
        this.textPort.setEnabled(enabled);
        this.rODM.setEnabled(enabled);
        this.rMetashape.setEnabled(enabled);
        this.photoButton.setEnabled(!enabled);
    }

    protected void log(String message) {
        this.logArea.append(message + "\n");
    }
}
