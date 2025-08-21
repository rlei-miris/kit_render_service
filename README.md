# Omniverse Kit Render Service

This is a Omniverse Kit based rendering service which exposes HTTP endpoints for opening a stage, and rendering
from input camera locations.

Only tested on Linux (Ubuntu-24.04)

## Clone the repo

Begin by cloning the `kit_render_service` to your local workspace:

```bash
git clone git@github.com:rlei-miris/kit_render_service.git
cd kit_render_service
```

## Build the project

**Linux:**
```bash
./repo.sh build
```

## Launch the service

**Linux:**
```bash
./repo.sh launch -- --no-window
```

## Try sending requests to the service

Open your webbrowser to http://localhost:8011/docs

Run the `/open_stage` endpoint to open a USD file, then `/render` to render from it.

