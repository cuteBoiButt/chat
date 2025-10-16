#pragma once

#include <QWidget>

namespace Ui { class LoginScreen; }

class LoginScreen : public QWidget {
    Q_OBJECT

public:
    explicit LoginScreen(QWidget *parent = nullptr);
    ~LoginScreen();

signals:
    // Signal to notify the main window
    void disconnectClicked();

private:
    Ui::LoginScreen *ui;
};
