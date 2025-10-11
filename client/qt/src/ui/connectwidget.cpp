#include <ui/connectwidget.h>
#include "ui_connectwidget.h"

ConnectWidget::ConnectWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::ConnectWidget) {
    ui->setupUi(this);

    // When the button in our UI is clicked, emit our custom signal
    connect(ui->connectButton, &QPushButton::clicked, this, &ConnectWidget::connectClicked);
}

ConnectWidget::~ConnectWidget() {
    delete ui;
}

