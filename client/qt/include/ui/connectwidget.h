#pragma once

#include <QWidget>

namespace Ui { class ConnectWidget; }

class ConnectWidget : public QWidget {
    Q_OBJECT
public:
    explicit ConnectWidget(QWidget *parent = nullptr);
    ~ConnectWidget();

signals:
    // Signal to notify the main window
    void connectClicked();

private:
    Ui::ConnectWidget *ui;
};
