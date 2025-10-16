import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

/**
 * UI panel displayed in the main window.
 * Shows a message and a button that triggers backend logic.
 */
Rectangle {
    id: root
    color: "#f0f0f0"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // Display backend message with automatic updates
        Text {
            text: backend.message
            font.pixelSize: 18
            Layout.alignment: Qt.AlignHCenter
        }

        // Button calls backend slot directly
        Button {
            text: "Click Me"
            onClicked: backend.onButtonClicked()
            Layout.alignment: Qt.AlignHCenter
        }
    }
}
