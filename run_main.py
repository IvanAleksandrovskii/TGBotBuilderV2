# run_main.py

from gunicorn_app import Application, get_app_options

from main import main_app


def main():
    app = Application(
        app=main_app,
        options=get_app_options()
    )
    
    app.run()


if __name__ == "__main__":
    main()
