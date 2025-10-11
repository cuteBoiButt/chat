#include <ui/loginscreen.h>
#include "ui_loginscreen.h"

LoginScreen::LoginScreen(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::LoginScreen) {
    ui->setupUi(this);

    // When the button in our UI is clicked, emit our custom signal
    connect(ui->disconnectButton, &QPushButton::clicked, this, &LoginScreen::disconnectClicked);
}

LoginScreen::~LoginScreen() {
    delete ui;
}
