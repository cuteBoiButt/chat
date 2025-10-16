#include <backend/backend.h>

namespace qt {

Backend::Backend(QObject *parent)
    : QObject(parent), m_message("Hello from Backend")
{
}

QString Backend::message() const
{
    return m_message;
}

void Backend::setMessage(const QString &msg)
{
    // Only update if value actually changed (avoids redundant signal emissions)
    if (m_message != msg) {
        m_message = msg;
        emit messageChanged();
    }
}

void Backend::onButtonClicked()
{
    setMessage("Button clicked from QML!");
}

}  // namespace qt
