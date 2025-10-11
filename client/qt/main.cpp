#include <QApplication>
#include <QMainWindow>
#include <QPushButton>
#include <QLabel>
#include <QVBoxLayout>
#include <QWidget>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    QMainWindow window;
    window.setWindowTitle("Simple Qt App");
    window.resize(400, 300);
    
    QWidget *central = new QWidget(&window);
    QVBoxLayout *layout = new QVBoxLayout(central);
    
    QLabel *label = new QLabel("Hello, Qt!", central);
    label->setAlignment(Qt::AlignCenter);
    
    QPushButton *button = new QPushButton("Click Me!", central);
    
    layout->addWidget(label);
    layout->addWidget(button);
    
    QObject::connect(button, &QPushButton::clicked, [label]() {
        label->setText("Button Clicked!");
    });
    
    window.setCentralWidget(central);
    window.show();
    
    return app.exec();
}
