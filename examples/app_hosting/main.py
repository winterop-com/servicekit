"""Example service hosting static web applications."""

from servicekit.api import BaseServiceBuilder, ServiceInfo

# Create service with app hosting
app = (
    BaseServiceBuilder(
        info=ServiceInfo(
            id="app-hosting-demo",
            display_name="App Hosting Demo",
            version="1.0.0",
            summary="Demonstrates hosting static web apps with servicekit",
            description="This service hosts a sample dashboard app at /dashboard",
        )
    )
    .with_logging()
    .with_health()
    .with_system()
    .with_landing_page()
    # Mount single app from filesystem
    .with_app("apps/sample-dashboard")
    # Or auto-discover all apps in directory:
    # .with_apps("apps")
    # Or auto-discover apps from package resources:
    # .with_apps(("mycompany.webapps", "apps"))
    .build()
)

if __name__ == "__main__":
    from servicekit.api import run_app

    run_app(app)
