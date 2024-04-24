package photobox;

import java.awt.BorderLayout;
import java.awt.Container;
import java.awt.Dimension;
import java.io.File;

import javax.swing.BoxLayout;
import javax.swing.ButtonGroup;
import javax.swing.JButton;
import javax.swing.JCheckBox;
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
import javax.swing.JTabbedPane;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import javax.swing.text.DefaultCaret;

public class ConnectorGui extends JFrame {
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
    private JMenuItem loadFolder;
    private JCheckBox checkboxCalc;
    private JScrollPane scrollPaneLog = null;
    private JTextField odmUrl;
    private JLabel odmUrlLabel;
    private JPanel processPanel;

    protected ConnectorGui(Connector connector) {
        super("PhotoBoxConnector");
        this.connector = connector;

        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }

        // Log-Area sofort erstellen
        this.logArea = new JTextArea();
        this.scrollPaneLog = new JScrollPane(this.logArea);

    }

    protected void startGui() {

        this.setSize(1000, 600);
        this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        this.setIconImage(getIconImage());

        JMenuBar menuBar = new JMenuBar();
        JMenu menu = new JMenu("File");

        this.loadFolder = new JMenuItem("Load Pictures from Folder...");
        this.loadFolder.addActionListener((e) -> {
            transferAllSettings();
            JFileChooser fileChooser = new JFileChooser(connector.getDirectory());
            fileChooser.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
            int option = fileChooser.showOpenDialog(this);
            if (option == JFileChooser.APPROVE_OPTION) {
                File file = fileChooser.getSelectedFile();
                this.connector.processPhotos(file.getAbsolutePath());
            }
        });
        menu.add(this.loadFolder);
        this.loadFolder.setEnabled(false);

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
            this.switchSfm();
        });

        this.rMetashape = new JRadioButton("Agisoft Metashape");
        this.rMetashape.setActionCommand("Metashape");
        this.rMetashape.setSelected(connector.getSoftware().equals("Metashape"));
        left.add(this.rMetashape);
        this.rMetashape.addActionListener((e) -> {
            this.switchSfm();
        });
        this.checkboxCalc = new JCheckBox("Calculate Model");
        this.checkboxCalc.setSelected(true);
        this.checkboxCalc.setVisible(false);
        left.add(this.checkboxCalc);

        this.rODM = new JRadioButton("OpenDroneMap");
        this.rODM.setActionCommand("ODM");
        this.rODM.setSelected(connector.getSoftware().equals("ODM"));
        left.add(this.rODM);
        this.rODM.addActionListener((e) -> {
            this.switchSfm();
        });

        this.odmUrlLabel = new JLabel("ODM-URL");
        this.odmUrlLabel.setVisible(false);
        left.add(this.odmUrlLabel);
        this.odmUrl = new JTextField();
        this.odmUrl.setText(this.connector.getOdmUrl());
        this.odmUrl.setMaximumSize(new Dimension(300, 30));
        this.odmUrl.setVisible(false);
        left.add(this.odmUrl);

        this.selectSfmSoftware = new ButtonGroup();
        this.selectSfmSoftware.add(rMetashape);
        this.selectSfmSoftware.add(rODM);
        this.selectSfmSoftware.add(rDownload);

        this.connect = new JButton("Connect");
        this.connect.addActionListener((e) -> {
            SwingUtilities.invokeLater(() -> {
                transferAllSettings();
                connector.toggleConnect();
            });
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

        JTabbedPane tabpane = new JTabbedPane();
        cp.add(tabpane, java.awt.BorderLayout.CENTER);

        this.processPanel = new JPanel();
        this.processPanel.setLayout(new BoxLayout(this.processPanel, BoxLayout.Y_AXIS));
        JScrollPane scrollPane = new JScrollPane(this.processPanel);
        JPanel processPanelScroll = new JPanel();
        processPanelScroll.setLayout(new BorderLayout());
        processPanelScroll.add(scrollPane, BorderLayout.CENTER);
        // tabpane.addTab("Process", scrollPane);
        tabpane.addTab("Process", processPanelScroll);

        JPanel logPanel = new JPanel();
        logPanel.setLayout(new BorderLayout());
        logPanel.add(scrollPaneLog, BorderLayout.CENTER);
        tabpane.addTab("Log", logPanel);

        // this.logArea = new JTextArea();
        this.logArea.setEditable(false);
        this.logArea.setLineWrap(true);
        this.logArea.setWrapStyleWord(true);
        // this.scrollPaneLog = new JScrollPane(this.logArea);

        DefaultCaret caret = (DefaultCaret) this.logArea.getCaret();
        caret.setUpdatePolicy(DefaultCaret.ALWAYS_UPDATE);

        this.photoButton = new JButton("Take Photo");
        this.photoButton.addActionListener((e) -> {
            SwingUtilities.invokeLater(() -> {
                connector.takePhoto();
            });
        });
        cp.add(this.photoButton, java.awt.BorderLayout.SOUTH);
        this.photoButton.setEnabled(false);

        this.requestFocus();
        // this.pack();

        this.setLocationRelativeTo(null);

        this.setVisible(true);
    }

    private void transferAllSettings() {
        connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        connector.setCalculateModel(this.checkboxCalc.isSelected());
        connector.setOdmUrl(this.odmUrl.getText());
        connector.setHost(textHostname.getText());
        connector.setPort(Integer.parseInt(this.textPort.getText()));
    }

    private void switchSfm() {
        this.checkboxCalc.setVisible(false);
        this.odmUrlLabel.setVisible(false);
        this.odmUrl.setVisible(false);
        this.connector.setSoftware(this.selectSfmSoftware.getSelection().getActionCommand());
        if (this.rDownload.isSelected()) {
            this.loadFolder.setEnabled(false);
            return;
        }
        this.loadFolder.setEnabled(true);
        if (this.rMetashape.isSelected()) {
            this.checkboxCalc.setVisible(true);
        }
        if (this.rODM.isSelected()) {
            this.odmUrlLabel.setVisible(true);
            this.odmUrl.setVisible(true);
        }
    }

    protected void setConnected() {
        toggleInput(false);
    }

    protected void setDisconnected() {
        toggleInput(true);
    }

    private void toggleInput(boolean enabled) {
        SwingUtilities.invokeLater(() -> {
            this.directoryButton.setEnabled(enabled);
            this.textHostname.setEnabled(enabled);
            this.textPort.setEnabled(enabled);
            this.rDownload.setEnabled(enabled);
            this.rODM.setEnabled(enabled);
            this.odmUrl.setEnabled(enabled);
            this.rMetashape.setEnabled(enabled);
            this.checkboxCalc.setEnabled(enabled);
            this.photoButton.setEnabled(!enabled);
            this.connect.setText(enabled ? "Connect" : "Disconnect");
        });
    }

    protected void log(String message) {
        this.logArea.append(message + "\n");
        // if (this.scrollPaneLog != null) {
        this.logArea.setCaretPosition(this.logArea.getText().length());
        scrollPaneLog.getVerticalScrollBar().setValue(scrollPaneLog.getVerticalScrollBar().getMaximum());
        // }
    }

    public void addToProcessPanel(ProcessGUI processGUI) {
        SwingUtilities.invokeLater(() -> {
            this.processPanel.add(processGUI);
            this.processPanel.revalidate();
        });
    }
}
