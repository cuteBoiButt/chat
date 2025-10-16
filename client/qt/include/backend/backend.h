#pragma once

#include <QObject>

namespace qt {

/**
 * Backend handles application logic and state management.
 * Exposes properties and slots to QML for UI interaction.
 */
class Backend : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString message READ message WRITE setMessage NOTIFY messageChanged)

public:
    explicit Backend(QObject *parent = nullptr);

    // Property accessors
    QString message() const;
    void setMessage(const QString &msg);

public slots:
    /**
     * Called when user clicks button in QML.
     * Updates the message property.
     */
    void onButtonClicked();

signals:
    /**
     * Emitted when message property changes.
     * QML automatically updates bound text when this fires.
     */
    void messageChanged();

private:
    QString m_message;
};

}  // namespace qt
