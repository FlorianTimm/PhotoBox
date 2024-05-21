package photobox;

import java.awt.Dimension;

import javax.swing.BoxLayout;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;

public abstract class ProcessGUI extends JPanel {
    private JProgressBar processBar;
    private JTextArea logArea;
    private Connector connector;
    private JScrollPane scrollPaneLog;

    protected ProcessGUI(Connector connector, String label) {
        super();
        this.connector = connector;

        initComponents(label);
        this.connector.getGui().addToProcessPanel(this);
    }

    private void initComponents(String label) {
        this.setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
        this.setBorder(javax.swing.BorderFactory.createTitledBorder(label));

        this.processBar = new JProgressBar();
        this.processBar.setStringPainted(true);
        this.add(processBar);

        this.logArea = new JTextArea();
        this.logArea.setEditable(false);
        this.scrollPaneLog = new JScrollPane(this.logArea);
        this.add(scrollPaneLog);

        this.setMaximumSize(new Dimension(Integer.MAX_VALUE, 200));

    }

    protected void setLabel(String label) {
        this.setBorder(javax.swing.BorderFactory.createTitledBorder(label));
    }

    protected void logProgress(int status) {
        // SwingUtilities.invokeLater(() -> {
        this.processBar.setValue(status);
        // });
    }

    public void log(String message) {
        // SwingUtilities.invokeLater(() -> {
        this.logArea.append(message + "\n");
        // });
        this.connector.log(message);
        this.logArea.setCaretPosition(this.logArea.getText().length());
        scrollPaneLog.getVerticalScrollBar().setValue(scrollPaneLog.getVerticalScrollBar().getMaximum());
    }
}
