#include <ui/mainwindow.h>
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow) {
    ui->setupUi(this);

    // Start on the connect page (index 0)
    ui->stackedWidget->setCurrentIndex(0);

    // Logic 1: When the connect page's button is clicked...
    connect(ui->connectPage, &ConnectWidget::connectClicked, this, [this]() {
        // ...switch the stacked widget to the login page (index 1)
        ui->stackedWidget->setCurrentIndex(1);
    });

    // Logic 2: When the login page's button is clicked...
    connect(ui->loginPage, &LoginScreen::disconnectClicked, this, [this]() {
        // ...switch the stacked widget back to the connect page (index 0)
        ui->stackedWidget->setCurrentIndex(0);
    });
}

MainWindow::~MainWindow() {
    delete ui;
}
