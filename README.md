# OSTIS Bibliography

<img src="https://github.com/ostis-apps/ostis-bibliography/actions/workflows/main.yml/badge.svg?branch=develop"> [![license](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

OSTIS Bibliography is an open-source knowledge base that serves as an intellectual reference system for bibliography on Open Semantic Technology for Intelligent Systems. The project aims to create a comprehensive and reliable resource for researchers, developers, and enthusiasts interested in the field.

## Installation

- Quick start using Docker Compose

  <details>
  
  <summary><b>Additional steps for Windows users</b></summary>

  Make sure you are using UNIX line endings inside the repository and `longpaths` are enabled, otherwise you may face problems during build or installation process. Use the commands below to reconfigure Git on your machine:

    ```sh
    git config --global core.autocrlf input
    git config --global core.longpaths true
    ```

  </details>

  Requirements: you will need [Docker](https://docs.docker.com/get-docker/) installed and running on your machine.

  ```sh
  git clone https://github.com/ostis-ai/ostis-web-platform
  cd ostis-web-platform
  # download images from Docker Hub
  docker compose pull
  # download KB and LaTeX docs plugin
  git submodule update --init --recursive
  # build knowledge base
  docker compose run machine build
  # launch web platform stack
  docker compose up
  ```

   <details>
   <summary> Building docker images locally </summary>

  This may come in handy e.g. when you want to use a custom branch of the sc-machine or sc-web.

  ### Requirements:

  1. In case you're using Windows, set up git using the installation instructions above
  2. Enable Docker BuildKit. You can use `DOCKER_BUILDKIT=1` shell variable for this.

  ### Build process

  ```sh
  git clone https://github.com/ostis-apps/ostis-bibliography
  git submodule update --init --recursive
  cd scripts
  ./prepare.sh no_build_sc_machine no_build_sc_web # download all submodules without compilation.
  cd ..
  docker compose build
  ```

   </details>

- Natively

  Note: Currently, only Ubuntu is supported by this installation method. If you're going to use it, it might take a while to download dependencies and compile the components. Use it only if you know what you're doing!

  ```sh
  cd ostis-web-platform/scripts/
  ./prepare.sh
  ```

## Usage

- Docker Compose

  ```sh
  # build the Knowledge Base.
  # Required before the first startup (or if you've made updates to KB sources)
  docker compose run machine build
  # start platform services and run web interface at localhost:8000
  docker compose up
  ```

- Native installation

  ```sh
  # Build knowledge base
  cd scripts/
  ./build_kb.sh
  # Launch knowledge processing machine
  cd scripts/
  ./run_sc_server.sh
  # *in another terminal*
  # Launch semantic web interface at localhost:8000
  cd scripts/
  ./run_scweb.sh
  ```

## Feedback

Contributions, bug reports and feature requests are welcome! Feel free to check our [issues page](https://github.com/ostis-apps/ostis-bibliography/issues) and file a new issue (or comment in existing ones).

## Contributing

- Ensure any install or build dependencies are removed before the end of the layer when doing a build.
- Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations and container parameters.
- You may merge the Pull Request in once you have the sign-off of one other developer, or if you do not have permission to do that, you may request the reviewer to merge it for you.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
