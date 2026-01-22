# GameDev National Workshop 🎮

Welcome to the GameDev National Workshop repository! This project is a curated collection of game development projects and AI agents designed for educational workshops. It covers a wide range of topics, including game logic implementation, computer vision for automated gameplay, and advanced AI techniques like Mixed Integer Programming and logical inference solvers.

## Tech Stack
- **Language:** Python
- **Frameworks:** Pygame
- **Build Tools:** py2exe, pipenv
- **Cloud/Capture:** mss (Screen Capture)

## Getting Started
To get the environment ready, we recommend using `pipenv` to manage your dependencies:

```bash
pipenv install
pipenv shell
```

## Deployment
We support multiple ways to deploy and run these projects locally or in specialized environments.

### Executable Build
For Windows users, you can package the projects into standalone executables using `py2exe`.

### Docker
If you prefer a containerized environment, you can use Docker to set up and run the workshop projects consistently. This ensures all Python dependencies and AI logic components work as expected.

1. **Build the Docker image:**
   ```bash
   docker build -t gamedev-workshop .
   ```

2. **Run the container:**
   ```bash
   docker run -it gamedev-workshop
   ```

*Note: Because some projects utilize Pygame and screen capture (mss), you may need to configure X11 forwarding or a virtual display (like Xvfb) to handle graphical output when running inside a container.*

## Contributing
Feel free to explore the projects and use them for your own learning or workshops! If you have suggestions or improvements, contributions are always welcome.